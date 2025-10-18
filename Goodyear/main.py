# -*- coding: utf-8 -*-
import sqlite3
import streamlit as st
from config.configuracion import ROL_CLIENTE, ROL_INTERNO, DB_PATH
from core.gestor_usuarios import GestorDB
from core.seguridad import crear_usuario
from interfaces import (
    login,
    pedidos,
    reclamos,
    despacho_interno,
    programacion,
    rutas,
    reclamos_internos,
    reporteria_clean as reporteria,
    pronosticos
)

st.set_page_config(page_title="Aplicación Goodyear", layout="wide")
db = GestorDB()

st.title("Aplicación Goodyear – Mejora de Procesos Logísticos y de Atención al Cliente")

user = st.session_state.get("user")

if user:
    st.sidebar.success(f"Sesión: {user['usuario']} ({user['rol']})")

    # Menú del cliente externo
    if user["rol"] == ROL_CLIENTE:
        opcion = st.sidebar.radio("Menú Cliente", ["Pedidos", "Reclamos", "Cerrar sesión"])

        if opcion == "Pedidos":
            pedidos.mostrar()
        elif opcion == "Reclamos":
            reclamos.mostrar()
        else:
            st.session_state.clear()
            st.rerun()

    # Menú del personal interno
    elif user["rol"] == ROL_INTERNO:
        opcion = st.sidebar.radio(
            "Menú Interno",
            [
                "Despacho interno",
                "Programación",
                "Rutas",
                "Reclamos internos",
                "Reportería",
                "Pronóstico de Demanda",
                "Cerrar sesión"
            ]
        )

        if opcion == "Despacho interno":
            despacho_interno.mostrar()
        elif opcion == "Programación":
            programacion.mostrar()
        elif opcion == "Rutas":
            rutas.mostrar()
        elif opcion == "Reclamos internos":
            reclamos_internos.mostrar()
        elif opcion == "Reportería":
            reporteria.mostrar()
        elif opcion == "Pronóstico de Demanda":
            pronosticos.mostrar()
        else:
            st.session_state.clear()
            st.rerun()

# Si no hay sesión iniciada
else:
    st.sidebar.info("Inicie sesión o cree usuarios de demostración.")
    opcion = st.sidebar.radio("Opciones", ["Login", "Seed (demo)"])

    if opcion == "Login":
        login.mostrar()
    else:
        st.subheader("Creación de usuarios de demostración")
        col1, col2 = st.columns(2)

        def _get_user_id(username: str):
            try:
                con = sqlite3.connect(DB_PATH)
                cur = con.cursor()
                cur.execute("SELECT id FROM usuarios WHERE usuario=?", (username,))
                row = cur.fetchone()
                return int(row[0]) if row else None
            except Exception:
                return None
            finally:
                try:
                    con.close()
                except Exception:
                    pass

        with col1:
            if st.button("Crear cliente de prueba"):
                existing = _get_user_id("cliente_demo")
                if existing:
                    st.info(f"Usuario cliente_demo ya existía (id={existing}, rol={ROL_CLIENTE}).")
                else:
                    uid = crear_usuario("cliente_demo", "cliente@example.com", "cliente123", ROL_CLIENTE)
                    st.success(f"Usuario cliente_demo creado (id={uid}, rol={ROL_CLIENTE}).")

        with col2:
            if st.button("Crear interno de prueba"):
                existing = _get_user_id("interno_demo")
                if existing:
                    st.info(f"Usuario interno_demo ya existía (id={existing}, rol={ROL_INTERNO}).")
                else:
                    uid = crear_usuario("interno_demo", "interno@example.com", "interno123", ROL_INTERNO)
                    st.success(f"Usuario interno_demo creado (id={uid}, rol={ROL_INTERNO}).")

        st.caption("Después de crear, vaya a Login para ingresar.")

        with st.expander("Ver usuarios en la base de datos"):
            try:
                con = sqlite3.connect(DB_PATH)
                cur = con.cursor()
                cur.execute("SELECT id, usuario, rol, email FROM usuarios ORDER BY id")
                rows = cur.fetchall()
                cols = ["id", "usuario", "rol", "email"]
                data = [dict(zip(cols, r)) for r in rows]
                if data:
                    st.table(data)
                else:
                    st.info("No hay usuarios registrados aún.")
            except Exception as e:
                st.error(f"No se pudo leer la base de datos: {e}")
            finally:
                try:
                    con.close()
                except Exception:
                    pass
