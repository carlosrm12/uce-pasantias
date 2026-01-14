import pandas as pd
from fpdf import FPDF
from app.dao.factory import UCEFactory
import os

def generate_combined_report() -> str:
    """
    Genera un PDF combinando datos de SQL y NoSQL.
    Retorna la ruta del archivo generado.
    Fuente: Sección 6.5 del informe.
    """
    factory = UCEFactory()
    
    try:
        # 1. Obtener Datos SQL (Estudiantes)
        student_dao = factory.get_student_dao()
        students_list = student_dao.get_all()
        # Convertir a DataFrame de Pandas
        students_df = pd.DataFrame(students_list)

        # 2. Obtener Datos Mongo (Oportunidades)
        opp_dao = factory.get_opportunity_dao()
        opp_list = opp_dao.get_all()
        
        # Aplanar estructura JSON anidada (ej. requirements)
        # Fuente: Sección 6.5 [cite: 338]
        if opp_list:
            opportunities_df = pd.json_normalize(opp_list)
        else:
            opportunities_df = pd.DataFrame()

        # 3. Generar PDF con FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt="Reporte Integrado UCE (Poliglota)", ln=1, align="C")
        
        # Sección SQL
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt=f"Estudiantes Registrados (Origen: PostgreSQL)", ln=1)
        pdf.set_font("Arial", size=10)
        
        if not students_df.empty:
            for index, row in students_df.iterrows():
                line = f"ID: {row['id']} | {row['name']} | GPA: {row['gpa']} | Dept: {row['department']}"
                pdf.cell(0, 10, txt=line, ln=1)
        else:
            pdf.cell(0, 10, txt="No hay estudiantes registrados.", ln=1)

        pdf.ln(10) # Salto de línea

        # Sección NoSQL
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt=f"Oportunidades Disponibles (Origen: MongoDB)", ln=1)
        pdf.set_font("Arial", size=10)

        if not opportunities_df.empty:
            for index, row in opportunities_df.iterrows():
                # Manejo seguro de columnas dinámicas
                title = row.get('title', 'N/A')
                company = row.get('company_name', 'N/A')
                # Pandas usa NaN para valores faltantes, lo convertimos a string
                pdf.cell(0, 10, txt=f"* {title} ({company})", ln=1)
        else:
            pdf.cell(0, 10, txt="No hay oportunidades registradas.", ln=1)

        
        # Guardar archivo
        # CAMBIO: Usamos ruta relativa o absoluta segura (/tmp)
        # Como estamos en /code, guardar en "reporte_uce.pdf" lo deja en la raíz del proyecto
        output_path = "reporte_uce.pdf" 
        
        pdf.output(output_path)
        
        # IMPORTANTE: Devolver la ruta absoluta para que Flask la encuentre
        return os.path.abspath(output_path)

    finally:
        factory.close()