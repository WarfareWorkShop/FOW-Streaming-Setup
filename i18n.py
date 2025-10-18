"""Lightweight internationalisation utilities shared across the project."""

from __future__ import annotations

import json
import locale
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Tuple

BASE_DIR = Path(__file__).resolve().parent
TRANSLATIONS_DIR = BASE_DIR / "translations"
DEFAULT_LANGUAGE = "es"
SUPPORTED_LANGUAGES: tuple[str, ...] = ("es", "en")
LANGUAGE_ARGUMENTS = {"--lang", "--language"}


class _SafeDict(dict):
    """Dictionary that leaves unknown placeholders untouched."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def available_languages() -> Tuple[str, ...]:
    """Return the list of supported language codes."""

    return SUPPORTED_LANGUAGES


def _translations_path(language: str) -> Path:
    return TRANSLATIONS_DIR / f"{language}.json"


@lru_cache(maxsize=None)
def _load_language(language: str) -> dict[str, Any]:
    path = _translations_path(language)
    if not path.exists():  # pragma: no cover - defensive guard
        return {}
    with path.open("r", encoding="utf8") as handle:
        return json.load(handle)


def _normalise_candidate(value: str | None) -> str | None:
    if not value:
        return None

    for candidate in str(value).split(","):
        primary = candidate.split(";", 1)[0].strip().replace("_", "-").lower()
        if not primary:
            continue
        code = primary.split("-", 1)[0]
        if code in SUPPORTED_LANGUAGES:
            return code

    return None


def resolve_language(*candidates: str | None) -> str:
    """Return the first supported language in the provided candidates."""

    for candidate in candidates:
        code = _normalise_candidate(candidate)
        if code:
            return code

    return DEFAULT_LANGUAGE


def detect_language_from_env() -> str:
    """Guess a preferred language from environment settings."""

    language, _ = locale.getdefaultlocale() if hasattr(locale, "getdefaultlocale") else (None, None)
    return resolve_language(
        os.environ.get("FOW_LANGUAGE"),
        os.environ.get("FOW_LANG"),
        os.environ.get("LC_MESSAGES"),
        os.environ.get("LANG"),
        language,
    )


def determine_language_from_cli(argv: Iterable[str] | None = None) -> tuple[str, list[str]]:
    """Extract an optional --lang/--language flag from CLI arguments."""

    args = list(argv if argv is not None else sys.argv[1:])
    remaining: list[str] = []
    extracted: str | None = None
    skip_next = False

    for value in args:
        if skip_next:
            skip_next = False
            extracted = value
            continue

        if any(value.startswith(prefix + "=") for prefix in LANGUAGE_ARGUMENTS):
            extracted = value.split("=", 1)[1]
            continue

        if value in LANGUAGE_ARGUMENTS:
            skip_next = True
            continue

        remaining.append(value)

    language = resolve_language(extracted, detect_language_from_env())
    return language, remaining


def _format_value(value: Any, params: dict[str, Any]) -> Any:
    if isinstance(value, str):
        return value.format_map(_SafeDict(params)) if params else value

    if isinstance(value, list):
        return [_format_value(item, params) for item in value]

    if isinstance(value, dict):
        return {key: _format_value(val, params) for key, val in value.items()}

    return value


def translate(key: str, language: str | None = None, **params: Any) -> Any:
    """Fetch a translation value using dotted keys."""

    lang = resolve_language(language, DEFAULT_LANGUAGE)
    value = _find_translation_value(key, lang)

    if value is None and lang != DEFAULT_LANGUAGE:
        value = _find_translation_value(key, DEFAULT_LANGUAGE)

    if value is None:
        return key

    return _format_value(value, params)


def _find_translation_value(key: str, language: str) -> Any:
    current: Any = _load_language(language)
    for segment in key.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(segment)
        if current is None:
            return None
    return current


def format_language_list(language: str) -> str:
    """Return a comma-separated list of language names in the requested language."""

    names = []
    for code in available_languages():
        label = translate(f"common.languages.{code}", language)
        names.append(label)
    return ", ".join(names)
