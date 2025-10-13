import streamlit as st
import logging
import os
import sqlite3
import hashlib

from config.configuracion import (
    APP_TITLE, LOG_FILE,
    SESSION_USER_KEY, SESSION_ROLE_KEY,
    ROL_CLIENTE, ROL_INTERNO
)
from interfaces.login import InterfazLogin
from interfaces.reclamos import InterfazReclamosCliente
from interfaces.reclamos_internos import InterfazReclamosInternos
from modulos.gestor_reclamos import GestorReclamos
from modulos.seguridad import crear_usuario, _hash_password  # <-- agregado _hash_password
import sqlite3
from config.configuracion import DB_PATH, PASSWORD_SALT

def _hash(p): return hashlib.sha256((PASSWORD_SALT + p).encode("utf-8")).hexdigest()

# --------------------- Logging ---------------------
# Crear carpeta de logs si no existe
log_dir = os.path.dirname(LOG_FILE)
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --------------------- Título ----------------------
st.set_page_config(page_title=APP_TITLE, layout="wide")
st.title(APP_TITLE)

# ------------------ Init DB + seed -----------------
def seed_db():
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    # Crear tabla usuarios si no existe (estructura objetivo)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            email TEXT,
            password_hash TEXT NOT NULL,
            rol TEXT NOT NULL
        )
    """)
    con.commit()

    # Revisar columnas actuales y migrar si hace falta
    cur.execute("PRAGMA table_info(usuarios)")
    cols = [row[1] for row in cur.fetchall()]
    # Si no existe password_hash, añadirla y migrar desde password si existe
    if "password_hash" not in cols:
        cur.execute("ALTER TABLE usuarios ADD COLUMN password_hash TEXT")
        con.commit()
        if "password" in cols:
            cur.execute("SELECT id, password FROM usuarios")
            rows = cur.fetchall()
            for uid, pwd in rows:
                if pwd is None:
                    continue
                try:
                    hashed = _hash_password(pwd)
                    cur.execute("UPDATE usuarios SET password_hash=? WHERE id=?", (hashed, uid))
                except Exception:
                    # Si algo falla para una fila, saltarla
                    continue
            con.commit()

    # Contar usuarios
    cur.execute("SELECT COUNT(*) FROM usuarios")
    count = cur.fetchone()[0]
    con.close()

    # Seed inicial si no hay usuarios
    if count == 0:
        try:
            crear_usuario("cliente_demo", "cliente@example.com", "cliente123", ROL_CLIENTE)
            crear_usuario("interno_demo", "interno@example.com", "interno123", ROL_INTERNO)
            st.info("Usuarios de prueba creados: cliente_demo / cliente123, interno_demo / interno123")
            logger.info("Seed de usuarios demo creado.")
        except Exception as e:
            logger.error(f"Error al crear seed: {e}")

seed_db()

# --------------------- Sidebar ---------------------
with st.sidebar:
    if SESSION_USER_KEY in st.session_state:
        st.success(f"Sesión iniciada como ID {st.session_state[SESSION_USER_KEY]} ({st.session_state[SESSION_ROLE_KEY]})")
        if st.button("Cerrar sesión"):
            st.session_state.pop(SESSION_USER_KEY, None)
            st.session_state.pop(SESSION_ROLE_KEY, None)
            st.rerun()
    else:
        st.info("No autenticado")

# -------------------- Navegación -------------------
if SESSION_USER_KEY not in st.session_state:
    InterfazLogin().render()
    st.stop()

uid = st.session_state[SESSION_USER_KEY]
rol = st.session_state[SESSION_ROLE_KEY]

if rol == ROL_CLIENTE:
    InterfazReclamosCliente(uid).render()
elif rol == ROL_INTERNO:
    InterfazReclamosInternos(uid).render()
else:
    st.error("Rol no reconocido.")
