import streamlit as st
import pandas as pd
import plotly.express as px
import base64
import os

# -------------------------------------------------------
# CONFIGURACIÓN GENERAL
# -------------------------------------------------------

st.set_page_config(
    page_title="Control de Residuos No Peligrosos",
    page_icon="♻️",
    layout="wide"
)

# -------------------------------------------------------
# FUNCIONES
# -------------------------------------------------------

def convertir_imagen_base64(ruta_imagen):
    if not os.path.exists(ruta_imagen):
        return None

    with open(ruta_imagen, "rb") as archivo:
        return base64.b64encode(archivo.read()).decode()


def agregar_sello_agua(ruta_sello):
    sello_base64 = convertir_imagen_base64(ruta_sello)

    if sello_base64 is None:
        st.warning(f"No se encontró el sello de agua: {ruta_sello}")
        return

    st.markdown(f"""
    <style>
        .stApp::before {{
            content: "";
            position: fixed;
            top: 52%;
            left: 50%;
            width: 560px;
            height: 560px;
            background-image: url("data:image/png;base64,{sello_base64}");
            background-repeat: no-repeat;
            background-position: center;
            background-size: contain;
            opacity: 0.045;
            transform: translate(-50%, -50%);
            z-index: 0;
            pointer-events: none;
        }}

        .block-container {{
            position: relative;
            z-index: 1;
        }}
    </style>
    """, unsafe_allow_html=True)


def formato_pesos(valor):
    try:
        valor = int(round(float(valor), 0))
        return "$ " + f"{valor:,}".replace(",", ".")
    except:
        return "$ 0"


def limpiar_monto(valor):
    if pd.isna(valor):
        return 0

    if isinstance(valor, (int, float)):
        return int(round(valor, 0))

    texto = str(valor).strip()

    if texto in ["", "-", "nan", "None"]:
        return 0

    texto = texto.replace("$", "")
    texto = texto.replace(" ", "")

    if "," in texto:
        texto = texto.replace(".", "")
        texto = texto.replace(",", ".")
    else:
        if "." in texto:
            partes = texto.split(".")
            if len(partes[-1]) == 3:
                texto = texto.replace(".", "")

    try:
        return int(round(float(texto), 0))
    except:
        return 0


def crear_ticks_pesos(maximo):
    if maximo <= 0:
        tickvals = [0]
    else:
        paso = maximo / 5
        tickvals = [round(paso * i) for i in range(0, 6)]

    ticktext = [formato_pesos(v) for v in tickvals]
    return tickvals, ticktext


def formato_base_grafico(fig):
    fig.update_layout(
        plot_bgcolor="#111827",
        paper_bgcolor="#111827",
        font=dict(color="#e5e7eb"),
        title_font=dict(size=24, color="#f8fafc"),
        legend=dict(
            font=dict(color="#e5e7eb"),
            title_font=dict(color="#e5e7eb")
        )
    )

    fig.update_xaxes(exponentformat="none")
    fig.update_yaxes(exponentformat="none")

    return fig


def aplicar_eje_y_pesos(fig, maximo):
    tickvals, ticktext = crear_ticks_pesos(maximo)

    fig.update_yaxes(
        title_text="Costo $",
        tickmode="array",
        tickvals=tickvals,
        ticktext=ticktext,
        exponentformat="none"
    )

    return fig


def aplicar_eje_x_pesos(fig, maximo):
    tickvals, ticktext = crear_ticks_pesos(maximo)

    fig.update_xaxes(
        title_text="Costo $",
        tickmode="array",
        tickvals=tickvals,
        ticktext=ticktext,
        exponentformat="none"
    )

    return fig


# -------------------------------------------------------
# ESTILO VISUAL
# -------------------------------------------------------

st.markdown("""
<style>
    .stApp {
        background-color: #0f172a;
        color: #e5e7eb;
    }

    .titulo-principal {
        font-size: 42px;
        font-weight: 800;
        color: #f8fafc;
        margin-bottom: 5px;
    }

    .subtitulo {
        font-size: 18px;
        color: #cbd5e1;
        margin-bottom: 25px;
    }

    .section-title {
        font-size: 25px;
        font-weight: 800;
        color: #f8fafc;
        margin-top: 35px;
        margin-bottom: 15px;
        border-left: 6px solid #22c55e;
        padding-left: 12px;
    }

    .card {
        background: linear-gradient(135deg, #1e293b, #111827);
        padding: 22px;
        border-radius: 18px;
        box-shadow: 0px 4px 16px rgba(0,0,0,0.45);
        text-align: center;
        border: 1px solid #334155;
    }

    .card-title {
        font-size: 15px;
        color: #cbd5e1;
        font-weight: 600;
    }

    .card-value {
        font-size: 29px;
        color: #22c55e;
        font-weight: 900;
        margin-top: 8px;
    }

    h1, h2, h3, h4, h5, h6, p, label {
        color: #e5e7eb;
    }

    div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #111827 !important;
        border-radius: 10px !important;
    }

    div[data-baseweb="select"] span {
        color: #111827 !important;
    }

    div[data-baseweb="select"] input {
        color: #111827 !important;
    }

    div[data-baseweb="tag"] {
        background-color: #ef4444 !important;
        color: white !important;
        border-radius: 8px !important;
    }

    div[data-baseweb="tag"] span {
        color: white !important;
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# SELLO DE AGUA
# -------------------------------------------------------

agregar_sello_agua("logoredondo.png")

# -------------------------------------------------------
# ENCABEZADO CON LOGO ARRIBA A LA DERECHA
# -------------------------------------------------------

col_titulo, col_logo = st.columns([5, 1])

with col_titulo:
    st.markdown(
        '<div class="titulo-principal">♻️ Dashboard de Costos de Residuos No Peligrosos</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitulo">Panel web para analizar costos de disposición y traslado de RAD, corteza, escoria y ceniza.</div>',
        unsafe_allow_html=True
    )

with col_logo:
    if os.path.exists("logo1.png"):
        st.image("logo1.png", width=300)
    else:
        st.warning("No se encontró logo1.png")

# -------------------------------------------------------
# ARCHIVO EXCEL
# -------------------------------------------------------

archivo_excel = "RESIDUOS NO PELIGROSOS - V01.xlsx"

try:
    df = pd.read_excel(archivo_excel)

    df.columns = df.columns.astype(str).str.strip()

    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")
    df = df.loc[:, ~df.columns.str.contains("Unnamed")]

    if "Fecha" not in df.columns:
        st.error("No se encontró la columna 'Fecha' en la planilla.")
        st.write("Columnas detectadas:")
        st.write(list(df.columns))
        st.stop()

    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce", dayfirst=True)
    df = df[df["Fecha"].notna()]

    if df.empty:
        st.error("No se encontraron fechas válidas en la columna Fecha.")
        st.stop()

    meses_espanol = {
        1: "Enero",
        2: "Febrero",
        3: "Marzo",
        4: "Abril",
        5: "Mayo",
        6: "Junio",
        7: "Julio",
        8: "Agosto",
        9: "Septiembre",
        10: "Octubre",
        11: "Noviembre",
        12: "Diciembre"
    }

    orden_meses = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]

    df["Año"] = df["Fecha"].dt.year
    df["Mes"] = df["Fecha"].dt.month
    df["Mes_Nombre"] = df["Mes"].map(meses_espanol)
    df["Periodo"] = df["Fecha"].dt.strftime("%Y-%m")
    df["Periodo_Texto"] = df["Mes_Nombre"] + " " + df["Año"].astype(str)

    columnas_no_costos = [
        "Fecha",
        "Año",
        "Mes",
        "Mes_Nombre",
        "Periodo",
        "Periodo_Texto"
    ]

    columnas_costos = [
        col for col in df.columns
        if col not in columnas_no_costos
    ]

    columnas_costos = [
        col for col in columnas_costos
        if any(
            palabra in col.lower()
            for palabra in ["rad", "corteza", "escoria", "ceniza"]
        )
    ]

    if len(columnas_costos) == 0:
        st.error("No se detectaron columnas de costos.")
        st.write("Columnas detectadas:")
        st.write(list(df.columns))
        st.stop()

    for col in columnas_costos:
        df[col] = df[col].apply(limpiar_monto).astype(int)

    df_largo = df.melt(
        id_vars=[
            "Fecha",
            "Periodo_Texto",
            "Año",
            "Mes",
            "Mes_Nombre",
            "Periodo"
        ],
        value_vars=columnas_costos,
        var_name="Concepto",
        value_name="Monto"
    )

    df_largo["Monto"] = df_largo["Monto"].astype(int)

    df_largo["Tipo_Costo"] = df_largo["Concepto"].apply(
        lambda x: "Disposición"
        if "disposicion" in x.lower() or "disposición" in x.lower()
        else "Traslado"
    )

    df_largo["Residuo"] = (
        df_largo["Concepto"]
        .str.replace("Disposición", "", regex=False)
        .str.replace("Disposicion", "", regex=False)
        .str.replace("disposición", "", regex=False)
        .str.replace("disposicion", "", regex=False)
        .str.replace("Traslado", "", regex=False)
        .str.replace("traslado", "", regex=False)
        .str.strip()
    )

    df_largo = df_largo[df_largo["Monto"] > 0]

    st.success("Planilla cargada correctamente.")

    if df_largo.empty:
        st.error("La planilla fue leída, pero no se encontraron montos válidos para analizar.")
        st.dataframe(df.head(10), use_container_width=True)
        st.stop()

    # -------------------------------------------------------
    # FILTROS
    # -------------------------------------------------------

    st.markdown('<div class="section-title">🔎 Filtros de análisis</div>', unsafe_allow_html=True)

    df_filtrado = df_largo.copy()

    colf1, colf2, colf3, colf4 = st.columns(4)

    with colf1:
        años = st.multiselect(
            "Año",
            sorted(df_largo["Año"].dropna().unique())
        )

        if años:
            df_filtrado = df_filtrado[df_filtrado["Año"].isin(años)]

    with colf2:
        residuos = st.multiselect(
            "Residuo",
            sorted(df_largo["Residuo"].dropna().unique())
        )

        if residuos:
            df_filtrado = df_filtrado[df_filtrado["Residuo"].isin(residuos)]

    with colf3:
        tipos_costo = st.multiselect(
            "Tipo de costo",
            sorted(df_largo["Tipo_Costo"].dropna().unique())
        )

        if tipos_costo:
            df_filtrado = df_filtrado[df_filtrado["Tipo_Costo"].isin(tipos_costo)]

    with colf4:
        meses_disponibles = [
            mes for mes in orden_meses
            if mes in df_largo["Mes_Nombre"].unique()
        ]

        meses_filtro = st.multiselect(
            "Mes",
            meses_disponibles
        )

        if meses_filtro:
            df_filtrado = df_filtrado[df_filtrado["Mes_Nombre"].isin(meses_filtro)]

    # -------------------------------------------------------
    # INDICADORES PRINCIPALES
    # -------------------------------------------------------

    st.markdown('<div class="section-title">📌 Indicadores principales</div>', unsafe_allow_html=True)

    total_monto = int(df_filtrado["Monto"].sum())
    total_registros = len(df_filtrado)
    total_residuos = df_filtrado["Residuo"].nunique()

    promedio_mensual = (
        df_filtrado.groupby("Periodo")["Monto"].sum().mean()
        if total_registros > 0 else 0
    )

    promedio_mensual = int(round(promedio_mensual, 0))

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">Costo total</div>
            <div class="card-value">{formato_pesos(total_monto)}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">Registros analizados</div>
            <div class="card-value">{total_registros}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">Tipos de residuos</div>
            <div class="card-value">{total_residuos}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">Promedio mensual</div>
            <div class="card-value">{formato_pesos(promedio_mensual)}</div>
        </div>
        """, unsafe_allow_html=True)

    # -------------------------------------------------------
    # GRÁFICOS
    # -------------------------------------------------------

    st.markdown('<div class="section-title">📊 Análisis gráfico de costos</div>', unsafe_allow_html=True)

    if df_filtrado.empty:
        st.warning("No existen datos para mostrar con los filtros seleccionados.")

    else:
        template_dark = "plotly_dark"

        resumen_anual = (
            df_filtrado.groupby("Año")["Monto"]
            .sum()
            .reset_index()
            .sort_values("Año")
        )

        resumen_anual["Monto_Texto"] = resumen_anual["Monto"].apply(formato_pesos)

        fig_anual = px.bar(
            resumen_anual,
            x="Año",
            y="Monto",
            text="Monto_Texto",
            title="Costo anual de residuos no peligrosos",
            color="Monto",
            color_continuous_scale="Greens",
            template=template_dark
        )

        fig_anual.update_traces(
            textposition="outside",
            hovertemplate="<b>Año %{x}</b><br>Costo: %{text}<extra></extra>"
        )

        fig_anual.update_layout(
            height=450,
            xaxis_title="Año",
            yaxis_title="Costo $",
            showlegend=False
        )

        fig_anual.update_xaxes(
            tickmode="array",
            tickvals=resumen_anual["Año"].tolist(),
            ticktext=[str(año) for año in resumen_anual["Año"].tolist()]
        )

        fig_anual = formato_base_grafico(fig_anual)
        fig_anual = aplicar_eje_y_pesos(fig_anual, resumen_anual["Monto"].max())

        st.plotly_chart(fig_anual, use_container_width=True)

        resumen_mensual = (
            df_filtrado.groupby(["Año", "Mes", "Mes_Nombre", "Periodo"])["Monto"]
            .sum()
            .reset_index()
            .sort_values(["Año", "Mes"])
        )

        resumen_mensual["Mes_Año"] = (
            resumen_mensual["Mes_Nombre"] + " " + resumen_mensual["Año"].astype(str)
        )

        resumen_mensual["Monto_Texto"] = resumen_mensual["Monto"].apply(formato_pesos)

        fig_mensual = px.line(
            resumen_mensual,
            x="Mes_Año",
            y="Monto",
            markers=True,
            title="Tendencia mensual de costos",
            template=template_dark
        )

        fig_mensual.update_traces(
            line=dict(width=4, color="#22c55e"),
            marker=dict(size=10, color="#16a34a"),
            hovertemplate="<b>%{x}</b><br>Costo: %{customdata}<extra></extra>",
            customdata=resumen_mensual["Monto_Texto"]
        )

        fig_mensual.update_layout(
            height=450,
            xaxis_title="Mes",
            yaxis_title="Costo $"
        )

        fig_mensual = formato_base_grafico(fig_mensual)
        fig_mensual = aplicar_eje_y_pesos(fig_mensual, resumen_mensual["Monto"].max())

        st.plotly_chart(fig_mensual, use_container_width=True)

        st.markdown('<div class="section-title">🥧 Distribución de costos por residuo</div>', unsafe_allow_html=True)

        resumen_residuo = (
            df_filtrado.groupby("Residuo")["Monto"]
            .sum()
            .reset_index()
            .sort_values("Monto", ascending=False)
        )

        resumen_residuo["Monto_Texto"] = resumen_residuo["Monto"].apply(formato_pesos)

        total_costo = int(resumen_residuo["Monto"].sum())

        fig_residuo = px.pie(
            resumen_residuo,
            names="Residuo",
            values="Monto",
            title="Participación por tipo de residuo",
            hole=0.55,
            template=template_dark,
            color_discrete_sequence=px.colors.sequential.Greens_r,
            custom_data=["Monto_Texto"]
        )

        fig_residuo.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>Costo: %{customdata[0]}<br>Participación: %{percent}<extra></extra>",
            marker=dict(line=dict(color="#0f172a", width=2))
        )

        fig_residuo.update_layout(
            height=580,
            paper_bgcolor="#111827",
            plot_bgcolor="#111827",
            font=dict(color="#e5e7eb"),
            title_font=dict(size=24, color="#f8fafc"),
            legend_title_text="Residuo",
            legend=dict(font=dict(color="#e5e7eb")),
            annotations=[
                dict(
                    text=f"{formato_pesos(total_costo)}<br>Total",
                    x=0.5,
                    y=0.5,
                    font_size=22,
                    font_color="#f8fafc",
                    showarrow=False
                )
            ]
        )

        st.plotly_chart(fig_residuo, use_container_width=True)

        st.markdown('<div class="section-title">🚛 Comparativo disposición vs traslado</div>', unsafe_allow_html=True)

        resumen_tipo = (
            df_filtrado.groupby("Tipo_Costo")["Monto"]
            .sum()
            .reset_index()
            .sort_values("Monto", ascending=False)
        )

        resumen_tipo["Monto_Texto"] = resumen_tipo["Monto"].apply(formato_pesos)

        fig_tipo = px.pie(
            resumen_tipo,
            names="Tipo_Costo",
            values="Monto",
            title="Participación por tipo de costo",
            hole=0.55,
            template=template_dark,
            color_discrete_sequence=px.colors.sequential.Teal_r,
            custom_data=["Monto_Texto"]
        )

        fig_tipo.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>Costo: %{customdata[0]}<br>Participación: %{percent}<extra></extra>",
            marker=dict(line=dict(color="#0f172a", width=2))
        )

        fig_tipo.update_layout(
            height=520,
            paper_bgcolor="#111827",
            plot_bgcolor="#111827",
            font=dict(color="#e5e7eb"),
            title_font=dict(size=24, color="#f8fafc"),
            legend_title_text="Tipo de costo",
            legend=dict(font=dict(color="#e5e7eb"))
        )

        st.plotly_chart(fig_tipo, use_container_width=True)

        st.markdown('<div class="section-title">🏆 Ranking de costos</div>', unsafe_allow_html=True)

        colb1, colb2 = st.columns(2)

        with colb1:
            ranking_residuo = (
                df_filtrado.groupby("Residuo")["Monto"]
                .sum()
                .reset_index()
                .sort_values("Monto", ascending=True)
            )

            ranking_residuo["Monto_Texto"] = ranking_residuo["Monto"].apply(formato_pesos)

            fig_ranking_residuo = px.bar(
                ranking_residuo,
                x="Monto",
                y="Residuo",
                orientation="h",
                text="Monto_Texto",
                title="Ranking por residuo",
                color="Monto",
                color_continuous_scale="Greens",
                template=template_dark
            )

            fig_ranking_residuo.update_traces(
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>Costo: %{text}<extra></extra>"
            )

            fig_ranking_residuo.update_layout(
                height=520,
                xaxis_title="Costo $",
                yaxis_title="Residuo",
                showlegend=False
            )

            fig_ranking_residuo = formato_base_grafico(fig_ranking_residuo)
            fig_ranking_residuo = aplicar_eje_x_pesos(
                fig_ranking_residuo,
                ranking_residuo["Monto"].max()
            )

            st.plotly_chart(fig_ranking_residuo, use_container_width=True)

        with colb2:
            ranking_concepto = (
                df_filtrado.groupby("Concepto")["Monto"]
                .sum()
                .reset_index()
                .sort_values("Monto", ascending=True)
            )

            ranking_concepto["Monto_Texto"] = ranking_concepto["Monto"].apply(formato_pesos)

            fig_ranking_concepto = px.bar(
                ranking_concepto,
                x="Monto",
                y="Concepto",
                orientation="h",
                text="Monto_Texto",
                title="Ranking por concepto",
                color="Monto",
                color_continuous_scale="Greens",
                template=template_dark
            )

            fig_ranking_concepto.update_traces(
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>Costo: %{text}<extra></extra>"
            )

            fig_ranking_concepto.update_layout(
                height=520,
                xaxis_title="Costo $",
                yaxis_title="Concepto",
                showlegend=False
            )

            fig_ranking_concepto = formato_base_grafico(fig_ranking_concepto)
            fig_ranking_concepto = aplicar_eje_x_pesos(
                fig_ranking_concepto,
                ranking_concepto["Monto"].max()
            )

            st.plotly_chart(fig_ranking_concepto, use_container_width=True)

        st.markdown('<div class="section-title">📆 Comparativo mensual por año</div>', unsafe_allow_html=True)

        resumen_mes_anio = (
            df_filtrado.groupby(["Año", "Mes", "Mes_Nombre"])["Monto"]
            .sum()
            .reset_index()
            .sort_values(["Año", "Mes"])
        )

        resumen_mes_anio["Año_Texto"] = resumen_mes_anio["Año"].astype(str)
        resumen_mes_anio["Monto_Texto"] = resumen_mes_anio["Monto"].apply(formato_pesos)

        fig_mes_anio = px.bar(
            resumen_mes_anio,
            x="Mes_Nombre",
            y="Monto",
            color="Año_Texto",
            barmode="group",
            text="Monto_Texto",
            title="Comparativo mensual por año",
            template=template_dark,
            category_orders={"Mes_Nombre": orden_meses},
            labels={
                "Año_Texto": "Año",
                "Mes_Nombre": "Mes",
                "Monto": "Costo $"
            }
        )

        fig_mes_anio.update_traces(
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Costo: %{text}<extra></extra>"
        )

        fig_mes_anio.update_layout(
            height=520,
            xaxis_title="Mes",
            yaxis_title="Costo $"
        )

        fig_mes_anio = formato_base_grafico(fig_mes_anio)
        fig_mes_anio = aplicar_eje_y_pesos(fig_mes_anio, resumen_mes_anio["Monto"].max())

        st.plotly_chart(fig_mes_anio, use_container_width=True)

        st.markdown('<div class="section-title">📅 Resumen anual por residuo</div>', unsafe_allow_html=True)

        resumen_anual_residuo = df_filtrado.pivot_table(
            index="Residuo",
            columns="Año",
            values="Monto",
            aggfunc="sum",
            fill_value=0
        )

        resumen_anual_residuo = resumen_anual_residuo.map(formato_pesos)

        st.dataframe(resumen_anual_residuo, use_container_width=True)

    st.markdown('<div class="section-title">📋 Registro general de costos de residuos</div>', unsafe_allow_html=True)

    columnas_mostrar = [
        "Fecha",
        "Periodo_Texto",
        "Año",
        "Mes_Nombre",
        "Residuo",
        "Tipo_Costo",
        "Concepto",
        "Monto"
    ]

    tabla_mostrar = df_filtrado[columnas_mostrar].copy()

    tabla_mostrar["Fecha"] = tabla_mostrar["Fecha"].dt.strftime("%d-%m-%Y")
    tabla_mostrar["Monto"] = tabla_mostrar["Monto"].apply(formato_pesos)

    tabla_mostrar = tabla_mostrar.rename(
        columns={
            "Periodo_Texto": "Periodo original",
            "Mes_Nombre": "Mes",
            "Tipo_Costo": "Tipo de Costo"
        }
    )

    st.dataframe(tabla_mostrar, use_container_width=True)

    st.markdown('<div class="section-title">⬇️ Descargar información</div>', unsafe_allow_html=True)

    csv = tabla_mostrar.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="Descargar datos filtrados",
        data=csv,
        file_name="control_costos_residuos_no_peligrosos.csv",
        mime="text/csv"
    )

except FileNotFoundError:
    st.error("No se encontró la planilla Excel.")
    st.write("Verifica que el archivo esté en la misma carpeta que app.py.")
    st.code(archivo_excel)

except Exception as e:
    st.error("Ocurrió un error al cargar la planilla.")
    st.write(e)