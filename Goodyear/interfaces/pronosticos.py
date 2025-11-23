
"""Sistema de Pronóstico de Demanda - Goodyear
Módulo de Machine Learning con Streamlit
Versión: 2.0
"""

import streamlit as st
import numpy as np
from datetime import datetime, timedelta
# Import scikit-learn lazily inside functions to avoid breaking app startup
# if scikit-learn is not installed in the environment. We provide numpy
# fallbacks for core functionality so the interface remains usable.
import json
import warnings
warnings.filterwarnings('ignore')

from core.pronosticos_db import fetch_series


class ForecastModel:
    """Modelos de pronóstico usando Machine Learning"""
    
    @staticmethod
    def arima_forecast(data, periods=3):
        """Pronóstico usando ARIMA simplificado (Moving Average)"""
        try:
            window = min(3, len(data))
            weights = np.exp(np.linspace(-1, 0, window))
            weights /= weights.sum()
            
            forecast = []
            confidence_lower = []
            confidence_upper = []
            
            data_copy = data.copy()
            
            for i in range(periods):
                recent_data = data_copy[-window:]
                pred = np.average(recent_data, weights=weights)
                std = np.std(recent_data)
                
                forecast.append(pred)
                confidence_lower.append(max(0, pred - 1.96 * std))
                confidence_upper.append(pred + 1.96 * std)
                
                data_copy = np.append(data_copy, pred)
            
            return forecast, confidence_lower, confidence_upper
        except Exception as e:
            st.error(f"Error en ARIMA: {e}")
            return None, None, None
    
    @staticmethod
    def regression_forecast(data, periods=3):
        """Pronóstico usando Regresión Lineal"""
        try:
            n = len(data)
            X = np.arange(n).reshape(-1, 1)
            y = data
            
            # Features temporales
            X_features = np.column_stack([
                X,
                np.sin(2 * np.pi * X / 12),
                np.cos(2 * np.pi * X / 12)
            ])
            
            try:
                from sklearn.linear_model import LinearRegression
                model = LinearRegression()
                model.fit(X_features, y)
                predict_fn = lambda Xp: model.predict(Xp)
            except Exception:
                # Fallback: simple least-squares with intercept using numpy
                Xf = np.hstack([np.ones((X_features.shape[0], 1)), X_features])
                beta, *_ = np.linalg.lstsq(Xf, y, rcond=None)
                def predict_fn(Xp):
                    Xp_f = np.hstack([np.ones((Xp.shape[0], 1)), Xp])
                    return Xp_f.dot(beta)
            
            # Predicción
            future_X = np.arange(n, n + periods).reshape(-1, 1)
            future_features = np.column_stack([
                future_X,
                np.sin(2 * np.pi * future_X / 12),
                np.cos(2 * np.pi * future_X / 12)
            ])
            
            forecast = predict_fn(future_features)
            
            # Intervalos de confianza
            residuals = y - predict_fn(X_features)
            std = np.std(residuals)
            
            confidence_lower = [max(0, f - 1.96 * std) for f in forecast]
            confidence_upper = [f + 1.96 * std for f in forecast]
            
            return forecast.tolist(), confidence_lower, confidence_upper
        except Exception as e:
            st.error(f"Error en Regresión: {e}")
            return None, None, None
    
    @staticmethod
    def prophet_forecast(data, periods=3):
        """Pronóstico usando descomposición estacional"""
        try:
            n = len(data)
            
            # Calcular tendencia
            X = np.arange(n).reshape(-1, 1)
            try:
                from sklearn.linear_model import LinearRegression
                model = LinearRegression()
                model.fit(X, data)
                trend = model.predict(X)
                pred_fn = lambda Xp: model.predict(Xp)
            except Exception:
                Xf = np.hstack([np.ones((X.shape[0], 1)), X])
                beta, *_ = np.linalg.lstsq(Xf, data, rcond=None)
                def pred_fn(Xp):
                    Xp_f = np.hstack([np.ones((Xp.shape[0], 1)), Xp])
                    return Xp_f.dot(beta)
                trend = pred_fn(X)
            
            # Estacionalidad
            seasonal = data - trend
            seasonal_period = 12 if n >= 12 else n
            seasonal_pattern = seasonal[-seasonal_period:]
            
            # Proyección
            future_X = np.arange(n, n + periods).reshape(-1, 1)
            trend_forecast = pred_fn(future_X)
            
            # Agregar estacionalidad
            seasonal_forecast = [seasonal_pattern[i % len(seasonal_pattern)] for i in range(periods)]
            forecast = trend_forecast + seasonal_forecast
            
            # Intervalos
            std = np.std(data[-12:]) if n >= 12 else np.std(data)
            confidence_lower = [max(0, f - 1.96 * std) for f in forecast]
            confidence_upper = [f + 1.96 * std for f in forecast]
            
            return forecast.tolist(), confidence_lower, confidence_upper
        except Exception as e:
            st.error(f"Error en Prophet: {e}")
            return None, None, None
    
    @staticmethod
    def calculate_metrics(actual, predicted):
        """Calcula métricas de precisión"""
        try:
            from sklearn.metrics import mean_absolute_error, mean_squared_error
            mae = mean_absolute_error(actual, predicted)
            rmse = np.sqrt(mean_squared_error(actual, predicted))
        except Exception:
            a = np.array(actual)
            p = np.array(predicted)
            mae = float(np.mean(np.abs(a - p)))
            rmse = float(np.sqrt(np.mean((a - p) ** 2)))

        mape = np.mean(np.abs((np.array(actual) - np.array(predicted)) / np.where(np.array(actual) != 0, np.array(actual), 1))) * 100
        
        return {
            'MAE': round(mae, 2),
            'RMSE': round(rmse, 2),
            'MAPE': round(mape, 2)
        }


# Note: Removed DataGenerator (synthetic data) as DB will always be present.
def _empty_data_structure():
    return {'fecha': [], 'eagle_f1': [], 'assurance': [], 'wrangler': [], 'efficientgrip': []}


def plot_forecast_simple(historical, forecast, lower, upper, dates_hist, dates_fore):
    """Crea gráfico ASCII simple para Streamlit"""
    
    # Combinar datos
    all_values = list(historical) + forecast
    
    # Crear visualización con caracteres
    chart_data = {
        'Período': list(range(len(historical))) + list(range(len(historical), len(historical) + len(forecast))),
        'Histórico': list(historical) + [None] * len(forecast),
        'Pronóstico': [None] * len(historical) + forecast,
        'Límite Inferior': [None] * len(historical) + lower,
        'Límite Superior': [None] * len(historical) + upper
    }
    
    st.line_chart(chart_data, x='Período')


def main():
    """Aplicación principal de Streamlit"""
    
    # Configuración de página
    st.set_page_config(
        page_title="Goodyear - Pronóstico de Demanda",
        page_icon="🚗",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS personalizado
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
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
        <div style='background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                    padding: 30px; border-radius: 10px; margin-bottom: 20px;'>
            <h1 style='color: white; text-align: center; margin: 0;'>
                🚗 Goodyear - Sistema de Pronóstico de Demanda
            </h1>
            <p style='color: white; text-align: center; margin: 10px 0 0 0; opacity: 0.9;'>
                Predicción de Ventas con Machine Learning
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Inicializar datos en session_state: preferir datos desde la BD si existen
    if 'data' not in st.session_state:
        try:
            # Leer directamente la tabla real `pronostico_historial`
            db_data = fetch_series('pronostico_historial')
            if db_data and len(db_data.get('fecha', [])) > 0:
                st.session_state.data = db_data
            else:
                st.error("No se encontraron datos en la tabla 'pronostico_historial'.")
                st.session_state.data = _empty_data_structure()
        except Exception as e:
            # Si falla la DB, mostrar error y usar estructura vacía
            st.error(f"Error al leer la base de datos: {e}")
            st.session_state.data = _empty_data_structure()
    
    if 'forecast_results' not in st.session_state:
        st.session_state.forecast_results = None
    
    # Sidebar - Panel de Control
    with st.sidebar:
        st.header("⚙️ Panel de Control")
        st.markdown("---")
        
        # Sección: Datos
        st.subheader("📊 Gestión de Datos")
        
        if st.button("🔄 Cargar Datos de Ejemplo (DB)", use_container_width=True):
            try:
                # Cargar desde la tabla real `pronostico_historial`
                st.session_state.data = fetch_series('pronostico_historial')
                st.success("✓ Datos cargados desde la base de datos (pronostico_historial)")
            except Exception as e:
                st.warning(f"No se pudo cargar desde BD: {e}.")
                st.session_state.data = _empty_data_structure()
                st.info("Se ha asignado una estructura vacía. Verifica la conexión a la base de datos.")
        
        st.markdown("---")
        
        # Sección: Configuración
        st.subheader("🤖 Configuración")
        
        model_options = {
            'Eagle F1 (Alto Rendimiento)': 'eagle_f1',
            'Assurance (Confort)': 'assurance',
            'Wrangler (SUV/4x4)': 'wrangler',
            'EfficientGrip (Eficiencia)': 'efficientgrip'
        }
        
        selected_model_name = st.selectbox(
            "Modelo de Llanta:",
            options=list(model_options.keys())
        )
        selected_model = model_options[selected_model_name]
        
        algorithm_options = {
            'Prophet (Recomendado)': 'prophet',
            'ARIMA (Clásico)': 'arima',
            'Regresión Lineal': 'regression'
        }
        
        selected_algo_name = st.selectbox(
            "Algoritmo de ML:",
            options=list(algorithm_options.keys())
        )
        selected_algorithm = algorithm_options[selected_algo_name]
        
        horizon = st.slider(
            "Horizonte de Pronóstico (meses):",
            min_value=1,
            max_value=6,
            value=3
        )
        
        st.markdown("---")
        
        # Botón principal
        if st.button("🚀 GENERAR PRONÓSTICO", use_container_width=True, type="primary"):
            with st.spinner("Entrenando modelo..."):
                try:
                    # Obtener datos
                    historical_data = np.array([st.session_state.data[selected_model][i] 
                                              for i in range(len(st.session_state.data['fecha']))])
                    
                    # Ejecutar modelo
                    if selected_algorithm == 'arima':
                        forecast, lower, upper = ForecastModel.arima_forecast(historical_data, horizon)
                    elif selected_algorithm == 'regression':
                        forecast, lower, upper = ForecastModel.regression_forecast(historical_data, horizon)
                    else:
                        forecast, lower, upper = ForecastModel.prophet_forecast(historical_data, horizon)
                    
                    if forecast:
                        # Calcular métricas
                        train_size = int(len(historical_data) * 0.8)
                        train_data = historical_data[:train_size]
                        test_data = historical_data[train_size:]
                        
                        if selected_algorithm == 'arima':
                            val_forecast, _, _ = ForecastModel.arima_forecast(train_data, len(test_data))
                        elif selected_algorithm == 'regression':
                            val_forecast, _, _ = ForecastModel.regression_forecast(train_data, len(test_data))
                        else:
                            val_forecast, _, _ = ForecastModel.prophet_forecast(train_data, len(test_data))
                        
                        metrics = ForecastModel.calculate_metrics(test_data, np.array(val_forecast))
                        
                        # Guardar resultados
                        st.session_state.forecast_results = {
                            'model': selected_model,
                            'model_name': selected_model_name,
                            'algorithm': selected_algo_name.split(' ')[0],
                            'horizon': horizon,
                            'historical': historical_data,
                            'forecast': forecast,
                            'lower': lower,
                            'upper': upper,
                            'metrics': metrics
                        }
                        
                        st.success("✓ Pronóstico generado exitosamente!")
                    else:
                        st.error("Error al generar pronóstico")
                        
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    # Main Content
    if st.session_state.forecast_results:
        results = st.session_state.forecast_results
        
        # Métricas
        st.subheader("📊 Métricas del Modelo")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("MAE", f"{results['metrics']['MAE']:.2f}")
        with col2:
            st.metric("RMSE", f"{results['metrics']['RMSE']:.2f}")
        with col3:
            mape_val = results['metrics']['MAPE']
            st.metric("MAPE", f"{mape_val:.2f}%")
        with col4:
            if mape_val < 10:
                st.metric("Estado", "Excelente ✓")
            elif mape_val < 20:
                st.metric("Estado", "Bueno ⚠")
            else:
                st.metric("Estado", "Regular ✗")
        
        st.markdown("---")
        
        # Tabs
        tab1, tab2, tab3 = st.tabs(["📈 Gráfico", "📋 Datos Históricos", "🔍 Valores Proyectados"])
        
        with tab1:
            st.subheader(f"Pronóstico de Demanda - {results['model_name']}")
            st.caption(f"Algoritmo: {results['algorithm']} | Horizonte: {results['horizon']} meses")
            
            # Preparar datos para gráfico
            historical = results['historical']
            forecast = results['forecast']
            lower = results['lower']
            upper = results['upper']
            
            # Crear DataFrame para Streamlit
            import io
            
            # Gráfico con line_chart nativo
            n_hist = len(historical)
            chart_dict = {}
            
            # Histórico
            for i in range(n_hist):
                chart_dict[i] = {'Histórico': historical[i], 'Pronóstico': None}
            
            # Pronóstico
            for i, (f, l, u) in enumerate(zip(forecast, lower, upper)):
                idx = n_hist + i
                chart_dict[idx] = {
                    'Histórico': None,
                    'Pronóstico': f,
                    'Límite Inferior': l,
                    'Límite Superior': u
                }
            
            # Convertir a formato para Streamlit
            chart_data = []
            for period, values in chart_dict.items():
                row = {'Período': period}
                row.update(values)
                chart_data.append(row)
            
            # Mostrar gráfico
            st.line_chart(chart_data, x='Período', y=['Histórico', 'Pronóstico', 'Límite Inferior', 'Límite Superior'])
            
            st.info("📌 La línea vertical imaginaria separa el histórico del pronóstico")
        
        with tab2:
            st.subheader("Datos Históricos de Ventas")
            
            # Crear tabla
            table_data = []
            for i, fecha in enumerate(st.session_state.data['fecha']):
                table_data.append({
                    'Fecha': fecha,
                    'Eagle F1': st.session_state.data['eagle_f1'][i],
                    'Assurance': st.session_state.data['assurance'][i],
                    'Wrangler': st.session_state.data['wrangler'][i],
                    'EfficientGrip': st.session_state.data['efficientgrip'][i]
                })
            
            st.dataframe(table_data, use_container_width=True)
        
        with tab3:
            st.subheader("Valores Proyectados")
            
            last_date = datetime.strptime(st.session_state.data['fecha'][-1], '%Y-%m-%d')
            
            projection_data = []
            for i, (pred, low, high) in enumerate(zip(forecast, lower, upper)):
                future_date = last_date + timedelta(days=30*(i+1))
                projection_data.append({
                    'Mes': future_date.strftime('%Y-%m'),
                    'Pronóstico': int(pred),
                    'Límite Inferior': int(low),
                    'Límite Superior': int(high),
                    'Rango': f"±{int(high - pred)}"
                })
            
            st.dataframe(projection_data, use_container_width=True)
            
            # Recomendaciones
            st.markdown("---")
            st.subheader("💡 Recomendaciones")
            
            avg_forecast = np.mean(forecast)
            avg_historical = np.mean(results['historical'][-6:])
            
            if avg_forecast > avg_historical * 1.1:
                st.success("📈 Tendencia CRECIENTE detectada. Recomendación: Incrementar inventario en 15%")
            elif avg_forecast < avg_historical * 0.9:
                st.warning("📉 Tendencia DECRECIENTE detectada. Recomendación: Optimizar inventario")
            else:
                st.info("➡️ Demanda ESTABLE. Mantener niveles actuales de inventario")
        
        # Exportar resultados
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        
        with col2:
            if st.button("📥 Exportar Resultados", use_container_width=True):
                # Crear JSON
                export_data = {
                    'metadata': {
                        'modelo': results['model_name'],
                        'algoritmo': results['algorithm'],
                        'horizonte': results['horizon'],
                        'fecha_generacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    },
                    'metricas': results['metrics'],
                    'pronosticos': [
                        {
                            'mes': (last_date + timedelta(days=30*(i+1))).strftime('%Y-%m'),
                            'pronostico': int(forecast[i]),
                            'limite_inferior': int(lower[i]),
                            'limite_superior': int(upper[i])
                        }
                        for i in range(len(forecast))
                    ]
                }
                
                st.download_button(
                    label="Descargar JSON",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"pronostico_{results['model']}_{datetime.now().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
    
    else:
        # Estado inicial
        st.info("👈 Configure los parámetros en el panel lateral y haga clic en 'GENERAR PRONÓSTICO'")
        
        st.subheader("📊 Vista Previa de Datos")
        
        # Mostrar muestra de datos
        if st.session_state.data:
            preview_data = []
            for i in range(min(10, len(st.session_state.data['fecha']))):
                preview_data.append({
                    'Fecha': st.session_state.data['fecha'][i],
                    'Eagle F1': st.session_state.data['eagle_f1'][i],
                    'Assurance': st.session_state.data['assurance'][i],
                    'Wrangler': st.session_state.data['wrangler'][i],
                    'EfficientGrip': st.session_state.data['efficientgrip'][i]
                })
            
            st.dataframe(preview_data, use_container_width=True)
            st.caption(f"Mostrando primeros 10 de {len(st.session_state.data['fecha'])} registros")


if __name__ == "__main__":
    main()

def mostrar():
    main()
