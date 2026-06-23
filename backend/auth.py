from flask import jsonify
import bcrypt
import jwt
import os
from dotenv import load_dotenv
from database import get_db
from models import User
from datetime import datetime, timedelta



load_dotenv()

def register_user(email, password):
    db = next(get_db())
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        return jsonify({"error": "email already registered"}), 400
    
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    new_user = User(email=email, hashed_password=hashed_password.decode("utf-8"))

    db.add(new_user)
    db.commit()
    return jsonify({"message": "User created successfully"}), 201
    
def login_user(email, password):
    db = next(get_db())
    existing_user = db.query(User).filter(User.email == email).first()
    if not existing_user:
        return jsonify({"error": "invalid credentials"}), 401
    
    #pull password and chekc against given passsword
    correct_password = bcrypt.checkpw(
        password.encode("utf-8"), 
        existing_user.hashed_password.encode("utf-8")
    )

    if not correct_password:
        return jsonify({"error": "invalid credentials"}), 401
    
    payload = {
    'user_id': existing_user.id,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }

    # 2. Define secret and algorithm
    secret_key = os.getenv("JWT_SECRET")
    algorithm = ["HS256"]

    # 3. Generate token
    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    return jsonify({"token": token}), 200

def verify_token(token):
    try:
        decoded_token = jwt.decode(
            token, 
            os.getenv("JWT_SECRET"),
            algorithm = ["HS256"]
        )
        return decoded_token["user_id"]
    except jwt.ExpiredSignatureError:
        return None  # token expired
    except jwt.InvalidTokenError:
        return None  # token is fake or malformed

    







