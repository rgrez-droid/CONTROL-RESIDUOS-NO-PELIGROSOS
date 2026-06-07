import base64
import hashlib
import hmac
import mimetypes
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Analisis Diesel SERFOCOL",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ARCHIVO_EXCEL = "DIESEL SERFOCOL- V01.xlsx"
LOGO_SUPERIOR = "logo1"
SELLO_AGUA = "logoredondo"
NOMBRE_INICIAL_SELFIE = "selfie"


def buscar_imagen(nombre_base):
    for extension in ["", ".png", ".jpg", ".jpeg", ".webp"]:
        ruta = Path(f"{nombre_base}{extension}")
        if ruta.exists() and ruta.is_file():
            return ruta

    return None


def buscar_selfie():
    extensiones = {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
    }

    archivos = sorted(
        archivo
        for archivo in Path(".").glob(
            f"{NOMBRE_INICIAL_SELFIE}*"
        )
        if archivo.is_file()
        and archivo.suffix.lower() in extensiones
    )

    return archivos[0] if archivos else None


def data_uri(ruta):
    if not ruta or not ruta.exists():
        return None

    contenido = base64.b64encode(
        ruta.read_bytes()
    ).decode(
        "utf-8"
    )

    tipo_mime, _ = mimetypes.guess_type(
        ruta.name
    )

    return (
        f"data:{tipo_mime or 'image/png'};"
        f"base64,{contenido}"
    )


logo = data_uri(
    buscar_imagen(
        LOGO_SUPERIOR
    )
)

sello = data_uri(
    buscar_imagen(
        SELLO_AGUA
    )
)

selfie = data_uri(
    buscar_selfie()
)


def calcular_hash(
    contrasena,
    salt,
):
    return hashlib.pbkdf2_hmac(
        "sha256",
        str(
            contrasena
        ).encode(
            "utf-8"
        ),
        bytes.fromhex(
            str(
                salt
            )
        ),
        200_000,
    ).hex()


def validar_credenciales(
    usuario,
    contrasena,
):
    try:
        usuarios = st.secrets[
            "usuarios"
        ]

    except Exception:
        return (
            False,
            "No existen usuarios configurados. "
            "Revise Streamlit Secrets.",
        )

    usuario = str(
        usuario
    ).strip()

    contrasena = str(
        contrasena
    )

    if (
        not usuario
        or usuario not in usuarios
    ):
        return (
            False,
            "Usuario o contrasena incorrectos.",
        )

    datos = usuarios[
        usuario
    ]

    # Formato simple:
    #
    # [usuarios]
    # ricardo = "ClaveSegura"
    #
    if isinstance(
        datos,
        str,
    ):
        valido = hmac.compare_digest(
            contrasena,
            datos,
        )

        return (
            (
                True,
                None,
            )
            if valido
            else (
                False,
                "Usuario o contrasena incorrectos.",
            )
        )

    # Formato avanzado con hash:
    #
    # [usuarios.ricardo]
    # salt = "..."
    # password_hash = "..."
    #
    try:
        valido = hmac.compare_digest(
            calcular_hash(
                contrasena,
                datos[
                    "salt"
                ],
            ),
            str(
                datos[
                    "password_hash"
                ]
            ),
        )

        return (
            (
                True,
                None,
            )
            if valido
            else (
                False,
                "Usuario o contrasena incorrectos.",
            )
        )

    except Exception:
        return (
            False,
            "La configuracion de usuarios "
            "en Streamlit Secrets no es valida.",
        )


def css_sello():
    if not sello:
        return ""

    return f"""
    .stApp::before {{
        content: "";
        position: fixed;
        top: 17%;
        left: 50%;
        transform:
            translateX(-50%);
        width:
            760px;
        height:
            760px;
        background-image:
            url("{sello}");
        background-repeat:
            no-repeat;
        background-position:
            center;
        background-size:
            contain;
        opacity:
            0.075;
        z-index:
            0;
        pointer-events:
            none;
    }}
    """


def mostrar_login():
    st.markdown(
        f"""
        <style>

        {css_sello()}

        html,
        body,
        .stApp {{
            min-height:
                100vh;
            background:
                #10182B !important;
            color:
                #FFFFFF !important;
        }}

        .stApp {{
            border-top:
                1px solid
                rgba(
                    255,
                    255,
                    255,
                    0.95
                );
        }}

        header[data-testid="stHeader"],
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        footer,
        section[data-testid="stSidebar"],
        button[data-testid="stSidebarCollapsedControl"] {{
            display:
                none !important;
        }}

        .block-container {{
            max-width:
                680px !important;
            padding-top:
                0.95rem !important;
            padding-bottom:
                0.25rem !important;
            position:
                relative;
            z-index:
                1;
        }}

        .contenedor-avatar {{
            display:
                flex;
            justify-content:
                center;
            margin:
                0 auto 10px;
        }}

        .avatar-circular {{
            width:
                148px;
            height:
                148px;
            overflow:
                hidden;
            background:
                #D8D8D8;
            border:
                4px solid
                #F59E0B;
            border-radius:
                50%;
            box-shadow:
                0 2px 8px
                rgba(
                    0,
                    0,
                    0,
                    0.18
                );
        }}

        .avatar-circular img {{
            width:
                100%;
            height:
                100%;
            object-fit:
                cover;
            object-position:
                center 46%;
            transform:
                scale(1.16);
        }}

        .avatar-vacio {{
            display:
                flex;
            align-items:
                center;
            justify-content:
                center;
            font-size:
                66px;
        }}

        .titulo-login {{
            color:
                #FFFFFF;
            font-size:
                35px;
            font-weight:
                900;
            line-height:
                1.12;
            letter-spacing:
                -0.6px;
            text-align:
                center;
        }}

        .subtitulo-login {{
            margin:
                10px 0 13px;
            color:
                #FFFFFF;
            font-size:
                15px;
            font-weight:
                500;
            line-height:
                1.3;
            text-align:
                center;
        }}

        div[data-testid="stForm"] {{
            padding:
                0 !important;
            background:
                transparent !important;
            border:
                none !important;
        }}

        div[data-testid="stWidgetLabel"] p,
        div[data-testid="stWidgetLabel"] label,
        label[data-testid="stWidgetLabel"],
        label[data-testid="stWidgetLabel"] p {{
            color:
                #FFFFFF !important;
            opacity:
                1 !important;
            font-size:
                13px !important;
            font-weight:
                700 !important;
        }}

        div[data-testid="stTextInput"] input {{
            min-height:
                39px !important;
            color:
                #111827 !important;
            background:
                #F8FAFC !important;
            border:
                1px solid
                #E5E7EB !important;
            border-radius:
                8px !important;
        }}

        div[data-testid="stTextInput"] input:focus {{
            border-color:
                #CBD5E1 !important;
            box-shadow:
                none !important;
        }}

        div[data-testid="stFormSubmitButton"] button {{
            width:
                100%;
            min-height:
                39px !important;
            color:
                #FFFFFF !important;
            background:
                #F44040 !important;
            border:
                1px solid
                #F44040 !important;
            border-radius:
                8px !important;
            font-size:
                14px !important;
            font-weight:
                700 !important;
        }}

        div[data-testid="stFormSubmitButton"] button:hover {{
            background:
                #E93333 !important;
            border-color:
                #E93333 !important;
        }}

        .pie-login {{
            margin-top:
                15px;
            padding-top:
                10px;
            border-top:
                1px solid
                rgba(
                    148,
                    163,
                    184,
                    0.36
                );
            text-align:
                center;
        }}

        .pie-login-titulo {{
            color:
                #FFFFFF;
            font-size:
                13px;
            font-weight:
                800;
        }}

        .pie-login-subtitulo,
        .pie-login-restringido {{
            margin-top:
                3px;
            color:
                #7FB4F4;
            font-size:
                12px;
            font-weight:
                500;
        }}

        @media (
            max-width:
                768px
        ) {{
            .block-container {{
                max-width:
                    92% !important;
                padding-top:
                    0.65rem !important;
            }}

            .avatar-circular {{
                width:
                    132px;
                height:
                    132px;
            }}

            .titulo-login {{
                font-size:
                    29px;
            }}
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )

    avatar = (
        (
            '<div class="contenedor-avatar">'
            '<div class="avatar-circular">'
            f'<img src="{selfie}" '
            'alt="Fotografia de acceso">'
            '</div>'
            '</div>'
        )
        if selfie
        else (
            '<div class="contenedor-avatar">'
            '<div class="avatar-circular avatar-vacio">'
            '👤'
            '</div>'
            '</div>'
        )
    )

    st.markdown(
        avatar,
        unsafe_allow_html=True,
    )

    st.markdown(
        (
            '<div class="titulo-login">'
            '🔐 Acceso restringido'
            '</div>'
            '<div class="subtitulo-login">'
            'Ingresa tu usuario y contrasena '
            'para visualizar el panel.'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    with st.form(
        "formulario_acceso",
        clear_on_submit=False,
    ):
        usuario = st.text_input(
            "Usuario"
        )

        contrasena = st.text_input(
            "Contrasena",
            type="password",
        )

        ingresar = st.form_submit_button(
            "Ingresar",
            use_container_width=True,
        )

    if ingresar:
        valido, mensaje = validar_credenciales(
            usuario,
            contrasena,
        )

        if valido:
            st.session_state[
                "acceso_autorizado"
            ] = True

            st.rerun()

        st.error(
            mensaje
        )

    st.markdown(
        (
            '<div class="pie-login">'
            '<div class="pie-login-titulo">'
            'Panel desarrollado por Ricardo Grez'
            '</div>'
            '<div class="pie-login-subtitulo">'
            'Administrador de Contrato | SAIVAM'
            '</div>'
            '<div class="pie-login-restringido">'
            'Acceso restringido para usuarios autorizados'
            '</div>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    st.stop()


if "acceso_autorizado" not in st.session_state:
    st.session_state[
        "acceso_autorizado"
    ] = False

if not st.session_state[
    "acceso_autorizado"
]:
    mostrar_login()


st.markdown(
    f"""
    <style>

    {css_sello()}

    html {{
        color-scheme:
            dark;
    }}

    .stApp,
    .main {{
        background:
            #0F172A;
        color:
            #E5E7EB;
    }}

    header[data-testid="stHeader"],
    div[data-testid="stToolbar"],
    div[data-testid="stDecoration"],
    footer,
    section[data-testid="stSidebar"],
    button[data-testid="stSidebarCollapsedControl"] {{
        display:
            none !important;
    }}

    .block-container {{
        position:
            relative;
        z-index:
            2;
        max-width:
            100% !important;
        padding-top:
            2.4rem;
        padding-bottom:
            1.5rem;
    }}

    .titulo-principal {{
        font-size:
            42px;
        font-weight:
            800;
        color:
            #F8FAFC;
        margin-bottom:
            8px;
        line-height:
            1.15;
    }}

    .subtitulo {{
        font-size:
            18px;
        color:
            #CBD5E1;
        margin-bottom:
            25px;
        line-height:
            1.4;
    }}

    .section-title {{
        font-size:
            25px;
        font-weight:
            800;
        color:
            #F8FAFC;
        margin-top:
            35px;
        margin-bottom:
            15px;
        border-left:
            6px solid
            #F59E0B;
        padding-left:
            12px;
    }}

    .card {{
        background:
            linear-gradient(
                135deg,
                #1E293B,
                #111827
            );
        padding:
            22px;
        border-radius:
            18px;
        box-shadow:
            0 4px 16px
            rgba(
                0,
                0,
                0,
                0.45
            );
        text-align:
            center;
        border:
            1px solid
            #334155;
        min-height:
            118px;
        display:
            flex;
        flex-direction:
            column;
        justify-content:
            center;
    }}

    .card-title {{
        font-size:
            15px;
        color:
            #CBD5E1;
        font-weight:
            600;
        line-height:
            1.25;
    }}

    .card-value {{
        font-size:
            31px;
        color:
            #F59E0B;
        font-weight:
            900;
        margin-top:
            8px;
    }}

    div[data-testid="stDataFrame"] {{
        background:
            #1E293B;
        border-radius:
            12px;
    }}

    .stSelectbox label,
    .stMultiSelect label,
    .stDateInput label,
    .stNumberInput label {{
        color:
            #E5E7EB !important;
        font-weight:
            700;
    }}

    h1,
    h2,
    h3,
    h4,
    h5,
    h6,
    p,
    label {{
        color:
            #E5E7EB;
    }}

    div[data-baseweb="select"] > div {{
        background:
            #F8FAFC !important;
        color:
            #0F172A !important;
        border-radius:
            10px !important;
        border:
            1px solid
            #CBD5E1 !important;
    }}

    div[data-baseweb="select"] span {{
        color:
            #0F172A !important;
    }}

    input {{
        background:
            #F8FAFC !important;
        color:
            #0F172A !important;
        border-radius:
            8px !important;
    }}

    .logo-header {{
        display:
            flex;
        justify-content:
            flex-end;
        align-items:
            flex-start;
        width:
            100%;
        padding-top:
            5px;
    }}

    .logo-header img {{
        width:
            190px;
        max-width:
            100%;
        height:
            auto;
        background:
            rgba(
                255,
                255,
                255,
                0.95
            );
        padding:
            6px;
        border-radius:
            10px;
        box-shadow:
            0 4px 12px
            rgba(
                0,
                0,
                0,
                0.35
            );
    }}

    .footer-panel {{
        width:
            100%;
        margin-top:
            65px;
        padding:
            24px 10px 12px;
        border-top:
            1px solid
            rgba(
                148,
                163,
                184,
                0.28
            );
        text-align:
            center;
        color:
            #94A3B8;
        font-size:
            14px;
        line-height:
            1.7;
    }}

    .footer-panel strong {{
        color:
            #E2E8F0;
        font-size:
            15px;
    }}

    @media (
        max-width:
            768px
    ) {{
        .titulo-principal {{
            font-size:
                31px;
        }}

        .subtitulo {{
            font-size:
                15px;
        }}

        .logo-header img {{
            width:
                130px;
        }}
    }}

    </style>
    """,
    unsafe_allow_html=True,
)


col_titulo, col_logo = st.columns(
    [
        5,
        1.2,
    ]
)

with col_titulo:
    st.markdown(
        (
            '<div class="titulo-principal">'
            '⛽ Control de Consumo de Diesel SERFOCOL'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        (
            '<div class="subtitulo">'
            'Visualizacion consolidada para el '
            'seguimiento operacional del consumo '
            'de diesel por periodo, descripcion, '
            'equipo y operador.'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

with col_logo:
    if logo:
        st.markdown(
            (
                '<div class="logo-header">'
                f'<img src="{logo}" '
                'alt="Logo superior">'
                '</div>'
            ),
            unsafe_allow_html=True,
        )


def titulo(
    texto
):
    st.markdown(
        (
            '<div class="section-title">'
            f'{texto}'
            '</div>'
        ),
        unsafe_allow_html=True,
    )


def tarjeta(
    nombre,
    valor,
):
    st.markdown(
        (
            '<div class="card">'
            '<div class="card-title">'
            f'{nombre}'
            '</div>'
            '<div class="card-value">'
            f'{valor}'
            '</div>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )


try:
    df = pd.read_excel(
        ARCHIVO_EXCEL,
        header=8,
        usecols="A:F",
    )

    df.columns = (
        df.columns
        .astype(
            str
        )
        .str
        .strip()
    )

    df = df.loc[
        :,
        ~df.columns.str.contains(
            "Unnamed"
        ),
    ].dropna(
        how="all"
    )

    for columna in [
        "Fechas",
        "Lts",
    ]:
        if columna not in df.columns:
            st.error(
                f"No se encontro la columna '{columna}'."
            )

            st.write(
                "Columnas detectadas:",
                list(
                    df.columns
                ),
            )

            st.stop()

    df = df.dropna(
        subset=[
            "Fechas",
            "Lts",
        ],
        how="all",
    )

    df[
        "Lts"
    ] = pd.to_numeric(
        df[
            "Lts"
        ],
        errors="coerce",
    )

    df = df[
        df[
            "Lts"
        ].notna()
        & (
            df[
                "Lts"
            ]
            > 0
        )
    ]

    df[
        "Fechas"
    ] = pd.to_datetime(
        df[
            "Fechas"
        ],
        errors="coerce",
        dayfirst=True,
    )

    df = df[
        df[
            "Fechas"
        ].notna()
    ]

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
        12: "Diciembre",
    }

    orden_meses = list(
        meses_espanol.values()
    )

    df[
        "Año"
    ] = df[
        "Fechas"
    ].dt.year.astype(
        int
    )

    df[
        "Mes"
    ] = df[
        "Fechas"
    ].dt.month

    df[
        "Mes_Nombre"
    ] = df[
        "Mes"
    ].map(
        meses_espanol
    )

    df[
        "Periodo"
    ] = df[
        "Fechas"
    ].dt.strftime(
        "%Y-%m"
    )

    df[
        "Fecha"
    ] = df[
        "Fechas"
    ].dt.strftime(
        "%d-%m-%Y"
    )

    titulo(
        "🔎 Filtros de analisis"
    )

    df_filtrado = df.copy()

    colf1, colf2, colf3 = st.columns(
        3
    )

    with colf1:
        años = st.multiselect(
            "Año",
            sorted(
                df[
                    "Año"
                ].unique()
            ),
            placeholder="Seleccionar año",
        )

        if años:
            df_filtrado = df_filtrado[
                df_filtrado[
                    "Año"
                ].isin(
                    años
                )
            ]

    with colf2:
        opciones_meses = [
            mes
            for mes in orden_meses
            if mes in df[
                "Mes_Nombre"
            ].unique()
        ]

        meses = st.multiselect(
            "Mes",
            opciones_meses,
            placeholder="Seleccionar mes",
        )

        if meses:
            df_filtrado = df_filtrado[
                df_filtrado[
                    "Mes_Nombre"
                ].isin(
                    meses
                )
            ]

    with colf3:
        if "Descripción" in df.columns:
            opciones = sorted(
                df[
                    "Descripción"
                ]
                .dropna()
                .astype(
                    str
                )
                .unique()
            )

            descripciones = st.multiselect(
                "Descripcion",
                opciones,
                placeholder="Seleccionar descripcion",
            )

            if descripciones:
                df_filtrado = df_filtrado[
                    df_filtrado[
                        "Descripción"
                    ]
                    .astype(
                        str
                    )
                    .isin(
                        descripciones
                    )
                ]

    titulo(
        "📅 Filtro por rango de fechas"
    )

    rango = st.date_input(
        "Selecciona rango de fechas",
        value=(
            df[
                "Fechas"
            ].min().date(),
            df[
                "Fechas"
            ].max().date(),
        ),
    )

    if (
        isinstance(
            rango,
            (
                list,
                tuple,
            ),
        )
        and len(
            rango
        )
        == 2
    ):
        inicio, fin = rango

        df_filtrado = df_filtrado[
            (
                df_filtrado[
                    "Fechas"
                ].dt.date
                >= inicio
            )
            & (
                df_filtrado[
                    "Fechas"
                ].dt.date
                <= fin
            )
        ]

    titulo(
        "📌 Indicadores principales"
    )

    total_litros = df_filtrado[
        "Lts"
    ].sum()

    total_registros = len(
        df_filtrado
    )

    promedio_carga = (
        df_filtrado[
            "Lts"
        ].mean()
        if total_registros
        else 0
    )

    consumo_por_mes = (
        df_filtrado
        .groupby(
            "Periodo"
        )[
            "Lts"
        ]
        .sum()
    )

    promedio_mensual = (
        consumo_por_mes.mean()
        if not consumo_por_mes.empty
        else 0
    )

    c1, c2, c3, c4 = st.columns(
        4
    )

    with c1:
        tarjeta(
            "Total litros consumidos",
            f"{total_litros:,.0f} L",
        )

    with c2:
        tarjeta(
            "Cantidad de registros",
            f"{total_registros}",
        )

    with c3:
        tarjeta(
            "Promedio por carga",
            f"{promedio_carga:,.1f} L",
        )

    with c4:
        tarjeta(
            "Promedio mensual de consumo diesel",
            f"{promedio_mensual:,.0f} L",
        )

    titulo(
        "📊 Analisis grafico de consumos"
    )

    if df_filtrado.empty:
        st.warning(
            "No existen datos para mostrar "
            "con los filtros seleccionados."
        )

    else:
        grafico_layout = dict(
            plot_bgcolor="#111827",
            paper_bgcolor="#111827",
            font=dict(
                color="#F8FAFC",
                size=15,
            ),
            title_font=dict(
                size=24,
                color="#FFFFFF",
            ),
            legend=dict(
                font=dict(
                    size=17,
                    color="#FFFFFF",
                ),
                title=dict(
                    font=dict(
                        size=18,
                        color="#F8FAFC",
                    )
                ),
                bgcolor="rgba(15, 23, 42, 0.92)",
                bordercolor="#64748B",
                borderwidth=1,
                x=1.02,
                xanchor="left",
                y=1,
                yanchor="top",
            ),
            margin=dict(
                l=60,
                r=210,
                t=80,
                b=60,
            ),
        )

        consumo_anual = (
            df_filtrado
            .groupby(
                "Año"
            )[
                "Lts"
            ]
            .sum()
            .reset_index()
            .sort_values(
                "Año"
            )
        )

        fig_anual = px.bar(
            consumo_anual,
            x="Año",
            y="Lts",
            text="Lts",
            title="Consumo anual de diesel",
            color="Lts",
            color_continuous_scale="Oranges",
            template="plotly_dark",
        )

        fig_anual.update_traces(
            texttemplate="%{text:,.0f} L",
            textposition="outside",
        )

        fig_anual.update_layout(
            height=440,
            xaxis_title="Año",
            yaxis_title="Litros",
            showlegend=False,
            **grafico_layout,
        )

        fig_anual.update_xaxes(
            tickmode="array",
            tickvals=consumo_anual[
                "Año"
            ].tolist(),
            ticktext=[
                str(
                    año
                )
                for año in consumo_anual[
                    "Año"
                ].tolist()
            ],
        )

        st.plotly_chart(
            fig_anual,
            use_container_width=True,
            config={
                "displayModeBar": False,
            },
        )

        consumo_mensual = (
            df_filtrado
            .groupby(
                [
                    "Año",
                    "Mes",
                    "Mes_Nombre",
                ]
            )[
                "Lts"
            ]
            .sum()
            .reset_index()
            .sort_values(
                [
                    "Año",
                    "Mes",
                ]
            )
        )

        consumo_mensual[
            "Mes_Año"
        ] = (
            consumo_mensual[
                "Mes_Nombre"
            ]
            + " "
            + consumo_mensual[
                "Año"
            ].astype(
                str
            )
        )

        fig_mensual = px.line(
            consumo_mensual,
            x="Mes_Año",
            y="Lts",
            markers=True,
            title="Tendencia mensual de consumo",
            template="plotly_dark",
        )

        fig_mensual.update_traces(
            line=dict(
                width=4,
                color="#F59E0B",
            ),
            marker=dict(
                size=10,
                color="#F97316",
            ),
        )

        fig_mensual.update_layout(
            height=440,
            xaxis_title="Mes",
            yaxis_title="Litros",
            **grafico_layout,
        )

        st.plotly_chart(
            fig_mensual,
            use_container_width=True,
            config={
                "displayModeBar": False,
            },
        )

        titulo(
            "🥧 Distribucion mensual del consumo"
        )

        distribucion = (
            df_filtrado
            .groupby(
                [
                    "Mes",
                    "Mes_Nombre",
                ]
            )[
                "Lts"
            ]
            .sum()
            .reset_index()
            .sort_values(
                "Mes"
            )
        )

        total_distribucion = (
            distribucion[
                "Lts"
            ].sum()
        )

        distribucion[
            "Porcentaje"
        ] = (
            distribucion[
                "Lts"
            ]
            / total_distribucion
            * 100
        )

        fig_torta = px.pie(
            distribucion,
            names="Mes_Nombre",
            values="Lts",
            title=(
                "Participacion mensual "
                "del consumo de diesel"
            ),
            hole=0.55,
            template="plotly_dark",
            color_discrete_sequence=(
                px.colors
                .sequential
                .Oranges_r
            ),
        )

        fig_torta.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate=(
                "<b>%{label}</b><br>"
                "Litros consumidos: "
                "%{value:,.0f} L<br>"
                "Participacion: "
                "%{percent}"
                "<extra></extra>"
            ),
            marker=dict(
                line=dict(
                    color="#0F172A",
                    width=2,
                )
            ),
        )

        fig_torta.update_layout(
            height=580,
            **grafico_layout,
            legend_title_text="Mes",
            annotations=[
                dict(
                    text=(
                        f"{total_distribucion:,.0f} L"
                        "<br>Total"
                    ),
                    x=0.5,
                    y=0.5,
                    font_size=22,
                    font_color="#F8FAFC",
                    showarrow=False,
                )
            ],
        )

        st.plotly_chart(
            fig_torta,
            use_container_width=True,
            config={
                "displayModeBar": False,
            },
        )

        titulo(
            "📋 Resumen mensual de participacion"
        )

        tabla_mensual = distribucion.copy()

        tabla_mensual[
            "Litros"
        ] = (
            tabla_mensual[
                "Lts"
            ]
            .round()
            .astype(
                int
            )
        )

        tabla_mensual[
            "Participacion"
        ] = (
            tabla_mensual[
                "Porcentaje"
            ]
            .round(
                1
            )
            .astype(
                str
            )
            + "%"
        )

        st.dataframe(
            tabla_mensual[
                [
                    "Mes_Nombre",
                    "Litros",
                    "Participacion",
                ]
            ].rename(
                columns={
                    "Mes_Nombre": "Mes",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

        titulo(
            "📆 Consumo mensual por año"
        )

        consumo_barra = (
            df_filtrado
            .groupby(
                [
                    "Año",
                    "Mes",
                    "Mes_Nombre",
                ]
            )[
                "Lts"
            ]
            .sum()
            .reset_index()
            .sort_values(
                [
                    "Año",
                    "Mes",
                ]
            )
        )

        consumo_barra[
            "Año_Texto"
        ] = consumo_barra[
            "Año"
        ].astype(
            str
        )

        fig_barra = px.bar(
            consumo_barra,
            x="Mes_Nombre",
            y="Lts",
            color="Año_Texto",
            barmode="group",
            text="Lts",
            title=(
                "Comparativo mensual por año"
            ),
            template="plotly_dark",
            labels={
                "Año_Texto": "Año",
                "Mes_Nombre": "Mes",
                "Lts": "Litros",
            },
        )

        fig_barra.update_traces(
            texttemplate="%{text:,.0f} L",
            textposition="outside",
        )

        fig_barra.update_layout(
            height=500,
            xaxis_title="Mes",
            yaxis_title="Litros",
            **grafico_layout,
            legend_title_text="Año",
        )

        st.plotly_chart(
            fig_barra,
            use_container_width=True,
            config={
                "displayModeBar": False,
            },
        )

        titulo(
            "📅 Resumen de consumo"
        )

        if "Equipo" in df_filtrado.columns:
            resumen_equipo = (
                df_filtrado
                .pivot_table(
                    index="Equipo",
                    columns="Año",
                    values="Lts",
                    aggfunc="sum",
                    fill_value=0,
                )
            )

            st.dataframe(
                resumen_equipo,
                use_container_width=True,
            )

    titulo(
        "📋 Registro general de diesel"
    )

    columnas = [
        "Fecha",
        "Descripción",
        "Operador",
        "Equipo",
        "N° Salida Existencia",
        "Lts",
        "Año",
        "Mes_Nombre",
        "Periodo",
    ]

    columnas = [
        columna
        for columna in columnas
        if columna in df_filtrado.columns
    ]

    st.dataframe(
        df_filtrado[
            columnas
        ].copy(),
        use_container_width=True,
        hide_index=True,
    )

    titulo(
        "🚨 Alertas de control"
    )

    limite = st.number_input(
        "Definir limite de litros por carga",
        min_value=0,
        value=50,
    )

    alertas = df_filtrado[
        df_filtrado[
            "Lts"
        ]
        > limite
    ]

    if not alertas.empty:
        st.warning(
            "Existen cargas que superan "
            "el limite definido."
        )

        st.dataframe(
            alertas[
                columnas
            ].copy(),
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.success(
            "No existen cargas sobre "
            "el limite definido."
        )

except FileNotFoundError:
    st.error(
        "No se encontro la planilla Excel."
    )

    st.write(
        "Verifica que el archivo este "
        "en la misma carpeta que app.py."
    )

    st.code(
        ARCHIVO_EXCEL
    )

except Exception as error:
    st.error(
        "Ocurrio un error al cargar la planilla."
    )

    st.write(
        error
    )


st.markdown(
    (
        '<div class="footer-panel">'
        '<strong>'
        'Panel desarrollado por Ricardo Grez'
        '</strong><br>'
        'Administrador de Contrato | SAIVAM'
        '<br>'
        'Version 1.0 | '
        'Ultima actualizacion: Mayo 2026'
        '</div>'
    ),
    unsafe_allow_html=True,
)