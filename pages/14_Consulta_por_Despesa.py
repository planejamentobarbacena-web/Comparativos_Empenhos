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

st.title("📂 Consulta por Despesa")

# =======================
# CARREGAR DADOS
# =======================
df = load_empenhos()
if df.empty:
    st.info("Nenhum dado encontrado.")
    st.stop()

# =======================
# CARREGAR REFERÊNCIAS
# =======================
referencias_path = os.path.join("data", f"{st.selectbox('Selecione arquivo de referência', [f for f in os.listdir('data') if f.endswith('_referencias.xlsx')])}")

try:
    referencias = pd.read_excel(referencias_path)
except Exception as e:
    st.error(f"Erro ao carregar arquivo de referência: {e}")
    st.stop()

# =======================
# PADRONIZAÇÃO DE TIPOS
# =======================
df["Ano"] = df["Ano"].astype(int)
df["numDespesa"] = df["numDespesa"].astype(int)
df["numNaturezaEmp"] = df["numNaturezaEmp"].astype(int)
df["nomeCredor"] = df["nomeCredor"].str.strip().str.upper()

referencias["anoEmpenho"] = referencias["anoEmpenho"].astype(int)
referencias["numDespesa"] = referencias["numDespesa"].astype(int)
referencias["numNaturezaDesp"] = referencias["numNaturezaDesp"].astype(int)
referencias["nomeEntidade"] = referencias["nomeEntidade"].str.strip().str.upper()

# =======================
# MERGE COM DESCRIÇÕES
# =======================
df = df.merge(
    referencias[["anoEmpenho","nomeEntidade","numDespesa","Descrição da despesa",
                 "numNaturezaDesp","Descrição da natureza"]],
    how="left",
    left_on=["Ano","nomeCredor","numDespesa","numNaturezaEmp"],
    right_on=["anoEmpenho","nomeEntidade","numDespesa","numNaturezaDesp"]
)

# =======================
# CRIAR COLUNAS COM DESCRIÇÕES
# =======================
df["Despesa"] = df["Descrição da despesa"].fillna(df["numDespesa"])
df["Natureza"] = df["Descrição da natureza"].fillna(df["numNaturezaEmp"])

# =======================
# FILTRO POR EXERCÍCIO
# =======================
anos = sorted(df["Ano"].unique())
anos_sel = st.multiselect(
    "📅 Selecione o(s) Exercício(s)",
    anos,
    default=anos
)
df = df[df["Ano"].isin(anos_sel)]

# =======================
# FILTRO POR DESPESA
# =======================
despesas = sorted(df["Despesa"].dropna().unique())
despesas_sel = st.multiselect(
    "📂 Selecione a(s) Despesa(s)",
    despesas
)
if despesas_sel:
    df = df[df["Despesa"].isin(despesas_sel)]

# =======================
# FILTRO POR NATUREZA
# =======================
naturezas = sorted(df["Natureza"].dropna().unique())
naturezas_sel = st.multiselect(
    "📂 Selecione a(s) Natureza(s)",
    naturezas
)
if naturezas_sel:
    df = df[df["Natureza"].isin(naturezas_sel)]

# =======================
# AGRUPAMENTO PARA GRÁFICO
# =======================
comparativo = (
    df.groupby(["Ano","Despesa","Natureza"], as_index=False)["valorEmpenhadoBruto_num"]
    .sum()
)

if comparativo.empty:
    st.info("Nenhum dado encontrado com os filtros selecionados.")
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
# TABELA DETALHADA
# =======================
st.subheader("📄 Dados Detalhados")
tabela = comparativo.copy()
tabela["Valor Empenhado"] = tabela["valorEmpenhadoBruto_num"].apply(
    lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)
tabela = tabela[["Ano","Despesa","Natureza","Valor Empenhado"]]
st.dataframe(tabela, use_container_width=True)

# =======================
# DOWNLOAD CSV
# =======================
csv_bytes = comparativo.rename(columns={
    "Ano":"Exercício",
    "Despesa":"Despesa",
    "Natureza":"Natureza",
    "valorEmpenhadoBruto_num":"Valor Empenhado"
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
