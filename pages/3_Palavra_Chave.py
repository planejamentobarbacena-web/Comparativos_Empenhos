import streamlit as st
import altair as alt
import pandas as pd
import unicodedata
from auth import login
from components.header import render_header
from data_loader import load_empenhos

# 🔐 Segurança
login()
render_header()

st.set_page_config(
    page_title="🔎 Empenhos por Palavra-Chave",
    layout="wide"
)

st.title("🔎 Empenhos por Palavra-Chave")

# ==========================
# CARREGAR DADOS
# ==========================
df = load_empenhos()
if df.empty:
    st.warning("Nenhum dado encontrado.")
    st.stop()

# ==========================
# TRATAMENTO DE VALORES (CORREÇÃO DO ERRO)
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
# FILTROS GLOBAIS
# ==========================
anos = sorted(df["anoEmpenho"].dropna().unique())
entidades = sorted(df["nomeEntidade"].dropna().unique())

anos_sel = st.multiselect(
    "📅 Selecione Exercício(s)",
    anos,
    default=anos
)

entidades_sel = st.multiselect(
    "🏢 Selecione Entidade(s)",
    entidades,
    default=entidades
)

df = df[
    df["anoEmpenho"].isin(anos_sel) &
    df["nomeEntidade"].isin(entidades_sel)
]

# ==========================
# Normalização de texto
# ==========================
def normalize_text(texto: str) -> str:
    if not texto:
        return ""
    texto = texto.upper()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto

def singularize(word: str) -> str:
    if word.endswith("S") and len(word) > 3:
        return word[:-1]
    return word

df["especificacao_norm"] = (
    df["especificacao"]
    .astype(str)
    .apply(normalize_text)
    .apply(singularize)
)

# ==========================
# Palavra-chave
# ==========================
palavra = st.text_input(
    "🔍 Palavra-chave para busca",
    placeholder="Ex: sonho de natal"
)

if not palavra:
    st.info("Digite uma palavra para iniciar a análise.")
    st.stop()

palavra_norm = singularize(normalize_text(palavra))

df_filtro = df[
    df["especificacao_norm"].str.contains(palavra_norm, na=False)
].copy()

if df_filtro.empty:
    st.warning("Nenhum empenho encontrado com essa palavra.")
    st.stop()

# ==========================
# Filtro por Descrição da Despesa
# ==========================
despesas = ["Todos"] + sorted(
    df_filtro["Descrição da despesa"].dropna().unique()
)

despesa_sel = st.multiselect(
    "📂 Filtro – Descrição da Despesa",
    despesas,
    default=["Todos"]
)

if "Todos" not in despesa_sel:
    df_filtro = df_filtro[
        df_filtro["Descrição da despesa"].isin(despesa_sel)
    ]

# ==========================
# Métrica
# ==========================
total = df_filtro["valorEmpenhadoLiquido"].sum()

st.metric(
    "💰 Total Empenhado Líquido",
    f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)

# ==========================
# Gráfico (sem linhas)
# ==========================
graf = (
    alt.Chart(df_filtro)
    .mark_bar(size=50)
    .encode(
        x=alt.X("anoEmpenho:N", title="Exercício"),
        y=alt.Y(
            "sum(valorEmpenhadoLiquido):Q",
            title="Valor Empenhado Líquido (R$)"
        ),
        tooltip=[
            "anoEmpenho:N",
            alt.Tooltip(
                "sum(valorEmpenhadoLiquido):Q",
                format=",.2f"
            )
        ]
    )
    .properties(height=420)
)

st.altair_chart(graf, use_container_width=True)

# ==========================
# Tabela
# ==========================
cols = [
    "numeroEmpenho",
    "Ano",
    "especificacao",
    "data",
    "valorEmpenhadoBruto",
    "valorEmpenhadoAnulado",
    "valor_liquido",
    "nomeCredor",
    "Descrição da despesa",
    "Descrição da natureza",
    "numRecurso"
]

tabela = df_filtro[cols].copy()

for col in ["valorEmpenhadoBruto", "valorEmpenhadoAnulado", "valor_liquido"]:
    tabela[col] = tabela[col].apply(
        lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )

st.subheader("📋 Empenhos encontrados")
st.dataframe(tabela, use_container_width=True)

# ==========================
# Download
# ==========================
csv = tabela.to_csv(index=False, sep=";", encoding="utf-8")

st.download_button(
    "⬇️ Baixar CSV – Palavra-Chave",
    csv,
    file_name=f"empenhos_palavra_chave_{palavra.replace(' ', '_')}.csv",
    mime="text/csv"
)
