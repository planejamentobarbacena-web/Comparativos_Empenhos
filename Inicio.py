import streamlit as st
import os
import json
import altair as alt

from auth import login, exige_admin
from components.header import render_header
from data_loader import load_empenhos  

# 🔐 Segurança
login()
render_header()

# ======================================================
# CONFIGURAÇÃO GERAL (apenas o necessário)
# ======================================================
st.set_page_config(
    page_title="Painel de Empenhos",
    page_icon="📊",
    layout="wide"
)

# --------------------------
# Autenticação (bloqueia se não logado)
# --------------------------
login()
# botão de logout disponível na sidebar


# ======================================================
# CSS (visual estilo app)
# ======================================================
def load_css():
    try:
        with open("assets/style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

load_css()

# ======================================================
# CARREGAMENTO DOS DADOS (ÚNICA FONTE)
# ======================================================
df = load_empenhos()

if df.empty:
    st.warning("Nenhum arquivo encontrado na pasta /data.")
    st.stop()

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
# MÉTRICAS GERAIS
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
# GRÁFICO CONSOLIDADO POR ANO (EMPENHADO)
# ======================================================
st.markdown("### 📊 Empenhado × Anulado × Baixado por Exercício")

base_grafico = df.copy()

graf = (
    alt.Chart(df)
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
    .mark_bar(size=45)   # 👈 barras - largura
    .encode(
        x=alt.X(
            "TipoLabel:N",
            title="Tipo de Valor",
            axis=alt.Axis(labelAngle=0)
        ),
        xOffset=alt.XOffset(
            "Ano:N",
            scale=alt.Scale(
                paddingInner=0.05,   # 👈 barras bem próximas
                paddingOuter=0.05
            ),
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
# Seleciona e formata colunas de valores como moeda brasileira
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

df_tabela = df[cols_tabela].copy()

# Formata os valores monetários
for col in ["valorEmpenhadoBruto_num", "valorEmpenhadoAnulado_num", "valorBaixadoBruto_num"]:
    df_tabela[col] = df_tabela[col].apply(
        lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )

# Exibe a tabela abaixo do gráfico
with st.expander("📋 Ver dados carregados (amostra)"):
    st.dataframe(df_tabela.head(50), use_container_width=True)

# ======================================================
# EXPORTAÇÃO CSV
# ======================================================
st.markdown("### ⬇️ Exportar dados")

csv = df.to_csv(index=False, sep=";").encode("utf-8")

st.download_button(
    label="📥 Baixar CSV completo",
    data=csv,
    file_name="empenhos_tratados.csv",
    mime="text/csv"
)
