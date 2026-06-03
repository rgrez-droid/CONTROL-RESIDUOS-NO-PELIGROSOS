import base64
import math
import os
import re
import unicodedata

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

st.set_page_config(
    page_title="Análisis de Residuos No Peligrosos",
    page_icon="♻️",
    layout="wide",
)

ARCHIVO_EXCEL = "RESIDUOS NO PELIGROSOS - V01.xlsx"
LOGO_SUPERIOR = "logo1.png"
SELLO_AGUA = "logoredondo.png"

AUTOR = "Ricardo Grez"
CARGO = "Administrador de Contrato"
VERSION = "1.0"

RESIDUOS = [
    "RAD",
    "Corteza",
    "Escoria",
    "Ceniza",
]

TIPOS_COSTO = [
    "Disposición",
    "Traslado",
]

COLORES_RESIDUOS = {
    "RAD": "#a855f7",
    "Corteza": "#ff5b3d",
    "Escoria": "#14d9b2",
    "Ceniza": "#6574ff",
}

COLORES_COSTO = {
    "Traslado": "#ff5b3d",
    "Disposición": "#6574ff",
}

MESES = {
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
    12: "Diciembre",
}

MESES_NUMERO = {
    nombre.lower(): numero
    for numero, nombre in MESES.items()
}


# =========================================================
# FUNCIONES DE LIMPIEZA Y FORMATO
# =========================================================

def normalizar(texto):
    texto = unicodedata.normalize(
        "NFD",
        str(texto).strip().lower(),
    )

    texto = "".join(
        caracter
        for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )

    return re.sub(
        r"\s+",
        " ",
        texto,
    )


def buscar_columna(columnas, nombre):
    mapa = {
        normalizar(columna): columna
        for columna in columnas
    }

    return mapa.get(
        normalizar(nombre)
    )


def limpiar_numero(valor):
    if pd.isna(valor):
        return 0.0

    if isinstance(
        valor,
        (
            int,
            float,
        ),
    ):
        return float(valor)

    texto = re.sub(
        r"[^0-9,.-]",
        "",
        str(valor),
    )

    if texto in {
        "",
        "-",
    }:
        return 0.0

    if "," in texto:
        texto = (
            texto
            .replace(".", "")
            .replace(",", ".")
        )

    elif (
        "." in texto
        and len(
            texto.split(".")[-1]
        ) == 3
    ):
        texto = texto.replace(
            ".",
            "",
        )

    try:
        return float(texto)

    except ValueError:
        return 0.0


def convertir_fecha(valor):
    if pd.isna(valor):
        return pd.NaT

    if isinstance(
        valor,
        pd.Timestamp,
    ):
        return valor

    texto = normalizar(valor)

    patron = (
        r"^(enero|febrero|marzo|abril|mayo|junio|"
        r"julio|agosto|septiembre|octubre|noviembre|"
        r"diciembre)\s+(\d{4})$"
    )

    coincidencia = re.match(
        patron,
        texto,
    )

    if coincidencia:
        return pd.Timestamp(
            year=int(
                coincidencia.group(2)
            ),
            month=MESES_NUMERO[
                coincidencia.group(1)
            ],
            day=1,
        )

    return pd.to_datetime(
        valor,
        errors="coerce",
        dayfirst=True,
    )


def pesos(valor):
    try:
        numero = int(
            round(
                float(valor)
            )
        )

        return (
            "$ "
            + f"{numero:,}".replace(
                ",",
                ".",
            )
        )

    except (
        TypeError,
        ValueError,
    ):
        return "$ 0"


def toneladas(valor):
    try:
        texto = f"{float(valor):,.1f}"

        return (
            texto
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
            + " t"
        )

    except (
        TypeError,
        ValueError,
    ):
        return "0,0 t"


def porcentaje(valor):
    try:
        return (
            f"{float(valor):.1f}%"
            .replace(".", ",")
        )

    except (
        TypeError,
        ValueError,
    ):
        return "0,0%"


def nombre_periodo(fecha):
    return (
        f"{MESES[fecha.month]} "
        f"{fecha.year}"
    )


# =========================================================
# COMPONENTES VISUALES
# =========================================================

def seccion(titulo):
    st.markdown(
        f'<div class="seccion">{titulo}</div>',
        unsafe_allow_html=True,
    )


def tarjeta(
    titulo,
    valor,
    subtitulo,
    color,
):
    st.markdown(
        (
            '<div class="tarjeta">'
            f'<div class="tarjeta-titulo">{titulo}</div>'
            f'<div class="tarjeta-valor {color}">{valor}</div>'
            f'<div class="tarjeta-subtitulo">{subtitulo}</div>'
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def aplicar_filtros(
    dataframe,
    anios,
    residuos,
    meses,
):
    salida = dataframe.copy()

    if anios:
        salida = salida[
            salida[
                "Año"
            ].isin(
                anios
            )
        ]

    if residuos:
        salida = salida[
            salida[
                "Residuo"
            ].isin(
                residuos
            )
        ]

    if meses:
        salida = salida[
            salida[
                "Mes_Nombre"
            ].isin(
                meses
            )
        ]

    return salida.copy()


def paso_eje(
    maximo,
    divisiones=5,
):
    if maximo <= 0:
        return 1

    aproximado = (
        maximo
        / divisiones
    )

    potencia = 10 ** math.floor(
        math.log10(
            aproximado
        )
    )

    base = (
        aproximado
        / potencia
    )

    if base <= 1:
        factor = 1

    elif base <= 2:
        factor = 2

    elif base <= 5:
        factor = 5

    else:
        factor = 10

    return (
        factor
        * potencia
    )


def aplicar_eje_clp(
    figura,
    valores,
    eje="y",
):
    serie = pd.Series(
        valores,
        dtype="float64",
    ).dropna()

    maximo = (
        float(
            serie.max()
        )
        if not serie.empty
        else 0
    )

    paso = paso_eje(
        maximo
    )

    limite = (
        math.ceil(
            maximo
            / paso
        )
        * paso
        if maximo > 0
        else paso
    )

    marcas = [
        numero
        * paso
        for numero in range(
            int(
                limite
                / paso
            )
            + 1
        )
    ]

    parametros = {
        "tickmode": "array",
        "tickvals": marcas,
        "ticktext": [
            pesos(valor)
            for valor in marcas
        ],
        "rangemode": "tozero",
    }

    if eje == "x":
        figura.update_xaxes(
            **parametros
        )

    else:
        figura.update_yaxes(
            **parametros
        )

    return figura


def formato_grafico(
    figura,
    altura=470,
):
    figura.update_layout(
        height=altura,
        plot_bgcolor="#111827",
        paper_bgcolor="#111827",

        font=dict(
            color="#e5e7eb",
            size=13,
        ),

        title_font=dict(
            size=20,
            color="#f8fafc",
        ),

        legend=dict(
            title=dict(
                font=dict(
                    color="#f8fafc",
                    size=13,
                )
            ),

            font=dict(
                color="#f8fafc",
                size=13,
            ),

            bgcolor="rgba(30, 41, 59, 0.82)",
            bordercolor="#475569",
            borderwidth=1,
            itemsizing="constant",
            tracegroupgap=6,
        ),

        margin=dict(
            l=35,
            r=35,
            t=70,
            b=55,
        ),

        hoverlabel=dict(
            bgcolor="#172033",
            font_color="#f8fafc",
        ),
    )

    estilo_eje = {
        "exponentformat": "none",

        "tickfont": {
            "color": "#cbd5e1",
            "size": 11,
        },

        "title_font": {
            "color": "#e5e7eb",
            "size": 12,
        },

        "gridcolor": (
            "rgba(148, 163, 184, 0.12)"
        ),
    }

    figura.update_xaxes(
        **estilo_eje
    )

    figura.update_yaxes(
        **estilo_eje
    )

    return figura


def grafico_linea(
    dataframe,
    valor_y,
    titulo,
    etiqueta,
    formateador,
    color,
    eje_clp=False,
):
    if dataframe.empty:
        st.info(
            "No existen datos disponibles "
            "para mostrar este gráfico."
        )

        return

    figura = px.line(
        dataframe,
        x="Periodo_Texto",
        y=valor_y,
        markers=True,
        title=titulo,
        template="plotly_dark",
    )

    figura.update_traces(
        line=dict(
            width=3,
            color=color,
        ),

        marker=dict(
            size=4,
            opacity=0.70,
            color=color,

            line=dict(
                width=0,
            ),
        ),

        customdata=dataframe[
            valor_y
        ].apply(
            formateador
        ),

        hovertemplate=(
            "<b>%{x}</b>"
            f"<br>{etiqueta}: %{{customdata}}"
            "<extra></extra>"
        ),
    )

    figura.update_layout(
        xaxis_title="Mes",
        yaxis_title=etiqueta,
        showlegend=False,
    )

    figura.update_xaxes(
        tickangle=-35
    )

    if eje_clp:
        aplicar_eje_clp(
            figura,
            dataframe[
                valor_y
            ],
            "y",
        )

    st.plotly_chart(
        formato_grafico(
            figura,
            440,
        ),
        use_container_width=True,
    )


def agregar_sello_agua(ruta):
    if not os.path.exists(ruta):
        return

    with open(
        ruta,
        "rb",
    ) as archivo:
        sello = base64.b64encode(
            archivo.read()
        ).decode()

    st.markdown(
        (
            "<style>"
            ".stApp::before{"
            'content:"";'
            "position:fixed;"
            "top:52%;"
            "left:50%;"
            "width:590px;"
            "height:590px;"
            f'background:url("data:image/png;base64,{sello}") '
            "center/contain no-repeat;"
            "opacity:.045;"
            "transform:translate(-50%,-50%);"
            "pointer-events:none;"
            "z-index:0;"
            "}"
            ".block-container{"
            "position:relative;"
            "z-index:1;"
            "}"
            "</style>"
        ),
        unsafe_allow_html=True,
    )


# =========================================================
# CARGA Y TRANSFORMACIÓN DE DATOS
# =========================================================

@st.cache_data
def cargar_datos(ruta_excel):
    dataframe = pd.read_excel(
        ruta_excel
    )

    dataframe = (
        dataframe
        .dropna(
            how="all"
        )
        .dropna(
            axis=1,
            how="all",
        )
    )

    dataframe.columns = (
        dataframe.columns
        .astype(str)
        .str.strip()
    )

    dataframe = dataframe.loc[
        :,
        ~dataframe.columns.str.contains(
            "Unnamed",
            case=False,
        ),
    ]

    columna_fecha = buscar_columna(
        dataframe.columns,
        "Fecha",
    )

    if columna_fecha is None:
        raise ValueError(
            "No se encontró la columna Fecha."
        )

    dataframe = dataframe.rename(
        columns={
            columna_fecha: "Fecha"
        }
    )

    dataframe[
        "Fecha"
    ] = dataframe[
        "Fecha"
    ].apply(
        convertir_fecha
    )

    dataframe = dataframe[
        dataframe[
            "Fecha"
        ].notna()
    ].copy()

    if dataframe.empty:
        raise ValueError(
            "No se detectaron fechas válidas "
            "en la planilla."
        )

    dataframe[
        "Año"
    ] = dataframe[
        "Fecha"
    ].dt.year

    dataframe[
        "Mes"
    ] = dataframe[
        "Fecha"
    ].dt.month

    dataframe[
        "Mes_Nombre"
    ] = dataframe[
        "Mes"
    ].map(
        MESES
    )

    dataframe[
        "Periodo"
    ] = dataframe[
        "Fecha"
    ].dt.strftime(
            "%Y-%m"
        )

    dataframe[
        "Periodo_Texto"
    ] = (
        dataframe[
            "Mes_Nombre"
        ]
        + " "
        + dataframe[
            "Año"
        ].astype(str)
    )

    return dataframe


@st.cache_data
def preparar_datos(dataframe):
    columnas_base = [
        "Fecha",
        "Año",
        "Mes",
        "Mes_Nombre",
        "Periodo",
        "Periodo_Texto",
    ]

    registros_costos = []
    registros_toneladas = []

    for residuo in RESIDUOS:

        for tipo_costo in TIPOS_COSTO:
            columna = buscar_columna(
                dataframe.columns,
                f"{tipo_costo} {residuo}",
            )

            if columna is None:
                raise ValueError(
                    "No se encontró la columna: "
                    f"{tipo_costo} {residuo}"
                )

            temporal = dataframe[
                columnas_base
            ].copy()

            temporal[
                "Residuo"
            ] = residuo

            temporal[
                "Tipo_Costo"
            ] = tipo_costo

            temporal[
                "Monto"
            ] = dataframe[
                columna
            ].apply(
                limpiar_numero
            )

            registros_costos.append(
                temporal
            )

        columna_toneladas = buscar_columna(
            dataframe.columns,
            f"Toneladas {residuo}",
        )

        if columna_toneladas is None:
            raise ValueError(
                "No se encontró la columna: "
                f"Toneladas {residuo}"
            )

        temporal = dataframe[
            columnas_base
        ].copy()

        temporal[
            "Residuo"
        ] = residuo

        temporal[
            "Toneladas"
        ] = dataframe[
            columna_toneladas
        ].apply(
            limpiar_numero
        )

        registros_toneladas.append(
            temporal
        )

    costos = pd.concat(
        registros_costos,
        ignore_index=True,
    )

    toneladas_df = pd.concat(
        registros_toneladas,
        ignore_index=True,
    )

    return (
        costos[
            costos[
                "Monto"
            ] > 0
        ].copy(),

        toneladas_df[
            toneladas_df[
                "Toneladas"
            ] > 0
        ].copy(),
    )


# =========================================================
# ESTILO GENERAL
# =========================================================

st.markdown(
    """
    <style>
        .stApp {
            background: #0f172a;
            color: #e5e7eb;
        }

        .titulo {
            font-size: 40px;
            font-weight: 850;
            color: #f8fafc;
        }

        .subtitulo {
            font-size: 17px;
            color: #cbd5e1;
            margin: 6px 0 10px;
        }

        .metadata {
            color: #94a3b8;
            font-size: 13px;
            margin-bottom: 18px;
        }

        .seccion {
            font-size: 23px;
            font-weight: 800;
            color: #f8fafc;
            margin: 32px 0 15px;
            border-left: 5px solid #22c55e;
            padding-left: 11px;
        }

        .tarjeta {
            background:
                linear-gradient(
                    135deg,
                    #1e293b,
                    #111827
                );

            border: 1px solid #334155;
            border-radius: 15px;
            padding: 17px 11px;
            min-height: 112px;
            text-align: center;

            box-shadow:
                0 4px 14px
                rgba(0, 0, 0, .18);
        }

        .tarjeta-titulo {
            font-size: 13px;
            color: #cbd5e1;
            font-weight: 700;
            min-height: 20px;
        }

        .tarjeta-valor {
            font-size: 24px;
            font-weight: 900;
            margin-top: 8px;
        }

        .tarjeta-subtitulo {
            color: #94a3b8;
            font-size: 12px;
            margin-top: 7px;
            line-height: 1.35;
        }

        .verde {
            color: #22c55e;
        }

        .azul {
            color: #38bdf8;
        }

        .naranjo {
            color: #fb923c;
        }

        .amarillo {
            color: #fbbf24;
        }

        .nota,
        .info,
        .resumen {
            background:
                linear-gradient(
                    135deg,
                    #172033,
                    #111827
                );

            border: 1px solid #334155;
            border-radius: 13px;
            padding: 16px 18px;
            color: #e5e7eb;
        }

        .info {
            border-left: 5px solid #38bdf8;
            margin-bottom: 12px;
        }

        .resumen {
            border-left: 5px solid #22c55e;
            line-height: 1.65;
        }

        .nota {
            border-left: 5px solid #fbbf24;
            margin: 17px 0 15px;
        }

        .nota-titulo {
            color: #fbbf24;
            font-size: 15px;
            font-weight: 800;
            margin-bottom: 6px;
        }

        .nota-texto {
            color: #cbd5e1;
            font-size: 13px;
            line-height: 1.55;
        }

        .pie-pagina {
            border-top: 1px solid #334155;
            color: #94a3b8;
            font-size: 12px;
            line-height: 1.65;
            margin-top: 38px;
            padding: 18px 0 8px;
            text-align: center;
        }

        div[data-baseweb="select"] > div {
            background: #ffffff !important;
            color: #111827 !important;
            border-radius: 8px !important;
        }

        div[data-baseweb="select"] span,
        div[data-baseweb="select"] input {
            color: #111827 !important;
        }

        h1,
        h2,
        h3,
        h4,
        p,
        label {
            color: #e5e7eb;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

agregar_sello_agua(
    SELLO_AGUA
)


# =========================================================
# APLICACIÓN
# =========================================================

try:
    df = cargar_datos(
        ARCHIVO_EXCEL
    )

    df_costos, df_toneladas = preparar_datos(
        df
    )

    fecha_minima = df[
        "Fecha"
    ].min()

    fecha_maxima = df[
        "Fecha"
    ].max()


    # =====================================================
    # ENCABEZADO
    # =====================================================

    col_titulo, col_logo = st.columns(
        [
            5,
            1,
        ]
    )

    with col_titulo:
        st.markdown(
            """
            <div class="titulo">
                ♻️ Análisis consolidado de residuos no peligrosos
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="subtitulo">
                Panel ejecutivo para el seguimiento operacional,
                económico y contractual de RAD, corteza, escoria y ceniza.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            (
                '<div class="metadata">'
                f"<b>Período analizado:</b> "
                f"{nombre_periodo(fecha_minima)} a "
                f"{nombre_periodo(fecha_maxima)}"
                " &nbsp;|&nbsp; "
                f"<b>Última actualización:</b> "
                f"{nombre_periodo(fecha_maxima)}"
                " &nbsp;|&nbsp; "
                "<b>Fuente:</b> Control mensual de residuos no peligrosos"
                "</div>"
            ),
            unsafe_allow_html=True,
        )

    with col_logo:
        if os.path.exists(
            LOGO_SUPERIOR
        ):
            st.image(
                LOGO_SUPERIOR,
                width=220,
            )


    # =====================================================
    # FILTROS
    # =====================================================

    seccion(
        "🔎 Filtros de análisis"
    )

    filtro1, filtro2, filtro3, filtro4 = st.columns(
        4
    )

    with filtro1:
        filtro_anios = st.multiselect(
            "Año",
            sorted(
                df[
                    "Año"
                ].unique()
            ),
        )

    with filtro2:
        filtro_residuos = st.multiselect(
            "Residuo",
            RESIDUOS,
        )

    with filtro3:
        filtro_tipos = st.multiselect(
            "Tipo de costo",
            TIPOS_COSTO,
        )

    with filtro4:
        filtro_meses = st.multiselect(
            "Mes",
            [
                mes
                for mes in MESES.values()
                if mes
                in df[
                    "Mes_Nombre"
                ].unique()
            ],
        )

    costos = aplicar_filtros(
        df_costos,
        filtro_anios,
        filtro_residuos,
        filtro_meses,
    )

    ton = aplicar_filtros(
        df_toneladas,
        filtro_anios,
        filtro_residuos,
        filtro_meses,
    )

    if filtro_tipos:
        costos = costos[
            costos[
                "Tipo_Costo"
            ].isin(
                filtro_tipos
            )
        ]

    traslado = costos[
        costos[
            "Tipo_Costo"
        ] == "Traslado"
    ]

    disposicion = costos[
        costos[
            "Tipo_Costo"
        ] == "Disposición"
    ]


    # =====================================================
    # INDICADORES
    # =====================================================

    periodos = (
        set(
            costos[
                "Periodo"
            ]
        )
        |
        set(
            ton[
                "Periodo"
            ]
        )
    )

    cantidad_meses = len(
        periodos
    )

    total_costos = float(
        costos[
            "Monto"
        ].sum()
    )

    total_toneladas = float(
        ton[
            "Toneladas"
        ].sum()
    )

    total_traslado = float(
        traslado[
            "Monto"
        ].sum()
    )

    total_disposicion = float(
        disposicion[
            "Monto"
        ].sum()
    )

    participacion_traslado = (
        total_traslado
        / total_costos
        * 100
        if total_costos
        else 0
    )

    participacion_disposicion = (
        total_disposicion
        / total_costos
        * 100
        if total_costos
        else 0
    )

    indicadores = [
        (
            "Costo total acumulado",
            pesos(
                total_costos
            ),
            "Disposición y traslado",
            "verde",
        ),

        (
            "Toneladas gestionadas",
            toneladas(
                total_toneladas
            ),
            "Total del período seleccionado",
            "azul",
        ),

        (
            "Costo total de traslado",
            pesos(
                total_traslado
            ),
            (
                f"{porcentaje(participacion_traslado)} "
                "del costo total"
            ),
            "naranjo",
        ),

        (
            "Costo de disposición final",
            pesos(
                total_disposicion
            ),
            (
                f"{porcentaje(participacion_disposicion)} "
                "del costo total"
            ),
            "amarillo",
        ),

        (
            "Promedio mensual de costos",
            pesos(
                total_costos
                / cantidad_meses
                if cantidad_meses
                else 0
            ),
            f"{cantidad_meses} meses considerados",
            "verde",
        ),

        (
            "Promedio mensual de toneladas",
            toneladas(
                total_toneladas
                / cantidad_meses
                if cantidad_meses
                else 0
            ),
            f"{cantidad_meses} meses considerados",
            "azul",
        ),

        (
            "Participación del traslado",
            porcentaje(
                participacion_traslado
            ),
            "Incidencia sobre el costo total",
            "naranjo",
        ),

        (
            "Participación de la disposición",
            porcentaje(
                participacion_disposicion
            ),
            "Incidencia sobre el costo total",
            "amarillo",
        ),
    ]

    seccion(
        "📌 Indicadores ejecutivos"
    )

    for inicio in range(
        0,
        len(
            indicadores
        ),
        4,
    ):
        columnas = st.columns(
            4
        )

        for columna, datos in zip(
            columnas,
            indicadores[
                inicio:inicio + 4
            ],
        ):
            with columna:
                tarjeta(
                    *datos
                )


    # =====================================================
    # RESUMEN EJECUTIVO
    # =====================================================

    seccion(
        "📝 Resumen ejecutivo"
    )

    st.markdown(
        (
            '<div class="resumen">'
            "<b>Lectura ejecutiva del período.</b> "
            f"El costo acumulado de la gestión alcanza "
            f"<b>{pesos(total_costos)}</b>, "
            f"con una participación del traslado equivalente al "
            f"<b>{porcentaje(participacion_traslado)}</b> "
            f"y una incidencia de disposición final del "
            f"<b>{porcentaje(participacion_disposicion)}</b>. "
            f"Durante el período seleccionado se gestionaron "
            f"<b>{toneladas(total_toneladas)}</b> de residuos "
            f"no peligrosos."
            "</div>"
        ),
        unsafe_allow_html=True,
    )


    # =====================================================
    # NOTA OPERACIONAL
    # =====================================================

    mostrar_nota = (
        "2026-05"
        in df[
            "Periodo"
        ].values
        and (
            not filtro_anios
            or 2026 in filtro_anios
        )
        and (
            not filtro_meses
            or "Mayo" in filtro_meses
        )
        and (
            not filtro_residuos
            or "Corteza" in filtro_residuos
        )
    )

    if mostrar_nota:
        st.markdown(
            (
                '<div class="nota">'
                '<div class="nota-titulo">'
                "📌 Antecedente operacional relevante — Corteza"
                "</div>"
                '<div class="nota-texto">'
                "Durante mayo de 2026, la corteza fue gestionada "
                "mediante disposición interna en planta. Este "
                "antecedente debe considerarse al interpretar la "
                "evolución mensual de los costos, debido a que la "
                "modalidad aplicada durante dicho período difiere "
                "del esquema habitual de disposición externa y puede "
                "generar variaciones en el comportamiento económico observado."
                "</div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )


    # =====================================================
    # TONELADAS ACUMULADAS
    # =====================================================

    seccion(
        "⚖️ Toneladas acumuladas por residuo"
    )

    for columna, residuo in zip(
        st.columns(
            4
        ),
        RESIDUOS,
    ):
        with columna:
            total_residuo = ton.loc[
                ton[
                    "Residuo"
                ] == residuo,
                "Toneladas",
            ].sum()

            tarjeta(
                residuo,
                toneladas(
                    total_residuo
                ),
                "Toneladas gestionadas",
                "azul",
            )


    # =====================================================
    # EVOLUCIÓN MENSUAL CONSOLIDADA
    # =====================================================

    seccion(
        "📈 Evolución mensual consolidada"
    )

    st.markdown(
        (
            '<div class="info">'
            "Los gráficos permiten identificar tendencias, "
            "variaciones operacionales y cambios en el comportamiento "
            "económico del servicio."
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    resumen_costos_mensual = (
        costos
        .groupby(
            [
                "Año",
                "Mes",
                "Periodo_Texto",
            ],
            as_index=False,
        )[
            "Monto"
        ]
        .sum()
        .sort_values(
            [
                "Año",
                "Mes",
            ]
        )
    )

    grafico_linea(
        resumen_costos_mensual,
        "Monto",
        "Evolución mensual del costo total",
        "Costo total",
        pesos,
        "#22c55e",
        True,
    )

    resumen_ton_mensual = (
        ton
        .groupby(
            [
                "Año",
                "Mes",
                "Periodo_Texto",
            ],
            as_index=False,
        )[
            "Toneladas"
        ]
        .sum()
        .sort_values(
            [
                "Año",
                "Mes",
            ]
        )
    )

    grafico_linea(
        resumen_ton_mensual,
        "Toneladas",
        "Evolución mensual de toneladas",
        "Toneladas",
        toneladas,
        "#38bdf8",
        False,
    )


    # =====================================================
    # BARRAS APILADAS: COSTOS
    # =====================================================

    seccion(
        "🚛 Composición mensual del costo"
    )

    costos_mensuales = (
        costos
        .groupby(
            [
                "Año",
                "Mes",
                "Periodo_Texto",
                "Tipo_Costo",
            ],
            as_index=False,
        )[
            "Monto"
        ]
        .sum()
        .sort_values(
            [
                "Año",
                "Mes",
            ]
        )
    )

    figura_costos = go.Figure()

    for tipo in TIPOS_COSTO:
        temporal = costos_mensuales[
            costos_mensuales[
                "Tipo_Costo"
            ] == tipo
        ]

        figura_costos.add_trace(
            go.Bar(
                x=temporal[
                    "Periodo_Texto"
                ],

                y=temporal[
                    "Monto"
                ],

                name=tipo,

                marker_color=COLORES_COSTO[
                    tipo
                ],

                customdata=temporal[
                    "Monto"
                ].apply(
                    pesos
                ),

                hovertemplate=(
                    "<b>%{x}</b>"
                    f"<br>{tipo}: %{{customdata}}"
                    "<extra></extra>"
                ),
            )
        )

    total_mensual = (
        costos_mensuales
        .groupby(
            [
                "Año",
                "Mes",
                "Periodo_Texto",
            ],
            as_index=False,
        )[
            "Monto"
        ]
        .sum()
        .sort_values(
            [
                "Año",
                "Mes",
            ]
        )
    )

    figura_costos.add_trace(
        go.Scatter(
            x=total_mensual[
                "Periodo_Texto"
            ],

            y=total_mensual[
                "Monto"
            ],

            name="Costo total",

            mode="lines+markers",

            line=dict(
                color="#f8fafc",
                width=2,
            ),

            marker=dict(
                size=4,
                opacity=0.70,
            ),

            customdata=total_mensual[
                "Monto"
            ].apply(
                pesos
            ),

            hovertemplate=(
                "<b>%{x}</b>"
                "<br>Costo total: %{customdata}"
                "<extra></extra>"
            ),
        )
    )

    figura_costos.update_layout(
        barmode="stack",
        title="Traslado y disposición final por mes",
        xaxis_title="Mes",
        yaxis_title="Costo (CLP)",
    )

    figura_costos.update_xaxes(
        tickangle=-35
    )

    aplicar_eje_clp(
        figura_costos,
        total_mensual[
            "Monto"
        ],
        "y",
    )

    st.plotly_chart(
        formato_grafico(
            figura_costos,
            490,
        ),
        use_container_width=True,
    )


    # =====================================================
    # BARRAS APILADAS: TONELADAS
    # =====================================================

    seccion(
        "⚖️ Toneladas mensuales por residuo"
    )

    toneladas_mensuales = (
        ton
        .groupby(
            [
                "Año",
                "Mes",
                "Periodo_Texto",
                "Residuo",
            ],
            as_index=False,
        )[
            "Toneladas"
        ]
        .sum()
        .sort_values(
            [
                "Año",
                "Mes",
            ]
        )
    )

    figura_toneladas = go.Figure()

    for residuo in RESIDUOS:
        temporal = toneladas_mensuales[
            toneladas_mensuales[
                "Residuo"
            ] == residuo
        ]

        figura_toneladas.add_trace(
            go.Bar(
                x=temporal[
                    "Periodo_Texto"
                ],

                y=temporal[
                    "Toneladas"
                ],

                name=residuo,

                marker_color=COLORES_RESIDUOS[
                    residuo
                ],

                customdata=temporal[
                    "Toneladas"
                ].apply(
                    toneladas
                ),

                hovertemplate=(
                    "<b>%{x}</b>"
                    f"<br>{residuo}: %{{customdata}}"
                    "<extra></extra>"
                ),
            )
        )

    figura_toneladas.update_layout(
        barmode="stack",
        title="Composición mensual de toneladas gestionadas",
        xaxis_title="Mes",
        yaxis_title="Toneladas",
    )

    figura_toneladas.update_xaxes(
        tickangle=-35
    )

    st.plotly_chart(
        formato_grafico(
            figura_toneladas,
            490,
        ),
        use_container_width=True,
    )


    # =====================================================
    # RANKING ACUMULADO
    # =====================================================

    seccion(
        "🏆 Ranking acumulado por residuo"
    )

    ranking1, ranking2 = st.columns(
        2
    )

    ranking_costos = (
        costos
        .groupby(
            "Residuo",
            as_index=False,
        )[
            "Monto"
        ]
        .sum()
        .sort_values(
            "Monto",
            ascending=True,
        )
    )

    figura_ranking_costos = px.bar(
        ranking_costos,
        x="Monto",
        y="Residuo",
        orientation="h",
        title="Costo acumulado por residuo",
        template="plotly_dark",
        color="Residuo",
        color_discrete_map=COLORES_RESIDUOS,

        text=ranking_costos[
            "Monto"
        ].apply(
            pesos
        ),
    )

    figura_ranking_costos.update_traces(
        textposition="outside",
        cliponaxis=False,

        hovertemplate=(
            "<b>%{y}</b>"
            "<br>Costo acumulado: %{text}"
            "<extra></extra>"
        ),
    )

    figura_ranking_costos.update_layout(
        showlegend=False,
        xaxis_title="Costo acumulado (CLP)",
        yaxis_title="Residuo",
    )

    aplicar_eje_clp(
        figura_ranking_costos,
        ranking_costos[
            "Monto"
        ],
        "x",
    )

    with ranking1:
        st.plotly_chart(
            formato_grafico(
                figura_ranking_costos,
                400,
            ),
            use_container_width=True,
        )

    ranking_toneladas = (
        ton
        .groupby(
            "Residuo",
            as_index=False,
        )[
            "Toneladas"
        ]
        .sum()
        .sort_values(
            "Toneladas",
            ascending=True,
        )
    )

    figura_ranking_ton = px.bar(
        ranking_toneladas,
        x="Toneladas",
        y="Residuo",
        orientation="h",
        title="Toneladas acumuladas por residuo",
        template="plotly_dark",
        color="Residuo",
        color_discrete_map=COLORES_RESIDUOS,

        text=ranking_toneladas[
            "Toneladas"
        ].apply(
            toneladas
        ),
    )

    figura_ranking_ton.update_traces(
        textposition="outside",
        cliponaxis=False,

        hovertemplate=(
            "<b>%{y}</b>"
            "<br>Toneladas acumuladas: %{text}"
            "<extra></extra>"
        ),
    )

    figura_ranking_ton.update_layout(
        showlegend=False,
        xaxis_title="Toneladas acumuladas",
        yaxis_title="Residuo",
    )

    with ranking2:
        st.plotly_chart(
            formato_grafico(
                figura_ranking_ton,
                400,
            ),
            use_container_width=True,
        )


    # =====================================================
    # DISTRIBUCIÓN PORCENTUAL
    # =====================================================

    seccion(
        "🥧 Distribución porcentual del servicio"
    )

    columna_pie_ton, columna_pie_costos = st.columns(
        2
    )


    # -----------------------------------------------------
    # GRÁFICO DE DONA: TONELADAS
    # -----------------------------------------------------

    resumen_pie_ton = (
        ton
        .groupby(
            "Residuo",
            as_index=False,
        )[
            "Toneladas"
        ]
        .sum()
    )

    resumen_pie_ton[
        "Texto"
    ] = resumen_pie_ton[
        "Toneladas"
    ].apply(
        toneladas
    )

    figura_pie_ton = px.pie(
        resumen_pie_ton,
        names="Residuo",
        values="Toneladas",
        hole=0.56,
        title="Participación de cada residuo sobre el tonelaje total",
        template="plotly_dark",
        color="Residuo",
        color_discrete_map=COLORES_RESIDUOS,

        custom_data=[
            "Texto"
        ],
    )

    figura_pie_ton.update_traces(
        textposition="inside",
        textinfo="percent+label",

        hovertemplate=(
            "<b>%{label}</b>"
            "<br>Toneladas: %{customdata[0]}"
            "<br>Participación: %{percent}"
            "<extra></extra>"
        ),
    )

    figura_pie_ton.update_layout(
        legend_title_text="Residuo"
    )

    with columna_pie_ton:
        st.plotly_chart(
            formato_grafico(
                figura_pie_ton,
                470,
            ),
            use_container_width=True,
        )


    # -----------------------------------------------------
    # GRÁFICO DE DONA: COSTOS
    # -----------------------------------------------------

    resumen_pie_costos = (
        costos
        .groupby(
            "Residuo",
            as_index=False,
        )[
            "Monto"
        ]
        .sum()
    )

    resumen_pie_costos[
        "Texto"
    ] = resumen_pie_costos[
        "Monto"
    ].apply(
        pesos
    )

    figura_pie_costos = px.pie(
        resumen_pie_costos,
        names="Residuo",
        values="Monto",
        hole=0.56,
        title="Participación de cada residuo en disposición y traslado",
        template="plotly_dark",
        color="Residuo",
        color_discrete_map=COLORES_RESIDUOS,

        custom_data=[
            "Texto"
        ],
    )

    figura_pie_costos.update_traces(
        textposition="inside",
        textinfo="percent+label",

        hovertemplate=(
            "<b>%{label}</b>"
            "<br>Costo total: %{customdata[0]}"
            "<br>Participación: %{percent}"
            "<extra></extra>"
        ),
    )

    figura_pie_costos.update_layout(
        legend_title_text="Residuo"
    )

    with columna_pie_costos:
        st.plotly_chart(
            formato_grafico(
                figura_pie_costos,
                470,
            ),
            use_container_width=True,
        )


    # =====================================================
    # TABLA CONSOLIDADA
    # =====================================================

    seccion(
        "📋 Resumen consolidado por residuo"
    )

    tabla_costos = costos.pivot_table(
        index="Residuo",
        columns="Tipo_Costo",
        values="Monto",
        aggfunc="sum",
        fill_value=0,
    )

    for columna in TIPOS_COSTO:
        if columna not in tabla_costos:
            tabla_costos[
                columna
            ] = 0

    tabla_costos[
        "Costo total"
    ] = (
        tabla_costos[
            "Disposición"
        ]
        + tabla_costos[
            "Traslado"
        ]
    )

    tabla_toneladas = (
        ton
        .groupby(
            "Residuo"
        )[
            "Toneladas"
        ]
        .sum()
    )

    tabla = (
        pd.DataFrame(
            index=RESIDUOS
        )
        .join(
            tabla_costos
        )
        .join(
            tabla_toneladas
        )
        .fillna(0)
        .reset_index()
        .rename(
            columns={
                "index": "Residuo"
            }
        )
    )

    tabla_mostrar = pd.DataFrame(
        {
            "Residuo": tabla[
                "Residuo"
            ],

            "Costo total (CLP)": tabla[
                "Costo total"
            ].apply(
                pesos
            ),

            "Costo de traslado (CLP)": tabla[
                "Traslado"
            ].apply(
                pesos
            ),

            "Costo de disposición (CLP)": tabla[
                "Disposición"
            ].apply(
                pesos
            ),

            "Toneladas gestionadas": tabla[
                "Toneladas"
            ].apply(
                toneladas
            ),
        }
    )

    st.dataframe(
        tabla_mostrar,
        use_container_width=True,
        hide_index=True,
    )


    # =====================================================
    # PIE DE PÁGINA
    # =====================================================

    st.markdown(
        (
            '<div class="pie-pagina">'
            f"<b>Panel desarrollado por {AUTOR}</b><br>"
            f"{CARGO} | SAIVAM<br>"
            f"Versión {VERSION} | "
            f"Última actualización: {nombre_periodo(fecha_maxima)}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


except FileNotFoundError:
    st.error(
        "No se encontró la planilla Excel."
    )

    st.write(
        "Verifica que el archivo esté en la misma carpeta "
        "que app.py y mantenga exactamente este nombre:"
    )

    st.code(
        ARCHIVO_EXCEL
    )


except Exception as error:
    st.error(
        "Ocurrió un error al cargar la planilla."
    )

    st.exception(
        error
    )