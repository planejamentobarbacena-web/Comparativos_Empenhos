import streamlit as st
import altair as alt
import pandas as pd

from auth import login
from components.header import render_header
from data_loader import load_empenhos  

# ==================================
# CONFIGURAÇÃO
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
# TRATAMENTO BÁSICO (OBRIGATÓRIO)
# ==================================

# Exercício
df["anoEmpenho"] = (
    df["anoEmpenho"]
    .astype(str)
    .str.replace(".0", "", regex=False)
    .str.strip()
)

# Entidade
df["nomeEntidade"] = df["nomeEntidade"].fillna("").astype(str).str.strip()

# Remover registros inválidos
df = df[(df["anoEmpenho"] != "") & (df["anoEmpenho"] != "nan")]
df = df[df["nomeEntidade"] != ""]

# Valores numéricos
col_valores = {
    "valorEmpenhadoBruto": "Empenhado",
    "valorEmpenhadoAnulado": "Anulado",
    "valorBaixadoBruto": "Baixado no Exercício"
}

for col in col_valores:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# ==================================
# MÉTRICAS GERAIS
# ==================================
col1, col2, col3 = st.columns(3)

col1.metric(
    "💰 Total Empenhado",
    f"R$ {df['valorEmpenhadoBruto'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)

col2.metric(
    "❌ Total Anulado",
    f"R$ {df['valorEmpenhadoAnulado'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)

col3.metric(
    "✅ Total Baixado",
    f"R$ {df['valorBaixadoBruto'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)

# ==================================
# FILTROS (ENTRE MÉTRICAS E GRÁFICO)
# ==================================
st.divider()

anos = sorted(df["anoEmpenho"].unique())
entidades = sorted(df["nomeEntidade"].unique())

colf1, colf2 = st.columns(2)

with colf1:
    ano_sel = st.multiselect(
        "📅 Exercício",
        anos,
        default=anos
    )

with colf2:
    entidade_sel = st.multiselect(
        "🏢 Entidade",
        entidades,
        default=entidades
    )

df = df[
    df["anoEmpenho"].isin(ano_sel) &
    df["nomeEntidade"].isin(entidade_sel)
]

# ==================================
# PREPARAÇÃO PARA O GRÁFICO
# ==================================
df_graf = (
    df.groupby("anoEmpenho", as_index=False)
    .agg({
        "valorEmpenhadoBruto": "sum",
        "valorEmpenhadoAnulado": "sum",
        "valorBaixadoBruto": "sum"
    })
    .rename(columns=col_valores)
)

df_long = df_graf.melt(
    id_vars="anoEmpenho",
    var_name="Tipo",
    value_name="Valor"
)

# ==================================
# GRÁFICO
# ==================================
st.markdown("### 📊 Empenhado × Anulado × Baixado por Exercício")

graf = (
    alt.Chart(df_long)
    .mark_bar(size=40)
    .encode(
        x=alt.X("anoEmpenho:N", title="Exercício"),
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

# ==================================
# TABELA RESUMO
# ==================================
st.subheader("📋 Resumo por Exercício")

tabela = df_graf.copy()

for col in ["Empenhado", "Anulado", "Baixado no Exercício"]:
    tabela[col] = tabela[col].apply(
        lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )

st.dataframe(tabela, use_container_width=True)
