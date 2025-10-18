
import os
import streamlit as st
from PIL import Image
from pathlib import Path
from core.gestor_usuarios import GestorDB
from core.validaciones import validar_descripcion, validar_imagen
from core.gestor_archivos import guardar_imagen
from config.configuracion import ROL_CLIENTE

db = GestorDB()

def _form_registro(user):
    """Formulario para registrar un nuevo reclamo."""
    st.markdown("### 📝 Registrar nuevo reclamo")
    
    with st.form("reclamo_form", clear_on_submit=True):
        desc = st.text_area(
            "Descripción del problema",
            max_chars=1000,
            help="Explique el inconveniente con suficiente detalle (mínimo 10 caracteres).",
            height=150
        )
        imagenes = st.file_uploader(
            "📎 Adjuntar imágenes (opcional)",
            type=["png", "jpg", "jpeg", "gif", "bmp", "webp"],
            accept_multiple_files=True,
            help="Puede adjuntar hasta 5 MB por imagen"
        )
        registrar = st.form_submit_button("🚀 Enviar reclamo")
    
    if registrar:
        if not validar_descripcion(desc):
            st.error("❌ La descripción debe tener entre 10 y 1000 caracteres.")
            return
        
        try:
            # Crear el reclamo
            rid = db.crear_reclamo(user["id"], desc.strip())
            
            # Guardar imágenes adjuntas
            imagenes_guardadas = 0
            for img in imagenes or []:
                contenido = img.getvalue()
                err = validar_imagen(img.name, contenido)
                if err:
                    st.warning(f"⚠️ No se adjuntó '{img.name}': {err}")
                    continue
                
                ruta = guardar_imagen(contenido, img.name, rid)
                db.registrar_imagen(rid, ruta)
                imagenes_guardadas += 1
            
            mensaje_exito = f"✅ Reclamo registrado con ID #{rid}."
            if imagenes_guardadas > 0:
                mensaje_exito += f" Se adjuntaron {imagenes_guardadas} imagen(es)."
            st.success(mensaje_exito)
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Ocurrió un error al registrar el reclamo: {e}")

def _listado(user):
    """Lista todos los reclamos del cliente."""
    st.markdown("### 📋 Mis reclamos")
    
    reclamos = db.listar_reclamos_cliente(user["id"])
    
    if not reclamos:
        st.info("ℹ️ No tiene reclamos registrados. ¡Registre su primer reclamo arriba!")
        return
    
    for r in reclamos:
        # Determinar el color del estado
        color_estado = {
            "Recibido": "🔵",
            "En evaluación": "🟡",
            "Resuelto": "🟢"
        }.get(r['estado'], "⚪")
        
        with st.expander(
            f"{color_estado} Reclamo #{r['id']} — {r['estado']} — {r['fecha'][:10]}",
            expanded=False
        ):
            st.markdown(f"**Descripción:**")
            st.write(r["descripcion"])
            
            # Mostrar imágenes adjuntas
            imgs = db.listar_imagenes(r["id"])
            if imgs:
                st.markdown(f"**📷 Imágenes adjuntas ({len(imgs)}):**")
                cols = st.columns(min(len(imgs), 3))
                for idx, ruta in enumerate(imgs):
                    try:
                        with cols[idx % 3]:
                            st.image(
                                Image.open(ruta),
                                caption=Path(ruta).name,
                                use_container_width=True
                            )
                    except Exception as e:
                        st.caption(f"⚠️ No se pudo cargar: {Path(ruta).name}")
            
            st.markdown("---")
            
            # Chat embebido
            from interfaces.chat import ChatReclamo
            ChatReclamo(user["id"], "cliente", r["id"]).render()

def mostrar():
    """Función principal que renderiza la interfaz de reclamos para clientes."""
    user = st.session_state.get("user")
    
    if not user or user.get("rol") != ROL_CLIENTE:
        st.error("❌ Acceso restringido a clientes.")
        return
    
    st.header("🎯 Gestión de Reclamos")
    st.markdown("En esta sección puede registrar nuevos reclamos y dar seguimiento a los existentes.")
    
    # Formulario de registro
    _form_registro(user)
    
    st.markdown("---")
    
    # Listado de reclamos
    _listado(user)
