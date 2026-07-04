import base64
import glob
import hashlib
import hmac
import importlib
import os
import re
import unicodedata
from collections.abc import Mapping

import pandas as pd
import plotly.express as px
import streamlit as st


# =========================================================
# CONFIGURACION GENERAL
# =========================================================

st.set_page_config(
    page_title="Analisis de Residuos No Peligrosos",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

ARCHIVO_EXCEL = "RESIDUOS NO PELIGROSOS - V01.xlsx"
LOGO_SUPERIOR = "logo1.png"

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


# =========================================================
# UTILIDADES
# =========================================================

def archivo_a_base64(ruta):
    if not ruta or not os.path.exists(ruta):
        return ""

    with open(ruta, "rb") as archivo:
        return base64.b64encode(
            archivo.read()
        ).decode("utf-8")


def buscar_archivo_sello():
    """
    Busca el sello de agua con nombre logoredondo.

    Archivos válidos:
        logoredondo.png
        logoredondo.jpg
        logoredondo.jpeg
        logoredondo.webp
        logoredondo
    """

    posibles = [
        "logoredondo.png",
        "logoredondo.jpg",
        "logoredondo.jpeg",
        "logoredondo.webp",
        "logoredondo",
    ]

    for archivo in posibles:
        if os.path.exists(archivo):
            return archivo

    return None


def obtener_tipo_imagen(ruta):
    extension = (
        os.path.splitext(ruta)[1]
        .lower()
        .replace(".", "")
    )

    if extension == "jpg":
        return "jpeg"

    if extension in [
        "jpeg",
        "png",
        "webp",
    ]:
        return extension

    return "png"


def buscar_selfie():
    """
    Busca automáticamente una imagen cuyo nombre comience por selfie.

    Ejemplos válidos:
        selfie.png
        selfie.jpg
        selfie.jpeg
        selfie.webp
    """

    for extension in (
        "png",
        "jpg",
        "jpeg",
        "webp",
    ):
        archivos = sorted(
            glob.glob(
                f"selfie*.{extension}"
            )
        )

        if archivos:
            return archivos[0]

    return None


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

    coincidencia = re.match(
        (
            r"^(enero|febrero|marzo|abril|mayo|junio|julio|"
            r"agosto|septiembre|octubre|noviembre|diciembre)"
            r"\s+(\d{4})$"
        ),
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
        return (
            "$ "
            + f"{int(round(float(valor))):,}"
            .replace(",", ".")
        )

    except (
        TypeError,
        ValueError,
    ):
        return "$ 0"


def toneladas(valor):
    try:
        return (
            f"{float(valor):,.1f}"
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
# ESTILO GENERAL
# =========================================================

def aplicar_estilo_general():
    st.markdown(
        """
<style>

/* Ocultar elementos nativos de Streamlit */
[data-testid="stSidebar"],
[data-testid="collapsedControl"],
header[data-testid="stHeader"],
#MainMenu,
footer {
    display: none !important;
}

/* Fondo general */
html,
body,
[data-testid="stAppViewContainer"],
.stApp {
    background: #0f172a !important;
    color: #e5e7eb !important;
}

.block-container {
    padding-top: 0.7rem !important;
    padding-bottom: 1rem !important;
    position: relative !important;
    z-index: 2 !important;
}

/* Encabezados */
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

/* Tarjetas */
.tarjeta {
    background:
        linear-gradient(
            135deg,
            rgba(30, 41, 59, 0.94),
            rgba(17, 24, 39, 0.94)
        );

    border: 1px solid #334155;
    border-radius: 15px;
    padding: 17px 11px;
    min-height: 112px;
    text-align: center;

    box-shadow:
        0 4px 14px
        rgba(
            0,
            0,
            0,
            0.18
        );
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

/* Resumen ejecutivo */
.resumen {
    background:
        linear-gradient(
            135deg,
            rgba(23, 32, 51, 0.94),
            rgba(17, 24, 39, 0.94)
        );

    border: 1px solid #334155;
    border-left: 5px solid #22c55e;
    border-radius: 13px;
    padding: 16px 18px;
    color: #e5e7eb;
    line-height: 1.65;
}

/* Pie de página del panel */
.pie-pagina {
    border-top: 1px solid #334155;
    color: #94a3b8;
    font-size: 12px;
    line-height: 1.65;
    margin-top: 38px;
    padding: 18px 0 8px;
    text-align: center;
}

/* Filtros */
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


# =========================================================
# SELLO DE AGUA
# =========================================================

def agregar_sello_agua_panel():
    ruta_sello = buscar_archivo_sello()

    if not ruta_sello:
        st.warning(
            "No se encontró la imagen del sello de agua. "
            "Verifica que el archivo se llame logoredondo.png y esté en la misma carpeta que app.py."
        )
        return

    sello = archivo_a_base64(
        ruta_sello
    )

    tipo_imagen = obtener_tipo_imagen(
        ruta_sello
    )

    st.markdown(
        (
            "<style>"

            ".marca-agua-panel {"
            "position:fixed;"
            "top:54%;"
            "left:50%;"
            "width:760px;"
            "height:760px;"
            "transform:translate(-50%,-50%);"
            f"background-image:url('data:image/{tipo_imagen};base64,{sello}');"
            "background-position:center;"
            "background-repeat:no-repeat;"
            "background-size:contain;"
            "opacity:0.08;"
            "pointer-events:none;"
            "z-index:1;"
            "}"

            ".block-container {"
            "position:relative !important;"
            "z-index:2 !important;"
            "}"

            "</style>"

            '<div class="marca-agua-panel"></div>'
        ),
        unsafe_allow_html=True,
    )


def agregar_sello_agua_login():
    ruta_sello = buscar_archivo_sello()

    if not ruta_sello:
        return

    sello = archivo_a_base64(
        ruta_sello
    )

    tipo_imagen = obtener_tipo_imagen(
        ruta_sello
    )

    st.markdown(
        (
            "<style>"

            ".login-sello-agua {"
            "position:fixed;"
            "top:58%;"
            "left:50%;"
            "width:760px;"
            "height:760px;"
            "transform:translate(-50%,-50%);"
            f"background-image:url('data:image/{tipo_imagen};base64,{sello}');"
            "background-position:center;"
            "background-repeat:no-repeat;"
            "background-size:contain;"
            "opacity:0.05;"
            "pointer-events:none;"
            "z-index:1;"
            "}"

            ".login-wrapper,"
            "div[data-testid='stForm'],"
            ".login-pie-fijo {"
            "position:relative !important;"
            "z-index:3 !important;"
            "}"

            "</style>"

            '<div class="login-sello-agua"></div>'
        ),
        unsafe_allow_html=True,
    )


# =========================================================
# CONTROL DE ACCESO
# =========================================================

def obtener_usuarios_desde_secrets():
    for seccion in (
        "usuarios",
        "users",
    ):
        if seccion in st.secrets:
            return st.secrets[
                seccion
            ]

    return {}


def obtener_registro_usuario(usuario_ingresado):
    usuario_buscado = str(
        usuario_ingresado
    ).strip().lower()

    for usuario, configuracion in obtener_usuarios_desde_secrets().items():

        if (
            str(usuario).strip().lower()
            == usuario_buscado
        ):
            return configuracion

    return None


def verificar_bcrypt(
    clave_ingresada,
    hash_guardado,
):
    try:
        bcrypt = importlib.import_module(
            "bcrypt"
        )

        return bool(
            bcrypt.checkpw(
                clave_ingresada.encode(
                    "utf-8"
                ),
                hash_guardado.encode(
                    "utf-8"
                ),
            )
        )

    except Exception:
        return False


def verificar_clave(
    clave_ingresada,
    configuracion_usuario,
):
    if configuracion_usuario is None:
        return False

    if isinstance(
        configuracion_usuario,
        Mapping,
    ):
        valor_guardado = (
            configuracion_usuario.get(
                "password_hash"
            )
            or configuracion_usuario.get(
                "clave_hash"
            )
            or configuracion_usuario.get(
                "hash"
            )
            or configuracion_usuario.get(
                "password"
            )
            or configuracion_usuario.get(
                "clave"
            )
        )

    else:
        valor_guardado = configuracion_usuario

    if valor_guardado is None:
        return False

    valor_guardado = str(
        valor_guardado
    ).strip()

    clave_ingresada = str(
        clave_ingresada
    )

    if valor_guardado.startswith(
        (
            "$2a$",
            "$2b$",
            "$2y$",
        )
    ):
        return verificar_bcrypt(
            clave_ingresada,
            valor_guardado,
        )

    if valor_guardado.lower().startswith(
        "sha256$"
    ):
        hash_guardado = (
            valor_guardado
            .split(
                "$",
                1,
            )[1]
            .strip()
            .lower()
        )

        hash_ingresado = hashlib.sha256(
            clave_ingresada.encode(
                "utf-8"
            )
        ).hexdigest()

        return hmac.compare_digest(
            hash_ingresado,
            hash_guardado,
        )

    if re.fullmatch(
        r"[a-fA-F0-9]{64}",
        valor_guardado,
    ):
        hash_ingresado = hashlib.sha256(
            clave_ingresada.encode(
                "utf-8"
            )
        ).hexdigest()

        return hmac.compare_digest(
            hash_ingresado,
            valor_guardado.lower(),
        )

    return hmac.compare_digest(
        clave_ingresada,
        valor_guardado,
    )


def construir_foto_acceso():
    selfie = buscar_selfie()

    if not selfie:
        return (
            '<div class="login-foto-placeholder">'
            "👤"
            "</div>"
        )

    extension = (
        os.path.splitext(
            selfie
        )[1]
        .lower()
        .replace(
            ".",
            "",
        )
    )

    if extension == "jpg":
        extension = "jpeg"

    imagen_base64 = archivo_a_base64(
        selfie
    )

    return (
        '<div class="login-foto-contenedor">'
        '<img '
        'class="login-foto" '
        f'src="data:image/{extension};base64,{imagen_base64}" '
        'alt="Foto de acceso">'
        "</div>"
    )


def aplicar_estilo_acceso():
    st.markdown(
        """
<style>

/* Contenedor central */
.login-wrapper {
    width: 100%;
    max-width: 680px;
    margin: 0 auto;
    text-align: center;
    position: relative;
    z-index: 4;
}

/* Fotografía circular */
.login-foto-contenedor,
.login-foto-placeholder {
    width: 165px;
    height: 165px;
    margin: 0 auto 14px auto;
    border-radius: 50%;
    border: 4px solid #f59e0b;
    overflow: hidden;
    background: #1e293b;

    box-shadow:
        0 0 0 6px rgba(245, 158, 11, 0.10),
        0 10px 28px rgba(0, 0, 0, 0.38);

    display: flex;
    align-items: center;
    justify-content: center;
}

.login-foto {
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: center 46%;
    transform: scale(1.34);
}

.login-foto-placeholder {
    color: #f8fafc;
    font-size: 62px;
}

/* Título y subtítulo */
.login-titulo {
    color: #f8fafc;
    font-size: 38px;
    font-weight: 900;
    line-height: 1.10;
    margin: 7px 0 9px 0;

    text-shadow:
        0 2px 4px rgba(0, 0, 0, 0.42);
}

.login-subtitulo {
    color: #f8fafc;
    font-size: 15px;
    font-weight: 700;
    line-height: 1.45;
    margin: 0 0 15px 0;
}

/* Formulario */
div[data-testid="stForm"] {
    background: transparent !important;
    border: 0 !important;
    padding: 0 !important;
    box-shadow: none !important;
    position: relative !important;
    z-index: 4 !important;
}

div[data-testid="stForm"] label {
    color: #f8fafc !important;
    font-weight: 800 !important;
    font-size: 14px !important;
}

div[data-testid="stForm"] input {
    background: #f8fafc !important;
    color: #111827 !important;
    border-radius: 8px !important;
    min-height: 47px !important;
}

/* Botón ingresar */
div[data-testid="stFormSubmitButton"] button {
    background: #ff4040 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 900 !important;
    min-height: 46px !important;
    margin-top: 7px !important;
}

div[data-testid="stFormSubmitButton"] button:hover {
    background: #ef4444 !important;
    color: #ffffff !important;
    border: none !important;
}

/* Icono para mostrar la contraseña */
div[data-testid="stTextInput"] button {
    background: transparent !important;
    color: #374151 !important;
    border: none !important;
    box-shadow: none !important;
}

div[data-testid="stTextInput"] button:hover {
    background: transparent !important;
    color: #111827 !important;
    border: none !important;
}

/* Pie fijo inferior */
.login-pie-fijo {
    position: fixed;
    left: 50%;
    bottom: 24px;
    transform: translateX(-50%);
    width: min(92vw, 720px);
    border-top: 1px solid rgba(148, 163, 184, 0.48);
    padding-top: 14px;
    text-align: center;
    line-height: 1.80;
    z-index: 5;
}

/* Texto principal inferior */
.login-pie-titulo {
    color: #f8fafc;
    font-size: 16px;
    font-weight: 900;
    letter-spacing: 0.2px;
}

/* Textos secundarios inferiores */
.login-pie-texto {
    color: #60a5fa;
    font-size: 13px;
    font-weight: 600;
}

/* Ajustes para celulares */
@media screen and (max-width: 768px) {

    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }

    .login-foto-contenedor,
    .login-foto-placeholder {
        width: 145px;
        height: 145px;
    }

    .login-titulo {
        font-size: 31px;
    }

    .login-subtitulo {
        font-size: 13px;
    }

    .login-sello-agua {
        width: 620px;
        height: 620px;
    }

    .login-pie-fijo {
        bottom: 18px;
        padding-top: 11px;
    }

    .login-pie-titulo {
        font-size: 14px;
    }

    .login-pie-texto {
        font-size: 12px;
    }
}

</style>
        """,
        unsafe_allow_html=True,
    )


def mostrar_encabezado_acceso():
    foto = construir_foto_acceso()

    encabezado = (
        '<div class="login-wrapper">'

        f"{foto}"

        '<div class="login-titulo">'
        "🔐 Acceso restringido"
        "</div>"

        '<div class="login-subtitulo">'
        "Ingresa tu usuario y contraseña para visualizar el panel."
        "</div>"

        "</div>"
    )

    st.markdown(
        encabezado,
        unsafe_allow_html=True,
    )


def mostrar_pie_acceso():
    pie = (
        '<div class="login-pie-fijo">'

        '<div class="login-pie-titulo">'
        "Panel desarrollado por Ricardo Grez"
        "</div>"

        '<div class="login-pie-texto">'
        "Administrador de Contrato | SAIVAM"
        "</div>"

        '<div class="login-pie-texto">'
        "Acceso restringido para usuarios autorizados"
        "</div>"

        "</div>"
    )

    st.markdown(
        pie,
        unsafe_allow_html=True,
    )


def mostrar_acceso_restringido():
    aplicar_estilo_acceso()

    agregar_sello_agua_login()

    columna_izquierda, columna_central, columna_derecha = st.columns(
        [
            1.00,
            1.28,
            1.00,
        ]
    )

    with columna_central:

        mostrar_encabezado_acceso()

        with st.form(
            "formulario_acceso",
            clear_on_submit=False,
        ):
            usuario = st.text_input(
                "Usuario",
                key="campo_usuario",
            )

            clave = st.text_input(
                "Contraseña",
                type="password",
                key="campo_clave",
            )

            ingresar = st.form_submit_button(
                "Ingresar",
                use_container_width=True,
            )

        if ingresar:

            registro_usuario = obtener_registro_usuario(
                usuario
            )

            acceso_valido = verificar_clave(
                clave,
                registro_usuario,
            )

            if acceso_valido:
                st.session_state[
                    "acceso_autorizado"
                ] = True

                st.session_state[
                    "usuario_autorizado"
                ] = str(
                    usuario
                ).strip()

                st.rerun()

            else:
                st.error(
                    "Usuario o contraseña incorrectos."
                )

    mostrar_pie_acceso()


# =========================================================
# CARGA Y PREPARACION DE DATOS
# =========================================================

@st.cache_data
def cargar_datos(ruta_excel):
    datos = (
        pd.read_excel(
            ruta_excel
        )
        .dropna(
            how="all"
        )
        .dropna(
            axis=1,
            how="all",
        )
    )

    datos.columns = (
        datos.columns
        .astype(str)
        .str.strip()
    )

    datos = datos.loc[
        :,
        ~datos.columns.str.contains(
            "Unnamed",
            case=False,
        ),
    ]

    columna_fecha = buscar_columna(
        datos.columns,
        "Fecha",
    )

    if columna_fecha is None:
        raise ValueError(
            "No se encontró la columna Fecha."
        )

    datos = datos.rename(
        columns={
            columna_fecha: "Fecha"
        }
    )

    datos[
        "Fecha"
    ] = datos[
        "Fecha"
    ].apply(
        convertir_fecha
    )

    datos = datos[
        datos[
            "Fecha"
        ].notna()
    ].copy()

    if datos.empty:
        raise ValueError(
            "No se detectaron fechas válidas en la planilla."
        )

    datos[
        "Año"
    ] = datos[
        "Fecha"
    ].dt.year

    datos[
        "Mes"
    ] = datos[
        "Fecha"
    ].dt.month

    datos[
        "Mes_Nombre"
    ] = datos[
        "Mes"
    ].map(
        MESES
    )

    datos[
        "Periodo"
    ] = datos[
        "Fecha"
    ].dt.strftime(
        "%Y-%m"
    )

    datos[
        "Periodo_Texto"
    ] = (
        datos[
            "Mes_Nombre"
        ]
        + " "
        + datos[
            "Año"
        ].astype(str)
    )

    return datos


@st.cache_data
def preparar_datos(datos):
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
                datos.columns,
                f"{tipo_costo} {residuo}",
            )

            if columna is None:
                raise ValueError(
                    "No se encontró la columna: "
                    f"{tipo_costo} {residuo}"
                )

            temporal = datos[
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
            ] = datos[
                columna
            ].apply(
                limpiar_numero
            )

            registros_costos.append(
                temporal
            )

        columna_toneladas = buscar_columna(
            datos.columns,
            f"Toneladas {residuo}",
        )

        if columna_toneladas is None:
            raise ValueError(
                "No se encontró la columna: "
                f"Toneladas {residuo}"
            )

        temporal = datos[
            columnas_base
        ].copy()

        temporal[
            "Residuo"
        ] = residuo

        temporal[
            "Toneladas"
        ] = datos[
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

    costos = costos[
        costos[
            "Monto"
        ] > 0
    ].copy()

    toneladas_df = toneladas_df[
        toneladas_df[
            "Toneladas"
        ] > 0
    ].copy()

    return (
        costos,
        toneladas_df,
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
    datos,
    anios,
    residuos,
    meses,
):
    salida = datos.copy()

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


def formato_grafico(
    figura,
    altura=460,
):
    figura.update_layout(
        height=altura,
        plot_bgcolor="rgba(17, 24, 39, 0.92)",
        paper_bgcolor="rgba(17, 24, 39, 0.92)",

        font=dict(
            color="#e5e7eb",
            size=13,
        ),

        title_font=dict(
            size=20,
            color="#f8fafc",
        ),

        legend=dict(
            font=dict(
                color="#f8fafc",
                size=15,
            ),

            title_font=dict(
                color="#f8fafc",
                size=14,
            ),

            bgcolor="rgba(0,0,0,0)",
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

    figura.update_xaxes(
        tickfont=dict(
            color="#cbd5e1",
            size=11,
        ),

        title_font=dict(
            color="#e5e7eb",
            size=12,
        ),

        gridcolor="rgba(148,163,184,.12)",
    )

    figura.update_yaxes(
        tickfont=dict(
            color="#cbd5e1",
            size=11,
        ),

        title_font=dict(
            color="#e5e7eb",
            size=12,
        ),

        gridcolor="rgba(148,163,184,.12)",
    )

    return figura


# =========================================================
# PANEL PRINCIPAL
# =========================================================

def mostrar_panel():
    datos = cargar_datos(
        ARCHIVO_EXCEL
    )

    costos_base, toneladas_base = preparar_datos(
        datos
    )

    fecha_minima = datos[
        "Fecha"
    ].min()

    fecha_maxima = datos[
        "Fecha"
    ].max()

    # -----------------------------------------------------
    # ENCABEZADO
    # -----------------------------------------------------

    col_titulo, col_logo = st.columns(
        [
            5,
            1,
        ]
    )

    with col_titulo:

        st.markdown(
            (
                '<div class="titulo">'
                "♻️ Análisis consolidado de residuos no peligrosos"
                "</div>"
            ),
            unsafe_allow_html=True,
        )

        st.markdown(
            (
                '<div class="subtitulo">'
                "Panel ejecutivo para el seguimiento operacional, "
                "económico y contractual de RAD, corteza, escoria y ceniza."
                "</div>"
            ),
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

                "<b>Fuente:</b> "
                "Control mensual de residuos no peligrosos"

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

    # -----------------------------------------------------
    # FILTROS
    # -----------------------------------------------------

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
                datos[
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
                in datos[
                    "Mes_Nombre"
                ].unique()
            ],
        )

    costos = aplicar_filtros(
        costos_base,
        filtro_anios,
        filtro_residuos,
        filtro_meses,
    )

    ton = aplicar_filtros(
        toneladas_base,
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

    # -----------------------------------------------------
    # CALCULOS
    # -----------------------------------------------------

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
        costos.loc[
            costos[
                "Tipo_Costo"
            ] == "Traslado",
            "Monto",
        ].sum()
    )

    total_disposicion = float(
        costos.loc[
            costos[
                "Tipo_Costo"
            ] == "Disposición",
            "Monto",
        ].sum()
    )

    cantidad_meses = len(
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

    # -----------------------------------------------------
    # INDICADORES
    # -----------------------------------------------------

    indicadores = [
        (
            "Costo total acumulado",
            pesos(total_costos),
            "Disposición y traslado",
            "verde",
        ),

        (
            "Toneladas gestionadas",
            toneladas(total_toneladas),
            "Total del período seleccionado",
            "azul",
        ),

        (
            "Costo total de traslado",
            pesos(total_traslado),
            f"{porcentaje(participacion_traslado)} del costo total",
            "naranjo",
        ),

        (
            "Costo de disposición final",
            pesos(total_disposicion),
            f"{porcentaje(participacion_disposicion)} del costo total",
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
            porcentaje(participacion_traslado),
            "Incidencia sobre el costo total",
            "naranjo",
        ),

        (
            "Participación de la disposición",
            porcentaje(participacion_disposicion),
            "Incidencia sobre el costo total",
            "amarillo",
        ),
    ]

    seccion(
        "📌 Indicadores ejecutivos"
    )

    for inicio in range(
        0,
        8,
        4,
    ):
        columnas = st.columns(
            4
        )

        for columna, datos_tarjeta in zip(
            columnas,
            indicadores[
                inicio:inicio + 4
            ],
        ):
            with columna:

                tarjeta(
                    *datos_tarjeta
                )

    # -----------------------------------------------------
    # RESUMEN EJECUTIVO
    # -----------------------------------------------------

    seccion(
        "📝 Resumen ejecutivo"
    )

    st.markdown(
        (
            '<div class="resumen">'

            "<b>Lectura ejecutiva del período.</b> "

            f"El costo acumulado alcanza "
            f"<b>{pesos(total_costos)}</b>, "

            f"con una participación del traslado equivalente al "
            f"<b>{porcentaje(participacion_traslado)}</b> "

            f"y una incidencia de disposición final del "
            f"<b>{porcentaje(participacion_disposicion)}</b>. "

            f"Durante el período seleccionado se gestionaron "
            f"<b>{toneladas(total_toneladas)}</b> "
            "de residuos no peligrosos."

            "</div>"
        ),
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------
    # TONELADAS ACUMULADAS
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # EVOLUCION MENSUAL
    # -----------------------------------------------------

    seccion(
        "📈 Evolución mensual consolidada"
    )

    resumen_costos = (
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

    resumen_ton = (
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

    figura_costos_linea = px.line(
        resumen_costos,
        x="Periodo_Texto",
        y="Monto",
        markers=True,
        title="Evolución mensual del costo total",
        template="plotly_dark",
    )

    figura_costos_linea.update_traces(
        line=dict(
            width=3,
            color="#22c55e",
        ),

        marker=dict(
            size=5,
        ),

        customdata=resumen_costos[
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

    st.plotly_chart(
        formato_grafico(
            figura_costos_linea
        ),
        use_container_width=True,
    )

    figura_ton_linea = px.line(
        resumen_ton,
        x="Periodo_Texto",
        y="Toneladas",
        markers=True,
        title="Evolución mensual de toneladas",
        template="plotly_dark",
    )

    figura_ton_linea.update_traces(
        line=dict(
            width=3,
            color="#38bdf8",
        ),

        marker=dict(
            size=5,
        ),

        customdata=resumen_ton[
            "Toneladas"
        ].apply(
            toneladas
        ),

        hovertemplate=(
            "<b>%{x}</b>"
            "<br>Toneladas: %{customdata}"
            "<extra></extra>"
        ),
    )

    st.plotly_chart(
        formato_grafico(
            figura_ton_linea
        ),
        use_container_width=True,
    )

    # -----------------------------------------------------
    # COMPOSICION MENSUAL DEL COSTO
    # -----------------------------------------------------

    seccion(
        "🚛 Composición mensual del costo"
    )

    mensual_costos = (
        costos
        .groupby(
            [
                "Periodo_Texto",
                "Tipo_Costo",
            ],
            as_index=False,
        )[
            "Monto"
        ]
        .sum()
    )

    figura_costos = px.bar(
        mensual_costos,
        x="Periodo_Texto",
        y="Monto",
        color="Tipo_Costo",
        barmode="stack",
        title="Traslado y disposición final por mes",
        template="plotly_dark",
        color_discrete_map=COLORES_COSTO,
    )

    st.plotly_chart(
        formato_grafico(
            figura_costos,
            490,
        ),
        use_container_width=True,
    )

    # -----------------------------------------------------
    # TONELADAS MENSUALES
    # -----------------------------------------------------

    seccion(
        "⚖️ Toneladas mensuales por residuo"
    )

    mensual_ton = (
        ton
        .groupby(
            [
                "Periodo_Texto",
                "Residuo",
            ],
            as_index=False,
        )[
            "Toneladas"
        ]
        .sum()
    )

    figura_ton = px.bar(
        mensual_ton,
        x="Periodo_Texto",
        y="Toneladas",
        color="Residuo",
        barmode="stack",
        title="Composición mensual de toneladas gestionadas",
        template="plotly_dark",
        color_discrete_map=COLORES_RESIDUOS,
    )

    st.plotly_chart(
        formato_grafico(
            figura_ton,
            490,
        ),
        use_container_width=True,
    )

    # -----------------------------------------------------
    # DISTRIBUCION PORCENTUAL
    # -----------------------------------------------------

    seccion(
        "🥧 Distribución porcentual del servicio"
    )

    columna_pie_ton, columna_pie_costos = st.columns(
        2
    )

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

    with columna_pie_ton:

        figura_pie_ton = px.pie(
            resumen_pie_ton,
            names="Residuo",
            values="Toneladas",
            hole=.56,
            title="Participación de cada residuo sobre el tonelaje total",
            template="plotly_dark",
            color="Residuo",
            color_discrete_map=COLORES_RESIDUOS,
        )

        figura_pie_ton.update_traces(
            textposition="inside",
            textinfo="percent+label",
        )

        st.plotly_chart(
            formato_grafico(
                figura_pie_ton,
                470,
            ),
            use_container_width=True,
        )

    with columna_pie_costos:

        figura_pie_costos = px.pie(
            resumen_pie_costos,
            names="Residuo",
            values="Monto",
            hole=.56,
            title="Participación de cada residuo en disposición y traslado",
            template="plotly_dark",
            color="Residuo",
            color_discrete_map=COLORES_RESIDUOS,
        )

        figura_pie_costos.update_traces(
            textposition="inside",
            textinfo="percent+label",
        )

        st.plotly_chart(
            formato_grafico(
                figura_pie_costos,
                470,
            ),
            use_container_width=True,
        )

    # -----------------------------------------------------
    # PIE DE PAGINA DEL PANEL
    # -----------------------------------------------------

    st.markdown(
        (
            '<div class="pie-pagina">'

            f"<b>Panel desarrollado por {AUTOR}</b>"
            "<br>"

            f"{CARGO} | SAIVAM"
            "<br>"

            f"Versión {VERSION} | "
            f"Última actualización: "
            f"{nombre_periodo(fecha_maxima)}"

            "</div>"
        ),
        unsafe_allow_html=True,
    )


# =========================================================
# EJECUCION
# =========================================================

aplicar_estilo_general()

if not st.session_state.get(
    "acceso_autorizado",
    False,
):
    mostrar_acceso_restringido()
    st.stop()

agregar_sello_agua_panel()

try:
    mostrar_panel()

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