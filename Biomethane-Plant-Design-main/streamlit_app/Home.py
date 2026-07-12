import streamlit as st

from utils import (
    fmt_eur_m,
    fmt_int,
    fmt_pct,
    load_economia,
    load_mc_optimas,
    load_scoring,
    sidebar_footer,
)

st.set_page_config(
    page_title="Biometano Huesca · Trabajo final",
    page_icon="🌱",
    layout="wide",
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




st.title(' Trabajo Final: Master Data Science')
st.header(' "Del Purin a la Planta de Biometano"')


st.caption(
"""
    <p style='text-align: center; font-size: 0.85rem; font-family: sans-serif;'>
        Participantes: Rafa, Bruno, Fernando 
    </p>
    """, 
    unsafe_allow_html=True
)

st.caption(
    '''
El objetivo del suiguente analisis es comprobar si a partir del ganado (purín) tenemos viabilidad economica real,
para la puesta en marcha de una Planta de Biometano.  Es decir partimos de una localización óptima y obtenemos una viabilidad económico-financiera.
    
''')

st.markdown(
    """
El Trabajo busca responder las siguientes tres preguntas:

    1. ¿Dónde conviene poner una planta de biometano a partir de purín porcino?
    2. ¿La materia prima va a seguir estando dentro de 15 años?
    3. Y la que de verdad importa: ¿qué probabilidad hay de ganar (o perder) dinero?

Como vamos a ver a lo largo del trabajo, Huesca es un caso ideal para preguntárselo: está en el corazón de Aragón, 
**la mayor región porcina de toda la UE**, y España es el único gran productor europeo cuya cabaña sigue creciendo.

"""
)

scoring = load_scoring()
econ = load_economia()
mc = load_mc_optimas()

n_total = len(scoring)
n_viables = len(econ)
n_optimas = int(econ["viable"].sum())
mejor = mc.iloc[0]

#st.divider()
#st.subheader("El embudo completo, en una mirada")

#c1, c2, c3, c4 = st.columns(4)
#c1.metric("Celdas analizadas (500×500 m)", fmt_int(n_total))
#c2.metric("Celdas viables", fmt_int(n_viables))
#c3.metric(
#    "Celdas óptimas",
#    fmt_int(n_optimas),
#    help="Cumplen a la vez: suministro robusto a 2040, gasoducto a ≤2 km y margen en el cuartil superior",
#)
#c4.metric(
#    "Mejor sitio · P(VAN > 0)",
#    fmt_pct(mejor["prob_VAN_positivo"]),
#    help=f"Celda {int(mejor['cell_id'])} — escala {mejor['escala_optima']}",
#)

#c1, c2, c3 = st.columns(3)
#c1.metric("VAN esperado del mejor sitio", fmt_eur_m(mejor["VAN_esperado"]))
#c2.metric("TIR mediana del mejor sitio", fmt_pct(mejor["TIR_p50"]))
#c3.metric("Escala recomendada", str(mejor["escala_optima"])) 



st.divider()
st.subheader("Paso a Paso hacia las conclusiones")

st.markdown(
    """
| Secciones | La pregunta que responde |
|---|---|
| 📦 **0 · Los datos de Huesca** | Las seis capas descargadas (granjas, gasoductos, DEM, Red Natura, viario, suelo) sobre la delimitación provincial |
| 🐷 **1 · El punto de partida** | ¿Por qué purín, por qué España, por qué Huesca? El contexto del censo porcino europeo |
| 🗺️ **2 · Idoneidad geoespacial** | De 63.612 celdas a 2.890 viables: exclusiones, score ponderado y el mapa de candidatas |
| 📈 **3 · Proyección a 2040** | ¿El purín va a seguir estando? Forecasting del censo de Huesca con validación temporal |
| 💰 **4 · Economía y celdas óptimas** | Cuenta de resultados celda a celda y el filtro triple que deja solo las óptimas |
| 🎲 **5 · Monte Carlo** | 25.000 futuros por sitio: la distribución del VAN, no un número suelto |
| 📉 **6 · Sensibilidad y break-even** | Qué variable manda de verdad y a qué precio el proyecto empieza a ganar |
| 🏆 **7 · Conclusiones** | El ranking final, la recomendación de inversión y lo que aprendimos |
"""
)


sidebar_footer()
