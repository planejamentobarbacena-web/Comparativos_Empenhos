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

# ==================================
# CSS RESPONSIVO (DESKTOP x MOBILE)
# ==================================
st.markdown("""
<style>

/* Esconde versão desktop no celular */
@media (max-width: 768px) {
    .desktop-only {
        display: none !important;
    }
}

/* Esconde versão mobile no desktop */
@media (min-width: 769px) {
    .mobile-only {
        display: none !important;
    }
}

</style>
""", unsafe_allow_html=True)

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

# Remover inválidos
df = df[(df["anoEmpenho"] != "") & (df["anoEmpenho"] != "nan")]
df = df[df["nomeEntidade"] != ""]

# Valores numéricos
colunas = [
    "valorEmpenhadoBruto",
    "valorEmpenhadoAnulado",
    "saldoBaixado"
]

for col in colunas:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# ==================================
# MÉTRICAS
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
# PREPARAÇÃO DO GRÁFICO
# ==================================
df_graf = (
    df.groupby("anoEmpenho", as_index=False)
    .agg({
        "valorEmpenhadoBruto": "sum",
        "valorEmpenhadoAnulado": "sum",
        "saldoBaixado": "sum"
    })
)

# Restos a Pagar (parte interna do Empenhado)
df_graf["Restos a Pagar"] = (
    df_graf["valorEmpenhadoBruto"]
    - df_graf["valorEmpenhadoAnulado"]
    - df_graf["saldoBaixado"]
)

df_long = df_graf.melt(
    id_vars="anoEmpenho",
    value_vars=["valorEmpenhadoAnulado", "Restos a Pagar", "saldoBaixado"],
    var_name="Tipo",
    value_name="Valor"
)

# Renomear para legenda
df_long["Tipo"] = df_long["Tipo"].replace({
    "valorEmpenhadoAnulado": "Anulado",
    "saldoBaixado": "Baixado no Exercício"
})

# Ordem correta do empilhamento
ordem_tipo = ["Anulado", "Restos a Pagar", "Baixado no Exercício"]

# ==================================
# GRÁFICO DESKTOP
# ==================================
graf_desktop = (
    alt.Chart(df_long)
    .mark_bar(size=34)
    .encode(
        x=alt.X("anoEmpenho:N", title="Exercício"),
        y=alt.Y("Valor:Q", title="Valor (R$)"),
        color=alt.Color(
            "Tipo:N",
            sort=ordem_tipo,
            title="Composição",
            legend=alt.Legend(
                orient="bottom",
                direction="horizontal"
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

# ==================================
# GRÁFICO MOBILE (SIMPLIFICADO)
# ==================================
graf_mobile = (
    alt.Chart(df_long)
    .mark_bar(size=46)
    .encode(
        x=alt.X("anoEmpenho:N", title=None),
        y=alt.Y("Valor:Q", title="R$"),
        color=alt.Color("Tipo:N", sort=ordem_tipo, legend=None),
        tooltip=[
            "anoEmpenho:N",
            "Tipo:N",
            alt.Tooltip("Valor:Q", format=",.2f")
        ]
    )
    .properties(height=320)
)

# ==================================
# EXIBIÇÃO RESPONSIVA
# ==================================
st.markdown('<div class="desktop-only">', unsafe_allow_html=True)
st.markdown("### 📊 Composição do Empenhado por Exercício")
st.altair_chart(graf_desktop, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="mobile-only">', unsafe_allow_html=True)
st.markdown("### 📊 Empenhado por Exercício")
st.altair_chart(graf_mobile, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)
