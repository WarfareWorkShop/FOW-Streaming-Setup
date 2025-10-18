from __future__ import annotations

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
        return render_template("index.html")

    @app.route("/api/chat", methods=["POST"])
    def chat():
        data = request.get_json(silent=True) or {}
        user_message = (data.get("message") or "").strip()
        provider = data.get("provider") or app.config["DEFAULT_AI_PROVIDER"]

        if not user_message:
            return jsonify({"error": "Message is required"}), 400

        try:
            ai_response = generate_ai_response(user_message, provider, app.config)
        except MissingConfigurationError as exc:
            return jsonify({"error": str(exc)}), 400
        except AIProviderError as exc:  # pragma: no cover - network failure path
            app.logger.exception("AI provider error")
            return jsonify({"error": str(exc)}), 502

        return jsonify({"response": ai_response, "provider": provider})

    app.register_blueprint(auth_bp, url_prefix="/api/auth")

    return app


app = create_app()


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    app.run(debug=True)
