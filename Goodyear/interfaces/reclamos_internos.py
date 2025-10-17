

import streamlit as st
from modulos.gestor_usuarios import GestorDB
from config.configuracion import ESTADOS

db = GestorDB()

def mostrar():
    user = st.session_state.get("user")
    if not user or user.get("rol") != "interno":
        st.error("Acceso restringido a personal interno.")
        return
    st.header("Reclamos internos")
    filtro = st.selectbox("Filtrar por estado", options=["Todos"] + ESTADOS)
    reclamos = db.listar_reclamos(None if filtro == "Todos" else filtro)
    st.caption(f"Registros: {len(reclamos)}")
    for r in reclamos:
        with st.expander(f"Reclamo {r['id']} — Estado actual: {r['estado']}"):
            st.write(r["descripcion"])
            st.caption(f"Fecha: {r['fecha']} — Cliente ID: {r['cliente_id']}")
            nuevo = st.selectbox(f"Nuevo estado para {r['id']}", options=ESTADOS, index=ESTADOS.index(r["estado"]))
            if st.button(f"Actualizar {r['id']}"):
                db.actualizar_estado(r["id"], nuevo)
                st.success(f"Actualizado a {nuevo}.")
                st.experimental_rerun()
