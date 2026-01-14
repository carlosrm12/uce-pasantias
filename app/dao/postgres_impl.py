from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash

# Imports de Interfaces y Modelos
from app.dao.interfaces import StudentDAO, UserDAO, GenericDAO
from app.models.sql import StudentModel, ApplicationModel, UserModel
from app.dto.models import StudentDTO, UserDTO

class PostgresStudentDAO(StudentDAO):
    """
    Implementación para Estudiantes (Datos Académicos para reportes).
    """
    def __init__(self, session: Session):
        self.session = session

    def create(self, data: Dict[str, Any]) -> StudentDTO:
        student = StudentModel(**data)
        self.session.add(student)
        self.session.commit()
        return self._map_to_dto(student)

    def get(self, id: Any) -> Optional[StudentDTO]:
        student = self.session.query(StudentModel).filter_by(id=int(id)).first()
        if not student:
            return None
        return self._map_to_dto(student)
        
    def get_all(self) -> List[Dict[str, Any]]:
        # --- CORREGIDO: Esto devuelve ESTUDIANTES, no aplicaciones ---
        students = self.session.query(StudentModel).all()
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

    def update(self, id: Any, data: Dict[str, Any]) -> bool:
        return False

    def delete(self, id: Any) -> bool:
        return False

    def _map_to_dto(self, student: StudentModel) -> StudentDTO:
        return StudentDTO(
            id=student.id,
            name=student.name,
            email=student.email,
            gpa=student.gpa,
            department=student.department
        )

class PostgresUserDAO(UserDAO):
    """
    Implementación para Usuarios (Login y Auth).
    """
    def __init__(self, session: Session):
        self.session = session

    def get_by_email(self, email: str) -> Optional[UserDTO]:
        user = self.session.query(UserModel).filter_by(email=email).first()
        if not user:
            return None
        return self._map_to_dto(user)

    def validate_login(self, email: str, password_plaintext: str) -> Optional[UserDTO]:
        user = self.session.query(UserModel).filter_by(email=email).first()
        if not user:
            return None
        if check_password_hash(user.password_hash, password_plaintext):
            return self._map_to_dto(user)
        return None

    def create(self, data: Dict[str, Any]) -> UserDTO:
        user = UserModel(**data)
        self.session.add(user)
        self.session.commit()
        return self._map_to_dto(user)

    def get(self, id: Any) -> Optional[UserDTO]:
        user = self.session.query(UserModel).filter_by(id=int(id)).first()
        if not user:
            return None
        return self._map_to_dto(user)

    # Helpers de GenericDAO
    def get_all(self) -> List[Dict[str, Any]]: return []
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
    """
    Implementación para Postulaciones (Trazabilidad).
    """
    def __init__(self, session: Session):
        self.session = session

    def create(self, data: Dict[str, Any]) -> Any:
        app = ApplicationModel(**data)
        self.session.add(app)
        self.session.commit()
        return app.id

    # --- IMPLEMENTACIÓN OBLIGATORIA DE LA INTERFAZ ---
    
    def get(self, id: Any) -> Optional[Any]:
        return None

    def get_all(self) -> List[Dict[str, Any]]:
        # --- CORREGIDO: Aquí es donde va la lógica de APLICACIONES ---
        # 1. Consultamos la base de datos real
        apps = self.session.query(ApplicationModel).order_by(ApplicationModel.created_at.desc()).all()
        
        result = []
        for app in apps:
            # 2. Obtenemos datos del usuario gracias a la relación
            if app.user:
                user_info = f"{app.user.name} ({app.user.email})"
            else:
                user_info = "Usuario Desconocido"

            # 3. Construimos el diccionario para el Frontend
            result.append({
                "id": app.id,
                "student": user_info,
                "opportunity_id": app.opportunity_id,
                "status": app.status,
                "created_at": app.created_at.strftime("%Y-%m-%d %H:%M") 
            })
            
        return result

    def update(self, id: Any, data: Dict[str, Any]) -> bool:
        return False

    def delete(self, id: Any) -> bool:
        return False