import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from utils import (
    MAP_IMG,
    fmt_int,
    load_delimitacion,
    load_gasoductos,
    load_granjas,
    load_red_natura,
    sidebar_footer,
)

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

st.set_page_config(page_title="Los datos de Huesca · Biometano", page_icon="📦", layout="wide")

st.title("📦 Seccion 0 · Los datos: seis capas y una provincia")
st.markdown(
    """
Antes de realizar el analizis hubo que **construir el dataset**, la parte "Donwload" del proyecto,
descarga, limpia y georeferencia seis capas de informacio sobre un mismo lienzo, **delimitación de la provincia de Huesca**.
Esta capa se forma a partir de:

    1. Ganados Porcinos
    2. Gasoductos
    3. Pendientes
    4. Red natural
    5. Red vial
    6. Clasificacion del suelo

Todo el analisis que se hace posterior (el score, las celdas viables, las óptimas, el Monte Carlo) se apoya en estas capas.

Cabe destacar que una viene de una fuente pública distinta, con su propio formato y sistema de
coordenadas — parte del trabajo fue unificarlas todas en **EPSG:25830** (UTM 30N, la proyección oficial peninsular) 
para poder cruzarlas celda a celda.
"""
)

st.divider()
st.subheader("Las seis capas y de dónde sale cada una (fuentes)")

capas_df = pd.DataFrame(
    [
        ["1 · Ganado porcino", "2.218 explotaciones georreferenciadas, con plazas por tipo (cebo, cerdas, lechones)", "REGA · Aragón Open Data + encuestas MAPA", "La materia prima: define la biomasa en 10 km de cada celda"],
        ["2 · Gasoductos", "97 tramos de la red de transporte y distribución", "OpenStreetMap (Overpass API)", "Dónde se puede inyectar el biometano — el criterio con más peso"],
        ["3 · Pendiente (DEM)", "Modelo digital del terreno a 5 m: 130+ teselas → mosaico y mapa de pendientes (~900 MB)", "IGN / IDEE (servicio WCS del MDT05)", "Encarece o excluye la obra civil"],
        ["4 · Red Natura 2000", "102 espacios protegidos (ZEC y ZEPA)", "EEA / MITECO", "Exclusión ambiental directa"],
        ["5 · Red viaria", "Carreteras aptas para camiones, por categoría", "OpenStreetMap (osmnx)", "El purín llega en cisterna: sin buena vía no hay logística"],
        ["6 · Clasificación del suelo", "Planeamiento urbanístico + buffers de 528 núcleos de población", "ICEAragon / IDEAragon (WFS) + INE", "Dónde está permitido construir"],
    ],
    columns=["Capa", "Qué contiene", "Fuente", "Para qué se usa después"],
)
st.dataframe(capas_df, width="stretch", hide_index=True)

st.divider()
st.subheader("Las diferentes capas, juntas en un mapa")
st.markdown(
    """
En la siguente imagen vemos:

La delimitación provincial (línea negra), las **granjas porcinas** (puntos, tamaño según
plazas), la **red de gasoductos** (naranja) y la **Red Natura 2000** (verde). Con una sola
observacion ya se intuye el resultado del capítulo 2: el negocio va a estar donde los puntos
se amontonan cerca de las líneas naranjas, lejos del verde.
"""
)

st.caption("Marca las capas que deceas ver:")


delim = load_delimitacion()
granjas = load_granjas()
gas = load_gasoductos()
natura = load_red_natura()

fig = go.Figure()

# Red Natura 2000 — polígonos rellenos
lat_n, lon_n = [], []
for geom in natura.geometry:
    polys = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
    for poly in polys:
        xs, ys = poly.exterior.xy
        lon_n.extend(list(xs) + [None])
        lat_n.extend(list(ys) + [None])
fig.add_trace(go.Scattermapbox(
    lon=lon_n, lat=lat_n, mode="lines", fill="toself",
    fillcolor="rgba(26, 152, 80, 0.25)",
    line=dict(color="#1a9850", width=1),
    name="Red Natura 2000",
    hoverinfo="skip",
))

# Gasoductos — líneas
lat_g, lon_g = [], []
for geom in gas.geometry:
    lines = geom.geoms if geom.geom_type == "MultiLineString" else [geom]
    for line in lines:
        xs, ys = line.xy
        lon_g.extend(list(xs) + [None])
        lat_g.extend(list(ys) + [None])
fig.add_trace(go.Scattermapbox(
    lon=lon_g, lat=lat_g, mode="lines",
    line=dict(color="#e67e22", width=3),
    name="Gasoductos (OSM)",
    hoverinfo="skip",
))

# Granjas — puntos escalados por plazas
granjas_plot = granjas[granjas["plazas_total"] > 0].copy()
size = (granjas_plot["plazas_total"] / granjas_plot["plazas_total"].max() * 14 + 3).clip(3, 17)
fig.add_trace(go.Scattermapbox(
    lon=granjas_plot.geometry.x, lat=granjas_plot.geometry.y,
    mode="markers",
    marker=dict(size=size, color="#4C72B0", opacity=0.55),
    name="Granjas porcinas (REGA)",
    text=[
        f"{m} · {fmt_int(p)} plazas"
        for m, p in zip(granjas_plot["municipio"], granjas_plot["plazas_total"])
    ],
    hoverinfo="text",
))

# Delimitación de Huesca — borde
lat_d, lon_d = [], []
for geom in delim.geometry:
    polys = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
    for poly in polys:
        xs, ys = poly.exterior.xy
        lon_d.extend(list(xs) + [None])
        lat_d.extend(list(ys) + [None])
fig.add_trace(go.Scattermapbox(
    lon=lon_d, lat=lat_d, mode="lines",
    line=dict(color="#222222", width=2.5),
    name="Delimitación de Huesca",
    hoverinfo="skip",
))

centroid = delim.geometry.union_all().centroid
fig.update_layout(
    mapbox=dict(style="open-street-map", center=dict(lat=centroid.y, lon=centroid.x), zoom=7.8),
    margin=dict(l=0, r=0, t=0, b=0),
    height=640,
    legend=dict(orientation="h", yanchor="bottom", y=1.01, bgcolor="rgba(255,255,255,0.7)"),
)
st.plotly_chart(fig, width="stretch")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Granjas porcinas", fmt_int(len(granjas)))
c2.metric("Plazas totales", fmt_int(granjas["plazas_total"].sum()))
c3.metric("Tramos de gasoducto", fmt_int(len(gas)))
c4.metric("Espacios Red Natura", fmt_int(len(natura)))

st.divider()
st.subheader("Capas individuales al descargarlas:")

col1, col2 = st.columns(2)
with col1:
    st.image(
        str(MAP_IMG / "01_ganado_porcino" / "kde_porcino_huesca.png"),
        caption="Densidad de ganado porcino (KDE) — ya se ven los clústers del sur de la provincia",
        width="stretch",
    )
with col2:
    st.image(
        str(MAP_IMG / "02_gasoductos" / "gasoductos_osm_huesca.png"),
        caption="Red de gasoductos descargada de OSM — el corredor que ordena todo el análisis",
        width="stretch",
    )

col1, col2 = st.columns(2)
with col1:
    st.image(
        str(MAP_IMG / "01_ganado_porcino" / "huesca_ganadero_especies.png"),
        caption="Explotaciones ganaderas por especie — el porcino domina la provincia",
        width="stretch",
    )
with col2:
    st.image(
        str(MAP_IMG / "01_ganado_porcino" / "huesca_estabulado_pastoreo_definitivo.png"),
        caption="Sistema productivo: estabulado vs pastoreo — el purín aprovechable sale del estabulado",
        width="stretch",
    )

st.markdown(
    "Debajo podemos activar el Mapa interactivo de **Red natural**"
)

if st.toggle("🌍 Cargar mapa interactivo de la Red Natura 2000 (Folium, ~9 MB — puede tardar)"):
    mapa_natura = MAP_IMG / "04_red_natura2000" / "mapa_red_natura.html"
    if mapa_natura.exists():
        components.html(mapa_natura.read_text(encoding="utf-8"), height=620, scrolling=False)
    else:
        st.info("Ejecutá el notebook 04_red_natura2000 para regenerar el mapa.")

st.divider()

st.success(
    "**La pendiente**: El DEM a 5 m del IGN son más de 130 teselas (~900 MB entre mosaico y"
    "mapa de pendientes) — demasiado pesado para pintarlo acá en vivo."
)

sidebar_footer()
