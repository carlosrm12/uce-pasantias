from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.dao.interfaces import StudentDAO, ApplicationDAO
from app.models.sql import StudentModel, ApplicationModel
from app.dto.models import StudentDTO, ApplicationDTO

class PostgresStudentDAO(StudentDAO):
    """
    Implementación concreta para PostgreSQL.
    Fuente: Sección 6.3 (Paso 2)
    """
    def __init__(self, session: Session):
        self.session = session

    def create(self, data: Dict[str, Any]) -> StudentDTO:
        # Convertimos diccionario a Modelo ORM
        student = StudentModel(**data)
        self.session.add(student)
        self.session.commit()
        self.session.refresh(student)
        
        # Retornamos DTO, no el Modelo
        return StudentDTO(
            id=student.id,
            name=student.name,
            email=student.email,
            gpa=student.gpa,
            department=student.department
        )

    def get(self, id: Any) -> Optional[StudentDTO]:
        student = self.session.query(StudentModel).filter_by(id=id).first()
        if not student:
            return None
            
        return StudentDTO(
            id=student.id,
            name=student.name,
            email=student.email,
            gpa=student.gpa,
            department=student.department
        )

    def update(self, id: Any, data: Dict[str, Any]) -> bool:
        # Lógica de actualización estándar de SQLAlchemy
        rows = self.session.query(StudentModel).filter_by(id=id).update(data)
        self.session.commit()
        return rows > 0

    def delete(self, id: Any) -> bool:
        rows = self.session.query(StudentModel).filter_by(id=id).delete()
        self.session.commit()
        return rows > 0

class PostgresApplicationDAO(ApplicationDAO):
    """
    Implementación concreta para Solicitudes en PostgreSQL.
    Maneja la trazabilidad crítica.
    """
    def __init__(self, session: Session):
        self.session = session

    def create(self, data: Dict[str, Any]) -> ApplicationDTO:
        application = ApplicationModel(**data)
        self.session.add(application)
        self.session.commit()
        self.session.refresh(application)
        
        return ApplicationDTO(
            id=application.id,
            student_id=application.student_id,
            opportunity_ref_id=application.opportunity_ref_id,
            status=application.status,
            created_at=application.created_at
        )

    # ... (get, update, delete serían similares, omitidos por brevedad pero requeridos)
    def get(self, id: Any) -> Optional[ApplicationDTO]:
         app = self.session.query(ApplicationModel).filter_by(id=id).first()
         if not app: return None
         return ApplicationDTO(app.id, app.student_id, app.opportunity_ref_id, app.status, app.created_at)

    def update(self, id: Any, data: Dict[str, Any]) -> bool: return False # Placeholder
    def delete(self, id: Any) -> bool: return False # Placeholder