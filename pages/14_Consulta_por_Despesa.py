graf = (
    alt.Chart(comparativo)
    .transform_fold(
        ["empenhado_liquido", "saldoBaixado"],
        as_=["Tipo", "Valor"]
    )
    .mark_bar(size=26)  # barras mais finas
    .encode(
        x=alt.X(
            "anoEmpenho:N",
            title="Exercício",
            axis=alt.Axis(labelAngle=0)
        ),
        xOffset=alt.XOffset("Tipo:N"),
        y=alt.Y(
            "Valor:Q",
            title="Valor (R$)"
        ),
        color=alt.Color(
            "Tipo:N",
            title="Tipo",
            scale=alt.Scale(
                domain=["empenhado_liquido", "saldoBaixado"],
                range=["#1f77b4", "#ff7f0e"]
            ),
            legend=alt.Legend(
                orient="bottom",
                direction="horizontal",
                columns=2   # 👈 só dois tipos
            )
        ),
        tooltip=[
            "anoEmpenho:N",
            "Tipo:N",
            alt.Tooltip("Valor:Q", format=",.2f")
        ]
    )
    .properties(height=420)
)

st.altair_chart(graf, use_container_width=True)
