import streamlit as st
import altair as alt
import pandas as pd

from auth import login
from components.header import render_header
from data_loader import load_empenhos

# ==================================
# CONFIGURAÇÃO / SEGURANÇA
# ==================================
login()
render_header()

st.title("💰 Pagos no Exercício")

# ==================================
# CARREGAR DADOS (PADRÃO DO PROJETO)
# ==================================
df = load_empenhos()

if df.empty:
    st.warning("Nenhum dado carregado.")
    st.stop()

# ==================================
# LIMPEZA BÁSICA
# ==================================
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

# ==================================
# TRATAMENTO DO VALOR USADO NO PAINEL
# ==================================
df["saldoBaixado"] = (
    df["saldoBaixado"]
    .astype(str)
    .str.replace(".", "", regex=False)
    .str.replace(",", ".", regex=False)
)

df["saldoBaixado"] = pd.to_numeric(
    df["saldoBaixado"],
    errors="coerce"
).fillna(0)

# ==================================
# FILTROS LIVRES (VERTICAIS)
# ==================================
st.markdown("### 🔎 Filtros")

def filtro_multiselect(df_base, coluna, label):
    opcoes = sorted(df_base[coluna].dropna().unique().tolist())

    selecionado = st.multiselect(
        label,
        options=opcoes,
        default=opcoes
    )

    if not selecionado:
        return df_base

    return df_base[df_base[coluna].isin(selecionado)]

df_filtrado = filtro_multiselect("anoEmpenho", "📅 Exercício")
df_filtrado = filtro_multiselect("nomeEntidade", "🏢 Entidade")
df_filtrado = filtro_multiselect("nomeCredor", "🏷️ Credor")
df_filtrado = filtro_multiselect("numRecurso", "💰 Fonte de Recurso")
df_filtrado = filtro_multiselect("Descrição da despesa", "📂 Natureza da Despesa")

if df_filtrado.empty:
    st.info("Nenhum dado para os filtros selecionados.")
    st.stop()

# ==================================
# AGRUPAMENTO PARA O GRÁFICO
# ==================================
df_graf = (
    df_filtrado
    .groupby("anoEmpenho", as_index=False)["saldoBaixado"]
    .sum()
)

# ==================================
# GRÁFICO – PAGOS NO EXERCÍCIO
# ==================================
st.markdown("### 📊 Total Pago por Exercício")

graf = (
    alt.Chart(df_graf)
    .mark_bar(size=60)
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
            alt.Tooltip("anoEmpenho:N", title="Exercício"),
            alt.Tooltip("saldoBaixado:Q", title="Valor Pago", format=",.2f")
        ]
    )
    .properties(height=420)
)

st.altair_chart(graf, use_container_width=True)

# ==================================
# TABELA DETALHADA
# ==================================
st.subheader("📋 Detalhamento")

tabela = df_filtrado[
    [
        "anoEmpenho",
        "nomeEntidade",
        "Descrição da despesa",
        "nomeCredor",
        "numRecurso",
        "saldoBaixado"
    ]
].copy()

tabela["Valor Pago"] = tabela["saldoBaixado"].apply(
    lambda x: f"R$ {x:,.2f}"
    .replace(",", "X")
    .replace(".", ",")
    .replace("X", ".")
)

tabela = tabela[
    [
        "anoEmpenho",
        "nomeEntidade",
        "Descrição da despesa",
        "nomeCredor",
        "numRecurso",
        "Valor Pago"
    ]
]

st.dataframe(tabela, use_container_width=True)

# ==================================
# DOWNLOAD
# ==================================
st.divider()

csv = tabela.to_csv(index=False, sep=";", encoding="utf-8-sig")

st.download_button(
    "📥 Baixar CSV – Pagos no Exercício",
    csv,
    file_name="pagos_no_exercicio.csv",
    mime="text/csv"
)
