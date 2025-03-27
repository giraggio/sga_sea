import streamlit as st
import pandas as pd
from io import StringIO

st.title("🔍 Buscador de Palabras Clave en CAV")

# Subir archivo CSV
archivo = 'https://raw.githubusercontent.com/giraggio/sga_sea/refs/heads/main/cavs_texto.csv'

if archivo is not None:
    df = pd.read_csv(archivo)

    # Ingresar palabras clave
    palabras_input = st.text_area("Escribe las palabras o frases clave separadas por coma", "sitio prioritario, zona protegida")
    palabras_clave = [p.strip().lower() for p in palabras_input.split(",") if p.strip()]

    # Botón de búsqueda
    if st.button("Buscar"):
        resultados = []

        for i, row in df.iterrows():
            texto = str(row["texto"]).lower()
            for palabra in palabras_clave:
                if palabra in texto:
                    resultados.append({
                        "Palabra Clave": palabra,
                        "URL": row["url"]
                    })
                    break  # Solo muestra una coincidencia por fila

        # if resultados:
        #     st.success(f"Se encontraron coincidencias en {len(resultados)} archivos.")
        #     st.dataframe(pd.DataFrame(resultados))
        # else:
        #     st.warning("No se encontraron coincidencias.")
        if resultados:
            st.success(f"Se encontraron coincidencias en {len(resultados)} archivos.")
    
            resultados_df = pd.DataFrame(resultados)

    # Convertir la columna URL a un enlace HTML clickeable
            resultados_df["URL"] = resultados_df["URL"].apply(
            lambda x: f'<a href="{x}" target="_blank">{x}</a>'
        )

    # Mostrar la tabla con HTML habilitado
            st.write(resultados_df.to_html(escape=False, index=False), unsafe_allow_html=True)

        else:
            st.warning("No se encontraron coincidencias.")

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 
