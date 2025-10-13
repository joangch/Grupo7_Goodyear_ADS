
import streamlit as st
from typing import Optional
from modulos.gestor_reclamos import GestorReclamos
from config.configuracion import ESTADO_RECIBIDO, ESTADO_EVALUACION, ESTADO_RESUELTO

class InterfazReclamosInternos:
    def __init__(self, usuario_id: int):
        self.usuario_id = usuario_id
        self.gestor = GestorReclamos()

    def _filtros(self):
        st.markdown("### Bandeja de Reclamos")
        col1, col2 = st.columns([1,2])
        with col1:
            estado = st.selectbox("Estado", options=["Todos", ESTADO_RECIBIDO, ESTADO_EVALUACION, ESTADO_RESUELTO])
        with col2:
            texto = st.text_input("Buscar en descripción")
        if estado == "Todos":
            estado = None
        return estado, texto

    def _tabla(self, estado, texto):
        reclamos = self.gestor.listar_reclamos_todos(estado, texto)
        if not reclamos:
            st.info("Sin resultados.")
            return
        for r in reclamos:
            with st.expander(f"#{r['id']} | {r['cliente']} | {r['estado']} | {r['fecha_creacion']}"):
                st.write(r["descripcion"])
                imgs = self.gestor.listar_imagenes(r["id"])
                if imgs:
                    st.write("Imágenes adjuntas:")
                    for ruta in imgs:
                        st.image(ruta, width='stretch')
                # Cambiar estado
                estados_disponibles = [ESTADO_RECIBIDO, ESTADO_EVALUACION, ESTADO_RESUELTO]
                estado_actual_index = estados_disponibles.index(r["estado"]) if r["estado"] in estados_disponibles else 0
                nuevo = st.selectbox("Actualizar estado", estados_disponibles, index=estado_actual_index, key=f"estado_{r['id']}")
                if st.button("Guardar estado", key=f"btn_estado_{r['id']}"):
                    try:
                        self.gestor.actualizar_estado(r["id"], nuevo)
                        st.success("Estado actualizado.")
                    except Exception as e:
                        st.error(f"Error al actualizar estado: {e}")
                # Chat embebido
                from interfaces.chat import ChatReclamo
                ChatReclamo(self.usuario_id, "interno", r["id"]).render()

    def render(self):
        estado, texto = self._filtros()
        self._tabla(estado, texto)
