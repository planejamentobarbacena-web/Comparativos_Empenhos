import streamlit as st
import pandas as pd
import altair as alt

# ===============================
# CONFIGURAÇÃO INICIAL
# ===============================
st.set_page_config(
    page_title="Pagos no Exercício",
    layout="wide"
)

st.markdown("## 💰 Pagos no Exercício")

# ===============================
# CARREGAMENTO DOS DADOS
# ===============================
@st.cache_data
def carregar_dados():
    df = pd.read_csv("dados.csv")  # ajuste se necessário
    return df

df = carregar_dados()

# ===============================
# FILTROS (VERTICAIS E INDEPENDENTES)
# ===============================
st.markdown("### 🔎 Filtros")

def filtro_multiselect(df, coluna, label):
    opcoes = ["Todos"] + sorted(df[coluna].dropna().unique().tolist())
    selecionado = st.multiselect(
        label,
        options=opcoes,
        default="Todos"
    )
    if "Todos" in selecionado or selecionado == []:
        return df
    return df[df[coluna].isin(selecionado)]

# Exercício
df_filtro = filtro_multiselect(df, "exercicio", "Exercício")

# Entidade
df_filtro = filtro_multiselect(df_filtro, "entidade", "Entidade")

# Credor
df_filtro = filtro_multiselect(df_filtro, "credor", "Credor")

# Recurso
df_filtro = filtro_multiselect(df_filtro, "recurso", "Recurso")

# Natureza da Despesa
df_filtro = filtro_multiselect(df_filtro, "naturezaDespesa", "Natureza da Despesa")

# ===============================
# TRATAMENTO DOS DADOS
# ===============================
df_filtro["saldoBaixado"] = pd.to_numeric(
    df_filtro["saldoBaixado"],
    errors="coerce"
).fillna(0)

# ===============================
# GRÁFICO PRINCIPAL
# ===============================
st.markdown("### 📊 Total Pago por Exercício")

df_graf = (
    df_filtro
    .groupby("exercicio", as_index=False)["saldoBaixado"]
    .sum()
)

graf = (
    alt.Chart(df_graf)
    .mark_bar(size=60)
    .encode(
        x=alt.X(
            "exercicio:N",
            title="Exercício",
            axis=alt.Axis(labelAngle=0)
        ),
        y=alt.Y(
            "saldoBaixado:Q",
            title="Valor Pago (R$)"
        ),
        tooltip=[
            alt.Tooltip("exercicio:N", title="Exercício"),
            alt.Tooltip("saldoBaixado:Q", title="Valor Pago", format=",.2f")
        ]
    )
    .properties(height=420)
)

st.altair_chart(graf, use_container_width=True)

# ===============================
# TABELA DETALHADA
# ===============================
st.markdown("### 📄 Detalhamento")

st.dataframe(
    df_filtro[
        [
            "exercicio",
            "entidade",
            "credor",
            "recurso",
            "naturezaDespesa",
            "saldoBaixado"
        ]
    ],
    use_container_width=True
)
