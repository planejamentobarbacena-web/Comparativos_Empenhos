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

# ==========================
# TRATAMENTO DE VALORES
# ==========================
for col in [
    "valorEmpenhadoBruto",
    "valorEmpenhadoAnulado",
    "saldoBaixado"
]:
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
    "📅 Exercício",
    anos,
    default=anos
)

df = df[df["anoEmpenho"].isin(anos_sel)]

# ==========================
# FILTRO – ENTIDADE
# ==========================
entidades = sorted(df["nomeEntidade"].dropna().unique())

entidades_sel = st.multiselect(
    "🏢 Entidade",
    entidades,
    default=entidades
)

df = df[df["nomeEntidade"].isin(entidades_sel)]

# ==========================
# FILTRO – CREDOR
# ==========================
credores = ["Todos"] + sorted(df["nomeCredor"].dropna().unique())

credor_sel = st.multiselect(
    "👤 Credor",
    credores,
    default=["Todos"]
)

if "Todos" not in credor_sel:
    df = df[df["nomeCredor"].isin(credor_sel)]

# ==========================
# FILTRO – DESCRIÇÃO DA DESPESA
# ==========================
despesas = ["Todos"] + sorted(df["Descrição da despesa"].dropna().unique())

despesa_sel = st.multiselect(
    "📂 Descrição da Despesa",
    despesas,
    default=["Todos"]
)

if "Todos" not in despesa_sel:
    df = df[df["Descrição da despesa"].isin(despesa_sel)]

# ==========================
# AGRUPAMENTO PARA GRÁFICO
# ==========================
comparativo = (
    df
    .groupby("anoEmpenho", as_index=False)
    .agg({
        "valorEmpenhadoLiquido": "sum",
        "saldoBaixado": "sum"
    })
)

comparativo_melt = comparativo.melt(
    id_vars="anoEmpenho",
    value_vars=[
        "valorEmpenhadoLiquido",
        "saldoBaixado"
    ],
    var_name="Tipo",
    value_name="Valor"
)

comparativo_melt["Tipo"] = comparativo_melt["Tipo"].map({
    "valorEmpenhadoLiquido": "Empenhado Líquido",
    "saldoBaixado": "Saldo Baixado"
})

# ==========================
# GRÁFICO (DUAS BARRAS)
# ==========================
graf = (
    alt.Chart(comparativo_melt)
    .mark_bar(size=40)
    .encode(
        x=alt.X("anoEmpenho:N", title="Exercício"),
        xOffset=alt.XOffset("Tipo:N"),
        y=alt.Y("Valor:Q", title="Valor (R$)"),
        color=alt.Color("Tipo:N", title="Tipo"),
        tooltip=[
            "anoEmpenho:N",
            "Tipo:N",
            alt.Tooltip("Valor:Q", format=",.2f")
        ]
    )
    .properties(height=420)
)

st.altair_chart(graf, use_container_width=True)

# ==========================
# TABELA DETALHADA
# ==========================
tabela = df[[
    "numeroEmpenho",
    "anoEmpenho",
    "nomeEntidade",
    "nomeCredor",
    "Descrição da despesa",
    "valorEmpenhadoBruto",
    "valorEmpenhadoAnulado",
    "valorEmpenhadoLiquido",
    "saldoBaixado"
]].copy()

for col in [
    "valorEmpenhadoBruto",
    "valorEmpenhadoAnulado",
    "valorEmpenhadoLiquido",
    "saldoBaixado"
]:
    tabela[col] = tabela[col].apply(
        lambda x: f"R$ {x:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

st.subheader("📋 Detalhamento dos Empenhos")
st.dataframe(tabela, use_container_width=True)

# ==========================
# DOWNLOAD CSV
# ==========================
csv = df.to_csv(
    index=False,
    sep=";",
    decimal=",",
    encoding="utf-8-sig"
)

st.download_button(
    "⬇️ Baixar CSV – Consulta por Credor",
    csv,
    file_name="consulta_por_credor.csv",
    mime="text/csv"
)
