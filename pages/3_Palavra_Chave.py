import streamlit as st
import os
import json
import altair as alt
import unicodedata

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
    Digite uma **palavra ou expressão** presente na descrição do empenho  
    (ex.: *carnaval*, *sonho de natal*, *festa das rosas*).
    """
)

# ==========================
# Normalização de texto
# ==========================
def normalize_text(texto: str) -> str:
    """Remove acentuação, cedilha e coloca em maiúscula"""
    if not texto:
        return ""
    texto = texto.upper()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join([c for c in texto if unicodedata.category(c) != "Mn"])
    return texto

def singularize(word: str) -> str:
    """Remove S do final para plural simples"""
    if word.endswith("S") and len(word) > 3:
        return word[:-1]
    return word

# ==========================
# Carregar dados
# ==========================
df = load_empenhos()

if df.empty:
    st.warning("Nenhum dado encontrado.")
    st.stop()

# Normalizar coluna de especificação
df["especificacao_norm"] = df["especificacao"].astype(str).apply(normalize_text).apply(singularize)

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

# Normalizar input do usuário
palavra_norm = singularize(normalize_text(palavra))

# ==========================
# Filtro na especificação
# ==========================
df_filtro = df[df["especificacao_norm"].str.contains(palavra_norm, na=False)].copy()

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
export_df = tabela.copy()
csv = export_df.to_csv(index=False, sep=";").encode("utf-8")

st.download_button(
    "⬇️ Baixar CSV – Palavra-Chave",
    csv,
    file_name=f"empenhos_palavra_chave_{palavra.replace(' ', '_')}.csv",
    mime="text/csv"
)
