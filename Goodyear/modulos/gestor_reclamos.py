
import sqlite3
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from config.configuracion import DB_PATH, ESTADO_RECIBIDO, ESTADO_EVALUACION, ESTADO_RESUELTO

class GestorReclamos:
    def __init__(self):
        self._ensure_schema()

    def _connect(self):
        return sqlite3.connect(DB_PATH)

    def _ensure_schema(self):
        con = self._connect()
        cur = con.cursor()
        cur.executescript(
            '''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE,
                email TEXT,
                password_hash TEXT,
                rol TEXT
            );
            CREATE TABLE IF NOT EXISTS reclamos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER,
                descripcion TEXT,
                estado TEXT,
                fecha_creacion TEXT,
                fecha_actualizacion TEXT,
                FOREIGN KEY(cliente_id) REFERENCES usuarios(id)
            );
            CREATE TABLE IF NOT EXISTS mensajes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reclamo_id INTEGER,
                autor_id INTEGER,
                autor_rol TEXT,
                mensaje TEXT,
                fecha TEXT,
                FOREIGN KEY(reclamo_id) REFERENCES reclamos(id),
                FOREIGN KEY(autor_id) REFERENCES usuarios(id)
            );
            CREATE TABLE IF NOT EXISTS imagenes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reclamo_id INTEGER,
                ruta TEXT,
                fecha TEXT,
                FOREIGN KEY(reclamo_id) REFERENCES reclamos(id)
            );
            '''
        )
        con.commit()
        con.close()

    # ---------------- Reclamos ----------------
    def registrar_reclamo(self, cliente_id: int, descripcion: str) -> int:
        ahora = datetime.utcnow().isoformat()
        con = self._connect()
        cur = con.cursor()
        cur.execute(
            "INSERT INTO reclamos (cliente_id, descripcion, estado, fecha_creacion, fecha_actualizacion) VALUES (?,?,?,?,?)",
            (cliente_id, descripcion, ESTADO_RECIBIDO, ahora, ahora)
        )
        reclamo_id = cur.lastrowid
        con.commit()
        con.close()
        return reclamo_id

    def actualizar_estado(self, reclamo_id: int, nuevo_estado: str):
        ahora = datetime.utcnow().isoformat()
        con = self._connect()
        cur = con.cursor()
        cur.execute(
            "UPDATE reclamos SET estado=?, fecha_actualizacion=? WHERE id=?",
            (nuevo_estado, ahora, reclamo_id)
        )
        con.commit()
        con.close()

    def obtener_reclamo(self, reclamo_id: int) -> Optional[Dict]:
        con = self._connect()
        cur = con.cursor()
        cur.execute(
            "SELECT id, cliente_id, descripcion, estado, fecha_creacion, fecha_actualizacion FROM reclamos WHERE id=?",
            (reclamo_id,)
        )
        row = cur.fetchone()
        con.close()
        if not row:
            return None
        return {
            "id": row[0],
            "cliente_id": row[1],
            "descripcion": row[2],
            "estado": row[3],
            "fecha_creacion": row[4],
            "fecha_actualizacion": row[5],
        }

    def listar_reclamos_cliente(self, cliente_id: int) -> List[Dict]:
        con = self._connect()
        cur = con.cursor()
        cur.execute(
            "SELECT id, descripcion, estado, fecha_creacion FROM reclamos WHERE cliente_id=? ORDER BY id DESC",
            (cliente_id,)
        )
        rows = cur.fetchall()
        con.close()
        return [
            {"id": r[0], "descripcion": r[1], "estado": r[2], "fecha_creacion": r[3]} for r in rows
        ]

    def listar_reclamos_todos(self, estado: Optional[str] = None, texto: Optional[str] = None) -> List[Dict]:
        con = self._connect()
        cur = con.cursor()
        query = "SELECT r.id, u.usuario, r.descripcion, r.estado, r.fecha_creacion FROM reclamos r JOIN usuarios u ON r.cliente_id=u.id"
        params = []
        conds = []
        if estado:
            conds.append("r.estado = ?")
            params.append(estado)
        if texto:
            conds.append("r.descripcion LIKE ?")
            params.append(f"%{texto}%")
        if conds:
            query += " WHERE " + " AND ".join(conds)
        query += " ORDER BY r.id DESC"
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        con.close()
        return [
            {"id": r[0], "cliente": r[1], "descripcion": r[2], "estado": r[3], "fecha_creacion": r[4]} for r in rows
        ]

    # ---------------- Imágenes ----------------
    def registrar_imagen(self, reclamo_id: int, ruta: str):
        con = self._connect()
        cur = con.cursor()
        cur.execute(
            "INSERT INTO imagenes (reclamo_id, ruta, fecha) VALUES (?,?, datetime('now'))",
            (reclamo_id, ruta)
        )
        con.commit()
        con.close()

    def listar_imagenes(self, reclamo_id: int) -> List[str]:
        con = self._connect()
        cur = con.cursor()
        cur.execute("SELECT ruta FROM imagenes WHERE reclamo_id=? ORDER BY id", (reclamo_id,))
        rows = cur.fetchall()
        con.close()
        return [r[0] for r in rows]

    # ---------------- Chat / Mensajes ----------------
    def agregar_mensaje(self, reclamo_id: int, autor_id: int, autor_rol: str, mensaje: str):
        con = self._connect()
        cur = con.cursor()
        cur.execute(
            "INSERT INTO mensajes (reclamo_id, autor_id, autor_rol, mensaje, fecha) VALUES (?,?,?,?, datetime('now'))",
            (reclamo_id, autor_id, autor_rol, mensaje)
        )
        con.commit()
        con.close()

    def listar_mensajes(self, reclamo_id: int) -> List[Dict]:
        con = self._connect()
        cur = con.cursor()
        cur.execute(
            "SELECT m.id, u.usuario, m.autor_rol, m.mensaje, m.fecha FROM mensajes m LEFT JOIN usuarios u ON m.autor_id = u.id WHERE m.reclamo_id=? ORDER BY m.id",
            (reclamo_id,)
        )
        rows = cur.fetchall()
        con.close()
        return [
            {"id": r[0], "autor": r[1] or "Usuario", "rol": r[2], "mensaje": r[3], "fecha": r[4]} for r in rows
        ]
