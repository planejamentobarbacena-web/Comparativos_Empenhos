import streamlit as st
import os
import json
import altair as alt

from auth import login, exige_admin
from components.header import render_header
from data_loader import load_empenhos  

# 🔐 Segurança
login()
render_header()

st.set_page_config(
    page_title="Filtro por Palavra-Chave",
    page_icon="🔎",
    layout="wide"
)

st.title("🔎 Empenhos por Palavra-Chave")

st.markdown(
    """
    Digite uma **palavra ou expressão exata** presente na descrição do empenho  
    (ex.: *carnaval*, *sonho de natal*, *festa das rosas*).
    """
)

# ==========================
# Carregar dados
# ==========================
df = load_empenhos()

if df.empty:
    st.warning("Nenhum dado encontrado.")
    st.stop()

# ==========================
# Campo de busca
# ==========================
palavra = st.text_input(
    "🔍 Palavra-chave para busca",
    placeholder="Ex: sonho de natal"
)

if not palavra:
    st.info("Digite uma palavra para iniciar a análise.")
    st.stop()

# ==========================
# Filtro na especificação
# ==========================
df_filtro = df[
    df["especificacao"]
    .str.contains(palavra, case=False, na=False)
].copy()

if df_filtro.empty:
    st.warning("Nenhum empenho encontrado com essa palavra.")
    st.stop()

# ==========================
# Métrica rápida
# ==========================
total = df_filtro["valorEmpenhadoBruto_num"].sum()

st.metric(
    "💰 Total Empenhado (Palavra-Chave)",
    f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)

# ==========================
# Gráfico por exercício
# ==========================
graf = (
    alt.Chart(df_filtro)
    .mark_bar(size=50)
    .encode(
        x=alt.X("Ano:N", title="Exercício"),
        y=alt.Y("sum(valorEmpenhadoBruto_num):Q", title="Valor Empenhado (R$)"),
        tooltip=[
            "Ano:N",
            alt.Tooltip("sum(valorEmpenhadoBruto_num):Q", format=",.2f")
        ]
    )
    .properties(height=420)
)

st.altair_chart(graf, use_container_width=True)

# ==========================
# Tabela detalhada
# ==========================
st.subheader("📋 Empenhos encontrados")

cols = [
    "numeroEmpenho",
    "Ano",
    "especificacao",
    "data",
    "valorEmpenhadoBruto_num",
    "nomeCredor",
    "numDespesa",
    "numNaturezaEmp",
    "numRecurso"
]

tabela = df_filtro[cols].copy()

tabela["valorEmpenhadoBruto_num"] = tabela["valorEmpenhadoBruto_num"].apply(
    lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)

st.dataframe(tabela, use_container_width=True)

# ==========================
# Download CSV
# ==========================
# ==========================
# DataFrame para exportação
# ==========================
export_df = df_filtro[cols].copy()

export_df["valorEmpenhadoBruto_num"] = export_df["valorEmpenhadoBruto_num"].apply(
    lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)

csv = export_df.to_csv(index=False, sep=";").encode("utf-8")


st.download_button(
    "⬇️ Baixar CSV – Palavra-Chave",
    csv,
    file_name=f"empenhos_palavra_chave_{palavra.replace(' ', '_')}.csv",
    mime="text/csv"
)
