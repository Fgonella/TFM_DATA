import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils import (
    CENSO_ANCHOR_DATA,
    CENSO_REGION_ARAGON,
    load_serie_censo,
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

st.set_page_config(page_title="El punto de partida · Biometano Huesca", page_icon="🐷", layout="wide")

st.title("🐷 Seccion 1 · El punto de partida: granjas y purín disponible")
st.markdown(
    """
Antes de mirar mapas debemos saber si: **¿hay materia prima suficiente,
y que pasara en el futuro?** Una planta de biometano a partir de purín porcino solo tiene
sentido donde el censo porcino es grande y estable. Por su parte, España es un caso raro en Europa:
mientras la UE lleva una década reduciendo su censo porcino, **España es el único gran
productor que crece**.
"""
)

st.divider()
st.subheader("Censo Europeo se reduce, España crece (Eurostat, dic. 2024)")

filas = []
for pais, (a0, c0, a1, c1) in CENSO_ANCHOR_DATA.items():
    var = (c1 / c0 - 1) * 100
    filas.append({"País": pais, "Censo 2014 (miles)": c0, "Censo 2024 (miles)": c1, "Variación 10 años (%)": round(var, 1)})
df_ue = pd.DataFrame(filas)

col1, col2 = st.columns([2, 1])
with col1:
    plot_df = df_ue[df_ue["País"] != "UE-27 (total)"].copy()
    fig = go.Figure()
    fig.add_bar(x=plot_df["País"], y=plot_df["Censo 2014 (miles)"] / 1000, name="2014", marker_color="#bdbdbd")
    fig.add_bar(x=plot_df["País"], y=plot_df["Censo 2024 (miles)"] / 1000, name="2024", marker_color="#4C72B0")
    for _, row in plot_df.iterrows():
        es_espana = row["País"] == "España"
        fig.add_annotation(
            x=row["País"],
            y=max(row["Censo 2014 (miles)"], row["Censo 2024 (miles)"]) / 1000 + 1.5,
            text=f"{row['Variación 10 años (%)']:+.1f}%",
            showarrow=False,
            font=dict(color="#c0392b" if es_espana else "#333", size=14 if es_espana else 11),
        )
    fig.update_layout(
        barmode="group",
        yaxis_title="Millones de cabezas",
        title="Censo porcino 2014 vs 2024 — grandes productores UE",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=420,
    )
    st.plotly_chart(fig, width="stretch")

with col2:
    st.dataframe(df_ue, width="stretch", hide_index=True)
    st.caption(
        "La UE-27 pierde un 8 % de cabaña en diez años. España gana un 18 % en el mismo período "
        "y ya concentra el 26 % del censo europeo."
    )

st.info(
    f"**Aragón**, la región del proyecto, es **la mayor región porcina NUTS2 de toda la UE**: "
    f"{CENSO_REGION_ARAGON['censo_2024_miles']:,} mil cabezas, un "
    f"{CENSO_REGION_ARAGON['share_UE_2024']*100:.1f} % del total europeo. "
    "No estamos eligiendo un sitio exótico: estamos yendo a donde está el recurso."
    .replace(",", ".")
)

st.divider()
st.subheader("Dentro de Aragón: la serie histórica de Huesca (MAPA)")
st.markdown(
    """
Esta es la serie que alimenta todo el análisis de proyección del capítulo 3: el censo porcino
de la provincia de Huesca según las **encuestas ganaderas del MAPA**, con dato semestral
(mayo y noviembre).
"""
)

serie = load_serie_censo()

fig2 = px.line(
    serie,
    x="fecha",
    y="total_animales",
    markers=True,
    labels={"fecha": "Fecha", "total_animales": "Cabezas de porcino"},
    title="Censo porcino de Huesca — serie semestral MAPA",
)
fig2.update_traces(line_color="#2ca25f")
fig2.update_layout(height=430)
st.plotly_chart(fig2, width="stretch")

ultimo = serie.sort_values("fecha").iloc[-1]
primero = serie.sort_values("fecha").iloc[0]
crecimiento = (ultimo["total_animales"] / primero["total_animales"] - 1) * 100

c1, c2, c3 = st.columns(3)
c1.metric("Inicio de la serie", f"{primero['fecha']:%b %Y}", f"{primero['total_animales']/1e6:.2f} M cabezas")
c2.metric("Último dato", f"{ultimo['fecha']:%b %Y}", f"{ultimo['total_animales']/1e6:.2f} M cabezas")
c3.metric("Crecimiento acumulado", f"{crecimiento:+.0f} %")

with st.expander("Ver composición por tipo de animal"):
    tipos = ["lechones", "cerdos_20_49kg", "cebo_total", "cerdas_reproductoras"]
    fig3 = px.area(
        serie,
        x="fecha",
        y=tipos,
        labels={"value": "Cabezas", "fecha": "Fecha", "variable": "Tipo"},
        title="Composición del censo por categoría",
    )
    fig3.update_layout(height=400)
    st.plotly_chart(fig3, width="stretch")
    st.caption(
        "Cada tipo produce un volumen de purín distinto (cerdas ~16 L/día, cebo ~4,5, "
        "lechones ~1,5) — por eso el modelo económico no cuenta cabezas a secas, "
        "las convierte a purín por categoría."
    )

st.divider()
st.success(
    "**Nota:** el recurso existe y crece. España es el único gran productor "
    "porcino de la UE en expansión, Aragón es la mayor región porcina de Europa, y la serie "
    "histórica de Huesca lo confirma provincia adentro. La pregunta ya no es si hay purín — "
    "es dónde ponerle la planta."
)

sidebar_footer()
