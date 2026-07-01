from flask import Flask, jsonify, request, Response, stream_with_context, current_app
from werkzeug.utils import secure_filename
from database import init_db, get_db_context
from models import User, Document, ChatHistory
from auth import register_user, login_user, verify_token
from rag import load_and_chunk, embed_and_store, answer_question
import os
import json
from flask_cors import CORS
from langchain_core.messages import HumanMessage, AIMessage

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
                db.flush()
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
        
        #fetch history
        try:
            with get_db_context() as db:
                chat_history = db.query(ChatHistory).filter(
                    ChatHistory.document_id == document_id,
                    ChatHistory.user_id == user_id
                ).order_by(ChatHistory.asked_at.desc()).limit(5).all()
        except Exception as e:
            return jsonify({"error": f"database error: {str(e)}"}), 500
        
        chat_history.reverse()

        #format for langchain
        formatted_history = []
        for chat in chat_history:
            formatted_history.append(HumanMessage(content=chat.question))
            formatted_history.append(AIMessage(content=chat.answer))

        # process question
        try:
            answer, source_chunks = answer_question(question, document_id, chat_history=formatted_history)
        except Exception as e:
            return jsonify({"error": f"failed to answer question: {str(e)}"}), 500

        if not answer or not source_chunks:
            return jsonify({"error": f"couldn't answer question: {str(e)}"}), 400

        sources = []
        for doc in source_chunks:
            text = getattr(doc, "page_content", "")
            metadata = getattr(doc, "metadata", {}) or {}
            page = metadata.get("page") if isinstance(metadata, dict) else None
            sources.append({"text": text, "page": page})

        sources_str = json.dumps(sources)

        app = current_app._get_current_object()

        def generate():
            full_ai_answer = ""
            yield json.dumps({"type": "sources", "data": sources}) + "\n\n"

            for chunk in answer:
                full_ai_answer += chunk
                yield json.dumps({"type": "chunk", "data": chunk}) + "\n\n"

            new_chat = ChatHistory(
                question=question,
                answer=full_ai_answer,
                sources=sources_str,
                document_id=document_id,
                user_id=user_id,
            )
            with app.app_context():
                try:
                    # Use your existing DB logic here
                    with get_db_context() as db:
                        db.add(new_chat)
                        db.commit()
                except Exception as e:
                    print(f"Database save failed inside stream: {e}")
                return Response(
                    stream_with_context(generate()),
                    mimetype="text/event-stream"
                )

        return Response(
            stream_with_context(generate()), 
            mimetype="text/event-stream"
        )

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
            results = [
                {
                    "question": chat.question,
                    "answer": chat.answer,
                    "sources": chat.sources,
                    "asked_at": chat.asked_at.isoformat() if chat.asked_at else None,
                    "document_id": chat.document_id
                }
                for chat in chat_history
            ]
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": f"database error: {str(e)}"}), 500

    

@app.route("/documents", methods=["GET"])
def get_documents():
    token = request.headers.get("Authorization")
    user_id = verify_token(token)
    if not user_id:
        return jsonify({"error": "invalid token"}), 401

    try:
        with get_db_context() as db:
            documents = db.query(Document).filter(Document.user_id == user_id).all()
            
            results = [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None
                }
                for doc in documents
            ]
            
    except Exception as e:
        return jsonify({"error": f"database error: {str(e)}"}), 500

    return jsonify(results), 200

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

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
