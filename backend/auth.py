from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token
from models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    # TODO: validate user credentials
    return jsonify({'access_token': create_access_token(identity=username)})

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    # TODO: create new user in database
    return jsonify({'message': 'User created'}), 201
