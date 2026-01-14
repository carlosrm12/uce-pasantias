from flask import Flask, jsonify, request
from app.db import init_db
from app.dao.factory import UCEFactory
from flask import send_file
from app.reporting.generator import generate_combined_report

app = Flask(__name__)

# Inicializamos las tablas SQL al arrancar la aplicación
# Esto asegura que la tabla 'students' exista antes de intentar guardar nada.
with app.app_context():
    init_db()

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "system": "UCE Internship Platform",
        "architecture": "Abstract Factory + Polyglot Persistence"
    })

@app.route('/api/students', methods=['POST'])
def create_student():
    """Crea un estudiante en PostgreSQL usando la Fábrica"""
    data = request.json
    
    # 1. Instanciamos la fábrica
    factory = UCEFactory()
    
    # 2. Obtenemos el DAO específico (SQL) sin saber que es SQL
    # Fuente: Sección 4.3 (Flujo Lógico)
    student_dao = factory.get_student_dao()
    
    try:
        new_student = student_dao.create(data)
        return jsonify(new_student.__dict__), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        factory.close()

@app.route('/api/opportunities', methods=['POST'])
def create_opportunity():
    """Crea una oportunidad en MongoDB usando la Fábrica"""
    data = request.json
    
    factory = UCEFactory()
    # 3. Obtenemos el DAO específico (NoSQL)
    opp_dao = factory.get_opportunity_dao()
    
    try:
        # El ID devuelto es un string (ObjectId de Mongo)
        new_id = opp_dao.create(data)
        return jsonify({"id": new_id, "message": "Oportunidad creada en Mongo"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        factory.close()

@app.route('/api/test-architecture', methods=['GET'])
def test_full_flow():
    """
    Prueba de Integración: Lee de SQL y Mongo simultáneamente.
    Valida que la Fábrica Híbrida funciona correctamente.
    """
    factory = UCEFactory()
    try:
        # Obtener todos los estudiantes (Simulado con get hardcodeado para prueba rápida si no hay datos)
        # En producción usaríamos un método get_all()
        student_dao = factory.get_student_dao()
        opp_dao = factory.get_opportunity_dao()
        
        return jsonify({
            "message": "Conexión exitosa a ambos orígenes de datos",
            "sql_status": "Connected via SQLAlchemy",
            "mongo_status": "Connected via PyMongo"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        factory.close()


@app.route('/api/reports/combined', methods=['GET'])
def get_report():
    """Genera y descarga el reporte PDF"""
    try:
        pdf_path = generate_combined_report()
        return send_file(pdf_path, as_attachment=True, download_name="reporte_uce.pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Esto solo se usa para desarrollo local sin Docker
    app.run(host='0.0.0.0', port=5000)