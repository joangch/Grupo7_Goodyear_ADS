
import streamlit as st
from modulos.seguridad import autenticar

def mostrar():
    st.header("Módulo de Login")
    with st.form("login_form"):
        usuario = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Ingresar")
    if submit:
        user = autenticar(usuario, password)
        if user:
            st.session_state["user"] = user
            st.success("Autenticación exitosa.")
            st.rerun()
        else:
            st.error("Usuario o contraseña inválidos.")
