import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models.sql import Base
from pymongo import MongoClient

# --- CONFIGURACIÓN SQL (POSTGRES) ---
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/ucedb")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- CONFIGURACIÓN NOSQL (MONGO) ---
# Fuente: Sección 6.3 (Paso 2)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
mongo_client = MongoClient(MONGO_URI)

def get_mongo_db():
    """Retorna la base de datos específica para la plataforma"""
    return mongo_client["uce_internship_db"]