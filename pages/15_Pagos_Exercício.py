import streamlit as st
import altair as alt
import pandas as pd
import unicodedata

from auth import login
from components.header import render_header
from data_loader import load_empenhos

# ==================================
# CONFIGURAÇÃO / SEGURANÇA
# ==================================
login()
render_header()

st.title("💰 Pagos no Exercício")

# ==================================
# FUNÇÕES AUXILIARES
# ==================================
def normalizar_texto(txt):
    if pd.isna(txt):
        return ""
    txt = str(txt)
    txt = unicodedata.normalize("NFKD", txt)
    return "".join(c for c in txt if not unicodedata.combining(c)).lower().strip()

def filtro_multiselect(df_base, coluna, label, normalizar=False):
    if normalizar:
        df_base["_filtro_norm"] = df_base[coluna].apply(normalizar_texto)
        opcoes = sorted(df_base["_filtro_norm"].unique().tolist())
    else:
        opcoes = sorted(df_base[coluna].dropna().unique().tolist())

    opcoes = ["Todos"] + opcoes

    selecionado = st.multiselect(
        label,
        options=opcoes,
        default=["Todos"]
    )

    if "Todos" in selecionado or not selecionado:
        return df_base

    if normalizar:
        return df_base[df_base["_filtro_norm"].isin(selecionado)]

    return df_base[df_base[coluna].isin(selecionado)]

# ==================================
# CARREGAR DADOS
# ==================================
df = load_empenhos()

if df.empty:
    st.warning("Nenhum dado carregado.")
    st.stop()

# ==================================
# LIMPEZA BÁSICA
# ==================================
df["anoEmpenho"] = df["anoEmpenho"].astype(str).str.strip()
df["nomeEntidade"] = df["nomeEntidade"].astype(str).str.strip()
df["nomeCredor"] = df["nomeCredor"].astype(str).str.strip()
df["Descrição da despesa"] = df["Descrição da despesa"].astype(str).str.strip()

# ==================================
# TRATAMENTO DOS VALORES
# ==================================
for col in ["saldoBaixado", "valorEmpenhadoBruto"]:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# ==================================
# FILTROS (VERTICAIS)
# ==================================
st.markdown("### 🔎 Filtros")

df_filtrado = df.copy()
df_filtrado = filtro_multiselect(df_filtrado, "anoEmpenho", "📅 Exercício")
df_filtrado = filtro_multiselect(df_filtrado, "nomeEntidade", "🏢 Entidade")
df_filtrado = filtro_multiselect(
    df_filtrado,
    "nomeCredor",
    "🏷️ Credor (ignora acentuação)",
    normalizar=True
)
df_filtrado = filtro_multiselect(df_filtrado, "numRecurso", "💰 Fonte de Recurso")
df_filtrado = filtro_multiselect(
    df_filtrado,
    "Descrição da despesa",
    "📂 Natureza da Despesa"
)

if df_filtrado.empty:
    st.info("Nenhum dado para os filtros selecionados.")
    st.stop()

# ==================================
# AGRUPAMENTO PARA O GRÁFICO
# ==================================
df_graf = (
    df_filtrado
    .groupby("anoEmpenho", as_index=False)["saldoBaixado"]
    .sum()
)

# ==================================
# GRÁFICO – PAGOS NO EXERCÍCIO
# ==================================
st.markdown("### 📊 Total Pago por Exercício")

graf = (
    alt.Chart(df_graf)
    .mark_bar(size=60)
    .encode(
        x=alt.X(
            "anoEmpenho:N",
            title="Exercício",
            axis=alt.Axis(labelAngle=0)
        ),
        y=alt.Y(
            "saldoBaixado:Q",
            title="Valor Pago (R$)",
            axis=alt.Axis(format=",.2f")  # formato numérico correto
        ),
        tooltip=[
            alt.Tooltip("anoEmpenho:N", title="Exercício"),
            alt.Tooltip("saldoBaixado:Q", title="Valor Pago", format=",.2f")
        ]
    )
    .properties(height=420)
)

st.altair_chart(graf, use_container_width=True)

# ==================================
# TABELA DETALHADA
# ==================================
st.subheader("📋 Detalhamento")

tabela = df_filtrado[
    [
        "anoEmpenho",
        "nomeEntidade",
        "Descrição da despesa",
        "nomeCredor",
        "numRecurso",
        "valorEmpenhadoBruto",
        "saldoBaixado"
    ]
].copy()

def formata_real(valor):
    return (
        f"{valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

tabela["Valor Empenhado Bruto"] = tabela["valorEmpenhadoBruto"].apply(formata_real)
tabela["Valor Pago"] = tabela["saldoBaixado"].apply(formata_real)

tabela = tabela[
    [
        "anoEmpenho",
        "nomeEntidade",
        "Descrição da despesa",
        "nomeCredor",
        "numRecurso",
        "Valor Empenhado Bruto",
        "Valor Pago"
    ]
]

st.dataframe(tabela, use_container_width=True)

# ==================================
# DOWNLOAD
# ==================================
st.divider()

csv = tabela.to_csv(index=False, sep=";", encoding="utf-8-sig")

st.download_button(
    "📥 Baixar CSV – Pagos no Exercício",
    csv,
    file_name="pagos_no_exercicio.csv",
    mime="text/csv"
)
