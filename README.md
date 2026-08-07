# ⚡ Humanox AI Sport Analytics

**Plataforma de analítica deportiva e IA aplicada al rendimiento y prevención
de lesiones**, a partir de datos biométricos simulados de sensores
inteligentes (espinilleras inteligentes, pulseras GPS, etc.).

MVP funcional construido con Python + Streamlit, sin dependencias de pago
ni APIs externas: 100% ejecutable en local y gratuito.

---

## 📌 Descripción

Humanox AI Sport Analytics simula un sistema real de monitoreo deportivo:

- Cada jugador del equipo tiene sensores ficticios que registran
  frecuencia cardíaca, distancia recorrida, velocidad máxima,
  aceleraciones, fatiga, calidad de sueño y fuerza de disparo en cada
  entrenamiento.
- Un **motor de reglas inteligentes** (sin IA generativa ni costo)
  analiza automáticamente esos datos y genera alertas de riesgo de
  lesión y de rendimiento.
- Un **dashboard ejecutivo** resume el estado del equipo completo:
  jugadores en riesgo, más constantes, rankings de velocidad, fuerza y
  fatiga.
- Un **simulador** permite generar nuevos entrenamientos con un clic,
  como si llegaran en vivo desde el hardware.

El proyecto está pensado como una demo de producto: los datos son
ficticios, pero la arquitectura, el modelado y la lógica de alertas
están construidos como lo haría un equipo de ingeniería real.

---

## 🧰 Tecnologías

| Categoría          | Tecnología          |
|--------------------|---------------------|
| Lenguaje           | Python 3.10+        |
| Interfaz / Dashboard | Streamlit         |
| Base de datos      | SQLite              |
| Manipulación de datos | Pandas            |
| Visualización      | Plotly              |
| Motor de alertas   | Reglas de negocio propias (sin API de pago) |

No se usa ninguna API externa de pago (ni OpenAI ni similares). Todas
las "predicciones" y alertas se generan con lógica determinística
basada en umbrales deportivos razonables, documentada en
`modules/alerts.py`.

---

## 📂 Arquitectura del proyecto

```
humanox-ai/
│
├── app.py                # Interfaz Streamlit (UI). Orquesta todo lo demás.
├── database.py           # Acceso a datos: esquema SQLite, seeding, queries.
├── analytics.py          # KPIs, rankings y agregaciones de negocio.
├── simulator.py          # Generador de entrenamientos aleatorios realistas.
├── requirements.txt      # Dependencias del proyecto.
├── README.md             # Este documento.
├── .streamlit/
│   └── config.toml       # Tema visual (dark, colores de marca).
├── data/
│   └── jugadores.db      # Base de datos SQLite (autogenerada al ejecutar).
├── assets/
│   └── logo.svg          # Logo de marca.
├── screenshots/          # Capturas de la app (ver screenshots/README.md).
└── modules/
    ├── alerts.py          # Motor de reglas inteligentes (alertas).
    ├── charts.py          # Constructores de gráficas Plotly reutilizables.
    └── styles.py          # CSS y branding de la interfaz.
```

Cada archivo tiene una única responsabilidad:

- **`database.py`** no sabe nada de Streamlit ni de reglas de negocio:
  solo persiste y consulta datos.
- **`analytics.py`** no sabe nada de SQL ni de la interfaz: solo
  transforma DataFrames en KPIs y rankings.
- **`modules/alerts.py`** contiene exclusivamente la lógica de reglas
  de riesgo, aislada para poder ajustar umbrales sin tocar el resto.
- **`modules/charts.py`** centraliza el estilo visual de todas las
  gráficas Plotly.
- **`app.py`** es la única capa que "sabe" de Streamlit: arma la
  página combinando los módulos anteriores.

---

## 🚀 Instalación

Requisitos previos: tener Python 3.10 o superior instalado.

```bash
# 1. Clona o descomprime el proyecto
cd humanox-ai

# 2. (Recomendado) crea un entorno virtual
python -m venv venv
source venv/bin/activate      # En Windows: venv\Scripts\activate

# 3. Instala las dependencias
pip install -r requirements.txt
```

---

## ▶️ Cómo ejecutar

```bash
streamlit run app.py
```

Esto abrirá automáticamente el navegador en `http://localhost:8501`.

En el **primer arranque**, la aplicación:

1. Crea la base de datos SQLite en `data/jugadores.db`.
2. Genera automáticamente entre 15 y 20 jugadores ficticios.
3. Genera un historial de 8 a 15 entrenamientos por jugador (más de
   150 registros en total), con valores realistas y coherentes entre sí.

No necesitas ejecutar ningún script adicional: todo ocurre al vuelo.

---

## 🖥️ Capturas de ejemplo

> Ver `screenshots/README.md` para instrucciones de cómo generarlas
> localmente antes de tu presentación. Las secciones principales son:

- **Dashboard General**: KPIs del equipo, evolución histórica de
  fatiga/FC/sueño, distribución por posición y tabla filtrable.
- **Jugador Individual**: radar comparativo vs. el equipo, gauges de
  fatiga y FC, evolución histórica por métrica y alertas personales.
- **Alertas Inteligentes**: listado de riesgos activos agrupados por
  severidad, con detalle tabular exportable.
- **Panel Ejecutivo**: jugadores de mayor riesgo, más constantes, y
  rankings de velocidad, fuerza y fatiga de todo el equipo.

---

## 🧠 Explicación técnica

### Modelo de datos

- **`jugadores`**: id, nombre, posición, edad.
- **`entrenamientos`**: id, jugador_id (FK), fecha, frecuencia
  cardíaca, distancia recorrida, velocidad máxima, aceleraciones,
  fatiga (1-10), calidad de sueño (1-10), fuerza de disparo.

### Simulador (`simulator.py`)

Genera nuevos registros a partir del **promedio histórico del propio
jugador**, aplicando variaciones aleatorias controladas (con
`random.gauss` y rangos acotados) para que los nuevos datos sean
realistas en vez de puramente arbitrarios — igual que el ruido natural
de un sensor real.

### Motor de alertas (`modules/alerts.py`)

Implementa tres reglas de negocio, cada una documentada en su propia
función:

1. **Riesgo de lesión muscular**: frecuencia cardíaca ≥ 165 bpm **y**
   fatiga ≥ 7/10 en el último entrenamiento.
2. **Recomendación de reducir carga**: calidad de sueño ≤ 4/10.
3. **Posible pérdida de rendimiento**: la distancia recorrida promedio
   de los últimos 3 entrenamientos cae más de un 15% respecto al
   promedio histórico previo.

Los umbrales están centralizados como constantes al inicio del archivo
para que puedan ajustarse sin tocar la lógica.

### Analítica (`analytics.py`)

Agrega los entrenamientos por jugador para calcular KPIs, tops
(velocidad, fuerza), ranking de fatiga, jugadores más constantes
(menor desviación estándar en distancia recorrida) y un estado físico
general del equipo (Óptimo / Con precaución / Crítico).

---

## ✅ Validación realizada

Antes de la entrega, este proyecto fue probado de extremo a extremo:

- Compilación de todos los módulos Python sin errores de sintaxis.
- Ejecución completa de `app.py` con `streamlit.testing.v1.AppTest`
  (el framework oficial de testing de Streamlit), sin excepciones.
- Prueba de interactividad real: selección de jugador en el filtro,
  clic en "Simular entrenamiento" y clic en "Simular jornada completa",
  todo verificado sin errores.
- Prueba funcional de la base de datos, el simulador, los KPIs y el
  motor de alertas de forma aislada (fuera de Streamlit).

---

## 🔮 Posibles mejoras futuras

- Conexión real con hardware de sensores vía MQTT o WebSocket.
- Autenticación de usuarios (cuerpo técnico, jugadores, directivos).
- Exportación de reportes en PDF por jugador o por jornada.
- Modelos predictivos de series temporales (ej. Prophet o modelos de
  regresión) para anticipar la fatiga acumulada, en vez de solo reglas.
- Migración de SQLite a PostgreSQL para un entorno multiusuario.
- Notificaciones push/email automáticas cuando se dispare una alerta
  de riesgo alto.
- Comparativas entre jornadas, temporadas o entre distintos equipos.

---

## 📄 Licencia y alcance

Proyecto desarrollado con fines demostrativos (MVP). Todos los datos
de jugadores son **completamente ficticios** y generados
aleatoriamente; cualquier coincidencia con personas reales es
casualidad.
