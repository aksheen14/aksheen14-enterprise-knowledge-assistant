# Enterprise Knowledge Assistant

A starter repository for an enterprise-grade knowledge assistant using a Flask backend and React frontend.

## Structure

- `backend/` — Flask APIs, RAG pipeline, authentication, database models
- `frontend/` — React UI for login, document upload, chat, and history
- `data/uploads/` — temporary upload storage for PDFs
- `tests/` — pytest coverage for auth and RAG functionality

## Getting started

1. Copy `.env.example` to `.env` and fill in secrets.
2. Install backend dependencies with `pip install -r backend/requirements.txt`.
3. Install frontend dependencies in `frontend/` with `npm install`.
4. Run Flask backend and React frontend separately.
