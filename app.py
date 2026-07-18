import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. CONFIGURAÇÃO CENTRALIZADA
# Dica: Se o seu relatório tiver nomes de colunas diferentes, ajuste apenas aqui.
CONFIG = {
    "Diabetes": {"pendencias": ["Sem HbA1c", "Sem avaliação dos pés"]},
    "Gestação": {"pendencias": ["Sem pré-natal", "Sem dTpa"]},
    "Infantil": {"pendencias": ["Sem consulta", "Sem Pentavalente"]},
    "Hipertensão": {"pendencias": ["Sem PA"]},
    "Idoso": {"pendencias": ["Sem Vacina Influenza"]},
    "Câncer": {"pendencias": ["Sem Rast. Colo", "Sem Rast. Mama"]}
}

# 2. LEITURA RESILIENTE
def carregar_dados(uploaded_file):
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    try:
        uploaded_file.seek(0)
        if ext in ['.xls', '.xlsx']:
            return pd.read_excel(uploaded_file)
        else:
            for enc in ['latin-1', 'utf-8', 'cp1252', 'iso-8859-1']:
                try:
                    uploaded_file.seek(0)
                    return pd.read_csv(uploaded_file, encoding=enc, sep=None, engine='python')
                except: continue
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}")
        return None

# 3. NORMALIZAÇÃO E PRIORIZAÇÃO
def processar_df(df, tipo):
    # Renomeia colunas para o padrão interno (ajuste se seus arquivos tiverem nomes diferentes)
    mapeamento = {
        'Nome Completo': 'nome', 'CNS': 'cns', 
        'Equipe Área': 'equipe', 'Microárea': 'micro',
        'Idade': 'idade', 'Acompanhado': 'status'
    }
    df = df.rename(columns=mapeamento)
    
    # Preenche colunas obrigatórias caso não existam
    for col in ['micro', 'idade', 'status']:
        if col not in df.columns: df[col] = 'N/A'
    
    # Calcula 'Total Pendências' baseado na configuração
    cols_pend = CONFIG[tipo]["pendencias"]
    cols_existentes = [c for c in cols_pend if c in df.columns]
    df['Total Pendências'] = df[cols_existentes].eq('N').sum(axis=1) if cols_existentes else 0
    return df

# 4. INTERFACE
st.set_page_config(layout="wide", page_title="Dashboard Saúde 360")
st.title("Dashboard APS - Saúde 360")

tipo_sel = st.sidebar.selectbox("Indicador em análise", list(CONFIG.keys()))
uploaded_file = st.sidebar.file_uploader("Upload de Relatório", type=["csv", "xls", "xlsx"])

if uploaded_file:
    df_raw = carregar_dados(uploaded_file)
    if df_raw is not None:
        df_base = processar_df(df_raw, tipo_sel)
        
        # --- FILTROS SIDEBAR ---
        st.sidebar.markdown("### 🔍 Filtros de Busca Ativa")
        df_filtrado = df_base.copy()
        
        if 'equipe' in df_filtrado.columns:
            sel_eq = st.sidebar.multiselect("Equipe", sorted(df_base['equipe'].astype(str).unique()))
            if sel_eq: df_filtrado = df_filtrado[df_filtrado['equipe'].isin(sel_eq)]
        
        if 'micro' in df_filtrado.columns:
            sel_micro = st.sidebar.multiselect("Microárea", sorted(df_base['micro'].astype(str).unique()))
            if sel_micro: df_filtrado = df_filtrado[df_filtrado['micro'].isin(sel_micro)]
            
        if 'idade' in df_filtrado.columns:
            sel_idade = st.sidebar.multiselect("Faixa Etária", sorted(df_base['idade'].astype(str).unique()))
            if sel_idade: df_filtrado = df_filtrado[df_filtrado['idade'].isin(sel_idade)]

        pend_existentes = [p for p in CONFIG[tipo_sel]["pendencias"] if p in df_base.columns]
        sel_pend = st.sidebar.multiselect("Pendências", pend_existentes)
        if sel_pend:
            df_filtrado = df_filtrado[df_filtrado[sel_pend].eq('N').any(axis=1)]
        
        # --- PAINEL ---
        # 1. Resumo macro (Base completa)
        st.subheader("📊 Visão Geral (Base Completa)")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total de Pacientes", len(df_base))
        c2.metric("Acompanhados", df_base[df_base['status'] == 'S'].shape[0])
        c3.metric("Média de Pendências", f"{df_base['Total Pendências'].mean():.1f}")
        
        st.divider()
        
        # 2. Busca Ativa (Filtrada)
        st.subheader(f"📋 Lista de Busca Ativa ({len(df_filtrado)} pacientes)")
        st.dataframe(df_filtrado.sort_values(by='Total Pendências', ascending=False), use_container_width=True)
        
        csv = df_filtrado.to_csv(index=False).encode('utf-8')
        st.download_button("Baixar Lista Filtrada", csv, "busca_ativa.csv", "text/csv")
else:
    st.info("Por favor, faça o upload de um relatório para iniciar a análise.")
