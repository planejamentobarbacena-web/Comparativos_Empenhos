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
# CSS (opcional)
# ======================================================
def load_css():
    try:
        with open("assets/style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

load_css()

# ======================================================
# CARREGAMENTO DOS DADOS
# ======================================================
df = load_empenhos()

if df.empty:
    st.warning("Nenhum arquivo encontrado na pasta /data.")
    st.stop()

# ======================================================
# TRATAMENTO PARA FILTROS (remove NaN)
# ======================================================
df = df.copy()

df["Ano"] = df["Ano"].dropna()
df["entidade"] = df["entidade"].fillna("")

# ======================================================
# TÍTULO
# ======================================================
st.title("📊 Painel de Empenhos – Visão Geral")

st.markdown(
    """
    Bem-vindo ao painel de **análise histórica de empenhos públicos**.  
    Os dados são carregados automaticamente a partir dos arquivos CSV.
    """
)

# ======================================================
# MÉTRICAS GERAIS (sempre totais)
# ======================================================
total_empenhado = df["valorEmpenhadoBruto_num"].sum()
total_anulado   = df["valorEmpenhadoAnulado_num"].sum()
total_baixado   = df["valorBaixadoBruto_num"].sum()

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
    "✅ Total Baixado",
    f"R$ {total_baixado:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)

# ======================================================
# FILTROS SIMPLES (ENTRE MÉTRICAS E GRÁFICO)
# ======================================================
st.markdown("---")

col_f1, col_f2 = st.columns(2)

with col_f1:
    exercicios = sorted(df["Ano"].dropna().unique())
    filtro_exercicio = st.selectbox(
        "📅 Exercício",
        options=["Todos"] + exercicios
    )

with col_f2:
    entidades = sorted(df["entidade"].unique())
    filtro_entidade = st.selectbox(
        "🏛️ Entidade",
        options=["Todas"] + entidades
    )

# ======================================================
# APLICA FILTROS
# ======================================================
df_filtrado = df.copy()

if filtro_exercicio != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Ano"] == filtro_exercicio]

if filtro_entidade != "Todas":
    df_filtrado = df_filtrado[df_filtrado["entidade"] == filtro_entidade]

# ======================================================
# GRÁFICO CONSOLIDADO
# ======================================================
st.markdown("### 📊 Empenhado × Anulado × Baixado por Exercício")

graf = (
    alt.Chart(df_filtrado)
    .transform_fold(
        [
            "valorEmpenhadoBruto_num",
            "valorEmpenhadoAnulado_num",
            "valorBaixadoBruto_num"
        ],
        as_=["Tipo", "Valor"]
    )
    .transform_calculate(
        TipoLabel="""
            datum.Tipo == 'valorEmpenhadoBruto_num' ? 'Empenhado' :
            datum.Tipo == 'valorEmpenhadoAnulado_num' ? 'Anulado' :
            'Baixado'
        """
    )
    .mark_bar(size=45)
    .encode(
        x=alt.X(
            "TipoLabel:N",
            title="Tipo de Valor",
            axis=alt.Axis(labelAngle=0)
        ),
        xOffset=alt.XOffset(
            "Ano:N",
            scale=alt.Scale(paddingInner=0.05, paddingOuter=0.05),
            title="Exercício"
        ),
        y=alt.Y(
            "sum(Valor):Q",
            title="Valor (R$)"
        ),
        color=alt.Color(
            "Ano:N",
            title="Exercício"
        ),
        tooltip=[
            "Ano:N",
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
cols_tabela = [
    "Ano",
    "numeroEmpenho",
    "nomeCredor",
    "numRecurso",
    "numNaturezaEmp",
    "valorEmpenhadoBruto_num",
    "valorEmpenhadoAnulado_num",
    "valorBaixadoBruto_num"
]

df_tabela = df_filtrado[cols_tabela].copy()

for col in [
    "valorEmpenhadoBruto_num",
    "valorEmpenhadoAnulado_num",
    "valorBaixadoBruto_num"
]:
    df_tabela[col] = df_tabela[col].apply(
        lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )

with st.expander("📋 Ver dados carregados (amostra)"):
    st.dataframe(df_tabela.head(50), use_container_width=True)

# ======================================================
# EXPORTAÇÃO
# ======================================================
st.markdown("### ⬇️ Exportar dados")

csv = df_filtrado.to_csv(index=False, sep=";").encode("utf-8")

st.download_button(
    label="📥 Baixar CSV filtrado",
    data=csv,
    file_name="empenhos_filtrados.csv",
    mime="text/csv"
)
