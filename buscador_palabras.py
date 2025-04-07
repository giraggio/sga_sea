import streamlit as st
import pandas as pd

st.title("🔍 Buscador de Palabras Clave")

# 🔽 Elegir base de datos
opcion = st.selectbox("Selecciona la base de datos que quieres consultar:", ["CAV", "ICC", "MEDIDAS"])

# 📂 URLs de los archivos
archivos = {
    "CAV": "https://raw.githubusercontent.com/giraggio/sga_sea/refs/heads/main/cavs_texto.csv",
    "ICC": "https://raw.githubusercontent.com/giraggio/sga_sea/refs/heads/main/pacs_texto.csv",
    "MEDIDAS": "https://raw.githubusercontent.com/giraggio/sga_sea/refs/heads/main/medidas_texto.csv"
}

# 📝 Ingreso de palabras clave
palabras_input = st.text_area(f"Escribe las palabras o frases clave separadas por coma", "sitio prioritario, zona protegida")
palabras_clave = [p.strip().lower() for p in palabras_input.split(",") if p.strip()]

# 🔍 Botón de búsqueda
if st.button("Buscar"):
    # Cargar CSV según la opción seleccionada
    df = pd.read_csv(archivos[opcion])

    # Combinar palabras clave en una expresión regular
    palabras_regex = "|".join([f"\\b{p}\\b" for p in palabras_clave])

    # Filtrar filas que contienen alguna palabra clave
    df["texto"] = df["texto"].astype(str).str.lower()
    coincidencias = df[df["texto"].str.contains(palabras_regex, na=False, regex=True)]

    if not coincidencias.empty:
        st.success(f"Se encontraron coincidencias en {len(coincidencias)} archivos.")
        resultados_df = coincidencias[["texto", "url"]].copy()
        resultados_df["Palabra Clave"] = resultados_df["texto"].apply(
            lambda texto: ", ".join([p for p in palabras_clave if p in texto])
        )

        # Hacer clickeables las URLs
        resultados_df["URL"] = resultados_df["url"].apply(
            lambda x: f'<a href="{x}" target="_blank">{x}</a>'
        )

        # Mostrar la tabla con HTML
        st.write(resultados_df[["Palabra Clave", "URL"]].to_html(escape=False, index=False), unsafe_allow_html=True)
    else:
        st.warning("No se encontraron coincidencias.")
