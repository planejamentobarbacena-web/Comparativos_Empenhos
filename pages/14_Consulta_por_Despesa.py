import streamlit as st
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

st.title("📂 Consulta por Despesa")

# =======================
# CARREGAR DADOS
# =======================
df = load_empenhos()
if df.empty:
    st.info("Nenhum dado encontrado.")
    st.stop()

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
# FILTRO POR ENTIDADE
# =======================
entidades = sorted(df["nomeEntidade"].dropna().unique())
entidades_sel = st.multiselect(
    "🏢 Selecione a(s) Entidade(s)",
    entidades
)
if entidades_sel:
    df = df[df["nomeEntidade"].isin(entidades_sel)]

# =======================
# FILTRO POR DESPESA
# =======================
despesas = sorted(df["numDespesa"].dropna().unique())
despesas_sel = st.multiselect(
    "📂 Selecione a(s) Despesa(s)",
    despesas
)
if despesas_sel:
    df = df[df["numDespesa"].isin(despesas_sel)]

# =======================
# FILTRO POR NATUREZA
# =======================
naturezas = sorted(df["numNaturezaEmp"].dropna().unique())
naturezas_sel = st.multiselect(
    "📂 Selecione a(s) Natureza(s)",
    naturezas
)
if naturezas_sel:
    df = df[df["numNaturezaEmp"].isin(naturezas_sel)]

# =======================
# AGRUPAMENTO PARA GRÁFICO
# =======================
comparativo = (
    df.groupby(["Ano","nomeEntidade","numDespesa","numNaturezaEmp"], as_index=False)["valorEmpenhadoBruto_num"]
    .sum()
)

if comparativo.empty:
    st.info("Nenhum dado encontrado com os filtros selecionados.")
    st.stop()

# =======================
# GRÁFICO COM ENTIDADES DIFERENCIADAS
# =======================
graf = (
    alt.Chart(comparativo)
    .mark_bar(size=30)
    .encode(
        x=alt.X("Ano:N", title="Exercício"),
        xOffset=alt.XOffset("numDespesa:N"),
        y=alt.Y("valorEmpenhadoBruto_num:Q", title="Valor Empenhado (R$)"),
        color=alt.Color("nomeEntidade:N", title="Entidade"),
        tooltip=[
            "Ano:N",
            "nomeEntidade:N",
            "numDespesa:N",
            "numNaturezaEmp:N",
            alt.Tooltip("valorEmpenhadoBruto_num:Q", format=",.2f")
        ]
    )
    .properties(height=450)
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
tabela = tabela[["Ano","nomeEntidade","numDespesa","numNaturezaEmp","Valor Empenhado"]]
st.dataframe(tabela, use_container_width=True)

# =======================
# DOWNLOAD CSV
# =======================
csv_bytes = comparativo.rename(columns={
    "Ano":"Exercício",
    "nomeEntidade":"Entidade",
    "numDespesa":"Despesa",
    "numNaturezaEmp":"Natureza",
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
