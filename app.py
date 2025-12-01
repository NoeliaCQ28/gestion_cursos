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
import google.generativeai as genai
from PIL import Image

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

# Configuración de Gemini
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Falta la API Key de Google en los secrets.")

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
    
    st.write("Enviando este payload a n8n:", payload)

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

def get_exams():
    """Obtiene todos los exámenes con detalles del curso"""
    response = supabase.table('exams').select('*, course_modules(title, courses(name))').execute()
    return response.data

def get_modules(course_id):
    """Obtiene los módulos para un curso específico"""
    if not course_id:
        return []
    response = supabase.table('course_modules').select('*').eq('course_id', course_id).order('module_number').execute()
    return response.data

def get_exams_for_module(module_id):
    """Obtiene los exámenes para un módulo específico"""
    if not module_id:
        return []
    response = supabase.table('exams').select('*').eq('module_id', module_id).execute()
    return response.data

def main():
    st.title(" 🎓  Sistema de Gestión de Cursos Online")

    # Sidebar para navegación
    menu = st.sidebar.selectbox(
        "Menú Principal",
        ["Dashboard", "Gestión de Cursos", "Estudiantes", "Inscripciones", "Gestión de Exámenes", "Reportes", "Configuración"]
    )

    if menu == "Dashboard":
        show_dashboard()
    elif menu == "Gestión de Cursos":
        manage_courses()
    elif menu == "Estudiantes":
        manage_students()
    elif menu == "Inscripciones":
        manage_enrollments()
    elif menu == "Gestión de Exámenes":
        manage_exams()
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
        # Añadido .get('score') para evitar errores si la clave no existe
        avg_score = sum([er['score'] for er in exam_results if er.get('score')]) / len(exam_results) if exam_results else 0
        st.metric("Promedio Calificaciones", f"{avg_score:.2f}")

    # Gráficos
    col1, col2 = st.columns(2)

    with col1:
        # Distribución de estudiantes por curso
        if enrollments:
            course_data = {}
            for enrollment in enrollments:
                # Añadida comprobación por si el curso fue eliminado
                if enrollment.get('courses'):
                    course_name = enrollment['courses']['name']
                    course_data[course_name] = course_data.get(course_name, 0) + 1

            if course_data:
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
            
            if status_data:
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
        
        # Filtramos inscripciones que podrían tener datos nulos de student o course
        valid_enrollments = [
            e for e in recent_enrollments 
            if e.get('students') and e.get('courses')
        ]
        
        enrollment_df = pd.DataFrame([{
            'Estudiante': f"{e['students']['first_name']} {e['students']['last_name']}",
            'Curso': e['courses']['name'],
            'Fecha': e['enrollment_date'],
            'Progreso': f"{e['progress_percentage']}%"
        } for e in valid_enrollments])
        st.dataframe(enrollment_df)

def manage_courses():
    st.header(" 📚  Gestión de Cursos, Módulos y Exámenes")

    tab1, tab2, tab3 = st.tabs(["Ver Cursos", "Crear Curso", "Gestión de Módulos y Exámenes"])

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
                st.rerun()

    with tab3:
        st.subheader("Seleccionar Curso")
        courses = get_courses()
        if not courses:
            st.warning("Primero debes crear un curso en la pestaña 'Crear Curso'.")
            return

        course_options = {c['name']: c['id'] for c in courses}
        selected_course_name = st.selectbox("Selecciona un curso para gestionar", options=course_options.keys())
        selected_course_id = course_options[selected_course_name]

        st.divider()
        
        col_mod, col_exam = st.columns(2)

        with col_mod:
            st.subheader("Módulos del Curso")
            modules = get_modules(selected_course_id)
            if modules:
                for mod in modules:
                    st.markdown(f"**{mod['module_number']}. {mod['title']}** (ID: `{mod['id']}`)")
            else:
                st.info("Este curso aún no tiene módulos.")
            
            with st.expander("➕ Crear Nuevo Módulo"):
                with st.form("crear_modulo", clear_on_submit=True):
                    mod_title = st.text_input("Título del Módulo")
                    mod_number = st.number_input("Número de Módulo (Orden)", min_value=1, step=1)
                    mod_release = st.number_input("Día de Publicación (ej. 7)", min_value=0, step=1, help="0 = inmediato, 7 = 7 días después de la inscripción.")
                    
                    if st.form_submit_button("Crear Módulo"):
                        new_module = {
                            "course_id": selected_course_id,
                            "title": mod_title,
                            "module_number": mod_number,
                            "release_day": mod_release
                        }
                        supabase.table('course_modules').insert(new_module).execute()
                        st.success(f"Módulo '{mod_title}' creado.")
                        st.rerun()

        with col_exam:
            st.subheader("Exámenes del Curso")
            
            if not modules:
                st.warning("Crea un módulo primero para poder asignarle un examen.")
                return

            module_options = {f"{m['module_number']}. {m['title']}": m['id'] for m in modules}
            selected_module_name = st.selectbox("Selecciona un módulo para ver/añadir exámenes", options=module_options.keys())
            selected_module_id = module_options[selected_module_name]

            exams = get_exams_for_module(selected_module_id)
            if exams:
                for ex in exams:
                    st.markdown(f"**{ex['title']}** (ID: `{ex['id']}`)")
            else:
                st.info("Este módulo aún no tiene exámenes.")
            
            with st.expander("➕ Crear Nuevo Examen"):
                with st.form("crear_examen", clear_on_submit=True):
                    exam_title = st.text_input("Título del Examen")
                    exam_score = st.number_input("Puntaje para Aprobar (ej. 70)", min_value=0, max_value=100, value=70, step=5)
                    
                    # Para las preguntas usamos JSON
                    st.caption("Usa JSON para definir las preguntas y respuestas correctas.")
                    exam_questions = st.text_area("Preguntas (JSON)", height=200, 
                        value='[{"pregunta": "¿Qué es n8n?", "opciones": ["A", "B"], "respuesta_correcta": "A"}]')

                    if st.form_submit_button("Crear Examen"):
                        try:
                            questions_json = json.loads(exam_questions)
                        except json.JSONDecodeError:
                            st.error("Error: El formato de JSON para las preguntas no es válido.")
                            return
                        
                        new_exam = {
                            "module_id": selected_module_id,
                            "title": exam_title,
                            "questions": questions_json, # Guardamos el JSON
                            "passing_score": exam_score
                        }
                        supabase.table('exams').insert(new_exam).execute()
                        st.success(f"Examen '{exam_title}' creado.")
                        st.rerun()

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
        
        if not students or not courses:
            st.warning("Debe crear estudiantes y cursos antes de poder realizar una inscripción.")
            return

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
                st.rerun()
            else:
                st.error("Error en el proceso de inscripción")

    # Lista de inscripciones
    enrollments = get_enrollments()
    if enrollments:
        # Filtramos inscripciones que podrían tener datos nulos de student o course
        valid_enrollments = [
            e for e in enrollments 
            if e.get('students') and e.get('courses')
        ]
        
        enrollment_df = pd.DataFrame([{
            'ID': e['id'],
            'Estudiante': f"{e['students']['first_name']} {e['students']['last_name']}",
            'Curso': e['courses']['name'],
            'Fecha': e['enrollment_date'],
            'Progreso': f"{e['progress_percentage']}%",
            'Estado': e['completion_status']
        } for e in valid_enrollments])
        st.dataframe(enrollment_df)

def manage_exams():
    st.header("📝 Corrección de Exámenes con IA")

    students = get_students()
    exams = get_exams()

    if not students or not exams:
        st.warning("Asegúrate de tener estudiantes y exámenes creados para poder corregir.")
        return

    with st.form("corregir_examen"):
        # Select student
        student_options = [f"{s['id']} - {s['first_name']} {s['last_name']}" for s in students]
        selected_student = st.selectbox("Estudiante", student_options)
        
        # Select exam
        exam_options = [f"{e['id']} - {e['title']}" for e in exams]
        selected_exam = st.selectbox("Examen", exam_options)
        
        # Obtenemos el objeto de examen completo para acceder al JSON de 'questions'
        exam_obj = next(e for e in exams if e['id'] == selected_exam.split(' - ')[0])
        
        st.subheader("Preguntas del Examen (para referencia)")
        st.info("Las respuestas correctas están dentro de este JSON.")
        st.json(exam_obj['questions'])
        
        # Simular las respuestas del estudiante
        st.subheader("Subir Examen Resuelto")
        uploaded_file = st.file_uploader("Sube una imagen o PDF del examen resuelto", type=['png', 'jpg', 'jpeg', 'pdf'])
        
        if uploaded_file is not None:
            # Mostrar imagen si es imagen
            if uploaded_file.type.startswith('image'):
                image = Image.open(uploaded_file)
                st.image(image, caption='Examen subido', use_column_width=True)
            
            if st.form_submit_button("Corregir con IA"):
                if "GOOGLE_API_KEY" not in st.secrets:
                    st.error("No se ha configurado la API Key de Google.")
                    return

                student_id = selected_student.split(' - ')[0]
                
                with st.spinner("La IA está analizando y corrigiendo el examen..."):
                    try:
                        # Preparar el prompt
                        model = genai.GenerativeModel('gemini-3-pro-image-preview')
                        
                        prompt = f"""
                        Actúa como un profesor experto. Tu tarea es corregir este examen.
                        
                        Aquí están las preguntas y las respuestas correctas (JSON):
                        {json.dumps(exam_obj['questions'], ensure_ascii=False)}
                        
                        El puntaje para aprobar es: {exam_obj.get('passing_score', 70)}
                        
                        Instrucciones:
                        1. Analiza la imagen del examen resuelto por el estudiante.
                        2. Identifica las respuestas del estudiante para cada pregunta.
                        3. Compara con las respuestas correctas.
                        4. Genera un JSON con el siguiente formato EXACTO (sin markdown):
                        {{
                            "student_answers": {{ "pregunta_id": "respuesta_detectada" }},
                            "corrections": [
                                {{
                                    "question": "texto de la pregunta",
                                    "student_answer": "respuesta detectada",
                                    "correct_answer": "respuesta correcta",
                                    "is_correct": boolean,
                                    "feedback": "breve explicación"
                                }}
                            ],
                            "score": puntaje_numerico_0_a_100,
                            "passed": boolean,
                            "general_feedback": "comentario general al estudiante"
                        }}
                        """
                        
                        # Procesar la imagen
                        if uploaded_file.type.startswith('image'):
                            response = model.generate_content([prompt, image])
                        else:
                            # TODO: Manejo de PDF (requiere conversión o uso de API específica)
                            st.warning("Por ahora solo se procesan imágenes directamente. Para PDF se requiere un paso extra.")
                            return

                        # Extraer JSON de la respuesta
                        response_text = response.text.replace('```json', '').replace('```', '').strip()
                        result_json = json.loads(response_text)
                        
                        # Mostrar resultados
                        st.success("¡Corrección completada!")
                        
                        col_res1, col_res2 = st.columns(2)
                        with col_res1:
                            st.metric("Calificación", f"{result_json['score']}/100")
                        with col_res2:
                            if result_json['passed']:
                                st.success("APROBADO")
                            else:
                                st.error("REPROBADO")
                                
                        st.write("### Feedback General")
                        st.info(result_json['general_feedback'])
                        
                        st.write("### Detalle de Corrección")
                        for correction in result_json['corrections']:
                            with st.expander(f"{'✅' if correction['is_correct'] else '❌'} {correction['question']}"):
                                st.write(f"**Tu respuesta:** {correction['student_answer']}")
                                st.write(f"**Respuesta correcta:** {correction['correct_answer']}")
                                st.write(f"**Feedback:** {correction['feedback']}")

                    except Exception as e:
                        error_msg = str(e)
                        if "429" in error_msg or "ResourceExhausted" in error_msg:
                            st.error("⚠️ Has excedido la cuota gratuita de la API de Google (Rate Limit). Por favor espera unos momentos e intenta de nuevo.")
                        elif "404" in error_msg or "NotFound" in error_msg:
                            st.error(f"⚠️ El modelo de IA no fue encontrado o no es compatible. Error: {error_msg}")
                        else:
                            st.error(f"Ocurrió un error inesperado: {error_msg}")
        else:
             if st.form_submit_button("Corregir con IA"):
                 st.warning("Por favor sube un archivo primero.")

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
            scores = [er['score'] for er in exam_results if er.get('score')]
            if scores:
                fig = px.box(scores, title="Distribución de Calificaciones")
                st.plotly_chart(fig)
            else:
                st.info("Aún no hay calificaciones para mostrar.")


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