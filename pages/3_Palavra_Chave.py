import streamlit as st
import altair as alt
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
# AJUSTE DE VALOR (BRUTO - ANULADO)
# ==========================
df["valor_liquido"] = (
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

df = df[df["anoEmpenho"].isin(anos_sel)]
df = df[df["nomeEntidade"].isin(entidades_sel)]

# ==========================
# Normalização de texto
# ==========================
def normalize_text(texto: str) -> str:
    if not texto:
        return ""
    texto = texto.upper()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        c for c in texto if unicodedata.category(c) != "Mn"
    )
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
# Campo de busca (palavra-chave)
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
# Filtro por DESCRIÇÃO DA DESPESA
# ==========================
despesas = ["Todos"] + sorted(
    df_filtro["Descrição da despesa"].dropna().unique()
)

despesas_sel = st.multiselect(
    "📂 Selecione a Despesa",
    despesas,
    default=["Todos"]
)

if "Todos" not in despesas_sel:
    df_filtro = df_filtro[
        df_filtro["Descrição da despesa"].isin(despesas_sel)
    ]

# ==========================
# MÉTRICA
# ==========================
total = df_filtro["valor_liquido"].sum()

st.metric(
    "💰 Total Empenhado (líquido)",
    f"R$ {total:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
)

# ==========================
# GRÁFICO POR EXERCÍCIO
# ==========================
graf = (
    alt.Chart(df_filtro)
    .mark_bar(size=50)
    .encode(
        x=alt.X("anoEmpenho:N", title="Exercício"),
        y=alt.Y(
            "sum(valor_liquido):Q",
            title="Valor Empenhado Líquido (R$)"
        ),
        tooltip=[
            "anoEmpenho:N",
            alt.Tooltip(
                "sum(valor_liquido):Q",
                format=",.2f"
            )
        ]
    )
    .properties(height=420)
)

st.altair_chart(graf, use_container_width=True)

# ==========================
# TABELA DETALHADA
# ==========================
st.subheader("📋 Empenhos encontrados")

cols = [
    "numeroEmpenho",
    "anoEmpenho",
    "nomeEntidade",
    "especificacao",
    "data",
    "Descrição da despesa",
    "Descrição da natureza",
    "nomeCredor",
    "numRecurso",
    "valor_liquido"
]

tabela = df_filtro[cols].copy()

tabela["valor_liquido"] = tabela["valor_liquido"].apply(
    lambda x: f"R$ {x:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
)

tabela = tabela.rename(columns={
    "anoEmpenho": "Exercício",
    "valor_liquido": "Valor Empenhado Líquido"
})

st.dataframe(tabela, use_container_width=True)

# ==========================
# DOWNLOAD CSV
# ==========================
csv = tabela.to_csv(
    index=False,
    sep=";",
    encoding="utf-8-sig"
)

st.download_button(
    "⬇️ Baixar CSV – Palavra-Chave",
    csv,
    file_name=f"empenhos_palavra_chave_{palavra.replace(' ','_')}.csv",
    mime="text/csv"
)
