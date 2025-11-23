# -*- coding: utf-8 -*-
from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
# carga .env (no commitear)
load_dotenv(BASE_DIR / ".env")

# Rutas y ficheros
DATA_DIR = BASE_DIR / "data"
DB_PATH = str(DATA_DIR / "goodyear.db")  # fallback sqlite
UPLOAD_DIR = BASE_DIR / "uploads"        # Path object; usar str(UPLOAD_DIR) si se necesita
LOGS_DIR = BASE_DIR / "logs"
LOG_FILE = str(LOGS_DIR / "app.log")

# Construir DATABASE_URL (usa DATABASE_URL env, o variables MYSQL_*, o fallback sqlite)
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    mysql_user = os.environ.get("MYSQL_USER")
    if mysql_user:
        mysql_password = os.environ.get("MYSQL_PASSWORD", "")
        mysql_host = os.environ.get("MYSQL_HOST", "localhost")
        mysql_port = os.environ.get("MYSQL_PORT", "3306")
        mysql_db = os.environ.get("MYSQL_DB", "goodyear")
        DATABASE_URL = f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_db}"
    else:
        DATABASE_URL = f"sqlite:///{DB_PATH}"

# Seguridad / constantes
PASSWORD_SALT = "goodyear_demo_salt"
HASH_ALG = "sha256"

# Límites y constantes de la app
EXT_IMAGENES = {".png", ".jpg", ".jpeg"}
MAX_IMG_SIZE = 5 * 1024 * 1024

ROL_CLIENTE = "cliente"
ROL_INTERNO = "interno"

ESTADO_RECIBIDO = "Recibido"
ESTADO_EVALUACION = "En evaluación"
ESTADO_RESUELTO = "Resuelto"
ESTADOS = [ESTADO_RECIBIDO, ESTADO_EVALUACION, ESTADO_RESUELTO]
