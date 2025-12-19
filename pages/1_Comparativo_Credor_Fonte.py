import streamlit as st
import altair as alt
from auth import login
from components.header import render_header
from data_loader import load_empenhos

# 🔐 Segurança
login()
render_header()

st.set_page_config(
    page_title="💰 Comparativo: Credor x Fonte",
    layout="wide"
)

st.title("💰 Comparativo: Credor x Fonte de Recurso")

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
credores = sorted(df["nomeCredor"].dropna().unique())

anos_sel = st.multiselect("📅 Selecione Exercício(s)", anos, default=anos)
entidades_sel = st.multiselect("🏢 Selecione Entidade(s)", entidades, default=entidades)
credores_sel = st.multiselect("👤 Selecione Credor(es)", credores, default=credores)

df = df[df["Ano"].isin(anos_sel)]
df = df[df["nomeEntidade"].isin(entidades_sel)]
df = df[df["nomeCredor"].isin(credores_sel)]

# =======================
# Melt dos dados para gráfico
# =======================
df_melt = df.melt(
    id_vars=["Ano", "nomeCredor", "numRecurso"],
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
# Totais para linha centralizada
# =======================
linha_totais = df_melt.groupby(["Ano", "Tipo"], as_index=False)["Montante"].sum()

# =======================
# Gráfico: barras + linha + labels
# =======================
barras = (
    alt.Chart(df_melt)
    .mark_bar()
    .encode(
        x=alt.X("Ano:N", title="Exercício"),
        xOffset=alt.XOffset("Tipo:N", scale=alt.Scale(paddingInner=0.1)),
        y=alt.Y("Montante:Q", title="Valor (R$)"),
        color=alt.Color("numRecurso:N", title="Fonte de Recurso", scale=alt.Scale(scheme='category20')),
        tooltip=[
            "Ano:N",
            "Tipo:N",
            "numRecurso:N",
            "nomeCredor:N",
            alt.Tooltip("Montante:Q", format=",.2f")
        ]
    )
)

labels = (
    alt.Chart(linha_totais)
    .mark_text(dy=-5, fontWeight="bold", fontSize=11)
    .encode(
        x=alt.X("Ano:N"),
        xOffset=alt.XOffset("Tipo:N", scale=alt.Scale(paddingInner=0.1)),
        y=alt.Y("Montante:Q"),
        text=alt.Text("Tipo:N")
    )
)

graf = alt.layer(barras, linha, labels).properties(height=450)
st.altair_chart(graf, use_container_width=True)

# =======================
# Tabela detalhada
# =======================
comparativo = df.groupby(["Ano", "numRecurso"], as_index=False)[
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

st.subheader("📋 Tabela de valores por Exercício e Fonte")
st.dataframe(comparativo_display, use_container_width=True)
