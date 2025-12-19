import streamlit as st
import pandas as pd
import altair as alt
from auth import login
from components.header import render_header
from data_loader import load_empenhos  

# 🔐 Segurança
login()
render_header()

st.set_page_config(
    page_title="📂 Consulta por Despesa",
    layout="wide"
)

st.title("📂 Consulta por Despesa e Natureza")

# =======================
# CARREGAR DADOS
# =======================
df = load_empenhos()
if df.empty:
    st.warning("Nenhum dado de empenhos encontrado.")
    st.stop()

# =======================
# CARREGAR REFERÊNCIAS
# =======================
import os
referencias_files = [f for f in os.listdir("data") if f.endswith("_referencias.xlsx")]
if not referencias_files:
    st.warning("Nenhum arquivo de referências encontrado na pasta /data.")
    st.stop()

# Seleciona arquivo de referência (ex: 2025_referencias.xlsx)
arquivo_ref = st.selectbox("📄 Selecione o arquivo de referências", referencias_files)
referencias = pd.read_excel(os.path.join("data", arquivo_ref))

# =======================
# SUBSTITUIR CÓDIGOS PELAS DESCRIÇÕES
# =======================
# Merge com left join, mantendo apenas as correspondências
df = df.merge(
    referencias[[
        "anoEmpenho",
        "nomeEntidade",
        "numDespesa",
        "Descrição da despesa",
        "numNaturezaDesp",
        "Descrição da natureza"
    ]],
    how="left",
    left_on=["Ano", "nomeCredor", "numDespesa", "numNaturezaEmp"],
    right_on=["anoEmpenho", "nomeEntidade", "numDespesa", "numNaturezaDesp"]
)

# Substitui os códigos pelas descrições quando disponível
df["Despesa"] = df["Descrição da despesa"].fillna(df["numDespesa"])
df["Natureza"] = df["Descrição da natureza"].fillna(df["numNaturezaEmp"])

# =======================
# FILTRO POR EXERCÍCIO
# =======================
anos = sorted(df["Ano"].unique())
anos_sel = st.multiselect("📅 Selecione o(s) Exercício(s)", anos, default=anos)
df = df[df["Ano"].isin(anos_sel)]

# =======================
# FILTRO POR DESPESA
# =======================
despesas = sorted(df["Despesa"].dropna().unique())
despesas_sel = st.multiselect("📂 Selecione a(s) Despesa(s)", despesas)

if despesas_sel:
    df = df[df["Despesa"].isin(despesas_sel)]

# =======================
# AGRUPAMENTO
# =======================
comparativo = df.groupby(["Ano", "Despesa", "Natureza"], as_index=False)["valorEmpenhadoBruto_num"].sum()
if comparativo.empty:
    st.info("Nenhum dado para os filtros selecionados.")
    st.stop()

# =======================
# GRÁFICO
# =======================
graf = (
    alt.Chart(comparativo)
    .mark_bar(size=35)
    .encode(
        x=alt.X("Ano:N", title="Exercício"),
        xOffset=alt.XOffset("Despesa:N"),
        y=alt.Y("valorEmpenhadoBruto_num:Q", title="Valor Empenhado (R$)"),
        color=alt.Color("Natureza:N", title="Natureza"),
        tooltip=[
            "Ano:N",
            "Despesa:N",
            "Natureza:N",
            alt.Tooltip("valorEmpenhadoBruto_num:Q", format=",.2f")
        ]
    )
    .properties(height=420)
)

st.altair_chart(graf, use_container_width=True)

# =======================
# TABELA
# =======================
st.subheader("📄 Dados Detalhados")
tabela = comparativo.copy()
tabela["Valor Empenhado"] = tabela["valorEmpenhadoBruto_num"].apply(
    lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)
st.dataframe(tabela[["Ano", "Despesa", "Natureza", "Valor Empenhado"]], use_container_width=True)

# =======================
# DOWNLOAD CSV
# =======================
csv_bytes = comparativo.rename(columns={
    "Ano": "Exercício",
    "Despesa": "Despesa",
    "Natureza": "Natureza",
    "valorEmpenhadoBruto_num": "Valor Empenhado"
}).to_csv(index=False, sep=";", decimal=",", encoding="utf-8-sig")

st.download_button(
    "📥 Baixar CSV dos dados filtrados",
    csv_bytes,
    file_name="consulta_por_despesa_filtrada.csv",
    mime="text/csv"
)
