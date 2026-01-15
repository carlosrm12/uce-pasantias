Proyecto Arquitectura de Software - Plataforma UCE
Este proyecto implementa una arquitectura híbrida utilizando el patrón de diseño Abstract Factory para gestionar la persistencia políglota (PostgreSQL y MongoDB) dentro de un entorno contenedorizado (Docker).

📋 Requisitos Previos
Docker Desktop instalado y corriendo.

Git (Opcional, para clonar).

🚀 Instrucciones de Despliegue
Descomprimir el archivo del proyecto.

Abrir una terminal en la carpeta raíz del proyecto.

Ejecutar el siguiente comando para construir y levantar los servicios:

docker-compose up --build

Esperar a que la terminal muestre el mensaje: Listening at: http://0.0.0.0:5000.

Abrir el navegador en: http://localhost:5000.

🏗️ Arquitectura y Patrones
1. Justificación de Bases de Datos
PostgreSQL (SQL): Se utiliza para datos estructurados y transaccionales críticos que requieren integridad referencial, específicamente: Usuarios, Estudiantes y Postulaciones.

MongoDB (NoSQL): Se utiliza para datos semi-estructurados o flexibles, específicamente: Oportunidades Laborales, permitiendo que cada oferta tenga requisitos dinámicos (JSON) sin alterar el esquema.

2. Patrón Abstract Factory
El sistema utiliza una fábrica abstracta (UCEFactory) que desacopla la lógica de negocio de la implementación de la base de datos.

Interfaz: GenericDAO define el contrato (CRUD).

Implementación: PostgresStudentDAO (SQL) y MongoOpportunityDAO (NoSQL) implementan la interfaz.

Uso: El controlador pide factory.get_student_dao() sin saber qué base de datos hay detrás.

📂 Estructura del Proyecto
/app/dao: Implementación de Patrones DAO y Factory.

/app/dto: Objetos de Transferencia de Datos (DTOs).

/app/models: Modelos de Base de Datos (SQLAlchemy).

/app/reporting: Motor de generación de reportes PDF combinados.
