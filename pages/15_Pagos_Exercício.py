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
    if coluna not in df_base.columns:
        return df_base

    df_temp = df_base.copy()

    if normalizar:
        df_temp["_filtro_norm"] = df_temp[coluna].apply(normalizar_texto)
        opcoes = sorted(df_temp["_filtro_norm"].dropna().unique().tolist())
    else:
        opcoes = sorted(df_temp[coluna].dropna().unique().tolist())

    opcoes = ["Todos"] + opcoes

    selecionado = st.multiselect(label, options=opcoes, default=["Todos"])

    if "Todos" in selecionado or not selecionado:
        return df_base

    if normalizar:
        df_filtrado = df_temp[df_temp["_filtro_norm"].isin(selecionado)]
        return df_filtrado.drop(columns=["_filtro_norm"], errors="ignore")

    return df_temp[df_temp[coluna].isin(selecionado)]

# ==================================
# CARREGAR DADOS
# ==================================
df = load_empenhos()

if df.empty:
    st.warning("Nenhum dado carregado.")
    st.stop()

# =======================
# LIMPEZA DEFINITIVA (PADRÃO DA PÁGINA BOA)
# =======================

colunas_texto = [
    "anoEmpenho",
    "nomeEntidade",
    "nomeCredor",
    "Descrição da despesa",
    "numRecurso"
]

for col in colunas_texto:
    if col in df.columns:
        df[col] = (
            df[col]
            .astype(str)
            .str.strip()
            .replace(["nan", "None", ""], pd.NA)
        )

# Remove linhas inválidas principais
df = df.dropna(subset=["anoEmpenho", "nomeEntidade"])

# ==================================
# TRATAMENTO DOS VALORES
# ==================================
colunas_valor = ["saldoBaixado", "valorEmpenhadoBruto"]

for col in colunas_valor:
    if col in df.columns:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# Remove registros sem ano válido
df = df[df["anoEmpenho"] != ""]

if df.empty:
    st.warning("Nenhum dado válido encontrado.")
    st.stop()

# ==================================
# FILTROS
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
# AGRUPAMENTO
# ==================================
df_graf = (
    df_filtrado
    .groupby("anoEmpenho", as_index=False)["saldoBaixado"]
    .sum()
)

# ==================================
# GRÁFICO
# ==================================
st.markdown("### 📊 Total Pago por Exercício")

graf = (
    alt.Chart(df_graf)
    .mark_bar(size=60)
    .encode(
        x=alt.X("anoEmpenho:N", title="Exercício", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("saldoBaixado:Q", title="Valor Pago (R$)", axis=alt.Axis(format=",.2f")),
        tooltip=[
            alt.Tooltip("anoEmpenho:N", title="Exercício"),
            alt.Tooltip("saldoBaixado:Q", title="Valor Pago", format=",.2f")
        ]
    )
    .properties(height=420)
)

st.altair_chart(graf, use_container_width=True)

# ==================================
# TABELA
# ==================================
st.subheader("📋 Detalhamento")

colunas_exibicao = [
    "anoEmpenho",
    "nomeEntidade",
    "Descrição da despesa",
    "nomeCredor",
    "numRecurso",
    "valorEmpenhadoBruto",
    "saldoBaixado"
]

colunas_exibicao = [c for c in colunas_exibicao if c in df_filtrado.columns]

tabela = df_filtrado[colunas_exibicao].copy()

def formata_real(valor):
    return (
        f"{valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

if "valorEmpenhadoBruto" in tabela.columns:
    tabela["Valor Empenhado Bruto"] = tabela["valorEmpenhadoBruto"].apply(formata_real)

if "saldoBaixado" in tabela.columns:
    tabela["Valor Pago"] = tabela["saldoBaixado"].apply(formata_real)

colunas_finais = [
    "anoEmpenho",
    "nomeEntidade",
    "Descrição da despesa",
    "nomeCredor",
    "numRecurso",
    "Valor Empenhado Bruto",
    "Valor Pago"
]

colunas_finais = [c for c in colunas_finais if c in tabela.columns]

st.dataframe(tabela[colunas_finais], use_container_width=True)

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
