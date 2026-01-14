from app.dao.interfaces import AbstractDAOFactory, StudentDAO, OpportunityDAO, ApplicationDAO
from app.dao.postgres_impl import PostgresStudentDAO, PostgresApplicationDAO
from app.dao.mongo_impl import MongoOpportunityDAO
from app.db import SessionLocal, get_mongo_db

class UCEFactory(AbstractDAOFactory):
    """
    La Fábrica Híbrida Concreta.
    Es el único punto de entrada para la lógica de negocio.
    Oculta la complejidad de instanciar conexiones SQL y NoSQL.
    Fuente: Sección 4.2.3 y 6.3 (Paso 2)
    """

    def __init__(self):
        """
        Al instanciar la fábrica, abrimos canales a ambas bases de datos.
        """
        # 1. Conexión SQL (PostgreSQL)
        self._sql_session = SessionLocal()
        
        # 2. Conexión NoSQL (MongoDB)
        self._mongo_db = get_mongo_db()

    def get_student_dao(self) -> StudentDAO:
        """
        Inyecta la sesión SQL en el DAO de Estudiantes.
        Fuente: Sección 6.3 (cite: 260-261)
        """
        return PostgresStudentDAO(self._sql_session)

    def get_opportunity_dao(self) -> OpportunityDAO:
        """
        Inyecta la colección de Mongo en el DAO de Oportunidades.
        Fuente: Sección 6.3 (cite: 262-264)
        """
        return MongoOpportunityDAO(self._mongo_db)

    def get_application_dao(self) -> ApplicationDAO:
        """
        Inyecta la sesión SQL en el DAO de Solicitudes (Trazabilidad).
        """
        return PostgresApplicationDAO(self._sql_session)

    def close(self):
        """
        Método de limpieza para cerrar la sesión SQL.
        Crucial para evitar fugas de memoria en producción.
        """
        self._sql_session.close()

    def __enter__(self):
        """Permite usar la fábrica con 'with' statement"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()