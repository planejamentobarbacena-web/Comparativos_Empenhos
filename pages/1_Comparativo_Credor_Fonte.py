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
    page_title="Comparativo Exercício x Tipo",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Comparativo: Credor x Fonte de Recurso")

# Carregar dados
df = load_empenhos()
if df.empty:
    st.warning("Nenhum dado carregado.")
    st.stop()

# Filtro opcional de credor
credor = st.selectbox(
    "Selecione o Credor:",
    ["Todos"] + sorted(df["nomeCredor"].dropna().unique())
)

df_sel = df.copy()
if credor != "Todos":
    df_sel = df_sel[df_sel["nomeCredor"] == credor]

# Melt dos dados
df_melt = df_sel.melt(
    id_vars=["Ano", "numRecurso"],
    value_vars=["valorEmpenhadoBruto_num", "valorEmpenhadoAnulado_num", "valorBaixadoBruto_num"],
    var_name="Tipo",
    value_name="Montante"
)

# Mapear nomes amigáveis
df_melt["Tipo"] = df_melt["Tipo"].map({
    "valorEmpenhadoBruto_num": "Empenhado Bruto",
    "valorEmpenhadoAnulado_num": "Empenhado Anulado",
    "valorBaixadoBruto_num": "Baixado Bruto"
})

# ==========================
# Calcular total por Tipo + Ano para a linha centralizada
# ==========================
linha_totais = df_melt.groupby(["Ano", "Tipo"], as_index=False)["Montante"].sum()

# ==========================
# Gráfico de barras empilhadas
# ==========================
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
            alt.Tooltip("Montante:Q", format=",.2f")
        ]
    )
)

# ==========================
# Linha centralizada no topo de cada barra
# ==========================
linha = (
    alt.Chart(linha_totais)
    .mark_line(color="black", size=2)
    .encode(
        x=alt.X("Ano:N"),
        xOffset=alt.XOffset("Tipo:N", scale=alt.Scale(paddingInner=0.1)),  # centraliza sobre cada barra
        y=alt.Y("Montante:Q"),
        detail="Tipo:N"  # linha por Tipo
    )
)

# ==========================
# Labels ao lado de cada barra
# ==========================
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

# ==========================
# Layer: barras + linha + labels
# ==========================
graf = alt.layer(barras, labels).properties(height=450)

st.altair_chart(graf, use_container_width=True)

# ======================================
# Tabela abaixo do gráfico
# ======================================
comparativo = df_sel.groupby(["Ano", "numRecurso"], as_index=False)[
    ["valorEmpenhadoBruto_num", "valorEmpenhadoAnulado_num", "valorBaixadoBruto_num"]
].sum()

comparativo_display = comparativo.rename(columns={
    "valorEmpenhadoBruto_num": "Empenhado Bruto",
    "valorEmpenhadoAnulado_num": "Empenhado Anulado",
    "valorBaixadoBruto_num": "Baixado Bruto"
})

# Formatar valores em R$
for col in ["Empenhado Bruto", "Empenhado Anulado", "Baixado Bruto"]:
    comparativo_display[col] = comparativo_display[col].apply(
        lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )

st.subheader("📋 Tabela de valores por Exercício e Fonte")
st.dataframe(comparativo_display, use_container_width=True)
