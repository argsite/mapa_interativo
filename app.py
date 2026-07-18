import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. CONFIGURAÇÃO CENTRALIZADA
CONFIG = {
    "Diabetes": {"colunas": ["HbA1c", "Pés"], "pendencias": ["Sem HbA1c", "Sem avaliação dos pés"]},
    "Gestação": {"colunas": ["Pré-natal", "dTpa"], "pendencias": ["Sem pré-natal", "Sem dTpa"]},
    "Infantil": {"colunas": ["Consulta 1º mês", "Pentavalente"], "pendencias": ["Sem consulta", "Sem Pentavalente"]},
    "Hipertensão": {"colunas": ["PA"], "pendencias": ["Sem PA"]},
    "Idoso": {"colunas": ["Influenza"], "pendencias": ["Sem Vacina Influenza"]},
    "Câncer": {"colunas": ["Rast. Colo", "Rast. Mama"], "pendencias": ["Sem Rast. Colo", "Sem Rast. Mama"]}
}

# 2. FUNÇÃO DE LEITURA RESILIENTE
def carregar_dados(uploaded_file):
    """
    Tenta ler o arquivo garantindo compatibilidade com formatos legados.
    """
    try:
        # 1. Tenta ler como Excel (funciona para .xls e .xlsx)
        # O pandas tenta detectar o formato automaticamente
        return pd.read_excel(uploaded_file)
    except:
        # 2. Se falhar, tenta ler como CSV, testando encodings mais permissivos
        # Adicionamos 'cp1252' e 'latin-1', que resolvem 99% dos casos de byte 0x87
        for enc in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
            try:
                uploaded_file.seek(0) # Volta ao início do arquivo para tentar de novo
                return pd.read_csv(uploaded_file, encoding=enc, sep=None, engine='python')
            except:
                continue
    
    st.error("Não foi possível detectar o formato ou a codificação do arquivo. Tente salvar o arquivo como .xlsx no Excel e enviar novamente.")
    return None

# 3. NORMALIZAÇÃO E MAPEAMENTO
def processar_df(df, tipo):
    mapeamento = {
        'Nome Completo': 'nome', 'CNS': 'cns', 
        'Equipe Área': 'equipe', 'Acompanhado': 'status'
    }
    df = df.rename(columns=mapeamento)
    # Garante colunas de status e equipe
    if 'status' not in df.columns: df['status'] = 'N'
    if 'equipe' not in df.columns: df['equipe'] = 'Indefinida'
    return df

# 4. INTERFACE PRINCIPAL
st.set_page_config(layout="wide", page_title="Dashboard Saúde 360")
st.title("Dashboard APS - Saúde 360")

tipo_selecionado = st.sidebar.selectbox("Selecione o Indicador", list(CONFIG.keys()))
uploaded_file = st.sidebar.file_uploader("Upload de Relatório", type=["csv", "xls", "xlsx"])

if uploaded_file:
    df = carregar_dados(uploaded_file)
    if df is not None:
        df = processar_df(df, tipo_selecionado)
        
        # Dashboard - Métricas
        col1, col2, col3 = st.columns(3)
        col1.metric("Total de Pacientes", len(df))
        col2.metric("Acompanhados", df[df['status'] == 'S'].shape[0])
        col3.metric("Pendentes", df[df['status'] == 'N'].shape[0])
        
        st.divider()
        
        # Visualização Modular
        tab1, tab2 = st.tabs(["Painel Gerencial", "Lista Nominal / Busca Ativa"])
        
        with tab1:
            fig = px.bar(df['equipe'].value_counts().reset_index(), x='index', y='equipe', 
                         title=f"Distribuição de {tipo_selecionado} por Equipe")
            st.plotly_chart(fig, use_container_width=True)
            
        with tab2:
            st.write("Filtre pacientes para busca ativa:")
            status_filtro = st.multiselect("Filtrar status", df['status'].unique())
            df_filtrado = df[df['status'].isin(status_filtro)] if status_filtro else df
            st.dataframe(df_filtrado)
            
            # Botão de exportação
            csv = df_filtrado.to_csv(index=False).encode('utf-8')
            st.download_button("Baixar Lista de Busca Ativa", csv, "busca_ativa.csv", "text/csv")
