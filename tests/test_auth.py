import pytest
from flask import Flask

from backend.auth import auth_bp

@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_signup_route_returns_201(client):
    response = client.post('/auth/signup', json={'username': 'testuser', 'password': 'secret'})
    assert response.status_code == 201
    assert response.json['message'] == 'User created'

def test_login_route_returns_token(client):
    response = client.post('/auth/login', json={'username': 'testuser', 'password': 'secret'})
    assert response.status_code == 200
    assert 'access_token' in response.json
