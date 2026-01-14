from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
from flask_login import UserMixin

@dataclass
class UserDTO(UserMixin):
    """
    DTO que representa al usuario logueado.
    Hereda de UserMixin para que Flask-Login pueda manejarlo (is_authenticated, etc).
    """
    id: int
    email: str
    name: str
    role: str
    
    # Flask-Login requiere que el ID sea string
    def get_id(self):
        return str(self.id)

@dataclass
class StudentDTO:
    """
    Transporta datos de estudiantes desde PostgreSQL hacia la aplicación.
    Fuente: Sección 4.2.2
    """
    id: int
    name: str
    email: str
    gpa: float
    department: str  # Carrera/Departamento

@dataclass
class OpportunityDTO:
    """
    Transporta datos de oportunidades desde MongoDB.
    Nota: 'metadata' maneja la variabilidad del esquema NoSQL.
    Fuente: Sección 4.2.2
    """
    id: str  # Será el ObjectId de Mongo convertido a string
    title: str
    company_name: str
    description: str
    # Diccionario flexible para requisitos variables (ej: nivel de seguridad, lenguajes)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ApplicationDTO:
    """
    Transporta el estado de una solicitud (Trazabilidad).
    Vincula SQL (Student) con NoSQL (Opportunity).
    Fuente: Sección 3.3 (Desafíos de Integración)
    """
    id: int
    student_id: int
    opportunity_ref_id: str  # Referencia al ID de MongoDB
    status: str  # Enviada, En Revisión, Aceptada
    created_at: datetime

@dataclass
class CombinedReportDTO:
    """
    DTO especial para el reporte final que fusiona ambos mundos.
    Fuente: Sección 4.2.2 y 6.5
    """
    student_name: str
    student_gpa: float
    opportunity_title: str
    company: str
    application_status: str