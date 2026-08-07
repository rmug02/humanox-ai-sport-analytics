"""
modules/styles.py
------------------
Estilos CSS y elementos de branding para dar a Humanox AI Sport
Analytics una apariencia de producto profesional dentro de Streamlit.
"""

CUSTOM_CSS = """
<style>
    /* Tipografía general */
    html, body, [class*="css"] {
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }

    /* Tarjetas de KPI */
    div[data-testid="stMetric"] {
        background-color: #1F2937;
        border: 1px solid #2D3748;
        border-radius: 12px;
        padding: 14px 18px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.25);
    }
    div[data-testid="stMetric"] label {
        color: #9CA3AF !important;
    }

    /* Encabezado de marca */
    .humanox-header {
        display: flex;
        align-items: center;
        gap: 12px;
        padding-bottom: 6px;
        margin-bottom: 10px;
        border-bottom: 1px solid #2D3748;
    }
    .humanox-header h1 {
        font-size: 26px;
        margin: 0;
        background: linear-gradient(90deg, #00E5A0, #3B82F6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .humanox-subtitle {
        color: #9CA3AF;
        font-size: 14px;
        margin-top: -6px;
    }

    /* Badges de alerta */
    .badge-alto {
        background-color: #3a1414;
        color: #FF6B6B;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
        border: 1px solid #FF4D4D55;
    }
    .badge-medio {
        background-color: #3a2c10;
        color: #FFC24D;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
        border: 1px solid #FFB02055;
    }
    .badge-ok {
        background-color: #0f3324;
        color: #4DFFB0;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
        border: 1px solid #00E5A055;
    }

    /* Botones */
    button[kind="primary"] {
        background-color: #00E5A0 !important;
        color: #0B1120 !important;
        font-weight: 600 !important;
        border: none !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #111827;
    }
</style>
"""

LOGO_SVG = """
<svg width="42" height="42" viewBox="0 0 42 42" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00E5A0"/>
      <stop offset="100%" stop-color="#3B82F6"/>
    </linearGradient>
  </defs>
  <circle cx="21" cy="21" r="20" fill="#111827" stroke="url(#grad)" stroke-width="2"/>
  <path d="M13 28 L13 14 L18 14 L18 19 L24 19 L24 14 L29 14 L29 28 L24 28 L24 23 L18 23 L18 28 Z"
        fill="url(#grad)"/>
</svg>
"""


def render_header(st) -> None:
    """Inyecta el CSS y dibuja el encabezado con logo y título de marca.

    Recibe el módulo `st` de Streamlit como parámetro (en lugar de
    importarlo aquí) para evitar dependencias circulares y facilitar
    pruebas del módulo de forma aislada.
    """
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="humanox-header">
            {LOGO_SVG}
            <div>
                <h1>Humanox AI Sport Analytics</h1>
                <div class="humanox-subtitle">
                    Monitoreo biométrico y prevención de lesiones en tiempo real
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def badge_html(nivel: str) -> str:
    """Devuelve un <span> HTML con el estilo de badge correspondiente al
    nivel de alerta ('alto', 'medio' o cualquier otro valor = ok)."""
    clase = {"alto": "badge-alto", "medio": "badge-medio"}.get(nivel, "badge-ok")
    etiqueta = {"alto": "RIESGO ALTO", "medio": "PRECAUCIÓN"}.get(nivel, "OK")
    return f'<span class="{clase}">{etiqueta}</span>'
