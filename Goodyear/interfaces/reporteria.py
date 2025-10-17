
import io
from datetime import datetime
from typing import Tuple
import pandas as pd
import streamlit as st
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from modulos.gestor_usuarios import GestorDB

db = GestorDB()

def _to_datetime(series):
    return pd.to_datetime(series, errors="coerce", utc=True)

def _kpis(df_pedidos: pd.DataFrame, df_despachos: pd.DataFrame, df_reclamos: pd.DataFrame) -> Tuple[float, float, float]:
    """Devuelve: (% entregas a tiempo, tiempo promedio de despacho en días, tasa de reclamos resueltos en %)"""
    pct_tiempo = float("nan")
    if not df_despachos.empty:
        pct_tiempo = 100.0 * (df_despachos["fecha_entrega"] <= df_despachos["fecha_programada"]).mean()

    t_prom = float("nan")
    if not df_despachos.empty:
        t_prom = ((df_despachos["fecha_entrega"] - df_despachos["fecha_pedido"]).dt.total_seconds() / 86400.0).mean()

    tasa_resueltos = float("nan")
    if not df_reclamos.empty:
        tasa_resueltos = 100.0 * (df_reclamos["estado"].str.lower() == "resuelto").mean()

    return float(pct_tiempo), float(t_prom), float(tasa_resueltos)

def _export_excel(df_reclamos, df_pedidos, df_despachos, kpi_dict) -> bytes:
    # Quitar zona horaria de columnas datetime
    for df in [df_reclamos, df_pedidos, df_despachos]:
        for col in df.select_dtypes(include=['datetime64[ns, UTC]', 'datetimetz']).columns:
            df[col] = df[col].dt.tz_localize(None)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_reclamos.to_excel(writer, index=False, sheet_name="Reclamos")
        df_pedidos.to_excel(writer, index=False, sheet_name="Pedidos")
        df_despachos.to_excel(writer, index=False, sheet_name="Despachos")
        pd.DataFrame([kpi_dict]).to_excel(writer, index=False, sheet_name="KPIs")
    return output.getvalue()

def _export_pdf(kpi_dict) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Módulo de Reportería")
    y -= 24
    c.setFont("Helvetica", 11)
    c.drawString(50, y, "Consolidación de pedidos, despachos y reclamos")
    y -= 30

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Indicadores KPI")
    y -= 20
    c.setFont("Helvetica", 11)
    for k, v in kpi_dict.items():
        c.drawString(60, y, f"- {k}: {v}")
        y -= 18

    c.setFont("Helvetica", 9)
    y -= 10
    c.drawString(50, y, f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.showPage()
    c.save()
    return buffer.getvalue()

def mostrar():
    user = st.session_state.get("user")
    if not user or user.get("rol") != "interno":
        st.error("Acceso restringido a personal interno.")
        return

    st.title("Módulo de Reportería")
    st.write("Consolida información de pedidos, despachos y reclamos para la toma de decisiones.")

    reclamos = db.listar_reclamos()
    pedidos = db.listar_pedidos()
    despachos = db.listar_despachos()

    df_reclamos = pd.DataFrame(reclamos)
    df_pedidos = pd.DataFrame(pedidos)
    df_despachos = pd.DataFrame(despachos)

    # Normalización de fechas
    if not df_reclamos.empty:
        df_reclamos["fecha"] = _to_datetime(df_reclamos["fecha"])
    if not df_pedidos.empty:
        df_pedidos["fecha"] = _to_datetime(df_pedidos["fecha"])
    if not df_despachos.empty:
        df_despachos["fecha_pedido"] = _to_datetime(df_despachos["fecha_pedido"])
        df_despachos["fecha_programada"] = _to_datetime(df_despachos["fecha_programada"])
        df_despachos["fecha_entrega"] = _to_datetime(df_despachos["fecha_entrega"])

    st.subheader("Reclamos")
    if df_reclamos.empty:
        st.info("No existen reclamos registrados.")
    else:
        st.dataframe(df_reclamos.sort_values("fecha", ascending=False), use_container_width=True)

    st.subheader("Pedidos")
    if df_pedidos.empty:
        st.info("No existen pedidos registrados.")
    else:
        st.dataframe(df_pedidos.sort_values("fecha", ascending=False), use_container_width=True)

    st.subheader("Despachos")
    if df_despachos.empty:
        st.info("No existen despachos registrados.")
    else:
        df = df_despachos.copy()
        df["lead_time_dias"] = (df["fecha_entrega"] - df["fecha_pedido"]).dt.total_seconds() / 86400.0
        df["entrega_a_tiempo"] = (df["fecha_entrega"] <= df["fecha_programada"])
        st.dataframe(df.sort_values("fecha_entrega", ascending=False), use_container_width=True)

    st.subheader("Indicadores KPI")
    pct_tiempo, t_prom, tasa_resueltos = _kpis(df_pedidos, df_despachos, df_reclamos)

    col1, col2, col3 = st.columns(3)
    col1.metric("% de entregas a tiempo", f"{pct_tiempo:.1f}%" if pd.notna(pct_tiempo) else "N/D")
    col2.metric("Tiempo promedio de despacho", f"{t_prom:.2f} días" if pd.notna(t_prom) else "N/D")
    col3.metric("Tasa de reclamos resueltos", f"{tasa_resueltos:.1f}%" if pd.notna(tasa_resueltos) else "N/D")

    st.subheader("Exportación de reportes")
    kpi_dict = {
        "% entregas a tiempo": f"{pct_tiempo:.1f}%" if pd.notna(pct_tiempo) else "N/D",
        "Tiempo promedio de despacho": f"{t_prom:.2f} días" if pd.notna(t_prom) else "N/D",
        "Tasa de reclamos resueltos": f"{tasa_resueltos:.1f}%" if pd.notna(tasa_resueltos) else "N/D",
    }

    bytes_xlsx = _export_excel(df_reclamos, df_pedidos, df_despachos, kpi_dict)
    st.download_button(
        label="Descargar Excel",
        data=bytes_xlsx,
        file_name=f"reportes_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    bytes_pdf = _export_pdf(kpi_dict)
    st.download_button(
        label="Descargar PDF",
        data=bytes_pdf,
        file_name=f"resumen_kpi_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
