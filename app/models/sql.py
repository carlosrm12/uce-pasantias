from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

# Clase base de SQLAlchemy
Base = declarative_base()


class UserModel(Base):
    """
    Tabla de Usuarios para Autenticación.
    Fuente: Sección 3.1 (PostgreSQL para usuarios)
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=False) # Nunca guardamos texto plano
    name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False) # 'admin' o 'student'
    applications = relationship("ApplicationModel", backref="user")

class StudentModel(Base):
    """
    Modelo ORM para la tabla 'students'.
    Mantiene la integridad de los datos académicos.
    Fuente: Sección 3.1
    """
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    gpa = Column(Float, nullable=False)
    department = Column(String(50), nullable=False)




class ApplicationModel(Base):
    """
    Tabla de Trazabilidad: Vincula un Usuario SQL con una Oportunidad NoSQL.
    """
    __tablename__ = 'applications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False) # Quién aplicó
    opportunity_id = Column(String(50), nullable=False) # ID de Mongo (string)
    status = Column(String(20), default='pending') # pending, accepted, rejected
    created_at = Column(DateTime, default=datetime.utcnow)