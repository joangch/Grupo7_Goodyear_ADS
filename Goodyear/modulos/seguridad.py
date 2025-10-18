import hashlib
import sqlite3
from typing import Optional, Tuple
from config.configuracion import DB_PATH, PASSWORD_SALT, ROL_CLIENTE, ROL_INTERNO

def _hash_password(password: str) -> str:
    data = (PASSWORD_SALT + password).encode("utf-8")
    return hashlib.sha256(data).hexdigest()

def crear_usuario(username: str, email: str, password: str, rol: str) -> int:
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    try:
        cur.execute(
            "INSERT INTO usuarios (usuario, email, password_hash, rol) VALUES (?,?,?,?)",
            (username, email, _hash_password(password), rol)
        )
        uid = cur.lastrowid
        con.commit()
        return int(uid)
    except sqlite3.IntegrityError:
        # Ya existe el usuario: devolver su id
        cur.execute("SELECT id FROM usuarios WHERE usuario=?", (username,))
        row = cur.fetchone()
        if row:
            return int(row[0])
        raise
    finally:
        con.close()

def autenticar(username: str, password: str) -> Optional[Tuple[int, str]]:
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT id, password_hash, rol FROM usuarios WHERE usuario=?", (username,))
    row = cur.fetchone()
    con.close()
    if not row:
        return None
    uid, pwhash, rol = row
    if pwhash == _hash_password(password):
        return (uid, rol)
    return None
