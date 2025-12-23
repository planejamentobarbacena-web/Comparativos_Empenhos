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
# TRATAMENTO BÁSICO
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

# Colunas financeiras
col_valores = {
    "valorEmpenhadoBruto": "Empenhado",
    "valorEmpenhadoAnulado": "Anulado",
    "saldoBaixado": "Baixado no Exercício"
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
    "✅ Total Baixado no Exercício",
    f"R$ {df['saldoBaixado'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)

# ==================================
# FILTROS
# ==================================
st.divider()

anos = sorted(df["anoEmpenho"].unique())
entidades = sorted(df["nomeEntidade"].unique())

colf1, colf2 = st.columns(2)

with colf1:
    ano_sel = st.multiselect("📅 Exercício", anos, default=anos)

with colf2:
    entidade_sel = st.multiselect("🏢 Entidade", entidades, default=entidades)

df = df[
    df["anoEmpenho"].isin(ano_sel) &
    df["nomeEntidade"].isin(entidade_sel)
]

# ==================================
# AGREGAÇÃO POR EXERCÍCIO
# ==================================
df_graf = (
    df.groupby("anoEmpenho", as_index=False)
    .agg({
        "valorEmpenhadoBruto": "sum",
        "valorEmpenhadoAnulado": "sum",
        "saldoBaixado": "sum"
    })
    .rename(columns=col_valores)
)

# ==================================
# RESTOS A PAGAR
# ==================================
df_graf["Resto a Pagar"] = (
    df_graf["Empenhado"]
    - df_graf["Anulado"]
    - df_graf["Baixado no Exercício"]
)

# ==================================
# PREPARAÇÃO DO GRÁFICO
# ==================================

# Empilhado dentro do Empenhado
df_empilhado = df_graf.melt(
    id_vars="anoEmpenho",
    value_vars=["Anulado", "Baixado no Exercício", "Resto a Pagar"],
    var_name="Tipo",
    value_name="Valor"
)
df_empilhado["Grupo"] = "Empenhado"

# Coluna isolada de Restos
df_restos = df_graf[["anoEmpenho", "Resto a Pagar"]].copy()
df_restos["Tipo"] = "Restos a Pagar"
df_restos["Valor"] = df_restos["Resto a Pagar"]
df_restos["Grupo"] = "Restos a Pagar"

df_plot = pd.concat([df_empilhado, df_restos], ignore_index=True)

# ==================================
# GRÁFICO
# ==================================
st.markdown("### 📊 Empenhado e Restos a Pagar por Exercício")

graf = (
    alt.Chart(df_plot)
    .mark_bar(size=26)
    .encode(
        x=alt.X(
            "anoEmpenho:N",
            title="Exercício",
            axis=alt.Axis(labelAngle=0)
        ),
        xOffset=alt.XOffset("Grupo:N"),
        y=alt.Y(
            "Valor:Q",
            title="Valor (R$)",
            stack="zero"
        ),
        color=alt.Color(
            "Tipo:N",
            title="Composição",
            scale=alt.Scale(
                domain=[
                    "Anulado",
                    "Baixado no Exercício",
                    "Resto a Pagar",
                    "Restos a Pagar"
                ],
                range=[
                    "#d62728",
                    "#2ca02c",
                    "#1f77b4",
                    "#9467bd"
                ]
            ),
            legend=alt.Legend(
                orient="bottom",
                direction="horizontal"
            )
        ),
        tooltip=[
            "anoEmpenho:N",
            "Grupo:N",
            "Tipo:N",
            alt.Tooltip("Valor:Q", format=",.2f")
        ]
    )
    .properties(height=430)
)

st.altair_chart(graf, use_container_width=True)

# ==================================
# TABELA RESUMO
# ==================================
st.subheader("📋 Resumo por Exercício")

tabela = df_graf.copy()

for col in ["Empenhado", "Anulado", "Baixado no Exercício", "Resto a Pagar"]:
    tabela[col] = tabela[col].apply(
        lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )

st.dataframe(tabela, use_container_width=True)
