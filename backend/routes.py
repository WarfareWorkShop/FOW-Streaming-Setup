from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from backend.i18n import translate
from backend.models import PasswordValidationError, User, db

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not username or not email or not password.strip():
        return jsonify({"message": translate("backend.auth.errors.missing_fields")}), 400

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
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password.strip():
        return jsonify({"message": translate("backend.auth.errors.password_required")}), 400

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        token = user.get_token()
        return jsonify({"token": token}), 200

    return jsonify({"message": translate("backend.auth.errors.invalid_credentials")}), 401


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"message": translate("backend.auth.errors.user_not_found")}), 404

    return jsonify({"id": user.id, "username": user.username, "email": user.email}), 200
