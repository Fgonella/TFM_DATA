import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from utils import (
    COLOR_NO_OPTIMA,
    COLOR_OPTIMA,
    DATA,
    IMG,
    fmt_eur,
    fmt_int,
    load_economia,
    load_viables_geo,
    sidebar_footer,
    umbrales_optimo,
)

st.set_page_config(page_title="Economía y óptimas · Biometano Huesca", page_icon="💰", layout="wide")

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

st.title("💰 Sección 4 · Economía celda a celda y el filtro de las óptimas")
st.markdown(
    """
En la siguiente parte del trabajo se hace **la cuenta de resultados (Margen) completa a las 2.890 celdas
viables**. Para cada una: purín movilizable en 10 km → biometano producible → ingresos,
OPEX, amortización → **margen anual** en tres escenarios de precio (pesimista, base,
optimista).

"""
)

econ = load_economia()
viables = load_viables_geo()
umb = umbrales_optimo(econ)
n_optimas = int(econ["viable"].sum())
n_total = len(econ)

st.divider()
st.subheader("La foto económica de las 2.890 celdas")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Margen base mediano", f"{econ['margen_base_€'].median()/1e6:.2f} M€/año")
c2.metric("Rango de margen base", f"{econ['margen_base_€'].min()/1e6:.1f} a {econ['margen_base_€'].max()/1e6:.1f} M€")
c3.metric("CAPEX típico", f"{econ['capex_total_M€'].median():.1f} M€")
c4.metric("Celdas con margen base > 0", fmt_int((econ["margen_base_€"] > 0).sum()))

col1, col2 = st.columns(2)
with col1:
    fig = px.histogram(
        econ, x="margen_base_M€", nbins=45,
        color_discrete_sequence=["#2ca25f"],
        labels={"margen_base_M€": "Margen anual escenario base (M€)"},
        title="Distribución del margen anual (escenario base)",
    )
    fig.add_vline(x=umb["margen"] / 1e6, line_dash="dash", line_color="#e67e22",
                  annotation_text="p75 (umbral óptima)")
    fig.update_layout(height=400, yaxis_title="Nº de celdas")
    st.plotly_chart(fig, width="stretch")

with col2:
    fig2 = px.scatter(
        econ, x="capex_total_M€", y="margen_base_M€",
        color="biomasa_10km",
        color_continuous_scale="Viridis",
        labels={
            "capex_total_M€": "CAPEX total (M€)",
            "margen_base_M€": "Margen base (M€/año)",
            "biomasa_10km": "Biomasa 10 km",
        },
        title="CAPEX vs margen — el color es la biomasa cercana",
        opacity=0.6,
    )
    fig2.update_layout(height=400)
    st.plotly_chart(fig2, width="stretch")
st.caption(
    "El scatter nos refleja que: las celdas con más biomasa en 10 km (amarillas) son "
    "las de mayor margen. ."
)

st.divider()
st.subheader("El filtro triple: qué hace 'óptima' a una celda")
st.markdown(
    """
Una celda es **óptima solo si cumple las tres condiciones a la vez**:
"""
)

filtro_df = pd.DataFrame(
    [
        ["1 · Suministro robusto", "Stock proyectado a 2040 en su entorno", f"≥ {fmt_int(umb['stock'])} plazas (mediana)", "Que el purín siga estando en 15 años"],
        ["2 · Conexión barata", "Distancia al gasoducto", "≤ 2.000 m (umbral fijo)", "Que inyectar a red no se coma el CAPEX"],
        ["3 · Economía sólida", "Margen anual escenario base", f"≥ {fmt_eur(umb['margen'])} (percentil 75)", "Estar en el cuartil superior del negocio"],
    ],
    columns=["Condición", "Variable", "Umbral de esta corrida", "Qué riesgo cubre"],
)
st.dataframe(filtro_df, width="stretch", hide_index=True)

c1, c2 = st.columns(2)
c1.metric("Celdas óptimas", f"{n_optimas} de {fmt_int(n_total)}", f"{n_optimas/n_total*100:.1f} % del total")
c2.metric("Por qué tan pocas", "mediana ∩ p75 ∩ 2 km", help=(
    "La mediana ya descarta el 50 %, el p75 descarta el 75 %, y encima se exige gasoducto a "
    "menos de 2 km. La intersección es chica a propósito: buscamos el cuartil superior "
    "económico con suministro asegurado y conexión barata."
))

st.divider()
st.subheader("El mapa: óptimas vs resto de viables")

geo = viables[["cell_id", "geometry"]].merge(
    econ[["cell_id", "score", "viable", "margen_base_M€", "biomasa_10km", "dist_gasoducto", "stock_proyectado_15a"]],
    on="cell_id",
    how="inner",
)
geo["Estado"] = geo["viable"].map({0: "Viable (no óptima)", 1: "Óptima"})
centroid = geo.geometry.union_all().centroid

fig_map = px.choropleth_mapbox(
    geo,
    geojson=geo.geometry.__geo_interface__,
    locations=geo.index,
    color="Estado",
    color_discrete_map={"Viable (no óptima)": COLOR_NO_OPTIMA, "Óptima": COLOR_OPTIMA},
    mapbox_style="open-street-map",
    center={"lat": centroid.y, "lon": centroid.x},
    zoom=8.3,
    opacity=0.65,
    hover_name="cell_id",
    hover_data={
        "score": ":.1f",
        "margen_base_M€": ":.2f",
        "biomasa_10km": ":.0f",
        "dist_gasoducto": ":.0f",
    },
    labels={
        "score": "Score",
        "margen_base_M€": "Margen base (M€)",
        "biomasa_10km": "Biomasa 10 km",
        "dist_gasoducto": "Dist. gasoducto (m)",
    },
)
fig_map.update_layout(
    margin=dict(l=0, r=0, t=0, b=0),
    height=600,
    legend=dict(orientation="h", yanchor="bottom", y=1.01),
)
st.plotly_chart(fig_map, width="stretch")
st.caption(
    "Las óptimas (naranja) forman clústers claros — no son celdas sueltas con suerte, son "
    "zonas enteras donde coinciden purín denso, gasoducto al lado y buena economía."
)
st.subheader("Mapa Final solo celdas óptimas")
with st.expander("🌍 Mapa interactivo completo"):
    mapa_html = (DATA / "mapa_optimas_biometano.html")
    if mapa_html.exists():
        components.html(mapa_html.read_text(encoding="utf-8"), height=620, scrolling=False)
    else:
        st.info("Ejecutá el notebook FINAL para regenerar mapa_optimas_biometano.html")

st.divider()
st.subheader("Random Forest de apoyo...")
st.markdown(
    """
Entrenamos dos Random Forest sobre las 2.890 celdas: uno clasifica óptima/no óptima y otro
predice el margen. Aca  lo importante no es predecir, eltarget lo definimos nosotros, así que un
F1 alto no sorprende a nadie. La gracia es la **importancia de variables**: el modelo,
mirando solo los datos, redescubre que lo que separa una óptima de una que no lo es, son la
**biomasa porcina en 10 km** y la **distancia al gasoducto**. Exactamente las dos variables
que más pesaban en el score geoespacial del capítulo 2.
"""
)

st.image(
    str(IMG / "dashboard_pipeline_completo.png"),
    caption="Dashboard del pipeline completo: serie y proyección del censo, distribución de márgenes, "
            "importancia de variables de los RF y el cruce score vs margen con las óptimas marcadas",
    width="stretch",
)

fig_sc = px.scatter(
    econ,
    x="score",
    y="margen_base_M€",
    color=econ["viable"].map({0: "Viable (no óptima)", 1: "Óptima"}),
    color_discrete_map={"Viable (no óptima)": COLOR_NO_OPTIMA, "Óptima": COLOR_OPTIMA},
    labels={"score": "Score de idoneidad (cap. 2)", "margen_base_M€": "Margen base (M€/año)", "color": "Estado"},
    title="Score geoespacial vs margen económico — dos mundos que no siempre coinciden",
    opacity=0.55,
)
fig_sc.update_layout(height=430, legend_title=None)
st.plotly_chart(fig_sc, width="stretch")


st.divider()
st.success(
    f"**Nota**: de {fmt_int(n_total)} celdas viables, {n_optimas} son óptimas "
    "(~7 %): suministro asegurado a 2040, gasoducto a menos de 2 km y margen en el cuartil "
    "superior. Pero el margen es una foto con supuestos fijos — y el mundo real no fija nada. "
    "Lo que sigue es someter a esas óptimas a 25.000 futuros distintos."
)

sidebar_footer()
