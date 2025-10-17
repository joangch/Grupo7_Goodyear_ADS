
# -*- coding: utf-8 -*-
import hashlib, sqlite3
from typing import Optional, Dict
from config.configuracion import DB_PATH, PASSWORD_SALT, HASH_ALG

def _hash(pwd: str) -> str:
    h = hashlib.new(HASH_ALG)
    h.update((pwd + PASSWORD_SALT).encode("utf-8"))
    return h.hexdigest()

def crear_usuario(usuario: str, email: str, password: str, rol: str) -> None:
    con = sqlite3.connect(DB_PATH); cur = con.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO usuarios (usuario, email, password_hash, rol)
        VALUES (?, ?, ?, ?)
    """, (usuario, email, _hash(password), rol))
    con.commit(); con.close()

def autenticar(usuario: str, password: str) -> Optional[Dict]:
    con = sqlite3.connect(DB_PATH); cur = con.cursor()
    cur.execute("SELECT id, usuario, email, password_hash, rol FROM usuarios WHERE usuario=?", (usuario,))
    row = con.cursor().fetchone() if False else cur.fetchone()
    con.close()
    if not row:
        return None
    uid, u, email, pwhash, rol = row
    if _hash(password) == pwhash:
        return {"id": uid, "usuario": u, "email": email, "rol": rol}
    return None
