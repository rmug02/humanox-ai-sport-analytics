"""
analytics.py
------------
Capa de analítica de negocio: transforma los datos crudos de
entrenamientos en KPIs, rankings y agregaciones listas para mostrar en
el dashboard ejecutivo.

Este módulo no accede directamente a SQLite ni dibuja nada en pantalla:
recibe DataFrames (típicamente provenientes de database.py) y devuelve
DataFrames o valores simples. Esto lo hace fácil de testear de forma
aislada y reutilizable fuera de Streamlit si algún día se expone como
API.
"""

import pandas as pd

from modules import alerts as alerts_engine


def kpis_generales(df: pd.DataFrame) -> dict:
    """Calcula los KPIs superiores del dashboard a partir de todos los
    entrenamientos filtrados actualmente en pantalla.
    """
    if df.empty:
        return {
            "jugadores_activos": 0,
            "fc_promedio": 0,
            "distancia_promedio": 0,
            "fatiga_promedio": 0,
            "sueno_promedio": 0,
            "velocidad_promedio": 0,
        }

    return {
        "jugadores_activos": df["jugador_id"].nunique(),
        "fc_promedio": round(df["frecuencia_cardiaca"].mean(), 1),
        "distancia_promedio": round(df["distancia_recorrida"].mean(), 2),
        "fatiga_promedio": round(df["fatiga"].mean(), 1),
        "sueno_promedio": round(df["calidad_sueno"].mean(), 1),
        "velocidad_promedio": round(df["velocidad_maxima"].mean(), 1),
    }


def resumen_por_jugador(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega los entrenamientos por jugador (promedios y conteos).

    Es la tabla base sobre la que se construyen la mayoría de los
    rankings del dashboard ejecutivo.
    """
    if df.empty:
        return pd.DataFrame()

    resumen = (
        df.groupby(["jugador_id", "nombre", "posicion"])
        .agg(
            entrenamientos=("id", "count"),
            fc_promedio=("frecuencia_cardiaca", "mean"),
            distancia_promedio=("distancia_recorrida", "mean"),
            velocidad_maxima=("velocidad_maxima", "max"),
            fatiga_promedio=("fatiga", "mean"),
            sueno_promedio=("calidad_sueno", "mean"),
            fuerza_maxima=("fuerza_disparo", "max"),
            fuerza_promedio=("fuerza_disparo", "mean"),
        )
        .reset_index()
    )

    for col in ["fc_promedio", "distancia_promedio", "fatiga_promedio",
                "sueno_promedio", "fuerza_promedio"]:
        resumen[col] = resumen[col].round(1)

    return resumen


def top_velocidad(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Top N jugadores por velocidad máxima registrada."""
    resumen = resumen_por_jugador(df)
    if resumen.empty:
        return resumen
    return resumen.sort_values("velocidad_maxima", ascending=False).head(n)


def top_fuerza(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Top N jugadores por fuerza de disparo máxima registrada."""
    resumen = resumen_por_jugador(df)
    if resumen.empty:
        return resumen
    return resumen.sort_values("fuerza_maxima", ascending=False).head(n)


def ranking_fatiga(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Top N jugadores con mayor fatiga promedio (los más exigidos/en riesgo)."""
    resumen = resumen_por_jugador(df)
    if resumen.empty:
        return resumen
    return resumen.sort_values("fatiga_promedio", ascending=False).head(n)


def jugadores_mas_constantes(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Jugadores con menor variabilidad (desviación estándar) en distancia
    recorrida entre entrenamientos: son los más consistentes en rendimiento.
    """
    if df.empty:
        return pd.DataFrame()

    variabilidad = (
        df.groupby(["jugador_id", "nombre", "posicion"])["distancia_recorrida"]
        .std()
        .fillna(0)
        .reset_index(name="variabilidad_distancia")
    )
    variabilidad["variabilidad_distancia"] = variabilidad["variabilidad_distancia"].round(2)
    return variabilidad.sort_values("variabilidad_distancia").head(n)


def jugadores_mayor_riesgo(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Jugadores con más alertas activas (mayor riesgo actual), usando el
    motor de reglas de modules/alerts.py.
    """
    reporte = alerts_engine.generar_reporte_alertas(df)
    if reporte.empty:
        return pd.DataFrame(columns=["jugador_id", "nombre", "num_alertas"])

    conteo = (
        reporte.groupby(["jugador_id", "nombre"])
        .size()
        .reset_index(name="num_alertas")
        .sort_values("num_alertas", ascending=False)
    )
    return conteo.head(n)


def estado_fisico_general(df: pd.DataFrame) -> str:
    """Devuelve una etiqueta cualitativa del estado físico general del
    equipo, combinando fatiga promedio y calidad de sueño promedio.
    """
    if df.empty:
        return "Sin datos"

    fatiga = df["fatiga"].mean()
    sueno = df["calidad_sueno"].mean()

    if fatiga >= 7 or sueno <= 4:
        return "Crítico"
    if fatiga >= 5.5 or sueno <= 6:
        return "Con precaución"
    return "Óptimo"


def historico_metrica(df: pd.DataFrame, metrica: str) -> pd.DataFrame:
    """Serie temporal (promedio diario del equipo) de una métrica dada,
    lista para graficar con Plotly.
    """
    if df.empty or metrica not in df.columns:
        return pd.DataFrame(columns=["fecha", metrica])

    serie = (
        df.groupby("fecha")[metrica]
        .mean()
        .reset_index()
        .sort_values("fecha")
    )
    return serie
