from flask import Blueprint, request, jsonify
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from models import User, db
from models import PasswordValidationError

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if data is None:
        return jsonify({"message": "Invalid payload."}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"message": "Username, email and password are required."}), 400

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
        return jsonify({"message": "Username or email already exists."}), 409

    return jsonify({"message": "User registered successfully!"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if data is None:
        return jsonify({"message": "Invalid payload."}), 400

    identifier = data.get('username') or data.get('email')
    password = data.get('password')

    if not identifier or not password:
        return jsonify({"message": "Username/email and password are required."}), 400

    user = User.query.filter(
        or_(User.username == identifier, User.email == identifier)
    ).first()

    if user and user.check_password(password):
        token = user.get_token()
        return jsonify({"token": token})
    return jsonify({"message": "Invalid credentials!"}), 401

