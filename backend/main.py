from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename
from database import init_db, get_db
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
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email and password required"}), 400

    return register_user(email, password)

@app.route("/auth/login", methods=["POST"]) 

def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email and password required"}), 400

    return login_user(email, password)

@app.route("/documents/upload", methods=["POST"]) 
def upload_documents():
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
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    #chunk it
    chunks = load_and_chunk(filepath)

    #save to db
    db = next(get_db())
    new_document = Document(filename=filename, filepath=filepath ,user_id=user_id)
    db.add(new_document)
    db.commit()
    db.refresh(new_document)
    document_id = new_document.id

    #embed it
    embed_and_store(chunks, document_id)
    return jsonify({
        "message": "Document uploaded successfully",
        "document_id": document_id
    }), 201

@app.route("/documents/ask", methods=["POST"]) 
def ask_question():
    #validate user
    token = request.headers.get("Authorization")
    user_id = verify_token(token)
    if not user_id:
        return jsonify({"error": "invalid credentials"}), 401


    #get question and doc id
    data = request.json
    question = data.get("question")
    document_id = data.get("document_id")

    #process 
    answer, source_chunks = answer_question(question, document_id)
    sources_str = json.dumps([
        {
            "text": doc.page_content,
            "page": doc.metadata.get("page")
        }
        for doc in source_chunks
    ])

    #save it  
    db = next(get_db())
    new_chat = ChatHistory(
        question=question, 
        answer=answer, 
        sources=sources_str, 
        document_id=document_id, 
        user_id=user_id
    )
    db.add(new_chat)
    db.commit()

    return jsonify({
        "answer": answer,
        "sources": [
            {
                "text": doc.page_content,
                "page": doc.metadata.get("page")
            } 
            for doc in source_chunks
        ]
    }), 200

@app.route("/documents/history", methods=["GET"]) 
def history():
    token = request.headers.get("Authorization")
    user_id = verify_token(token)
    if not user_id:
        return jsonify({"error": "invalid credentials"}), 401


    db = next(get_db())
    chat_history = db.query(ChatHistory).filter(ChatHistory.user_id == user_id).all()
    
    return jsonify([
        {
            "question": chat.question,
            "answer": chat.answer,
            "sources": chat.sources,
            "asked_at": chat.asked_at.isoformat(),
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

    db = next(get_db())
    documents = db.query(Document).filter(Document.user_id == user_id).all()

    return jsonify([
        {
            "id": doc.id,
            "filename": doc.filename,
            "uploaded_at": doc.uploaded_at.isoformat()
        }
        for doc in documents
    ]), 200

if __name__ == "__main__":
    app.run(debug=True)
    
