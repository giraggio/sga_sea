import streamlit as st
import pandas as pd
import re

st.title("🔍 Buscador de Palabras Clave")



# 🔽 Elegir base de datos
opcion = st.selectbox("Selecciona la base de datos que quieres consultar:", ["CAV", "ICC", "MEDIDAS", "Planes de PCyE", "EVI"])

# 📂 URLs de los archivos
archivos = {
    "CAV": "https://raw.githubusercontent.com/giraggio/sga_sea/main/jsonl/cavs_texto_test.jsonl.gz",
    "ICC": "https://raw.githubusercontent.com/giraggio/sga_sea/main/jsonl/pacs_texto_test.jsonl.gz",
    "MEDIDAS": "https://raw.githubusercontent.com/giraggio/sga_sea/main/jsonl/medidas_texto_test.jsonl.gz",
    "Planes de PCyE": 'https://raw.githubusercontent.com/giraggio/sga_sea/main/jsonl/ppce_texto_test.jsonl.gz',
    "EVI": 'https://raw.githubusercontent.com/giraggio/sga_sea/main/jsonl/evi_texto_test.jsonl.gz'
}

# Inicializar estado
if "buscar" not in st.session_state:
    st.session_state["buscar"] = False
if "resultados_df" not in st.session_state:
    st.session_state["resultados_df"] = pd.DataFrame()
if "palabras_clave_input" not in st.session_state:
    st.session_state["palabras_clave_input"] = ""


# 📝 Ingreso de palabras clave
palabras_input = st.text_area(f"Escribe las palabras o frases clave separadas por coma", "sitio prioritario, zona protegida")
palabras_clave = [p.strip().lower() for p in palabras_input.split(",") if p.strip()]

# 🔍 Botón de búsqueda
if st.button("Buscar"):
    st.session_state["buscar"] = True
    st.session_state["palabras_clave_input"] = palabras_input
    # Cargar CSV según la opción seleccionada
    df = pd.read_json(archivos[opcion], lines=True, compression='gzip')

    # Combinar palabras clave en una expresión regular
    palabras_regex = "|".join([f"\\b{p}\\b" for p in palabras_clave])

    # Filtrar filas que contienen alguna palabra clave
    df["texto"] = df["texto"].astype(str).str.lower()
    coincidencias = df[df["texto"].str.contains(palabras_regex, na=False, regex=True)]

    if not coincidencias.empty:
        resultados_df = coincidencias[["texto", "url"]].copy()
        resultados_df["Palabra Clave"] = resultados_df["texto"].apply(
            lambda texto: ", ".join([p for p in palabras_clave if p in texto])
        )
        resultados_df["URL"] = resultados_df["url"].apply(lambda x: f'<a href="{x}" target="_blank">{x}</a>')

        st.session_state["resultados_df"] = resultados_df
    else:
        st.session_state["resultados_df"] = pd.DataFrame()
        st.warning("No se encontraron coincidencias.")

if st.session_state["buscar"] and not st.session_state["resultados_df"].empty:
    resultados_df = st.session_state["resultados_df"]
    st.success(f"Se encontraron coincidencias en {len(resultados_df)} archivos.")

    palabras_unicas = sorted(resultados_df["Palabra Clave"].unique())
    palabra_seleccionada = st.selectbox("Filtrar por Palabra Clave", ["Todas"] + palabras_unicas)

    if palabra_seleccionada != "Todas":
        df_filtrado = resultados_df[resultados_df["Palabra Clave"].str.contains(rf"\b{re.escape(palabra_seleccionada)}\b")]
    else:
        df_filtrado = resultados_df

    st.write(df_filtrado[["Palabra Clave", "URL"]].to_html(escape=False, index=False), unsafe_allow_html=True)

st.markdown(
    """
    #### Preguntas Frecuentes
    """
)

with st.expander("¿Qué es esta plataforma?"):
    st.write(
        """
        Se trata de una ***herramienta interna*** que permite buscar palabras o frases clave en diferentes bases de datos. Indicando en que documento -publicado en el SEA- aparecen las palabras buscadas.

        **NO DEBE SER COMPARTIDA CON EXTERNOS.**

        Estas bases de datos se obtienen a partir de un scraping a los expedientes de proyectos en el SEA.
        Actualmente, se extrae información de **todos EIA publicados en el SEA desde el 2022 (independiente de su estado).**
        La herramienta se encuentra en una fase de prueba y se espera que evolucione con el tiempo.
        """
    )

with st.expander("¿Cómo funciona?"):
    st.write(
        """
        1. **Selecciona la base de datos**: Elige entre Compromisos Ambientales Voluntarios (CAV), Anexos de Participación Ciudadana (ICC), Planes de Medidas (MEDIDAS), Planes de Prevención de Contingencias y Emergencias (Planes de PCyE) O Evaluaciones de Impacto (EVI).
        2. **Escribe las palabras clave**: Ingresa las palabras o frases que deseas buscar, separadas por comas.
        3. **Haz clic en "Buscar"**: Se mostrarán los resultados con las coincidencias encontradas.
        4. **Filtrar por palabra clave**: Puedes filtrar los resultados por palabra clave específica si lo deseas.
        """
    )
