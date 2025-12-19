import streamlit as st
import altair as alt

from auth import login
from components.header import render_header
from data_loader import load_empenhos  

# 🔐 Segurança
login()
render_header()

st.title("📑 Consulta por Despesa")

# =======================
# CARREGAR DADOS
# =======================
df = load_empenhos()
if df.empty:
    st.warning("Nenhum dado carregado.")
    st.stop()

# =======================
# CÁLCULOS
# =======================
df["empenhado_liquido"] = (
    df["valorEmpenhadoBruto_num"] - df["valorEmpenhadoAnulado_num"]
)

# =======================
# FILTRO EXERCÍCIO
# =======================
anos = sorted(df["Ano"].unique())
anos_sel = st.multiselect(
    "📅 Exercício",
    anos,
    default=anos
)
df = df[df["Ano"].isin(anos_sel)]

# =======================
# FILTRO ENTIDADE
# =======================
entidades = sorted(df["nomeEntidade"].dropna().unique())
entidades_sel = st.multiselect(
    "🏛️ Entidade",
    entidades
)
if entidades_sel:
    df = df[df["nomeEntidade"].isin(entidades_sel)]

# =======================
# FILTRO DESCRIÇÃO DA DESPESA
# =======================
despesas = sorted(df["Descrição da despesa"].dropna().unique())
despesas_sel = st.multiselect(
    "📌 Descrição da Despesa",
    despesas
)
if despesas_sel:
    df = df[df["Descrição da despesa"].isin(despesas_sel)]

# =======================
# FILTRO CREDOR
# =======================
credores = sorted(df["nomeCredor"].dropna().unique())
credores_sel = st.multiselect(
    "🏢 Credor",
    credores
)
if credores_sel:
    df = df[df["nomeCredor"].isin(credores_sel)]

# =======================
# FILTRO FONTE
# =======================
fontes = sorted(df["numRecurso"].dropna().unique())
fontes_sel = st.multiselect(
    "💰 Fonte de Recurso",
    fontes
)
if fontes_sel:
    df = df[df["numRecurso"].isin(fontes_sel)]

# =======================
# AGRUPAMENTO
# =======================
comparativo = (
    df
    .groupby(
        ["Ano", "Descrição da despesa"],
        as_index=False
    )
    .agg({
        "empenhado_liquido": "sum",
        "saldoBaixado": "sum"
    })
)

if comparativo.empty:
    st.info("Nenhum dado encontrado para os filtros selecionados.")
    st.stop()

# =======================
# TRANSFORMA PARA GRÁFICO
# =======================
graf_df = comparativo.melt(
    id_vars=["Ano", "Descrição da despesa"],
    value_vars=["empenhado_liquido", "saldoBaixado"],
    var_name="Tipo",
    value_name="Valor"
)

mapa_tipos = {
    "empenhado_liquido": "Empenhado Líquido",
    "saldoBaixado": "Saldo Baixado"
}

graf_df["Tipo"] = graf_df["Tipo"].map(mapa_tipos)

# =======================
# GRÁFICO
# =======================
graf = (
    alt.Chart(graf_df)
    .mark_bar(size=28)
    .encode(
        x=alt.X("Ano:N", title="Exercício"),
        xOffset=alt.XOffset("Tipo:N"),
        y=alt.Y("Valor:Q", title="Valor (R$)"),
        color=alt.Color("Tipo:N", title="Tipo"),
        tooltip=[
            "Ano:N",
            "Descrição da despesa:N",
            "Tipo:N",
            alt.Tooltip("Valor:Q", format=",.2f")
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

tabela["Empenhado Líquido"] = tabela["empenhado_liquido"].apply(
    lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)

tabela["Saldo Baixado"] = tabela["saldoBaixado"].apply(
    lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)

tabela = tabela[
    ["Ano", "Descrição da despesa", "Empenhado Líquido", "Saldo Baixado"]
]

st.dataframe(tabela, use_container_width=True)

# =======================
# DOWNLOAD CSV
# =======================
st.divider()

csv_bytes = comparativo.rename(columns={
    "Ano": "Exercício",
    "Descrição da despesa": "Despesa",
    "empenhado_liquido": "Empenhado Líquido",
    "saldoBaixado": "Saldo Baixado"
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
