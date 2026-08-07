"""
app.py
------
Punto de entrada de Humanox AI Sport Analytics.

Este archivo SOLO se encarga de la interfaz (Streamlit): arma la
página, aplica filtros del usuario y llama a las funciones de
analytics.py, modules/alerts.py y modules/charts.py para obtener datos
y figuras ya calculados. No contiene lógica de negocio ni SQL directo,
para mantener el código modular y fácil de mantener.

Ejecutar con:
    streamlit run app.py
"""

from datetime import date, timedelta

import pandas as pd
import streamlit as st

import analytics
import database as db
import simulator
from modules import alerts as alerts_engine
from modules import charts
from modules import styles

# ---------------------------------------------------------------------------
# Configuración de página (debe ser la primera llamada de Streamlit)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Humanox AI Sport Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inicializa la base de datos (crea tablas y siembra datos la 1ª vez)
db.init_database()

styles.render_header(st)


# ---------------------------------------------------------------------------
# Sidebar: branding, filtros y simulador
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### ⚙️ Panel de control")

    jugadores_df = db.get_players()
    opciones_jugador = ["Todos los jugadores"] + jugadores_df["nombre"].tolist()
    jugador_seleccionado = st.selectbox("Filtrar por jugador", opciones_jugador)

    st.markdown("---")
    st.markdown("**Rango de fechas**")
    rango_fechas = st.date_input(
        "Selecciona un rango",
        value=(date.today() - timedelta(days=60), date.today()),
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### 🧪 Simulador de sensores")
    st.caption(
        "Genera nuevas lecturas biométricas ficticias, como si llegaran "
        "en vivo desde las espinilleras inteligentes."
    )

    if st.button("➕ Simular entrenamiento (jugador filtrado)", width='stretch'):
        if jugador_seleccionado == "Todos los jugadores":
            st.warning("Selecciona un jugador específico para simular su entrenamiento.")
        else:
            jugador_id = int(
                jugadores_df.loc[jugadores_df["nombre"] == jugador_seleccionado, "id"].iloc[0]
            )
            nuevo = simulator.simular_nuevo_entrenamiento(jugador_id)
            st.success(f"Nuevo entrenamiento generado para {jugador_seleccionado} "
                       f"el {nuevo['fecha']}.")
            st.rerun()

    if st.button("🔁 Simular jornada completa del equipo", width='stretch'):
        total = simulator.simular_jornada_completa()
        st.success(f"Se generaron {total} nuevos entrenamientos (uno por jugador).")
        st.rerun()

    st.markdown("---")
    st.caption("Humanox AI · Demo MVP · Datos 100% ficticios")


# ---------------------------------------------------------------------------
# Carga de datos según filtros seleccionados
# ---------------------------------------------------------------------------

jugador_id_filtro = None
if jugador_seleccionado != "Todos los jugadores":
    jugador_id_filtro = int(
        jugadores_df.loc[jugadores_df["nombre"] == jugador_seleccionado, "id"].iloc[0]
    )

fecha_inicio = fecha_fin = None
if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
    fecha_inicio, fecha_fin = rango_fechas[0].isoformat(), rango_fechas[1].isoformat()

df = db.get_trainings(
    jugador_id=jugador_id_filtro, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin
)

if df.empty:
    st.info(
        "No hay entrenamientos para el filtro seleccionado. Prueba a ampliar el "
        "rango de fechas o simula un nuevo entrenamiento desde la barra lateral."
    )
    st.stop()


# ---------------------------------------------------------------------------
# KPIs superiores
# ---------------------------------------------------------------------------

kpis = analytics.kpis_generales(df)

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Jugadores activos", kpis["jugadores_activos"])
k2.metric("FC promedio", f"{kpis['fc_promedio']} bpm")
k3.metric("Distancia promedio", f"{kpis['distancia_promedio']} km")
k4.metric("Fatiga promedio", f"{kpis['fatiga_promedio']} /10")
k5.metric("Sueño promedio", f"{kpis['sueno_promedio']} /10")
k6.metric("Velocidad promedio", f"{kpis['velocidad_promedio']} km/h")

st.markdown("")


# ---------------------------------------------------------------------------
# Tabs principales
# ---------------------------------------------------------------------------

tab_dashboard, tab_jugador, tab_alertas, tab_ejecutivo = st.tabs(
    ["📊 Dashboard General", "🧍 Jugador Individual", "🚨 Alertas Inteligentes",
     "🏆 Panel Ejecutivo"]
)

# --- Tab 1: Dashboard general -----------------------------------------------
with tab_dashboard:
    col1, col2 = st.columns(2)
    with col1:
        serie_fatiga = analytics.historico_metrica(df, "fatiga")
        st.plotly_chart(
            charts.linea_historica(serie_fatiga, "fecha", "fatiga",
                                    "Evolución de la fatiga del equipo"),
            width='stretch',
        )
    with col2:
        serie_fc = analytics.historico_metrica(df, "frecuencia_cardiaca")
        st.plotly_chart(
            charts.linea_historica(serie_fc, "fecha", "frecuencia_cardiaca",
                                    "Evolución de frecuencia cardíaca"),
            width='stretch',
        )

    col3, col4 = st.columns(2)
    with col3:
        distribucion_posicion = jugadores_df["posicion"].value_counts().reset_index()
        distribucion_posicion.columns = ["posicion", "cantidad"]
        st.plotly_chart(
            charts.pie_distribucion(distribucion_posicion, "posicion", "cantidad",
                                     "Distribución de jugadores por posición"),
            width='stretch',
        )
    with col4:
        serie_sueno = analytics.historico_metrica(df, "calidad_sueno")
        st.plotly_chart(
            charts.linea_historica(serie_sueno, "fecha", "calidad_sueno",
                                    "Evolución de calidad de sueño"),
            width='stretch',
        )

    st.markdown("#### Historial de entrenamientos filtrados")
    columnas_tabla = [
        "fecha", "nombre", "posicion", "frecuencia_cardiaca", "distancia_recorrida",
        "velocidad_maxima", "aceleraciones", "fatiga", "calidad_sueno", "fuerza_disparo",
    ]
    st.dataframe(
        df[columnas_tabla].sort_values("fecha", ascending=False),
        width='stretch', hide_index=True,
    )

# --- Tab 2: Jugador individual ----------------------------------------------
with tab_jugador:
    if jugador_seleccionado == "Todos los jugadores":
        st.info("Selecciona un jugador específico en la barra lateral para ver su perfil detallado.")
    else:
        jugador_row = jugadores_df.loc[jugadores_df["nombre"] == jugador_seleccionado].iloc[0]
        st.markdown(f"### {jugador_row['nombre']} · {jugador_row['posicion']} · {jugador_row['edad']} años")

        ultimo = df.sort_values("fecha").iloc[-1]
        promedio_equipo = analytics.kpis_generales(db.get_trainings())

        colr1, colr2 = st.columns([1, 1])
        with colr1:
            valores_jugador = {
                "FC": ultimo["frecuencia_cardiaca"],
                "Velocidad": ultimo["velocidad_maxima"],
                "Fatiga": ultimo["fatiga"],
                "Sueño": ultimo["calidad_sueno"],
                "Fuerza": ultimo["fuerza_disparo"] / 10,  # normalizado a escala 0-10
            }
            valores_equipo = {
                "FC": promedio_equipo["fc_promedio"],
                "Velocidad": promedio_equipo["velocidad_promedio"],
                "Fatiga": promedio_equipo["fatiga_promedio"],
                "Sueño": promedio_equipo["sueno_promedio"],
                "Fuerza": 6.5,
            }
            st.plotly_chart(
                charts.radar_jugador(valores_jugador, valores_equipo),
                width='stretch',
            )
        with colr2:
            st.plotly_chart(
                charts.indicador_gauge(
                    ultimo["fatiga"], "Nivel de fatiga actual", 10, umbral_alerta=7
                ),
                width='stretch',
            )
            st.plotly_chart(
                charts.indicador_gauge(
                    ultimo["frecuencia_cardiaca"], "FC último entrenamiento (bpm)", 220,
                    umbral_alerta=165,
                ),
                width='stretch',
            )

        st.markdown("#### Evolución histórica")
        metrica_elegida = st.selectbox(
            "Métrica a graficar",
            ["frecuencia_cardiaca", "distancia_recorrida", "velocidad_maxima",
             "aceleraciones", "fatiga", "calidad_sueno", "fuerza_disparo"],
        )
        serie = df.sort_values("fecha")[["fecha", metrica_elegida]]
        st.plotly_chart(
            charts.linea_historica(serie, "fecha", metrica_elegida,
                                    f"Historial de {metrica_elegida.replace('_', ' ')}"),
            width='stretch',
        )

        st.markdown("#### Alertas activas para este jugador")
        alertas_jugador = alerts_engine.evaluar_jugador(df.sort_values("fecha"))
        if not alertas_jugador:
            st.markdown(styles.badge_html("ok") + "  Sin alertas activas.", unsafe_allow_html=True)
        else:
            for a in alertas_jugador:
                st.markdown(
                    f"{styles.badge_html(a['nivel'])}  {a['mensaje']}",
                    unsafe_allow_html=True,
                )

# --- Tab 3: Alertas inteligentes --------------------------------------------
with tab_alertas:
    st.markdown("#### Motor de alertas basado en reglas (sin IA externa, sin costo)")
    st.caption(
        "Las alertas se generan automáticamente combinando frecuencia cardíaca, "
        "fatiga, calidad de sueño y tendencia de distancia recorrida."
    )

    reporte = alerts_engine.generar_reporte_alertas(df)
    if reporte.empty:
        st.markdown(styles.badge_html("ok") + "  El equipo no presenta alertas activas.",
                     unsafe_allow_html=True)
    else:
        for nivel, etiqueta in [("alto", "🔴 Riesgo alto"), ("medio", "🟠 Precaución")]:
            subset = reporte[reporte["nivel"] == nivel]
            if subset.empty:
                continue
            st.markdown(f"##### {etiqueta} ({len(subset)})")
            for _, fila in subset.iterrows():
                st.markdown(
                    f"{styles.badge_html(fila['nivel'])}  **{fila['nombre']}** — {fila['mensaje']}",
                    unsafe_allow_html=True,
                )
            st.markdown("")

        st.markdown("#### Detalle tabular")
        st.dataframe(reporte, width='stretch', hide_index=True)

# --- Tab 4: Panel ejecutivo --------------------------------------------------
with tab_ejecutivo:
    df_completo = db.get_trainings()  # panel ejecutivo usa TODO el histórico

    estado = analytics.estado_fisico_general(df_completo)
    color_estado = {"Óptimo": "🟢", "Con precaución": "🟡", "Crítico": "🔴"}.get(estado, "⚪")
    st.markdown(f"### Estado físico general del equipo: {color_estado} **{estado}**")

    colA, colB = st.columns(2)
    with colA:
        st.markdown("##### 🚑 Jugadores con mayor riesgo")
        st.dataframe(
            analytics.jugadores_mayor_riesgo(df_completo),
            width='stretch', hide_index=True,
        )
    with colB:
        st.markdown("##### 🧱 Jugadores más constantes")
        st.dataframe(
            analytics.jugadores_mas_constantes(df_completo),
            width='stretch', hide_index=True,
        )

    colC, colD = st.columns(2)
    with colC:
        st.plotly_chart(
            charts.barras_ranking(
                analytics.top_velocidad(df_completo), "velocidad_maxima", "nombre",
                "🏃 Top velocidad máxima",
            ),
            width='stretch',
        )
    with colD:
        st.plotly_chart(
            charts.barras_ranking(
                analytics.top_fuerza(df_completo), "fuerza_maxima", "nombre",
                "💥 Top fuerza de disparo", color=charts.COLOR_INFO,
            ),
            width='stretch',
        )

    st.plotly_chart(
        charts.barras_ranking(
            analytics.ranking_fatiga(df_completo), "fatiga_promedio", "nombre",
            "😮‍💨 Ranking de fatiga promedio", color=charts.COLOR_MEDIO,
        ),
        width='stretch',
    )
