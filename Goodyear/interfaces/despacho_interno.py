"""Sistema de Despacho Interno - Goodyear
Módulo de Gestión de Pedidos y Entregas
Versión: 1.0
"""

import streamlit as st
import numpy as np
from datetime import datetime, timedelta
import json
import os
import warnings
warnings.filterwarnings('ignore')


class DispatchDataGenerator:
    """Generador de datos de pedidos para despacho"""
    
    CLIENTES = [
        "Taller Lima Centro", "AutoServicios del Norte", "Mecánica Express",
        "LlantasPlus Perú", "ServiRuedas SAC", "Centro Automotriz Callao",
        "Distribuidora Andina", "Taller San Isidro", "Ruedas del Sur"
    ]
    
    TIPOS_LLANTA = ["Eagle F1", "Assurance", "Wrangler", "EfficientGrip"]
    
    ESTADOS = ["Preparando", "En tránsito", "Entregado"]
    
    @staticmethod
    def generar_pedidos(cantidad=15):
        """Genera datos sintéticos de pedidos"""
        pedidos = []
        
        for i in range(1, cantidad + 1):
            fecha_creado = datetime.now() - timedelta(
                minutes=np.random.randint(30, 300)
            )
            
            estado_idx = np.random.choice([0, 0, 0, 1, 1, 2])
            estado = DispatchDataGenerator.ESTADOS[estado_idx]
            
            timestamps = {
                "creado": fecha_creado.strftime('%Y-%m-%d %H:%M:%S'),
                "preparando": fecha_creado.strftime('%Y-%m-%d %H:%M:%S'),
                "en_transito": None,
                "entregado": None
            }
            
            if estado in ["En tránsito", "Entregado"]:
                fecha_transito = fecha_creado + timedelta(
                    minutes=np.random.randint(15, 60)
                )
                timestamps["en_transito"] = fecha_transito.strftime('%Y-%m-%d %H:%M:%S')
            
            if estado == "Entregado":
                fecha_entrega = datetime.strptime(
                    timestamps["en_transito"], '%Y-%m-%d %H:%M:%S'
                ) + timedelta(minutes=np.random.randint(20, 90))
                timestamps["entregado"] = fecha_entrega.strftime('%Y-%m-%d %H:%M:%S')
            
            pedido = {
                "codigo": f"PED{i:03d}",
                "cliente": np.random.choice(DispatchDataGenerator.CLIENTES),
                "producto": np.random.choice(DispatchDataGenerator.TIPOS_LLANTA),
                "cantidad": np.random.randint(4, 24),
                "estado": estado,
                "timestamps": timestamps,
                "coordenadas": {
                    "lat": -12.0464 + np.random.uniform(-0.1, 0.1),
                    "lng": -77.0428 + np.random.uniform(-0.1, 0.1)
                },
                "vehiculo_disponible": np.random.choice([True, True, False]),
                "direccion": f"Av. Principal {np.random.randint(100, 999)}, Lima"
            }
            
            pedidos.append(pedido)
        
        return pedidos


class LeadTimeCalculator:
    """Calculador de Lead Time logístico"""
    
    OBJETIVO_MINUTOS = 120
    LIMITE_ACEPTABLE = 150
    
    @staticmethod
    def calcular_lead_time(pedido):
        """Calcula el lead time en minutos para un pedido entregado"""
        if pedido["estado"] != "Entregado":
            return None
        
        try:
            fecha_creado = datetime.strptime(
                pedido["timestamps"]["creado"], '%Y-%m-%d %H:%M:%S'
            )
            fecha_entregado = datetime.strptime(
                pedido["timestamps"]["entregado"], '%Y-%m-%d %H:%M:%S'
            )
            delta = fecha_entregado - fecha_creado
            return round(delta.total_seconds() / 60, 1)
        except Exception:
            return None
    
    @staticmethod
    def clasificar_lead_time(minutos):
        """Clasifica el lead time según objetivos"""
        if minutos is None:
            return "N/A", "⚪"
        
        if minutos < LeadTimeCalculator.OBJETIVO_MINUTOS:
            return "Excelente ✓", "🟢"
        elif minutos <= LeadTimeCalculator.LIMITE_ACEPTABLE:
            return "Aceptable ⚠", "🟡"
        else:
            return "Lento ✗", "🔴"
    
    @staticmethod
    def obtener_metricas(pedidos):
        """Calcula métricas de lead time"""
        lead_times = []
        
        for p in pedidos:
            lt = LeadTimeCalculator.calcular_lead_time(p)
            if lt is not None:
                lead_times.append(lt)
        
        if not lead_times:
            return {"promedio": 0, "minimo": 0, "maximo": 0}
        
        return {
            "promedio": round(np.mean(lead_times), 1),
            "minimo": round(min(lead_times), 1),
            "maximo": round(max(lead_times), 1)
        }


class IntegracionModulos:
    """Integración con otros módulos del sistema"""
    
    @staticmethod
    def verificar_ruta_optima():
        """Verifica si existe archivo de ruta óptima exportado"""
        archivos_ruta = [f for f in os.listdir('.') 
                        if f.startswith('ruta_') and f.endswith('.json')]
        return len(archivos_ruta) > 0, archivos_ruta
    
    @staticmethod
    def cargar_ruta_optima(archivo):
        """Carga datos de ruta óptima desde JSON"""
        try:
            with open(archivo, 'r') as f:
                return json.load(f)
        except Exception:
            return None


def _aplicar_filtros(pedidos, filtros):
    """Aplica filtros a la lista de pedidos"""
    resultado = pedidos.copy()
    
    if filtros.get('cliente') and filtros['cliente'] != "Todos":
        resultado = [p for p in resultado if p['cliente'] == filtros['cliente']]
    
    if filtros.get('producto') and filtros['producto'] != "Todos":
        resultado = [p for p in resultado if p['producto'] == filtros['producto']]
    
    if filtros.get('fecha_desde'):
        fecha_desde = datetime.combine(filtros['fecha_desde'], datetime.min.time())
        resultado = [p for p in resultado 
                    if datetime.strptime(p['timestamps']['creado'], '%Y-%m-%d %H:%M:%S') >= fecha_desde]
    
    if filtros.get('fecha_hasta'):
        fecha_hasta = datetime.combine(filtros['fecha_hasta'], datetime.max.time())
        resultado = [p for p in resultado 
                    if datetime.strptime(p['timestamps']['creado'], '%Y-%m-%d %H:%M:%S') <= fecha_hasta]
    
    return resultado


def _actualizar_estado(codigo, nuevo_estado):
    """Actualiza el estado de un pedido y registra timestamp"""
    for pedido in st.session_state.pedidos:
        if pedido['codigo'] == codigo:
            pedido['estado'] = nuevo_estado
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if nuevo_estado == "En tránsito":
                pedido['timestamps']['en_transito'] = timestamp
            elif nuevo_estado == "Entregado":
                pedido['timestamps']['entregado'] = timestamp
            
            return True
    return False


def _contar_por_estado(pedidos):
    """Cuenta pedidos por estado"""
    conteo = {"Preparando": 0, "En tránsito": 0, "Entregado": 0}
    for p in pedidos:
        if p['estado'] in conteo:
            conteo[p['estado']] += 1
    return conteo


def main():
    """Aplicación principal de Streamlit"""
    
    st.set_page_config(
        page_title="Goodyear - Despacho Interno",
        page_icon="🚚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.markdown("""
        <style>
        .main {
            background-color: #f8f9fa;
        }
        .stButton>button {
            background-color: #2a5298;
            color: white;
            font-weight: bold;
            border-radius: 8px;
            padding: 10px 24px;
            border: none;
        }
        .stButton>button:hover {
            background-color: #1e3c72;
        }
        .metric-card {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .pedido-card {
            background-color: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            border-left: 4px solid #2a5298;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <div style='background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                    padding: 30px; border-radius: 10px; margin-bottom: 20px;'>
            <h1 style='color: white; text-align: center; margin: 0;'>
                🚚 Goodyear - Sistema de Despacho Interno
            </h1>
            <p style='color: white; text-align: center; margin: 10px 0 0 0; opacity: 0.9;'>
                Control de Flujo de Pedidos y Entregas
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    if 'pedidos' not in st.session_state:
        st.session_state.pedidos = []
    
    if 'filtros' not in st.session_state:
        st.session_state.filtros = {}
    
    with st.sidebar:
        st.header("📦 Gestión de Pedidos")
        st.markdown("---")
        
        if st.button("🔄 Cargar Pedidos de Ejemplo", use_container_width=True):
            st.session_state.pedidos = DispatchDataGenerator.generar_pedidos(15)
            st.success("✓ 15 pedidos cargados")
            st.rerun()
        
        st.markdown("---")
        st.subheader("🔍 Filtros")
        
        clientes = ["Todos"]
        productos = ["Todos"]
        
        if st.session_state.pedidos:
            clientes += list(set(p['cliente'] for p in st.session_state.pedidos))
            productos += list(set(p['producto'] for p in st.session_state.pedidos))
        
        filtro_cliente = st.selectbox("Cliente:", options=clientes)
        filtro_producto = st.selectbox("Tipo de Llanta:", options=productos)
        
        col1, col2 = st.columns(2)
        with col1:
            fecha_desde = st.date_input("Desde:", value=None)
        with col2:
            fecha_hasta = st.date_input("Hasta:", value=None)
        
        if st.button("🔎 Aplicar Filtros", use_container_width=True):
            st.session_state.filtros = {
                'cliente': filtro_cliente,
                'producto': filtro_producto,
                'fecha_desde': fecha_desde,
                'fecha_hasta': fecha_hasta
            }
            st.success("✓ Filtros aplicados")
        
        st.markdown("---")
        st.subheader("🚚 Estado Actual")
        
        if st.session_state.pedidos:
            conteo = _contar_por_estado(st.session_state.pedidos)
            st.metric("📦 Preparando", conteo["Preparando"])
            st.metric("🚛 En tránsito", conteo["En tránsito"])
            st.metric("✅ Entregados", conteo["Entregado"])
    
    if not st.session_state.pedidos:
        st.info("👈 Cargue pedidos en el panel lateral para comenzar.")
        return
    
    pedidos_filtrados = _aplicar_filtros(
        st.session_state.pedidos, 
        st.session_state.filtros
    )
    
    conteo = _contar_por_estado(pedidos_filtrados)
    
    st.subheader("📊 Métricas Generales")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Pedidos", len(pedidos_filtrados))
    with col2:
        st.metric("📦 Preparando", conteo["Preparando"])
    with col3:
        st.metric("🚛 En Tránsito", conteo["En tránsito"])
    with col4:
        st.metric("✅ Entregados", conteo["Entregado"])
    
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["📋 Pedidos", "⏱️ Lead Time", "🔍 Historial del Pedido"])
    
    with tab1:
        st.subheader("Lista de Pedidos")
        
        tiene_ruta, archivos_ruta = IntegracionModulos.verificar_ruta_optima()
        if tiene_ruta:
            st.success(f"🗺️ Ruta óptima disponible: {archivos_ruta[0]}")
        
        for pedido in pedidos_filtrados:
            color_estado = {
                "Preparando": "🟡",
                "En tránsito": "🟠", 
                "Entregado": "🟢"
            }.get(pedido['estado'], "⚪")
            
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([1.5, 2, 1.5, 1.5, 2])
                
                with col1:
                    st.markdown(f"**{pedido['codigo']}**")
                    st.caption(f"{color_estado} {pedido['estado']}")
                
                with col2:
                    st.markdown(f"👤 {pedido['cliente']}")
                    st.caption(f"🛞 {pedido['producto']} ({pedido['cantidad']} uds)")
                
                with col3:
                    st.caption("📅 Creado:")
                    st.caption(pedido['timestamps']['creado'][:16])
                
                with col4:
                    if pedido['vehiculo_disponible']:
                        st.caption("🚛 Vehículo disponible")
                    else:
                        st.caption("⚠️ Sin vehículo")
                
                with col5:
                    if pedido['estado'] == "Preparando":
                        if st.button("➜ Marcar En tránsito", 
                                    key=f"transito_{pedido['codigo']}",
                                    use_container_width=True):
                            _actualizar_estado(pedido['codigo'], "En tránsito")
                            st.rerun()
                    
                    elif pedido['estado'] == "En tránsito":
                        if st.button("✓ Marcar Entregado", 
                                    key=f"entregado_{pedido['codigo']}",
                                    use_container_width=True):
                            _actualizar_estado(pedido['codigo'], "Entregado")
                            st.rerun()
                    
                    else:
                        st.caption("✅ Completado")
                
                st.markdown("---")
    
    with tab2:
        st.subheader("Análisis de Lead Time")
        
        metricas_lt = LeadTimeCalculator.obtener_metricas(pedidos_filtrados)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            color = "normal"
            if metricas_lt['promedio'] > 0:
                if metricas_lt['promedio'] < 120:
                    color = "off"
                elif metricas_lt['promedio'] > 150:
                    color = "inverse"
            st.metric("⏱️ Promedio", f"{metricas_lt['promedio']} min")
        with col2:
            st.metric("⬇️ Mínimo", f"{metricas_lt['minimo']} min")
        with col3:
            st.metric("⬆️ Máximo", f"{metricas_lt['maximo']} min")
        
        st.markdown("---")
        st.markdown("**Objetivo: < 120 minutos** | Aceptable: 120-150 min | Lento: > 150 min")
        st.markdown("---")
        
        tabla_lt = []
        for p in pedidos_filtrados:
            lt = LeadTimeCalculator.calcular_lead_time(p)
            clasificacion, icono = LeadTimeCalculator.clasificar_lead_time(lt)
            
            tabla_lt.append({
                'Código': p['codigo'],
                'Cliente': p['cliente'],
                'Estado': p['estado'],
                'Lead Time (min)': lt if lt else "—",
                'Clasificación': f"{icono} {clasificacion}"
            })
        
        st.dataframe(tabla_lt, use_container_width=True)
    
    with tab3:
        st.subheader("Historial Detallado del Pedido")
        
        codigos = [p['codigo'] for p in pedidos_filtrados]
        codigo_seleccionado = st.selectbox("Seleccione un pedido:", options=codigos)
        
        pedido_seleccionado = next(
            (p for p in pedidos_filtrados if p['codigo'] == codigo_seleccionado), 
            None
        )
        
        if pedido_seleccionado:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📦 Información del Pedido")
                st.markdown(f"**Código:** {pedido_seleccionado['codigo']}")
                st.markdown(f"**Cliente:** {pedido_seleccionado['cliente']}")
                st.markdown(f"**Producto:** {pedido_seleccionado['producto']}")
                st.markdown(f"**Cantidad:** {pedido_seleccionado['cantidad']} unidades")
                st.markdown(f"**Dirección:** {pedido_seleccionado['direccion']}")
                
                color_estado = {"Preparando": "🟡", "En tránsito": "🟠", "Entregado": "🟢"}
                st.markdown(f"**Estado Actual:** {color_estado.get(pedido_seleccionado['estado'], '⚪')} {pedido_seleccionado['estado']}")
            
            with col2:
                st.markdown("### ⏱️ Timeline de Etapas")
                
                ts = pedido_seleccionado['timestamps']
                
                st.markdown(f"📝 **Creado:** {ts['creado']}")
                st.markdown(f"📦 **Preparando:** {ts['preparando']}")
                
                if ts['en_transito']:
                    st.markdown(f"🚛 **En tránsito:** {ts['en_transito']}")
                    
                    t1 = datetime.strptime(ts['preparando'], '%Y-%m-%d %H:%M:%S')
                    t2 = datetime.strptime(ts['en_transito'], '%Y-%m-%d %H:%M:%S')
                    delta1 = round((t2 - t1).total_seconds() / 60, 1)
                    st.caption(f"   ↳ Tiempo preparación: {delta1} min")
                else:
                    st.markdown("🚛 **En tránsito:** Pendiente")
                
                if ts['entregado']:
                    st.markdown(f"✅ **Entregado:** {ts['entregado']}")
                    
                    t2 = datetime.strptime(ts['en_transito'], '%Y-%m-%d %H:%M:%S')
                    t3 = datetime.strptime(ts['entregado'], '%Y-%m-%d %H:%M:%S')
                    delta2 = round((t3 - t2).total_seconds() / 60, 1)
                    st.caption(f"   ↳ Tiempo en tránsito: {delta2} min")
                    
                    lt = LeadTimeCalculator.calcular_lead_time(pedido_seleccionado)
                    clasificacion, icono = LeadTimeCalculator.clasificar_lead_time(lt)
                    st.markdown(f"**Lead Time Total:** {lt} min — {icono} {clasificacion}")
                else:
                    st.markdown("✅ **Entregado:** Pendiente")
            
            st.markdown("---")
            st.markdown("### 🔗 Integraciones")
            
            col1, col2 = st.columns(2)
            
            with col1:
                tiene_ruta, archivos = IntegracionModulos.verificar_ruta_optima()
                if tiene_ruta:
                    st.success(f"🗺️ Ruta óptima disponible")
                    st.caption(f"Archivo: {archivos[0]}")
                else:
                    st.warning("🗺️ Sin ruta óptima cargada")
            
            with col2:
                if pedido_seleccionado['vehiculo_disponible']:
                    st.success("🚛 Vehículo asignado disponible")
                else:
                    st.warning("🚛 Vehículo no disponible")
    
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("📥 Exportar Pedidos", use_container_width=True):
            export_data = {
                "metadata": {
                    "fecha_generacion": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "total_pedidos": len(st.session_state.pedidos),
                    "filtros_aplicados": st.session_state.filtros if st.session_state.filtros else "Ninguno"
                },
                "metricas": {
                    "conteo_estados": _contar_por_estado(st.session_state.pedidos),
                    "lead_time": LeadTimeCalculator.obtener_metricas(st.session_state.pedidos)
                },
                "pedidos": st.session_state.pedidos
            }
            
            st.download_button(
                label="⬇️ Descargar JSON",
                data=json.dumps(export_data, indent=2, ensure_ascii=False),
                file_name=f"despacho_interno_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )


def mostrar():
    """Función de entrada para integración con otros módulos"""
    main()


if __name__ == "__main__":
    main()
