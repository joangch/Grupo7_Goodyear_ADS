
import streamlit as st
from core.seguridad import autenticar

def mostrar():
    st.header("🔐 Módulo de Login")
    
    # Mostrar usuarios disponibles para demo
    st.info("👥 **Usuarios disponibles para demo:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🙋 Cliente Externo:**
        - **Usuario:** `cliente_demo`
        - **Contraseña:** `cliente123`
        - **Acceso a:** Pedidos y Reclamos
        """)
    
    with col2:
        st.markdown("""
        **👨‍💼 Personal Interno:**
        - **Usuario:** `interno_demo`
        - **Contraseña:** `interno123`
        - **Acceso a:** Todos los módulos
        """)
    
    st.markdown("---")
    
    # Formulario de login
    with st.form("login_form"):
        usuario = st.text_input("👤 Usuario", placeholder="Ingrese su usuario")
        password = st.text_input("🔑 Contraseña", type="password", placeholder="Ingrese su contraseña")
        submit = st.form_submit_button("🚀 Ingresar")
    
    if submit:
        if not usuario or not password:
            st.warning("⚠️ Por favor complete todos los campos.")
            return

        resultado = autenticar(usuario, password)
        if resultado:
            uid, rol = resultado
            st.session_state["user"] = {"id": uid, "usuario": usuario, "rol": rol}
            st.success(f"✅ ¡Bienvenido {usuario}! Autenticación exitosa.")
            st.rerun()
        else:
            st.error("❌ Usuario o contraseña inválidos. Por favor intente nuevamente.")
