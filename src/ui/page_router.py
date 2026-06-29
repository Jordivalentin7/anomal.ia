"""Página 4 — Router adaptativo por complejidad.

Compara la respuesta con prompt genérico (baseline) frente a la respuesta con
prompt especializado seleccionado por el clasificador. Este es el mecanismo
propuesto para mitigar el valle de interferencia identificado en el estudio
de referencia.
"""
from __future__ import annotations

import streamlit as st

from ..results_store import save_result
from ..router import run_adaptive, run_baseline
from .common import (
    EXAMPLE_QUERIES,
    get_active_dataset_context,
    model_selector_chips,
    page_header,
    query_picker,
    render_prompt,
    render_response,
)


# Conjunto plano de las 12 consultas oficiales del banco de ejemplos.
# Se usa para detectar si una ejecución del router debe persistirse en el
# almacén de resultados que alimenta la vista "Resultados obtenidos".
_OFFICIAL_QUERIES: set[str] = {q.strip().lower() for level in EXAMPLE_QUERIES.values() for q in level}


def _is_official_query(query: str) -> tuple[bool, str | None]:
    """Devuelve (es_oficial, nivel) si la consulta está en EXAMPLE_QUERIES."""
    norm = query.strip().lower()
    for level, qs in EXAMPLE_QUERIES.items():
        for q in qs:
            if q.strip().lower() == norm:
                return True, level
    return False, None


def _left_column_title(baseline) -> str:
    """Etiqueta del panel izquierdo según el origen de la respuesta baseline."""
    if baseline.baseline_source == "reference":
        return "Mixtral entrenado · Arnau-Muñoz et al."
    return "Modo baseline (prompt genérico)"


def _render_response_metrics(outcome) -> None:
    """Muestra debajo de cada respuesta una banda compacta con palabras,
    latencia y puntuación del evaluador. Permite comparar visualmente las
    dos columnas sin tener que contar palabras a ojo.
    """
    if outcome.llm_response.error:
        return
    words = len(outcome.llm_response.content.split())
    latency = outcome.llm_response.latency_s
    quality = outcome.score.total
    st.markdown(
        f"<div style='display:flex;gap:1.2rem;justify-content:center;"
        f"padding:0.55rem 0.8rem;margin-top:0.4rem;"
        f"background:rgba(15,23,42,0.04);border-radius:8px;"
        f"font-family:\"JetBrains Mono\",monospace;font-size:0.78rem;"
        f"color:#475569;'>"
        f"<span><b style='color:#0A1F3D;'>{words}</b> palabras</span>"
        f"<span><b style='color:#0A1F3D;'>{latency:.2f}s</b></span>"
        f"<span>Q&nbsp;<b style='color:#0A1F3D;'>{quality:.2f}</b></span>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_arithmetic_warnings(outcome) -> None:
    """Si la verificación post-LLM detectó errores aritméticos, los muestra
    como chips de aviso debajo de la respuesta.
    """
    findings = outcome.arithmetic_findings or []
    if not findings:
        return
    parts = ["<div style='margin-top:0.5rem;'>"]
    for f in findings:
        parts.append(
            f"<div style='background:rgba(234,179,8,0.10);"
            f"border:1px solid rgba(234,179,8,0.40);border-radius:8px;"
            f"padding:0.55rem 0.85rem;margin-bottom:0.3rem;"
            f"font-family:Manrope,sans-serif;font-size:0.82rem;color:#713F12;'>"
            f"<b>⚠ Verificación aritmética:</b> "
            f"<code style='background:transparent;'>{f.expression}</code> "
            f"→ recálculo exacto <b>{f.computed:.4g}</b>, "
            f"la respuesta indica <b>{f.claimed:.4g}</b> "
            f"<span style='color:#A16207;'>(diferencia {f.rel_error_pct:.2f}%)</span>"
            f"</div>"
        )
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


@st.dialog("Resultado del router", width="large")
def _show_result_modal(baseline, adaptativo) -> None:
    """Modal centrado con animación que muestra ambas respuestas lado a lado."""
    _COL_TITLE = (
        "<div style='text-align:center;font-family:Manrope,sans-serif;"
        "font-weight:600;font-size:0.95rem;color:#0A1F3D;"
        "margin:0 0 0.6rem 0;'>{txt}</div>"
    )
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown(
            _COL_TITLE.format(txt=_left_column_title(baseline)),
            unsafe_allow_html=True,
        )
        if baseline.llm_response.error:
            st.error(baseline.llm_response.error)
        else:
            render_response(baseline.llm_response.content)
    with col_r:
        st.markdown(
            _COL_TITLE.format(txt="Router adaptativo · TFG"),
            unsafe_allow_html=True,
        )
        if adaptativo.llm_response.error:
            st.error(adaptativo.llm_response.error)
        else:
            render_response(adaptativo.llm_response.content)


def _render_results(baseline, adaptativo) -> None:
    """Pinta las dos columnas con las respuestas. Reutilizable para resultado fresco o cacheado."""
    _COL_TITLE = (
        "<div style='text-align:center;font-family:Manrope,sans-serif;"
        "font-weight:600;font-size:1rem;color:#0A1F3D;"
        "margin:0 0 0.6rem 0;'>{txt}</div>"
    )
    col_l, col_r = st.columns(2)

    # Si la respuesta de la izquierda es del modelo entrenado del paper,
    # mostramos un sub-rótulo aclarativo encima.
    left_title = _left_column_title(baseline)
    right_title = (
        "Router adaptativo · TFG"
        if baseline.baseline_source == "reference"
        else "Modo adaptativo (prompt por nivel)"
    )

    with col_l:
        st.markdown(_COL_TITLE.format(txt=left_title), unsafe_allow_html=True)
        if baseline.baseline_source == "reference":
            st.caption(
                "Respuesta literal del Mixtral 8x7B fine-tuneado (variante "
                "ultra_expert, 7.530 ejemplos) del banco oficial."
            )
        if baseline.llm_response.error:
            st.error(baseline.llm_response.error)
        else:
            render_response(baseline.llm_response.content)
            _render_response_metrics(baseline)
            _render_arithmetic_warnings(baseline)

    with col_r:
        st.markdown(_COL_TITLE.format(txt=right_title), unsafe_allow_html=True)
        if baseline.baseline_source == "reference":
            st.caption(
                f"Generada en vivo por {adaptativo.llm_response.model} "
                "con el prompt especializado del nivel detectado."
            )
        if adaptativo.llm_response.error:
            st.error(adaptativo.llm_response.error)
        else:
            render_response(adaptativo.llm_response.content)
            _render_response_metrics(adaptativo)
            _render_arithmetic_warnings(adaptativo)


def render() -> None:
    page_header(
        number="04",
        page_name="Router adaptativo",
        title_html="Baseline vs <em>prompt adaptado</em> al nivel",
        lede="Compara la respuesta genérica con la adaptada al nivel de la consulta.",
    )

    # CSS local: pega el contenido al título y aumenta espacio label↔widget
    st.markdown(
        """
        <style>
        .caudal-page-head { margin-bottom: 0.2rem !important; }
        [data-testid="stMain"] [data-testid="stSelectbox"] label,
        [data-testid="stMain"] [data-testid="stTextArea"] label {
            margin-bottom: 0.7rem !important;
        }
        [data-testid="stMain"] [data-testid="stSelectbox"] label p,
        [data-testid="stMain"] [data-testid="stTextArea"] label p {
            margin-bottom: 0.7rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Si la Comparativa dejó un ganador, lo pre-seleccionamos la primera vez
    # que el operador entra al Router con esa recomendación. Si después cambia
    # manualmente el modelo, su elección se respeta hasta que llegue una
    # recomendación nueva.
    recommended = st.session_state.get("recommended_model_name")
    applied_key = "router_applied_recommendation"
    if recommended and st.session_state.get(applied_key) != recommended:
        st.session_state["router_model_chips_selected"] = recommended
        st.session_state[applied_key] = recommended

    if recommended:
        st.markdown(
            f"<div style='background:rgba(20,184,166,0.08);"
            f"border:1px solid rgba(20,184,166,0.35);border-radius:10px;"
            f"padding:0.55rem 0.95rem;margin-bottom:0.85rem;"
            f"font-family:Manrope,sans-serif;color:#0F766E;font-size:0.88rem;"
            f"display:flex;align-items:center;gap:0.5rem;'>"
            f"<span style='font-family:\"JetBrains Mono\",monospace;"
            f"font-size:0.72rem;letter-spacing:0.14em;font-weight:700;"
            f"color:#14B8A6;'>RECOMENDADO POR LA COMPARATIVA</span>"
            f"<span style='color:#0A1F3D;font-weight:600;'>{recommended}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    model = model_selector_chips(label="1. Modelo", key="router_model_chips")
    if model is None:
        return

    # Margen mínimo entre paso 1 y pasos 2/3
    st.markdown("<div style='height:0.2rem'></div>", unsafe_allow_html=True)

    # Si hay un resultado previo cacheado y el textarea está vacío, lo poblamos
    # con la consulta ejecutada para que el operador vea a qué query corresponde
    # el análisis mostrado abajo.
    _last_cached = st.session_state.get("router_last_result")
    _text_key = "router_query_text"
    if _last_cached and not st.session_state.get(_text_key, "").strip():
        st.session_state[_text_key] = _last_cached["query"]
        st.session_state.setdefault("router_level", "Escribir manualmente")
        st.session_state["router_last_default"] = ""

    query, lanzar = query_picker(
        key_prefix="router",
        horizontal=True,
        label="3. Consulta del operador",
        level_label="2. Nivel de complejidad",
        inline_button_label="Ejecutar ambos modos",
    )
    payload = ""

    if lanzar and query.strip():
        ds_context = get_active_dataset_context()
        with st.spinner("Ejecutando modos baseline y adaptativo…"):
            baseline = run_baseline(query, payload, model, dataset_context=ds_context)
            adaptativo = run_adaptive(query, payload, model, dataset_context=ds_context)
        st.session_state["router_last_result"] = {
            "query": query,
            "model_name": model.display_name,
            "dataset_label": st.session_state.get("scada_active", "—"),
            "baseline": baseline,
            "adaptativo": adaptativo,
        }
        st.session_state["router_show_modal"] = True

        # Si la consulta forma parte del banco oficial de ejemplos, persistir
        # el resultado del modo adaptativo para alimentar "Resultados obtenidos".
        is_official, level = _is_official_query(query)
        if is_official and not adaptativo.llm_response.error:
            via = (
                "LLM"
                if any(r.startswith("[LLM") for r in adaptativo.classification.reasons)
                else "Heurística"
            )
            try:
                save_result(
                    query=query,
                    level=level or adaptativo.classification.level,
                    model_name=model.display_name,
                    response=adaptativo.llm_response.content,
                    latency_s=adaptativo.llm_response.latency_s,
                    quality_score=adaptativo.score.total,
                    classification_level=adaptativo.classification.level,
                    classification_confidence=adaptativo.classification.score,
                    classification_via=via,
                    arithmetic_findings_count=len(adaptativo.arithmetic_findings or []),
                )
                st.session_state["_router_just_saved"] = True
            except Exception:  # noqa: BLE001
                # Si falla el guardado, no rompemos la ejecución del router.
                st.session_state["_router_just_saved"] = False

    last = st.session_state.get("router_last_result")
    if last is None:
        return

    # Modal centrado con animación si se acaba de ejecutar
    if st.session_state.get("router_show_modal"):
        _show_result_modal(last["baseline"], last["adaptativo"])
        st.session_state["router_show_modal"] = False

    # Aviso de guardado para "Resultados obtenidos" (visible una sola vez)
    if st.session_state.pop("_router_just_saved", False):
        st.markdown(
            "<div style='background:rgba(20,184,166,0.10);"
            "border:1px solid rgba(20,184,166,0.40);border-radius:10px;"
            "padding:0.6rem 0.95rem;margin-bottom:0.8rem;"
            "font-family:Manrope,sans-serif;font-size:0.86rem;color:#0F766E;'>"
            "✓ Resultado capturado en <b>Resultados obtenidos</b>."
            "</div>",
            unsafe_allow_html=True,
        )

    # Botón para reabrir el modal del resultado en cualquier momento
    _, col_btn = st.columns([4, 1])
    with col_btn:
        if st.button(
            "⛶  Ver resultados",
            key="router_reopen_modal",
            use_container_width=True,
            help="Mostrar las dos respuestas centradas con backdrop",
        ):
            st.session_state["router_show_modal"] = True
            st.rerun()

    _render_results(
        baseline=last["baseline"],
        adaptativo=last["adaptativo"],
    )

    # Separación visual entre la banda de métricas y el expander de detalles
    st.markdown("<div style='height:1.8rem;'></div>", unsafe_allow_html=True)

    with st.expander("Detalles del cálculo"):
        classification = last["adaptativo"].classification
        st.markdown("**Clasificación de la consulta**")
        st.markdown(
            f"Nivel detectado: **{classification.level}** · confianza "
            f"{classification.score}"
        )
        for r in classification.reasons:
            st.caption("· " + r)

        st.markdown("**Prompt aplicado · Modo adaptativo**")
        render_prompt(last["adaptativo"].system_prompt)
        st.markdown("**Prompt aplicado · Modo baseline**")
        render_prompt(last["baseline"].system_prompt)
