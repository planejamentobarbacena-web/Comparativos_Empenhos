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

st.title("📁 Consulta por Credor")

# Carregar dados
# Carregar dados
df = load_empenhos()
if df.empty:
    st.warning("Nenhum dado carregado.")
    st.stop()

# =======================
# FILTRO POR EXERCÍCIO
# =======================
anos_disponiveis = sorted(df["Ano"].unique())

anos_selecionados = st.multiselect(
    "📅 Selecione o(s) Exercício(s)",
    anos_disponiveis,
    default=anos_disponiveis  # começa com todos
)

if anos_selecionados:
    df = df[df["Ano"].isin(anos_selecionados)]


# =======================
# FILTRO POR CREDOR
# =======================
lista_credores = sorted(df["nomeCredor"].dropna().unique())

credores_selecionados = st.multiselect(
    "🏢 Selecione o(s) Credor(es)",
    lista_credores
)

if credores_selecionados:
    df_sel = df[df["nomeCredor"].isin(credores_selecionados)]
else:
    df_sel = df.copy()


comparativo = (
    df_sel
    .groupby(["Ano", "nomeCredor"], as_index=False)["valorEmpenhadoBruto_num"]
    .sum()
)


# Renomear colunas para exibição
comparativo_display = comparativo.rename(columns={
    "valorEmpenhadoBruto_num": "Empenhado Bruto",
    "valorEmpenhadoAnulado_num": "Empenhado Anulado",
    "valorBaixadoBruto_num": "Baixado Bruto"
})

# Melt para gráfico
df_melt = comparativo.melt(id_vars="Ano", var_name="Tipo", value_name="Valor")
df_melt["Tipo"] = df_melt["Tipo"].map({
    "valorEmpenhadoBruto_num": "Empenhado Bruto",
    "valorEmpenhadoAnulado_num": "Empenhado Anulado",
    "valorBaixadoBruto_num": "Baixado Bruto"
})

# =======================
# GRÁFICO
# =======================
graf = (
    alt.Chart(comparativo)
    .mark_bar(size=40)
    .encode(
        x=alt.X(
            "nomeCredor:N",
            title="Credor",
            sort="-y"
        ),
        xOffset=alt.XOffset(
            "Ano:N",
            title="Exercício"
        ),
        y=alt.Y(
            "valorEmpenhadoBruto_num:Q",
            title="Valor Empenhado (R$)"
        ),
        color=alt.Color(
            "Ano:N",
            title="Exercício"
        ),
        tooltip=[
            "Ano:N",
            "nomeCredor:N",
            alt.Tooltip("valorEmpenhadoBruto_num:Q", format=",.2f")
        ]
    )
    .properties(height=420)
)

st.altair_chart(graf, use_container_width=True)

# =======================
# TABELA ABAIXO DO GRÁFICO
# =======================
comparativo_display_format = comparativo_display.copy()

for col in ["Empenhado Bruto", "Empenhado Anulado", "Baixado Bruto"]:
    comparativo_display_format[col] = comparativo_display_format[col].apply(
        lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )

st.dataframe(comparativo_display_format, use_container_width=True)
