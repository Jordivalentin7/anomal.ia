"""Página 1 — Resumen del TFG y planteamiento."""
from __future__ import annotations

import streamlit as st

from .common import page_header


PROBLEM_SOLUTION_HTML = """
<div style='display:grid;grid-template-columns:1fr 1fr;gap:0.8rem;margin-bottom:1rem;'>
  <div style='
      background:#FFFFFF;
      border:1px solid #E2E8F0;
      border-left:4px solid #EF4444;
      border-radius:10px;
      padding:0.85rem 1.1rem;
  '>
    <div style='
        display:flex;align-items:center;gap:0.55rem;
        font-size:0.74rem;letter-spacing:0.1em;text-transform:uppercase;
        color:#991B1B;font-weight:700;margin-bottom:0.6rem;
    '>
      <span style='
          display:inline-block;width:8px;height:8px;border-radius:50%;
          background:#EF4444;
      '></span>
      Problema
    </div>
    <div style='font-size:1rem;color:#0A1F3D;font-weight:600;margin-bottom:0.45rem;'>
      Sobre-elaboración en preguntas simples
    </div>
    <div style='color:#475569;font-size:0.92rem;line-height:1.55;'>
      Un LLM entrenado como experto responde con 150 palabras a
      «¿es seguro este cloro?» cuando el operador solo necesita un
      <i>sí/no</i>. El exceso de contexto dificulta la decisión rápida.
    </div>
  </div>
  <div style='
      background:#FFFFFF;
      border:1px solid #E2E8F0;
      border-left:4px solid #14B8A6;
      border-radius:10px;
      padding:0.85rem 1.1rem;
  '>
    <div style='
        display:flex;align-items:center;gap:0.55rem;
        font-size:0.74rem;letter-spacing:0.1em;text-transform:uppercase;
        color:#0F766E;font-weight:700;margin-bottom:0.6rem;
    '>
      <span style='
          display:inline-block;width:8px;height:8px;border-radius:50%;
          background:#14B8A6;
      '></span>
      Propuesta
    </div>
    <div style='font-size:1rem;color:#0A1F3D;font-weight:600;margin-bottom:0.45rem;'>
      Clasificar antes de preguntar
    </div>
    <div style='color:#475569;font-size:0.92rem;line-height:1.55;'>
      La consulta se analiza primero, se identifica su nivel y se aplica
      un prompt específico. El LLM devuelve una respuesta ajustada al
      tipo de pregunta: breve cuando toca, detallada cuando hace falta.
    </div>
  </div>
</div>
"""


SECTIONS = [
    ("02", "SCADA", "Dataset del operador", "Monitorización SCADA"),
    ("03", "Comparativa", "Ranking entre modelos", "Comparativa de modelos"),
    ("04", "Router", "Baseline vs. propuesta", "Router adaptativo"),
    ("05", "Flujo", "Esquema del proceso", "Flujo del router"),
]


NAV_BUTTON_CSS = """
<style>
.resumen-nav-grid div[data-testid="stButton"] {
    position: relative;
}
.resumen-nav-grid div[data-testid="stButton"] button {
    width: 100% !important;
    text-align: left !important;
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
    padding: 1rem 1.1rem !important;
    height: 120px !important;
    transition: all 0.2s ease !important;
    color: #0A1F3D !important;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04) !important;
    font-weight: 500 !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: flex-start !important;
    justify-content: flex-start !important;
    gap: 0 !important;
    overflow: hidden !important;
    position: relative !important;
}
.resumen-nav-grid div[data-testid="stButton"] button::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #14B8A6 0%, #0EA5E9 100%);
    opacity: 0;
    transition: opacity 0.2s ease;
}
.resumen-nav-grid div[data-testid="stButton"] button::after {
    content: '→';
    position: absolute;
    bottom: 1rem;
    right: 1.2rem;
    font-size: 1.15rem;
    color: #CBD5E1;
    transition: all 0.2s ease;
    font-weight: 600;
}
.resumen-nav-grid div[data-testid="stButton"] button:hover {
    border-color: #14B8A6 !important;
    box-shadow: 0 10px 28px rgba(20, 184, 166, 0.15) !important;
    transform: translateY(-2px);
}
.resumen-nav-grid div[data-testid="stButton"] button:hover::before {
    opacity: 1;
}
.resumen-nav-grid div[data-testid="stButton"] button:hover::after {
    color: #14B8A6;
    transform: translateX(3px);
}
.resumen-nav-grid div[data-testid="stButton"] button p {
    margin: 0 !important;
    text-align: left !important;
    line-height: 1.35 !important;
    width: 100% !important;
}
.resumen-nav-grid div[data-testid="stButton"] button p:nth-of-type(1) {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.78rem !important;
    color: #14B8A6 !important;
    font-weight: 700 !important;
    letter-spacing: 0.12em !important;
    margin-bottom: 0.7rem !important;
}
.resumen-nav-grid div[data-testid="stButton"] button p:nth-of-type(2) {
    font-size: 1.08rem !important;
    color: #0A1F3D !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em !important;
    margin-bottom: 0.35rem !important;
}
.resumen-nav-grid div[data-testid="stButton"] button p:nth-of-type(3) {
    font-size: 0.85rem !important;
    color: #64748B !important;
    font-weight: 400 !important;
}
</style>
"""


def _set_nav(section_name: str) -> None:
    st.session_state["nav_page"] = section_name


def render() -> None:
    page_header(
        number="01",
        page_name="Resumen",
        title_html=(
            "Detección de anomalías en<br>"
            "<em>infraestructuras críticas</em> con IA."
        ),
        lede=(
            "Mejora el uso de los grandes modelos de lenguaje en "
            "infraestructuras críticas reduciendo la dependencia de la "
            "pericia del usuario."
        ),
        is_hero=True,
    )
    st.markdown(PROBLEM_SOLUTION_HTML, unsafe_allow_html=True)

    st.markdown(NAV_BUTTON_CSS, unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:0.74rem;letter-spacing:0.1em;"
        "text-transform:uppercase;color:#64748B;font-weight:700;"
        "margin-bottom:0.6rem;'>Recorrido de la demo</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='resumen-nav-grid'>", unsafe_allow_html=True)
    cols = st.columns(len(SECTIONS))
    for col, (num, title, desc, target) in zip(cols, SECTIONS):
        with col:
            label = f"**{num}**\n\n**{title}**\n\n{desc}"
            st.button(
                label,
                key=f"nav_resumen_{num}",
                use_container_width=True,
                on_click=_set_nav,
                args=(target,),
            )
    st.markdown("</div>", unsafe_allow_html=True)
