
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

            /* Mensajes de chat para reclamos */
            CREATE TABLE IF NOT EXISTS mensajes_reclamo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reclamo_id INTEGER NOT NULL,
                usuario_id INTEGER NOT NULL,
                tipo_usuario TEXT NOT NULL,
                mensaje TEXT NOT NULL,
                fecha_envio TEXT NOT NULL,
                FOREIGN KEY(reclamo_id) REFERENCES reclamos(id),
                FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
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

    # ---------- Mensajes de Chat ----------
    def crear_mensaje(self, reclamo_id: int, usuario_id: int, tipo_usuario: str, mensaje: str) -> int:
        from datetime import datetime
        con = self._connect(); cur = con.cursor()
        cur.execute("""INSERT INTO mensajes_reclamo (reclamo_id, usuario_id, tipo_usuario, mensaje, fecha_envio)
                       VALUES (?,?,?,?,?)""",
                    (reclamo_id, usuario_id, tipo_usuario, mensaje, datetime.utcnow().isoformat()))
        mid = cur.lastrowid; con.commit(); con.close()
        return mid

    def listar_mensajes(self, reclamo_id: int) -> List[Dict]:
        con = self._connect(); cur = con.cursor()
        cur.execute("""SELECT m.*, u.usuario 
                       FROM mensajes_reclamo m
                       JOIN usuarios u ON u.id = m.usuario_id
                       WHERE m.reclamo_id = ?
                       ORDER BY m.id ASC""", (reclamo_id,))
        rows = cur.fetchall(); con.close()
        return [dict(r) for r in rows]

    # ---------- Métodos adicionales para reclamos ----------
    def obtener_reclamo(self, reclamo_id: int) -> Optional[Dict]:
        con = self._connect(); cur = con.cursor()
        cur.execute("""SELECT r.*, u.usuario as cliente_usuario, u.email as cliente_email
                       FROM reclamos r
                       JOIN usuarios u ON u.id = r.cliente_id
                       WHERE r.id = ?""", (reclamo_id,))
        row = cur.fetchone(); con.close()
        return dict(row) if row else None

    def listar_reclamos_con_cliente(self, estado: Optional[str] = None, texto: Optional[str] = None) -> List[Dict]:
        con = self._connect(); cur = con.cursor()
        query = """SELECT r.*, u.usuario as cliente_usuario, u.email as cliente_email
                   FROM reclamos r
                   JOIN usuarios u ON u.id = r.cliente_id
                   WHERE 1=1"""
        params = []
        
        if estado and estado in ESTADOS:
            query += " AND r.estado = ?"
            params.append(estado)
        
        if texto and texto.strip():
            query += " AND r.descripcion LIKE ?"
            params.append(f"%{texto.strip()}%")
        
        query += " ORDER BY r.id DESC"
        
        cur.execute(query, params)
        rows = cur.fetchall(); con.close()
        return [dict(r) for r in rows]
