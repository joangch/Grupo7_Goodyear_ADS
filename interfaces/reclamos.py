import streamlit as st
import sqlite3
import hashlib
from typing import Optional
from modulos.gestor_reclamos import GestorReclamos
from modulos.validaciones import validar_descripcion, validar_imagen
from modulos.gestor_archivos import guardar_imagen
from config.configuracion import (
    SESSION_USER_KEY, ROL_CLIENTE,
    ESTADO_RECIBIDO, ESTADO_EVALUACION, ESTADO_RESUELTO,
    DB_PATH, PASSWORD_SALT
)

def _hash(p): return hashlib.sha256((PASSWORD_SALT + p).encode("utf-8")).hexdigest()

class InterfazReclamosCliente:
    def __init__(self, usuario_id: int):
        self.usuario_id = usuario_id
        self.gestor = GestorReclamos()

    def _form_registro(self):
        st.markdown("### Registrar nuevo reclamo")
        descripcion = st.text_area("Descripción del problema", help="Explique el inconveniente con suficiente detalle.")
        imgs = st.file_uploader("Adjuntar imágenes (opcional)", type=["png","jpg","jpeg","gif","bmp","webp"], accept_multiple_files=True)
        if st.button("Enviar reclamo"):
            if not validar_descripcion(descripcion):
                st.error("La descripción debe tener entre 10 y 1000 caracteres.")
                return
            try:
                rid = self.gestor.registrar_reclamo(self.usuario_id, descripcion)

                # Guardar imágenes
                for i in imgs or []:
                    contenido = i.getvalue()
                    err = validar_imagen(i.name, contenido)
                    if err:
                        st.warning(f"No se adjuntó '{i.name}': {err}")
                        continue
                    ruta = guardar_imagen(contenido, i.name, rid)
                    self.gestor.registrar_imagen(rid, ruta)

                st.success(f"Reclamo registrado con ID #{rid}.")
            except Exception as e:
                st.error(f"Ocurrió un error al registrar el reclamo: {e}")

    def _listado(self):
        st.markdown("### Mis reclamos")
        listado = self.gestor.listar_reclamos_cliente(self.usuario_id)
        if not listado:
            st.info("No tiene reclamos registrados.")
            return
        for r in listado:
            with st.expander(f"Reclamo #{r['id']} - Estado: {r['estado']} - {r['fecha_creacion']}"):
                st.write(r["descripcion"])
                imgs = self.gestor.listar_imagenes(r["id"])
                if imgs:
                    st.write("Imágenes adjuntas:")
                    for ruta in imgs:
                        st.image(ruta, width='stretch')
                # Chat embebido
                from interfaces.chat import ChatReclamo
                ChatReclamo(self.usuario_id, "cliente", r["id"]).render()

    def render(self):
        self._form_registro()
        st.markdown("---")
        self._listado()
