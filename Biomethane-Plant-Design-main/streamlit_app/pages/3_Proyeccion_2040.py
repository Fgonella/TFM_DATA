import plotly.graph_objects as go
import streamlit as st

from utils import IMG, fmt_int, load_proyeccion_censo, load_serie_censo, sidebar_footer

st.set_page_config(page_title="Proyección 2040 · Biometano Huesca", page_icon="📈", layout="wide")

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

st.title("📈 Sección 3 · Proyección Censo animales a 2040")
st.markdown(
    """
En la siguiete seccion, se proyecto el censo hasta el año 2040, 
Se utilizaron diferentes metodos de forecasting: **Regresión Lineal, Random Forest y Gradient
Boosting**, los dos últimos tuneados con **Optuna**, y todos validados con **ventanas
temporales** (entrenar con el pasado, predecir el futuro.
"""
)

st.divider()
st.subheader("La competición de modelos")

col1, col2 = st.columns(2)
with col1:
    st.image(str(IMG / "comparacion_modelos.png"), caption="Comparación de modelos — error en validación y test", width="stretch")
with col2:
    st.image(str(IMG / "validacion_modelo_elegido.png"), caption="Validación del modelo elegido sobre el tramo de test", width="stretch")

st.markdown(
    """
El ganador fue la **Regresión Lineal**, con un MAPE en test de **~1,6 %**:
la serie de Huesca es un crecimiento sostenido y bastante limpio, sin estacionalidad, 

"""
)

st.divider()
st.subheader("La proyección: histórico + 15 años")

serie = load_serie_censo()
proy = load_proyeccion_censo()

fig = go.Figure()
fig.add_scatter(
    x=serie["fecha"], y=serie["total_animales"],
    mode="lines+markers", name="Histórico (MAPA)",
    line=dict(color="#2ca25f"),
)
fig.add_scatter(
    x=proy["ds"], y=proy["yhat"],
    mode="lines", name="Proyección (Regresión Lineal)",
    line=dict(color="#e67e22", dash="dash", width=3),
)
fig.update_layout(
    yaxis_title="Cabezas de porcino",
    xaxis_title="Fecha",
    title="Censo porcino de Huesca — histórico y proyección a 2040",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=470,
)
st.plotly_chart(fig, width="stretch")

stock_actual = float(serie.sort_values("fecha")["total_animales"].iloc[-1])
stock_2040 = float(proy["yhat"].iloc[-1])

c1, c2, c3 = st.columns(3)
c1.metric("Stock actual de la provincia", f"{stock_actual/1e6:.2f} M cabezas")
c2.metric("Stock proyectado a 2040", f"{stock_2040/1e6:.2f} M cabezas")
c3.metric("Crecimiento proyectado", f"{(stock_2040/stock_actual - 1)*100:+.0f} %")

st.warning(
    "**Nota sobre el rol de esta proyección**: la proyección se usa "
    "como **filtro de robustez del suministro** (Para saber si vamos a disponer de purín)"
    "**no** para calcular ingresos. Toda la parte económica se calcula con el purín "
    "**actual**. Si el censo crece como proyecta el modelo, los resultados financieros solo "
    "pueden mejorar. El modelo conservador."
)

with st.expander("¿Cómo se baja la proyección provincial a cada celda?"):
    st.markdown(
        f"""
Calculo simpre: cada celda tiene su biomasa actual en 10 km. Se calcula qué
**proporción** del stock provincial representa, y se le aplica esa misma proporción al stock
proyectado de 2040:

```
stock_proyectado_celda = (biomasa_10km / stock_provincial_actual) × stock_provincial_2040
```

Con el stock actual de {fmt_int(stock_actual)} cabezas y el proyectado de
{fmt_int(stock_2040)}, cada celda "hereda" el crecimiento provincial de forma proporcional.
No pretendemos saber qué granja concreta va a crecer — solo que la marea sube para todas.
"""
    )

st.divider()
st.success(
    "**Nota**: el suministro es robusto. Tres modelos compitieron con "
    "validación temporal seria, ganó el más simple con ~1,6 % de error en test, y la proyección "
    "dice que el censo de Huesca sigue creciendo hasta 2040"
)

sidebar_footer()
