import streamlit as st
import os
import json
import altair as alt

from auth import login, exige_admin
from components.header import render_header
from data_loader import load_empenhos_xlsx

# 🔐 Segurança
login()
render_header()

st.title("📁 Consulta por Credor")

# Carregar dados
# Carregar dados
df = load_empenhos_xlsx()
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

# =======================
# GRÁFICO
# =======================
graf = (
    alt.Chart(comparativo)
    .mark_bar(size=35)
    .encode(
        x=alt.X(
            "Ano:N",
            title="Exercício"
        ),
        xOffset=alt.XOffset(
            "nomeCredor:N",
            title="Credor"
        ),
        y=alt.Y(
            "valorEmpenhadoBruto_num:Q",
            title="Valor Empenhado (R$)"
        ),
        color=alt.Color(
            "nomeCredor:N",
            title="Credor"
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

st.subheader("📊 Detalhamento por Exercício e Credor")

tabela = comparativo.copy()

tabela["Valor Empenhado"] = tabela["valorEmpenhadoBruto_num"].apply(
    lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)
# DOWNLOAD CSV (FILTRADO)
# =======================
st.divider()

csv_download = comparativo.rename(columns={
    "Ano": "Exercício",
    "nomeCredor": "Credor",
    "valorEmpenhadoBruto_num": "Valor Empenhado"
})

csv_bytes = csv_download.to_csv(
    index=False,
    sep=";",
    decimal=",",
    encoding="utf-8-sig"
)

st.download_button(
    label="📥 Baixar CSV dos dados filtrados",
    data=csv_bytes,
    file_name="consulta_por_credor_filtrada.csv",
    mime="text/csv"
)

tabela = tabela[["Ano", "nomeCredor", "Valor Empenhado"]]

st.dataframe(tabela, use_container_width=True)

