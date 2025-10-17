

import os
import streamlit as st
from PIL import Image
from pathlib import Path
from modulos.gestor_usuarios import GestorDB
from config.configuracion import EXT_IMAGENES, MAX_IMG_SIZE, UPLOADS_DIR

db = GestorDB()
Path(UPLOADS_DIR).mkdir(parents=True, exist_ok=True)

def _validar_imagen(file) -> str:
    if not file:
        return ""
    ext = Path(file.name).suffix.lower()
    if ext not in EXT_IMAGENES:
        return "Formato no permitido."
    content = file.getvalue()
    if len(content) > MAX_IMG_SIZE:
        return "El archivo supera el tamaño máximo permitido."
    return ""

def mostrar():
    user = st.session_state.get("user")
    if not user or user.get("rol") != "cliente":
        st.error("Acceso restringido a clientes.")
        return
    st.header("Reclamos")
    with st.form("reclamo_form"):
        desc = st.text_area("Descripción del reclamo", max_chars=1000)
        imagenes = st.file_uploader("Evidencias (PNG/JPG, máximo 5 MB)", type=["png","jpg","jpeg"], accept_multiple_files=True)
        registrar = st.form_submit_button("Registrar reclamo")
    if registrar and desc.strip():
        rid = db.crear_reclamo(user["id"], desc.strip())
        for img in imagenes or []:
            err = _validar_imagen(img)
            if err:
                st.warning(f"{img.name}: {err}")
                continue
            from pathlib import Path
            import uuid
            nombre = f"reclamo_{rid}_{uuid.uuid4().hex}{Path(img.name).suffix.lower()}"
            ruta = Path(UPLOADS_DIR) / nombre
            ruta.write_bytes(img.getvalue())
            db.registrar_imagen(rid, str(ruta))
        st.success(f"Reclamo registrado con ID {rid}.")

    st.subheader("Mis reclamos")
    for r in db.listar_reclamos_cliente(user["id"]):
        st.markdown(f"Reclamo {r['id']} — Estado: {r['estado']} — Fecha: {r['fecha']}")
        st.write(r["descripcion"])
        for ruta in db.listar_imagenes(r["id"]):
            try:
                st.image(Image.open(ruta), caption=os.path.basename(ruta), use_column_width=True)
            except Exception:
                st.caption(f"No se pudo cargar {ruta}")
        st.write("---")
