from abc import ABC, abstractmethod
from typing import Any, List, Optional, Dict

class GenericDAO(ABC):
    """
    Interfaz base que define las operaciones CRUD estándar.
    Fuente: Sección 4.2.1 del informe.
    """
    
    @abstractmethod
    def create(self, data: Dict[str, Any]) -> Any:
        """
        Crea un nuevo registro/documento.
        :param data: Diccionario con los datos a persistir.
        :return: El ID del objeto creado o el objeto mismo.
        """
        pass

    @abstractmethod
    def get(self, id: Any) -> Optional[Dict[str, Any]]:
        """
        Obtiene un registro por su ID único.
        :param id: Puede ser un int (SQL) o str/ObjectId (Mongo).
        :return: Diccionario con los datos o None si no existe.
        """
        pass

    @abstractmethod
    def get_all(self) -> List[Dict[str, Any]]:
        """
        Recupera todos los registros como una lista de diccionarios.
        Optimizado para exportación de datos (Pandas).
        Fuente: Sección 6.5
        """
        pass

        
    @abstractmethod
    def update(self, id: Any, data: Dict[str, Any]) -> bool:
        """
        Actualiza un registro existente.
        """
        pass

    @abstractmethod
    def delete(self, id: Any) -> bool:
        """
        Elimina un registro por su ID.
        """
        pass


class StudentDAO(GenericDAO):
    """
    Interfaz específica para operaciones de Estudiantes (Dominio SQL).
    """
    # Aquí podríamos agregar métodos como get_by_email(email)
    pass


class OpportunityDAO(GenericDAO):
    """
    Interfaz específica para operaciones de Oportunidades (Dominio NoSQL).
    """
    # Aquí podríamos agregar métodos como search_by_tags(tags)
    pass


class ApplicationDAO(GenericDAO):
    """
    Interfaz para las solicitudes de pasantía (Dominio SQL - Trazabilidad).
    Fuente: Sección 4.2.1
    """
    pass


class AbstractDAOFactory(ABC):
    """
    La Fábrica Abstracta.
    Declara métodos para crear DAOs específicos sin especificar sus clases concretas.
    Fuente: Sección 4.2.1 y 6.3 del informe.
    """

    @abstractmethod
    def get_student_dao(self) -> StudentDAO:
        """Retorna un DAO capaz de manejar estudiantes (PostgreSQL)"""
        pass

    @abstractmethod
    def get_opportunity_dao(self) -> OpportunityDAO:
        """Retorna un DAO capaz de manejar oportunidades (MongoDB)"""
        pass

    @abstractmethod
    def get_application_dao(self) -> ApplicationDAO:
        """Retorna un DAO capaz de manejar solicitudes (PostgreSQL)"""
        pass