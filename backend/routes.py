from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Deque, Dict

import requests
from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from backend.extensions import limiter
from backend.i18n import translate
from backend.models import PasswordValidationError, TokenBlocklist, User, db

auth_bp = Blueprint("auth", __name__)

_FAILED_LOGINS: Dict[str, Deque[datetime]] = defaultdict(deque)
_ACCOUNT_LOCKS: Dict[str, datetime] = {}


def _rate_limit_auth() -> str:
    return current_app.config.get("AUTH_RATE_LIMIT", "10/hour")


def _lock_key(username: str) -> str:
    remote_addr = request.remote_addr or "unknown"
    return f"{username.lower()}::{remote_addr}"


def _is_locked(key: str) -> bool:
    unlock_time = _ACCOUNT_LOCKS.get(key)
    if not unlock_time:
        return False
    if unlock_time <= datetime.utcnow():
        _ACCOUNT_LOCKS.pop(key, None)
        _FAILED_LOGINS.pop(key, None)
        return False
    return True


def _register_failure(key: str) -> None:
    settings = current_app.config
    window_seconds = int(settings.get("LOGIN_LOCKOUT_WINDOW", 900))
    threshold = int(settings.get("LOGIN_LOCKOUT_THRESHOLD", 5))
    duration = int(settings.get("LOGIN_LOCKOUT_DURATION", 900))

    failures = _FAILED_LOGINS[key]
    now = datetime.utcnow()
    failures.append(now)

    threshold_time = now - timedelta(seconds=window_seconds)
    while failures and failures[0] < threshold_time:
        failures.popleft()

    if not failures:
        _FAILED_LOGINS.pop(key, None)
        return

    if len(failures) >= threshold:
        _ACCOUNT_LOCKS[key] = now + timedelta(seconds=duration)


def _verify_captcha(token: str | None) -> bool:
    secret = current_app.config.get("RECAPTCHA_SECRET_KEY")
    if not secret:
        return True
    if not token:
        return False

    try:
        response = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={"secret": secret, "response": token, "remoteip": request.remote_addr},
            timeout=5,
        )
        response.raise_for_status()
        payload = response.json()
        return bool(payload.get("success"))
    except requests.RequestException:
        current_app.logger.warning("reCAPTCHA verification failed", exc_info=True)
        return False


@auth_bp.route("/register", methods=["POST"])
@limiter.limit(_rate_limit_auth)
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    captcha_token = data.get("captchaToken")

    if not username or not email or not password.strip():
        return jsonify({"message": translate("backend.auth.errors.missing_fields")}), 400

    if not _verify_captcha(captcha_token):
        return jsonify({"message": "Captcha verification failed."}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"message": translate("backend.auth.errors.username_taken")}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({"message": translate("backend.auth.errors.email_taken")}), 409

    new_user = User(username=username, email=email)
    try:
        new_user.set_password(password)
    except PasswordValidationError as exc:
        return jsonify({"message": str(exc)}), 400

    db.session.add(new_user)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": translate("backend.auth.errors.registration_conflict")}), 409
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"message": translate("backend.auth.errors.registration_failed")}), 500

    return jsonify({"message": translate("backend.auth.success.registered")}), 201


@auth_bp.route("/login", methods=["POST"])
@limiter.limit(_rate_limit_auth)
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    captcha_token = data.get("captchaToken")

    if not username or not password.strip():
        return jsonify({"message": translate("backend.auth.errors.password_required")}), 400

    if not _verify_captcha(captcha_token):
        return jsonify({"message": "Captcha verification failed."}), 400

    key = _lock_key(username)
    if _is_locked(key):
        return (
            jsonify({"message": "Account temporarily locked due to repeated failures."}),
            423,
        )

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        _FAILED_LOGINS.pop(key, None)
        _ACCOUNT_LOCKS.pop(key, None)

        identity = str(user.id)
        access_token = create_access_token(identity=identity, fresh=True)
        refresh_token = create_refresh_token(identity=identity)

        return (
            jsonify(
                {
                    "accessToken": access_token,
                    "refreshToken": refresh_token,
                    "expiresIn": int(current_app.config["JWT_ACCESS_TOKEN_EXPIRES"].total_seconds()),
                }
            ),
            200,
        )

    _register_failure(key)
    return jsonify({"message": "Invalid credentials!"}), 401


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id)) if user_id is not None else None

    if not user:
        return jsonify({"message": translate("backend.auth.errors.user_not_found")}), 404

    return jsonify({"id": user.id, "username": user.username, "email": user.email}), 200


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh_token():
    identity = get_jwt_identity()
    user = User.query.get(int(identity)) if identity is not None else None
    if not user:
        return jsonify({"message": "User not found."}), 404

    access_token = create_access_token(identity=identity)
    return (
        jsonify(
            {
                "accessToken": access_token,
                "expiresIn": int(current_app.config["JWT_ACCESS_TOKEN_EXPIRES"].total_seconds()),
            }
        ),
        200,
    )


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    jwt_data = get_jwt()
    jti = jwt_data.get("jti")
    identity = get_jwt_identity()
    if not jti or not identity:
        return jsonify({"message": "Invalid token."}), 400

    db.session.add(TokenBlocklist(jti=jti, user_id=int(identity)))
    db.session.commit()
    return jsonify({"message": "Token revoked."}), 200
