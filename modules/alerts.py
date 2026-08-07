"""
modules/alerts.py
------------------
Motor de alertas inteligentes basado en reglas de negocio.

Deliberadamente NO usa ningún modelo de lenguaje ni API externa: las
alertas se generan con umbrales y heurísticas deportivas simples, lo
que mantiene el proyecto 100% gratuito y funcionando sin conexión a
internet. Esto es lo que en la industria se llama un "rule engine".

Cada regla devuelve, cuando se cumple, un diccionario con:
    - nivel:   "alto" | "medio" | "info"
    - mensaje: texto explicativo listo para mostrar en la UI
    - metrica: la métrica que disparó la alerta (para trazabilidad)

Umbrales configurables al inicio del archivo para facilitar el ajuste
fino sin tocar la lógica.
"""

import pandas as pd

# ---------------------------------------------------------------------------
# Umbrales de negocio (ajustables)
# ---------------------------------------------------------------------------

FC_ALTA = 165           # pulsaciones por minuto consideradas elevadas
FATIGA_ALTA = 7         # escala 1-10
SUENO_BAJO = 4          # escala 1-10
CAIDA_DISTANCIA_PCT = 0.15   # 15% de caída sostenida
VENTANA_TENDENCIA = 3        # nº de entrenamientos consecutivos a analizar


def evaluar_riesgo_lesion(fc: float, fatiga: float) -> dict | None:
    """Regla 1: FC elevada + fatiga alta -> riesgo de lesión muscular."""
    if fc >= FC_ALTA and fatiga >= FATIGA_ALTA:
        return {
            "nivel": "alto",
            "mensaje": "Riesgo alto de lesión muscular: frecuencia cardíaca "
                       "elevada combinada con niveles de fatiga altos.",
            "metrica": "frecuencia_cardiaca + fatiga",
        }
    return None


def evaluar_calidad_sueno(calidad_sueno: float) -> dict | None:
    """Regla 2: sueño insuficiente -> recomendar reducir carga."""
    if calidad_sueno <= SUENO_BAJO:
        return {
            "nivel": "medio",
            "mensaje": "Calidad de sueño baja: se recomienda reducir la carga "
                       "de entrenamiento y priorizar la recuperación.",
            "metrica": "calidad_sueno",
        }
    return None


def evaluar_tendencia_distancia(distancias: pd.Series) -> dict | None:
    """Regla 3: caída sostenida de distancia recorrida -> pérdida de rendimiento.

    Compara el promedio de los últimos `VENTANA_TENDENCIA` entrenamientos
    contra el promedio histórico previo. Si la caída supera el umbral,
    se dispara la alerta.
    """
    if len(distancias) < VENTANA_TENDENCIA + 2:
        return None

    recientes = distancias.tail(VENTANA_TENDENCIA).mean()
    previos = distancias.iloc[: -VENTANA_TENDENCIA].mean()

    if previos > 0 and recientes < previos * (1 - CAIDA_DISTANCIA_PCT):
        return {
            "nivel": "medio",
            "mensaje": "Posible pérdida de rendimiento: la distancia recorrida "
                       "muestra una caída sostenida en los últimos "
                       f"{VENTANA_TENDENCIA} entrenamientos.",
            "metrica": "distancia_recorrida",
        }
    return None


def evaluar_jugador(df_jugador: pd.DataFrame) -> list[dict]:
    """Aplica todas las reglas sobre el historial de un único jugador.

    Args:
        df_jugador: DataFrame con los entrenamientos de un jugador,
            ordenado cronológicamente ascendente.

    Returns:
        Lista de alertas activas (puede estar vacía) basadas en el
        registro más reciente y en la tendencia histórica.
    """
    if df_jugador.empty:
        return []

    ultimo = df_jugador.iloc[-1]
    alertas = []

    for regla in (
        evaluar_riesgo_lesion(ultimo["frecuencia_cardiaca"], ultimo["fatiga"]),
        evaluar_calidad_sueno(ultimo["calidad_sueno"]),
        evaluar_tendencia_distancia(df_jugador["distancia_recorrida"]),
    ):
        if regla is not None:
            alertas.append(regla)

    return alertas


def generar_reporte_alertas(df_entrenamientos: pd.DataFrame) -> pd.DataFrame:
    """Genera un reporte tabular de alertas para todo el equipo.

    Args:
        df_entrenamientos: DataFrame con TODOS los entrenamientos,
            incluyendo columnas jugador_id y nombre.

    Returns:
        DataFrame con columnas: jugador_id, nombre, nivel, mensaje, metrica.
        Una fila por cada alerta activa (un jugador puede tener varias).
    """
    filas = []

    if df_entrenamientos.empty:
        return pd.DataFrame(columns=["jugador_id", "nombre", "nivel", "mensaje", "metrica"])

    for jugador_id, grupo in df_entrenamientos.groupby("jugador_id"):
        grupo_ordenado = grupo.sort_values("fecha")
        nombre = grupo_ordenado.iloc[-1]["nombre"]

        for alerta in evaluar_jugador(grupo_ordenado):
            filas.append({
                "jugador_id": jugador_id,
                "nombre": nombre,
                **alerta,
            })

    reporte = pd.DataFrame(filas)
    if not reporte.empty:
        orden_nivel = {"alto": 0, "medio": 1, "info": 2}
        reporte["orden"] = reporte["nivel"].map(orden_nivel)
        reporte = reporte.sort_values("orden").drop(columns="orden").reset_index(drop=True)

    return reporte
