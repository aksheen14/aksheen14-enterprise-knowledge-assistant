import pytest
from flask import Flask

from backend.rag import rag_bp

@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(rag_bp, url_prefix='/api')
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_upload_endpoint_requires_file(client):
    response = client.post('/api/upload')
    assert response.status_code == 400
    assert response.json['error'] == 'No file uploaded'

def test_query_endpoint_returns_placeholder_answer(client):
    response = client.post('/api/query', json={'question': 'What is the product roadmap?'})
    assert response.status_code == 200
    assert response.json['answer'] == 'This is a placeholder answer.'
    assert response.json['question'] == 'What is the product roadmap?'
