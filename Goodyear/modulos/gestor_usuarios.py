
import sqlite3
from typing import Optional, Dict, List
from config.configuracion import DB_PATH, ESTADO_RECIBIDO, ESTADOS

class GestorDB:
    def __init__(self):
        self._ensure_schema()

    def _connect(self):
        con = sqlite3.connect(DB_PATH)
        con.row_factory = sqlite3.Row
        return con

    def _ensure_schema(self):
        con = self._connect(); cur = con.cursor()
        cur.executescript('''
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE NOT NULL,
                email TEXT,
                password_hash TEXT NOT NULL,
                rol TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reclamos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                descripcion TEXT NOT NULL,
                estado TEXT NOT NULL,
                fecha TEXT NOT NULL,
                FOREIGN KEY(cliente_id) REFERENCES usuarios(id)
            );

            CREATE TABLE IF NOT EXISTS imagenes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reclamo_id INTEGER NOT NULL,
                ruta TEXT NOT NULL,
                fecha TEXT NOT NULL,
                FOREIGN KEY(reclamo_id) REFERENCES reclamos(id)
            );

            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                detalle TEXT NOT NULL,
                fecha TEXT NOT NULL,
                FOREIGN KEY(cliente_id) REFERENCES usuarios(id)
            );

            /* Despachos: fecha programada y fecha real de entrega para KPIs */
            CREATE TABLE IF NOT EXISTS despachos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pedido_id INTEGER NOT NULL,
                fecha_programada TEXT NOT NULL,
                fecha_entrega TEXT NOT NULL,
                transportista TEXT,
                estado TEXT NOT NULL,
                FOREIGN KEY(pedido_id) REFERENCES pedidos(id)
            );
        ''')
        con.commit(); con.close()

    # ---------- Reclamos ----------
    def crear_reclamo(self, cliente_id: int, descripcion: str) -> int:
        from datetime import datetime
        con = self._connect(); cur = con.cursor()
        cur.execute(
            "INSERT INTO reclamos (cliente_id, descripcion, estado, fecha) VALUES (?,?,?,?)",
            (cliente_id, descripcion, ESTADO_RECIBIDO, datetime.utcnow().isoformat())
        )
        rid = cur.lastrowid; con.commit(); con.close()
        return rid

    def listar_reclamos_cliente(self, cliente_id: int) -> List[Dict]:
        con = self._connect(); cur = con.cursor()
        cur.execute("SELECT * FROM reclamos WHERE cliente_id=? ORDER BY id DESC", (cliente_id,))
        rows = cur.fetchall(); con.close()
        return [dict(r) for r in rows]

    def listar_reclamos(self, estado: Optional[str] = None) -> List[Dict]:
        con = self._connect(); cur = con.cursor()
        if estado and estado in ESTADOS:
            cur.execute("SELECT * FROM reclamos WHERE estado=? ORDER BY id DESC", (estado,))
        else:
            cur.execute("SELECT * FROM reclamos ORDER BY id DESC")
        rows = cur.fetchall(); con.close()
        return [dict(r) for r in rows]

    def actualizar_estado(self, reclamo_id: int, estado: str) -> None:
        con = self._connect(); cur = con.cursor()
        cur.execute("UPDATE reclamos SET estado=? WHERE id=?", (estado, reclamo_id))
        con.commit(); con.close()

    def registrar_imagen(self, reclamo_id: int, ruta: str) -> None:
        from datetime import datetime
        con = self._connect(); cur = con.cursor()
        cur.execute("INSERT INTO imagenes (reclamo_id, ruta, fecha) VALUES (?,?,?)",
                    (reclamo_id, ruta, datetime.utcnow().isoformat()))
        con.commit(); con.close()

    def listar_imagenes(self, reclamo_id: int):
        con = self._connect(); cur = con.cursor()
        cur.execute("SELECT ruta FROM imagenes WHERE reclamo_id=? ORDER BY id", (reclamo_id,))
        rows = [r[0] for r in cur.fetchall()]; con.close()
        return rows

    # ---------- Pedidos ----------
    def crear_pedido(self, cliente_id: int, detalle: str) -> int:
        from datetime import datetime
        con = self._connect(); cur = con.cursor()
        cur.execute("INSERT INTO pedidos (cliente_id, detalle, fecha) VALUES (?,?,?)",
                    (cliente_id, detalle, datetime.utcnow().isoformat()))
        pid = cur.lastrowid; con.commit(); con.close()
        return pid

    def listar_pedidos_cliente(self, cliente_id: int) -> List[Dict]:
        con = self._connect(); cur = con.cursor()
        cur.execute("SELECT * FROM pedidos WHERE cliente_id=? ORDER BY id DESC", (cliente_id,))
        rows = cur.fetchall(); con.close()
        return [dict(r) for r in rows]

    def listar_pedidos(self) -> List[Dict]:
        con = self._connect(); cur = con.cursor()
        cur.execute("SELECT * FROM pedidos ORDER BY id DESC")
        rows = cur.fetchall(); con.close()
        return [dict(r) for r in rows]

    # ---------- Despachos ----------
    def crear_despacho(self, pedido_id: int, fecha_programada: str, fecha_entrega: str,
                       transportista: str, estado: str) -> int:
        con = self._connect(); cur = con.cursor()
        cur.execute("""INSERT INTO despachos (pedido_id, fecha_programada, fecha_entrega, transportista, estado)
                       VALUES (?,?,?,?,?)""",
                    (pedido_id, fecha_programada, fecha_entrega, transportista, estado))
        did = cur.lastrowid; con.commit(); con.close()
        return did

    def listar_despachos(self) -> List[Dict]:
        con = self._connect(); cur = con.cursor()
        cur.execute("""SELECT d.*, p.cliente_id, p.fecha AS fecha_pedido
                       FROM despachos d
                       JOIN pedidos p ON p.id = d.pedido_id
                       ORDER BY d.id DESC""")
        rows = cur.fetchall(); con.close()
        return [dict(r) for r in rows]
