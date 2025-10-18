"""Helper utilities to integrate shared translations with Flask."""

from __future__ import annotations

from functools import partial
from typing import Any, Callable

from flask import Request, request

from i18n import resolve_language, translate as base_translate


def get_request_language(req: Request | None = None) -> str:
    """Resolve the preferred language for the current request."""

    active_request = req or request
    if active_request is None:  # pragma: no cover - only when outside request context
        return resolve_language(None)

    return resolve_language(
        active_request.args.get("lang"),
        active_request.headers.get("X-App-Language"),
        active_request.headers.get("Accept-Language"),
    )


def get_translator(language: str | None = None) -> Callable[[str, Any], Any]:
    """Return a partial translation function bound to a language."""

    lang = resolve_language(language, get_request_language())
    return partial(base_translate, language=lang)


def translate(key: str, language: str | None = None, **params: Any) -> Any:
    """Translate a key using the request-aware language detection."""

    lang = resolve_language(language, get_request_language())
    return base_translate(key, lang, **params)
