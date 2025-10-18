"""Application configuration helpers."""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path
from typing import Iterable, List

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency fallback
    def load_dotenv(*_args, **_kwargs):  # type: ignore[func-returns-value]
        return False

# Load variables defined in a local .env file, if present.
load_dotenv()


def _split_csv(value: str | None) -> List[str]:
    """Split a comma separated string into a cleaned list of values."""

    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


class Config:
    """Centralised configuration values for the Flask application."""

    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URI", f"sqlite:///{Path('instance') / 'app.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEFAULT_AI_PROVIDER = os.getenv("DEFAULT_AI_PROVIDER", "openai")
    AI_REQUEST_TIMEOUT = int(os.getenv("AI_REQUEST_TIMEOUT", "30"))

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "512"))

    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
    ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    ANTHROPIC_API_VERSION = os.getenv("ANTHROPIC_API_VERSION", "2023-06-01")
    ANTHROPIC_MAX_TOKENS = int(os.getenv("ANTHROPIC_MAX_TOKENS", "1024"))
    ANTHROPIC_TEMPERATURE = float(os.getenv("ANTHROPIC_TEMPERATURE", "0.7"))

    LM_STUDIO_BASE_URL = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
    LM_STUDIO_MODEL = os.getenv("LM_STUDIO_MODEL", "local-model")
    LM_STUDIO_AUTH_TOKEN = os.getenv("LM_STUDIO_AUTH_TOKEN")

    CHAT_RATE_LIMIT = os.getenv("CHAT_RATE_LIMIT", "30/minute")
    AUTH_RATE_LIMIT = os.getenv("AUTH_RATE_LIMIT", "10/hour")
    TACTICS_RATE_LIMIT = os.getenv("TACTICS_RATE_LIMIT", "20/minute")
    GLOBAL_RATE_LIMITS: Iterable[str] = _split_csv(
        os.getenv("GLOBAL_RATE_LIMITS", "")
    )
    REQUIRE_AUTH_FOR_CHAT = os.getenv("REQUIRE_AUTH_FOR_CHAT", "true").lower() in (
        "1",
        "true",
        "yes",
    )
    MAX_CHAT_MESSAGE_LENGTH = int(os.getenv("MAX_CHAT_MESSAGE_LENGTH", "2000"))

    LOGIN_LOCKOUT_THRESHOLD = int(os.getenv("LOGIN_LOCKOUT_THRESHOLD", "5"))
    LOGIN_LOCKOUT_WINDOW = int(os.getenv("LOGIN_LOCKOUT_WINDOW", "900"))  # seconds
    LOGIN_LOCKOUT_DURATION = int(os.getenv("LOGIN_LOCKOUT_DURATION", "900"))

    RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")

    ALLOWED_CORS_ORIGINS = _split_csv(os.getenv("ALLOWED_CORS_ORIGINS"))

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_MINUTES", "60"))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.getenv("JWT_REFRESH_TOKEN_DAYS", "7"))
    )
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_ERROR_MESSAGE_KEY = "message"

    CHAT_MODERATION_ENABLED = os.getenv("CHAT_MODERATION_ENABLED", "false").lower() in (
        "1",
        "true",
        "yes",
    )
    CHAT_BLOCKED_PHRASES = _split_csv(os.getenv("CHAT_BLOCKED_PHRASES"))

    DEFAULT_SCENARIO_ROLE = os.getenv("DEFAULT_SCENARIO_ROLE", "battlefield analyst")
    MAX_DICE_UPLOAD_SIZE = int(os.getenv("MAX_DICE_UPLOAD_SIZE", str(5 * 1024 * 1024)))

    @staticmethod
    def ensure_secret_key(value: str | None) -> str:
        """Validate that a secret key is present before serving requests."""

        if not value:
            raise RuntimeError(
                "SECRET_KEY must be configured. Set the SECRET_KEY environment variable before running the application."
            )
        return value
