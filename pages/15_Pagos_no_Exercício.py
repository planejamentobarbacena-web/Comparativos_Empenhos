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
    page_title="Pagos no Exercício",
    page_icon="💵",
    layout="wide"
)

login()
render_header()

st.title("💵 Pagos no Exercício")

st.markdown(
    """
    Painel de consulta dos **valores pagos no exercício**, com filtros livres por  
    exercício, entidade, credor, recurso e natureza da despesa.
    """
)

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
df["anoEmpenho"] = (
    df["anoEmpenho"]
    .astype(str)
    .str.replace(".0", "", regex=False)
    .str.strip()
)

colunas_texto = [
    "nomeEntidade",
    "nomeCredor",
    "numRecurso",
    "numNaturezaEmp"
]

for col in colunas_texto:
    df[col] = df[col].fillna("").astype(str).str.strip()

df = df[(df["anoEmpenho"] != "") & (df["anoEmpenho"] != "nan")]

df["saldoBaixado"] = (
    df["saldoBaixado"]
    .astype(str)
    .str.replace(".", "", regex=False)
    .str.replace(",", ".", regex=False)
)

df["saldoBaixado"] = pd.to_numeric(df["saldoBaixado"], errors="coerce").fillna(0)

# ==================================
# FILTROS LIVRES (BASE NO DF ORIGINAL)
# ==================================
st.divider()
st.subheader("🔎 Filtros")

anos = sorted(df["anoEmpenho"].unique())
entidades = sorted(df["nomeEntidade"].unique())
credores = sorted(df["nomeCredor"].unique())
recursos = sorted(df["numRecurso"].unique())
naturezas = sorted(df["numNaturezaEmp"].unique())

f1, f2, f3 = st.columns(3)
f4, f5 = st.columns(2)

with f1:
    ano_sel = st.multiselect("📅 Exercício", anos, default=anos)

with f2:
    entidade_sel = st.multiselect("🏢 Entidade", entidades, default=entidades)

with f3:
    credor_sel = st.multiselect("👤 Credor", credores, default=credores)

with f4:
    recurso_sel = st.multiselect("💰 Recurso", recursos, default=recursos)

with f5:
    natureza_sel = st.multiselect("📄 Natureza da Despesa", naturezas, default=naturezas)

# ==================================
# APLICAÇÃO DOS FILTROS (UMA ÚNICA VEZ)
# ==================================
df_filtro = df[
    df["anoEmpenho"].isin(ano_sel) &
    df["nomeEntidade"].isin(entidade_sel) &
    df["nomeCredor"].isin(credor_sel) &
    df["numRecurso"].isin(recurso_sel) &
    df["numNaturezaEmp"].isin(natureza_sel)
]

# ==================================
# MÉTRICA PRINCIPAL
# ==================================
st.divider()

st.metric(
    "💵 Total Pago no Exercício",
    f"R$ {df_filtro['saldoBaixado'].sum():,.2f}"
    .replace(",", "X").replace(".", ",").replace("X", ".")
)

# ==================================
# GRÁFICO – PAGOS POR EXERCÍCIO
# ==================================
st.markdown("### 📊 Pagos no Exercício por Ano")

df_graf = (
    df_filtro
    .groupby("anoEmpenho", as_index=False)["saldoBaixado"]
    .sum()
)

graf = (
    alt.Chart(df_graf)
    .mark_bar(size=50)
    .encode(
        x=alt.X(
            "anoEmpenho:N",
            title="Exercício",
            axis=alt.Axis(labelAngle=0)
        ),
        y=alt.Y(
            "saldoBaixado:Q",
            title="Valor Pago (R$)"
        ),
        tooltip=[
            "anoEmpenho:N",
            alt.Tooltip("saldoBaixado:Q", format=",.2f", title="Pago")
        ]
    )
    .properties(height=420)
)

st.altair_chart(graf, use_container_width=True)

# ==================================
# TABELA DETALHADA
# ==================================
st.subheader("📋 Detalhamento dos Pagamentos")

tabela = df_filtro[
    [
        "anoEmpenho",
        "nomeEntidade",
        "nomeCredor",
        "numRecurso",
        "numNaturezaEmp",
        "saldoBaixado"
    ]
].copy()

tabela["saldoBaixado"] = tabela["saldoBaixado"].apply(
    lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)

st.dataframe(tabela, use_container_width=True)
