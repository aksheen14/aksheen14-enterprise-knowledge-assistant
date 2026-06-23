from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key= True)
    email = Column(String(255), unique = True, nullable=False)
    hashed_password = Column(String(255), nullable = False)
    created_at = Column(DateTime, default=datetime.utcnow)

    documents = relationship("Document", back_populates = "owner")
    chats = relationship("ChatHistory", back_populates = "user")

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key= True)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates = "documents")
    chat = relationship("ChatHistory", back_populates = "document")

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key= True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources = Column(Text)
    asked_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    document_id = Column(Integer, ForeignKey("documents.id"))

    user = relationship("User", back_populates = "chats")
    document = relationship("Document", back_populates = "chat")
