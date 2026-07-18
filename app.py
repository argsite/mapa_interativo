import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. CONFIGURAÇÃO CENTRALIZADA (Adicione novos indicadores aqui)
# pendencias: colunas que contêm 'N' ou 'Não' quando o paciente precisa de atenção
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
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    try:
        if ext in ['.xls', '.xlsx']:
            return pd.read_excel(uploaded_file)
        else:
            for enc in ['latin-1', 'utf-8', 'cp1252']:
                try:
                    uploaded_file.seek(0)
                    return pd.read_csv(uploaded_file, encoding=enc, sep=None, engine='python')
                except: continue
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}")
        return None

# 3. NORMALIZAÇÃO E PRIORIZAÇÃO
def processar_df(df, tipo):
    mapeamento = {
        'Nome Completo': 'nome', 'CNS': 'cns', 
        'Equipe Área': 'equipe', 'Acompanhado': 'status'
    }
    df = df.rename(columns=mapeamento)
    
    # Cria coluna de "Prioridade" (contagem de pendências marcadas como 'N')
    pendencias = CONFIG[tipo]["pendencias"]
    if all(col in df.columns for col in pendencias):
        df['Total Pendências'] = df[pendencias].eq('N').sum(axis=1)
    else:
        df['Total Pendências'] = 0
        
    return df

# 4. INTERFACE STREAMLIT
st.set_page_config(layout="wide", page_title="Dashboard Saúde 360")
st.title("Dashboard APS - Saúde 360")

tipo_selecionado = st.sidebar.selectbox("Selecione o Indicador", list(CONFIG.keys()))
uploaded_file = st.sidebar.file_uploader("Upload de Relatório", type=["csv", "xls", "xlsx"])

if uploaded_file:
    df_raw = carregar_dados(uploaded_file)
    if df_raw is not None:
        df = processar_df(df_raw, tipo_selecionado)
        
        # --- FILTROS SIDEBAR ---
        st.sidebar.markdown("### 🔍 Filtros de Busca Ativa")
        
        # Filtro de Equipe
        equipes = sorted(df['equipe'].unique().astype(str))
        equipes_sel = st.sidebar.multiselect("Equipe", equipes)
        if equipes_sel: df = df[df['equipe'].isin(equipes_sel)]
            
        # Filtro de Pendências
        pendencias_sel = st.sidebar.multiselect("Pendências (Busca Ativa)", CONFIG[tipo_selecionado]["pendencias"])
        if pendencias_sel:
            df = df[df[pendencias_sel].eq('N').any(axis=1)]
        
        # --- DASHBOARD REATIVO ---
        st.info(f"Visualizando {len(df)} pacientes após os filtros.")
        
        # Cards
        c1, c2, c3 = st.columns(3)
        c1.metric("Total de Pacientes", len(df))
        c2.metric("Acompanhados", df[df['status'] == 'S'].shape[0])
        c3.metric("Média de Pendências", f"{df['Total Pendências'].mean():.1f}")
        
        # Gráficos e Lista
        tab1, tab2 = st.tabs(["📊 Painel de Desempenho", "📋 Lista Nominal"])
        
        with tab1:
            fig = px.bar(df['equipe'].value_counts().reset_index(), x='index', y='equipe', 
                         title="Distribuição por Equipe")
            st.plotly_chart(fig, use_container_width=True)
            
        with tab2:
            # Lista ordenada por prioridade (quem tem mais pendências primeiro)
            df_lista = df.sort_values(by='Total Pendências', ascending=False)
            st.dataframe(df_lista, use_container_width=True)
            
            # Download
            csv = df_lista.to_csv(index=False).encode('utf-8')
            st.download_button("Baixar Lista de Busca Ativa", csv, "lista_busca_ativa.csv", "text/csv")
