# -*- coding: utf-8 -*-
"""
GestorDB: Capa simple de acceso a datos basada en SQLite para la app Goodyear.
Provee los métodos usados por las interfaces (reclamos, internos, chat, pedidos, reportería).
"""
from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime
from typing import Any, Dict, List, Optional

from config.configuracion import (
    DB_PATH,
    ESTADOS,
    ESTADO_RECIBIDO,
)

ISO = "%Y-%m-%dT%H:%M:%S"


def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def _ensure_schema() -> None:
    with closing(_connect()) as con, closing(con.cursor()) as cur:
        # usuarios (referencia básica)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE NOT NULL,
                email TEXT,
                password_hash TEXT,
                rol TEXT NOT NULL
            )
            """
        )
        # reclamos del cliente
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS reclamos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                descripcion TEXT NOT NULL,
                estado TEXT NOT NULL,
                fecha TEXT NOT NULL,
                FOREIGN KEY (cliente_id) REFERENCES usuarios(id)
            )
            """
        )
        # imágenes asociadas a reclamos
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS imagenes_reclamo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reclamo_id INTEGER NOT NULL,
                ruta TEXT NOT NULL,
                FOREIGN KEY (reclamo_id) REFERENCES reclamos(id)
            )
            """
        )
        # mensajes de chat por reclamo
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS mensajes_reclamo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reclamo_id INTEGER NOT NULL,
                usuario_id INTEGER NOT NULL,
                tipo_usuario TEXT NOT NULL,  -- 'cliente' | 'interno'
                mensaje TEXT NOT NULL,
                fecha_envio TEXT NOT NULL,
                FOREIGN KEY (reclamo_id) REFERENCES reclamos(id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
            """
        )
        # pedidos del cliente (simple)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                detalle TEXT NOT NULL,
                fecha TEXT NOT NULL,
                estado TEXT DEFAULT 'Nuevo',
                FOREIGN KEY (cliente_id) REFERENCES usuarios(id)
            )
            """
        )
        # despachos asociados a pedidos (simple)
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS despachos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pedido_id INTEGER NOT NULL,
                fecha_salida TEXT,
                fecha_entrega TEXT,
                transportista TEXT,
                estado TEXT,
                on_time INTEGER DEFAULT 1,
                FOREIGN KEY (pedido_id) REFERENCES pedidos(id)
            )
            """
        )
        con.commit()


class GestorDB:
    def __init__(self) -> None:
        _ensure_schema()

    # ---------------- Reclamos (cliente) -----------------
    def crear_reclamo(self, cliente_id: int, descripcion: str) -> int:
        now = datetime.now().strftime(ISO)
        with closing(_connect()) as con, closing(con.cursor()) as cur:
            cur.execute(
                "INSERT INTO reclamos (cliente_id, descripcion, estado, fecha) VALUES (?,?,?,?)",
                (cliente_id, descripcion, ESTADO_RECIBIDO, now),
            )
            rid = cur.lastrowid
            con.commit()
            return int(rid)

    def listar_reclamos_cliente(self, cliente_id: int) -> List[Dict[str, Any]]:
        with closing(_connect()) as con, closing(con.cursor()) as cur:
            cur.execute(
                "SELECT id, descripcion, estado, fecha FROM reclamos WHERE cliente_id=? ORDER BY id DESC",
                (cliente_id,),
            )
            return [dict(row) for row in cur.fetchall()]

    def registrar_imagen(self, reclamo_id: int, ruta: str) -> None:
        with closing(_connect()) as con, closing(con.cursor()) as cur:
            cur.execute(
                "INSERT INTO imagenes_reclamo (reclamo_id, ruta) VALUES (?,?)",
                (reclamo_id, ruta),
            )
            con.commit()

    def listar_imagenes(self, reclamo_id: int) -> List[str]:
        with closing(_connect()) as con, closing(con.cursor()) as cur:
            cur.execute(
                "SELECT ruta FROM imagenes_reclamo WHERE reclamo_id=? ORDER BY id ASC",
                (reclamo_id,),
            )
            return [row[0] for row in cur.fetchall()]

    # ------------- Reclamos (vista interna) --------------
    def listar_reclamos_con_cliente(
        self, estado: Optional[str] = None, texto: str = ""
    ) -> List[Dict[str, Any]]:
        q = [
            "SELECT r.id, r.descripcion, r.estado, r.fecha, u.usuario as cliente",
            "FROM reclamos r JOIN usuarios u ON u.id = r.cliente_id",
            "WHERE 1=1",
        ]
        params: List[Any] = []
        if estado and estado in ESTADOS:
            q.append("AND r.estado = ?")
            params.append(estado)
        if texto:
            q.append("AND (r.descripcion LIKE ? OR u.usuario LIKE ?)")
            like = f"%{texto}%"
            params.extend([like, like])
        q.append("ORDER BY r.id DESC")
        sql = " ".join(q)
        with closing(_connect()) as con, closing(con.cursor()) as cur:
            cur.execute(sql, params)
            return [dict(row) for row in cur.fetchall()]

    def actualizar_estado(self, reclamo_id: int, nuevo_estado: str) -> None:
        with closing(_connect()) as con, closing(con.cursor()) as cur:
            cur.execute(
                "UPDATE reclamos SET estado=? WHERE id=?",
                (nuevo_estado, reclamo_id),
            )
            con.commit()

    # ---------------------- Chat -------------------------
    def crear_mensaje(
        self, reclamo_id: int, usuario_id: int, tipo_usuario: str, mensaje: str
    ) -> None:
        now = datetime.now().strftime(ISO)
        with closing(_connect()) as con, closing(con.cursor()) as cur:
            cur.execute(
                """
                INSERT INTO mensajes_reclamo (reclamo_id, usuario_id, tipo_usuario, mensaje, fecha_envio)
                VALUES (?,?,?,?,?)
                """,
                (reclamo_id, usuario_id, tipo_usuario, mensaje, now),
            )
            con.commit()

    def listar_mensajes(self, reclamo_id: int) -> List[Dict[str, Any]]:
        with closing(_connect()) as con, closing(con.cursor()) as cur:
            cur.execute(
                """
                SELECT usuario_id, tipo_usuario, mensaje, fecha_envio
                FROM mensajes_reclamo
                WHERE reclamo_id=?
                ORDER BY id ASC
                """,
                (reclamo_id,),
            )
            return [dict(row) for row in cur.fetchall()]

    # --------------------- Pedidos -----------------------
    def crear_pedido(self, cliente_id: int, detalle: str) -> int:
        now = datetime.now().strftime(ISO)
        with closing(_connect()) as con, closing(con.cursor()) as cur:
            cur.execute(
                "INSERT INTO pedidos (cliente_id, detalle, fecha) VALUES (?,?,?)",
                (cliente_id, detalle, now),
            )
            pid = cur.lastrowid
            con.commit()
            return int(pid)

    def listar_pedidos_cliente(self, cliente_id: int) -> List[Dict[str, Any]]:
        with closing(_connect()) as con, closing(con.cursor()) as cur:
            cur.execute(
                "SELECT id, detalle, fecha, estado FROM pedidos WHERE cliente_id=? ORDER BY id DESC",
                (cliente_id,),
            )
            return [dict(row) for row in cur.fetchall()]

    def listar_pedidos(self) -> List[Dict[str, Any]]:
        with closing(_connect()) as con, closing(con.cursor()) as cur:
            cur.execute("SELECT id, cliente_id, detalle, fecha, estado FROM pedidos ORDER BY id DESC")
            return [dict(row) for row in cur.fetchall()]

    # -------------------- Despachos ----------------------
    def listar_despachos(self) -> List[Dict[str, Any]]:
        with closing(_connect()) as con, closing(con.cursor()) as cur:
            cur.execute(
                """
                SELECT id, pedido_id, fecha_salida, fecha_entrega, transportista, estado, on_time
                FROM despachos
                ORDER BY id DESC
                """
            )
            return [dict(row) for row in cur.fetchall()]

    # -------------------- Reportería ---------------------
    def listar_reclamos(self) -> List[Dict[str, Any]]:
        with closing(_connect()) as con, closing(con.cursor()) as cur:
            cur.execute("SELECT id, cliente_id, descripcion, estado, fecha FROM reclamos ORDER BY id DESC")
            return [dict(row) for row in cur.fetchall()]


# Inicializar el esquema al importar el módulo (primera carga)
_ensure_schema()
