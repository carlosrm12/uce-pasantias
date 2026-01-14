from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

# Clase base de SQLAlchemy
Base = declarative_base()

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

    # Relación: Un estudiante tiene muchas solicitudes
    applications = relationship("ApplicationModel", back_populates="student")

class ApplicationModel(Base):
    """
    Modelo ORM para la tabla 'applications'.
    Garantiza el cumplimiento ACID en cambios de estado.
    Fuente: Sección 3.1 (Punto 2)
    """
    __tablename__ = 'applications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    
    # REFERENCIA POLÍGLOTA:
    # Guardamos el ID de MongoDB aquí como un string simple.
    # No hay FK de base de datos hacia Mongo, la integridad es lógica.
    # Fuente: Sección 3.3 (Desafíos de Integración)
    opportunity_ref_id = Column(String(50), nullable=False)
    
    status = Column(String(20), default="Enviada") # Enviada, En Revisión, Aceptada
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("StudentModel", back_populates="applications")