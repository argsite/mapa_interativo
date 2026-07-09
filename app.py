import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide", page_title="Mapa de Saúde Territorial")

st.title("📍 Dashboard de Saúde - Rastreamento Territorial")
st.markdown("Faça o upload da sua planilha para visualizar os pacientes no mapa.")

uploaded_file = st.file_uploader(
    "Escolha sua planilha (Excel ou CSV)",
    type=["xlsx", "csv"]
)

if uploaded_file:
    try:
        if uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file)

        st.write("### Dados carregados")
        st.dataframe(df.head())

        cols = df.columns.tolist()
        lat_col = st.selectbox("Selecione a coluna de Latitude", cols, index=None)
        lon_col = st.selectbox("Selecione a coluna de Longitude", cols, index=None)
        area_col = st.selectbox("Selecione a coluna de Microárea (para cores)", cols, index=None)

        if st.button("Gerar Mapa"):
            if lat_col and lon_col:
                mapa = folium.Map(location=[-23.218, -47.520], zoom_start=14)

                cores = ["red", "blue", "green", "purple", "orange", "darkred"]

                for _, row in df.iterrows():
                    try:
                        lat = float(row[lat_col])
                        lon = float(row[lon_col])

                        cor = "gray"
                        if area_col:
                            idx = hash(str(row[area_col])) % len(cores)
                            cor = cores[idx]

                        folium.Marker(
                            location=[lat, lon],
                            popup=f"Paciente: {row.get('Paciente', 'N/A')}",
                            tooltip=f"Microárea: {row.get(area_col, 'N/A') if area_col else 'N/A'}",
                            icon=folium.Icon(color=cor)
                        ).add_to(mapa)
                    except Exception:
                        continue

                st.success("Mapa gerado com sucesso!")
                st_folium(mapa, width=1000, height=600)
            else:
                st.error("Por favor, selecione as colunas de Latitude e Longitude.")
    except Exception as e:
        st.error(f"Erro ao processar o arquivo: {e}")
else:
    st.info("Aguardando upload da planilha...")
