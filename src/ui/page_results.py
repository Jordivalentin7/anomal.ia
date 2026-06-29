"""Página 5 — Resultados obtenidos.

Vista de documentación del trabajo experimental: para cada una de las 12
consultas del banco oficial (3 por nivel), se muestra cara a cara la
respuesta del Mixtral fine-tuneado de Arnau-Muñoz et al. frente a la
respuesta del router adaptativo del TFG (capturada automáticamente al
ejecutarla en la vista Router adaptativo).

Sirve como portfolio visual de los experimentos realizados, organizado
por dificultad y con métricas comparadas (palabras, latencia, calidad).
"""
from __future__ import annotations

import streamlit as st

from ..reference_bank import bank_size, lookup_reference
from ..results_store import get_all_results, get_result_for
from .common import EXAMPLE_QUERIES, page_header


_LEVEL_META = {
    "Básica": {
        "color": "#14B8A6",
        "accent": "rgba(20,184,166,0.10)",
        "border": "rgba(20,184,166,0.40)",
        "icon": "01",
        "desc": "verificación binaria de un valor contra un rango conocido",
    },
    "Intermedia": {
        "color": "#0EA5E9",
        "accent": "rgba(14,165,233,0.10)",
        "border": "rgba(14,165,233,0.40)",
        "icon": "02",
        "desc": "evaluación contra criterio normativo u operativo",
    },
    "Avanzada": {
        "color": "#8B5CF6",
        "accent": "rgba(139,92,246,0.10)",
        "border": "rgba(139,92,246,0.40)",
        "icon": "03",
        "desc": "cálculo numérico explícito o comparación cuantitativa",
    },
    "Experta": {
        "color": "#EF4444",
        "accent": "rgba(239,68,68,0.10)",
        "border": "rgba(239,68,68,0.40)",
        "icon": "04",
        "desc": "diagnóstico abierto, optimización o predicción contextual",
    },
}


def _render_summary(total: int, captured: int) -> None:
    """Banda superior con el progreso de documentación (X/12 capturadas)."""
    pct = (captured / total * 100) if total else 0
    remaining = total - captured
    st.markdown(
        f"<div style='background:#FFFFFF;border:1px solid #E2E8F0;"
        f"border-radius:14px;padding:1.1rem 1.4rem;margin-bottom:1.6rem;"
        f"display:flex;align-items:center;gap:2rem;flex-wrap:wrap;'>"
        f"<div>"
        f"<div style='font-family:\"JetBrains Mono\",monospace;font-size:0.72rem;"
        f"letter-spacing:0.14em;font-weight:700;color:#64748B;'>"
        f"PROGRESO DE DOCUMENTACIÓN</div>"
        f"<div style='font-family:Manrope,sans-serif;font-weight:700;"
        f"font-size:1.8rem;color:#0A1F3D;margin-top:0.15rem;'>"
        f"{captured} <span style='color:#64748B;font-weight:400;'>/ {total}</span> "
        f"<span style='font-size:1rem;color:#64748B;font-weight:400;'>"
        f"consultas capturadas</span></div>"
        f"</div>"
        f"<div style='flex:1;min-width:220px;'>"
        f"<div style='background:#F1F5F9;border-radius:10px;height:10px;"
        f"overflow:hidden;'>"
        f"<div style='background:linear-gradient(90deg,#14B8A6 0%,#0EA5E9 100%);"
        f"width:{pct}%;height:100%;transition:width 0.4s ease;'></div>"
        f"</div>"
        f"<div style='font-size:0.78rem;color:#64748B;margin-top:0.4rem;'>"
        f"{pct:.0f}% completado · {remaining} consultas pendientes "
        f"de ejecutar en la vista <b>Router adaptativo</b></div>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _format_pill(label: str, color: str = "#14B8A6") -> str:
    return (
        f"<span style='display:inline-block;font-family:\"JetBrains Mono\",monospace;"
        f"font-size:0.68rem;letter-spacing:0.12em;font-weight:700;color:{color};"
        f"background:{color}1a;border:1px solid {color}55;border-radius:6px;"
        f"padding:0.18rem 0.55rem;text-transform:uppercase;'>{label}</span>"
    )


def _render_question_card(query: str, level: str, idx: int) -> None:
    """Card comparando paper vs TFG para una consulta concreta."""
    paper = lookup_reference(query)
    tfg = get_result_for(query)

    # Banner de pregunta
    meta = _LEVEL_META[level]
    st.markdown(
        f"<div style='border:1px solid #E2E8F0;border-left:4px solid {meta['color']};"
        f"border-radius:12px;background:#FFFFFF;padding:1.1rem 1.3rem;"
        f"margin-bottom:0.9rem;'>"
        f"<div style='font-family:\"JetBrains Mono\",monospace;font-size:0.72rem;"
        f"letter-spacing:0.14em;font-weight:700;color:{meta['color']};"
        f"margin-bottom:0.55rem;'>"
        f"P{idx:02d} · {level.upper()}</div>"
        f"<div style='font-family:Manrope,sans-serif;font-weight:600;"
        f"font-size:1.05rem;color:#0A1F3D;line-height:1.4;'>{query}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    col_l, col_r = st.columns(2)

    # === Columna izquierda: Mixtral entrenado (paper) ===
    with col_l:
        st.markdown(
            f"<div style='font-family:Manrope,sans-serif;font-weight:600;"
            f"font-size:0.92rem;color:#0A1F3D;margin-bottom:0.4rem;'>"
            f"Mixtral entrenado · Arnau-Muñoz et al.</div>",
            unsafe_allow_html=True,
        )
        if paper is None:
            if bank_size() == 0:
                st.markdown(
                    "<div style='background:#F1F5F9;border:1px dashed #CBD5E1;"
                    "border-radius:10px;padding:0.9rem 1.05rem;color:#475569;"
                    "font-size:0.85rem;text-align:center;line-height:1.5;'>"
                    "<b>Material no incluido en el repositorio público.</b><br>"
                    "Las respuestas oficiales del paper de Arnau-Muñoz et al. "
                    "no se distribuyen aquí. Coloca <code>data/reference_responses.json</code> "
                    "en local si tienes acceso a las evaluaciones del trabajo."
                    "</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.info("Esta pregunta no está en el banco oficial cargado.")
        else:
            words = paper.word_count
            with st.container(border=True):
                st.markdown(paper.answer)
            st.markdown(
                f"<div style='display:flex;gap:1rem;justify-content:center;"
                f"padding:0.45rem 0.7rem;margin-top:0.5rem;"
                f"background:rgba(15,23,42,0.04);border-radius:8px;"
                f"font-family:\"JetBrains Mono\",monospace;font-size:0.75rem;"
                f"color:#475569;'>"
                f"<span><b style='color:#0A1F3D;'>{words}</b> palabras</span>"
                f"<span><b style='color:#0A1F3D;'>{paper.response_time:.2f}s</b></span>"
                f"<span>Q&nbsp;<b style='color:#0A1F3D;'>{paper.quality_score:.2f}</b></span>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # === Columna derecha: Router adaptativo (TFG) ===
    with col_r:
        st.markdown(
            f"<div style='font-family:Manrope,sans-serif;font-weight:600;"
            f"font-size:0.92rem;color:#0A1F3D;margin-bottom:0.4rem;'>"
            f"Router adaptativo · TFG</div>",
            unsafe_allow_html=True,
        )
        if tfg is None:
            st.markdown(
                f"<div style='background:#FEF3C7;border:1px dashed #FCD34D;"
                f"border-radius:10px;padding:1.1rem 1.05rem;font-size:0.88rem;"
                f"color:#92400E;text-align:center;line-height:1.5;"
                f"min-height:160px;display:flex;flex-direction:column;"
                f"justify-content:center;align-items:center;gap:0.4rem;'>"
                f"<div style='font-family:\"JetBrains Mono\",monospace;"
                f"font-size:0.72rem;letter-spacing:0.14em;font-weight:700;'>"
                f"PENDIENTE DE EJECUTAR</div>"
                f"<div>Lanza esta consulta en <b>Router adaptativo</b> "
                f"para capturar el resultado.</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        else:
            via_color = "#0EA5E9" if tfg.classification_via == "LLM" else "#14B8A6"
            with st.container(border=True):
                st.markdown(tfg.response)
            st.markdown(
                f"<div style='display:flex;gap:0.9rem;justify-content:center;"
                f"flex-wrap:wrap;"
                f"padding:0.45rem 0.7rem;margin-top:0.5rem;"
                f"background:rgba(15,23,42,0.04);border-radius:8px;"
                f"font-family:\"JetBrains Mono\",monospace;font-size:0.75rem;"
                f"color:#475569;'>"
                f"<span><b style='color:#0A1F3D;'>{tfg.word_count}</b> palabras</span>"
                f"<span><b style='color:#0A1F3D;'>{tfg.latency_s:.2f}s</b></span>"
                f"<span>Q&nbsp;<b style='color:#0A1F3D;'>{tfg.quality_score:.2f}</b></span>"
                f"<span style='color:{via_color};'>{tfg.classification_via}</span>"
                f"</div>"
                f"<div style='font-family:\"JetBrains Mono\",monospace;"
                f"font-size:0.68rem;color:#94A3B8;text-align:center;margin-top:0.4rem;'>"
                f"modelo: {tfg.model_name}</div>",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:1.4rem;'></div>", unsafe_allow_html=True)


def _render_level_section(level: str, queries: list[str], start_idx: int) -> None:
    """Sección por nivel: encabezado de color y cards de las consultas."""
    meta = _LEVEL_META[level]
    captured = sum(1 for q in queries if get_result_for(q) is not None)
    total = len(queries)

    st.markdown(
        f"<div style='margin:2rem 0 1.1rem 0;'>"
        f"<div style='display:flex;align-items:baseline;gap:0.9rem;"
        f"border-bottom:2px solid {meta['border']};padding-bottom:0.55rem;'>"
        f"<span style='font-family:\"JetBrains Mono\",monospace;"
        f"font-size:0.74rem;letter-spacing:0.16em;font-weight:700;"
        f"color:{meta['color']};'>SECCIÓN · {meta['icon']}</span>"
        f"<h2 style='font-family:Manrope,sans-serif;font-weight:700;"
        f"font-size:1.5rem;color:#0A1F3D;margin:0;letter-spacing:-0.01em;'>"
        f"{level}</h2>"
        f"<span style='font-family:\"JetBrains Mono\",monospace;font-size:0.72rem;"
        f"letter-spacing:0.1em;color:#64748B;margin-left:auto;'>"
        f"{captured} / {total} capturadas</span>"
        f"</div>"
        f"<div style='font-size:0.88rem;color:#64748B;margin-top:0.45rem;"
        f"font-style:italic;'>{meta['desc']}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    for i, q in enumerate(queries):
        _render_question_card(q, level, start_idx + i)


def render() -> None:
    page_header(
        number="06",
        page_name="Resultados obtenidos",
        title_html="Mixtral entrenado <em>vs</em> router adaptativo",
        lede=(
            "Comparación cara a cara sobre las 12 consultas del banco oficial. "
            "Las respuestas del paper están precargadas; las del TFG se capturan "
            "automáticamente al ejecutar la consulta en la vista Router adaptativo."
        ),
    )

    # === Aviso si falta el banco oficial (instalación pública sin material) ===
    if bank_size() == 0:
        st.markdown(
            "<div style='background:rgba(14,165,233,0.08);"
            "border:1px solid rgba(14,165,233,0.30);border-radius:12px;"
            "padding:0.95rem 1.2rem;margin-bottom:1.2rem;"
            "font-family:Manrope,sans-serif;font-size:0.92rem;color:#0C4A6E;"
            "line-height:1.55;'>"
            "<b>ℹ Las respuestas oficiales del paper no están cargadas.</b><br>"
            "Esta instalación pública no incluye <code>data/reference_responses.json</code> "
            "(material derivado del trabajo de Arnau-Muñoz et al., uso solo local con "
            "autorización académica). Los paneles de la columna izquierda mostrarán "
            "<i>«Material no incluido»</i>. Los paneles del TFG (derecha) funcionan "
            "normalmente al ejecutar consultas en la vista <b>Router adaptativo</b>."
            "</div>",
            unsafe_allow_html=True,
        )

    # === Banda de progreso ===
    all_queries = [q for level in EXAMPLE_QUERIES.values() for q in level]
    total = len(all_queries)
    captured = sum(1 for q in all_queries if get_result_for(q) is not None)
    _render_summary(total, captured)

    # === Secciones por nivel ===
    idx = 1
    for level in ("Básica", "Intermedia", "Avanzada", "Experta"):
        _render_level_section(level, EXAMPLE_QUERIES[level], idx)
        idx += len(EXAMPLE_QUERIES[level])

    # === Acción de mantenimiento ===
    if captured > 0:
        st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)
        with st.expander("Acciones de mantenimiento"):
            st.markdown(
                "Si quieres resetear los resultados del TFG capturados y "
                "volver a ejecutar las consultas desde cero:"
            )
            if st.button("Borrar todos los resultados capturados", type="secondary"):
                from ..results_store import _store_path
                import os
                p = _store_path()
                if os.path.exists(p):
                    os.remove(p)
                # Limpiar la caché del store
                get_all_results.cache_clear() if hasattr(get_all_results, "cache_clear") else None
                st.success("Resultados borrados. Recarga la página.")
                st.rerun()
