import io
import re
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Saúde 360 - Painel de Indicadores", layout="wide")

# =========================
# Configuração dos indicadores
# =========================
INDICATORS = {
    "C1": {
        "nome": "Mais acesso",
        "tipo": "percentual",
        "descricao": "Indicador de acesso com foco em cadastro e vínculo.",
        "boas_praticas": [
            {"key": "cadastro_atualizado", "label": "Cadastro atualizado", "peso": 1.0},
            {"key": "vinculo", "label": "Equipe de vínculo informada", "peso": 1.0},
        ],
        "aliases": {
            "cadastro_atualizado": ["cadastro atualizado"],
            "vinculo": ["equipe vínculo", "equipe vinculo"],
        },
    },
    "C2": {
        "nome": "Desenvolvimento infantil",
        "tipo": "pontuacao",
        "descricao": "Boas práticas de cuidado no desenvolvimento infantil.",
        "boas_praticas": [
            {"key": "consulta", "label": "Consulta médica/enfermagem", "peso": 1.0},
            {"key": "peso_altura", "label": "Peso/altura registrados", "peso": 1.0},
            {"key": "visita", "label": "Visita domiciliar", "peso": 1.0},
            {"key": "vacina", "label": "Vacinação em dia", "peso": 1.0},
        ],
        "aliases": {
            "consulta": ["consulta médica/enfermagem", "consulta medica/enfermagem", "consulta"],
            "peso_altura": ["peso/altura", "qtd. registros de peso/altura"],
            "visita": ["visitas domiciliares", "qtd. visitas domiciliares"],
            "vacina": ["vacina", "vacinação", "vacinacao em dia"],
        },
    },
    "C3": {
        "nome": "Gestação e puerpério",
        "tipo": "pontuacao",
        "descricao": "Boas práticas do cuidado na gestação e puerpério.",
        "boas_praticas": [
            {"key": "pre_natal", "label": "Pré-natal em acompanhamento", "peso": 1.0},
            {"key": "consulta", "label": "Consulta médica/enfermagem", "peso": 1.0},
            {"key": "odonto", "label": "Atendimento odontológico", "peso": 1.0},
            {"key": "vacina", "label": "Vacinação/registro oportuno", "peso": 1.0},
        ],
        "aliases": {
            "pre_natal": ["pré-natal", "pre natal", "prenatal"],
            "consulta": ["consulta médica/enfermagem", "consulta"],
            "odonto": ["odonto", "atendimento odontológico", "atendimento odontologico"],
            "vacina": ["vacina", "imunização", "imunizacao"],
        },
    },
    "C4": {
        "nome": "Pessoa com diabetes",
        "tipo": "pontuacao",
        "descricao": "Boas práticas do cuidado com a pessoa com diabetes.",
        "boas_praticas": [
            {"key": "consulta", "label": "Consulta médica/enfermagem", "peso": 1.0},
            {"key": "peso_altura", "label": "Peso/altura registrados", "peso": 1.0},
            {"key": "hemoglobina", "label": "Hemoglobina glicada", "peso": 1.0},
            {"key": "pes", "label": "Avaliação dos pés", "peso": 1.0},
            {"key": "visita", "label": "Visita domiciliar", "peso": 1.0},
            {"key": "acompanhado", "label": "Acompanhado", "peso": 1.0},
        ],
        "aliases": {
            "consulta": ["consulta médica/enfermagem", "consulta medica/enfermagem"],
            "peso_altura": ["qtd. registros de peso/altura", "peso/altura"],
            "hemoglobina": ["hemoglobina glicada", "hb glicada", "hba1c"],
            "pes": ["avaliação dos pés", "avaliacao dos pes", "pés", "pes"],
            "visita": ["qtd. visitas domiciliares", "visitas domiciliares"],
            "acompanhado": ["acompanhado"],
        },
    },
    "C5": {
        "nome": "Pessoa com hipertensão",
        "tipo": "pontuacao",
        "descricao": "Boas práticas do cuidado com a pessoa com hipertensão.",
        "boas_praticas": [
            {"key": "consulta", "label": "Consulta médica/enfermagem", "peso": 1.0},
            {"key": "peso_altura", "label": "Peso/altura registrados", "peso": 1.0},
            {"key": "visita", "label": "Visita domiciliar", "peso": 1.0},
            {"key": "pressao", "label": "Aferição de pressão arterial", "peso": 1.0},
            {"key": "acompanhado", "label": "Acompanhado", "peso": 1.0},
        ],
        "aliases": {
            "consulta": ["consulta médica/enfermagem", "consulta medica/enfermagem"],
            "peso_altura": ["qtd. registros de peso/altura", "peso/altura"],
            "visita": ["qtd. visitas domiciliares", "visitas domiciliares"],
            "pressao": ["aferição de pressão arterial", "afericao de pressao arterial", "pressão arterial"],
            "acompanhado": ["acompanhado"],
        },
    },
    "C6": {
        "nome": "Pessoa idosa",
        "tipo": "pontuacao",
        "descricao": "Boas práticas do cuidado da pessoa idosa.",
        "boas_praticas": [
            {"key": "consulta", "label": "Consulta médica/enfermagem", "peso": 1.0},
            {"key": "peso_altura", "label": "Peso/altura registrados", "peso": 1.0},
            {"key": "visita", "label": "Visita domiciliar", "peso": 1.0},
            {"key": "influenza", "label": "Vacina influenza", "peso": 1.0},
        ],
        "aliases": {
            "consulta": ["consulta médica/enfermagem", "consulta medica/enfermagem"],
            "peso_altura": ["qtd. registros de peso/altura", "peso/altura"],
            "visita": ["qtd. visitas domiciliares", "visitas domiciliares"],
            "influenza": ["vacina influenza", "influenza"],
        },
    },
    "C7": {
        "nome": "Mulher na prevenção do câncer",
        "tipo": "pontuacao",
        "descricao": "Boas práticas do cuidado da mulher na prevenção do câncer.",
        "boas_praticas": [
            {"key": "colo_utero", "label": "Rastreamento do câncer do colo do útero", "peso": 1.0},
            {"key": "hpv", "label": "Vacina HPV entre 9 e 14 anos", "peso": 1.0},
            {"key": "saude_reprodutiva", "label": "Atendimento em saúde reprodutiva", "peso": 1.0},
            {"key": "mama", "label": "Rastreamento do câncer de mama", "peso": 1.0},
            {"key": "acompanhado", "label": "Acompanhado", "peso": 1.0},
        ],
        "aliases": {
            "colo_utero": ["rast. câncer do colo do útero", "rast. cancer do colo do utero", "colo do útero"],
            "hpv": ["vacina hpv entre 9 e 14 anos", "vacina hpv", "hpv"],
            "saude_reprodutiva": ["atend. saúde reprodutiva", "atend. saude reprodutiva", "saúde reprodutiva"],
            "mama": ["rast. câncer de mama", "rast. cancer de mama", "câncer de mama"],
            "acompanhado": ["acompanhado"],
        },
    },
}

COMMON_ALIASES = {
    "nome": ["nome completo", "nome"],
    "cpf": ["cpf"],
    "cns": ["cns"],
    "data_nascimento": ["data nascimento", "data de nascimento"],
    "idade": ["idade"],
    "endereco": ["endereço", "endereco"],
    "equipe_area": ["equipe área", "equipe area"],
    "microarea": ["microárea", "microarea"],
    "equipe_vinculo": ["equipe vínculo", "equipe vinculo"],
    "cadastro_atualizado": ["cadastro atualizado"],
    "data_atualizacao_cadastro": ["data atualização cadastro", "data atualizacao cadastro"],
}

# =========================
# Utilitários
# =========================
def normalize_text(text: str) -> str:
    if text is None:
        return ""
    text = str(text).strip().lower()
    replacements = {
        "á": "a", "à": "a", "â": "a", "ã": "a",
        "é": "e", "ê": "e",
        "í": "i",
        "ó": "o", "ô": "o", "õ": "o",
        "ú": "u",
        "ç": "c",
    }
    for a, b in replacements.items():
        text = text.replace(a, b)
    text = re.sub(r"\s+", " ", text)
    return text


def find_column(columns: List[str], candidates: List[str]) -> str | None:
    norm_cols = {normalize_text(c): c for c in columns}
    for cand in candidates:
        nc = normalize_text(cand)
        if nc in norm_cols:
            return norm_cols[nc]
    for cand in candidates:
        nc = normalize_text(cand)
        for orig in columns:
            if nc in normalize_text(orig):
                return orig
    return None


def bool_from_value(val) -> int:
    if pd.isna(val):
        return 0
    s = normalize_text(val)
    if s in {"s", "sim", "true", "1", "ok", "x"}:
        return 1
    if s in {"n", "nao", "não", "false", "0", "-", ""}:
        return 0
    m = re.search(r"\d+", s)
    if m:
        return 1 if int(m.group()) > 0 else 0
    return 0


def parse_uploaded_file(uploaded_file) -> pd.DataFrame:
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    return pd.read_excel(uploaded_file)


def detect_indicator(df: pd.DataFrame) -> str | None:
    cols = [normalize_text(c) for c in df.columns]
    joined = " | ".join(cols)
    if "pressao arterial" in joined:
        return "C5"
    if "hemoglobina glicada" in joined or "avaliacao dos pes" in joined or "avaliação dos pés" in joined:
        return "C4"
    if "cancer do colo do utero" in joined or "vacina hpv" in joined or "saude reprodutiva" in joined:
        return "C7"
    if "influenza" in joined:
        return "C6"
    return None


def map_columns(df: pd.DataFrame, indicator_code: str) -> Dict[str, str]:
    mapping = {}
    for key, aliases in COMMON_ALIASES.items():
        col = find_column(df.columns.tolist(), aliases)
        if col:
            mapping[key] = col
    indicator = INDICATORS[indicator_code]
    for bp in indicator["boas_praticas"]:
        col = find_column(df.columns.tolist(), indicator["aliases"].get(bp["key"], [bp["label"]]))
        if col:
            mapping[bp["key"]] = col
    return mapping


def standardize_dataset(df: pd.DataFrame, indicator_code: str) -> pd.DataFrame:
    mapping = map_columns(df, indicator_code)
    out = pd.DataFrame()
    base_fields = ["nome", "cpf", "cns", "data_nascimento", "idade", "endereco", "equipe_area", "microarea", "equipe_vinculo", "cadastro_atualizado", "data_atualizacao_cadastro"]
    for field in base_fields:
        out[field] = df[mapping[field]] if field in mapping else np.nan
    indicator = INDICATORS[indicator_code]
    for bp in indicator["boas_praticas"]:
        source = mapping.get(bp["key"])
        out[bp["key"]] = df[source].apply(bool_from_value) if source else 0
    out["indicador"] = indicator_code
    out["indicador_nome"] = indicator["nome"]
    out["idade"] = pd.to_numeric(out["idade"], errors="coerce")
    return out


def compute_scores(df: pd.DataFrame, indicator_code: str) -> pd.DataFrame:
    indicator = INDICATORS[indicator_code]
    bp_keys = [bp["key"] for bp in indicator["boas_praticas"]]
    total = len(bp_keys)
    df = df.copy()
    df["itens_ok"] = df[bp_keys].sum(axis=1)
    df["itens_total"] = total
    df["score_pct"] = np.where(total > 0, (df["itens_ok"] / total) * 100, 0)
    if indicator_code == "C1":
        df["acompanhado"] = np.where((df["cadastro_atualizado"].astype(str).str.upper() == "S") & (df["equipe_vinculo"].notna()), 1, 0)
        df["score_pct"] = df["acompanhado"] * 100
        df["itens_ok"] = df["acompanhado"]
        df["itens_total"] = 1
    return df


def aggregate_team(df: pd.DataFrame) -> pd.DataFrame:
    group_cols = [c for c in ["equipe_area", "equipe_vinculo", "microarea"] if c in df.columns]
    if not group_cols:
        group_cols = ["indicador_nome"]
    agg = df.groupby(group_cols, dropna=False).agg(
        pacientes=("nome", "count"),
        media_score=("score_pct", "mean"),
        acompanhados=("itens_ok", "sum"),
    ).reset_index()
    agg["media_score"] = agg["media_score"].round(1)
    return agg.sort_values("media_score", ascending=False)


def data_quality_report(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in df.columns:
        miss = df[col].isna().sum()
        empty = (df[col].astype(str).str.strip() == "").sum() if df[col].dtype == object else 0
        rows.append({
            "coluna": col,
            "nulos": int(miss),
            "vazios": int(empty),
            "preenchimento_%": round((1 - ((miss + empty) / max(len(df), 1))) * 100, 1),
        })
    return pd.DataFrame(rows).sort_values(["preenchimento_%", "coluna"])


def sample_data(indicator_code: str) -> pd.DataFrame:
    if indicator_code == "C5":
        return pd.DataFrame([
            {"Nome Completo": "Ana Silva", "CPF": "111", "CNS": "7001", "Data Nascimento": "1980-01-01", "Idade": 46, "Endereço": "Rua A", "Equipe Área": "Azul", "Microárea": "1", "Equipe Vínculo": "0001 - Azul", "Cadastro Atualizado": "S", "Data Atualização Cadastro": "2026-07-01", "Consulta Médica/Enfermagem": "S", "Qtd. Registros de peso/altura": 1, "Qtd. Visitas Domiciliares": 1, "Aferição de pressão arterial": "S", "Acompanhado": "S"},
            {"Nome Completo": "João Souza", "CPF": "222", "CNS": "7002", "Data Nascimento": "1970-01-01", "Idade": 56, "Endereço": "Rua B", "Equipe Área": "Azul", "Microárea": "2", "Equipe Vínculo": "0001 - Azul", "Cadastro Atualizado": "N", "Data Atualização Cadastro": "2025-01-10", "Consulta Médica/Enfermagem": "N", "Qtd. Registros de peso/altura": 0, "Qtd. Visitas Domiciliares": 0, "Aferição de pressão arterial": "N", "Acompanhado": "N"},
        ])
    if indicator_code == "C7":
        return pd.DataFrame([
            {"Nome Completo": "Maria Costa", "CPF": "333", "CNS": "7003", "Data Nascimento": "1975-04-29", "Idade": 51, "Rast. Câncer do Colo do Útero": "S", "Vacina HPV entre 9 e 14 anos": "-", "Atend. Saúde Reprodutiva": "S", "Rast. Câncer de mama": "S", "Acompanhado": "S", "Endereço": "Rua C", "Equipe Área": "Ouro", "Microárea": "5", "Equipe Vínculo": "0002 - Ouro", "Cadastro Atualizado": "S", "Data Atualização Cadastro": "2026-05-26"},
            {"Nome Completo": "Paula Lima", "CPF": "444", "CNS": "7004", "Data Nascimento": "1987-09-03", "Idade": 38, "Rast. Câncer do Colo do Útero": "N", "Vacina HPV entre 9 e 14 anos": "-", "Atend. Saúde Reprodutiva": "S", "Rast. Câncer de mama": "-", "Acompanhado": "N", "Endereço": "Rua D", "Equipe Área": "Ouro", "Microárea": "6", "Equipe Vínculo": "0002 - Ouro", "Cadastro Atualizado": "S", "Data Atualização Cadastro": "2026-07-17"},
        ])
    cols = {
        "Nome Completo": ["Paciente A", "Paciente B"],
        "CPF": ["123", "456"],
        "CNS": ["7000", "7001"],
        "Data Nascimento": ["1990-01-01", "1995-01-01"],
        "Idade": [36, 31],
        "Endereço": ["Rua X", "Rua Y"],
        "Equipe Área": ["Equipe 1", "Equipe 1"],
        "Microárea": ["1", "2"],
        "Equipe Vínculo": ["0001 - Equipe 1", "0001 - Equipe 1"],
        "Cadastro Atualizado": ["S", "S"],
        "Data Atualização Cadastro": ["2026-06-01", "2026-06-10"],
    }
    for bp in INDICATORS[indicator_code]["boas_praticas"]:
        label = bp["label"]
        cols[label] = ["S", "N"]
    return pd.DataFrame(cols)


def to_excel_bytes(df_dict: Dict[str, pd.DataFrame]) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, dfx in df_dict.items():
            dfx.to_excel(writer, index=False, sheet_name=sheet_name[:31])
    return output.getvalue()


# =========================
# Interface
# =========================
st.title("Saúde 360 - Painel Integrado dos 7 Indicadores")
st.caption("Base modular para monitoramento nominal, desempenho por equipe e qualidade dos dados.")

with st.sidebar:
    st.header("Configuração")
    modo_demo = st.toggle("Usar dados de demonstração", value=True)
    indicador_manual = st.selectbox(
        "Indicador principal",
        options=list(INDICATORS.keys()),
        format_func=lambda x: f"{x} - {INDICATORS[x]['nome']}",
        index=4,
    )
    uploaded_files = st.file_uploader(
        "Envie uma ou mais planilhas (.xls, .xlsx, .csv)",
        type=["xls", "xlsx", "csv"],
        accept_multiple_files=True,
    )

st.markdown("### Visão geral")
cols = st.columns(4)
cols[0].metric("Indicadores", len(INDICATORS))
cols[1].metric("Tipo principal", "Pontuação")
cols[2].metric("Upload múltiplo", "Sim")
cols[3].metric("Exportação", "CSV / XLSX")

# Carregamento
frames = []
source_info = []
if uploaded_files:
    for up in uploaded_files:
        try:
            raw = parse_uploaded_file(up)
            detected = detect_indicator(raw) or indicador_manual
            std = standardize_dataset(raw, detected)
            calc = compute_scores(std, detected)
            frames.append(calc)
            source_info.append({"arquivo": up.name, "indicador": detected, "linhas": len(calc)})
        except Exception as e:
            st.error(f"Erro ao ler {up.name}: {e}")

if not frames and modo_demo:
    for code in INDICATORS:
        raw = sample_data(code)
        std = standardize_dataset(raw, code)
        calc = compute_scores(std, code)
        frames.append(calc)
        source_info.append({"arquivo": f"demo_{code}.xlsx", "indicador": code, "linhas": len(calc)})

if not frames:
    st.info("Envie pelo menos uma planilha ou habilite os dados de demonstração.")
    st.stop()

master = pd.concat(frames, ignore_index=True)
source_df = pd.DataFrame(source_info)

# Filtros
st.markdown("## Filtros")
fc1, fc2, fc3 = st.columns(3)
inds = fc1.multiselect("Indicadores", options=sorted(master["indicador"].dropna().unique()), default=sorted(master["indicador"].dropna().unique()))
equipes = fc2.multiselect("Equipe área", options=sorted(master["equipe_area"].dropna().astype(str).unique()), default=sorted(master["equipe_area"].dropna().astype(str).unique())[:10])
score_min = fc3.slider("Score mínimo", 0, 100, 0)

filtered = master[master["indicador"].isin(inds)].copy()
if equipes:
    filtered = filtered[filtered["equipe_area"].astype(str).isin(equipes)]
filtered = filtered[filtered["score_pct"] >= score_min]

# KPIs
st.markdown("## Painel executivo")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Pacientes", int(len(filtered)))
k2.metric("Média geral", f"{filtered['score_pct'].mean():.1f}%")
k3.metric("Equipes", int(filtered['equipe_area'].nunique()))
k4.metric("Arquivos", int(len(source_df)))

# Abas
aba1, aba2, aba3, aba4, aba5, aba6 = st.tabs([
    "Resumo",
    "Por indicador",
    "Por equipe",
    "Nominal",
    "Qualidade dos dados",
    "Exportação",
])

with aba1:
    st.dataframe(source_df, use_container_width=True)
    resumo = filtered.groupby(["indicador", "indicador_nome"], dropna=False).agg(
        pacientes=("nome", "count"),
        media_score=("score_pct", "mean"),
    ).reset_index()
    resumo["media_score"] = resumo["media_score"].round(1)
    st.dataframe(resumo, use_container_width=True)
    st.bar_chart(resumo.set_index("indicador_nome")["media_score"])

with aba2:
    indicador_sel = st.selectbox(
        "Selecione o indicador",
        options=sorted(filtered["indicador"].unique()),
        format_func=lambda x: f"{x} - {INDICATORS[x]['nome']}",
        key="indicador_tab",
    )
    sub = filtered[filtered["indicador"] == indicador_sel].copy()
    st.write(INDICATORS[indicador_sel]["descricao"])
    bps = [bp["key"] for bp in INDICATORS[indicador_sel]["boas_praticas"]]
    bp_labels = {bp["key"]: bp["label"] for bp in INDICATORS[indicador_sel]["boas_praticas"]}
    bp_df = pd.DataFrame({
        "boa_pratica": [bp_labels[k] for k in bps],
        "adesao_%": [round(sub[k].mean() * 100, 1) if len(sub) else 0 for k in bps],
    })
    st.dataframe(bp_df, use_container_width=True)
    st.bar_chart(bp_df.set_index("boa_pratica")["adesao_%"])

with aba3:
    equipe_agg = aggregate_team(filtered)
    st.dataframe(equipe_agg, use_container_width=True)
    cols_chart = [c for c in ["equipe_area", "equipe_vinculo"] if c in equipe_agg.columns]
    idx = cols_chart[0] if cols_chart else equipe_agg.columns[0]
    st.bar_chart(equipe_agg.set_index(idx)["media_score"])

with aba4:
    view_cols = [c for c in ["indicador", "indicador_nome", "nome", "idade", "equipe_area", "microarea", "equipe_vinculo", "score_pct", "itens_ok", "itens_total"] if c in filtered.columns]
    st.dataframe(filtered[view_cols].sort_values(["indicador", "score_pct"], ascending=[True, False]), use_container_width=True)
    csv_bytes = filtered.to_csv(index=False).encode("utf-8-sig")
    st.download_button("Baixar nominal filtrado (CSV)", data=csv_bytes, file_name="saude360_nominal_filtrado.csv", mime="text/csv")

with aba5:
    dq = data_quality_report(filtered)
    st.dataframe(dq, use_container_width=True)
    st.bar_chart(dq.set_index("coluna")["preenchimento_%"])

with aba6:
    st.markdown("### Exportações")
    resumo_export = filtered.groupby(["indicador", "indicador_nome"], dropna=False).agg(
        pacientes=("nome", "count"), media_score=("score_pct", "mean")
    ).reset_index()
    equipe_export = aggregate_team(filtered)
    xlsx = to_excel_bytes({
        "base_filtrada": filtered,
        "resumo_indicador": resumo_export,
        "resumo_equipe": equipe_export,
        "fontes": source_df,
    })
    st.download_button(
        "Baixar pacote Excel",
        data=xlsx,
        file_name="saude360_exportacoes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.markdown("### Modelo de planilha")
    template_indicator = st.selectbox(
        "Gerar modelo para",
        options=list(INDICATORS.keys()),
        format_func=lambda x: f"{x} - {INDICATORS[x]['nome']}",
        key="template_indicator",
    )
    template_df = sample_data(template_indicator)
    template_csv = template_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Baixar modelo CSV",
        data=template_csv,
        file_name=f"modelo_{template_indicator.lower()}.csv",
        mime="text/csv",
    )

st.markdown("---")
st.markdown(
    "**Observação técnica:** esta base usa parser flexível por nomes de colunas e foi desenhada para ser refinada com os relatórios reais da secretaria."
)
