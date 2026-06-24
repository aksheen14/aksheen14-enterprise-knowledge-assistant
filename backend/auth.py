from flask import jsonify
import bcrypt
import jwt
import os
from dotenv import load_dotenv
from database import get_db_context
from models import User
from datetime import datetime, timedelta



load_dotenv()

def register_user(email, password):
    try:
        with get_db_context() as db:
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                return jsonify({"error": "email already registered"}), 400

            hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
            new_user = User(email=email, hashed_password=hashed_password.decode("utf-8"))

            db.add(new_user)
            return jsonify({"message": "User created successfully"}), 201
    except Exception as e:
        return jsonify({"error": f"failed to create user: {str(e)}"}), 500
    
def login_user(email, password):
    try:
        with get_db_context() as db:
            existing_user = db.query(User).filter(User.email == email).first()

            if not existing_user:
                return jsonify({"error": "invalid credentials"}), 401

            correct_password = bcrypt.checkpw(
                password.encode("utf-8"), 
                existing_user.hashed_password.encode("utf-8")
            )

            if not correct_password:
                return jsonify({"error": "invalid credentials"}), 401

            payload = {
                "user_id": existing_user.id,
                "exp": datetime.utcnow() + timedelta(hours=1)
            }

            secret_key = os.getenv("JWT_SECRET")
            algorithm = "HS256"

            token = jwt.encode(payload, secret_key, algorithm=algorithm)
            return jsonify({"token": token}), 200
    except Exception as e:
        return jsonify({"error": f"failed to login user: {str(e)}"}), 500

def verify_token(token):
    try:
        if token and token.startswith("Bearer "):
            token = token[7:]

        decoded_token = jwt.decode(
            token,
            os.getenv("JWT_SECRET"),
            algorithms=["HS256"]
        )
        return decoded_token["user_id"]
    except jwt.ExpiredSignatureError:
        return None  # token expired
    except jwt.InvalidTokenError:
        return None  # token is fake or malformed

    







