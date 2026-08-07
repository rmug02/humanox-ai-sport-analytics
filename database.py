"""
database.py
------------
Capa de acceso a datos de Humanox AI Sport Analytics.

Responsabilidades de este módulo:
    - Crear y mantener el esquema de la base de datos SQLite.
    - Poblar la base de datos con jugadores y entrenamientos de ejemplo
      (datos ficticios) la primera vez que se ejecuta la aplicación.
    - Exponer funciones de lectura/escritura para el resto de módulos
      (analytics.py, simulator.py, app.py) sin que estos tengan que
      conocer detalles de SQL.

No contiene lógica de negocio ni de presentación: solo persistencia.
"""

import sqlite3
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Configuración general
# ---------------------------------------------------------------------------

DB_PATH = Path(__file__).parent / "data" / "jugadores.db"

POSICIONES = [
    "Portero",
    "Defensa Central",
    "Lateral Derecho",
    "Lateral Izquierdo",
    "Mediocampista Defensivo",
    "Mediocampista Ofensivo",
    "Extremo Derecho",
    "Extremo Izquierdo",
    "Delantero Centro",
]

NOMBRES = [
    "Mateo Rodríguez", "Santiago Gómez", "Emiliano Torres", "Thiago Fernández",
    "Benjamín Herrera", "Lucas Martínez", "Joaquín Ramírez", "Nicolás Castro",
    "Sebastián Morales", "Agustín Vargas", "Federico Ríos", "Tomás Navarro",
    "Diego Salazar", "Martín Ortega", "Gabriel Cabrera", "Julián Reyes",
    "Cristian Peña", "Andrés Guzmán", "Ricardo Aguilar", "Fabián Molina",
]


def get_connection() -> sqlite3.Connection:
    """Devuelve una conexión a la base de datos SQLite.

    Se usa `check_same_thread=False` porque Streamlit puede invocar
    callbacks desde hilos distintos al de renderizado.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_database(force_reset: bool = False) -> None:
    """Crea las tablas si no existen y siembra datos ficticios iniciales.

    Args:
        force_reset: si es True, elimina las tablas existentes y las
            vuelve a crear desde cero (útil en desarrollo/demo).
    """
    conn = get_connection()
    cur = conn.cursor()

    if force_reset:
        cur.execute("DROP TABLE IF EXISTS entrenamientos;")
        cur.execute("DROP TABLE IF EXISTS jugadores;")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS jugadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            posicion TEXT NOT NULL,
            edad INTEGER NOT NULL
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS entrenamientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            jugador_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            frecuencia_cardiaca INTEGER NOT NULL,
            distancia_recorrida REAL NOT NULL,
            velocidad_maxima REAL NOT NULL,
            aceleraciones INTEGER NOT NULL,
            fatiga INTEGER NOT NULL,
            calidad_sueno INTEGER NOT NULL,
            fuerza_disparo REAL NOT NULL,
            FOREIGN KEY (jugador_id) REFERENCES jugadores (id)
        );
        """
    )
    conn.commit()

    # Solo sembramos datos si la tabla de jugadores está vacía, para no
    # duplicar información en ejecuciones sucesivas de la app.
    cur.execute("SELECT COUNT(*) FROM jugadores;")
    total_jugadores = cur.fetchone()[0]
    if total_jugadores == 0:
        _seed_data(conn)

    conn.close()


def _seed_data(conn: sqlite3.Connection) -> None:
    """Genera jugadores y su historial de entrenamientos ficticios.

    Cada jugador recibe un "perfil base" aleatorio (rango de forma
    física) y luego se generan entre 8 y 15 entrenamientos con
    variaciones realistas alrededor de ese perfil, distribuidos en los
    últimos 60 días.
    """
    cur = conn.cursor()
    random.seed(42)  # reproducibilidad de la demo

    for nombre in NOMBRES:
        posicion = random.choice(POSICIONES)
        edad = random.randint(18, 34)
        cur.execute(
            "INSERT INTO jugadores (nombre, posicion, edad) VALUES (?, ?, ?);",
            (nombre, posicion, edad),
        )
        jugador_id = cur.lastrowid

        # Perfil base individual: define el "nivel" del jugador para que
        # los datos generados sean coherentes entre sí (no puramente random).
        base_fc = random.randint(60, 75)
        base_velocidad = round(random.uniform(26, 33), 1)
        base_fuerza = round(random.uniform(55, 90), 1)
        base_sueno = random.randint(5, 9)

        n_entrenamientos = random.randint(8, 15)
        hoy = date.today()

        for i in range(n_entrenamientos):
            dias_atras = (n_entrenamientos - i) * random.randint(2, 5)
            fecha = hoy - timedelta(days=dias_atras)

            fatiga = max(1, min(10, round(random.gauss(5, 2))))
            calidad_sueno = max(1, min(10, base_sueno + random.randint(-2, 2)))
            frecuencia_cardiaca = max(
                55, min(200, int(base_fc + fatiga * 3 + random.randint(-8, 12)))
            )
            distancia = round(max(3.0, random.gauss(9.5, 1.8)), 2)
            velocidad_maxima = round(
                max(18.0, base_velocidad + random.uniform(-2, 2)), 1
            )
            aceleraciones = max(0, int(random.gauss(20, 6)))
            fuerza_disparo = round(
                max(20.0, base_fuerza + random.uniform(-8, 8)), 1
            )

            cur.execute(
                """
                INSERT INTO entrenamientos (
                    jugador_id, fecha, frecuencia_cardiaca, distancia_recorrida,
                    velocidad_maxima, aceleraciones, fatiga, calidad_sueno,
                    fuerza_disparo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    jugador_id, fecha.isoformat(), frecuencia_cardiaca, distancia,
                    velocidad_maxima, aceleraciones, fatiga, calidad_sueno,
                    fuerza_disparo,
                ),
            )

    conn.commit()


# ---------------------------------------------------------------------------
# Consultas de lectura (usadas por analytics.py y app.py)
# ---------------------------------------------------------------------------

def get_players() -> pd.DataFrame:
    """Devuelve todos los jugadores registrados."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM jugadores ORDER BY nombre;", conn)
    conn.close()
    return df


def get_trainings(jugador_id: int | None = None,
                   fecha_inicio: str | None = None,
                   fecha_fin: str | None = None) -> pd.DataFrame:
    """Devuelve entrenamientos, opcionalmente filtrados.

    Args:
        jugador_id: si se especifica, filtra por un único jugador.
        fecha_inicio / fecha_fin: strings 'YYYY-MM-DD' para filtrar rango.
    """
    conn = get_connection()

    query = """
        SELECT e.*, j.nombre, j.posicion, j.edad
        FROM entrenamientos e
        JOIN jugadores j ON j.id = e.jugador_id
        WHERE 1 = 1
    """
    params: list = []

    if jugador_id is not None:
        query += " AND e.jugador_id = ?"
        params.append(jugador_id)

    if fecha_inicio is not None:
        query += " AND e.fecha >= ?"
        params.append(fecha_inicio)

    if fecha_fin is not None:
        query += " AND e.fecha <= ?"
        params.append(fecha_fin)

    query += " ORDER BY e.fecha ASC;"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()

    if not df.empty:
        df["fecha"] = pd.to_datetime(df["fecha"])

    return df


def insert_training(jugador_id: int, fecha: str, frecuencia_cardiaca: int,
                     distancia_recorrida: float, velocidad_maxima: float,
                     aceleraciones: int, fatiga: int, calidad_sueno: int,
                     fuerza_disparo: float) -> None:
    """Inserta un nuevo registro de entrenamiento para un jugador."""
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO entrenamientos (
            jugador_id, fecha, frecuencia_cardiaca, distancia_recorrida,
            velocidad_maxima, aceleraciones, fatiga, calidad_sueno,
            fuerza_disparo
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            jugador_id, fecha, frecuencia_cardiaca, distancia_recorrida,
            velocidad_maxima, aceleraciones, fatiga, calidad_sueno,
            fuerza_disparo,
        ),
    )
    conn.commit()
    conn.close()
