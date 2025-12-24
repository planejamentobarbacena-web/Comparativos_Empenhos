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
# FUNÇÃO AUXILIAR – NORMALIZA TEXTO
# ==================================
def normalizar(txt):
    if pd.isna(txt):
        return ""
    txt = str(txt)
    txt = unicodedata.normalize("NFD", txt)
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    return txt.lower().strip()

# ==================================
# CARREGAR DADOS (PADRÃO DO PROJETO)
# ==================================
df = load_empenhos()

if df.empty:
    st.warning("Nenhum dado carregado.")
    st.stop()

# ==================================
# LIMPEZA BÁSICA
# ==================================
df["anoEmpenho"] = (
    df["anoEmpenho"]
    .astype(str)
    .str.strip()
    .replace(["nan", "None", ""], pd.NA)
)

df["nomeEntidade"] = (
    df["nomeEntidade"]
    .astype(str)
    .str.strip()
    .replace(["nan", "None", ""], pd.NA)
)

df = df.dropna(subset=["anoEmpenho", "nomeEntidade"])

# ==================================
# TRATAMENTO DOS VALORES NUMÉRICOS
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
# FILTRO MULTISELECT (AMARRADO + TODOS + SEM ACENTO)
# ==================================
def filtro_multiselect(df_base, coluna, label):
    df_aux = df_base.copy()

    col_norm = coluna + "_norm"
    df_aux[col_norm] = df_aux[coluna].apply(normalizar)

    opcoes = sorted(df_aux[coluna].dropna().unique().tolist())
    opcoes = ["Todos"] + opcoes

    selecionado = st.multiselect(
        label,
        options=opcoes,
        default=["Todos"]
    )

    if not selecionado or "Todos" in selecionado:
        return df_base

    selecionado_norm = [normalizar(v) for v in selecionado]

    return df_aux[
        df_aux[col_norm].isin(selecionado_norm)
    ].drop(columns=[col_norm])

# ==================================
# FILTROS (VERTICAIS – CASCATA)
# ==================================
st.markdown("### 🔎 Filtros")

df_f = df.copy()

df_f = filtro_multiselect(df_f, "anoEmpenho", "📅 Exercício")
df_f = filtro_multiselect(df_f, "nomeEntidade", "🏢 Entidade")
df_f = filtro_multiselect(df_f, "Descrição da despesa", "📂 Natureza da Despesa")
df_f = filtro_multiselect(df_f, "nomeCredor", "🏷️ Credor")
df_f = filtro_multiselect(df_f, "numRecurso", "💰 Fonte de Recurso")

if df_f.empty:
    st.info("Nenhum dado para os filtros selecionados.")
    st.stop()

# ==================================
# AGRUPAMENTO PARA O GRÁFICO
# ==================================
df_graf = (
    df_f
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
            title="Valor Pago (R$)"
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

tabela = df_f[
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

tabela["Empenhado Bruto"] = tabela["valorEmpenhadoBruto"].apply(
    lambda x: f"R$ {x:,.2f}"
    .replace(",", "X")
    .replace(".", ",")
    .replace("X", ".")
)

tabela["Valor Pago"] = tabela["saldoBaixado"].apply(
    lambda x: f"R$ {x:,.2f}"
    .replace(",", "X")
    .replace(".", ",")
    .replace("X", ".")
)

tabela = tabela[
    [
        "anoEmpenho",
        "nomeEntidade",
        "Descrição da despesa",
        "nomeCredor",
        "numRecurso",
        "Empenhado Bruto",
        "Valor Pago"
    ]
]

st.dataframe(tabela, use_container_width=True)

# ==================================
# DOWNLOAD CSV
# ==================================
st.divider()

csv = tabela.to_csv(index=False, sep=";", encoding="utf-8-sig")

st.download_button(
    "📥 Baixar CSV – Pagos no Exercício",
    csv,
    file_name="pagos_no_exercicio.csv",
    mime="text/csv"
)
