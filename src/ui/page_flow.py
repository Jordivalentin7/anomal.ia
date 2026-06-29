"""Página 5 — Esquema interactivo del flujo del router adaptativo."""
from __future__ import annotations

import streamlit as st

from .common import page_header


NODE_INFO = {
    "1": {
        "title": "Consulta del operador",
        "kicker": "INPUT",
        "summary": (
            "Punto de entrada al pipeline. El operador formula una pregunta "
            "en lenguaje natural desde la interfaz SCADA."
        ),
        "details": [
            "Acepta preguntas de cualquier longitud y nivel técnico",
            "No se realiza preprocesamiento ni normalización",
            "La consulta se pasa tal cual al clasificador",
        ],
        "example": "«¿Es seguro un cloro residual de 0.4 mg/L?»",
        "module": "src/ui/common.py · query_picker()",
    },
    "2": {
        "title": "Clasificador de nivel",
        "kicker": "DETECT COMPLEXITY",
        "summary": (
            "Analiza la consulta mediante patrones léxicos y determina su "
            "nivel de complejidad antes de enviarla al modelo."
        ),
        "details": [
            "Regex y keywords identifican verbos de acción, operadores y unidades",
            "Detecta solicitudes de cálculo, normativa o diagnóstico complejo",
            "Devuelve nivel + score de confianza + razones",
        ],
        "example": "classify('¿Es seguro...?') → Básica · confianza 0.82",
        "module": "src/classifier.py · classify()",
    },
    "3": {
        "title": "Nivel detectado",
        "kicker": "BASIC · INTERMEDIATE · ADVANCED · EXPERT",
        "summary": (
            "Etiqueta discreta que selecciona la plantilla de prompt. "
            "Se propaga al siguiente paso como clave de lookup."
        ),
        "details": [
            "Básica — verificación directa, respuesta de 20–40 palabras",
            "Intermedia — consulta normativa, 60–100 palabras",
            "Avanzada — cálculo con fórmula, 150–250 palabras",
            "Experta — análisis multicriterio, 300–500 palabras",
        ],
        "example": "LENGTH_TARGETS['Básica'] = {optimal: 20–40}",
        "module": "src/config.py · LENGTH_TARGETS",
    },
    "4": {
        "title": "Prompt especializado",
        "kicker": "TEMPLATE · LEVEL",
        "summary": (
            "Selecciona y aplica el prompt de sistema correspondiente al "
            "nivel detectado. Cada plantilla ajusta tono, extensión y formato."
        ),
        "details": [
            "Plantilla específica por nivel (no un prompt único como el baseline)",
            "Incluye rango de palabras esperado y tipo de respuesta",
            "Inyecta el resultado de verificación determinista si existe",
        ],
        "example": "prompt_for('Básica') → 'Responde en 1 frase…'",
        "module": "src/prompts.py · prompt_for()",
    },
    "5": {
        "title": "LLM · Inferencia",
        "kicker": "MISTRAL · GROQ · LLAMA",
        "summary": (
            "Llamada al modelo de lenguaje seleccionado con el prompt "
            "especializado + la consulta del operador."
        ),
        "details": [
            "Proveedores soportados: Mistral AI y Groq (Llama 3.1/3.3)",
            "Temperatura fija en 0.0 para reproducibilidad",
            "max_tokens = 800, timeout por defecto",
        ],
        "example": "call_model(spec, system_prompt, user_prompt)",
        "module": "src/providers.py · call_model()",
    },
    "6": {
        "title": "Respuesta ajustada",
        "kicker": "OUTPUT · OPTIMIZED",
        "summary": (
            "Salida final devuelta al operador. A diferencia del baseline, "
            "su formato y extensión coinciden con lo esperado para el nivel."
        ),
        "details": [
            "Evaluada por cinco métricas: keywords, unidades, técnica, cálculo y longitud",
            "Puntuación ponderada según el nivel",
            "Comparable frente a la respuesta baseline en la sección 04",
        ],
        "example": "evaluate(response, 'Básica') → score 0.87",
        "module": "src/evaluation.py · evaluate()",
    },
}


NODE_ORDER = [
    ("1", "Consulta del operador"),
    ("2", "Clasificador de nivel"),
    ("3", "Nivel detectado"),
    ("4", "Prompt especializado"),
    ("5", "LLM · Inferencia"),
    ("6", "Respuesta ajustada"),
]


# CSS específico de la página: estiliza el radio vertical como lista de botones-pipeline
FLOW_CSS = """
<style>
/* Marker invisible para detectar la columna izquierda */
.flow-marker { display: none; }

/* La columna izquierda entera se convierte en tarjeta */
[data-testid="column"]:has(.flow-marker) {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-left: 4px solid #14B8A6;
    border-radius: 12px;
    padding: 1.3rem 1.5rem !important;
    box-sizing: border-box;
}

/* Igualamos altura de las dos columnas y añadimos margen superior */
[data-testid="stHorizontalBlock"]:has(.flow-marker) {
    align-items: stretch !important;
    margin-top: 1.5rem !important;
}

/* Targetamos el radio DIRECTAMENTE por la clase de su key (más fiable) */
.st-key-flow_node_radio [role="radiogroup"] {
    display: flex !important;
    flex-direction: column !important;
    gap: 0.8rem !important;
    width: 100% !important;
}

/* CADA OPCIÓN se transforma en TARJETA-BOTÓN */
.st-key-flow_node_radio [role="radiogroup"] label {
    width: 240px !important;
    max-width: 240px !important;
    min-width: 240px !important;
    margin: 0 !important;
    padding: 0.75rem 1.1rem !important;
    background: #FFFFFF !important;
    border: 1.5px solid #E2E8F0 !important;
    border-left: 3px solid #E2E8F0 !important;
    border-radius: 10px !important;
    font-family: 'Manrope', sans-serif !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    color: #0A1F3D !important;
    cursor: pointer !important;
    transition: all 0.15s ease !important;
    box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06) !important;
    box-sizing: border-box !important;
    display: flex !important;
    align-items: center !important;
}
.st-key-flow_node_radio [role="radiogroup"] label:hover {
    border-color: #14B8A6 !important;
    border-left-color: #14B8A6 !important;
    color: #0F766E !important;
    transform: translateX(2px);
    box-shadow: 0 4px 12px rgba(20, 184, 166, 0.12) !important;
}

/* Oculta el círculo del radio nativo */
.st-key-flow_node_radio [role="radiogroup"] label > div:first-child {
    display: none !important;
}

/* Texto interno */
.st-key-flow_node_radio [role="radiogroup"] label p {
    margin: 0 !important;
    font-family: 'Manrope', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    color: inherit !important;
    line-height: 1.2 !important;
    font-variant-numeric: tabular-nums !important;
    white-space: nowrap !important;
}

/* Estado seleccionado: teal suave + borde izquierdo grueso */
.st-key-flow_node_radio [role="radiogroup"] label:has(input:checked) {
    background: #F0FDFA !important;
    border-color: #14B8A6 !important;
    border-left: 4px solid #14B8A6 !important;
    color: #0F766E !important;
    box-shadow: 0 4px 12px rgba(20, 184, 166, 0.18) !important;
}
.st-key-flow_node_radio [role="radiogroup"] label:has(input:checked) p {
    color: #0F766E !important;
}

/* Oculta la etiqueta del radio (label_visibility=collapsed ya lo hace pero por si acaso) */
.st-key-flow_node_radio > label,
.st-key-flow_node_radio [data-testid="stWidgetLabel"] {
    display: none !important;
}
</style>
"""


def _build_info_panel(selected: str) -> str:
    info = NODE_INFO[selected]
    details_html = "".join(
        f"<li style='margin-bottom:0.4rem;'>{d}</li>" for d in info["details"]
    )
    return (
        "<div style='background:#FFFFFF;border:1px solid #E2E8F0;"
        "border-left:4px solid #14B8A6;border-radius:12px;"
        "padding:1.3rem 1.5rem;box-sizing:border-box;'>"
        f"<div style='font-family:\"JetBrains Mono\",monospace;"
        f"font-size:11px;letter-spacing:0.16em;color:#14B8A6;"
        f"font-weight:700;margin-bottom:0.4rem;'>"
        f"NODO {selected} · {info['kicker']}</div>"
        f"<h3 style='font-family:\"Manrope\",sans-serif;font-weight:400;"
        f"font-size:1.5rem;color:#0A1F3D;margin:0 0 0.8rem 0;"
        f"letter-spacing:-0.02em;line-height:1.2;'>{info['title']}</h3>"
        f"<p style='color:#475569;font-size:0.95rem;line-height:1.55;"
        f"margin:0 0 1rem 0;'>{info['summary']}</p>"
        f"<div style='font-family:\"JetBrains Mono\",monospace;font-size:10px;"
        f"letter-spacing:0.12em;color:#64748B;font-weight:700;"
        f"margin-bottom:0.5rem;'>DETALLES</div>"
        f"<ul style='color:#334155;font-size:0.88rem;line-height:1.55;"
        f"margin:0 0 1rem 0;padding-left:1.2rem;'>{details_html}</ul>"
        f"<div style='font-family:\"JetBrains Mono\",monospace;font-size:10px;"
        f"letter-spacing:0.12em;color:#64748B;font-weight:700;"
        f"margin-bottom:0.4rem;'>EJEMPLO</div>"
        f"<div style='background:#F8FAFC;border:1px solid #E2E8F0;"
        f"border-radius:8px;padding:0.7rem 0.9rem;"
        f"font-family:\"JetBrains Mono\",monospace;font-size:0.82rem;"
        f"color:#0F766E;margin-bottom:1rem;word-break:break-word;'>"
        f"{info['example']}</div>"
        f"<div style='font-family:\"JetBrains Mono\",monospace;font-size:10px;"
        f"letter-spacing:0.12em;color:#94A3B8;font-weight:600;"
        f"padding-top:0.5rem;border-top:1px solid #F1F5F9;'>"
        f"{info['module']}</div>"
        "</div>"
    )


def render() -> None:
    page_header(
        number="05",
        page_name="Flujo del router",
        title_html="Pipeline de clasificación en <em>tiempo real</em>",
        lede=(
            "Pulsa en cualquier nodo del diagrama para ver su rol, "
            "parámetros y ubicación en el código."
        ),
    )

    st.markdown(FLOW_CSS, unsafe_allow_html=True)

    col_l, col_r = st.columns([3, 5], gap="small")

    with col_l:
        # Marker invisible para targetear esta columna desde CSS (la columna se vuelve la tarjeta)
        st.markdown("<span class='flow-marker'></span>", unsafe_allow_html=True)
        # Radio nativo de Streamlit estilizado como lista de tarjetas-botón
        node_ids = [nid for nid, _ in NODE_ORDER]
        labels = {nid: f"{nid}.  {title}" for nid, title in NODE_ORDER}
        selected = st.radio(
            label="pipeline",
            options=node_ids,
            format_func=lambda x: labels[x],
            key="flow_node_radio",
            label_visibility="collapsed",
        )

    with col_r:
        st.markdown(_build_info_panel(selected), unsafe_allow_html=True)
