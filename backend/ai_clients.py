"""Utilities to talk with different AI providers."""
from __future__ import annotations

from typing import Any, Dict

import requests


class AIProviderError(RuntimeError):
    """Base error raised when an AI provider cannot fulfil a request."""


class MissingConfigurationError(AIProviderError):
    """Raised when the configuration for a provider is incomplete."""


def _build_messages(user_message: str) -> list[Dict[str, str]]:
    return [{"role": "user", "content": user_message}]


def call_openai(user_message: str, config: Dict[str, Any]) -> str:
    api_key = config.get("OPENAI_API_KEY")
    if not api_key:
        raise MissingConfigurationError("OPENAI_API_KEY is not configured")

    base_url = config.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = config.get("OPENAI_MODEL", "gpt-3.5-turbo")
    temperature = float(config.get("OPENAI_TEMPERATURE", 0.7))
    timeout = int(config.get("AI_REQUEST_TIMEOUT", 30))

    payload: Dict[str, Any] = {
        "model": model,
        "messages": _build_messages(user_message),
        "temperature": temperature,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        f"{base_url}/chat/completions",
        headers=headers,
        json=payload,
        timeout=timeout,
    )
    if response.status_code != 200:
        raise AIProviderError(
            f"OpenAI request failed with status {response.status_code}: {response.text}"
        )

    data = response.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise AIProviderError("Unexpected response format from OpenAI") from exc


def call_anthropic(user_message: str, config: Dict[str, Any]) -> str:
    api_key = config.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise MissingConfigurationError("ANTHROPIC_API_KEY is not configured")

    base_url = config.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
    model = config.get("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
    max_tokens = int(config.get("ANTHROPIC_MAX_TOKENS", 1024))
    temperature = float(config.get("ANTHROPIC_TEMPERATURE", 0.7))
    timeout = int(config.get("AI_REQUEST_TIMEOUT", 30))

    payload: Dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": _build_messages(user_message),
    }

    headers = {
        "x-api-key": api_key,
        "anthropic-version": config.get("ANTHROPIC_API_VERSION", "2023-06-01"),
        "content-type": "application/json",
    }

    response = requests.post(
        f"{base_url}/v1/messages",
        headers=headers,
        json=payload,
        timeout=timeout,
    )
    if response.status_code != 200:
        raise AIProviderError(
            f"Anthropic request failed with status {response.status_code}: {response.text}"
        )

    data = response.json()
    try:
        content = data["content"]
        if isinstance(content, list):
            text_parts = [item.get("text", "") for item in content if isinstance(item, dict)]
            return "".join(text_parts).strip()
        if isinstance(content, str):
            return content.strip()
        raise TypeError("Unexpected content type")
    except (KeyError, TypeError) as exc:
        raise AIProviderError("Unexpected response format from Anthropic") from exc


def call_lmstudio(user_message: str, config: Dict[str, Any]) -> str:
    base_url = config.get("LM_STUDIO_BASE_URL", "http://localhost:1234/v1").rstrip("/")
    model = config.get("LM_STUDIO_MODEL", "local-model")
    timeout = int(config.get("AI_REQUEST_TIMEOUT", 30))

    payload: Dict[str, Any] = {
        "model": model,
        "messages": _build_messages(user_message),
    }

    headers = {
        "Content-Type": "application/json",
    }

    response = requests.post(
        f"{base_url}/chat/completions",
        headers=headers,
        json=payload,
        timeout=timeout,
    )
    if response.status_code != 200:
        raise AIProviderError(
            f"LM Studio request failed with status {response.status_code}: {response.text}"
        )

    data = response.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise AIProviderError("Unexpected response format from LM Studio") from exc


PROVIDER_HANDLERS = {
    "openai": call_openai,
    "anthropic": call_anthropic,
    "lmstudio": call_lmstudio,
}


def generate_ai_response(user_message: str, provider: str, config: Dict[str, Any]) -> str:
    provider_key = provider.lower()
    if provider_key not in PROVIDER_HANDLERS:
        raise AIProviderError(f"Unsupported AI provider: {provider}")

    handler = PROVIDER_HANDLERS[provider_key]
    return handler(user_message, config)
