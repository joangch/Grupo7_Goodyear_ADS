
import streamlit as st
from modulos import seguridad
from modulos.validaciones import validar_usuario, validar_password
from config.configuracion import SESSION_USER_KEY, SESSION_ROLE_KEY, ROL_CLIENTE, ROL_INTERNO

class InterfazLogin:
    def __init__(self):
        st.subheader("Ingreso al Sistema")

    def render(self):
        with st.form("login_form"):
            usuario = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("Ingresar")

        if submitted:
            if not validar_usuario(usuario):
                st.error("Usuario inválido (entre 3 y 50 caracteres).")
                return
            if not validar_password(password):
                st.error("La contraseña debe tener al menos 6 caracteres.")
                return
            res = seguridad.autenticar(usuario, password)
            if res:
                uid, rol = res
                st.session_state[SESSION_USER_KEY] = uid
                st.session_state[SESSION_ROLE_KEY] = rol
                st.success("¡Autenticación exitosa!")
                st.rerun()
            else:
                st.error("Credenciales incorrectas.")
