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
st.title("📂 Consulta por Natureza da Despesa")

df = load_empenhos()
if df.empty:
    st.stop()

natureza = st.selectbox(
    "Selecione a Natureza:",
    ["Todos"] + sorted(df["numNaturezaEmp"].dropna().unique())
)

if natureza == "Todos":
    df_sel = df.copy()
else:
    df_sel = df[df["numNaturezaEmp"] == natureza]

comparativo = (
    df_sel
    .groupby("Ano", as_index=False)[
        ["valorEmpenhadoBruto_num", "valorEmpenhadoAnulado_num", "valorBaixadoBruto_num"]
    ]
    .sum()
)

comparativo_display = comparativo.rename(columns={
    "valorEmpenhadoBruto_num": "Empenhado Bruto",
    "valorEmpenhadoAnulado_num": "Empenhado Anulado",
    "valorBaixadoBruto_num": "Baixado Bruto"
})


df_melt = comparativo.melt(id_vars="Ano", var_name="Tipo", value_name="Valor")
df_melt["Tipo"] = df_melt["Tipo"].map({
    "valorEmpenhadoBruto_num": "Empenhado Bruto",
    "valorEmpenhadoAnulado_num": "Empenhado Anulado",
    "valorBaixadoBruto_num": "Baixado Bruto"
})

graf = (
    alt.Chart(df_melt)
    .mark_bar(size=45)   # barras finas
    .encode(
        x=alt.X(
            "Tipo:N",
            title="Tipo de Valor",
            axis=alt.Axis(labelAngle=0)
        ),
        xOffset=alt.XOffset(
            "Ano:N",
            scale=alt.Scale(
                paddingInner=0.1,
                paddingOuter=0.1
            ),
            title="Exercício"
        ),
        y=alt.Y(
            "Valor:Q",
            title="Valor (R$)"
        ),
        color=alt.Color(
            "Ano:N",
            title="Exercício"
        ),
        tooltip=[
            "Ano:N",
            "Tipo:N",
            alt.Tooltip("Valor:Q", format=",.2f")
        ]
    )
    .properties(height=420)
)

st.altair_chart(graf, use_container_width=True)


# =======================
# Tabela abaixo do gráfico
# =======================
comparativo_display_format = comparativo_display.copy()

for col in ["Empenhado Bruto", "Empenhado Anulado", "Baixado Bruto"]:
    comparativo_display_format[col] = comparativo_display_format[col].apply(
        lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )

st.dataframe(comparativo_display_format, use_container_width=True)
