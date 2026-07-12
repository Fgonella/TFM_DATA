# TFM Biometano Huesca

**Qué es:** pipeline de ciencia de datos que identifica las **localizaciones óptimas para plantas
de biometano a partir de purín porcino en la provincia de Huesca** y evalúa su viabilidad económica
bajo incertidumbre y una app narrativa en Streamlit.

**Las tres preguntas que responde:**

1. ¿Dónde conviene poner una planta de biometano a partir de purín porcino?
2. ¿La materia prima seguirá estando dentro de 15 años?
3. ¿Qué probabilidad hay de ganar (o perder) dinero?

---

## El pipeline en tres partes

De 63.612 celdas de 500 m a una recomendación de inversión, en un embudo de tres etapas:

| | Parte 1 — Geoespacial | Parte 2 — Selección | Parte 3 — Financiera |
|---|---|---|---|
| **Pregunta** | ¿Dónde se puede? | ¿Dónde conviene y seguirá habiendo purín? | ¿Se gana dinero y con qué probabilidad? |
| **Método** | Malla 500 m, 6 capas, exclusiones + scoring + K-Means | Proyección del censo + economía preliminar + Random Forest | Monte Carlo 25.000 sim. × 3 escalas, DCF a 15 años |
| **Entra → Sale** | 63.612 → **2.890 viables** | 2.890 → **209 óptimas** | 209 → **ranking + recomendación** |
| **Resultado** | Mapa de idoneidad | Drivers: biomasa 10 km + gasoducto | Celda 13806 · Grande · P(VAN>0)=76,9 % |

---

## Estructura del repositorio

```
notebooks/
├── 01_download/              Descarga de las 6 capas base
│   ├── 01_ganado_porcino.ipynb
│   ├── 02_gasoductos.ipynb
│   ├── 03_pendiente_dem.ipynb
│   ├── 04_red_natura2000.ipynb
│   ├── 05_red_viaria.ipynb
│   └── 06_clasificacion_suelo.ipynb
├── 02_analysis/              Grid 500 m, scoring, K-Means y mapa
│   └── idoneidad_scoring_clustering.ipynb
└── 03_viability/             Proyección + óptimas + Monte Carlo
    └── viabilidad_economica.ipynb   (notebook FINAL: modelo Monte Carlo)

data/
├── raw/                      Salidas de los notebooks de descarga (una subcarpeta por notebook)
├── map/                      Mapas HTML/PNG generados
└── processed/                Grid, celdas viables, óptimas, resultados y gráficos

streamlit_app/                App narrativa (se lanza desde Home.py)
```

**CRS:** todo lo vectorial se reproyecta a **EPSG:25830** (UTM 30N) para medir distancias en metros;
el mapa final usa EPSG:4326.

---

## Parte 1 — Análisis geoespacial de idoneidad

Notebooks `01_download/` (construcción del dataset) y `02_analysis/idoneidad_scoring_clustering.ipynb`
(análisis).

Sobre la provincia se tiende una malla de **63.612 celdas de 500×500 m** y a cada una se le cruzan
seis capas: biomasa porcina en 10 km, distancia y categoría del gasoducto y la carretera, pendiente
(DEM), clasificación del suelo y Red Natura 2000. La lógica es de dos pasos:

- **Exclusiones duras** (lo que no puede ser): dentro de Red Natura, suelo no apto, pendiente > 25°,
  dentro del buffer de un núcleo urbano, gasoducto a más de 15 km o biomasa < 20.000 plazas en 10 km.
- **Score de idoneidad ponderado** sobre las celdas aptas, con estos pesos (suman 1):

  | Variable | Peso | | Variable | Peso |
  |---|---|---|---|---|
  | Distancia al gasoducto | 0,25 | | Distancia a núcleos | 0,10 |
  | Biomasa porcina 10 km | 0,25 | | Categoría de vía | 0,07 |
  | Clasificación del suelo | 0,15 | | Distancia a carretera | 0,05 |
  | Pendiente media | 0,10 | | Red Natura 2000 | 0,03 |

Un filtro de umbrales estrictos (biomasa ≥ 200.000 plazas, gasoducto ≤ 10 km, pendiente ≤ 15°, vía de
categoría suficiente) deja **2.890 celdas viables**. Se añade un K-Means (k = 7, por el codo) como
apoyo descriptivo, no como filtro de decisión.

---

## Parte 2 — Proyección del censo y detección de celdas óptimas

Notebook `03_viability/viabilidad_economica.ipynb` (primera etapa). Que un sitio sea apto en el mapa
no significa que los números cierren. Antes de decidir hacen falta tres cosas:

1. **Proyección del censo porcino a 2040.** Serie histórica del MAPA (semestral, provincia 722),
   competición de cinco modelos (regresión lineal, polinómica, SVR, Random Forest, Gradient Boosting)
   optimizados con Optuna y validados con **ventana temporal expansiva** (nada de mezclar pasado y
   futuro → evita *data leakage*). Gana la **regresión lineal**, con MAPE en test ≈ 1,6 %. Se usa como
   **filtro de robustez del suministro**, no para inflar ingresos: la economía se calcula con el purín
   *actual* (modelo conservador).

2. **Economía preliminar celda a celda.** Sobre las 2.890 viables se calcula el purín movilizable en
   10 km (factores cebo 4,5 · cerda 16,0 · lechón 1,5 L/día), el biometano producible, los ingresos,
   OPEX, amortización y el **margen anual** en tres escenarios de precio.

3. **Modelos de apoyo Random Forest.** Dos modelos (clasificador óptima/no y regresor del margen)
   confirman qué variables pesan. La aportación no es el F1 (el objetivo lo definimos nosotros), sino
   la **importancia de variables**: el modelo redescubre que **la biomasa en 10 km y la distancia al
   gasoducto** son las que deciden — las mismas de más peso en el score geoespacial.

### ¿Qué hace "óptima" a una celda?

Filtro estricto: debe cumplir **las tres condiciones a la vez**. Los dos umbrales relativos se
recalculan en cada corrida; el de gasoducto es fijo.

| Condición | Umbral | Qué garantiza |
|---|---|---|
| Stock porcino proyectado a 2040 en su entorno | ≥ mediana de todas las celdas | Suministro robusto a futuro |
| Distancia al gasoducto | ≤ 2.000 m | Conexión a red barata |
| Margen anual (escenario base) | ≥ percentil 75, y positivo | Cuartil superior económico |

Resultado: **209 celdas óptimas** (~7 % de las viables).

---

## Parte 3 — Viabilidad económica: Monte Carlo

Notebook `03_viability/viabilidad_economica.ipynb` (segunda etapa). En vez de un único VAN, se simulan
**25.000 futuros** por localización sobre un modelo de flujos de caja descontados a 15 años. La salida
no es un número, sino una **distribución de VAN** y la **probabilidad de ganar dinero**, P(VAN>0).

### Paso a paso del modelo

1. **De cabezas a biometano.** Para cada celda, granjas en 10 km → purín por tipo → biometano
   (rendimiento central 20 Nm³/t).
2. **Tamaño de planta.** Tres escalas (pequeña, mediana, grande); se prueban las tres con los mismos
   sorteos y se elige la de mejor VAN esperado.
3. **CAPEX no fijo.** A la inversión base se le suman los costes geoespaciales de la celda: pendiente,
   distancia al gasoducto, conexiones y coste ambiental.
4. **Curva de arranque.** La planta produce al 60 % los años 1–5, sube al 100 % en el año 10.
5. **Monte Carlo: 25.000 futuros.** Se sortean 8 variables como triangulares (mín/moda/máx):
   movilización del feedstock, rendimiento, precio del biometano, GdOs, OPEX variable, sobrecoste de
   obra, subvenciones y co-productos.
6. **Estado financiero año a año.** Ingresos, OPEX, EBITDA, amortización, impuestos y capital de
   trabajo, descontados al 8 % (WACC) a 15 años, por cada iteración.
7. **Métricas de riesgo y ranking.** P(VAN>0), VAN esperado, mediana y rango P5–P95. Se ordena por
   **probabilidad de éxito**, no por VAN.

**Resultado:** la mejor localización (celda **13806**, escala **Grande**) tiene **P(VAN>0) = 76,9 %** y
VAN esperado 2,36 M€ (P5–P95: −2,6 a +7,4 M€). De las 209 óptimas, 131 superan el 50 % de
probabilidad; el reparto es 167 Grande / 42 Mediana. El **break-even** del precio del biometano está
en ≈ **0,648 €/Nm³** (precio central asumido 0,70 €/Nm³).

### Por qué (casi) todas las plantas salen Grande

No es un fallo del modelo, es **apalancamiento operativo**. El OPEX fijo (personal ~400k, seguros,
administración, digestato) es casi el mismo produzca la planta 2 o 10 millones de Nm³, pero los
ingresos sí escalan. Ejemplo ilustrativo sobre una óptima (la 13803; la recomendada nº 1 es la 13806),
desglose determinista al 100 % de utilización:

| (M€, a pleno rendimiento) | Pequeña | Mediana | Grande |
|---|---:|---:|---:|
| Capacidad (M Nm³) | 2 | 5 | 10 |
| Ingresos | 1,75 | 4,04 | 7,87 |
| OPEX fijo | 0,88 | 0,96 | 1,11 |
| Margen EBITDA | 20 % | 44 % | **53 %** |
| **VAN** | **−5,08** | **−2,61** | **+0,42** |

A eso se suma el CAPEX específico decreciente (2,0 €/Nm³ la pequeña frente a 1,5 la grande). Invertir
en pequeño es doblemente ineficiente.

---

## La app Streamlit

App narrativa que recorre todo el trabajo, del contexto del censo a la recomendación de inversión.
Lee las salidas de los notebooks (no recalcula); si cambian los datos, la app se actualiza sola.

### Cómo lanzarla

```bash
cd Biomethane-Plant-Design-main
streamlit run streamlit_app/Home.py
```

### Estructura narrativa (8 secciones)

| Sección | La pregunta que responde |
|---|---|
| 0 · Los datos de Huesca | Las seis capas descargadas sobre la delimitación provincial |
| 1 · El punto de partida | ¿Por qué purín, por qué España, por qué Huesca? Censo porcino UE + serie de Huesca |
| 2 · Idoneidad geoespacial | De 63.612 celdas a 2.890 viables: exclusiones, score y mapa |
| 3 · Proyección 2040 | ¿Seguirá habiendo purín? Forecasting del censo con validación temporal |
| 4 · Economía y celdas óptimas | Cuenta de resultados celda a celda + filtro triple |
| 5 · Monte Carlo | 25.000 futuros por sitio: la distribución del VAN |
| 6 · Sensibilidad y break-even | Qué variable manda y a qué precio empieza a ganar |
| 7 · Conclusiones | Ranking final, recomendación y fuentes |

### Datos que consume (en `data/processed/`, generados por los notebooks)

| Archivo | Contiene |
|---|---|
| `scoring_biometano.csv` | Malla de 63.612 celdas con score |
| `viables_interseccion.gpkg` | Las 2.890 celdas viables con geometría |
| `huesca_porcino_serie.csv` · `proyeccion_porcino_15anios.csv` | Serie histórica y proyección del censo |
| `resultados_viabilidad_economica_final.csv` | Economía celda a celda + flag de óptima |
| `viabilidad_final_montecarlo_optimas.csv/.gpkg` | Monte Carlo sobre las óptimas |
| `mapa_optimas_biometano.html` · `mc_*.png` · `dashboard_pipeline_completo.png` | Mapas y gráficos |

---

## Tecnologías

- **GeoPandas, Shapely, PyProj** — procesado vectorial
- **Rasterio, rasterstats** — procesado raster (pendiente / DEM)
- **OSMnx** — descarga de red viaria
- **scikit-learn, statsmodels** — Random Forest, K-Means, análisis VIF
- **Optuna** — optimización de hiperparámetros
- **numpy / numpy-financial** — motor Monte Carlo y flujos de caja (VAN, TIR)
- **pydeck, Folium, Plotly, Streamlit** — visualización y app

---

## Fuentes de los supuestos

Todos los supuestos financieros, técnicos y de coste están justificados con fuentes sectoriales.

**Parámetros financieros**

| Parámetro | Valor | Fuente |
|---|---|---|
| Horizonte de evaluación | 15 años | EBA + plazos de *project finance* bancario |
| WACC (tasa de descuento) | 8 % | Valoración de renovables (PwC / EY) |
| Impuesto de Sociedades + amortización lineal | 25 % · 6,67 %/año | Ley del IS · Agencia Tributaria |
| Mantenimiento (O&M) | 2 % del CAPEX/año | Ratios O&M agroindustriales (Miogas, Biovic) |
| Fondo de maniobra (NOF) | 5 % de ingresos | Estándar de tesorería corporativa (*utilities*) |

**Supuestos técnicos del feedstock porcino**

| Parámetro | Valor | Fuente |
|---|---|---|
| Rendimiento de biometano | 20 Nm³/t purín (central; triangular 15–20–25) | IDAE, fichas de AguaSigma (15–30 Nm³/t) |
| Coste de adquisición del purín | 0 €/t (subproducto) | AEBIG, SEDIGAS (el ganadero se ahorra un pasivo ambiental) |
| Coste de transporte | 0,18 €/t·km | Observatorio de Costes del Transporte (Mitma) |
| Coste de pretratamiento | 2,5 €/t | Ingeniería agroindustrial (Miogas), rango 2–4 €/t |
| Factor de disponibilidad | 85 % | Métrica prudencial (PwC, Biovic) |

**Escalas de planta (economías de escala)**

| Escala | CAPEX | Capacidad | CAPEX específico | Fuente |
|---|---|---|---|---|
| Pequeña | 3 M€ | 2 M Nm³/año | 2,00 €/Nm³ | AEBIG (plantas *on-farm* / cooperativas), EBA |
| Mediana | 6 M€ | 5 M Nm³/año | 1,60 €/Nm³ | Biovic / PwC (estándar ibérico) |
| Grande | 12 M€ | 10 M Nm³/año | 1,50 €/Nm³ | EBA (plantas industriales de inyección en red) |

**Costes de conexión e infraestructura lineal (CAPEX)**

| Concepto | Coste | Fuente |
|---|---|---|
| Conexión a gasoducto | 300.000 €/km | SEDIGAS, CNMC (300–450 k€/km) |
| Conexión eléctrica (MT) | 80.000 €/km | MITECO, distribuidoras (i-DE, Endesa) |
| Conexión de agua | 60.000 €/km | Confederaciones hidrográficas, ACA |
| Acceso por carretera | 80.000 €/km | Bancos de precios de obra pública (IVE, ITeC) |

**Penalizaciones geoespaciales del CAPEX**

| Concepto | Recargo | Fuente |
|---|---|---|
| Pendiente ≤5 % / 5–10 % / >10 % | +1 % / +2,5 % / +5 % del CAPEX | ITeC / IVE, SEDIGAS |
| Restricción ambiental (baja) | +1 % CAPEX · 25.000 €/año OPEX | AEBIG, MITECO, MTD/BAT de la CE |

> **Nota:** las distancias de conexión eléctrica y de agua no estaban cartografiadas; se asumen 2 km
> uniformes para todos (al ser iguales, no distorsionan el ranking). El acarreo del purín se aproxima
> como medio radio de captación (5 km).

---

*Equipo: Rafael · Bruno · Fernando Gonella.*
