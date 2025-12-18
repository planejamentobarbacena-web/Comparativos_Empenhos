import streamlit as st
import altair as alt

from auth import login
from components.header import render_header
from data_loader import load_empenhos  

# 🔐 Segurança
login()
render_header()

st.title("💰 Consulta por Fonte de Recurso")

# =======================
# CARREGAR DADOS
# =======================
df = load_empenhos()
if df.empty:
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
# FILTRO POR FONTE
# =======================
fontes = sorted(df["numRecurso"].dropna().unique())

fontes_sel = st.multiselect(
    "💰 Selecione a(s) Fonte(s)",
    fontes
)

if fontes_sel:
    df_sel = df[df["numRecurso"].isin(fontes_sel)]
else:
    df_sel = df.copy()

# =======================
# AGRUPAMENTO
# =======================
comparativo = (
    df_sel
    .groupby(["Ano", "numRecurso"], as_index=False)["valorEmpenhadoBruto_num"]
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
        xOffset=alt.XOffset("numRecurso:N", title="Fonte"),
        y=alt.Y("valorEmpenhadoBruto_num:Q", title="Valor Empenhado (R$)"),
        color=alt.Color("numRecurso:N", title="Fonte"),
        tooltip=[
            "Ano:N",
            "numRecurso:N",
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

tabela = tabela[["Ano", "numRecurso", "Valor Empenhado"]]
st.dataframe(tabela, use_container_width=True)

# =======================
# DOWNLOAD CSV
# =======================
st.divider()

csv_bytes = comparativo.rename(columns={
    "Ano": "Exercício",
    "numRecurso": "Fonte",
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
    file_name="consulta_por_fonte_filtrada.csv",
    mime="text/csv"
)
