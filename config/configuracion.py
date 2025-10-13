
import os
from pathlib import Path

# Rutas base
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"
LOG_DIR = BASE_DIR / "logs"

# Archivos
DB_PATH = DATA_DIR / "reclamos.db"
LOG_FILE = LOG_DIR / "app.log"

# Seguridad (prototipo): sal para hash
PASSWORD_SALT = "gyd_demo_salt_2025"

# Roles
ROL_CLIENTE = "cliente"
ROL_INTERNO = "interno"

# Estados de reclamo
ESTADO_RECIBIDO = "Recibido"
ESTADO_EVALUACION = "En evaluación"
ESTADO_RESUELTO = "Resuelto"

# Extensiones permitidas para imágenes
EXT_IMAGENES = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}

# Tamaños máximos (en bytes) - 5MB por imagen (prototipo)
MAX_IMG_SIZE = 5 * 1024 * 1024

# Streamlit keys
SESSION_USER_KEY = "usuario"
SESSION_ROLE_KEY = "rol"
SESSION_VIEW_KEY = "vista_activa"
SESSION_COMPLAINT_KEY = "reclamo_activo"

# App info
APP_TITLE = "Goodyear - Sistema de Reclamos (Prototipo)"
