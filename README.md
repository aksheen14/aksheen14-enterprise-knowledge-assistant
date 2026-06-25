# Enterprise Knowledge Assistant

An AI-powered document assistant that lets users register, upload documents, and chat with an AI to ask questions about uploaded files. The frontend uses React and Vite, while the backend is powered by Python Flask and containerized with Docker.

## Features

- **User authentication** with register/login flows
- **PDF document upload** and metadata storage
- **AI chat interface** for asking questions about uploaded documents
- **JWT-based auth** with tokens stored in local storage
- **PostgreSQL** for user and document metadata
- **ChromaDB** for storing document embeddings
- **LangChain + OpenAI** integration for AI-powered answers
- **CORS support** for frontend/backend communication
- **Document delete** support from the dashboard

## Tech Stack

- Frontend: **React**
- Bundler: **Vite**
- API calls: **Axios**
- Backend: **Python / Flask**
- CORS: **Flask-CORS**
- Database: **PostgreSQL**
- ORM: **SQLAlchemy**
- Vector Store: **ChromaDB**
- AI Integration: **LangChain** + **OpenAI API**
- Containerization: **Docker**

## Project Structure

- `backend/` — Flask APIs, authentication, document upload, RAG pipeline, and SQLAlchemy models
- `frontend/` — React/Vite UI for login, upload, chat, and document management
- `data/uploads/` — local PDF upload storage
- `tests/` — backend unit tests for auth and RAG functionality

## Prerequisites

Make sure the following are installed:

- **Docker**
- **Node.js**
- **Python**
- **PostgreSQL** (local or accessible database)
- **npm** or **pnpm** for frontend package management

## Environment Variables

Create a `.env` file from the example below:

```env
DATABASE_URL=postgresql://username:password@host.docker.internal:5432/your_database
OPENAI_API_KEY=your_openai_api_key
JWT_SECRET=your_jwt_secret
FLASK_ENV=development
FLASK_APP=backend/main.py
```

> Use `host.docker.internal` for Docker-to-Mac networking if your PostgreSQL instance is running on the host machine.

## Local Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/your-username/enterprise-knowledge-assistant.git
cd enterprise-knowledge-assistant
```

### 2. Build and run the backend

```bash
docker build -t my-python-backend ./backend
docker run -d -p 5000:5000 --env-file .env my-python-backend
```

### 3. Install frontend dependencies and start the app

```bash
cd frontend
npm install
npm run dev
```

> If you prefer to run the backend locally without Docker, install the backend dependencies and start Flask directly:

```bash
python -m pip install -r backend/requirements.txt
python backend/main.py
```

## Usage

1. Open the frontend URL shown by `npm run dev` (typically `http://localhost:3000` or `http://localhost:5173`).
2. Register a new user or login.
3. Upload a PDF document from the dashboard.
4. Select the uploaded document and ask questions through the AI chat interface.
5. The AI will answer based on the document content stored in ChromaDB and powered by OpenAI.
