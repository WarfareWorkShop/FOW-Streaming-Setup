from __future__ import annotations

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from flask_jwt_extended import verify_jwt_in_request

from backend.ai_clients import (
    AIProviderError,
    MissingConfigurationError,
    generate_ai_response,
)
from backend.config import Config
from backend.extensions import bcrypt, db, jwt, limiter, migrate
from backend.models import TokenBlocklist
from backend.routes import auth_bp
from backend.tactics import tactics_bp


def create_app(config_class: type[Config] = Config) -> Flask:
    """Application factory used by both tests and production."""

    app = Flask(__name__)
    app.config.from_object(config_class)

    Config.ensure_secret_key(app.config.get("SECRET_KEY"))

    cors_kwargs: dict[str, object] = {"supports_credentials": True}
    allowed_origins = app.config.get("ALLOWED_CORS_ORIGINS") or []
    if allowed_origins:
        cors_kwargs["origins"] = allowed_origins

    CORS(app, resources={r"/api/*": cors_kwargs})

    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)

    default_limits = [limit for limit in app.config.get("GLOBAL_RATE_LIMITS", []) if limit]
    if default_limits:
        limiter._default_limits = tuple(default_limits)

    @app.route("/")
    def index() -> str:
        return render_template("index.html")

    @app.route("/api/chat", methods=["POST"])
    @limiter.limit(lambda: app.config.get("CHAT_RATE_LIMIT", "30/minute"))
    def chat():
        if app.config.get("REQUIRE_AUTH_FOR_CHAT", True):
            verify_jwt_in_request()

        data = request.get_json(silent=True) or {}
        user_message = (data.get("message") or "").strip()
        provider = data.get("provider") or app.config["DEFAULT_AI_PROVIDER"]

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        max_length = int(app.config.get("MAX_CHAT_MESSAGE_LENGTH", 2000))
        if len(user_message) > max_length:
            return (
                jsonify({"error": f"Message is too long (max {max_length} characters)."}),
                413,
            )

        blocked_phrases = app.config.get("CHAT_BLOCKED_PHRASES", [])
        for phrase in blocked_phrases:
            if phrase and phrase.lower() in user_message.lower():
                return jsonify({"error": "The submitted message violates content policy."}), 400

        try:
            ai_response = generate_ai_response(user_message, provider, app.config)
        except MissingConfigurationError as exc:
            return jsonify({"error": str(exc)}), 400
        except AIProviderError as exc:  # pragma: no cover - network failure path
            app.logger.warning("AI provider error", extra={"provider_error": str(exc)})
            return jsonify({"error": str(exc)}), getattr(exc, "status_code", 502)

        return jsonify({"response": ai_response, "provider": provider})

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(tactics_bp, url_prefix="/api/tactics")

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(_jwt_header, jwt_payload):  # pragma: no cover - simple query
        jti = jwt_payload.get("jti")
        if not jti:
            return True
        token = TokenBlocklist.query.filter_by(jti=jti).one_or_none()
        if token is not None:
            return True

        pwd_claim = jwt_payload.get("pwd")
        if not pwd_claim:
            return False

        from datetime import datetime

        from backend.models import User

        try:
            issued_pwd = datetime.fromisoformat(pwd_claim)
        except (TypeError, ValueError):
            return True

        identity = jwt_payload.get("sub")
        user = User.query.get(int(identity)) if identity is not None else None
        if not user or not user.last_password_change:
            return False

        return user.last_password_change.replace(microsecond=0) > issued_pwd.replace(
            microsecond=0
        )

    @jwt.additional_claims_loader
    def add_password_timestamp(identity):  # pragma: no cover - simple serialization
        from backend.models import User

        user = User.query.get(int(identity)) if identity is not None else None
        if not user or not user.last_password_change:
            return {}
        timestamp = user.last_password_change.isoformat()
        return {"pwd": timestamp}

    return app


app = create_app()


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    app.run(debug=True)
