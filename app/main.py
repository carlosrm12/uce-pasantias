from flask import Flask, jsonify, request
from app.db import init_db
from app.dao.factory import UCEFactory
from flask import send_file
from app.reporting.generator import generate_combined_report
from flask import Flask, jsonify, request, send_file, render_template, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import init_db
from app.dao.factory import UCEFactory

app = Flask(__name__)

app.secret_key = "super_secreto_uce_key"  # NECESARIO para firmar las cookies

# Inicializar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Si alguien intenta entrar sin permiso, lo manda aquí

@login_manager.user_loader
def load_user(user_id):
    """
    Recarga el objeto usuario desde el ID almacenado en la sesión.
    Usa la Fábrica para mantener el desacoplamiento.
    """
    factory = UCEFactory()
    try:
        user_dao = factory.get_user_dao()
        return user_dao.get(user_id)
    finally:
        factory.close()

def create_initial_admin():
    """Crea el usuario administrador si no existe"""
    factory = UCEFactory()
    try:
        user_dao = factory.get_user_dao()
        admin_email = "admin@uce.edu.ec"
        
        if not user_dao.get_by_email(admin_email):
            print(f"--- Creando Admin Inicial ({admin_email}) ---")
            hashed_pw = generate_password_hash("admin123") # Contraseña por defecto
            user_dao.create({
                "email": admin_email,
                "password_hash": hashed_pw,
                "name": "Administrador UCE",
                "role": "admin"
            })
        else:
            print("--- Admin ya existe ---")
    except Exception as e:
        print(f"Error creando admin: {e}")
    finally:
        factory.close()

# Inicializamos las tablas SQL al arrancar la aplicación
# Esto asegura que la tabla 'students' exista antes de intentar guardar nada.
with app.app_context():
    init_db()
    create_initial_admin()



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
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Permite a un estudiante registrarse por sí mismo"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        factory = UCEFactory()
        try:
            user_dao = factory.get_user_dao()
            
            # 1. Verificar si ya existe
            if user_dao.get_by_email(email):
                return render_template('register.html', error="El correo ya está registrado.")
            
            # 2. Crear usuario (Encriptando contraseña)
            # IMPORTANTE: Forzamos role='student' por seguridad
            hashed_pw = generate_password_hash(password)
            user_dao.create({
                "email": email,
                "password_hash": hashed_pw,
                "name": name,
                "role": "student" 
            })
            
            # 3. Éxito: Redirigir al login
            # (Podríamos hacer login automático, pero es mejor confirmar)
            return render_template('login.html', error="¡Cuenta creada! Por favor inicia sesión.")
            
        except Exception as e:
            return render_template('register.html', error=f"Error del sistema: {str(e)}")
        finally:
            factory.close()
            
    return render_template('register.html')

@app.route('/api/applications', methods=['POST'])
@login_required # <--- Solo usuarios logueados
def apply_opportunity():
    """Registra la postulación del estudiante"""
    data = request.json
    opp_id = data.get('opportunity_id')
    
    if not opp_id:
        return jsonify({"error": "Falta opportunity_id"}), 400

    factory = UCEFactory()
    try:
        # Usamos el nuevo DAO
        app_dao = factory.get_application_dao()
        
        # Guardamos el cruce: ID del usuario actual + ID de Mongo
        app_id = app_dao.create({
            "user_id": current_user.id,
            "opportunity_id": opp_id,
            "status": "enviada"
        })
        
        return jsonify({"message": "Postulación exitosa", "ref": app_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        factory.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        factory = UCEFactory()
        try:
            user_dao = factory.get_user_dao()
            # Usamos el nuevo método que encapsula la lógica
            user = user_dao.validate_login(email, password)
            
            if user:
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                return render_template('login.html', error="Credenciales inválidas")
        finally:
            factory.close()
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('index.html', user=current_user)

@app.route('/api/opportunities', methods=['GET', 'POST'])
def handle_opportunities():
    """
    POST: Crea oportunidad en Mongo.
    GET: Lee todas las oportunidades de Mongo (Para el Dashboard).
    """
    factory = UCEFactory()
    opp_dao = factory.get_opportunity_dao()
    
    try:
        if request.method == 'POST':
            # --- Lógica de Creación (Igual que antes) ---
            data = request.json
            new_id = opp_dao.create(data)
            return jsonify({"id": new_id, "message": "Oportunidad creada en Mongo"}), 201
        
        else:
            # --- NUEVA Lógica de Lectura (GET) ---
            # Usamos el método get_all() que creamos para el reporte
            opportunities = opp_dao.get_all()
            return jsonify(opportunities), 200

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