
import streamlit as st
from modulos.gestor_reclamos import GestorReclamos
from config.configuracion import ROL_CLIENTE, ROL_INTERNO

class ChatReclamo:
    def __init__(self, usuario_id: int, rol: str, reclamo_id: int):
        self.usuario_id = usuario_id
        self.rol = rol
        self.reclamo_id = reclamo_id
        self.gestor = GestorReclamos()

    def render(self):
        st.markdown("""
        <div style='padding:0.25rem 0; font-weight:600;'>Chat del Reclamo</div>
        """, unsafe_allow_html=True)
        mensajes = self.gestor.listar_mensajes(self.reclamo_id)
        for m in mensajes:
            autor = f"{m['autor']} ({m['rol']})"
            st.chat_message("assistant" if m['rol']=="interno" else "user").markdown(f"**{autor}** — {m['fecha']}\n\n{m['mensaje']}")
        # Entrada de mensaje
        nuevo = st.text_input("Escribe un mensaje", key=f"msg_{self.reclamo_id}")
        if st.button("Enviar", key=f"enviar_{self.reclamo_id}"):
            if not nuevo or not nuevo.strip():
                st.warning("El mensaje no puede estar vacío.")
                return
            try:
                self.gestor.agregar_mensaje(self.reclamo_id, self.usuario_id, self.rol, nuevo.strip())
                st.success("Mensaje enviado.")
                st.rerun()
            except Exception as e:
                st.error(f"Error al enviar mensaje: {e}")
