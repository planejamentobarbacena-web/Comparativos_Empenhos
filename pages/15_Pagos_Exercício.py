import streamlit as st
import pandas as pd
import altair as alt

# ===============================
# CONFIGURAÇÃO DA PÁGINA
# ===============================
st.set_page_config(
    page_title="Pagos no Exercício",
    layout="wide"
)

st.markdown("## 💰 Pagos no Exercício")

# ===============================
# VERIFICA SE OS DADOS EXISTEM
# ===============================
if "df" not in st.session_state:
    st.error("Os dados ainda não foram carregados. Volte à página inicial.")
    st.stop()

df = st.session_state["df"].copy()

# ===============================
# FILTROS VERTICAIS E LIVRES
# ===============================
st.markdown("### 🔎 Filtros")

def filtro_multiselect(df_base, coluna, label):
    opcoes = ["Todos"] + sorted(df_base[coluna].dropna().unique().tolist())
    selecionado = st.multiselect(
        label,
        options=opcoes,
        default=["Todos"]
    )

    if "Todos" in selecionado or len(selecionado) == 0:
        return df_base

    return df_base[df_base[coluna].isin(selecionado)]

df_filtro = filtro_multiselect(df, "exercicio", "Exercício")
df_filtro = filtro_multiselect(df_filtro, "entidade", "Entidade")
df_filtro = filtro_multiselect(df_filtro, "credor", "Credor")
df_filtro = filtro_multiselect(df_filtro, "recurso", "Recurso")
df_filtro = filtro_multiselect(df_filtro, "naturezaDespesa", "Natureza da Despesa")

# ===============================
# TRATAMENTO DO VALOR
# ===============================
df_filtro["saldoBaixado"] = pd.to_numeric(
    df_filtro["saldoBaixado"],
    errors="coerce"
).fillna(0)

# ===============================
# GRÁFICO
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
# TABELA
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
