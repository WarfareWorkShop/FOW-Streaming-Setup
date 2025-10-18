"""Utility script to populate the database with sample users."""

import os
import sys

from getpass import getpass
from typing import List, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app  # noqa: E402
from models import PasswordValidationError, User, db  # noqa: E402

SAMPLE_USERS: List[Tuple[str, str, str]] = [
    ("test_user", "test_user@example.com", "TestUser123!"),
    ("streamer", "streamer@example.com", "Streamer123!"),
]


def ensure_user(username: str, email: str, password: str) -> bool:
    """Create a user if it does not already exist."""
    existing = User.query.filter_by(username=username).first()
    if existing:
        return False

    existing_email = User.query.filter_by(email=email).first()
    if existing_email:
        return False

    user = User(username=username, email=email)
    try:
        user.set_password(password)
    except PasswordValidationError as exc:
        raise RuntimeError(f"Provided fixture password for {username} is invalid: {exc}") from exc

    db.session.add(user)
    return True


def main() -> None:
    app = create_app()
    created_any = False

    with app.app_context():
        for username, email, password in SAMPLE_USERS:
            if ensure_user(username, email, password):
                created_any = True

        custom_user = os.getenv("FIXTURE_CREATE_USER")
        if custom_user:
            email = os.getenv("FIXTURE_CREATE_EMAIL")
            password = os.getenv("FIXTURE_CREATE_PASSWORD") or getpass("Password for fixture user: ")
            if not email:
                raise RuntimeError("FIXTURE_CREATE_EMAIL environment variable is required when creating a custom user.")
            if ensure_user(custom_user, email, password):
                created_any = True

        if created_any:
            db.session.commit()
            print("Fixture users created successfully.")
        else:
            print("No new fixture users were created (users already exist).")

if __name__ == "__main__":
    main()
