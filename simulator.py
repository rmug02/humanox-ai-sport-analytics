"""
simulator.py
------------
Simula la llegada de datos biométricos desde sensores inteligentes
(espinilleras inteligentes, pulseras, chalecos GPS, etc.).

En un producto real, este módulo sería reemplazado por un listener que
recibe eventos de hardware (MQTT, WebSocket, API REST del fabricante).
Para esta demo, generamos valores aleatorios pero realistas, basados en
el historial reciente del jugador, para que la nueva medición sea
coherente con su rendimiento habitual en lugar de completamente
arbitraria.
"""

import random
from datetime import date

import pandas as pd

import database as db


def _valor_o_default(serie: pd.Series, default: float) -> float:
    """Devuelve la media de una serie, o un valor por defecto si está vacía."""
    return float(serie.mean()) if not serie.empty else default


def generar_entrenamiento_aleatorio(jugador_id: int) -> dict:
    """Genera un diccionario con un nuevo entrenamiento simulado.

    Se apoya en el historial del jugador (si existe) para variar los
    valores de forma realista alrededor de su promedio, simulando el
    ruido natural de un sensor biométrico.
    """
    historial = db.get_trainings(jugador_id=jugador_id)

    fc_base = _valor_o_default(historial.get("frecuencia_cardiaca", pd.Series()), 70)
    dist_base = _valor_o_default(historial.get("distancia_recorrida", pd.Series()), 9.0)
    vel_base = _valor_o_default(historial.get("velocidad_maxima", pd.Series()), 28.0)
    acc_base = _valor_o_default(historial.get("aceleraciones", pd.Series()), 20)
    fuerza_base = _valor_o_default(historial.get("fuerza_disparo", pd.Series()), 65.0)
    sueno_base = _valor_o_default(historial.get("calidad_sueno", pd.Series()), 7)

    fatiga = max(1, min(10, round(random.gauss(5, 2))))
    calidad_sueno = max(1, min(10, round(sueno_base + random.uniform(-2, 2))))
    frecuencia_cardiaca = max(
        55, min(210, int(fc_base + fatiga * 3 + random.randint(-8, 12)))
    )
    distancia_recorrida = round(max(2.0, random.gauss(dist_base, 1.5)), 2)
    velocidad_maxima = round(max(15.0, vel_base + random.uniform(-2.5, 2.5)), 1)
    aceleraciones = max(0, int(random.gauss(acc_base, 5)))
    fuerza_disparo = round(max(15.0, fuerza_base + random.uniform(-6, 6)), 1)

    return {
        "jugador_id": jugador_id,
        "fecha": date.today().isoformat(),
        "frecuencia_cardiaca": frecuencia_cardiaca,
        "distancia_recorrida": distancia_recorrida,
        "velocidad_maxima": velocidad_maxima,
        "aceleraciones": aceleraciones,
        "fatiga": fatiga,
        "calidad_sueno": calidad_sueno,
        "fuerza_disparo": fuerza_disparo,
    }


def simular_nuevo_entrenamiento(jugador_id: int) -> dict:
    """Genera un entrenamiento simulado y lo persiste en la base de datos.

    Devuelve el registro insertado para que la UI pueda mostrar feedback
    inmediato al usuario (por ejemplo, un toast de confirmación).
    """
    entrenamiento = generar_entrenamiento_aleatorio(jugador_id)
    db.insert_training(**entrenamiento)
    return entrenamiento


def simular_jornada_completa() -> int:
    """Genera un nuevo entrenamiento para TODOS los jugadores del equipo.

    Útil para simular una jornada de entrenamiento completa con un solo
    clic desde el dashboard. Devuelve el número de registros insertados.
    """
    jugadores = db.get_players()
    for jugador_id in jugadores["id"]:
        simular_nuevo_entrenamiento(int(jugador_id))
    return len(jugadores)
