from typing import Dict, Any, Optional, List  
from sqlalchemy.orm import Session
from app.dao.interfaces import StudentDAO, ApplicationDAO, UserDAO
from app.models.sql import StudentModel, ApplicationModel, UserModel
from app.dto.models import StudentDTO, ApplicationDTO, UserDTO
from werkzeug.security import check_password_hash

class PostgresUserDAO(UserDAO):
    def __init__(self, session: Session):
        self.session = session

    def get_by_email(self, email: str) -> Optional[UserDTO]:
        user = self.session.query(UserModel).filter_by(email=email).first()
        if not user:
            return None
        return self._map_to_dto(user)

    def get(self, id: Any) -> Optional[UserDTO]:
        user = self.session.query(UserModel).filter_by(id=int(id)).first()
        if not user:
            return None
        return self._map_to_dto(user)
    
    def create(self, data: Dict[str, Any]) -> UserDTO:
        user = UserModel(**data)
        self.session.add(user)
        self.session.commit()
        return self._map_to_dto(user)

    def validate_login(self, email: str, password_plaintext: str) -> Optional[UserDTO]:
        """Verifica credenciales y retorna el usuario si son válidas"""
        user = self.session.query(UserModel).filter_by(email=email).first()
        if not user:
            return None
        
        if check_password_hash(user.password_hash, password_plaintext):
            return self._map_to_dto(user)
        return None

    # Helpers requeridos por GenericDAO
    def get_all(self): return [] # No necesario por ahora
    def update(self, id, data): pass
    def delete(self, id): pass

    def _map_to_dto(self, user: UserModel) -> UserDTO:
        return UserDTO(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role
        )

class PostgresApplicationDAO(GenericDAO):
    def __init__(self, session: Session):
        self.session = session

    def create(self, data: Dict[str, Any]) -> Any:
        # data espera: {'user_id': 1, 'opportunity_id': '65a...'}
        app = ApplicationModel(**data)
        self.session.add(app)
        self.session.commit()
        return app.id

    # Métodos obligatorios por la interfaz (los dejamos vacíos por ahora)
    def get(self, id): pass
    def get_all(self): pass
    def update(self, id, data): pass
    def delete(self, id): pass

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

    def get_all(self) -> List[Dict[str, Any]]:
        # Consulta masiva optimizada
        students = self.session.query(StudentModel).all()
        # Convertimos objetos SQLAlchemy a lista de diccionarios planos
        return [
            {
                "id": s.id,
                "name": s.name,
                "email": s.email,
                "gpa": s.gpa,
                "department": s.department
            }
            for s in students
        ]



    
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