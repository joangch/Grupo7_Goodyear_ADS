

import streamlit as st

def mostrar():
    user = st.session_state.get("user")
    if not user or user.get("rol") != "interno":
        st.error("Acceso restringido a personal interno.")
        return
    st.header("Despacho interno")
    st.info("Plantilla del módulo. Aquí se implementarán las funciones de despacho.")
