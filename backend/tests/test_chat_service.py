"""Tests for chat validation and OpenAI integration helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import sys
import types

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from chat_service import (  # noqa: E402  pylint: disable=wrong-import-position
    MessageValidationError,
    OpenAIServiceError,
    UnexpectedAIServiceError,
    generate_ai_reply,
    validate_prompt,
)


def test_validate_prompt_strips_and_returns_text():
    assert validate_prompt("  hola  ", 20) == "hola"


@pytest.mark.parametrize(
    "message, expected_error",
    [
        (None, "cadena"),
        ("   ", "vacío"),
    ],
)
def test_validate_prompt_rejects_invalid_inputs(message: Any, expected_error: str):
    with pytest.raises(MessageValidationError) as exc:
        validate_prompt(message, 30)
    assert expected_error in str(exc.value).lower()


def test_validate_prompt_rejects_long_input():
    with pytest.raises(MessageValidationError) as exc:
        validate_prompt("a" * 11, 10)
    assert "límite" in str(exc.value).lower()


class FakeOpenAIError(Exception):
    """Minimal exception to simulate the OpenAI SDK."""


def _build_client(response: Dict[str, Any] | None = None, exc: Exception | None = None):
    calls: Dict[str, Any] = {}

    def _call(**kwargs):
        calls["kwargs"] = kwargs
        if exc:
            raise exc
        return response

    chat_completion = types.SimpleNamespace(create=_call)
    client = types.SimpleNamespace(ChatCompletion=chat_completion)
    return client, calls


def test_generate_ai_reply_returns_message():
    response = {
        "choices": [
            {"message": {"content": "Respuesta", "role": "assistant"}}
        ]
    }
    client, calls = _build_client(response=response)

    result = generate_ai_reply(
        client,
        FakeOpenAIError,
        user_message="Hola",
        settings={
            "OPENAI_MODEL": "gpt-test",
            "OPENAI_SYSTEM_PROMPT": "System",
            "OPENAI_TEMPERATURE": 0.4,
            "OPENAI_MAX_TOKENS": 120,
        },
    )

    assert result == "Respuesta"
    assert calls["kwargs"]["model"] == "gpt-test"
    assert calls["kwargs"]["messages"][0]["content"] == "System"
    assert calls["kwargs"]["messages"][1]["content"] == "Hola"
    assert calls["kwargs"]["temperature"] == 0.4
    assert calls["kwargs"]["max_tokens"] == 120


def test_generate_ai_reply_handles_openai_error():
    client, _ = _build_client(exc=FakeOpenAIError("boom"))

    with pytest.raises(OpenAIServiceError) as exc:
        generate_ai_reply(
            client,
            FakeOpenAIError,
            user_message="Hola",
            settings={},
        )

    assert "servicio de ia" in exc.value.user_message.lower()
    assert "boom" in (exc.value.detail or "")


def test_generate_ai_reply_handles_invalid_structure():
    client, _ = _build_client(response={"choices": []})

    with pytest.raises(UnexpectedAIServiceError) as exc:
        generate_ai_reply(
            client,
            FakeOpenAIError,
            user_message="Hola",
            settings={},
        )

    assert "respuesta inválida" in exc.value.user_message.lower()
