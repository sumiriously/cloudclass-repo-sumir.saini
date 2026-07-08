import re

from flask import Blueprint, jsonify, request
from flask_login import login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.models import User, db

auth = Blueprint("auth", __name__)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_credentials(email, password):
    if not email or not password:
        return "Email and password are required"
    if not EMAIL_RE.match(email):
        return "Invalid email format"
    if len(password) < 8:
        return "Password must be at least 8 characters"
    return None


@auth.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")

    error = validate_credentials(email, password)
    if error:
        return jsonify({"message": error}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already exists"}), 409

    user = User(email=email, password_hash=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "User created"}), 201


@auth.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    password = data.get("password")

    error = validate_credentials(email, password)
    if error:
        return jsonify({"message": error}), 400

    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password_hash, password):
        login_user(user)
        return jsonify({"message": "Logged in"}), 200

    return jsonify({"message": "Invalid credentials"}), 401


@auth.route("/logout", methods=["POST"])
def logout():
    logout_user()
    return jsonify({"message": "Logged out"}), 200
