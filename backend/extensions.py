"""Shared Flask extensions for the backend application."""
from __future__ import annotations

from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager

try:  # pragma: no cover - optional dependency fallback
    from flask_migrate import Migrate
except ImportError:  # pragma: no cover
    class Migrate:  # type: ignore[too-few-public-methods]
        def init_app(self, *args, **kwargs):
            pass

from flask_sqlalchemy import SQLAlchemy

try:  # pragma: no cover - dependency optional during tests
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
except ImportError:  # pragma: no cover - graceful fallback for environments sin Flask-Limiter
    from collections import defaultdict, deque
    from functools import wraps
    from time import time
    from typing import Callable, Deque, Dict, Iterable, Tuple

    from flask import abort

    _PERIODS_IN_SECONDS = {
        "second": 1,
        "seconds": 1,
        "minute": 60,
        "minutes": 60,
        "hour": 3600,
        "hours": 3600,
        "day": 86400,
        "days": 86400,
    }

    def _parse_limit(limit: str) -> Tuple[int, float]:
        parts = limit.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid rate limit expression: {limit!r}")
        try:
            count = int(parts[0].strip())
        except ValueError as exc:  # pragma: no cover - defensive
            raise ValueError(f"Invalid rate limit count in {limit!r}") from exc

        period_key = parts[1].strip().lower()
        seconds = _PERIODS_IN_SECONDS.get(period_key)
        if not seconds:
            raise ValueError(f"Unsupported period in rate limit: {limit!r}")
        return count, float(seconds)

    class Limiter:  # type: ignore[too-few-public-methods]
        """Minimal in-memory fallback when Flask-Limiter is unavailable."""

        def __init__(self, key_func: Callable[[], str] | None = None, default_limits: Iterable[str] | None = None):
            self._key_func = key_func or (lambda: "global")
            self._limits = tuple(default_limits or ())
            self._storage: Dict[str, Dict[Tuple[int, float], Deque[float]]] = defaultdict(lambda: defaultdict(deque))

        def init_app(self, app):
            app.logger.warning(
                "Flask-Limiter no está instalado; se activa un limitador en memoria de respaldo.")

        def _resolve_limits(self, limits: Iterable[str | Callable[[], str | Iterable[str]]]) -> Tuple[str, ...]:
            resolved: list[str] = []
            for limit in limits:
                value: str | Iterable[str] | None
                if callable(limit):  # type: ignore[call-arg]
                    value = limit()
                else:
                    value = limit

                if value is None:
                    continue

                if isinstance(value, (list, tuple, set)):
                    for item in value:
                        if item:
                            resolved.append(str(item))
                else:
                    resolved.append(str(value))
            return tuple(resolved)

        def _check(self, limits: Iterable[str | Callable[[], str | Iterable[str]]]) -> None:
            key = self._key_func()
            now = time()
            for limit in self._resolve_limits(limits):
                count, period = _parse_limit(limit)
                bucket = self._storage[key][(count, period)]
                threshold = now - period
                while bucket and bucket[0] <= threshold:
                    bucket.popleft()
                if len(bucket) >= count:
                    abort(429)
                bucket.append(now)

        def limit(self, *limits: str):
            active_limits = limits or self._limits

            def decorator(func: Callable):
                @wraps(func)
                def wrapper(*args, **kwargs):
                    self._check(active_limits)
                    return func(*args, **kwargs)

                return wrapper

            return decorator

    def get_remote_address():  # type: ignore[func-returns-value]
        from flask import request

        return request.remote_addr or "0.0.0.0"


db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address, default_limits=[])

__all__ = ["db", "bcrypt", "migrate", "jwt", "limiter"]
