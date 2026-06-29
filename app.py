"""Anomal.ia — Herramienta apoyada en IA para la detección de anomalías.

Punto de entrada Streamlit del TFG. Articula cuatro vistas: resumen,
monitorización SCADA, comparativa de modelos y router adaptativo.

Lanzamiento:
    streamlit run app.py

Requiere MISTRAL_API_KEY y/o GROQ_API_KEY en un archivo .env.
"""
from __future__ import annotations

import streamlit as st

from src.ui.page_compare import render as render_compare
from src.ui.page_flow import render as render_flow
from src.ui.page_results import render as render_results
from src.ui.page_resumen import render as render_resumen
from src.ui.page_router import render as render_router
from src.ui.page_scada import render as render_scada
from src.ui.styles import CUSTOM_CSS


PAGES = {
    "Resumen": ("01", render_resumen),
    "Monitorización SCADA": ("02", render_scada),
    "Comparativa de modelos": ("03", render_compare),
    "Router adaptativo": ("04", render_router),
    "Flujo del router": ("05", render_flow),
    "Resultados obtenidos": ("06", render_results),
}


@st.cache_resource
def _warm_up_classifier_llm() -> bool:
    """Pre-calienta el cliente Groq haciendo una clasificación dummy.

    El cold start de Groq añade ~1 s a la primera llamada de la sesión.
    Lanzando una clasificación ligera al arrancar (cacheada con
    st.cache_resource para que se ejecute una sola vez por proceso) el
    primer query real del operador encuentra el cliente caliente.
    Cualquier fallo se ignora silenciosamente: no debe impedir el arranque.
    """
    try:
        from src.classifier import _classify_llm
        _classify_llm("calentamiento del clasificador")
        return True
    except Exception:  # noqa: BLE001
        return False


def _topbar_html(number: str, page_name: str, dataset_label: str) -> str:
    return (
        "<div class='caudal-topbar'>"
        "<span class='caudal-topbar-brand'>ANOMAL.IA</span>"
        "<span class='caudal-topbar-sep'>·</span>"
        f"<span class='caudal-topbar-mark'>{number} · {page_name.upper()}</span>"
        "<span class='caudal-topbar-dataset'>"
        "<span class='caudal-topbar-ds-label'>DATASET</span>"
        f"<span class='caudal-topbar-ds-name'>{dataset_label}</span>"
        "</span>"
        "</div>"
    )


BRAND_HTML = """
<div class='caudal-brand'>
  <div class='caudal-logo'><span class='caudal-logo-name'>Anomal</span><span class='caudal-logo-ai'>.ia</span></div>
</div>
"""


SIDEBAR_FOOTER_HTML = (
    "<div class='caudal-sidebar-footer'>"
    "Jordi Valentín Ivanov<br>"
    "TFG · Ingeniería Multimedia<br>"
    "Universidad de Alicante · 2025–26"
    "</div>"
)


def main() -> None:
    st.set_page_config(
        page_title="Anomal.ia · Agente SCADA",
        page_icon="≋",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # Pre-calentar el cliente Groq al primer arranque del proceso para
    # eliminar el cold start (~1 s) de la primera clasificación real.
    _warm_up_classifier_llm()

    with st.sidebar:
        st.markdown(BRAND_HTML, unsafe_allow_html=True)
        st.markdown("#### Navegación")
        page = st.radio(
            label="Sección",
            options=list(PAGES.keys()),
            label_visibility="collapsed",
            key="nav_page",
        )
        st.markdown(SIDEBAR_FOOTER_HTML, unsafe_allow_html=True)

    number, renderer = PAGES[page]
    # Reservamos slot en la parte superior para el topbar, lo rellenamos al
    # terminar la renderización para que refleje el dataset activo justo en el
    # momento del último cambio (selección, upload, etc.).
    topbar_slot = st.empty()
    renderer()
    dataset_label = st.session_state.get(
        "scada_active", "Por defecto · dataset_evaluacion.csv"
    )
    topbar_slot.markdown(
        _topbar_html(number, page, dataset_label), unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
