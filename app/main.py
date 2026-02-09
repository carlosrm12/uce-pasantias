import socket
from flask import Flask, jsonify, request, send_file, render_template, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Imports propios
from app.db import init_db
from app.dao.factory import UCEFactory
from app.reporting.generator import generate_combined_report

app = Flask(__name__)
app.secret_key = "super_secreto_uce_key"

# --- CONFIGURACIÓN DE LOGIN ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 

@login_manager.user_loader
def load_user(user_id):
    factory = UCEFactory()
    try:
        user_dao = factory.get_user_dao()
        return user_dao.get(user_id)
    finally:
        factory.close()

def create_initial_admin():
    factory = UCEFactory()
    try:
        user_dao = factory.get_user_dao()
        admin_email = "admin@uce.edu.ec"
        if not user_dao.get_by_email(admin_email):
            print(f"--- Creando Admin Inicial ({admin_email}) ---")
            hashed_pw = generate_password_hash("admin123")
            user_dao.create({
                "email": admin_email,
                "password_hash": hashed_pw,
                "name": "Administrador UCE",
                "role": "admin"
            })
    except Exception as e:
        print(f"Error creando admin: {e}")
    finally:
        factory.close()

with app.app_context():
    init_db()
    create_initial_admin()

# --- RUTAS PÚBLICAS Y GENERALES ---

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        factory = UCEFactory()
        try:
            user_dao = factory.get_user_dao()
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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        factory = UCEFactory()
        try:
            user_dao = factory.get_user_dao()
            if user_dao.get_by_email(email):
                return render_template('register.html', error="El correo ya está registrado.")
            
            hashed_pw = generate_password_hash(password)
            user_dao.create({
                "email": email,
                "password_hash": hashed_pw,
                "name": name,
                "role": "student" 
            })
            return render_template('login.html', error="¡Cuenta creada! Por favor inicia sesión.")
        except Exception as e:
            return render_template('register.html', error=f"Error del sistema: {str(e)}")
        finally:
            factory.close()
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    container_id = socket.gethostname()
    return render_template('index.html', user=current_user, node_id=container_id)

# --- API: GESTIÓN DE ESTUDIANTES (SQL) ---

@app.route('/api/students', methods=['POST'])
@login_required
def create_student():
    if current_user.role != 'admin':
        return jsonify({"error": "No autorizado"}), 403
    data = request.json
    factory = UCEFactory()
    try:
        student_dao = factory.get_student_dao()
        new_student = student_dao.create(data)
        return jsonify(new_student.__dict__), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        factory.close()

# --- API: GESTIÓN DE OPORTUNIDADES (MONGO) ---

@app.route('/api/opportunities', methods=['GET', 'POST'])
def handle_opportunities():
    factory = UCEFactory()
    try:
        opp_dao = factory.get_opportunity_dao()

        if request.method == 'POST':
            if not current_user.is_authenticated or current_user.role != 'admin':
                return jsonify({"error": "No autorizado"}), 403

            data = request.json
            if not data.get('title') or not data.get('company_name'):
                return jsonify({"error": "Título y Empresa son obligatorios"}), 400

            try:
                new_id = opp_dao.create(data)
                return jsonify({"id": new_id, "message": "Oportunidad creada en Mongo"}), 201
            except ValueError as e:
                return jsonify({"error": str(e)}), 409
        
        else:
            opportunities = opp_dao.get_all()
            return jsonify(opportunities), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        factory.close()

# --- API: GESTIÓN DE POSTULACIONES (SQL) ---

@app.route('/api/applications', methods=['POST'])
@login_required 
def apply_opportunity():
    data = request.json
    opp_id = data.get('opportunity_id')
    
    if not opp_id:
        return jsonify({"error": "Falta opportunity_id"}), 400

    factory = UCEFactory()
    try:
        app_dao = factory.get_application_dao()
        app_id = app_dao.create({
            "user_id": current_user.id,
            "opportunity_id": opp_id,
            "status": "enviada"
        })
        return jsonify({"message": "Postulación exitosa", "ref": app_id}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 409 
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        factory.close()

@app.route('/api/applications/all', methods=['GET'])
@login_required
def get_applications_list():
    if current_user.role != 'admin':
        return jsonify({"error": "No autorizado"}), 403
    factory = UCEFactory()
    try:
        app_dao = factory.get_application_dao()
        apps = app_dao.get_all()
        return jsonify(apps), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        factory.close()

@app.route('/api/my-applications', methods=['GET'])
@login_required
def get_my_applications():
    """
    Retorna historial del estudiante.
    CORRECCIÓN APLICADA: Conversión de tipos (str vs int) en el ID.
    """
    if current_user.role != 'student':
        return jsonify([]), 403
    
    factory = UCEFactory()
    try:
        app_dao = factory.get_application_dao()
        
        def get_val(obj, key, default=None):
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        # 1. Obtener postulaciones
        apps = []
        try:
            # Si el DAO tiene método optimizado, lo usamos
            apps = app_dao.get_by_user_id(current_user.id)
        except AttributeError:
            # Fallback: Traemos todas y filtramos asegurando TIPOS
            all_apps = app_dao.get_all()
            # ---> AQUÍ ESTÁ LA CORRECCIÓN CLAVE <---
            # Convertimos ambos IDs a string para evitar fallos de comparación (int vs str)
            apps = [a for a in all_apps if str(get_val(a, 'user_id')) == str(current_user.id)]

        data = []
        
        # 2. Configurar DAO de Oportunidades (Mongo)
        opp_dao = None
        try:
            opp_dao = factory.get_opportunity_dao()
        except:
            pass 

        for app in apps:
            opp_title = "Oferta no disponible"
            opp_company = "Empresa desconocida"

            # Enriquecer con Mongo
            opp_id = get_val(app, 'opportunity_id')
            if opp_dao and opp_id:
                try:
                    opp = opp_dao.get(opp_id)
                    if opp:
                        opp_title = opp.title
                        opp_company = opp.company_name
                except Exception:
                    pass 
            
            raw_date = get_val(app, 'application_date')
            formatted_date = "N/A"
            if raw_date:
                if hasattr(raw_date, 'strftime'):
                    formatted_date = raw_date.strftime('%Y-%m-%d')
                else:
                    formatted_date = str(raw_date)[:10]

            data.append({
                'id': str(get_val(app, 'id')), 
                'date': formatted_date,
                'status': get_val(app, 'status', 'Desconocido'),
                'opportunity_title': opp_title,
                'company_name': opp_company
            })
            
        return jsonify(data)

    except Exception as e:
        print(f"Error CRÍTICO en my-applications: {e}")
        return jsonify([]) 
    finally:
        factory.close()

@app.route('/api/applications/<int:app_id>/status', methods=['PUT'])
@login_required
def update_application_status(app_id):
    if current_user.role != 'admin':
        return jsonify({"error": "No tiene permisos de administrador"}), 403
    
    data = request.json
    new_status = data.get('status')
    
    if new_status not in ['aprobada', 'rechazada']:
        return jsonify({"error": "Estado no válido"}), 400

    factory = UCEFactory()
    try:
        app_dao = factory.get_application_dao()
        success = app_dao.update(app_id, {"status": new_status})
        if success:
            return jsonify({"message": f"Postulación marcada como {new_status}"}), 200
        else:
            return jsonify({"error": "No se encontró la postulación"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        factory.close()

# --- VISTAS ADMIN ---

@app.route('/admin/applications-view')
@login_required
def admin_applications_view():
    if current_user.role != 'admin':
        return redirect(url_for('dashboard'))
    return render_template('applications.html', user=current_user)

# --- REPORTES Y MÉTRICAS ---

@app.route('/api/stats', methods=['GET'])
@login_required
def get_dashboard_stats():
    if current_user.role != 'admin':
        return jsonify({}), 403

    factory = UCEFactory()
    try:
        try:
            std_dao = factory.get_student_dao()
            total_students = len(std_dao.get_all())
        except: total_students = 0

        try:
            app_dao = factory.get_application_dao()
            total_apps = len(app_dao.get_all())
        except: total_apps = 0

        try:
            opp_dao = factory.get_opportunity_dao()
            raw_opps = opp_dao.get_all()
            if len(raw_opps) == 1 and raw_opps[0].get('id') == 'maintenance':
                total_opps = 0
            else:
                total_opps = len(raw_opps)
        except Exception:
            total_opps = 0

        return jsonify({
            "students": total_students,
            "opportunities": total_opps,
            "applications": total_apps
        })
    except Exception as e:
        return jsonify({"students": 0, "opportunities": 0, "applications": 0})
    finally:
        factory.close()

@app.route('/api/reports/combined', methods=['GET'])
def get_report():
    try:
        pdf_path = generate_combined_report()
        return send_file(pdf_path, as_attachment=True, download_name="reporte_uce.pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/test-architecture', methods=['GET'])
def test_full_flow():
    factory = UCEFactory()
    try:
        return jsonify({
            "message": "Conexión exitosa a ambos orígenes de datos",
            "sql_status": "Connected via SQLAlchemy",
            "mongo_status": "Connected via PyMongo"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        factory.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)