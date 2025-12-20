import streamlit as st
import altair as alt

from auth import login
from components.header import render_header
from data_loader import load_empenhos

# ======================================================
# CONFIGURAÇÃO DA PÁGINA
# ======================================================
st.set_page_config(
    page_title="Painel de Empenhos",
    page_icon="📊",
    layout="wide"
)

# ======================================================
# SEGURANÇA
# ======================================================
login()
render_header()

# ======================================================
# CARREGAMENTO DOS DADOS
# ======================================================
df = load_empenhos()

if df.empty:
    st.warning("Nenhum dado carregado.")
    st.stop()

df = df.copy()

# ======================================================
# AJUSTE DE COLUNAS (EVITA KeyError)
# ======================================================

# Exercício
if "anoEmpenho" not in df.columns:
    st.error("Coluna 'anoEmpenho' não encontrada.")
    st.stop()

# Entidade
if "nomeEntidade" not in df.columns:
    st.error("Coluna 'nomeEntidade' não encontrada.")
    st.stop()

# Empenhado
if "valorEmpenhadoBruto" not in df.columns:
    st.error("Coluna 'valorEmpenhadoBruto' não encontrada.")
    st.stop()

# Anulado
if "valorEmpenhadoAnulado" not in df.columns:
    df["valorEmpenhadoAnulado"] = 0

# Baixado (nome varia no seu CSV)
if "valorBaixadoBruto" not in df.columns:
    if "saldoBaixado" in df.columns:
        df["valorBaixadoBruto"] = df["saldoBaixado"]
    else:
        df["valorBaixadoBruto"] = 0

# Limpeza básica
df["nomeEntidade"] = df["nomeEntidade"].fillna("")
df["anoEmpenho"] = df["anoEmpenho"].fillna("")

# ======================================================
# TÍTULO
# ======================================================
st.title("📊 Painel de Empenhos – Visão Geral")

st.markdown(
    "Análise consolidada de **Empenhado, Anulado e Baixado no Exercício**, "
    "com filtros simples por **Exercício** e **Entidade**."
)

# ======================================================
# MÉTRICAS
# ======================================================
total_empenhado = df["valorEmpenhadoBruto"].sum()
total_anulado   = df["valorEmpenhadoAnulado"].sum()
total_baixado   = df["valorBaixadoBruto"].sum()

c1, c2, c3 = st.columns(3)

c1.metric("💰 Total Empenhado", f"R$ {total_empenhado:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
c2.metric("❌ Total Anulado", f"R$ {total_anulado:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
c3.metric("✅ Total Baixado no Exercício", f"R$ {total_baixado:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

# ======================================================
# FILTROS (ENTRE MÉTRICAS E GRÁFICO)
# ======================================================
st.markdown("---")

f1, f2 = st.columns(2)

with f1:
    anos = sorted(df["anoEmpenho"].dropna().unique())
    ano_sel = st.selectbox("📅 Exercício", ["Todos"] + anos)

with f2:
    entidades = sorted(df["nomeEntidade"].unique())
    ent_sel = st.selectbox("🏛️ Entidade", ["Todas"] + entidades)

df_filtro = df.copy()

if ano_sel != "Todos":
    df_filtro = df_filtro[df_filtro["anoEmpenho"] == ano_sel]

if ent_sel != "Todas":
    df_filtro = df_filtro[df_filtro["nomeEntidade"] == ent_sel]

if df_filtro.empty:
    st.info("Nenhum dado para os filtros selecionados.")
    st.stop()

# ======================================================
# GRÁFICO
# ======================================================
st.markdown("### 📊 Empenhado × Anulado × Baixado no Exercício")

graf = (
    alt.Chart(df_filtro)
    .transform_fold(
        ["valorEmpenhadoBruto", "valorEmpenhadoAnulado", "valorBaixadoBruto"],
        as_=["Tipo", "Valor"]
    )
    .transform_calculate(
        TipoLabel="""
            datum.Tipo == 'valorEmpenhadoBruto' ? 'Empenhado' :
            datum.Tipo == 'valorEmpenhadoAnulado' ? 'Anulado' :
            'Baixado no Exercício'
        """
    )
    .mark_bar(size=45)
    .encode(
        x=alt.X("TipoLabel:N", title="Tipo"),
        xOffset=alt.XOffset("anoEmpenho:N", title="Exercício"),
        y=alt.Y("sum(Valor):Q", title="Valor (R$)"),
        color=alt.Color("anoEmpenho:N", title="Exercício"),
        tooltip=[
            "anoEmpenho:N",
            "TipoLabel:N",
            alt.Tooltip("sum(Valor):Q", format=",.2f")
        ]
    )
    .properties(height=420)
)

st.altair_chart(graf, use_container_width=True)

# ======================================================
# TABELA
# ======================================================
st.markdown("### 📄 Resumo")

tabela = (
    df_filtro
    .groupby(["anoEmpenho", "nomeEntidade"], as_index=False)[
        ["valorEmpenhadoBruto", "valorEmpenhadoAnulado", "valorBaixadoBruto"]
    ]
    .sum()
)

for col in ["valorEmpenhadoBruto", "valorEmpenhadoAnulado", "valorBaixadoBruto"]:
    tabela[col] = tabela[col].apply(
        lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )

tabela.columns = [
    "Exercício",
    "Entidade",
    "Empenhado",
    "Anulado",
    "Baixado no Exercício"
]

st.dataframe(tabela, use_container_width=True)
