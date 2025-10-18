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
    class Limiter:  # type: ignore[too-few-public-methods]
        def __init__(self, *args, **kwargs):  # noqa: D401 - compatibility shim
            self.enabled = False

        def init_app(self, app):
            app.logger.warning(
                "Flask-Limiter no está instalado; los límites de velocidad están deshabilitados.")

        def limit(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator

    def get_remote_address():  # type: ignore[func-returns-value]
        return "0.0.0.0"


db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address, default_limits=[])

__all__ = ["db", "bcrypt", "migrate", "jwt", "limiter"]
