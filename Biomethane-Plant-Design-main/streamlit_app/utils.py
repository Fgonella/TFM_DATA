"""Carga de datos compartida para la app de Streamlit v2.

Fuente única de la parte económica y de proyecciones:
notebooks/03_viability/TFM_viabilidad_economica_FINAL.ipynb

Todas las rutas son relativas a la carpeta ``data/`` del proyecto
Biomethane-Plant-Design, independientemente de desde dónde se lance
``streamlit run``.
"""
from pathlib import Path

import geopandas as gpd
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"
IMG = ROOT / "data" / "processed"


# Colores compartidos

CATEGORIA_COLORS = {
    "ÓPTIMO": "#1a9850",
    "BUENO": "#91cf60",
    "MODERADO": "#fee08b",
    "EXCLUIDO": "#bdbdbd",
}
COLOR_OPTIMA = "#e67e22"      # naranja — celda óptima
COLOR_NO_OPTIMA = "#4C72B0"   # azul — viable pero no óptima



# Cargas de datos — todas salidas reales del notebook FINAL

RAW = ROOT / "data" / "raw"
MAP_IMG = ROOT / "data" / "map"


@st.cache_data(show_spinner="Cargando delimitación de Huesca...")
def load_delimitacion() -> gpd.GeoDataFrame:
    """Límite provincial de Huesca — el lienzo de todo el análisis."""
    return gpd.read_file(RAW / "delimitations" / "Huesca_Delimitacion.geojson").to_crs(4326)


@st.cache_data(show_spinner="Cargando granjas porcinas...")
def load_granjas() -> gpd.GeoDataFrame:
    """Explotaciones porcinas georreferenciadas (REGA / Aragón Open Data)."""
    gdf = gpd.read_file(RAW / "01_ganado_porcino" / "clasificacion_porcino.gpkg").to_crs(4326)
    for c in ["capacidad_cebo", "capacidad_cerdas", "capacidad_lechones"]:
        if c in gdf.columns:
            gdf[c] = gdf[c].fillna(0)
    gdf["plazas_total"] = (
        gdf.get("capacidad_cebo", 0) + gdf.get("capacidad_cerdas", 0) + gdf.get("capacidad_lechones", 0)
    )
    return gdf


@st.cache_data(show_spinner="Cargando gasoductos...")
def load_gasoductos() -> gpd.GeoDataFrame:
    """Red de gasoductos de Huesca (OpenStreetMap / Overpass API)."""
    return gpd.read_file(RAW / "02_gasoductos" / "gasoductos_huesca.gpkg").to_crs(4326)


@st.cache_data(show_spinner="Cargando Red Natura 2000...")
def load_red_natura() -> gpd.GeoDataFrame:
    """Espacios protegidos Red Natura 2000 en Huesca (EEA / MITECO)."""
    return gpd.read_file(RAW / "04_red_natura2000" / "red_natura_huesca.gpkg").to_crs(4326)


@st.cache_data(show_spinner="Cargando scoring geoespacial...")
def load_scoring() -> pd.DataFrame:
    """Malla completa de 63.612 celdas con score y categoría (Parte 1)."""
    return pd.read_csv(DATA / "scoring_biometano.csv")


@st.cache_data(show_spinner="Cargando celdas viables...")
def load_viables_geo() -> gpd.GeoDataFrame:
    """Las 744 celdas viables con geometría (entrada del notebook FINAL)."""
    gdf = gpd.read_file(DATA / "viables_interseccion.gpkg")
    gdf["cell_id"] = gdf["cell_id"].astype(int)
    return gdf.to_crs(4326)


@st.cache_data(show_spinner="Cargando economía preliminar...")
def load_economia() -> pd.DataFrame:
    """Economía celda a celda de TODAS las viables + flag de óptima.

    Salida: resultados_viabilidad_economica_final.csv (sección de economía
    preliminar del notebook FINAL).
    """
    df = pd.read_csv(DATA / "resultados_viabilidad_economica_final.csv")
    df["cell_id"] = df["cell_id"].astype(int)
    return df


@st.cache_data(show_spinner="Cargando resultados de Monte Carlo...")
def load_mc_optimas() -> pd.DataFrame:
    """Monte Carlo sobre las celdas óptimas (25.000 sim. por sitio × escala)."""
    df = pd.read_csv(DATA / "viabilidad_final_montecarlo_optimas.csv")
    df["cell_id"] = df["cell_id"].astype(int)
    return df.sort_values("prob_VAN_positivo", ascending=False).reset_index(drop=True)


@st.cache_data(show_spinner="Cargando geometrías de las óptimas...")
def load_mc_optimas_geo() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(DATA / "viabilidad_final_montecarlo_optimas.gpkg")
    gdf["cell_id"] = gdf["cell_id"].astype(int)
    return gdf.to_crs(4326)


@st.cache_data(show_spinner="Cargando serie histórica del censo...")
def load_serie_censo() -> pd.DataFrame:
    """Serie semestral del censo porcino de Huesca (MAPA, encuestas ganaderas)."""
    df = pd.read_csv(DATA / "huesca_porcino_serie.csv", parse_dates=["fecha"])
    return df


@st.cache_data(show_spinner="Cargando proyección del censo...")
def load_proyeccion_censo() -> pd.DataFrame:
    """Proyección del stock porcino de Huesca a 15 años (modelo elegido)."""
    return pd.read_csv(DATA / "proyeccion_porcino_15anios.csv", parse_dates=["ds"])


def umbrales_optimo(df_econ: pd.DataFrame) -> dict:
    """Recalcula los umbrales de 'óptimo' igual que el notebook FINAL.

    Los dos relativos (mediana / p75) dependen de los datos de la corrida;
    el de gasoducto es fijo.
    """
    return {
        "stock": df_econ["stock_proyectado_15a"].quantile(0.50),
        "gasoducto": 2_000,
        "margen": max(0.0, df_econ["margen_base_€"].quantile(0.75)),
    }



# Parámetros del modelo financiero — sección 4 del notebook FINAL

VIDA_UTIL = 15
WACC = 0.08
TASA_IMPUESTO = 0.25
MANTENIMIENTO_PCT_CAPEX = 0.02
WORKING_CAPITAL_PCT_INGRESOS = 0.05
FACTOR_DISPONIBILIDAD = 0.85
N_SIM = 25_000

PLANTAS = {
    "Pequeña": {"capex": 3_000_000, "capacidad": 2_000_000},
    "Mediana": {"capex": 6_000_000, "capacidad": 5_000_000},
    "Grande": {"capex": 12_000_000, "capacidad": 10_000_000},
}

OPEX_FIJO_COMPONENTES = {
    "Personal": 400_000,
    "Seguros": 80_000,
    "Administración": 100_000,
    "Gestión digestato": 180_000,
    "Ambiental": 25_000,
}
OPEX_FIJO_BASE = sum(OPEX_FIJO_COMPONENTES.values())

# Variables inciertas del Monte Carlo — triangular (mín, moda, máx)

MC_DIST = {
    "Movilización del feedstock": (0.72, 0.85, 0.96, "Un promotor contrata la mayoría del purín cercano, pero no todo"),
    "Rendimiento (Nm³/t purín)": (15.0, 20.0, 25.0, "Conversión purín → biometano"),
    "Precio biometano (€/Nm³)": (0.55, 0.70, 0.85, "≈70 €/MWh, mediana de mercado con caída posible"),
    "GdOs (€/Nm³)": (0.02, 0.045, 0.07, "Mercado de garantías de origen volátil"),
    "OPEX variable (€/Nm³)": (0.10, 0.12, 0.16, "Los costes operativos suelen desviarse al alza"),
    "Sobrecoste de obra (×CAPEX)": (1.00, 1.03, 1.12, "Los proyectos de obra civil casi siempre se pasan"),
    "Subvenciones (€/año)": (0, 70_000, 110_000, "Incierto por política pública"),
    "Co-productos: CO₂ + digestato (€/año)": (80_000, 150_000, 240_000, "Ingresos adicionales por subproductos"),
}

# Curva de arranque de producción (años 1 a 15) — notebook FINAL
RAMP = [0.60, 0.60, 0.60, 0.60, 0.60, 0.70, 0.80, 0.80, 0.90, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00]

# Break-even de la mejor localización (celda 13846, Grande) — salida de la última
# corrida del notebook viabilidad_economica.ipynb
BREAKEVEN = {
    "precio_van0": 0.654,     # €/Nm³ para VAN esperado = 0
    "precio_p75": 0.671,      # €/Nm³ para P(VAN>0) = 75 %
    "precio_central": 0.70,   # moda de la triangular
}



# Contexto europeo del censo porcino (Eurostat, dic. 2024)

CENSO_ANCHOR_DATA = {
    # país: (año_base, censo_base_miles, año_reciente, censo_reciente_miles)
    "España":        (2014,  29200, 2024, 34500),
    "Alemania":      (2014,  28000, 2024, 21200),
    "Francia":       (2014,  13200, 2024, 11700),
    "Dinamarca":     (2014,  12300, 2024, 11500),
    "Países Bajos":  (2014,  11800, 2024, 10100),
    "UE-27 (total)": (2014, 143850, 2024, 132100),
}

CENSO_REGION_ARAGON = {
    "región": "Aragón (ES)",
    "censo_2024_miles": 9900,
    "share_UE_2024": 0.075,
    "fuente": "Eurostat, Agriculture statistics at regional level (dic. 2024)",
}



# Formato

def fmt_int(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".")


def fmt_eur(value: float) -> str:
    return f"{value:,.0f} €".replace(",", ".")


def fmt_eur_m(value: float) -> str:
    return f"{value / 1e6:,.2f} M€".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(value: float) -> str:
    return f"{value * 100:,.1f} %".replace(".", ",")


def sidebar_footer() -> None:
    st.sidebar.divider()
    st.sidebar.caption(
        "Trabajo final · Locacion y viabilidad de planta de biometano (Huesca)\n\n"
        "Integrantes:\n\n"
        "Rafael Sánchez Clavijo\n\n"
        "Bruno Olgiatti\n\n"
        "Fernando Gonella\n\n"
        
        
    )
