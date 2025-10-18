"""Utility functions to manage chat validation and OpenAI requests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


class MessageValidationError(ValueError):
    """Raised when the user prompt is not valid."""


@dataclass
class OpenAIServiceError(RuntimeError):
    """Raised when the OpenAI API reports a handled error."""

    user_message: str
    detail: str | None = None


class UnexpectedAIServiceError(RuntimeError):
    """Raised when the OpenAI API behaves unexpectedly."""

    def __init__(self, user_message: str) -> None:
        super().__init__(user_message)
        self.user_message = user_message


def validate_prompt(message: Any, max_chars: int) -> str:
    """Validate and normalise the prompt provided by the user."""

    if not isinstance(message, str):
        raise MessageValidationError("El mensaje debe ser una cadena de texto.")

    sanitized = message.strip()
    if not sanitized:
        raise MessageValidationError("El mensaje no puede estar vacío.")

    if len(sanitized) > max_chars:
        raise MessageValidationError(
            f"El mensaje supera el límite de {max_chars} caracteres permitido."
        )

    return sanitized


def generate_ai_reply(
    client: Any,
    error_cls: type[Exception],
    *,
    user_message: str,
    settings: Mapping[str, Any],
) -> str:
    """Call the OpenAI API and return the assistant reply."""

    system_prompt = settings.get(
        "OPENAI_SYSTEM_PROMPT", "Eres un asistente útil y conciso."
    )
    try:
        response = client.ChatCompletion.create(
            model=settings.get("OPENAI_MODEL", "gpt-3.5-turbo"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=settings.get("OPENAI_TEMPERATURE", 0.7),
            max_tokens=settings.get("OPENAI_MAX_TOKENS", 512),
        )
    except error_cls as exc:  # type: ignore[arg-type]
        raise OpenAIServiceError(
            "Error al comunicarse con el servicio de IA.", str(exc)
        ) from exc
    except Exception as exc:  # pragma: no cover - fallback
        raise UnexpectedAIServiceError(
            "Error inesperado al generar la respuesta. Intenta nuevamente."
        ) from exc

    try:
        return response["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise UnexpectedAIServiceError(
            "El servicio de IA devolvió una respuesta inválida."
        ) from exc
