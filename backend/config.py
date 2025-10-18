"""Application configuration helpers."""

import os
from typing import Optional

from dotenv import load_dotenv

# Load variables defined in a local .env file, if present.
load_dotenv()


def _int_env(name: str, default: int) -> int:
    """Return an integer environment variable or a default value."""

    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _float_env(name: str, default: float) -> float:
    """Return a float environment variable or a default value."""

    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


class Config:
    """Base configuration values used by the Flask application."""

    SECRET_KEY = os.getenv("SECRET_KEY", "change_me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI", "sqlite:///site.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change_me")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    OPENAI_SYSTEM_PROMPT = os.getenv(
        "OPENAI_SYSTEM_PROMPT", "Eres un asistente útil y conciso."
    )
    OPENAI_TEMPERATURE = _float_env("OPENAI_TEMPERATURE", 0.7)
    OPENAI_MAX_TOKENS = _int_env("OPENAI_MAX_TOKENS", 512)
    PROMPT_MAX_CHARS = _int_env("PROMPT_MAX_CHARS", 2000)


