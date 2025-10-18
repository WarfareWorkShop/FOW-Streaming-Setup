from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Generator

os.environ.setdefault("SECRET_KEY", "testing-secret-key")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

from backend.app import create_app
from backend.config import Config
from backend.models import User, db


class TestConfig(Config):  # type: ignore[misc]
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OPENAI_API_KEY = "test"


@pytest.fixture
def app() -> Generator:
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user_factory(app):
    def _factory(username: str, email: str) -> User:
        user = User(username=username, email=email)
        user.set_password("Password1!")
        db.session.add(user)
        db.session.commit()
        return user

    yield _factory
