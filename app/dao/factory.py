import os
from app.dao.interfaces import AbstractDAOFactory, StudentDAO, OpportunityDAO, ApplicationDAO, UserDAO
from app.dao.postgres_impl import PostgresStudentDAO, PostgresApplicationDAO, PostgresUserDAO
from app.dao.mongo_impl import MongoOpportunityDAO
from app.db import SessionLocal
# Eliminamos get_mongo_db de aquí porque ya no lo usaremos globalmente

class UCEFactory(AbstractDAOFactory):
    """
    La Fábrica Híbrida Concreta.
    Es el único punto de entrada para la lógica de negocio.
    """

    def __init__(self):
        """
        Al instanciar la fábrica, abrimos solo la sesión SQL.
        La conexión a Mongo se delegará al DAO específico para manejar Timeouts.
        """
        # 1. Conexión SQL (PostgreSQL) - Esta sí la mantenemos abierta
        self._sql_session = SessionLocal()
        
        # 2. Conexión NoSQL (MongoDB)
        # YA NO conectamos aquí. Si lo hacemos, la fábrica se bloquearía 30s si Mongo cae.
        pass

    def get_user_dao(self) -> UserDAO:
        """
        Gestiona usuarios en PostgreSQL (Auth Seguro).
        """
        return PostgresUserDAO(self._sql_session)

    def get_student_dao(self) -> StudentDAO:
        """
        Inyecta la sesión SQL en el DAO de Estudiantes.
        """
        return PostgresStudentDAO(self._sql_session)

    def get_opportunity_dao(self) -> OpportunityDAO:
        """
        Inyecta la URI de conexión en el DAO de Oportunidades.
        El DAO se encargará de crear la conexión 'Fail Fast' (2 segundos).
        """
        # Obtenemos la URI del entorno o usamos la default de Docker
        mongo_uri = os.getenv("MONGO_URI", "mongodb://mongo:27017/")
        
        # Pasamos el STRING, no el objeto de base de datos
        return MongoOpportunityDAO(mongo_uri)

    def get_application_dao(self) -> ApplicationDAO:
        # Importación local para evitar dependencias circulares si las hubiera
        from app.dao.postgres_impl import PostgresApplicationDAO
        return PostgresApplicationDAO(self._sql_session)

    def close(self):
        """
        Método de limpieza para cerrar la sesión SQL.
        """
        self._sql_session.close()

    def __enter__(self):
        """Permite usar la fábrica con 'with' statement"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()