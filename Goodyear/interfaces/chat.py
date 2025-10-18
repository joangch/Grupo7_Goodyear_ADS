
import streamlit as st
from core.gestor_usuarios import GestorDB
from core.validaciones import validar_mensaje
from config.configuracion import ROL_CLIENTE, ROL_INTERNO

class ChatReclamo:
    """
    Componente de chat integrado para comunicación entre cliente y personal interno
    sobre un reclamo específico.
    """
    
    def __init__(self, usuario_id: int, tipo_usuario: str, reclamo_id: int):
        """
        Args:
            usuario_id: ID del usuario actual
            tipo_usuario: 'cliente' o 'interno'
            reclamo_id: ID del reclamo asociado
        """
        self.usuario_id = usuario_id
        self.tipo_usuario = tipo_usuario
        self.reclamo_id = reclamo_id
        self.db = GestorDB()

    def render(self):
        """Renderiza la interfaz del chat."""
        st.markdown("""
        <div style='padding:0.5rem 0; font-weight:600; color:#0066cc;'>
            💬 Chat del Reclamo
        </div>
        """, unsafe_allow_html=True)
        
        # Mostrar mensajes existentes
        mensajes = self.db.listar_mensajes(self.reclamo_id)
        
        if not mensajes:
            st.info("No hay mensajes aún. ¡Sé el primero en escribir!")
        else:
            for m in mensajes:
                # Determinar el tipo de avatar según el remitente
                avatar = "assistant" if m['tipo_usuario'] == "interno" else "user"
                autor = f"{m['usuario']} ({m['tipo_usuario']})"
                fecha = m['fecha_envio'][:19].replace('T', ' ')  # Formatear fecha
                
                with st.chat_message(avatar):
                    st.markdown(f"**{autor}** — {fecha}")
                    st.markdown(m['mensaje'])
        
        st.markdown("---")
        
        # Entrada de nuevo mensaje
        with st.form(key=f"chat_form_{self.reclamo_id}", clear_on_submit=True):
            nuevo_mensaje = st.text_area(
                "Escribe tu mensaje:",
                max_chars=500,
                height=80,
                key=f"msg_input_{self.reclamo_id}"
            )
            submitted = st.form_submit_button("📤 Enviar mensaje")
        
        if submitted:
            if not nuevo_mensaje or not nuevo_mensaje.strip():
                st.warning("⚠️ El mensaje no puede estar vacío.")
                return
            
            if not validar_mensaje(nuevo_mensaje):
                st.error("❌ El mensaje debe tener entre 1 y 500 caracteres.")
                return
            
            try:
                self.db.crear_mensaje(
                    reclamo_id=self.reclamo_id,
                    usuario_id=self.usuario_id,
                    tipo_usuario=self.tipo_usuario,
                    mensaje=nuevo_mensaje.strip()
                )
                st.success("✅ Mensaje enviado correctamente.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error al enviar mensaje: {e}")
