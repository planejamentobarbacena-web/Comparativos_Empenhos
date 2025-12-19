import streamlit as st
import pandas as pd
import altair as alt
import os
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
referencias_files = [f for f in os.listdir("data") if f.endswith("_referencias.xlsx")]

referencias_file = st.selectbox(
    "Selecione o arquivo de referências",
    options=referencias_files
)

referencias = pd.read_excel(f"data/{referencias_file}")

# =======================
# PADRONIZAÇÃO PARA MERGE
# =======================
for col in ["anoEmpenho","numDespesa","nomeEntidade"]:
    df[col] = df.get(col, df["Ano"]).astype(str) if col == "anoEmpenho" else df[col].astype(str)
    referencias[col] = referencias[col].astype(str)

df["numNaturezaEmp"] = df["numNaturezaEmp"].astype(str)
referencias["numNaturezaDesp"] = referencias["numNaturezaDesp"].astype(str)
df["nomeEntidade"] = df["nomeEntidade"].str.strip()
referencias["nomeEntidade"] = referencias["nomeEntidade"].str.strip()

# =======================
# MERGE COM DESCRIÇÕES
# =======================
df = df.merge(
    referencias[[
        "anoEmpenho",
        "numDespesa",
        "numNaturezaDesp",
        "nomeEntidade",
        "Descrição da despesa",
        "Descrição da natureza"
    ]],
    how="left",
    left_on=["anoEmpenho","numDespesa","numNaturezaEmp","nomeEntidade"],
    right_on=["anoEmpenho","numDespesa","numNaturezaDesp","nomeEntidade"]
)

# =======================
# FILTRO POR EXERCÍCIO
# =======================
anos = sorted(df["anoEmpenho"].unique())
anos_sel = st.multiselect(
    "📅 Selecione o(s) Exercício(s)",
    anos,
    default=anos
)
df = df[df["anoEmpenho"].isin(anos_sel)]

# =======================
# FILTRO POR DESPESA E NATUREZA
# =======================
despesas = sorted(df["Descrição da despesa"].dropna().unique())
despesa_sel = st.multiselect("📂 Despesas", despesas)

naturezas = sorted(df["Descrição da natureza"].dropna().unique())
natureza_sel = st.multiselect("📂 Naturezas", naturezas)

if despesa_sel:
    df = df[df["Descrição da despesa"].isin(despesa_sel)]
if natureza_sel:
    df = df[df["Descrição da natureza"].isin(natureza_sel)]

# =======================
# AGRUPAMENTO
# =======================
comparativo = df.groupby(
    ["anoEmpenho", "Descrição da despesa", "Descrição da natureza"],
    as_index=False
)["valorEmpenhadoBruto_num"].sum()

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
        x=alt.X("anoEmpenho:N", title="Exercício"),
        xOffset=alt.XOffset("Descrição da despesa:N"),
        y=alt.Y("valorEmpenhadoBruto_num:Q", title="Valor Empenhado (R$)"),
        color=alt.Color("Descrição da natureza:N", title="Natureza"),
        tooltip=[
            "anoEmpenho:N",
            "Descrição da despesa:N",
            "Descrição da natureza:N",
            alt.Tooltip("valorEmpenhadoBruto_num:Q", format=",.2f")
        ]
    )
    .properties(height=420)
)

st.altair_chart(graf, use_container_width=True)

# =======================
# TABELA DETALHADA
# =======================
st.subheader("📄 Dados Detalhados")

tabela = comparativo.copy()
tabela["Valor Empenhado"] = tabela["valorEmpenhadoBruto_num"].apply(
    lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)
tabela = tabela[["anoEmpenho", "Descrição da despesa", "Descrição da natureza", "Valor Empenhado"]]

st.dataframe(tabela, use_container_width=True)

# =======================
# DOWNLOAD CSV
# =======================
csv_bytes = comparativo.rename(columns={
    "anoEmpenho": "Exercício",
    "Descrição da despesa": "Despesa",
    "Descrição da natureza": "Natureza",
    "valorEmpenhadoBruto_num": "Valor Empenhado"
}).to_csv(
    index=False,
    sep=";",
    decimal=",",
    encoding="utf-8-sig"
)

st.download_button(
    "📥 Baixar CSV dos dados filtrados",
    csv_bytes,
    file_name="consulta_por_despesa_filtrada.csv",
    mime="text/csv"
)
