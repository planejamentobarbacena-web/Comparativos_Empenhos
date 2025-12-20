import streamlit as st
import pandas as pd
import altair as alt

# =========================================================
# CONFIGURAÇÃO DA PÁGINA
# =========================================================
st.set_page_config(
    page_title="Consulta por Despesa",
    layout="wide"
)

st.title("📊 Consulta por Despesa")

# =========================================================
# CARREGAMENTO DOS DADOS
# =========================================================
@st.cache_data
def load_empenhos():
    try:
        return pd.read_csv("data/empenhos_tratados.csv")
    except Exception:
        return pd.DataFrame()

df = load_empenhos()

if df.empty:
    st.warning("⚠️ Nenhum dado carregado.")
    st.stop()

# =========================================================
# TRATAMENTO BÁSICO
# =========================================================
colunas_necessarias = [
    "anoEmpenho",
    "nomeEntidade",
    "descricaoDespesa",
    "nomeCredor",
    "numRecurso",
    "valorEmpenhadoLiquido",
    "valorBaixadoBruto"
]

df = df[colunas_necessarias].copy()

df = df.fillna("")
df = df[df["anoEmpenho"] != ""]
df = df[df["nomeEntidade"] != ""]

# =========================================================
# FILTROS
# =========================================================
st.subheader("🔎 Filtros")

c1, c2, c3, c4 = st.columns(4)

with c1:
    exercicios = sorted(df["anoEmpenho"].unique())
    ano_sel = st.selectbox("Exercício", exercicios)

with c2:
    entidades = sorted(df["nomeEntidade"].unique())
    entidade_sel = st.selectbox("Entidade", entidades)

with c3:
    despesas = sorted(df["descricaoDespesa"].unique())
    despesa_sel = st.selectbox("Despesa", despesas)

with c4:
    credores = sorted(df["nomeCredor"].unique())
    credor_sel = st.selectbox("Credor", credores)

df_filtro = df[
    (df["anoEmpenho"] == ano_sel) &
    (df["nomeEntidade"] == entidade_sel) &
    (df["descricaoDespesa"] == despesa_sel) &
    (df["nomeCredor"] == credor_sel)
]

if df_filtro.empty:
    st.info("Nenhum registro encontrado para os filtros selecionados.")
    st.stop()

# =========================================================
# AGREGAÇÃO
# =========================================================
comparativo = (
    df_filtro
    .groupby("anoEmpenho", as_index=False)
    .agg(
        empenhado_liquido=("valorEmpenhadoLiquido", "sum"),
        saldoBaixado=("valorBaixadoBruto", "sum")
    )
)

# =========================================================
# GRÁFICO
# =========================================================
st.subheader("📈 Empenhado Líquido x Baixado no Exercício")

graf = (
    alt.Chart(comparativo)
    .transform_fold(
        ["empenhado_liquido", "saldoBaixado"],
        as_=["Tipo", "Valor"]
    )
    .mark_bar(size=36)
    .encode(
        x=alt.X(
            "anoEmpenho:N",
            title="Exercício",
            axis=alt.Axis(labelAngle=0)
        ),
        xOffset="Tipo:N",
        y=alt.Y(
            "Valor:Q",
            title="Valor (R$)"
        ),
        color=alt.Color(
            "Tipo:N",
            title="Tipo",
            legend=alt.Legend(
                orient="bottom",
                direction="horizontal"
            ),
            scale=alt.Scale(
                domain=["empenhado_liquido", "saldoBaixado"],
                range=["#1f77b4", "#ff7f0e"]
            )
        ),
        tooltip=[
            "anoEmpenho:N",
            "Tipo:N",
            alt.Tooltip("Valor:Q", format=",.2f")
        ]
    )
    .properties(height=420)
)

st.altair_chart(graf, use_container_width=True)

# =========================================================
# TABELA
# =========================================================
st.subheader("📋 Dados Consolidados")

tabela = comparativo.copy()
tabela["Empenhado Líquido (R$)"] = tabela["empenhado_liquido"]
tabela["Baixado no Exercício (R$)"] = tabela["saldoBaixado"]

st.dataframe(
    tabela[[
        "anoEmpenho",
        "Empenhado Líquido (R$)",
        "Baixado no Exercício (R$)"
    ]],
    use_container_width=True
)
