
# -*- coding: utf-8 -*-
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = str(BASE_DIR / "data" / "goodyear.db")
UPLOADS_DIR = str(BASE_DIR / "uploads")
LOGS_DIR = str(BASE_DIR / "logs" / "app.log")

PASSWORD_SALT = "goodyear_demo_salt"
HASH_ALG = "sha256"

EXT_IMAGENES = {".png", ".jpg", ".jpeg"}
MAX_IMG_SIZE = 5 * 1024 * 1024

ROL_CLIENTE = "cliente"
ROL_INTERNO = "interno"

ESTADO_RECIBIDO = "Recibido"
ESTADO_EVALUACION = "En evaluación"
ESTADO_RESUELTO = "Resuelto"
ESTADOS = [ESTADO_RECIBIDO, ESTADO_EVALUACION, ESTADO_RESUELTO]
