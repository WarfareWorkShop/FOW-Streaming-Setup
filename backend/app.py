from __future__ import annotations

from functools import partial

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

from backend.ai_clients import (
    AIProviderError,
    MissingConfigurationError,
    generate_ai_response,
)
from backend.config import Config
from backend.i18n import get_request_language, translate
from backend.models import bcrypt, db
from backend.routes import auth_bp

migrate = Migrate()
jwt = JWTManager()


def create_app(config_class: type[Config] = Config) -> Flask:
    """Application factory used by both tests and production."""

    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app)

    db.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    @app.route("/")
    def index() -> str:
        language = get_request_language()
        translator = partial(translate, language=language)
        return render_template("index.html", language=language, t=translator)

    @app.route("/api/chat", methods=["POST"])
    def chat():
        data = request.get_json(silent=True) or {}
        user_message = (data.get("message") or "").strip()
        provider = data.get("provider") or app.config["DEFAULT_AI_PROVIDER"]

        language = get_request_language()

        if not user_message:
            return jsonify({"error": translate("backend.chat.errors.message_required", language)}), 400

        try:
            ai_response = generate_ai_response(user_message, provider, app.config)
        except MissingConfigurationError as exc:
            error = translate(
                "backend.chat.errors.missing_configuration",
                language,
                details=str(exc),
            )
            return jsonify({"error": error}), 400
        except AIProviderError as exc:  # pragma: no cover - network failure path
            app.logger.exception("AI provider error")
            error = translate(
                "backend.chat.errors.provider_error",
                language,
                details=str(exc),
            )
            return jsonify({"error": error}), 502

        return jsonify({"response": ai_response, "provider": provider})

    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    return app


app = create_app()


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    app.run(debug=True)
