import streamlit as st

from utils import BREAKEVEN, IMG, MC_DIST, sidebar_footer

st.set_page_config(page_title="Sensibilidad y break-even · Biometano Huesca", page_icon="📉", layout="wide")

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

st.title("📉 Sección 6 · ¿Qué variable manda? Sensibilidad y break-even")
st.markdown(
    """
25.000 simulaciones dan mucho más que una distribución: permiten preguntar **qué variable
explica que una simulación acabe en la cola buena o en la mala**. Para ver esto, el siguiente grafico
— se mueve cada variable de su percentil bajo a su percentil alto,
manteniendo el resto incierto, y se mide cuánto se desplaza el VAN.
"""
)

st.divider()
st.subheader("El tornado: una variable manda y las demás acompañan")

st.image(
    str(IMG / "mc_tornado_sensibilidad.png"),
    caption="Sensibilidad del VAN a cada variable incierta (percentil bajo → alto)",
    width="stretch",
)

precio_min, precio_moda, precio_max = MC_DIST["Precio biometano (€/Nm³)"][:3]
st.markdown(
    f"""
El resultado destacable es que: **el VAN depende del precio del biometano** (sorteado entre {precio_min:.2f} y {precio_max:.2f} €/Nm³,
moda {precio_moda:.2f}). Las garantías de origen aportan un segundo empujón, y el resto:
rendimiento, movilización del purín, sobrecostes de obra, tienen influencia pero no definen a la inversión

"""
)

st.divider()
st.subheader("Break-even: ¿a qué precio empezamos a ganar?")

st.image(
    str(IMG / "mc_breakeven_precio.png"),
    caption="VAN esperado y P(VAN>0) en función del precio de venta — todo lo demás sigue incierto",
    width="stretch",
)

c1, c2, c3 = st.columns(3)
c1.metric(
    "Precio break-even (VAN esperado = 0)",
    f"{BREAKEVEN['precio_van0']:.3f} €/Nm³",
    help="Última corrida del notebook FINAL, mejor localización con curva de arranque incluida",
)
c2.metric("Precio para P(éxito) = 75 %", f"{BREAKEVEN['precio_p75']:.3f} €/Nm³")
c3.metric("Precio central asumido", f"{BREAKEVEN['precio_central']:.2f} €/Nm³")

st.markdown(
    f"""
La lectura es directa: el proyecto **necesita colocar el biometano por encima de
~{BREAKEVEN['precio_van0']:.2f} €/Nm³** para no destruir valor, y a partir de
~{BREAKEVEN['precio_p75']:.2f} €/Nm³ la apuesta ya es cómoda (75 % de probabilidad de éxito).
El precio central de mercado asumido ({BREAKEVEN['precio_central']:.2f} €/Nm³) queda por
encima de ambos — hay colchón, pero es **finito**: una caída sostenida del precio de ~8 % se
lo come.
"""
)

st.divider()
st.success(
    "**Nota**: el negocio es, esencialmente, una apuesta al precio del "
    "biometano. El análisis lo cuantifica: break-even en ~0,65 €/Nm³, comodidad a partir de "
    "~0,67. Todo lo que sea asegurar precio (PPA, subvención, GdOs contratadas) convierte "
    "riesgo en valor — y es la palanca número uno del proyecto."
)

sidebar_footer()
