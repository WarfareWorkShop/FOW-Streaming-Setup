from __future__ import annotations

import re
from datetime import timedelta

from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
bcrypt = Bcrypt()


class PasswordValidationError(ValueError):
    """Raised when a password does not meet the strength requirements."""


def _validate_password(password: str) -> None:
    """Ensure that the provided password satisfies the security policy."""
    if password is None:
        raise PasswordValidationError("Password is required.")

    if len(password) < 8:
        raise PasswordValidationError("Password must be at least 8 characters long.")

    if not re.search(r"[A-Z]", password):
        raise PasswordValidationError("Password must include at least one uppercase letter.")

    if not re.search(r"[a-z]", password):
        raise PasswordValidationError("Password must include at least one lowercase letter.")

    if not re.search(r"\d", password):
        raise PasswordValidationError("Password must include at least one number.")

    if not re.search(r"[^A-Za-z0-9]", password):
        raise PasswordValidationError("Password must include at least one special character.")


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(128), nullable=False)

    def set_password(self, password: str) -> None:
        _validate_password(password)
        self.password = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password, password)

    def get_token(self, expires_in: int = 3600) -> str:
        expires_delta = timedelta(seconds=max(1, int(expires_in)))
        return create_access_token(identity=self.id, expires_delta=expires_delta)
