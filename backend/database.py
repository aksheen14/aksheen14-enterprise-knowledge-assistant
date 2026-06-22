import os
from sqlalchemy import create_engine
from models import Base
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker, declarative_base


load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set — check your .env file")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set — check your .env file")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
