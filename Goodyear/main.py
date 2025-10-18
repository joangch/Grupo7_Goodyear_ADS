# -*- coding: utf-8 -*-
import streamlit as st
from config.configuracion import ROL_CLIENTE, ROL_INTERNO
from modulos.gestor_usuarios import GestorDB
from modulos.seguridad import crear_usuario
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

        with col1:
            if st.button("Crear cliente de prueba"):
                crear_usuario("cliente_demo", "cliente@example.com", "cliente123", ROL_CLIENTE)
                st.success("Usuario cliente_demo creado.")

        with col2:
            if st.button("Crear interno de prueba"):
                crear_usuario("interno_demo", "interno@example.com", "interno123", ROL_INTERNO)
                st.success("Usuario interno_demo creado.")

        st.caption("Después de crear, vaya a Login para ingresar.")
