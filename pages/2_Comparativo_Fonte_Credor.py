import streamlit as st
import altair as alt
from auth import login
from components.header import render_header
from data_loader import load_empenhos

# 🔐 Segurança
login()
render_header()

st.set_page_config(
    page_title="💰 Comparativo Fonte → Credor",
    layout="wide"
)

st.title("💰 Comparativo: Fonte de Recurso → Credores")

# =======================
# CARREGAR DADOS
# =======================
df = load_empenhos()
if df.empty:
    st.warning("Nenhum dado carregado.")
    st.stop()

# =======================
# FILTROS GLOBAIS
# =======================
anos = sorted(df["Ano"].dropna().unique())
entidades = sorted(df["nomeEntidade"].dropna().unique())

anos_sel = st.multiselect("📅 Selecione Exercício(s)", anos, default=anos)
entidades_sel = st.multiselect("🏢 Selecione Entidade(s)", entidades, default=entidades)

df = df[df["Ano"].isin(anos_sel)]
df = df[df["nomeEntidade"].isin(entidades_sel)]

# =======================
# FILTRO POR FONTE DE RECURSO
# =======================
fonte = st.selectbox("Selecione a Fonte de Recurso:", ["Todos"] + sorted(df["numRecurso"].dropna().unique()))
df_sel = df.copy()
if fonte != "Todos":
    df_sel = df_sel[df_sel["numRecurso"] == fonte]

# =======================
# Melt para Altair
# =======================
df_melt = df_sel.melt(
    id_vars=["Ano", "nomeCredor"],
    value_vars=["valorEmpenhadoBruto_num", "valorEmpenhadoAnulado_num", "valorBaixadoBruto_num"],
    var_name="Tipo",
    value_name="Montante"
)

df_melt["Tipo"] = df_melt["Tipo"].map({
    "valorEmpenhadoBruto_num": "Empenhado Bruto",
    "valorEmpenhadoAnulado_num": "Empenhado Anulado",
    "valorBaixadoBruto_num": "Baixado Bruto"
})

# =======================
# GRÁFICO
# =======================
graf = (
    alt.Chart(df_melt)
    .mark_bar()
    .encode(
        x=alt.X("Ano:N", title="Exercício"),
        xOffset=alt.XOffset("Tipo:N", scale=alt.Scale(paddingInner=0.1)),
        y=alt.Y("Montante:Q", title="Valor (R$)"),
        color=alt.Color("nomeCredor:N", title="Credor", scale=alt.Scale(scheme='category20')),
        tooltip=[
            "Ano:N",
            "Tipo:N",
            "nomeCredor:N",
            alt.Tooltip("Montante:Q", format=",.2f")
        ]
    )
    .properties(height=450)
)
st.altair_chart(graf, use_container_width=True)

# =======================
# TABELA
# =======================
comparativo = df_sel.groupby(["Ano", "nomeCredor"], as_index=False)[
    ["valorEmpenhadoBruto_num", "valorEmpenhadoAnulado_num", "valorBaixadoBruto_num"]
].sum()

comparativo_display = comparativo.rename(columns={
    "valorEmpenhadoBruto_num": "Empenhado Bruto",
    "valorEmpenhadoAnulado_num": "Empenhado Anulado",
    "valorBaixadoBruto_num": "Baixado Bruto"
})

for col in ["Empenhado Bruto", "Empenhado Anulado", "Baixado Bruto"]:
    comparativo_display[col] = comparativo_display[col].apply(
        lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )

st.subheader("📋 Tabela de valores por Exercício e Credor")
st.dataframe(comparativo_display, use_container_width=True)
