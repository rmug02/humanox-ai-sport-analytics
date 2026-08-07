"""
modules/charts.py
------------------
Constructores de gráficas Plotly reutilizables para el dashboard.

Centralizar aquí la creación de figuras evita duplicar configuración de
estilo (colores, tema, márgenes) en app.py y mantiene la paleta de la
marca Humanox consistente en todas las visualizaciones.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Paleta de marca Humanox
COLOR_PRIMARIO = "#00E5A0"
COLOR_SECUNDARIO = "#1F2937"
COLOR_ALERTA = "#FF4D4D"
COLOR_MEDIO = "#FFB020"
COLOR_INFO = "#3B82F6"
PLANTILLA = "plotly_dark"


def linea_historica(df: pd.DataFrame, x: str, y: str, titulo: str) -> go.Figure:
    """Gráfica de línea para series temporales (ej. evolución de fatiga)."""
    fig = px.line(
        df, x=x, y=y, markers=True, template=PLANTILLA,
        color_discrete_sequence=[COLOR_PRIMARIO], title=titulo,
    )
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=320)
    return fig


def barras_ranking(df: pd.DataFrame, x: str, y: str, titulo: str,
                    color: str = COLOR_PRIMARIO) -> go.Figure:
    """Gráfica de barras horizontales para rankings (top N jugadores)."""
    fig = px.bar(
        df, x=x, y=y, orientation="h", template=PLANTILLA,
        color_discrete_sequence=[color], title=titulo, text=x,
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10), height=320,
        yaxis=dict(autorange="reversed"),
    )
    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    return fig


def radar_jugador(valores_jugador: dict, valores_promedio_equipo: dict,
                   titulo: str = "Perfil físico vs. promedio del equipo") -> go.Figure:
    """Radar comparando el perfil de un jugador contra el promedio del equipo.

    Ambos diccionarios deben compartir las mismas claves (métricas).
    """
    categorias = list(valores_jugador.keys())

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=list(valores_jugador.values()), theta=categorias, fill="toself",
        name="Jugador", line_color=COLOR_PRIMARIO,
    ))
    fig.add_trace(go.Scatterpolar(
        r=list(valores_promedio_equipo.values()), theta=categorias, fill="toself",
        name="Promedio equipo", line_color=COLOR_INFO, opacity=0.6,
    ))
    fig.update_layout(
        template=PLANTILLA, title=titulo,
        polar=dict(radialaxis=dict(visible=True)),
        margin=dict(l=20, r=20, t=40, b=20), height=380,
        showlegend=True,
    )
    return fig


def indicador_gauge(valor: float, titulo: str, rango_max: float,
                     umbral_alerta: float | None = None) -> go.Figure:
    """Indicador tipo velocímetro (gauge) para una métrica puntual."""
    color_barra = COLOR_PRIMARIO
    if umbral_alerta is not None and valor >= umbral_alerta:
        color_barra = COLOR_ALERTA

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valor,
        title={"text": titulo},
        gauge={
            "axis": {"range": [0, rango_max]},
            "bar": {"color": color_barra},
            "bgcolor": COLOR_SECUNDARIO,
        },
    ))
    fig.update_layout(template=PLANTILLA, margin=dict(l=20, r=20, t=40, b=10), height=250)
    return fig


def pie_distribucion(df: pd.DataFrame, nombres: str, valores: str,
                      titulo: str) -> go.Figure:
    """Gráfica de pastel, típicamente usada para distribución por posición
    o por nivel de alerta.
    """
    fig = px.pie(
        df, names=nombres, values=valores, template=PLANTILLA, title=titulo,
        color_discrete_sequence=px.colors.sequential.Teal,
        hole=0.4,
    )
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=320)
    return fig
