import streamlit as st
import altair as alt
import pandas as pd

from auth import login
from components.header import render_header
from data_loader import load_empenhos

# 🔐 Segurança
login()
render_header()

st.title("📑 Consulta por Despesa")

# =======================
# CARREGAR DADOS
# =======================
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

# =======================
# TRATAMENTO DE VALORES
# =======================
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

df["empenhado_liquido"] = (
    df["valorEmpenhadoBruto"] - df["valorEmpenhadoAnulado"]
)

# =======================
# FILTRO – EXERCÍCIO
# =======================
anos = sorted(df["anoEmpenho"].dropna().unique())

anos_sel = st.multiselect(
    "📅 Exercício",
    anos,
    default=anos
)

df = df[df["anoEmpenho"].isin(anos_sel)]

# =======================
# FILTRO – ENTIDADE
# =======================
entidades = sorted(df["nomeEntidade"].dropna().unique())

entidades_sel = st.multiselect(
    "🏢 Entidade",
    entidades,
    default=entidades
)

df = df[df["nomeEntidade"].isin(entidades_sel)]

# =======================
# FILTRO – DESCRIÇÃO DA DESPESA
# =======================
despesas = ["Todos"] + sorted(df["Descrição da despesa"].dropna().unique())

despesa_sel = st.multiselect(
    "📂 Descrição da Despesa",
    despesas,
    default=["Todos"]
)

if "Todos" not in despesa_sel:
    df = df[df["Descrição da despesa"].isin(despesa_sel)]

# =======================
# FILTRO – CREDOR
# =======================
credores = ["Todos"] + sorted(df["nomeCredor"].dropna().unique())

credor_sel = st.multiselect(
    "🏷️ Credor",
    credores,
    default=["Todos"]
)

if "Todos" not in credor_sel:
    df = df[df["nomeCredor"].isin(credor_sel)]

# =======================
# FILTRO – FONTE
# =======================
fontes = ["Todos"] + sorted(df["numRecurso"].dropna().unique())

fonte_sel = st.multiselect(
    "💰 Fonte de Recurso",
    fontes,
    default=["Todos"]
)

if "Todos" not in fonte_sel:
    df = df[df["numRecurso"].isin(fonte_sel)]

if df.empty:
    st.info("Nenhum dado para os filtros selecionados.")
    st.stop()

# =======================
# AGRUPAMENTO
# =======================
comparativo = (
    df
    .groupby("anoEmpenho", as_index=False)[
        ["empenhado_liquido", "saldoBaixado"]
    ]
    .sum()
)

# =======================
# GRÁFICO (DUAS BARRAS)
# =======================
graf = (
    alt.Chart(comparativo)
    .transform_fold(
        ["empenhado_liquido", "saldoBaixado"],
        as_=["Tipo", "Valor"]
    )
    .mark_bar(size=40)
    .encode(
        x=alt.X("anoEmpenho:N", title="Exercício"),
        xOffset="Tipo:N",
        y=alt.Y("Valor:Q", title="Valor (R$)"),
        color=alt.Color(
            "Tipo:N",
            title="Tipo",
            scale=alt.Scale(
                domain=["empenhado_liquido", "saldoBaixado"],
                range=["#1f77b4", "#ff7f0e"]
            )
        ),
        tooltip=[
            "anoEmpenho:N",
            "Tipo:N",
            alt.Tooltip("Valor:Q", format=",.2f")
        ]
    )
    .properties(height=420)
)

st.altair_chart(graf, use_container_width=True)

# =======================
# TABELA
# =======================
st.subheader("📊 Detalhamento")

tabela = df[
    [
        "anoEmpenho",
        "nomeEntidade",
        "Descrição da despesa",
        "nomeCredor",
        "numRecurso",
        "empenhado_liquido",
        "saldoBaixado"
    ]
].copy()

tabela["Empenhado Líquido"] = tabela["empenhado_liquido"].apply(
    lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)

tabela["Saldo Baixado"] = tabela["saldoBaixado"].apply(
    lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)

tabela = tabela[
    [
        "anoEmpenho",
        "nomeEntidade",
        "Descrição da despesa",
        "nomeCredor",
        "numRecurso",
        "Empenhado Líquido",
        "Saldo Baixado"
    ]
]

st.dataframe(tabela, use_container_width=True)

# =======================
# DOWNLOAD CSV
# =======================
st.divider()

csv = tabela.to_csv(index=False, sep=";", encoding="utf-8-sig")

st.download_button(
    "📥 Baixar CSV – Consulta por Despesa",
    csv,
    file_name="consulta_por_despesa.csv",
    mime="text/csv"
)
