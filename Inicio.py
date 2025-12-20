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

# ======================================================
# VALIDAÇÃO DAS COLUNAS OBRIGATÓRIAS
# ======================================================
colunas_necessarias = [
    "nomeEntidade",
    "anoEmpenho",
    "valorEmpenhadoBruto",
    "valorEmpenhadoAnulado",
    "valorBaixadoBruto"
]

faltando = [c for c in colunas_necessarias if c not in df.columns]

if faltando:
    st.error(f"Colunas ausentes no arquivo: {', '.join(faltando)}")
    st.stop()

# ======================================================
# TRATAMENTO BÁSICO
# ======================================================
df = df.copy()
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
# MÉTRICAS GERAIS
# ======================================================
total_empenhado = df["valorEmpenhadoBruto"].sum()
total_anulado   = df["valorEmpenhadoAnulado"].sum()
total_baixado   = df["valorBaixadoBruto"].sum()

col1, col2, col3 = st.columns(3)

col1.metric(
    "💰 Total Empenhado",
    f"R$ {total_empenhado:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)

col2.metric(
    "❌ Total Anulado",
    f"R$ {total_anulado:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)

col3.metric(
    "✅ Total Baixado no Exercício",
    f"R$ {total_baixado:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)

# ======================================================
# FILTROS (ENTRE TOTAIS E GRÁFICO)
# ======================================================
st.markdown("---")

f1, f2 = st.columns(2)

with f1:
    anos = sorted(df["anoEmpenho"].dropna().unique())
    filtro_ano = st.selectbox(
        "📅 Exercício",
        options=["Todos"] + anos
    )

with f2:
    entidades = sorted(df["nomeEntidade"].unique())
    filtro_entidade = st.selectbox(
        "🏛️ Entidade",
        options=["Todas"] + entidades
    )

# ======================================================
# APLICAÇÃO DOS FILTROS
# ======================================================
df_filtrado = df.copy()

if filtro_ano != "Todos":
    df_filtrado = df_filtrado[df_filtrado["anoEmpenho"] == filtro_ano]

if filtro_entidade != "Todas":
    df_filtrado = df_filtrado[df_filtrado["nomeEntidade"] == filtro_entidade]

if df_filtrado.empty:
    st.info("Nenhum dado para os filtros selecionados.")
    st.stop()

# ======================================================
# GRÁFICO CONSOLIDADO
# ======================================================
st.markdown("### 📊 Empenhado × Anulado × Baixado no Exercício")

graf = (
    alt.Chart(df_filtrado)
    .transform_fold(
        [
            "valorEmpenhadoBruto",
            "valorEmpenhadoAnulado",
            "valorBaixadoBruto"
        ],
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
# TABELA RESUMIDA
# ======================================================
st.markdown("### 📄 Resumo dos Dados")

tabela = (
    df_filtrado
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

# ======================================================
# EXPORTAÇÃO
# ======================================================
st.markdown("### ⬇️ Exportar dados filtrados")

csv = df_filtrado.to_csv(index=False, sep=";", decimal=",", encoding="utf-8-sig")

st.download_button(
    "📥 Baixar CSV",
    csv,
    file_name="empenhos_filtrados.csv",
    mime="text/csv"
)
