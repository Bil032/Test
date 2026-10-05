import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(
    page_title="Dashboard de Ventas y Rendimiento Operativo",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilo CSS personalizado para mejorar las métricas y diseño general
st.markdown(
    """
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# 2. CARGA Y PROCESAMIENTO DE DATOS (CON CACHÉ)
@st.cache_data
def cargar_datos():
  # Lee el archivo Excel de la misma carpeta
  df = pd.read_excel("Ventas_y_Rendimiento_Operativo_500.xlsx")

  # Asegurar tipos de datos
  df["Fecha"] = pd.to_datetime(df["Fecha"])

  # Cálculos de Métricas
  df["Venta_Bruta"] = df["Cantidad"] * df["Precio_Unitario"]
  df["Venta_Neta"] = df["Venta_Bruta"] * (1.0 - df["Descuento_Pct"])
  df["Costo_Total"] = df["Cantidad"] * df["Costo_Unitario"]
  df["Ganancia_Neta"] = df["Venta_Neta"] - df["Costo_Total"]
  df["Margen_Pct"] = df["Ganancia_Neta"] / df["Venta_Neta"]

  return df


df_raw = cargar_datos()

# 3. PANEL LATERAL (SIDEBAR) - FILTROS DINÁMICOS
st.sidebar.header("🔍 Filtros de Control")

# Filtro de Rango de Fechas
fecha_min = df_raw["Fecha"].min().date()
fecha_max = df_raw["Fecha"].max().date()

rango_fechas = st.sidebar.date_input(
    "Selecciona el Rango de Fechas",
    value=(fecha_min, fecha_max),
    min_value=fecha_min,
    max_value=fecha_max,
)

# Validar selección de fechas
if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
  f_inicio, f_fin = rango_fechas
else:
  f_inicio, f_fin = fecha_min, fecha_max

# Filtro de Región
regiones_opt = ["Todas"] + sorted(list(df_raw["Region"].unique()))
region_sel = st.sidebar.selectbox("Región", opciones := regiones_opt)

# Filtro de Canal de Venta
canales_opt = ["Todos"] + sorted(list(df_raw["Canal_Venta"].unique()))
canal_sel = st.sidebar.selectbox("Canal de Venta", opciones := canales_opt)

# Filtro de Categoría
categorias_opt = ["Todas"] + sorted(list(df_raw["Categoria"].unique()))
categoria_sel = st.sidebar.selectbox(
    "Categoría de Producto", opciones := categorias_opt
)

# APLICACIÓN DE FILTROS AL DATAFRAME
df_filtrado = df_raw[
    (df_raw["Fecha"].dt.date >= f_inicio) & (df_raw["Fecha"].dt.date <= f_fin)
]

if region_sel != "Todas":
  df_filtrado = df_filtrado[df_filtrado["Region"] == region_sel]

if canal_sel != "Todos":
  df_filtrado = df_filtrado[df_filtrado["Canal_Venta"] == canal_sel]

if categoria_sel != "Todas":
  df_filtrado = df_filtrado[df_filtrado["Categoria"] == categoria_sel]


# 4. ENCABEZADO DEL DASHBOARD
st.title("📊 Dashboard de Ventas y Rendimiento Operativo")
st.markdown(
    "Análisis interactivo de indicadores clave de desempeño (KPIs) y gráficos"
    " dinámicos."
)
st.divider()

# Validar si el filtro devuelve datos
if df_filtrado.empty:
  st.warning(
      "⚠️ No se encontraron registros con los filtros seleccionados."
      " Por favor, ajusta los criterios en el panel lateral."
  )
else:
  # 5. TARJETAS DE KPIS (TARJETAS MONITOREO)
  col1, col2, col3, col4 = st.columns(4)

  venta_neta_total = df_filtrado["Venta_Neta"].sum()
  ganancia_neta_total = df_filtrado["Ganancia_Neta"].sum()
  margen_promedio = (
      ganancia_neta_total / venta_neta_total if venta_neta_total > 0 else 0
  )
  ticket_promedio = df_filtrado["Venta_Neta"].mean()

  col1.metric("💰 Venta Neta Total", f"${venta_neta_total:,.2f}")
  col2.metric("📈 Ganancia Neta", f"${ganancia_neta_total:,.2f}")
  col3.metric("🎯 Margen Operativo %", f"{margen_promedio:.1%}")
  col4.metric("🛒 Ticket Promedio (AOV)", f"${ticket_promedio:,.2f}")

  st.divider()

  # 6. MATRIZ DE VISUALIZACIÓN 2x2
  col_graf1, col_graf2 = st.columns(2)

  # [0, 0]: Evolución mensual (Línea + Fill)
  with col_graf1:
    df_evo = (
        df_filtrado.set_index("Fecha")
        .resample("ME")["Venta_Neta"]
        .sum()
        .reset_index()
    )
    df_evo["Fecha_Str"] = df_evo["Fecha"].dt.strftime("%Y-%m")

    fig1 = px.line(
        df_evo,
        x="Fecha_Str",
        y="Venta_Neta",
        title="<b>Evolución Mensual de Ventas Netas</b>",
        labels={"Fecha_Str": "Mes", "Venta_Neta": "Venta Neta ($)"},
        markers=True,
    )
    fig1.update_traces(
        fill="tozeroy",
        fillcolor="rgba(31, 119, 180, 0.2)",
        line_color="#1f77b4",
        line_width=3,
    )
    fig1.update_layout(
        template="plotly_white",
        yaxis_tickprefix="$",
        yaxis_tickformat=",",
        height=380,
    )
    st.plotly_chart(fig1, use_container_width=True)

  # [0, 1]: Ganancia por Categoría (Barras horizontales ordenadas)
  with col_graf2:
    df_cat = (
        df_filtrado.groupby("Categoria")["Ganancia_Neta"]
        .sum()
        .reset_index()
        .sort_values("Ganancia_Neta", ascending=True)
    )

    fig2 = px.bar(
        df_cat,
        x="Ganancia_Neta",
        y="Categoria",
        orientation="h",
        title="<b>Ganancia Neta por Categoría</b>",
        labels={"Ganancia_Neta": "Ganancia Neta ($)", "Categoria": ""},
        text_auto="$,.0f",
        color_discrete_sequence=["#2ca02c"],
    )
    fig2.update_traces(textposition="outside")
    fig2.update_layout(
        template="plotly_white",
        xaxis_tickprefix="$",
        xaxis_tickformat=",",
        height=380,
    )
    st.plotly_chart(fig2, use_container_width=True)

  col_graf3, col_graf4 = st.columns(2)

  # [1, 0]: Participación de venta por canal (Gráfico Donut)
  with col_graf3:
    df_canal = (
        df_filtrado.groupby("Canal_Venta")["Venta_Neta"].sum().reset_index()
    )

    fig3 = px.pie(
        df_canal,
        values="Venta_Neta",
        names="Canal_Venta",
        title="<b>Participación de Ventas por Canal</b>",
        hole=0.5,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig3.update_traces(
        textinfo="percent+label", textposition="inside", fontweight="bold"
    )
    fig3.update_layout(template="plotly_white", height=380, showlegend=False)
    st.plotly_chart(fig3, use_container_width=True)

  # [1, 1]: Margen Operativo % Promedio por Región (Barras verticales)
  with col_graf4:
    df_reg = (
        df_filtrado.groupby("Region")["Margen_Pct"]
        .mean()
        .reset_index()
        .sort_values("Margen_Pct", ascending=False)
    )
    df_reg["Margen_Pct_Display"] = df_reg["Margen_Pct"] * 100

    fig4 = px.bar(
        df_reg,
        x="Region",
        y="Margen_Pct_Display",
        title="<b>Margen Operativo Promedio por Región</b>",
        labels={"Region": "Región", "Margen_Pct_Display": "Margen (%)"},
        text_auto=".1f",
        color_discrete_sequence=["#ff7f0e"],
    )
    fig4.update_traces(texttemplate="%{y:.1f}%", textposition="outside")
    fig4.update_layout(
        template="plotly_white",
        yaxis_ticksuffix="%",
        height=380,
        yaxis_range=[0, df_reg["Margen_Pct_Display"].max() * 1.2],
    )
    st.plotly_chart(fig4, use_container_width=True)

  # 7. TABLA DE DATOS INTERACTIVA CON OPCIÓN DE DESCARGA
  with st.expander("📋 Ver y Descargar Base de Datos Filtrada"):
    st.dataframe(
        df_filtrado[
            [
                "ID_Orden",
                "Fecha",
                "Region",
                "Canal_Venta",
                "Categoria",
                "Producto",
                "Cantidad",
                "Precio_Unitario",
                "Venta_Neta",
                "Ganancia_Neta",
                "Estado_Envio",
            ]
        ],
        use_container_width=True,
    )

    # Botón para descargar los datos filtrados en CSV
    csv = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Descargar datos filtrados (CSV)",
        data=csv,
        file_name="Ventas_Filtradas.csv",
        mime="text/csv",
    )