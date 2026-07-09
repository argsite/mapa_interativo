
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Dashboard APS - Hipertensão e Diabetes")
st.title("Dashboard APS - Hipertensão e Diabetes")
st.caption("Painel para acompanhamento territorial, busca ativa e monitoramento por equipe e microárea.")


def carregar_planilha(uploaded_file):
    if uploaded_file.name.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)
    return pd.read_csv(uploaded_file)


def normalizar_colunas(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def faixa_etaria(idade):
    try:
        idade = int(idade)
    except:
        return "Ignorado"
    if idade < 18:
        return "0-17"
    if idade < 40:
        return "18-39"
    if idade < 60:
        return "40-59"
    if idade < 80:
        return "60-79"
    return "80+"


def multiselect_com_todos(label, opcoes):
    opcoes = [o for o in opcoes if pd.notna(o)]
    opcoes = sorted(pd.Series(opcoes).astype(str).unique().tolist())
    return st.sidebar.multiselect(label, opcoes)


def aplicar_filtros_base(df, col_equipe, col_micro, col_idade, col_prioridade):
    equipes = multiselect_com_todos("Equipe Área", df[col_equipe].dropna().tolist()) if col_equipe in df.columns else []
    micros = multiselect_com_todos("Microárea", df[col_micro].dropna().tolist()) if col_micro in df.columns else []
    faixas = st.sidebar.multiselect("Faixa etária", ["0-17", "18-39", "40-59", "60-79", "80+"])
    prioridades = st.sidebar.multiselect("Prioridade", ["Alta", "Média", "Baixa"])

    filtrado = df.copy()
    if equipes:
        filtrado = filtrado[filtrado[col_equipe].astype(str).isin(equipes)]
    if micros:
        filtrado = filtrado[filtrado[col_micro].astype(str).isin(micros)]
    if faixas and "Faixa Etária" in filtrado.columns:
        filtrado = filtrado[filtrado["Faixa Etária"].isin(faixas)]
    if prioridades and col_prioridade in filtrado.columns:
        filtrado = filtrado[filtrado[col_prioridade].isin(prioridades)]
    return filtrado


def exibir_metricas(cards):
    cols = st.columns(len(cards))
    for col, (titulo, valor) in zip(cols, cards):
        col.metric(titulo, valor)


def grafico_barras(df, x, y, titulo, cor=None):
    if df.empty:
        st.info("Sem dados para exibir neste gráfico.")
        return
    fig = px.bar(df, x=x, y=y, title=titulo, color=cor)
    fig.update_layout(margin=dict(l=10, r=10, t=60, b=10), xaxis_title=None, yaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)


def preparar_diabetes(df):
    df = normalizar_colunas(df)
    mapa = {
        "nome": "Nome Completo",
        "idade": "Idade",
        "endereco": "Endereço",
        "equipe": "Equipe Área",
        "micro": "Microárea",
        "cadastro": "Cadastro Atualizado",
        "data_cadastro": "Data Atualização Cadastro",
        "consulta": "Consulta Médica/Enfermagem",
        "pa": "Aferição de PA",
        "peso": "Qtd. Registros de peso/altura",
        "visitas": "Qtd. Visitas Domiciliares",
        "hba1c": "Hemoglobina Glicada",
        "pes": "Avaliação dos pés",
        "acomp": "Acompanhado",
    }
    for chave in ["cadastro", "consulta", "pa", "hba1c", "pes", "acomp"]:
        if mapa[chave] in df.columns:
            df[mapa[chave]] = df[mapa[chave]].astype(str).str.upper().str.strip()
    if mapa["idade"] in df.columns:
        df["Faixa Etária"] = df[mapa["idade"]].apply(faixa_etaria)
    df["Sem consulta"] = df[mapa["consulta"]] == "N"
    df["Sem PA"] = df[mapa["pa"]] == "N"
    df["Sem HbA1c"] = df[mapa["hba1c"]] == "N"
    df["Sem avaliação dos pés"] = df[mapa["pes"]] == "N"
    df["Não acompanhado"] = df[mapa["acomp"]] == "N"
    df["Cadastro desatualizado"] = df[mapa["cadastro"]] == "N"
    df["Sem visita"] = pd.to_numeric(df[mapa["visitas"]], errors="coerce").fillna(0) == 0
    df["Pontuação Prioridade"] = (
        df["Sem consulta"].astype(int)
        + df["Sem PA"].astype(int)
        + df["Sem HbA1c"].astype(int)
        + df["Sem avaliação dos pés"].astype(int)
        + df["Não acompanhado"].astype(int)
    )
    df["Prioridade"] = df["Pontuação Prioridade"].map(lambda x: "Alta" if x >= 3 else ("Média" if x == 2 else "Baixa"))
    return df, mapa


def preparar_hipertensao(df):
    df = normalizar_colunas(df)
    mapa = {
        "nome": "Nome Completo",
        "idade": "Idade",
        "endereco": "Endereço",
        "equipe": "Equipe Área",
        "micro": "Microárea",
        "cadastro": "Cadastro Atualizado",
        "data_cadastro": "Data Atualização Cadastro",
        "consulta": "Consulta Médica/Enfermagem",
        "peso": "Qtd. Registros de peso/altura",
        "visitas": "Qtd. Visitas Domiciliares",
        "pa": "Aferição de pressão arterial",
        "acomp": "Acompanhado",
    }
    for chave in ["cadastro", "consulta", "pa", "acomp"]:
        if mapa[chave] in df.columns:
            df[mapa[chave]] = df[mapa[chave]].astype(str).str.upper().str.strip()
    if mapa["idade"] in df.columns:
        df["Faixa Etária"] = df[mapa["idade"]].apply(faixa_etaria)
    df["Sem consulta"] = df[mapa["consulta"]] == "N"
    df["Sem PA"] = df[mapa["pa"]] == "N"
    df["Não acompanhado"] = df[mapa["acomp"]] == "N"
    df["Cadastro desatualizado"] = df[mapa["cadastro"]] == "N"
    df["Sem visita"] = pd.to_numeric(df[mapa["visitas"]], errors="coerce").fillna(0) == 0
    df["Pontuação Prioridade"] = (
        df["Sem consulta"].astype(int)
        + df["Sem PA"].astype(int)
        + df["Não acompanhado"].astype(int)
        + df["Cadastro desatualizado"].astype(int)
        + df["Sem visita"].astype(int)
    )
    df["Prioridade"] = df["Pontuação Prioridade"].map(lambda x: "Alta" if x >= 3 else ("Média" if x == 2 else "Baixa"))
    return df, mapa


def render_diabetes(df):
    df, m = preparar_diabetes(df)
    st.sidebar.header("Filtros")
    filtrado = aplicar_filtros_base(df, m["equipe"], m["micro"], m["idade"], "Prioridade")
    total = len(filtrado)
    pct = lambda col: f"{((filtrado[col] == 'S').mean() * 100 if total else 0):.1f}%"
    pct_visita = f"{(((pd.to_numeric(filtrado[m['visitas']], errors='coerce').fillna(0) > 0).mean() * 100) if total else 0):.1f}%"
    exibir_metricas([
        ("Total", total),
        ("Consulta", pct(m["consulta"])),
        ("PA", pct(m["pa"])),
        ("HbA1c", pct(m["hba1c"])),
        ("Pés", pct(m["pes"])),
        ("Acompanhados", pct(m["acomp"])),
        ("Com visita", pct_visita),
    ])
    c1, c2 = st.columns(2)
    with c1:
        g1 = filtrado.groupby(m["micro"], dropna=False)["Não acompanhado"].sum().reset_index().sort_values("Não acompanhado", ascending=False)
        grafico_barras(g1, m["micro"], "Não acompanhado", "Não acompanhados por microárea")
    with c2:
        pend = pd.DataFrame({
            "Indicador": ["Sem consulta", "Sem PA", "Sem HbA1c", "Sem avaliação dos pés"],
            "Quantidade": [
                int(filtrado["Sem consulta"].sum()),
                int(filtrado["Sem PA"].sum()),
                int(filtrado["Sem HbA1c"].sum()),
                int(filtrado["Sem avaliação dos pés"].sum()),
            ],
        })
        grafico_barras(pend, "Indicador", "Quantidade", "Pendências do cuidado - Diabetes")
    st.subheader("Lista nominal para busca ativa")
    cols = [m["nome"], m["idade"], m["endereco"], m["equipe"], m["micro"], m["consulta"], m["pa"], m["hba1c"], m["pes"], m["visitas"], m["acomp"], "Prioridade"]
    st.dataframe(filtrado[[c for c in cols if c in filtrado.columns]], use_container_width=True)


def render_hipertensao(df):
    df, m = preparar_hipertensao(df)
    st.sidebar.header("Filtros")
    filtrado = aplicar_filtros_base(df, m["equipe"], m["micro"], m["idade"], "Prioridade")
    total = len(filtrado)
    pct = lambda col: f"{((filtrado[col] == 'S').mean() * 100 if total else 0):.1f}%"
    pct_visita = f"{(((pd.to_numeric(filtrado[m['visitas']], errors='coerce').fillna(0) > 0).mean() * 100) if total else 0):.1f}%"
    exibir_metricas([
        ("Total", total),
        ("Consulta", pct(m["consulta"])),
        ("PA aferida", pct(m["pa"])),
        ("Com visita", pct_visita),
        ("Cadastro atualizado", pct(m["cadastro"])),
        ("Acompanhados", pct(m["acomp"])),
    ])
    c1, c2 = st.columns(2)
    with c1:
        g1 = filtrado.groupby(m["micro"], dropna=False)["Sem PA"].sum().reset_index().sort_values("Sem PA", ascending=False)
        grafico_barras(g1, m["micro"], "Sem PA", "Sem aferição de PA por microárea")
    with c2:
        pend = pd.DataFrame({
            "Indicador": ["Sem consulta", "Sem PA", "Sem visita", "Não acompanhado", "Cadastro desatualizado"],
            "Quantidade": [
                int(filtrado["Sem consulta"].sum()),
                int(filtrado["Sem PA"].sum()),
                int(filtrado["Sem visita"].sum()),
                int(filtrado["Não acompanhado"].sum()),
                int(filtrado["Cadastro desatualizado"].sum()),
            ],
        })
        grafico_barras(pend, "Indicador", "Quantidade", "Pendências do cuidado - Hipertensão")
    st.subheader("Lista nominal para busca ativa")
    cols = [m["nome"], m["idade"], m["endereco"], m["equipe"], m["micro"], m["consulta"], m["pa"], m["visitas"], m["acomp"], "Prioridade"]
    st.dataframe(filtrado[[c for c in cols if c in filtrado.columns]], use_container_width=True)


secao = st.sidebar.radio("Linha de cuidado", ["Hipertensão", "Diabetes"])
arquivo = st.file_uploader("Envie a planilha correspondente", type=["xlsx", "xls", "csv"])

with st.expander("Como usar"):
    st.markdown("""
    - Escolha a linha de cuidado na barra lateral.
    - Envie a planilha correspondente daquela seção.
    - Use os filtros por equipe, microárea, faixa etária e prioridade.
    - A tabela nominal ajuda na organização da busca ativa.
    """)

if arquivo is None:
    st.info("Aguardando upload da planilha de hipertensão ou diabetes.")
else:
    try:
        df = carregar_planilha(arquivo)
        if secao == "Hipertensão":
            render_hipertensao(df)
        else:
            render_diabetes(df)
    except Exception as e:
        st.error(f"Não foi possível processar a planilha: {e}")
