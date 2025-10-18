from __future__ import annotations

import logging
from typing import Any, Dict

try:  # pragma: no cover - executed only when SDK is available
    import openai
    from openai.error import OpenAIError
except ModuleNotFoundError:  # pragma: no cover - fallback for environments sin SDK
    class OpenAIError(Exception):
        """Fallback error when the OpenAI SDK is missing."""

    class _ChatCompletion:
        @staticmethod
        def create(*_: Any, **__: Any) -> Dict[str, Any]:
            raise OpenAIError(
                "El paquete 'openai' no está instalado. Instálalo para usar la IA."
            )

    class _OpenAIStub:
        api_key: str | None = None
        ChatCompletion = _ChatCompletion

    openai = _OpenAIStub()  # type: ignore[assignment]

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import Config
from chat_service import (
    MessageValidationError,
    OpenAIServiceError,
    UnexpectedAIServiceError,
    generate_ai_reply,
    validate_prompt,
)

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)  # Habilitar CORS para permitir peticiones desde el frontend
jwt = JWTManager(app)

if app.config.get("OPENAI_API_KEY"):
    openai.api_key = app.config["OPENAI_API_KEY"]
else:
    logging.warning(
        "OPENAI_API_KEY is not configured. The /api/chat endpoint will not be able to "
        "contact OpenAI."
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    if not request.is_json:
        return (
            jsonify({"error": "Solicitud inválida. Se esperaba un cuerpo JSON."}),
            400,
        )

    user_message = request.json.get('message')

    try:
        sanitized_message = validate_prompt(
            user_message, app.config.get("PROMPT_MAX_CHARS", 2000)
        )
    except MessageValidationError as exc:
        return jsonify({"error": str(exc)}), 400

    if not app.config.get("OPENAI_API_KEY"):
        return (
            jsonify({"error": "Servicio de IA no configurado. Contacta al administrador."}),
            500,
        )

    try:
        ai_message = generate_ai_reply(
            openai,
            OpenAIError,
            user_message=sanitized_message,
            settings=app.config,
        )
    except OpenAIServiceError as exc:
        logging.exception("OpenAI API error: %s", exc)
        payload = {"error": exc.user_message}
        if exc.detail:
            payload["detalle"] = exc.detail
        return jsonify(payload), 502
    except UnexpectedAIServiceError as exc:
        logging.exception("Unexpected OpenAI error: %s", exc)
        return jsonify({"error": exc.user_message}), 500

    return jsonify({"response": ai_message})

if __name__ == '__main__':
    app.run(debug=True)

