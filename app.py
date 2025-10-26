import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import json
from supabase import create_client, Client
import base64
from fpdf import FPDF
import io

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Gestión de Cursos Online",
    page_icon=" 🎓 ",
    layout="wide"
)

# Configuración de Supabase
@st.cache_resource
def init_supabase():
    supabase_url = st.secrets["SUPABASE_URL"]
    supabase_key = st.secrets["SUPABASE_KEY"]
    return create_client(supabase_url, supabase_key)
supabase = init_supabase()

# Configuración n8n
N8N_WEBHOOK_URL = st.secrets["N8N_WEBHOOK_URL"]

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Reporte de Gestión de Cursos', 0, 1, 'C')
        self.ln(10)

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(5)

    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

def trigger_n8n_workflow(workflow_type, data):
    """Dispara workflows de n8n"""
    payload = {
        "workflow_type": workflow_type,
        "data": data
    }
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload)
        return response.status_code == 200
    except:
        return False

def get_courses():
    """Obtiene todos los cursos"""
    response = supabase.table('courses').select('*').eq('is_active', True).execute()
    return response.data

def get_students():
    """Obtiene todos los estudiantes"""
    response = supabase.table('students').select('*').execute()
    return response.data

def get_enrollments():
    """Obtiene todas las inscripciones"""
    response = supabase.table('enrollments').select('*, students(*), courses(*)').execute()
    return response.data

def get_exam_results():
    """Obtiene resultados de exámenes"""
    response = supabase.table('exam_results').select('*, exams(*), students(*)').execute()
    return response.data

def generate_pdf_report():
    """Genera reporte PDF con estadísticas"""
    pdf = PDFReport()
    pdf.add_page()

    # Estadísticas generales
    courses = get_courses()
    students = get_students()
    enrollments = get_enrollments()
    exam_results = get_exam_results()

    pdf.chapter_title("Estadísticas Generales")
    stats_text = f"""
    Total de Cursos: {len(courses)}
    Total de Estudiantes: {len(students)}
    Total de Inscripciones: {len(enrollments)}
    Tasa de Completación: {len([e for e in enrollments if e['completion_status'] == 'completed']) / len(enrollments) * 100 if enrollments else 0:.2f}%
    Promedio de Calificaciones: {sum([er['score'] for er in exam_results if er['score']]) / len(exam_results) if exam_results else 0:.2f}
    """
    pdf.chapter_body(stats_text)

    # Cursos más populares
    pdf.chapter_title("Cursos Más Populares")
    course_enrollments = {}
    for enrollment in enrollments:
        course_name = enrollment['courses']['name']
        course_enrollments[course_name] = course_enrollments.get(course_name, 0) + 1

    popular_courses = "\n".join([f"{course}: {count} estudiantes"
                                 for course, count in sorted(course_enrollments.items(),
                                                             key=lambda x: x[1], reverse=True)[:5]])
    pdf.chapter_body(popular_courses)

    return pdf

def main():
    st.title(" 🎓  Sistema de Gestión de Cursos Online")

    # Sidebar para navegación
    menu = st.sidebar.selectbox(
        "Menú Principal",
        ["Dashboard", "Gestión de Cursos", "Estudiantes", "Inscripciones", "Reportes", "Configuración"]
    )

    if menu == "Dashboard":
        show_dashboard()
    elif menu == "Gestión de Cursos":
        manage_courses()
    elif menu == "Estudiantes":
        manage_students()
    elif menu == "Inscripciones":
        manage_enrollments()
    elif menu == "Reportes":
        show_reports()
    elif menu == "Configuración":
        show_settings()

def show_dashboard():
    st.header(" 📊  Dashboard Principal")

    # Métricas clave
    col1, col2, col3, col4 = st.columns(4)

    courses = get_courses()
    students = get_students()
    enrollments = get_enrollments()
    exam_results = get_exam_results()

    with col1:
        st.metric("Total Cursos", len(courses))
    with col2:
        st.metric("Total Estudiantes", len(students))
    with col3:
        st.metric("Inscripciones Activas", len([e for e in enrollments if e['completion_status'] == 'in_progress']))
    with col4:
        avg_score = sum([er['score'] for er in exam_results if er['score']]) / len(exam_results) if exam_results else 0
        st.metric("Promedio Calificaciones", f"{avg_score:.2f}")

    # Gráficos
    col1, col2 = st.columns(2)

    with col1:
        # Distribución de estudiantes por curso
        if enrollments:
            course_data = {}
            for enrollment in enrollments:
                course_name = enrollment['courses']['name']
                course_data[course_name] = course_data.get(course_name, 0) + 1

            fig = px.pie(
                values=list(course_data.values()),
                names=list(course_data.keys()),
                title="Distribución de Estudiantes por Curso"
            )
            st.plotly_chart(fig)

    with col2:
        # Progreso de estudiantes
        if enrollments:
            status_data = {}
            for enrollment in enrollments:
                status = enrollment['completion_status']
                status_data[status] = status_data.get(status, 0) + 1

            fig = px.bar(
                x=list(status_data.keys()),
                y=list(status_data.values()),
                title="Estado de Completación de Cursos"
            )
            st.plotly_chart(fig)

    # Últimas inscripciones
    st.subheader("Últimas Inscripciones")
    if enrollments:
        recent_enrollments = sorted(enrollments, key=lambda x: x['enrollment_date'], reverse=True)[:10]
        enrollment_df = pd.DataFrame([{
            'Estudiante': f"{e['students']['first_name']} {e['students']['last_name']}",
            'Curso': e['courses']['name'],
            'Fecha': e['enrollment_date'],
            'Progreso': f"{e['progress_percentage']}%"
        } for e in recent_enrollments])
        st.dataframe(enrollment_df)

def manage_courses():
    st.header(" 📚  Gestión de Cursos")

    tab1, tab2, tab3 = st.tabs(["Ver Cursos", "Crear Curso", "Módulos"])

    with tab1:
        courses = get_courses()
        if courses:
            for course in courses:
                with st.expander(f"{course['name']} - ${course['price']}"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Descripción:** {course['description']}")
                        st.write(f"**Duración:** {course['duration_days']} días")
                    with col2:
                        if st.button("Eliminar", key=f"del_{course['id']}"):
                            supabase.table('courses').update({'is_active': False}).eq('id', course['id']).execute()
                            st.success("Curso eliminado")
                            st.rerun()

    with tab2:
        with st.form("crear_curso"):
            name = st.text_input("Nombre del Curso")
            description = st.text_area("Descripción")
            price = st.number_input("Precio", min_value=0.0, step=10.0)
            duration = st.number_input("Duración (días)", min_value=1, step=1)

            if st.form_submit_button("Crear Curso"):
                new_course = {
                    'name': name,
                    'description': description,
                    'price': price,
                    'duration_days': duration
                }
                supabase.table('courses').insert(new_course).execute()
                st.success("Curso creado exitosamente")

    with tab3:
        st.subheader("Gestión de Módulos")
        courses = get_courses()
        if courses:
            selected_course = st.selectbox("Seleccionar Curso",
                                           [f"{c['id']} - {c['name']}" for c in courses])
            course_id = selected_course.split(' - ')[0]

            # Aquí iría la gestión de módulos específica
            st.info("La gestión detallada de módulos se implementaría aquí.")

def manage_students():
    st.header(" 👥  Gestión de Estudiantes")

    students = get_students()
    if students:
        df = pd.DataFrame(students)
        st.dataframe(df[['first_name', 'last_name', 'email', 'subscription_tier', 'created_at']])

    # Formulario para agregar estudiante
    with st.form("agregar_estudiante"):
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("Nombre")
            email = st.text_input("Email")
        with col2:
            last_name = st.text_input("Apellido")
            subscription = st.selectbox("Tipo de Suscripción", ["basic", "premium", "enterprise"])

        if st.form_submit_button("Agregar Estudiante"):
            new_student = {
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'subscription_tier': subscription
            }
            supabase.table('students').insert(new_student).execute()
            st.success("Estudiante agregado exitosamente")

def manage_enrollments():
    st.header(" 🎫  Gestión de Inscripciones")

    # Formulario para nueva inscripción
    with st.form("nueva_inscripcion"):
        students = get_students()
        courses = get_courses()

        col1, col2 = st.columns(2)
        with col1:
            student_options = [f"{s['id']} - {s['first_name']} {s['last_name']}" for s in students]
            selected_student = st.selectbox("Estudiante", student_options)
        with col2:
            course_options = [f"{c['id']} - {c['name']}" for c in courses]
            selected_course = st.selectbox("Curso", course_options)

        if st.form_submit_button("Inscribir Estudiante"):
            student_id = selected_student.split(' - ')[0]
            course_id = selected_course.split(' - ')[0]

            new_enrollment = {
                'student_id': student_id,
                'course_id': course_id
            }

            # Disparar workflow de n8n para inscripción automática
            if trigger_n8n_workflow('enrollment', new_enrollment):
                st.success("Inscripción procesada exitosamente")
            else:
                st.error("Error en el proceso de inscripción")

    # Lista de inscripciones
    enrollments = get_enrollments()
    if enrollments:
        enrollment_df = pd.DataFrame([{
            'ID': e['id'],
            'Estudiante': f"{e['students']['first_name']} {e['students']['last_name']}",
            'Curso': e['courses']['name'],
            'Fecha': e['enrollment_date'],
            'Progreso': f"{e['progress_percentage']}%",
            'Estado': e['completion_status']
        } for e in enrollments])
        st.dataframe(enrollment_df)

def show_reports():
    st.header(" 📈  Reportes y Estadísticas")

    # Generar estadísticas descriptivas
    enrollments = get_enrollments()
    exam_results = get_exam_results()

    col1, col2 = st.columns(2)

    with col1:
        # Gráfico de progreso general
        if enrollments:
            progress_data = [e['progress_percentage'] for e in enrollments]
            fig = px.histogram(progress_data, nbins=20, title="Distribución del Progreso")
            st.plotly_chart(fig)

    with col2:
        # Rendimiento en exámenes
        if exam_results:
            scores = [er['score'] for er in exam_results if er['score']]
            fig = px.box(scores, title="Distribución de Calificaciones")
            st.plotly_chart(fig)

    # Reporte detallado
    st.subheader("Reporte Detallado")

    if st.button("Generar Reporte PDF"):
        pdf = generate_pdf_report()

        # Guardar PDF en buffer
        pdf_buffer = io.BytesIO()
        pdf.output(pdf_buffer)
        pdf_buffer.seek(0)

        # Crear botón de descarga
        b64 = base64.b64encode(pdf_buffer.read()).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="reporte_cursos.pdf">Descargar Reporte PDF</a>'
        st.markdown(href, unsafe_allow_html=True)

def show_settings():
    st.header(" ⚙️  Configuración")

    st.subheader("Configuración de n8n")
    webhook_url = st.text_input("URL Webhook n8n", value=N8N_WEBHOOK_URL)

    st.subheader("Configuración de Supabase")
    st.info("Las credenciales de Supabase se configuran mediante secrets de Streamlit")

if __name__ == "__main__":
    main()