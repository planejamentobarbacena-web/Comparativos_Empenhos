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
# CARREGAR EMPENHOS
# =======================
df = load_empenhos()
if df.empty:
    st.warning("Nenhum dado de empenho encontrado.")
    st.stop()

# =======================
# CARREGAR REFERÊNCIAS
# =======================
@st.cache_data(show_spinner="📂 Carregando referências...")
def load_referencias():
    arquivos = [f for f in os.listdir("data") if f.endswith("_referencias.xlsx")]
    if not arquivos:
        return pd.DataFrame()
    df_list = []
    for arq in arquivos:
        caminho = os.path.join("data", arq)
        xls = pd.ExcelFile(caminho)
        for aba in xls.sheet_names:
            df_ref = pd.read_excel(xls, sheet_name=aba)
            df_list.append(df_ref)
    if df_list:
        df_all = pd.concat(df_list, ignore_index=True)
        for col in ["nomeEntidade", "Descrição da despesa", "Descrição da natureza"]:
            if col in df_all.columns:
                df_all[col] = df_all[col].astype(str).str.strip()
        return df_all
    return pd.DataFrame()

referencias = load_referencias()

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
# MESCLAR COM REFERÊNCIAS
# =======================
if not referencias.empty:
    df = df.merge(
        referencias[["anoEmpenho","nomeEntidade","numDespesa","Descrição da despesa",
                     "numNaturezaDesp","Descrição da natureza"]],
        how="left",
        left_on=["Ano","numDespesa","numNaturezaEmp","nomeCredor"],
        right_on=["anoEmpenho","numDespesa","numNaturezaDesp","nomeEntidade"]
    )
else:
    df["Descrição da despesa"] = df["numDespesa"].astype(str)
    df["Descrição da natureza"] = df["numNaturezaEmp"].astype(str)

# =======================
# FILTRO POR DESPESA E NATUREZA
# =======================
despesas = sorted(df["Descrição da despesa"].dropna().unique())
naturezas = sorted(df["Descrição da natureza"].dropna().unique())

despesas_sel = st.multiselect("📂 Selecione a(s) Despesa(s)", despesas, default=despesas)
naturezas_sel = st.multiselect("📂 Selecione a(s) Natureza(s)", naturezas, default=naturezas)

df_sel = df[
    df["Descrição da despesa"].isin(despesas_sel) &
    df["Descrição da natureza"].isin(naturezas_sel)
].copy()

if df_sel.empty:
    st.info("Nenhum dado encontrado para os filtros selecionados.")
    st.stop()

# =======================
# AGRUPAMENTO PARA GRÁFICO
# =======================
comparativo = (
    df_sel
    .groupby(["Ano","Descrição da despesa","Descrição da natureza"], as_index=False)["valorEmpenhadoBruto_num"]
    .sum()
)

# =======================
# GRÁFICO
# =======================
graf = (
    alt.Chart(comparativo)
    .mark_bar(size=35)
    .encode(
        x=alt.X("Ano:N", title="Exercício"),
        xOffset=alt.XOffset("Descrição da despesa:N"),
        y=alt.Y("valorEmpenhadoBruto_num:Q", title="Valor Empenhado (R$)"),
        color=alt.Color("Descrição da natureza:N", title="Natureza"),
        tooltip=[
            "Ano:N",
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
tabela = df_sel[["Ano","numDespesa","Descrição da despesa","numNaturezaEmp","Descrição da natureza","valorEmpenhadoBruto_num","nomeCredor"]].copy()
tabela["Valor Empenhado"] = tabela["valorEmpenhadoBruto_num"].apply(
    lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)
st.dataframe(tabela, use_container_width=True)

# =======================
# DOWNLOAD CSV
# =======================
csv_bytes = tabela.rename(columns={
    "Ano":"Exercício",
    "numDespesa":"Código Despesa",
    "Descrição da despesa":"Despesa",
    "numNaturezaEmp":"Código Natureza",
    "Descrição da natureza":"Natureza",
    "valorEmpenhadoBruto_num":"Valor Empenhado",
    "nomeCredor":"Entidade"
}).to_csv(index=False, sep=";", decimal=",", encoding="utf-8-sig")

st.download_button(
    "📥 Baixar CSV dos dados filtrados",
    csv_bytes,
    file_name="consulta_por_despesa_filtrada.csv",
    mime="text/csv"
)
