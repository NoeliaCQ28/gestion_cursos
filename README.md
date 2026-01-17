🎓 Sistema de Gestión de Cursos Online
Una plataforma web integral desarrollada en Python y Streamlit para la administración de cursos, estudiantes y evaluaciones. Este sistema incorpora Inteligencia Artificial (Google Gemini) para la corrección automática de exámenes y herramientas estadísticas avanzadas para validar instrumentos de evaluación.

🚀 Características Principales
🛠️ Gestión Administrativa
Dashboard Interactivo: Métricas en tiempo real sobre estudiantes, cursos activos y tasas de completación.

Gestión de Cursos: Creación y edición de cursos, módulos y exámenes.

Base de Datos en la Nube: Integración nativa con Supabase para persistencia de datos segura.

🤖 Inteligencia Artificial & Automatización
Corrección Automática de Exámenes: Utiliza Google Gemini Pro Vision para corregir exámenes subidos en formato imagen o PDF.

Compara respuestas del estudiante con una hoja de claves (JSON).

Genera feedback automático y calificación numérica.

Integración con n8n: Webhooks configurados para automatizar flujos de inscripción y notificaciones.

🧪 Módulo de Psicometría y Validación
Herramientas para validar la calidad de los instrumentos de evaluación:

Validez de Contenido: Calculadora de V de Aiken para juicio de expertos.

Confiabilidad: Cálculo de Alfa de Cronbach y Omega de McDonald (implementación manual y vía pingouin).

⚡ Pruebas de Rendimiento
Pruebas de Carga Integradas: Ejecución de tests de estrés con Locust directamente desde la interfaz para medir la capacidad del servidor.

Comparativa de Tiempos: Módulo para medir el ROI de tiempo entre corrección manual vs. corrección con IA.

🛠️ Tecnologías Utilizadas
Frontend/Backend: Streamlit

Lenguaje: Python 3.11+

Base de Datos: Supabase (PostgreSQL)

IA Generativa: Google Generative AI (Gemini Models)

Visualización: Plotly Express

Análisis de Datos & Estadística: Pandas, NumPy, Scikit-learn, Pingouin

Reportes: FPDF2

Testing: Locust

⚙️ Instalación y Configuración
1. Clonar el repositorio
Bash

git clone https://github.com/tu-usuario/gestion_cursos.git
cd gestion_cursos
2. Crear un entorno virtual (Recomendado)
Bash

python -m venv venv
# En Windows
venv\Scripts\activate
# En Mac/Linux
source venv/bin/activate
3. Instalar dependencias
Bash

pip install -r requirements.txt
4. Configurar Variables de Entorno
Crea una carpeta .streamlit en la raíz del proyecto y dentro un archivo secrets.toml. Añade tus credenciales:

Archivo: .streamlit/secrets.toml

Ini, TOML

SUPABASE_URL = "TU_URL_DE_SUPABASE"
SUPABASE_KEY = "TU_ANON_KEY_DE_SUPABASE"
GOOGLE_API_KEY = "TU_API_KEY_DE_GOOGLE_GEMINI"
N8N_WEBHOOK_URL = "TU_WEBHOOK_DE_N8N" (Opcional)
▶️ Ejecución
Para iniciar la aplicación en tu servidor local:

Bash

streamlit run app.py
La aplicación estará disponible en http://localhost:8501.

📂 Estructura del Proyecto
Plaintext

gestion_cursos/
├── app.py                  # Archivo principal de la aplicación
├── requirements.txt        # Dependencias del proyecto
├── locustfile.py           # Definición de pruebas de carga
├── .streamlit/
│   └── secrets.toml        # Credenciales (No subir al repo)
├── check_deps.py           # Scripts de verificación de entorno
└── ...
📝 Uso del Corrector con IA
Ve a la pestaña Gestión de Exámenes.

Selecciona un estudiante y el examen correspondiente.

Sube una foto o PDF del examen resuelto.

Haz clic en "Corregir con IA".

El sistema analizará la imagen, comparará con el patrón de respuestas y guardará la nota automáticamente en Supabase.

👥 Contribución
Las contribuciones son bienvenidas. Por favor, abre un issue primero para discutir qué te gustaría cambiar.

Desarrollado por [NoeCQ/ AbrahamJimenez - Proyecto de Curso de Investigacion / Ingeniería de Sistemas
