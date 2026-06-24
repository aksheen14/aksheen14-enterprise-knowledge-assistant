from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename
from database import init_db, get_db_context
from models import User, Document, ChatHistory
from auth import register_user, login_user, verify_token
from rag import load_and_chunk, embed_and_store, answer_question
import os
import json
from flask_cors import CORS

# create the flask app
app = Flask(__name__)
CORS(app)
# folder where uploaded files will be saved
UPLOAD_FOLDER = "data/uploads/"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# create the uploads folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# initialize the database — creates tables if they don't exist
init_db()

@app.route("/auth/register", methods=["POST"]) 
def register():
    data = request.get_json(silent=True) or {}
    if not data:
        return jsonify({"error": "invalid request body"}), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email and password required"}), 400

    try:
        return register_user(email, password)
    except Exception as e:
        return jsonify({"error": f"server error: {str(e)}"}), 500

@app.route("/auth/login", methods=["POST"]) 
def login():
    try:
        data = request.get_json(silent=True) or {}
        if not data:
            return jsonify({"error": "invalid request body"}), 400

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"error": "email and password required"}), 400

        return login_user(email, password)
    except Exception as e: 
        return jsonify({"error": f"server error: {str(e)}"}), 500

@app.route("/documents/upload", methods=["POST"]) 
def upload_documents():
    try:
        #valideate user
        token = request.headers.get("Authorization")
        user_id = verify_token(token)
        if not user_id:
            return jsonify({"error": "invalid credentials"}), 401
        
        #get file
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "no file uploaded"}), 400
        
        #save to folder
        filename = secure_filename(file.filename)
        if not filename:
            return jsonify({"error": "invalid filename"}), 400

        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        try:
            file.save(filepath)
        except Exception as e:
            return jsonify({"error": f"failed to save file: {str(e)}"}), 500

        #chunk it
        try: 
            chunks = load_and_chunk(filepath)
        except Exception as e:
            return jsonify({"error": f"failed to chunk PDF: {str(e)}"}), 400

        try:
            with get_db_context() as db:
                new_document = Document(filename=filename, filepath=filepath, user_id=user_id)
                db.add(new_document)
                db.refresh(new_document)
                document_id = new_document.id
        except Exception as e:
            return jsonify({"error": f"failed to save document metadata: {str(e)}"}), 500

        #embed it
        try: 
            embed_and_store(chunks, document_id)
        except Exception as e:
            return jsonify({"error": f"failed to embed PDF: {str(e)}"}), 500

        return jsonify({
            "message": "Document uploaded successfully",
            "document_id": document_id
        }), 201
    except Exception as e: 
        return jsonify({"error": f"server error: {str(e)}"}), 500

@app.route("/documents/ask", methods=["POST"]) 
def ask_question():
    try:
        # validate user
        token = request.headers.get("Authorization")
        user_id = verify_token(token)
        if not user_id:
            return jsonify({"error": "invalid credentials"}), 401

        # get request body
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "invalid request body"}), 400

        question = data.get("question")
        if not isinstance(question, str) or not question.strip():
            return jsonify({"error": "invalid question"}), 400

        document_id = data.get("document_id")
        if document_id is None:
            return jsonify({"error": "invalid document_id"}), 400

        try:
            document_id = int(document_id)
        except (TypeError, ValueError):
            return jsonify({"error": "invalid document_id"}), 400

        # verify document ownership
        try:
            with get_db_context() as db:
                document = db.query(Document).filter(
                    Document.id == document_id,
                    Document.user_id == user_id,
                ).first()
        except Exception as e:
            return jsonify({"error": f"database error: {str(e)}"}), 500

        if not document:
            return jsonify({"error": "document not found"}), 404

        # process question
        try:
            answer, source_chunks = answer_question(question, document_id)
        except Exception as e:
            return jsonify({"error": f"failed to answer question: {str(e)}"}), 500

        if not answer or not source_chunks:
            return jsonify({"error": "couldn't answer question"}), 400

        sources = []
        for doc in source_chunks:
            text = getattr(doc, "page_content", "")
            metadata = getattr(doc, "metadata", {}) or {}
            page = metadata.get("page") if isinstance(metadata, dict) else None
            sources.append({"text": text, "page": page})

        sources_str = json.dumps(sources)

        new_chat = ChatHistory(
            question=question,
            answer=answer,
            sources=sources_str,
            document_id=document_id,
            user_id=user_id,
        )

        try:
            with get_db_context() as db:
                db.add(new_chat)
                db.commit()
        except Exception as e:
            return jsonify({"error": f"failed to save chat history: {str(e)}"}), 500

        return jsonify({"answer": answer, "sources": sources}), 200

    except Exception as e:
        return jsonify({"error": f"server error: {str(e)}"}), 500

@app.route("/documents/history", methods=["GET"]) 
def history():
    token = request.headers.get("Authorization")
    user_id = verify_token(token)
    if not user_id:
        return jsonify({"error": "invalid credentials"}), 401

    try:
        with get_db_context() as db:
            chat_history = db.query(ChatHistory).filter(ChatHistory.user_id == user_id).all()
    except Exception as e:
        return jsonify({"error": f"database error: {str(e)}"}), 500

    return jsonify([
        {
            "question": chat.question,
            "answer": chat.answer,
            "sources": chat.sources,
            "asked_at": chat.asked_at.isoformat() if chat.asked_at else None,
            "document_id": chat.document_id
        }
        for chat in chat_history
    ]), 200

@app.route("/documents", methods=["GET"])
def get_documents():
    token = request.headers.get("Authorization")
    user_id = verify_token(token)
    if not user_id:
        return jsonify({"error": "invalid token"}), 401

    try:
        with get_db_context() as db:
            documents = db.query(Document).filter(Document.user_id == user_id).all()
    except Exception as e:
        return jsonify({"error": f"database error: {str(e)}"}), 500

    return jsonify([
        {
            "id": doc.id,
            "filename": doc.filename,
            "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None
        }
        for doc in documents
    ]), 200

@app.route("/documents/<int:document_id>", methods=["DELETE"])
def delete_document(document_id):
    token = request.headers.get("Authorization")
    user_id = verify_token(token)
    if not user_id:
        return jsonify({"error": "invalid token"}), 401

    try:
        with get_db_context() as db:
            document = db.query(Document).filter(
                Document.id == document_id,
                Document.user_id == user_id
            ).first()

            if not document:
                return jsonify({"error": "document not found"}), 404

            db.query(ChatHistory).filter(ChatHistory.document_id == document_id).delete()
            db.delete(document)

        if document.filepath and os.path.isfile(document.filepath):
            try:
                os.remove(document.filepath)
            except Exception as e:
                print(f"Failed to remove document file: {e}")

        return jsonify({"message": "Document deleted"}), 200
    except Exception as e:
        return jsonify({"error": f"failed to delete document: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
    
