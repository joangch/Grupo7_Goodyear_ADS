from __future__ import annotations

import io
from datetime import datetime
from typing import Tuple, Dict, Any, List

import numpy as np
import pandas as pd
import streamlit as st
import altair as alt
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

try:
    from modulos.gestor_usuarios import GestorDB
    _DB_OK = True
except Exception:
    _DB_OK = False
    GestorDB = None  # type: ignore

PRIMARY = "#01ad91"
PRIMARY_2 = "#0d94ac"
OK = "#0ea35a"
WARN = "#f5a623"
ALERT = "#d9534f"

CSS = f"""
<style>
    .main {{ background: #f6f8fb; }}
    .kpi-card {{
        background:#fff;border:1px solid #eaeef6;border-radius:14px;padding:14px 16px;
        box-shadow:0 8px 24px rgba(30,60,114,0.06)
    }}
    .kpi-title {{ font-size:12px;color:#657389;margin-bottom:4px }}
    .kpi-value {{ font-size:24px;font-weight:800;color:#0f172a }}
    .kpi-help  {{ font-size:11px;color:#8b97a8;margin-top:2px }}
    .panel {{
        padding:16px;border-radius:14px;background:linear-gradient(135deg,{PRIMARY} 0%, {PRIMARY_2} 100%);
        color:#fff;border:1px solid rgba(255,255,255,.2)
    }}
    .stDownloadButton button {{ border-radius:10px; font-weight:700 }}
</style>
"""

def _get_db():
    return GestorDB() if _DB_OK else None


def _to_datetime(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce", utc=True)


def _strip_tz(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.select_dtypes(include=["datetime64[ns, UTC]", "datetimetz"]).columns:
        df[col] = df[col].dt.tz_localize(None)
    return df


def _kpis(df_pedidos: pd.DataFrame, df_despachos: pd.DataFrame, df_reclamos: pd.DataFrame) -> Tuple[float, float, float]:
    pct_tiempo = float("nan")
    if not df_despachos.empty and {"fecha_entrega", "fecha_programada"}.issubset(df_despachos.columns):
        pct_tiempo = 100.0 * (df_despachos["fecha_entrega"] <= df_despachos["fecha_programada"]).mean()
    t_prom = float("nan")
    if not df_despachos.empty and {"fecha_pedido", "fecha_entrega"}.issubset(df_despachos.columns):
        t_prom = ((df_despachos["fecha_entrega"] - df_despachos["fecha_pedido"]).dt.total_seconds() / 86400.0).mean()
    tasa_resueltos = float("nan")
    if not df_reclamos.empty and "estado" in df_reclamos.columns:
        tasa_resueltos = 100.0 * (df_reclamos["estado"].astype(str).str.lower() == "resuelto").mean()
    return float(pct_tiempo), float(t_prom), float(tasa_resueltos)


def _simular_datos(meses: int = 8, semilla: int = 42) -> Dict[str, pd.DataFrame]:
    rng = np.random.default_rng(semilla)
    hoy = pd.Timestamp.utcnow().normalize()
    fechas_ped = pd.date_range(hoy - pd.offsets.MonthBegin(meses - 1), periods=meses, freq="MS")

    clientes = ["Tottus", "Falabella", "Ripley", "Makro", "Maestro", "Sodimac"]
    transportistas = ["TransLima", "Ransa", "Shalom", "Chaski", "Olva"]
    causas = ["Demora transporte", "Error picking", "Falla producto", "Stock insuficiente", "Otro"]

    pedidos = []
    for f in fechas_ped:
        for _ in range(rng.integers(25, 45)):
            pedidos.append({
                "id": int(rng.integers(1_000, 9_999)),
                "fecha": f + pd.Timedelta(days=int(rng.integers(0, 27))),
                "cliente": str(rng.choice(clientes)),
                "estado": str(rng.choice(["Registrado", "Facturado", "Anulado"], p=[0.6, 0.35, 0.05])),
                "monto": float(rng.integers(200, 1200)),
            })
    df_ped = pd.DataFrame(pedidos)
    if not df_ped.empty:
        df_ped["fecha"] = _to_datetime(df_ped["fecha"])

    despachos = []
    for _, row in df_ped.iterrows():
        fp = row["fecha"]
        delta_prog = int(rng.integers(1, 6))
        delta_real = delta_prog + int(rng.integers(-1, 4))
        fecha_prog = fp + pd.Timedelta(days=delta_prog)
        fecha_ent = fp + pd.Timedelta(days=max(0, delta_real))
        despachos.append({
            "id": int(rng.integers(30_000, 90_000)),
            "fecha_pedido": fp,
            "fecha_programada": fecha_prog,
            "fecha_entrega": fecha_ent,
            "transportista": str(rng.choice(transportistas)),
            "estado": str(rng.choice(["Programado", "En tránsito", "Entregado", "Incidencia"], p=[0.1, 0.05, 0.8, 0.05])),
        })
    df_des = pd.DataFrame(despachos)
    if not df_des.empty:
        for c in ["fecha_pedido", "fecha_programada", "fecha_entrega"]:
            df_des[c] = _to_datetime(df_des[c])

    reclamos = []
    recl_count = int(len(df_des) * 0.12) if len(df_des) else 0
    if recl_count:
        idxs = rng.choice(df_des.index, size=recl_count, replace=False)
        for i in idxs:
            d = df_des.loc[i]
            f_recl = d["fecha_entrega"] + pd.Timedelta(days=int(rng.integers(0, 7)))
            resuelto = bool(rng.choice([True, False], p=[0.75, 0.25]))
            reclamos.append({
                "id": int(rng.integers(200_000, 900_000)),
                "fecha": f_recl,
                "cliente": str(rng.choice(clientes)),
                "causa": str(rng.choice(causas)),
                "estado": "Resuelto" if resuelto else "Abierto",
                "detalle": "Auto-generado (demo)",
            })
    df_rec = pd.DataFrame(reclamos)
    if not df_rec.empty:
        df_rec["fecha"] = _to_datetime(df_rec["fecha"])

    return {"reclamos": df_rec, "pedidos": df_ped, "despachos": df_des}


@st.cache_data(show_spinner=False, ttl=60)

def _cargar_data(modo_demo: bool) -> Dict[str, pd.DataFrame]:
    if modo_demo or not _DB_OK:
        return _simular_datos()
    try:
        db = _get_db()
        reclamos = pd.DataFrame(db.listar_reclamos())
        pedidos = pd.DataFrame(db.listar_pedidos())
        despachos = pd.DataFrame(db.listar_despachos())
    except Exception:
        return _simular_datos()

    if not reclamos.empty and "fecha" in reclamos.columns:
        reclamos["fecha"] = _to_datetime(reclamos["fecha"])
    if not pedidos.empty and "fecha" in pedidos.columns:
        pedidos["fecha"] = _to_datetime(pedidos["fecha"])
    if not despachos.empty:
        for c in ["fecha_pedido", "fecha_programada", "fecha_entrega"]:
            if c in despachos.columns:
                despachos[c] = _to_datetime(despachos[c])

    if not despachos.empty and {"fecha_entrega", "fecha_pedido"}.issubset(despachos.columns):
        despachos["lead_time_dias"] = (
            (despachos["fecha_entrega"] - despachos["fecha_pedido"]).dt.total_seconds() / 86400.0
        )
    if not despachos.empty and {"fecha_entrega", "fecha_programada"}.issubset(despachos.columns):
        despachos["entrega_a_tiempo"] = despachos["fecha_entrega"] <= despachos["fecha_programada"]

    return {"reclamos": reclamos, "pedidos": pedidos, "despachos": despachos}


def _export_excel(df_reclamos: pd.DataFrame, df_pedidos: pd.DataFrame, df_despachos: pd.DataFrame, kpi_dict: Dict[str, Any]) -> bytes:
    df_reclamos = _strip_tz(df_reclamos)
    df_pedidos = _strip_tz(df_pedidos)
    df_despachos = _strip_tz(df_despachos)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as w:
        df_reclamos.to_excel(w, index=False, sheet_name="Reclamos")
        df_pedidos.to_excel(w, index=False, sheet_name="Pedidos")
        df_despachos.to_excel(w, index=False, sheet_name="Despachos")
        pd.DataFrame([kpi_dict]).to_excel(w, index=False, sheet_name="KPIs")
    return output.getvalue()


def _export_pdf(kpi_dict: Dict[str, Any], notas: List[str] | None = None) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    y = height - 50

    c.setFillColorRGB(1, 1, 1)
    c.setStrokeColorRGB(0.85, 0.9, 1)
    c.setFillColorRGB(0.12, 0.24, 0.45)
    c.rect(30, y - 10, width - 60, 36, fill=True, stroke=False)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, "Goodyear – Módulo de Reportería")
    y -= 40

    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Indicadores KPI")
    y -= 18
    c.setFont("Helvetica", 10)
    for k, v in kpi_dict.items():
        c.drawString(50, y, f"• {k}: {v}")
        y -= 14

    if notas:
        y -= 8
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Notas / Observaciones")
        y -= 16
        c.setFont("Helvetica", 10)
        for n in notas:
            c.drawString(50, y, f"- {n}")
            y -= 13
            if y < 70:
                c.showPage()
                y = height - 50
                c.setFont("Helvetica", 10)

    y -= 6
    c.setFont("Helvetica", 9)
    c.drawString(40, y, f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.showPage()
    c.save()
    return buf.getvalue()


def _kpi_card(title: str, value: str, help_text: str = "", color: str = PRIMARY_2):
    st.markdown(
        f"""
        <div class=\"kpi-card\">
            <div class=\"kpi-title\">{title}</div>
            <div class=\"kpi-value\" style=\"color:{color}\">{value}</div>
            <div class=\"kpi-help\">{help_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _chart_tendencia_despachos(df: pd.DataFrame):
    if df.empty or "fecha_entrega" not in df.columns:
        return
    serie = (
        df.assign(fecha=df["fecha_entrega"].dt.date)
        .groupby("fecha", as_index=False)
        .size()
        .rename(columns={"size": "despachos"})
    )
    chart = (
        alt.Chart(serie)
        .mark_line(point=True)
        .encode(
            x=alt.X("fecha:T", title="Fecha"),
            y=alt.Y("despachos:Q", title="Despachos"),
            tooltip=["fecha:T", "despachos:Q"],
        )
        .properties(height=260)
    )
    st.altair_chart(chart, use_container_width=True)


def _chart_leadtime_hist(df: pd.DataFrame):
    if df.empty or "lead_time_dias" not in df.columns:
        return
    base = df[["lead_time_dias"]].dropna()
    if base.empty:
        return
    chart = (
        alt.Chart(base)
        .mark_bar()
        .encode(
            x=alt.X("lead_time_dias:Q", bin=alt.Bin(maxbins=24), title="Lead time (días)"),
            y=alt.Y("count():Q", title="Frecuencia"),
            tooltip=[alt.Tooltip("count():Q", title="Registros")],
        )
        .properties(height=260)
    )
    st.altair_chart(chart, use_container_width=True)


def _chart_sla_transportista(df: pd.DataFrame):
    if df.empty or not {"transportista", "entrega_a_tiempo"}.issubset(df.columns):
        return
    agg = (
        df.groupby("transportista", as_index=False)["entrega_a_tiempo"].mean().assign(
            sla=lambda x: (x["entrega_a_tiempo"] * 100).round(1)
        )
    )
    chart = (
        alt.Chart(agg)
        .mark_bar()
        .encode(
            x=alt.X("transportista:N", sort="-y", title="Transportista"),
            y=alt.Y("sla:Q", title="% entregas a tiempo"),
            tooltip=["transportista:N", "sla:Q"],
        )
        .properties(height=260)
    )
    st.altair_chart(chart, use_container_width=True)


def _chart_pareto_causas(df: pd.DataFrame):
    if df.empty or "causa" not in df.columns:
        return
    top = (
        df["causa"].fillna("Sin causa").astype(str).str.strip().replace("", "Sin causa").value_counts().reset_index()
    )
    top.columns = ["causa", "conteo"]
    if top.empty:
        return
    top["acum"] = (top["conteo"].cumsum() / top["conteo"].sum() * 100).round(1)
    bars = alt.Chart(top).mark_bar().encode(
        x=alt.X("causa:N", sort="-y", title="Causa"),
        y=alt.Y("conteo:Q", title="Frecuencia"),
        tooltip=["causa:N", "conteo:Q", "acum:Q"],
    )
    line = alt.Chart(top).mark_line(point=True).encode(
        x="causa:N",
        y=alt.Y("acum:Q", axis=alt.Axis(title="% acumulado", grid=False)),
    )
    chart = alt.layer(bars, line).resolve_scale(y="independent").properties(height=300)
    st.altair_chart(chart, use_container_width=True)


def _chart_calor_mes_transportista(df: pd.DataFrame):
    if df.empty or not {"transportista", "fecha_entrega", "entrega_a_tiempo"}.issubset(df.columns):
        return
    tmp = df.copy()
    tmp["mes"] = tmp["fecha_entrega"].dt.to_period("M").astype(str)
    agg = tmp.groupby(["mes", "transportista"])["entrega_a_tiempo"].mean().reset_index()
    agg["sla"] = (agg["entrega_a_tiempo"] * 100).round(1)
    chart = (
        alt.Chart(agg)
        .mark_rect()
        .encode(
            x=alt.X("mes:N", title="Mes"),
            y=alt.Y("transportista:N", title="Transportista"),
            color=alt.Color("sla:Q", title="% a tiempo"),
            tooltip=["mes", "transportista", "sla"],
        )
        .properties(height=260)
    )
    st.altair_chart(chart, use_container_width=True)


def _sidebar_filtros(dfs: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    st.sidebar.header("Filtros")
    df_reclamos, df_pedidos, df_despachos = dfs["reclamos"], dfs["pedidos"], dfs["despachos"]

    fechas = []
    for df, col in [(df_reclamos, "fecha"), (df_pedidos, "fecha"), (df_despachos, "fecha_entrega")]:
        if not df.empty and col in df.columns:
            fechas.append(df[col].dropna())
    if fechas:
        fmin = min(s.min() for s in fechas).date()
        fmax = max(s.max() for s in fechas).date()
        rango = st.sidebar.date_input("Rango de fechas", value=(fmin, fmax))
    else:
        rango = None

    filtros: Dict[str, Any] = {"rango": rango}

    if not df_despachos.empty and "transportista" in df_despachos.columns:
        ops = ["(Todos)"] + sorted(df_despachos["transportista"].dropna().astype(str).unique().tolist())
        filtros["transportista"] = st.sidebar.selectbox("Transportista", ops)

    if not df_despachos.empty and "estado" in df_despachos.columns:
        ops = ["(Todos)"] + sorted(df_despachos["estado"].dropna().astype(str).unique().tolist())
        filtros["estado"] = st.sidebar.selectbox("Estado de despacho", ops)

    if not df_reclamos.empty and "causa" in df_reclamos.columns:
        ops = ["(Todos)"] + sorted(df_reclamos["causa"].dropna().astype(str).unique().tolist())
        filtros["causa"] = st.sidebar.selectbox("Causa de reclamo", ops)

    st.sidebar.markdown("---")
    filtros["incluir_notas"] = st.sidebar.checkbox("Agregar observaciones en PDF", value=True)
    filtros["nota_texto"] = (
        st.sidebar.text_area("Observaciones (PDF)", value="Reporte generado desde el Módulo de Reportería.", height=70)
        if filtros["incluir_notas"]
        else ""
    )

    return filtros


def _aplicar_filtros(dfs: Dict[str, pd.DataFrame], filtros: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
    df_reclamos = dfs["reclamos"].copy()
    df_pedidos = dfs["pedidos"].copy()
    df_despachos = dfs["despachos"].copy()

    for df in [df_reclamos, df_pedidos, df_despachos]:
        for col in df.select_dtypes(include=["datetimetz"]).columns:
            df[col] = df[col].dt.tz_localize(None)

    rango = filtros.get("rango")
    if rango and isinstance(rango, (list, tuple)) and len(rango) == 2:
        d1 = pd.to_datetime(rango[0])
        d2 = pd.to_datetime(rango[1]) + pd.Timedelta(days=1)
        if not df_reclamos.empty and "fecha" in df_reclamos.columns:
            df_reclamos = df_reclamos[(df_reclamos["fecha"] >= d1) & (df_reclamos["fecha"] < d2)]
        if not df_pedidos.empty and "fecha" in df_pedidos.columns:
            df_pedidos = df_pedidos[(df_pedidos["fecha"] >= d1) & (df_pedidos["fecha"] < d2)]
        if not df_despachos.empty and "fecha_entrega" in df_despachos.columns:
            df_despachos = df_despachos[(df_despachos["fecha_entrega"] >= d1) & (df_despachos["fecha_entrega"] < d2)]

    trp = filtros.get("transportista")
    if trp and trp != "(Todos)" and not df_despachos.empty and "transportista" in df_despachos.columns:
        df_despachos = df_despachos[df_despachos["transportista"].astype(str) == trp]

    est = filtros.get("estado")
    if est and est != "(Todos)" and not df_despachos.empty and "estado" in df_despachos.columns:
        df_despachos = df_despachos[df_despachos["estado"].astype(str) == est]

    causa = filtros.get("causa")
    if causa and causa != "(Todos)" and not df_reclamos.empty and "causa" in df_reclamos.columns:
        df_reclamos = df_reclamos[df_reclamos["causa"].astype(str) == causa]

    return {"reclamos": df_reclamos, "pedidos": df_pedidos, "despachos": df_despachos}


def _recomendaciones(pct_tiempo: float, t_prom: float, df_desp: pd.DataFrame) -> List[str]:
    tips: List[str] = []
    if pd.notna(pct_tiempo):
        if pct_tiempo >= 95:
            tips.append("Excelente nivel de servicio general (≥95%). Mantener acuerdos con transportistas.")
        elif pct_tiempo >= 90:
            tips.append("Buen nivel de servicio (90–95%). Revisar outliers por zona/transporte.")
        else:
            tips.append("Servicio <90%. Priorizar mejora con los 2 transportistas de menor SLA.")
    if pd.notna(t_prom):
        if t_prom <= 4:
            tips.append("Lead time saludable (≤4 días).")
        elif t_prom <= 6:
            tips.append("Lead time moderado (4–6 días). Ajustar programación de despacho.")
        else:
            tips.append("Lead time alto (>6 días). Revisar cuellos de botella en preparación y ruta.")
    if not df_desp.empty and {"transportista", "entrega_a_tiempo"}.issubset(df_desp.columns):
        slas = (df_desp.groupby("transportista")["entrega_a_tiempo"].mean() * 100).sort_values()
        malos = slas.head(2)
        if not malos.empty:
            lows = ", ".join([f"{k} ({v:.1f}%)" for k, v in malos.items()])
            tips.append(f"Transportistas a mejorar: {lows}.")
    return tips


def mostrar():
    user = st.session_state.get("user", {"rol": "interno", "nombre": "demo"})
    default_demo = True if user.get("rol") != "interno" else False
    modo_demo = st.sidebar.toggle("Modo DEMO (simular datos)", value=default_demo)

    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class=\"panel\">
            <h2 style=\"margin:0;\">📊 Módulo de Reportería</h2>
            <div style=\"opacity:.9;margin-top:6px\">
                Consolidación de pedidos, despachos y reclamos para la toma de decisiones.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")

    dfs = _cargar_data(modo_demo)
    filtros = _sidebar_filtros(dfs)
    dfs_f = _aplicar_filtros(dfs, filtros)

    df_reclamos = dfs_f["reclamos"]
    df_pedidos = dfs_f["pedidos"]
    df_despachos = dfs_f["despachos"]

    st.subheader("Indicadores KPI")
    pct_tiempo, t_prom, tasa_resueltos = _kpis(df_pedidos, df_despachos, df_reclamos)

    col1, col2, col3 = st.columns(3)
    with col1:
        color = OK if pd.notna(pct_tiempo) and pct_tiempo >= 95 else (WARN if pd.notna(pct_tiempo) and pct_tiempo >= 90 else ALERT)
        _kpi_card("% de entregas a tiempo", f"{pct_tiempo:.1f}%" if pd.notna(pct_tiempo) else "N/D", "Entrega ≤ fecha programada", color)
    with col2:
        color = OK if pd.notna(t_prom) and t_prom <= 4 else (WARN if pd.notna(t_prom) and t_prom <= 6 else ALERT)
        _kpi_card("Tiempo promedio de despacho", f"{t_prom:.2f} días" if pd.notna(t_prom) else "N/D", "Desde pedido hasta entrega", color)
    with col3:
        color = OK if pd.notna(tasa_resueltos) and tasa_resueltos >= 90 else (WARN if pd.notna(tasa_resueltos) and tasa_resueltos >= 75 else ALERT)
        _kpi_card("Tasa de reclamos resueltos", f"{tasa_resueltos:.1f}%" if pd.notna(tasa_resueltos) else "N/D", "Estado = Resuelto", color)

    st.markdown("---")

    st.subheader("Tablero de análisis")
    a1, a2 = st.columns(2)
    with a1:
        st.markdown("**Tendencia de despachos**")
        _chart_tendencia_despachos(df_despachos)
    with a2:
        st.markdown("**Distribución del lead time**")
        _chart_leadtime_hist(df_despachos)

    b1, b2 = st.columns(2)
    with b1:
        st.markdown("**SLA por transportista**")
        _chart_sla_transportista(df_despachos)
    with b2:
        st.markdown("**On-time por Mes × Transportista**")
        _chart_calor_mes_transportista(df_despachos)

    st.markdown("**Pareto de causas de reclamos**")
    _chart_pareto_causas(df_reclamos)

    st.subheader("Reclamos")
    if df_reclamos.empty:
        st.info("No existen reclamos para el filtro actual.")
    else:
        cols = list(df_reclamos.columns)
        orden = [c for c in ["id", "fecha", "cliente", "causa", "estado", "detalle"] if c in cols]
        cols_final = orden + [c for c in cols if c not in orden]
        st.dataframe(
            df_reclamos[cols_final].sort_values([c for c in ["fecha"] if c in cols_final], ascending=False),
            use_container_width=True,
        )

    st.subheader("Pedidos")
    if df_pedidos.empty:
        st.info("No existen pedidos para el filtro actual.")
    else:
        cols = list(df_pedidos.columns)
        orden = [c for c in ["id", "fecha", "cliente", "estado", "monto"] if c in cols]
        cols_final = orden + [c for c in cols if c not in orden]
        st.dataframe(
            df_pedidos[cols_final].sort_values([c for c in ["fecha"] if c in cols_final], ascending=False),
            use_container_width=True,
        )

    st.subheader("Despachos")
    if df_despachos.empty:
        st.info("No existen despachos para el filtro actual.")
    else:
        dfv = df_despachos.copy()
        if "lead_time_dias" not in dfv.columns and {"fecha_entrega", "fecha_pedido"}.issubset(dfv.columns):
            dfv["lead_time_dias"] = (dfv["fecha_entrega"] - dfv["fecha_pedido"]).dt.total_seconds() / 86400.0
        if "entrega_a_tiempo" not in dfv.columns and {"fecha_entrega", "fecha_programada"}.issubset(dfv.columns):
            dfv["entrega_a_tiempo"] = dfv["fecha_entrega"] <= dfv["fecha_programada"]
        cols = list(dfv.columns)
        orden = [
            c for c in [
                "id", "fecha_pedido", "fecha_programada", "fecha_entrega", "transportista", "estado", "lead_time_dias", "entrega_a_tiempo"
            ] if c in cols
        ]
        cols_final = orden + [c for c in cols if c not in orden]
        st.dataframe(
            dfv[cols_final].sort_values([c for c in ["fecha_entrega"] if c in cols_final], ascending=False),
            use_container_width=True,
        )

    st.subheader("💡 Recomendaciones")
    for tip in _recomendaciones(pct_tiempo, t_prom, df_despachos):
        st.markdown(f"- {tip}")

    st.subheader("Exportación de reportes")
    kpi_dict = {
        "% entregas a tiempo": f"{pct_tiempo:.1f}%" if pd.notna(pct_tiempo) else "N/D",
        "Tiempo promedio de despacho": f"{t_prom:.2f} días" if pd.notna(t_prom) else "N/D",
        "Tasa de reclamos resueltos": f"{tasa_resueltos:.1f}%" if pd.notna(tasa_resueltos) else "N/D",
    }

    colx, coly = st.columns([2, 1])
    with colx:
        bytes_xlsx = _export_excel(df_reclamos, df_pedidos, df_despachos, kpi_dict)
        st.download_button(
            label="⬇️ Descargar Excel (con filtros)",
            data=bytes_xlsx,
            file_name=f"reportes_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with coly:
        notas = [filtros.get("nota_texto")] if filtros.get("incluir_notas") and filtros.get("nota_texto") else []
        bytes_pdf = _export_pdf(kpi_dict, notas)
        st.download_button(
            label="⬇️ Descargar PDF (resumen KPI)",
            data=bytes_pdf,
            file_name=f"resumen_kpi_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
