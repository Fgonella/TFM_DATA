import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils import CATEGORIA_COLORS, fmt_int, load_scoring, load_viables_geo, sidebar_footer

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

st.set_page_config(page_title="Idoneidad geoespacial · Biometano Huesca", page_icon="🗺️", layout="wide")

scoring = load_scoring()
viables = load_viables_geo()

n_total = len(scoring)
n_viables = len(viables)

st.title("🗺️ Sección 2 · Idoneidad geoespacial: Elección de las celdas")
st.markdown(
    f"""
Sobre la provincia de Huesca se tiende una malla de **{fmt_int(n_total)} celdas de 500×500 metros** y a cada una
se le cruzan seis capas de información: biomasa porcina en un radio de 10 km, distancia al
gasoducto, distancia y categoría de la carretera más cercana, pendiente del terreno (DEM),
clasificación urbanística del suelo y restricciones de la Red Natura 2000.

La lógica es de dos pasos: primero se **excluye** lo que directamente no puede ser (zona
protegida, pendiente imposible, sin purín cerca...), y al resto se le pone un **score de
idoneidad ponderado**. Las que superan además umbrales estrictos de contraste quedan como
**viables** — y esas {fmt_int(n_viables)} celdas son las protagonistas del resto de la historia.
"""
)

st.divider()
st.subheader("El embudo")

n_total = len(scoring)
n_aptas = int((scoring["categoria"] != "EXCLUIDO").sum())
n_viables = len(viables)

fig_funnel = go.Figure(go.Funnel(
    y=["Celdas totales (grid 500 m)", "Aptas (sin exclusión)", "Viables (umbrales estrictos)"],
    x=[n_total, n_aptas, n_viables],
    textinfo="value+percent initial",
    marker=dict(color=["#bdbdbd", "#91cf60", "#1a9850"]),
))
fig_funnel.update_layout(height=320)
st.plotly_chart(fig_funnel, width="stretch")

st.caption(
    "El salto de **aptas → viables** aplica cuatro **umbrales estrictos** simultáneos, más "
    "exigentes que los de exclusión: biomasa en 10 km **≥ 120.000 plazas**, gasoducto "
    "**≤ 3.000 m**, pendiente media **≤ 15°** y categoría de vía **≥ 3** (primaria o mejor). "
    "Solo las celdas que cumplen las cuatro a la vez pasan el filtro."
)
st.divider()
col1, col2 = st.columns(2)

with col1:
    st.subheader("Criterios de exclusión")
    exclusion_df = pd.DataFrame(
        [
            ["Red Natura 2000", "Dentro de ZEC/ZEPA — protección ambiental"],
            ["Suelo no apto", "Clasificación urbanística incompatible"],
            ["Pendiente excesiva (>25°)", "Obra civil inviable"],
            ["Núcleo urbano", "Dentro del buffer de población"],
            ["Gasoducto a más de 15 km", "Conexión a red inviable"],
            ["Biomasa < 20.000 plazas en 10 km", "No hay purín suficiente"],
        ],
        columns=["Motivo", "Por qué excluye"],
    )
    st.dataframe(exclusion_df, width="stretch", hide_index=True)

with col2:
    st.subheader("Pesos del score (AHP)")
    pesos_df = pd.DataFrame(
        [
            ["Biomasa porcina en 10 km", "29,3 %"],
            ["Distancia a gasoducto", "29,3 %"],
            ["Clasificación del suelo", "14,6 %"],
            ["Categoría de la vía cercana", "9,8 %"],
            ["Pendiente media", "7,3 %"],
            ["Distancia a carretera", "4,9 %"],
            ["Distancia a núcleos urbanos", "4,9 %"],
        ],
        columns=["Variable", "Peso"],
    )
    st.dataframe(pesos_df, width="stretch", hide_index=True)
    st.caption(
        "Pesos derivados por **AHP** (matriz de comparación por pares de Saaty, CR < 0,1). "
        "La Red Natura 2000 no puntúa: ya actúa como exclusión binaria. Biomasa y gasoducto "
        "se llevan casi el 60 % del score entre las dos — un adelanto de lo que después "
        "confirman los modelos del capítulo 4: son las variables que mandan."
    )

st.divider()
st.subheader(f"El mapa de las {fmt_int(n_viables)} celdas viables")
st.markdown(
    """
Cada polígono es una celda de 500×500 m que sobrevivió a todos los filtros. El color es el
**score de idoneidad**. Se ve a simple vista que las candidatas no están repartidas al azar:
se concentran en los corredores donde coinciden **granjas densas y gasoducto cerca**.
"""
)

viables_plot = viables.copy()
centroid = viables_plot.geometry.union_all().centroid

fig_map = px.choropleth_mapbox(
    viables_plot,
    geojson=viables_plot.geometry.__geo_interface__,
    locations=viables_plot.index,
    color="score",
    color_continuous_scale="Viridis",
    mapbox_style="open-street-map",
    center={"lat": centroid.y, "lon": centroid.x},
    zoom=8.3,
    opacity=0.65,
    hover_name="cell_id",
    hover_data={
        "score": ":.1f",
        "biomasa_10km": ":.0f",
        "dist_gasoducto": ":.0f",
        "pendiente_media": ":.1f",
        "categoria": True,
    },
    labels={
        "score": "Score",
        "biomasa_10km": "Biomasa 10 km (plazas)",
        "dist_gasoducto": "Dist. gasoducto (m)",
        "pendiente_media": "Pendiente media (°)",
        "categoria": "Categoría",
    },
)
fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=600)
st.plotly_chart(fig_map, width="stretch")

st.divider()
col1, col2 = st.columns(2)

with col1:
    st.subheader("Categorías de toda la malla")
    counts = scoring["categoria"].value_counts().reindex(
        ["ÓPTIMO", "BUENO", "MODERADO", "EXCLUIDO"]
    ).dropna()
    fig = px.bar(
        counts,
        x=counts.index,
        y=counts.values,
        color=counts.index,
        color_discrete_map=CATEGORIA_COLORS,
        text=counts.values,
    )
    fig.update_layout(showlegend=False, yaxis_title="Nº de celdas", xaxis_title=None, height=380)
    st.plotly_chart(fig, width="stretch")

with col2:
    st.subheader("Score de las viables")
    fig2 = px.histogram(viables_plot, x="score", nbins=40, color_discrete_sequence=["#2ca25f"])
    fig2.update_layout(xaxis_title="Score de idoneidad", yaxis_title="Nº de celdas", height=380)
    st.plotly_chart(fig2, width="stretch")

st.divider()

sidebar_footer()
