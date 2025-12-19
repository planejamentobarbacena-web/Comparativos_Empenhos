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

st.title("📂 Consulta por Despesa com Referências")

# =======================
# CARREGAR DADOS
# =======================
df_empenhos = load_empenhos()
if df_empenhos.empty:
    st.warning("Nenhum dado de empenhos encontrado.")
    st.stop()

# =======================
# FILTRO POR EXERCÍCIO
# =======================
anos = sorted(df_empenhos["Ano"].unique())
anos_sel = st.multiselect(
    "📅 Selecione o(s) Exercício(s)",
    anos,
    default=anos
)
df_empenhos = df_empenhos[df_empenhos["Ano"].isin(anos_sel)]

# =======================
# CARREGAR ARQUIVOS DE REFERÊNCIA
# =======================
referencias = pd.DataFrame()

for ano in anos_sel:
    file_path = os.path.join("data", f"{ano}_referencias.xlsx")
    if os.path.exists(file_path):
        df_ref = pd.read_excel(file_path, dtype=str)
        referencias = pd.concat([referencias, df_ref], ignore_index=True)

if referencias.empty:
    st.warning("Nenhum arquivo de referência encontrado para os exercícios selecionados.")
    st.stop()

# =======================
# MERGE PARA SUBSTITUIR CÓDIGOS PELAS DESCRIÇÕES
# =======================
df = df_empenhos.merge(
    referencias[["anoEmpenho","nomeEntidade","numDespesa","numNaturezaDesp",
                 "Descrição da despesa","Descrição da natureza"]],
    how="left",
    left_on=["Ano","nomeEntidade","numDespesa","numNaturezaEmp"],
    right_on=["anoEmpenho","nomeEntidade","numDespesa","numNaturezaDesp"]
)

# Substituir códigos pelas descrições (apenas para exibição)
df["numDespesa"] = df["Descrição da despesa"].fillna(df["numDespesa"])
df["numNaturezaEmp"] = df["Descrição da natureza"].fillna(df["numNaturezaEmp"])

# =======================
# FILTRO POR DESPESA
# =======================
despesas = sorted(df["numDespesa"].dropna().unique())
despesas_sel = st.multiselect("📂 Selecione a(s) Despesa(s)", despesas)

if despesas_sel:
    df = df[df["numDespesa"].isin(despesas_sel)]

# =======================
# AGRUPAMENTO
# =======================
comparativo = (
    df.groupby(["Ano","numDespesa","numNaturezaEmp"], as_index=False)["valorEmpenhadoBruto_num"]
    .sum()
)

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
        xOffset=alt.XOffset("numDespesa:N", title="Despesa"),
        y=alt.Y("valorEmpenhadoBruto_num:Q", title="Valor Empenhado (R$)"),
        color=alt.Color("numDespesa:N", title="Despesa"),
        tooltip=[
            "Ano:N",
            "numDespesa:N",
            "numNaturezaEmp:N",
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
tabela = tabela[["Ano","numDespesa","numNaturezaEmp","Valor Empenhado"]]
st.dataframe(tabela, use_container_width=True)

# =======================
# DOWNLOAD CSV
# =======================
csv_bytes = comparativo.rename(columns={
    "Ano": "Exercício",
    "numDespesa": "Despesa",
    "numNaturezaEmp": "Natureza",
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
