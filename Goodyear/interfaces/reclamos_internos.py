
import os
import streamlit as st
from PIL import Image
from pathlib import Path
from modulos.gestor_usuarios import GestorDB
from config.configuracion import ESTADOS, ROL_INTERNO

db = GestorDB()

def _filtros():
    """Renderiza los controles de filtrado."""
    st.markdown("### 🔍 Filtros de búsqueda")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        estado = st.selectbox(
            "Estado del reclamo",
            options=["Todos"] + ESTADOS,
            help="Filtra los reclamos por su estado actual"
        )
    
    with col2:
        texto = st.text_input(
            "🔎 Buscar en descripción",
            placeholder="Ingrese palabras clave...",
            help="Busca texto en la descripción de los reclamos"
        )
    
    estado_filtro = None if estado == "Todos" else estado
    return estado_filtro, texto

def _tabla(estado, texto, user):
    """Muestra la tabla de reclamos con opciones de gestión."""
    reclamos = db.listar_reclamos_con_cliente(estado, texto)
    
    if not reclamos:
        st.info("ℹ️ No se encontraron reclamos con los filtros aplicados.")
        return
    
    st.markdown(f"**📊 Total de reclamos: {len(reclamos)}**")
    st.markdown("---")
    
    for r in reclamos:
        # Determinar el color del estado
        color_estado = {
            "Recibido": "🔵",
            "En evaluación": "🟡",
            "Resuelto": "🟢"
        }.get(r['estado'], "⚪")
        
        with st.expander(
            f"{color_estado} Reclamo #{r['id']} | Cliente: {r['cliente_usuario']} | {r['estado']} | {r['fecha'][:10]}",
            expanded=False
        ):
            # Información del cliente
            st.markdown(f"**👤 Cliente:** {r['cliente_usuario']} ({r['cliente_email']})")
            st.markdown(f"**📅 Fecha:** {r['fecha'][:19].replace('T', ' ')}")
            st.markdown(f"**📋 Estado actual:** {r['estado']}")
            
            st.markdown("---")
            st.markdown("**Descripción del reclamo:**")
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
            
            # Gestión de estado
            col1, col2 = st.columns([2, 1])
            
            with col1:
                estado_actual_index = ESTADOS.index(r["estado"]) if r["estado"] in ESTADOS else 0
                nuevo_estado = st.selectbox(
                    "Cambiar estado del reclamo:",
                    options=ESTADOS,
                    index=estado_actual_index,
                    key=f"estado_{r['id']}"
                )
            
            with col2:
                st.write("")  # Espaciado
                if st.button("💾 Guardar estado", key=f"btn_estado_{r['id']}"):
                    if nuevo_estado != r["estado"]:
                        try:
                            db.actualizar_estado(r["id"], nuevo_estado)
                            st.success(f"✅ Estado actualizado a: {nuevo_estado}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error al actualizar estado: {e}")
                    else:
                        st.info("ℹ️ El estado no ha cambiado.")
            
            st.markdown("---")
            
            # Chat embebido
            from interfaces.chat import ChatReclamo
            ChatReclamo(user["id"], "interno", r["id"]).render()

def mostrar():
    """Función principal que renderiza la interfaz de reclamos internos."""
    user = st.session_state.get("user")
    
    if not user or user.get("rol") != ROL_INTERNO:
        st.error("❌ Acceso restringido a personal interno.")
        return
    
    st.header("🏢 Gestión de Reclamos - Panel Interno")
    st.markdown("Administre y dé seguimiento a todos los reclamos de clientes.")
    st.markdown("---")
    
    # Filtros
    estado, texto = _filtros()
    
    st.markdown("---")
    
    # Tabla de reclamos
    _tabla(estado, texto, user)
