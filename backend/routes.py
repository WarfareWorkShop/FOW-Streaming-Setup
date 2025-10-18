from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from models import User, db

from backend.models import User, db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    username = data.get('username')
    password = data.get('password')

    if not isinstance(username, str) or not isinstance(password, str):
        return jsonify({"message": "Username and password are required."}), 400

    username = username.strip()
    if not username or not password or not password.strip():
        return jsonify({"message": "Username and password cannot be empty."}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "Username is already taken."}), 409

    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Username is already taken."}), 409
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"message": "Could not register user. Please try again later."}), 500

    return jsonify({"message": "User registered successfully!"}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get('username')
    password = data.get('password')

    if not isinstance(username, str) or not isinstance(password, str):
        return jsonify({"message": "Username and password are required."}), 400

    if not username.strip() or not password.strip():
        return jsonify({"message": "Username and password cannot be empty."}), 400

    user = User.query.filter_by(username=username.strip()).first()
    if user and user.check_password(password):
        token = user.get_token()
        return jsonify({"token": token}), 200

    return jsonify({"message": "Invalid credentials!"}), 401


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found."}), 404

    return jsonify({"id": user.id, "username": user.username}), 200

