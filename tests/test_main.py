import json
from datetime import datetime
from flask import jsonify

from unittest.mock import MagicMock

import pytest

from backend import main


@pytest.fixture
def client():
    return main.app.test_client()


def test_register_route_requires_email_and_password(client):
    response = client.post("/auth/register", json={})

    assert response.status_code == 400
    assert response.json == {"error": "email and password required"}


def test_login_route_delegates_to_login_user(monkeypatch, client):
    monkeypatch.setattr(
        main,
        "login_user",
        lambda email, password: (jsonify({"token": "fake-token"}), 200),
    )

    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "secret"},
    )

    assert response.status_code == 200
    assert response.json == {"token": "fake-token"}


def test_history_route_returns_user_chat_history(monkeypatch, client):
    def fake_verify_token(token):
        return 123

    class DummyQuery:
        def __init__(self, data):
            self._data = data

        def filter(self, *args, **kwargs):
            return self

        def all(self):
            return self._data

    class DummyDB:
        def query(self, model):
            fake_chat = MagicMock(
                question="What is AI?",
                answer="AI is artificial intelligence.",
                sources="[]",
                asked_at=datetime(2026, 1, 1),
                document_id=42,
            )
            return DummyQuery([fake_chat])

    def fake_get_db_context():
        class DummyContext:
            def __enter__(self):
                return DummyDB()

            def __exit__(self, exc_type, exc, tb):
                return False

        return DummyContext()

    monkeypatch.setattr(main, "verify_token", fake_verify_token)
    monkeypatch.setattr(main, "get_db_context", fake_get_db_context)

    response = client.get(
        "/documents/history",
        headers={"Authorization": "Bearer fake-token"},
    )

    assert response.status_code == 200
    assert response.json == [
        {
            "question": "What is AI?",
            "answer": "AI is artificial intelligence.",
            "sources": "[]",
            "asked_at": "2026-01-01T00:00:00",
            "document_id": 42,
        }
    ]
