import os
import bcrypt
import jwt
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure a test database and secret are available before importing backend code.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret")

from backend.auth import register_user, login_user, verify_token
from backend.models import User
from backend.database import Base


@pytest.fixture(scope="module")
def db_engine():
    engine = create_engine(os.environ["DATABASE_URL"])
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture()
def db_session(db_engine, monkeypatch):
    Session = sessionmaker(bind=db_engine)
    session = Session()

    def fake_get_db():
        try:
            yield session
        finally:
            session.close()

    monkeypatch.setattr("backend.auth.get_db", fake_get_db)
    yield session
    session.rollback()
    session.close()


def test_register_user_creates_user(db_session):
    response, status_code = register_user("test@example.com", "secret123")

    assert status_code == 201
    assert response.json["message"] == "User created successfully"

    user = db_session.query(User).filter(User.email == "test@example.com").first()
    assert user is not None
    assert user.email == "test@example.com"


def test_register_user_rejects_duplicate_email(db_session):
    existing = User(email="duplicate@example.com", hashed_password=bcrypt.hashpw(b"secret", bcrypt.gensalt()).decode())
    db_session.add(existing)
    db_session.commit()

    response, status_code = register_user("duplicate@example.com", "anotherpass")

    assert status_code == 400
    assert response.json["error"] == "email already registered"


def test_login_user_returns_token(db_session):
    password = "loginpass"
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = User(email="login@example.com", hashed_password=hashed)
    db_session.add(user)
    db_session.commit()

    response, status_code = login_user("login@example.com", password)

    assert status_code == 200
    assert "token" in response.json

    token = response.json["token"]
    assert verify_token(token) == user.id


def test_login_user_rejects_invalid_password(db_session):
    password = "correctpass"
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = User(email="wrongpass@example.com", hashed_password=hashed)
    db_session.add(user)
    db_session.commit()

    response, status_code = login_user("wrongpass@example.com", "incorrect")

    assert status_code == 401
    assert response.json["error"] == "invalid credentials"


def test_verify_token_accepts_bearer_token():
    payload = {
        "user_id": 42,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, os.environ["JWT_SECRET"], algorithm="HS256")

    assert verify_token("Bearer {}".format(token)) == 42
