
# -*- coding: utf-8 -*-
import streamlit as st
from modulos.gestor_usuarios import GestorDB

db = GestorDB()

def mostrar():
    user = st.session_state.get("user")
    if not user or user.get("rol") != "cliente":
        st.error("Acceso restringido a clientes.")
        return
    st.header("Pedidos")
    with st.form("pedido_form"):
        detalle = st.text_area("Detalle del pedido", max_chars=1000)
        enviar = st.form_submit_button("Registrar pedido")
    if enviar and detalle.strip():
        pid = db.crear_pedido(user["id"], detalle.strip())
        st.success(f"Pedido registrado con ID {pid}.")

    st.subheader("Mis pedidos")
    for p in db.listar_pedidos_cliente(user["id"]):
        st.markdown(f"ID {p['id']} — {p['fecha']}")
        st.write(p["detalle"])
        st.write("---")
