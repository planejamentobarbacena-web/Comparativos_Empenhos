import streamlit as st
import altair as alt
import pandas as pd

from auth import login
from components.header import render_header
from data_loader import load_empenhos

# 🔐 Segurança
login()
render_header()

st.set_page_config(
    page_title="📁 Consulta por Credor",
    layout="wide"
)

st.title("📁 Consulta por Credor")

# ==========================
# CARREGAR DADOS
# ==========================
df = load_empenhos()
if df.empty:
    st.warning("Nenhum dado carregado.")
    st.stop()

# 🔹 Limpeza definitiva de Exercício e Entidade
df["anoEmpenho"] = (
    df["anoEmpenho"]
    .astype(str)
    .str.strip()
    .replace(["nan", "None", ""], pd.NA)
)

df["nomeEntidade"] = (
    df["nomeEntidade"]
    .astype(str)
    .str.strip()
    .replace(["nan", "None", ""], pd.NA)
)

df = df.dropna(subset=["anoEmpenho", "nomeEntidade"])

# ==========================
# TRATAMENTO DE VALORES
# ==========================
for col in ["valorEmpenhadoBruto", "valorEmpenhadoAnulado"]:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

df["valorEmpenhadoLiquido"] = (
    df["valorEmpenhadoBruto"] - df["valorEmpenhadoAnulado"]
)

# ==========================
# FILTRO – EXERCÍCIO
# ==========================
anos = sorted(df["anoEmpenho"].dropna().unique())

anos_sel = st.multiselect(
    "📅 Selecione Exercício(s)",
    anos,
    default=anos
)

df = df[df["anoEmpenho"].isin(anos_sel)]

# ==========================
# FILTRO – ENTIDADE
# ==========================
entidades = sorted(df["nomeEntidade"].dropna().unique())

entidades_sel = st.multiselect(
    "🏢 Selecione Entidade(s)",
    entidades,
    default=entidades
)

df = df[df["nomeEntidade"].isin(entidades_sel)]

# ==========================
# FILTRO – CREDOR
# ==========================
credores = ["Todos"] + sorted(df["nomeCredor"].dropna().unique())

credor_sel = st.multiselect(
    "🏦 Selecione Credor(es)",
    credores,
    default=["Todos"]
)

if "Todos" not in credor_sel:
    df = df[df["nomeCredor"].isin(credor_sel)]

# ==========================
# FILTRO – FONTE (numRecurso)
# ==========================
fontes = ["Todos"] + sorted(df["numRecurso"].dropna().unique())

fonte_sel = st.multiselect(
    "💰 Selecione Fonte(s) de Recurso",
    fontes,
    default=["Todos"]
)

if "Todos" not in fonte_sel:
    df = df[df["numRecurso"].isin(fonte_sel)]

# ==========================
# FILTRO – DESCRIÇÃO DA DESPESA
# ==========================
despesas = ["Todos"] + sorted(df["Descrição da despesa"].dropna().unique())

despesa_sel = st.multiselect(
    "📂 Selecione Descrição da Despesa",
    despesas,
    default=["Todos"]
)

if "Todos" not in despesa_sel:
    df = df[df["Descrição da despesa"].isin(despesa_sel)]

# ==========================
# AGRUPAMENTO
# ==========================
comparativo = (
    df
    .groupby(
        ["anoEmpenho", "nomeCredor"],
        as_index=False
    )["valorEmpenhadoLiquido"]
    .sum()
)

if comparativo.empty:
    st.info("Nenhum dado encontrado com os filtros selecionados.")
    st.stop()

# ==========================
# GRÁFICO
# ==========================
graf = (
    alt.Chart(comparativo)
    .mark_bar(size=35)
    .encode(
        x=alt.X("anoEmpenho:N", title="Exercício"),
        xOffset=alt.XOffset("nomeCredor:N"),
        y=alt.Y(
            "valorEmpenhadoLiquido:Q",
            title="Valor Empenhado Líquido (R$)"
        ),
        color=alt.Color("nomeCredor:N", title="Credor"),
        tooltip=[
            "anoEmpenho:N",
            "nomeCredor:N",
            alt.Tooltip("valorEmpenhadoLiquido:Q", format=",.2f")
        ]
    )
    .properties(height=420)
)

st.altair_chart(graf, use_container_width=True)

# ==========================
# TABELA DETALHADA
# ==========================
st.subheader("📋 Detalhamento")

tabela = df[
    [
        "numeroEmpenho",
        "anoEmpenho",
        "nomeEntidade",
        "nomeCredor",
        "numRecurso",
        "Descrição da despesa",
        "valorEmpenhadoBruto",
        "valorEmpenhadoAnulado",
        "valorEmpenhadoLiquido",
    ]
].copy()

# Formatação
for col in [
    "valorEmpenhadoBruto",
    "valorEmpenhadoAnulado",
    "valorEmpenhadoLiquido"
]:
    tabela[col] = tabela[col].apply(
        lambda x: f"R$ {x:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

st.dataframe(tabela, use_container_width=True)

# ==========================
# DOWNLOAD CSV
# ==========================
csv = tabela.to_csv(index=False, sep=";", encoding="utf-8")

st.download_button(
    "⬇️ Baixar CSV – Consulta por Credor",
    csv,
    file_name="consulta_por_credor_filtrada.csv",
    mime="text/csv"
)
