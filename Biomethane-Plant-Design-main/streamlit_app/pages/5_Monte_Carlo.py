import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils import (
    IMG,
    MC_DIST,
    N_SIM,
    OPEX_FIJO_COMPONENTES,
    PLANTAS,
    RAMP,
    VIDA_UTIL,
    WACC,
    fmt_int,
    load_mc_optimas,
    sidebar_footer,
)

st.set_page_config(page_title="Monte Carlo · Biometano Huesca", page_icon="🎲", layout="wide")

st.markdown(
    """
    <style>
    h1 {
        text-align: center;
        color: #2E7D32;
        font-size: 20px;
    }
    
        h2 {
        text-align: center;
        color: #2E7D32;
        font-size: 16px;
    }
   
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🎲 Sección 5 · Monte Carlo: 25.000 futuros por sitio")
st.markdown(
    f"""
**¿Por que realizamos un Monte Carlo?** Un VAN calculado con supuestos fijos es una foto — y las fotos mienten por omisión. 
El precio del biometano puede caer, la obra puede pasarse de presupuesto, el purín contratado puede ser
menos del esperado. En vez de fingir que sabemos esos números, **los sorteamos**: para cada
celda óptima corremos **{fmt_int(N_SIM)} simulaciones** de un modelo de flujos de caja
descontados a {VIDA_UTIL} años (WACC {WACC*100:.0f} %), variando 8 supuestos a la vez.

El resultado por sitio no es un VAN: es una **distribución de VAN**, de la que sale la métrica
que de verdad importa — **P(VAN > 0)**, la probabilidad de no perder dinero.
"""
)

mc = load_mc_optimas()

st.divider()
st.subheader("Las 8 variables que se sortean (distribuciones triangulares)")

dist_df = pd.DataFrame(
    [(k, v[0], v[1], v[2], v[3]) for k, v in MC_DIST.items()],
    columns=["Variable", "Mínimo", "Más probable", "Máximo", "Por qué este rango"],
)
st.dataframe(dist_df, width="stretch", hide_index=True)
st.caption(
    "Rangos deliberadamente prudentes: preferimos que el modelo peque de conservador. "
    "El valor 'más probable' de cada triangular es el mismo que usó la economía preliminar "
    "del capítulo 4 — para ser coherentes entre las dos etapas."
)

st.divider()
col1, col2 = st.columns(2)

with col1:
    st.subheader("La curva de arranque")
    st.markdown(
        "La planta **no produce al 100 % desde el día uno** , eso también está modelado: "
        "60 % los primeros 5 años, subida escalonada y crucero desde el año 10."
    )
    fig_ramp = go.Figure(go.Bar(
        x=[f"Año {i}" for i in range(1, VIDA_UTIL + 1)],
        y=[r * 100 for r in RAMP],
        marker_color=["#fdae61"] * 5 + ["#a6d96a"] * 4 + ["#1a9850"] * 6,
    ))
    fig_ramp.update_layout(yaxis_title="Producción (%)", height=350)
    st.plotly_chart(fig_ramp, width="stretch")

with col2:
    st.subheader("Los costes fijos, la clave de la escala")
    opex_df = pd.DataFrame(
        list(OPEX_FIJO_COMPONENTES.items()), columns=["Concepto", "€/año"]
    )
    fig_opex = px.bar(
        opex_df, x="€/año", y="Concepto", orientation="h",
        color_discrete_sequence=["#4C72B0"], text="€/año",
    )
    fig_opex.update_traces(texttemplate="%{text:,.0f} €")
    fig_opex.update_layout(height=350, yaxis_title=None)
    st.plotly_chart(fig_opex, width="stretch")
    st.caption(
        "Personal, seguros, administración... son casi iguales produzca la planta 2 o 10 "
        "millones de Nm³. Por eso la escala grande gana casi siempre: reparte estos costes "
        "sobre más producción."
    )

st.divider()
st.subheader("La escala no se fija de antemano: se prueban las tres")
st.markdown(
    """
Para cada sitio se simulan las tres escalas, para que la comparación sea justa — y se queda la de mejor VAN esperado.
"""
)



escalas_df = pd.DataFrame(
    [(k, f"{v['capex']/1e6:.0f} M€", f"{v['capacidad']/1e6:.0f} M Nm³/año", f"{v['capex']/v['capacidad']:.2f} €/Nm³")
     for k, v in PLANTAS.items()],
    columns=["Escala", "CAPEX base", "Capacidad", "CAPEX específico"],

)

col1, col2 = st.columns([1, 1.3])
with col1:
    st.dataframe(escalas_df, width="stretch", hide_index=True)
    reparto = mc["escala_optima"].value_counts()
    for esc, n in reparto.items():
        st.metric(f"Sitios donde gana la {esc}", fmt_int(n))
    st.caption(
        "La economía de escala empuja a la Grande donde hay biomasa de sobra; donde no "
        "alcanza, una Mediana evita cargar con un CAPEX medio vacío. El modelo lo decide "
        "sitio a sitio."
    )

with col2:
    fig_esc = px.scatter(
        mc,
        x="VAN_esperado",
        y="prob_VAN_positivo",
        color="escala_optima",
        color_discrete_map={"Grande": "#1a9850", "Mediana": "#e67e22", "Pequeña": "#4C72B0"},
        hover_name="cell_id",
        labels={
            "VAN_esperado": "VAN esperado (€)",
            "prob_VAN_positivo": "P(VAN > 0)",
            "escala_optima": "Escala ganadora",
        },
        title="Cada punto es una celda óptima tras 25.000 simulaciones",
        opacity=0.7,
    )
    fig_esc.add_hline(y=0.5, line_dash="dot", line_color="gray", annotation_text="Moneda al aire")
    fig_esc.add_vline(x=0, line_dash="dot", line_color="gray")
    fig_esc.update_layout(height=450)
    st.plotly_chart(fig_esc, width="stretch")

st.divider()
st.subheader("Las distribuciones de VAN")

col1, col2 = st.columns(2)
with col1:
    st.image(str(IMG / "mc_distribucion_van_mejor.png"),
             caption="Distribución del VAN de la mejor localización — 25.000 simulaciones", width="stretch")
with col2:
    st.image(str(IMG / "mc_cdf_van.png"),
             caption="Curva acumulada (CDF): en qué punto cada sitio cruza el VAN = 0", width="stretch")

col1, col2 = st.columns(2)
with col1:
    st.image(str(IMG / "mc_violin_van_sitios.png"),
             caption="Violines de VAN por sitio — no solo dónde está el centro, sino cuánto riesgo hay en las colas", width="stretch")
with col2:
    st.image(str(IMG / "mc_mapa_decision.png"),
             caption="Mapa de decisión: VAN esperado vs probabilidad de éxito", width="stretch")

st.image(str(IMG / "mc_distribucion_van_todas.png"),
         caption="Panel de distribuciones de VAN de los mejores sitios — verde: P(VAN>0) ≥ 70 %", width="stretch")

st.divider()
mejor = mc.iloc[0]
st.success(
    f"**Nota**: tras {fmt_int(N_SIM)} futuros por sitio, la mejor celda "
    f"({int(mejor['cell_id'])}, escala {mejor['escala_optima']}) tiene una probabilidad de "
    f"éxito del {mejor['prob_VAN_positivo']*100:.0f} % con un VAN esperado de "
    f"{mejor['VAN_esperado']/1e6:.2f} M€. Positivo, sí — pero no es un billete de lotería "
    "premiado: hay un rango de resultados y colas negativas. La pregunta natural que sigue es "
    "*¿de qué depende caer en la cola buena o en la mala?* — capítulo 6."
)

sidebar_footer()
