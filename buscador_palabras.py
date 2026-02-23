import datetime
import re

import pandas as pd
import streamlit as st

from src.search import search


st.set_page_config(
    page_title="Buscador de Palabras Clave",
    page_icon=r"https://raw.githubusercontent.com/giraggio/sga_sea/refs/heads/main/SLR-Logo-DIGITAL-Dark%20Green.svg",
    layout="wide",
)
st.title("🔍 Buscador de Palabras Clave")


@st.cache_data
def cargar_proyectos() -> pd.DataFrame:
    df_proyectos = pd.read_excel(r"https://raw.githubusercontent.com/giraggio/sga_sea/main/seia_filtrado.xlsx")
    df_proyectos.rename(columns={"URL Expediente": "proyecto_origen"}, inplace=True)
    return df_proyectos


@st.cache_data
def cargar_fuente(url: str) -> pd.DataFrame:
    return pd.read_json(url, lines=True, compression="gzip")


def transformar_url(url):
    match = re.search(r"id_expediente=(\d+)", str(url))
    if match:
        id_exp = match.group(1)
        return f"https://seia.sea.gob.cl/expediente/ficha/fichaPrincipal.php?modo=normal&id_expediente={id_exp}"
    return None


df_proyectos = cargar_proyectos()

opcion = st.selectbox(
    "Selecciona la base de datos que quieres consultar:",
    ["CAV", "ICC", "MEDIDAS", "Planes de PCyE", "EVI", "ICT"],
)

archivos = {
    "CAV": "https://raw.githubusercontent.com/giraggio/sga_sea/main/jsonl/cavs_texto_test.jsonl.gz",
    "ICC": "https://raw.githubusercontent.com/giraggio/sga_sea/main/jsonl/pacs_texto_test.jsonl.gz",
    "MEDIDAS": "https://raw.githubusercontent.com/giraggio/sga_sea/main/jsonl/medidas_texto_test.jsonl.gz",
    "Planes de PCyE": "https://raw.githubusercontent.com/giraggio/sga_sea/main/jsonl/ppce_texto_test.jsonl.gz",
    "EVI": "https://raw.githubusercontent.com/giraggio/sga_sea/main/jsonl/evi_texto_test.jsonl.gz",
    "ICT": "https://raw.githubusercontent.com/giraggio/sga_sea/main/jsonl/ict_texto_test.jsonl.gz",
}

if "buscar" not in st.session_state:
    st.session_state["buscar"] = False
if "resultados_df" not in st.session_state:
    st.session_state["resultados_df"] = pd.DataFrame()

palabras_input = st.text_area(
    "Escribe palabras, frases o una pregunta en lenguaje natural",
    '"sitio prioritario", zona protegida',
)

modo = st.selectbox(
    "Modo de búsqueda",
    ["clasico", "lexico", "semantico", "hibrido"],
    index=0,
    help="Clásico mantiene coincidencia exacta. Híbrido combina señal léxica y aproximación semántica.",
)

if st.button("Buscar"):
    st.session_state["buscar"] = True
    df = cargar_fuente(archivos[opcion])
    resultados = search(
        query=palabras_input,
        fuente=opcion,
        modo=modo,
        filtros={},
        top_k=200,
        dataset=df,
    )

    if not resultados.empty:
        if "proyecto_origen" in resultados.columns:
            resultados = resultados.merge(df_proyectos, on="proyecto_origen", how="left")
        st.session_state["resultados_df"] = resultados
    else:
        st.session_state["resultados_df"] = pd.DataFrame()
        st.warning("No se encontraron coincidencias.")

if st.session_state["buscar"] and not st.session_state["resultados_df"].empty:
    resultados_df = st.session_state["resultados_df"].copy()
    st.success(f"Se encontraron coincidencias en {len(resultados_df)} archivos.")

    with st.expander("Filtros"):
        df_filtrado = resultados_df.copy()

        if "Región" in df_filtrado.columns:
            regiones = sorted(df_filtrado["Región"].dropna().unique())
            regiones_seleccionadas = st.multiselect("Filtrar por Región", regiones, default=regiones)
            if regiones_seleccionadas:
                df_filtrado = df_filtrado[df_filtrado["Región"].isin(regiones_seleccionadas)]

        if "Estado" in df_filtrado.columns:
            estados = sorted(df_filtrado["Estado"].dropna().unique())
            estados_seleccionados = st.multiselect("Filtrar por Estado", estados, default=estados)
            if estados_seleccionados:
                df_filtrado = df_filtrado[df_filtrado["Estado"].isin(estados_seleccionados)]

        if "Fecha presentación" in df_filtrado.columns:
            fechas = pd.to_datetime(df_filtrado["Fecha presentación"], errors="coerce")
            min_fecha = fechas.min()
            max_fecha = datetime.datetime.now().date()
            if pd.notna(min_fecha):
                fecha_inicio, fecha_fin = st.date_input(
                    "Filtrar por Fecha de Presentación",
                    value=(min_fecha, max_fecha),
                    min_value=min_fecha,
                    max_value=max_fecha,
                )
                df_filtrado = df_filtrado[(fechas >= pd.to_datetime(fecha_inicio)) & (fechas <= pd.to_datetime(fecha_fin))]

    df_filtrado["url_expediente"] = df_filtrado.get("proyecto_origen", pd.Series(index=df_filtrado.index)).apply(transformar_url)

    columnas = [
        c
        for c in [
            "score_total",
            "fuente_score",
            "razon_match",
            "intent_detectada",
            "url",
            "Nombre",
            "Región",
            "Comuna",
            "Estado",
            "Fecha presentación",
            "url_expediente",
        ]
        if c in df_filtrado.columns
    ]

    st.dataframe(
        df_filtrado[columnas],
        column_config={
            "score_total": st.column_config.NumberColumn(format="%.4f"),
            "url": st.column_config.LinkColumn(display_text="URL Archivo"),
            "url_expediente": st.column_config.LinkColumn(display_text="Ver Expediente SEA"),
        },
        hide_index=True,
        use_container_width=True,
    )

with st.expander("¿Qué es esta plataforma?"):
    st.write(
        """
        Se trata de una ***herramienta interna*** que permite buscar palabras, frases o consultas más amplias
        en distintas bases del SEIA.

        **NO DEBE SER COMPARTIDA CON EXTERNOS.**

        Estas bases de datos se obtienen a partir de scraping de expedientes publicados en el SEA.
        """
    )
