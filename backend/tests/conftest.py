from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = ROOT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault('SECRET_KEY', 'testing-secret')

from backend.app import create_app
from backend.config import Config
from backend.extensions import db


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'testing-secret'
    WTF_CSRF_ENABLED = False
    REQUIRE_AUTH_FOR_CHAT = True
    RATELIMIT_ENABLED = False
    GLOBAL_RATE_LIMITS = []


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_headers(client):
    registration_payload = {
        'username': 'commander',
        'email': 'commander@example.com',
        'password': 'Sup3r$ecure',
    }
    client.post('/api/auth/register', json=registration_payload)

    response = client.post(
        '/api/auth/login',
        json={'username': registration_payload['username'], 'password': registration_payload['password']},
    )
    data = response.get_json()
    return {
        'Authorization': f"Bearer {data['accessToken']}",
    }
