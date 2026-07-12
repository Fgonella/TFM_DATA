import pandas as pd
import plotly.express as px
import streamlit as st

from utils import (
    BREAKEVEN,
    N_SIM,
    fmt_eur_m,
    fmt_int,
    fmt_pct,
    load_economia,
    load_mc_optimas,
    load_mc_optimas_geo,
    sidebar_footer,
)

st.set_page_config(page_title="Conclusiones · Biometano Huesca", page_icon="🏆", layout="wide")

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

st.title("🏆 Sección 7 · El ranking final y concluciones")

mc = load_mc_optimas()
econ = load_economia()
mejor = mc.iloc[0]
n_rentables = int((mc["prob_VAN_positivo"] >= 0.5).sum())

st.markdown(
    f"""
El analisis completo, en una línea: 

    Se analizan {fmt_int(len(econ))} celdas viables → {len(mc)} óptimas →{fmt_int(N_SIM)} simulaciones por sitio → un ranking por probabilidad de éxito. 
Hay que tene en cuenta que el ranking **no ordena por VAN**, ordena por **P(VAN > 0)**
"""
)

st.divider()
st.subheader("La recomendación de inversión")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Celda recomendada", f"{int(mejor['cell_id'])}")
c2.metric("Escala", str(mejor["escala_optima"]))
c3.metric("P(VAN > 0)", fmt_pct(mejor["prob_VAN_positivo"]))
c4.metric("VAN esperado", fmt_eur_m(mejor["VAN_esperado"]))

c1, c2, c3, c4 = st.columns(4)
c1.metric("VAN mediana (P50)", fmt_eur_m(mejor["VAN_p50"]))
c2.metric("Rango probable (P5–P95)", f"{mejor['VAN_p5']/1e6:.1f} a {mejor['VAN_p95']/1e6:.1f} M€")
c3.metric("TIR mediana", fmt_pct(mejor["TIR_p50"]))
c4.metric("Utilización media de planta", fmt_pct(mejor["utilizacion_media"]))

st.warning(
    f"**Condición no negociable**: asegurar la venta del biometano por encima del break-even "
    f"(~{BREAKEVEN['precio_van0']:.2f} €/Nm³) con contrato a largo plazo o subvención "
    "equivalente **antes** de comprometer el CAPEX. Con eso firmado, la inversión se apoya en "
    "probabilidad, no en esperanza."
)

st.divider()
st.subheader("El top de localizaciones, sobre el mapa")

geo = load_mc_optimas_geo()
geo_plot = geo.merge(
    mc[["cell_id", "prob_VAN_positivo", "VAN_esperado", "escala_optima"]],
    on="cell_id",
    how="inner",
    suffixes=("", "_mc"),
)
# nos quedamos con las columnas del merge (por si el gpkg ya las trae)
geo_plot["P_exito_%"] = geo_plot["prob_VAN_positivo"] * 100
geo_plot["VAN_M"] = geo_plot["VAN_esperado"] / 1e6
centroid = geo_plot.geometry.union_all().centroid

fig_map = px.choropleth_mapbox(
    geo_plot,
    geojson=geo_plot.geometry.__geo_interface__,
    locations=geo_plot.index,
    color="P_exito_%",
    color_continuous_scale="RdYlGn",
    range_color=(0, 100),
    mapbox_style="open-street-map",
    center={"lat": centroid.y, "lon": centroid.x},
    zoom=8.5,
    opacity=0.75,
    hover_name="cell_id",
    hover_data={"P_exito_%": ":.1f", "VAN_M": ":.2f", "escala_optima": True},
    labels={"P_exito_%": "P(VAN>0) %", "VAN_M": "VAN esperado (M€)", "escala_optima": "Escala"},
)
fig_map.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=580)
st.plotly_chart(fig_map, width="stretch")
st.caption(
    "Las celdas óptimas coloreadas por probabilidad de éxito tras el Monte Carlo. "
    "Verde: la inversión tiene las probabilidades a favor."
)

with st.expander("Ver ranking completo (todas las óptimas simuladas)"):
    tabla = mc.copy()
    tabla["VAN esperado (M€)"] = (tabla["VAN_esperado"] / 1e6).round(2)
    tabla["VAN P50 (M€)"] = (tabla["VAN_p50"] / 1e6).round(2)
    tabla["P(VAN>0) %"] = (tabla["prob_VAN_positivo"] * 100).round(1)
    tabla["TIR P50 %"] = (tabla["TIR_p50"] * 100).round(1)
    st.dataframe(
        tabla[["cell_id", "escala_optima", "score_idoneidad", "VAN esperado (M€)",
               "VAN P50 (M€)", "P(VAN>0) %", "TIR P50 %"]],
        width="stretch",
        hide_index=True,
    )
    st.caption(f"{n_rentables} de {len(mc)} óptimas terminan con P(VAN>0) ≥ 50 %.")

st.divider()
st.subheader("Las cuatro conclusiones del trabajo")

st.markdown(
    """
**1 · La localización no es el problema.** El cruce del filtro geoespacial con la economía
preliminar deja un conjunto sólido de celdas óptimas: biomasa de sobra en 10 km, gasoducto
cerca y sin restricciones ambientales serias. Y como los números se calcularon con el purín
*actual*, si el censo crece como proyecta el modelo, los resultados solo pueden mejorar.

**2 · El negocio es una apuesta al precio.** El tornado lo dice clarito: el VAN vive y muere
con el precio del biometano (y en menor medida con las GdOs). Todo lo demás mueve la aguja,
pero no define el proyecto.

**3 · La escala importa, pero se resuelve sola.** La economía de escala empuja a plantas
grandes donde hay biomasa de sobra; donde no alcanza, una mediana evita cargar con un CAPEX
medio vacío. El modelo lo decide sitio a sitio y no hace falta forzarlo.

**4 · El número a mirar no es el VAN, es P(VAN > 0).** Un VAN esperado positivo con una
probabilidad de pérdida cercana al 50 % no es una inversión, es una moneda al aire. Por eso
el ranking ordena por probabilidad de éxito, y la recomendación queda condicionada a asegurar
el precio de venta **antes** de mover un euro de CAPEX.
"""
)

st.divider()
st.subheader("Fuentes de todos los supuestos")
st.markdown(
    "Ningún número del modelo está inventado — cada supuesto financiero, técnico y de coste "
    "tiene fuente sectorial. Están acá para la ronda de preguntas:"
)

with st.expander("💶 Parámetros financieros"):
    st.dataframe(pd.DataFrame(
        [
            ["Horizonte de evaluación", "15 años", "EBA + plazos de project finance bancario"],
            ["WACC (tasa de descuento)", "8 %", "Valoración de renovables (PwC / EY), fondos de infraestructura"],
            ["Impuesto de Sociedades + amortización lineal", "25 % · 6,67 %/año", "Ley del IS · tablas de la Agencia Tributaria"],
            ["Mantenimiento (O&M)", "2 % del CAPEX/año", "Ratios O&M agroindustriales (Miogas, Biovic)"],
            ["Fondo de maniobra (NOF)", "5 % de ingresos", "Estándar de tesorería corporativa (utilities)"],
        ],
        columns=["Parámetro", "Valor", "Fuente"],
    ), width="stretch", hide_index=True)

with st.expander("🐖 Supuestos técnicos del feedstock porcino"):
    st.dataframe(pd.DataFrame(
        [
            ["Rendimiento de biometano", "~20 Nm³/t purín (central; rango 15–25)", "IDAE, fichas de AguaSigma (15–30 Nm³/t)"],
            ["Coste de adquisición del purín", "0 €/t (subproducto)", "AEBIG, SEDIGAS — el ganadero se ahorra un pasivo ambiental"],
            ["Coste de transporte", "0,18 €/t·km", "Observatorio de Costes del Transporte (Mitma)"],
            ["Coste de pretratamiento", "2,5 €/t", "Ingeniería agroindustrial (Miogas), rango 2–4 €/t"],
            ["Factor de disponibilidad", "85 %", "Métrica prudencial (PwC, Biovic): vacíos sanitarios, mermas"],
        ],
        columns=["Parámetro", "Valor", "Fuente"],
    ), width="stretch", hide_index=True)

with st.expander("🏭 Escalas de planta (economías de escala)"):
    st.dataframe(pd.DataFrame(
        [
            ["Pequeña", "3 M€", "2 M Nm³/año", "2,00 €/Nm³", "AEBIG (plantas on-farm / cooperativas), EBA"],
            ["Mediana", "6 M€", "5 M Nm³/año", "1,60 €/Nm³", "Biovic / PwC (estándar ibérico)"],
            ["Grande", "12 M€", "10 M Nm³/año", "1,50 €/Nm³", "EBA (plantas industriales de inyección en red)"],
        ],
        columns=["Escala", "CAPEX", "Capacidad", "CAPEX específico", "Fuente"],
    ), width="stretch", hide_index=True)

with st.expander("🔌 Costes de conexión y penalizaciones geoespaciales del CAPEX"):
    st.dataframe(pd.DataFrame(
        [
            ["Conexión a gasoducto", "300.000 €/km", "SEDIGAS, CNMC (300–450 k€/km)"],
            ["Conexión eléctrica (MT)", "80.000 €/km", "MITECO, distribuidoras (i-DE, Endesa)"],
            ["Conexión de agua", "60.000 €/km", "Confederaciones hidrográficas, Canal Isabel II / ACA"],
            ["Acceso por carretera", "80.000 €/km", "Bancos de precios de obra pública (IVE, ITeC)"],
            ["Pendiente ≤5 / 5–10 / >10 %", "+1 / +2,5 / +5 % del CAPEX", "ITeC / IVE, SEDIGAS"],
            ["Restricción ambiental baja", "+1 % CAPEX · 25.000 €/año OPEX", "AEBIG, MITECO, MTD/BAT de la CE"],
        ],
        columns=["Concepto", "Coste", "Fuente"],
    ), width="stretch", hide_index=True)
    st.caption(
        "Las distancias de conexión eléctrica y de agua no estaban cartografiadas: se asumen "
        "2 km uniformes para todos los sitios — al ser iguales, no distorsionan el ranking. "
        "El acarreo del purín se aproxima como medio radio de captación (5 km)."
    )

st.divider()
st.success(
    f"**Nota Final**: el análisis recorre sin saltos el camino completo — del censo europeo a una "
    f"celda concreta ({int(mejor['cell_id'])}, escala {mejor['escala_optima']}) con "
    f"{fmt_pct(mejor['prob_VAN_positivo'])} de probabilidad de éxito y un VAN esperado de "
    f"{fmt_eur_m(mejor['VAN_esperado'])}. La decisión final no es un acto de fe: es una "
    "probabilidad medida, con sus condiciones explícitas."
)

sidebar_footer()
