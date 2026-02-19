import streamlit as st
import altair as alt
import pandas as pd

from auth import login
from components.header import render_header
from data_loader import load_empenhos  

# ==================================
# CONFIGURAÇÃO DA PÁGINA
# ==================================
st.set_page_config(
    page_title="Painel de Empenhos",
    page_icon="📊",
    layout="wide"
)

login()
render_header()

st.title("📊 Painel de Empenhos – Visão Geral")

# ==================================
# CARREGAR DADOS
# ==================================
df = load_empenhos()

if df.empty:
    st.warning("Nenhum dado carregado.")
    st.stop()

# ==================================
# TRATAMENTO DOS DADOS
# ==================================
df["anoEmpenho"] = (
    df["anoEmpenho"]
    .astype(str)
    .str.replace(".0", "", regex=False)
    .str.strip()
)

df["nomeEntidade"] = (
    df["nomeEntidade"]
    .fillna("")
    .astype(str)
    .str.strip()
)

df = df[(df["anoEmpenho"] != "") & (df["anoEmpenho"] != "nan")]
df = df[df["nomeEntidade"] != ""]

for col in ["valorEmpenhadoBruto", "valorEmpenhadoAnulado", "saldoBaixado"]:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# ==================================
# FILTROS
# ==================================
st.divider()

anos = sorted(df["anoEmpenho"].unique())
entidades = sorted(df["nomeEntidade"].unique())

f1, f2 = st.columns(2)

with f1:
    ano_sel = st.multiselect("📅 Exercício", anos, default=anos)

with f2:
    entidade_sel = st.multiselect("🏢 Entidade", entidades, default=entidades)

# DF FILTRADO (mantém original intacto)
df_filtrado = df[
    df["anoEmpenho"].isin(ano_sel) &
    df["nomeEntidade"].isin(entidade_sel)
]

if df_filtrado.empty:
    st.warning("Nenhum dado encontrado para o filtro selecionado.")
    st.stop()

# ==================================
# MÉTRICAS
# ==================================
st.markdown("### 📌 Indicadores Gerais")

c1, c2, c3 = st.columns(3)

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

c1.metric(
    "💰 Total Empenhado",
    formatar_moeda(df_filtrado["valorEmpenhadoBruto"].sum())
)

c2.metric(
    "❌ Total Anulado",
    formatar_moeda(df_filtrado["valorEmpenhadoAnulado"].sum())
)

c3.metric(
    "✅ Total Baixado",
    formatar_moeda(df_filtrado["saldoBaixado"].sum())
)

# ==================================
# PREPARAÇÃO DO GRÁFICO
# ==================================
df_graf = (
    df_filtrado
    .groupby("anoEmpenho", as_index=False)
    .agg({
        "valorEmpenhadoBruto": "sum",
        "valorEmpenhadoAnulado": "sum",
        "saldoBaixado": "sum"
    })
)

df_graf["Restos a Pagar"] = (
    df_graf["valorEmpenhadoBruto"]
    - df_graf["valorEmpenhadoAnulado"]
    - df_graf["saldoBaixado"]
)

df_long = df_graf.melt(
    id_vars="anoEmpenho",
    value_vars=[
        "valorEmpenhadoAnulado",
        "Restos a Pagar",
        "saldoBaixado"
    ],
    var_name="Tipo",
    value_name="Valor"
)

mapa_tipos = {
    "valorEmpenhadoAnulado": "Anulado",
    "Restos a Pagar": "Restos a Pagar",
    "saldoBaixado": "Baixado no Exercício"
}

df_long["Tipo"] = df_long["Tipo"].map(mapa_tipos)

ordem_tipo = ["Anulado", "Restos a Pagar", "Baixado no Exercício"]

# Percentual para tooltip
df_totais = (
    df_long.groupby("anoEmpenho", as_index=False)["Valor"]
    .sum()
    .rename(columns={"Valor": "Total"})
)

df_long = df_long.merge(df_totais, on="anoEmpenho")
df_long["Percentual"] = df_long["Valor"] / df_long["Total"]

# ==================================
# GRÁFICO
# ==================================
st.markdown("### 📊 Composição do Empenhado por Exercício")

graf = (
    alt.Chart(df_long)
    .mark_bar(size=60)
    .encode(
        x=alt.X("anoEmpenho:N", title="Exercício"),
        y=alt.Y("Valor:Q", title="Valor (R$)", stack="zero"),
        color=alt.Color(
            "Tipo:N",
            sort=ordem_tipo,
            title="Composição",
            scale=alt.Scale(
                domain=ordem_tipo,
                range=["#d62728", "#ffbb78", "#2ca02c"]
            ),
            legend=alt.Legend(orient="bottom", direction="horizontal")
        ),
        tooltip=[
            "anoEmpenho:N",
            "Tipo:N",
            alt.Tooltip("Valor:Q", format=",.2f", title="Valor"),
            alt.Tooltip("Percentual:Q", format=".1%", title="Percentual")
        ]
    )
    .properties(height=420)
)

st.altair_chart(graf, use_container_width=True)

# ==================================
# TABELA RESUMO
# ==================================
st.subheader("📋 Resumo por Exercício")

tabela = df_graf.rename(columns={
    "valorEmpenhadoBruto": "Empenhado",
    "valorEmpenhadoAnulado": "Anulado",
    "saldoBaixado": "Baixado no Exercício"
})

for col in ["Empenhado", "Anulado", "Baixado no Exercício", "Restos a Pagar"]:
    tabela[col] = tabela[col].apply(formatar_moeda)

st.dataframe(tabela, use_container_width=True)
