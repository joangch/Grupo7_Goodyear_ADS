"""
Sistema de Planificación de Rutas - Goodyear
Módulo de optimización de rutas de entrega en Lima Metropolitana
"""

import streamlit as st
import numpy as np
import json
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')


class RouteDataGenerator:
    """Generador de datos de ejemplo para paradas de entrega en Lima Metropolitana"""
    
    @staticmethod
    def generate_sample_stops():
        """
        Genera paradas de ejemplo con coordenadas realistas de Lima
        
        Returns:
            list: Lista de diccionarios con datos de paradas
        """
        stops = [
            {"codigo": "DEP_001", "nombre": "Centro de Distribución Principal", "lat": -12.0464, "lon": -77.0428},
            {"codigo": "PTO_001", "nombre": "Taller San Juan de Lurigancho", "lat": -11.9853, "lon": -76.9842},
            {"codigo": "PTO_002", "nombre": "Taller Los Olivos", "lat": -11.9617, "lon": -77.0722},
            {"codigo": "PTO_003", "nombre": "Taller San Miguel", "lat": -12.0772, "lon": -77.0878},
            {"codigo": "PTO_004", "nombre": "Taller Miraflores", "lat": -12.1192, "lon": -77.0289},
            {"codigo": "PTO_005", "nombre": "Taller Surco", "lat": -12.1392, "lon": -76.9931},
            {"codigo": "PTO_006", "nombre": "Taller Villa El Salvador", "lat": -12.2131, "lon": -76.9394},
            {"codigo": "PTO_007", "nombre": "Taller Callao", "lat": -12.0564, "lon": -77.1181},
            {"codigo": "PTO_008", "nombre": "Taller La Victoria", "lat": -12.0692, "lon": -77.0136},
            {"codigo": "PTO_009", "nombre": "Taller San Borja", "lat": -12.0969, "lon": -77.0006},
            {"codigo": "PTO_010", "nombre": "Taller Ate", "lat": -12.0536, "lon": -76.9506}
        ]
        return stops


class RoutePlanner:
    """Planificador de rutas usando algoritmos heurísticos"""
    
    def __init__(self):
        self.distance_matrix = None
        self.locations = None
        
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """
        Calcula la distancia haversine entre dos puntos geográficos
        
        Args:
            lat1, lon1: Coordenadas del punto 1
            lat2, lon2: Coordenadas del punto 2
            
        Returns:
            float: Distancia en kilómetros
        """
        R = 6371  # Radio de la Tierra en km
        
        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        delta_lat = np.radians(lat2 - lat1)
        delta_lon = np.radians(lon2 - lon1)
        
        a = np.sin(delta_lat/2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c
    
    def calculate_distance_matrix(self, locations):
        """
        Calcula la matriz de distancias entre todas las ubicaciones
        
        Args:
            locations: Lista de diccionarios con 'lat' y 'lon'
            
        Returns:
            numpy.ndarray: Matriz de distancias
        """
        self.locations = locations
        n = len(locations)
        matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    matrix[i][j] = self.haversine_distance(
                        locations[i]['lat'], locations[i]['lon'],
                        locations[j]['lat'], locations[j]['lon']
                    )
        
        self.distance_matrix = matrix
        return matrix
    
    def nearest_neighbor_route(self, distance_matrix, start_index=0):
        """
        Algoritmo del vecino más cercano para TSP
        
        Args:
            distance_matrix: Matriz de distancias
            start_index: Índice del punto de partida
            
        Returns:
            list: Ruta ordenada como lista de índices
        """
        n = len(distance_matrix)
        unvisited = set(range(n))
        route = [start_index]
        unvisited.remove(start_index)
        
        current = start_index
        
        while unvisited:
            nearest = min(unvisited, key=lambda x: distance_matrix[current][x])
            route.append(nearest)
            unvisited.remove(nearest)
            current = nearest
        
        route.append(start_index)  # Regresar al origen
        return route
    
    def calculate_route_distance(self, route, distance_matrix):
        """
        Calcula la distancia total de una ruta
        
        Args:
            route: Lista de índices representando la ruta
            distance_matrix: Matriz de distancias
            
        Returns:
            float: Distancia total en km
        """
        total = 0
        for i in range(len(route) - 1):
            total += distance_matrix[route[i]][route[i+1]]
        return total
    
    def two_opt_improvement(self, route, distance_matrix, max_iterations=100):
        """
        Mejora la ruta usando el algoritmo 2-opt
        
        Args:
            route: Ruta inicial
            distance_matrix: Matriz de distancias
            max_iterations: Número máximo de iteraciones
            
        Returns:
            list: Ruta mejorada
        """
        best_route = route.copy()
        best_distance = self.calculate_route_distance(best_route, distance_matrix)
        improved = True
        iterations = 0
        
        while improved and iterations < max_iterations:
            improved = False
            iterations += 1
            
            for i in range(1, len(route) - 2):
                for j in range(i + 1, len(route) - 1):
                    new_route = best_route.copy()
                    new_route[i:j+1] = reversed(new_route[i:j+1])
                    new_distance = self.calculate_route_distance(new_route, distance_matrix)
                    
                    if new_distance < best_distance:
                        best_route = new_route
                        best_distance = new_distance
                        improved = True
                        break
                
                if improved:
                    break
        
        return best_route
    
    def compute_route_stats(self, route, distance_matrix, avg_speed_kmh):
        """
        Calcula estadísticas detalladas de la ruta
        
        Args:
            route: Lista de índices de la ruta
            distance_matrix: Matriz de distancias
            avg_speed_kmh: Velocidad promedio en km/h
            
        Returns:
            dict: Estadísticas de la ruta
        """
        stops_details = []
        cumulative_distance = 0
        cumulative_time = 0
        
        for i, stop_idx in enumerate(route):
            if i == 0:
                distance_from_prev = 0
            else:
                distance_from_prev = distance_matrix[route[i-1]][stop_idx]
            
            cumulative_distance += distance_from_prev
            cumulative_time = (cumulative_distance / avg_speed_kmh) * 60  # en minutos
            
            stops_details.append({
                "orden": i + 1,
                "indice": stop_idx,
                "distancia_desde_anterior_km": round(distance_from_prev, 2),
                "distancia_acumulada_km": round(cumulative_distance, 2),
                "tiempo_estimado_min": round(cumulative_time, 1)
            })
        
        total_distance = cumulative_distance
        total_time = cumulative_time
        
        return {
            "paradas": stops_details,
            "distancia_total_km": round(total_distance, 2),
            "tiempo_total_estimado_min": round(total_time, 1),
            "numero_paradas": len(route) - 1  # No contar el regreso al origen
        }


def apply_custom_css():
    """Aplica estilos CSS personalizados"""
    st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .main-header h1 {
            color: white;
            margin: 0;
            font-size: 2.5rem;
            font-weight: 700;
        }
        .main-header p {
            color: #e0e0e0;
            margin: 0.5rem 0 0 0;
            font-size: 1.1rem;
        }
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1.5rem;
            border-radius: 10px;
            color: white;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .stButton>button {
            width: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-weight: 600;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        }
        </style>
    """, unsafe_allow_html=True)


def format_time_hhmm(minutes):
    """
    Convierte minutos a formato HH:MM
    
    Args:
        minutes: Tiempo en minutos
        
    Returns:
        str: Tiempo en formato HH:MM
    """
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    return f"{hours:02d}:{mins:02d}"


def calculate_eta(start_time_str, travel_minutes):
    """
    Calcula hora estimada de llegada
    
    Args:
        start_time_str: Hora de inicio en formato "HH:MM"
        travel_minutes: Minutos de viaje
        
    Returns:
        str: Hora de llegada en formato "HH:MM"
    """
    try:
        start_time = datetime.strptime(start_time_str, "%H:%M")
        eta = start_time + timedelta(minutes=travel_minutes)
        return eta.strftime("%H:%M")
    except:
        return "N/A"


def export_route_to_json(stops_data, route_stats, algorithm_name, avg_speed, start_time):
    """
    Exporta la ruta optimizada a formato JSON
    
    Args:
        stops_data: Lista de paradas con información completa
        route_stats: Estadísticas de la ruta
        algorithm_name: Nombre del algoritmo usado
        avg_speed: Velocidad promedio
        start_time: Hora de inicio
        
    Returns:
        dict: Datos en formato JSON
    """
    paradas_export = []
    
    for stop_stat in route_stats['paradas']:
        stop_idx = stop_stat['indice']
        stop_info = stops_data[stop_idx]
        
        eta = calculate_eta(start_time, stop_stat['tiempo_estimado_min'])
        
        paradas_export.append({
            "orden": stop_stat['orden'],
            "codigo": stop_info['codigo'],
            "nombre": stop_info['nombre'],
            "lat": stop_info['lat'],
            "lon": stop_info['lon'],
            "distancia_desde_anterior_km": stop_stat['distancia_desde_anterior_km'],
            "distancia_acumulada_km": stop_stat['distancia_acumulada_km'],
            "tiempo_estimado_min": stop_stat['tiempo_estimado_min'],
            "hora_estimada_llegada": eta
        })
    
    export_data = {
        "metadata": {
            "fecha_generacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "algoritmo": algorithm_name,
            "velocidad_promedio_kmh": avg_speed,
            "hora_inicio": start_time
        },
        "paradas": paradas_export,
        "totales": {
            "distancia_total_km": route_stats['distancia_total_km'],
            "tiempo_total_estimado_min": route_stats['tiempo_total_estimado_min'],
            "numero_paradas": route_stats['numero_paradas']
        }
    }
    
    return export_data


def main():
    """Función principal de la aplicación"""
    
    st.set_page_config(
        page_title="Planificación de Rutas - Goodyear",
        page_icon="🚚",
        layout="wide"
    )
    
    apply_custom_css()
    
    # Encabezado principal
    st.markdown("""
        <div class="main-header">
            <h1>🚚 Sistema de Planificación de Rutas – Goodyear</h1>
            <p>Optimización de rutas de entrega en Lima Metropolitana</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Inicializar session state
    if 'stops_data' not in st.session_state:
        st.session_state.stops_data = None
    if 'route_results' not in st.session_state:
        st.session_state.route_results = None
    
    # Sidebar - Panel de Control
    st.sidebar.header("🎛️ Panel de Control")
    
    # Sección 1: Datos de Paradas
    st.sidebar.subheader("📍 Datos de Paradas")
    
    if st.sidebar.button("📦 Cargar Datos de Ejemplo"):
        generator = RouteDataGenerator()
        st.session_state.stops_data = generator.generate_sample_stops()
        st.sidebar.success(f"✅ {len(st.session_state.stops_data)} paradas cargadas")
    
    # Opción de cargar CSV
    uploaded_file = st.sidebar.file_uploader("📄 O subir archivo CSV", type=['csv'])
    if uploaded_file is not None:
        try:
            import pandas as pd
            df = pd.read_csv(uploaded_file)
            stops = []
            for _, row in df.iterrows():
                stops.append({
                    'codigo': str(row['codigo']),
                    'nombre': str(row['nombre']),
                    'lat': float(row['lat']),
                    'lon': float(row['lon'])
                })
            st.session_state.stops_data = stops
            st.sidebar.success(f"✅ {len(stops)} paradas cargadas desde CSV")
        except Exception as e:
            st.sidebar.error(f"❌ Error al cargar CSV: {str(e)}")
    
    # Sección 2: Configuración de Ruta
    st.sidebar.subheader("🚚 Configuración de Ruta")
    
    if st.session_state.stops_data:
        stop_options = [f"{s['codigo']} - {s['nombre']}" for s in st.session_state.stops_data]
        start_stop_idx = st.sidebar.selectbox(
            "🏭 Punto de Partida (Depósito)",
            range(len(stop_options)),
            format_func=lambda x: stop_options[x]
        )
        
        algorithm_choice = st.sidebar.selectbox(
            "🧮 Algoritmo de Optimización",
            ["Nearest Neighbor (Rápido)", "Nearest Neighbor + 2-Opt (Recomendado)"]
        )
        
        avg_speed = st.sidebar.slider(
            "⚡ Velocidad Promedio (km/h)",
            min_value=10,
            max_value=60,
            value=30,
            step=5
        )
        
        start_time = st.sidebar.time_input(
            "🕐 Hora de Inicio",
            value=datetime.strptime("08:00", "%H:%M").time()
        )
        start_time_str = start_time.strftime("%H:%M")
        
        st.sidebar.markdown("---")
        
        # Botón principal
        if st.sidebar.button("🚀 OPTIMIZAR RUTA", type="primary"):
            with st.spinner("Calculando ruta óptima..."):
                try:
                    planner = RoutePlanner()
                    
                    # Calcular matriz de distancias
                    distance_matrix = planner.calculate_distance_matrix(st.session_state.stops_data)
                    
                    # Calcular ruta con vecino más cercano
                    route = planner.nearest_neighbor_route(distance_matrix, start_stop_idx)
                    
                    # Aplicar 2-opt si está seleccionado
                    if "2-Opt" in algorithm_choice:
                        route = planner.two_opt_improvement(route, distance_matrix)
                    
                    # Calcular estadísticas
                    route_stats = planner.compute_route_stats(route, distance_matrix, avg_speed)
                    
                    # Guardar resultados
                    st.session_state.route_results = {
                        'route': route,
                        'stats': route_stats,
                        'algorithm': algorithm_choice,
                        'avg_speed': avg_speed,
                        'start_time': start_time_str,
                        'distance_matrix': distance_matrix
                    }
                    
                    st.sidebar.success("✅ Ruta optimizada exitosamente")
                    
                except Exception as e:
                    st.sidebar.error(f"❌ Error: {str(e)}")
        
        # Sección de Lead Time
        st.sidebar.markdown("---")
        st.sidebar.subheader("⏱️ Comparación Lead Time")
        
        lead_time_real = st.sidebar.number_input(
            "Lead Time Real (minutos)",
            min_value=0,
            value=0,
            step=5
        )
        
        st.session_state.lead_time_real = lead_time_real
    
    # Contenido Principal
    if st.session_state.stops_data is None:
        st.info("👈 Por favor, cargue los datos de paradas desde el panel de control")
        
        st.markdown("### 📋 Ejemplo de formato CSV")
        st.markdown("""
```
        codigo,nombre,lat,lon
        DEP_001,Centro de Distribución,-12.0464,-77.0428
        PTO_001,Taller San Juan,-11.9853,-76.9842
```
        """)
    
    elif st.session_state.route_results is None:
        st.info("👈 Configure las paradas y haga clic en 'OPTIMIZAR RUTA'")
        
        st.markdown("### 📍 Vista Previa de Paradas")
        
        preview_data = []
        for stop in st.session_state.stops_data:
            preview_data.append({
                "Código": stop['codigo'],
                "Nombre": stop['nombre'],
                "Latitud": stop['lat'],
                "Longitud": stop['lon']
            })
        
        st.dataframe(preview_data, use_container_width=True)
    
    else:
        # Mostrar resultados
        results = st.session_state.route_results
        stats = results['stats']
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "📏 Distancia Total",
                f"{stats['distancia_total_km']} km"
            )
        
        with col2:
            st.metric(
                "⏱️ Tiempo Estimado",
                f"{format_time_hhmm(stats['tiempo_total_estimado_min'])}"
            )
        
        with col3:
            st.metric(
                "📍 Número de Paradas",
                stats['numero_paradas']
            )
        
        with col4:
            if st.session_state.get('lead_time_real', 0) > 0:
                lead_real = st.session_state.lead_time_real
                lead_estimado = stats['tiempo_total_estimado_min']
                diferencia = lead_real - lead_estimado
                porcentaje = (diferencia / lead_estimado) * 100 if lead_estimado > 0 else 0
                
                if porcentaje < -10:
                    estado = "🟢 Mejor"
                    color = "normal"
                elif porcentaje > 10:
                    estado = "🔴 Peor"
                    color = "inverse"
                else:
                    estado = "🟡 Normal"
                    color = "off"
                
                st.metric(
                    "Estado Lead Time",
                    estado,
                    f"{diferencia:+.1f} min",
                    delta_color=color
                )
            else:
                st.metric(
                    "Estado Lead Time",
                    "No ingresado"
                )
        
        # Tabs
        tab1, tab2, tab3 = st.tabs(["🗺️ Ruta Óptima", "📋 Tabla de Paradas", "📦 Resumen para Despachos"])
        
        with tab1:
            st.markdown("### 🗺️ Visualización de la Ruta")
            
            # Gráfico de coordenadas
            route_coords = []
            for stop_idx in results['route']:
                stop = st.session_state.stops_data[stop_idx]
                route_coords.append([stop['lon'], stop['lat']])
            
            route_coords_array = np.array(route_coords)
            
            col_a, col_b = st.columns([2, 1])
            
            with col_a:
                # Gráfico de ruta en coordenadas
                import matplotlib.pyplot as plt
                
                fig, ax = plt.subplots(figsize=(10, 8))
                
                # Dibujar la ruta
                ax.plot(route_coords_array[:, 0], route_coords_array[:, 1], 'b-', linewidth=2, alpha=0.6)
                ax.scatter(route_coords_array[:, 0], route_coords_array[:, 1], c='red', s=100, zorder=5)
                
                # Marcar inicio
                ax.scatter(route_coords_array[0, 0], route_coords_array[0, 1], c='green', s=300, marker='*', zorder=6, label='Inicio/Fin')
                
                # Etiquetas
                for i, (lon, lat) in enumerate(route_coords_array[:-1]):  # No etiquetar el regreso
                    ax.annotate(str(i+1), (lon, lat), xytext=(5, 5), textcoords='offset points', fontsize=8)
                
                ax.set_xlabel('Longitud')
                ax.set_ylabel('Latitud')
                ax.set_title('Ruta Optimizada de Entrega')
                ax.legend()
                ax.grid(True, alpha=0.3)
                
                st.pyplot(fig)
            
            with col_b:
                st.markdown("#### 📊 Estadísticas")
                st.markdown(f"""
                - **Algoritmo:** {results['algorithm']}
                - **Velocidad:** {results['avg_speed']} km/h
                - **Hora Inicio:** {results['start_time']}
                - **Distancia Total:** {stats['distancia_total_km']} km
                - **Tiempo Total:** {stats['tiempo_total_estimado_min']:.1f} min
                - **Paradas:** {stats['numero_paradas']}
                """)
                
                # Gráfico de distancia acumulada
                distancias = [p['distancia_acumulada_km'] for p in stats['paradas']]
                
                fig2, ax2 = plt.subplots(figsize=(6, 4))
                ax2.plot(range(len(distancias)), distancias, 'o-', linewidth=2, markersize=6)
                ax2.set_xlabel('Parada #')
                ax2.set_ylabel('Distancia Acumulada (km)')
                ax2.set_title('Progreso de la Ruta')
                ax2.grid(True, alpha=0.3)
                
                st.pyplot(fig2)
        
        with tab2:
            st.markdown("### 📋 Detalle de Paradas")
            
            table_data = []
            for stop_stat in stats['paradas'][:-1]:  # No mostrar el regreso
                stop_idx = stop_stat['indice']
                stop_info = st.session_state.stops_data[stop_idx]
                eta = calculate_eta(results['start_time'], stop_stat['tiempo_estimado_min'])
                
                table_data.append({
                    "Orden": stop_stat['orden'],
                    "Código": stop_info['codigo'],
                    "Nombre": stop_info['nombre'],
                    "Dist. desde Anterior (km)": stop_stat['distancia_desde_anterior_km'],
                    "Dist. Acumulada (km)": stop_stat['distancia_acumulada_km'],
                    "Tiempo Estimado (min)": stop_stat['tiempo_estimado_min'],
                    "ETA": eta
                })
            
            st.dataframe(table_data, use_container_width=True)
        
        with tab3:
            st.markdown("### 📦 Resumen para Programación de Despachos")
            
            # Preparar JSON para exportar
            export_data = export_route_to_json(
                st.session_state.stops_data,
                stats,
                results['algorithm'],
                results['avg_speed'],
                results['start_time']
            )
            
            # Mostrar resumen
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📝 Itinerario Resumido")
                for stop_stat in stats['paradas'][:-1][:5]:  # Primeras 5 paradas
                    stop_idx = stop_stat['indice']
                    stop_info = st.session_state.stops_data[stop_idx]
                    eta = calculate_eta(results['start_time'], stop_stat['tiempo_estimado_min'])
                    st.markdown(f"**{stop_stat['orden']}.** {stop_info['nombre']} - ETA: {eta}")
                
                if len(stats['paradas']) > 6:
                    st.markdown("...")
            
            with col2:
                st.markdown("#### 📊 Totales")
                st.markdown(f"""
                - **Distancia Total:** {stats['distancia_total_km']} km
                - **Tiempo Total:** {stats['tiempo_total_estimado_min']:.1f} min ({format_time_hhmm(stats['tiempo_total_estimado_min'])})
                - **Número de Paradas:** {stats['numero_paradas']}
                - **Hora Inicio:** {results['start_time']}
                - **Hora Fin Estimada:** {calculate_eta(results['start_time'], stats['tiempo_total_estimado_min'])}
                """)
            
            st.markdown("---")
            
            # Botón de exportación
            json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
            
            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
            
            with col_btn1:
                st.download_button(
                    label="📥 Exportar Ruta (JSON)",
                    data=json_str,
                    file_name=f"ruta_optimizada_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            with col_btn2:
                if st.button("👁️ Vista Previa JSON"):
                    st.session_state.show_json_preview = not st.session_state.get('show_json_preview', False)
            
            if st.session_state.get('show_json_preview', False):
                st.markdown("#### 📄 Vista Previa del JSON")
                st.json(export_data)


def mostrar():
    """Función de interfaz para integración con otros módulos"""
    main()


if __name__ == "__main__":
    main()