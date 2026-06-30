"""Página 3 — Comparativa entre modelos."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pandas as pd
import streamlit as st

from ..classifier import classify
from ..config import ModelSpec
from ..evaluation import EvalScore, evaluate
from ..prompts import prompt_for
from ..providers import LLMResponse, call_model
from .common import (
    get_active_dataset_context,
    multi_model_selector,
    page_header,
    query_picker,
    render_prompt,
    render_response,
)


# Pesos del indicador global. La suma debe ser 1.0.
#   Calidad (55 %)  — la respuesta debe ser técnicamente correcta y adecuada al nivel.
#   Velocidad (30 %) — criterio operativo: el operador SCADA necesita respuestas rápidas.
#   Concisión (15 %) — a igual calidad, menos palabras reduce la carga de lectura.
INDICATOR_WEIGHTS = {
    "calidad": 0.55,
    "velocidad": 0.30,
    "concision": 0.15,
}


@dataclass
class ModelRun:
    model: ModelSpec
    response: LLMResponse
    score: EvalScore


@dataclass
class IndicatorRow:
    model_name: str
    quality: float
    speed: float
    concision: float
    global_score: float
    latency: float
    words: int


def _compute_indicators(runs: List[ModelRun]) -> List[IndicatorRow]:
    """Normaliza métricas entre modelos y calcula el indicador global.

    Velocidad y concisión se normalizan por el mínimo observado entre los
    modelos comparados, de modo que el mejor de cada dimensión obtiene 1.0.
    """
    valid = [r for r in runs if not r.response.error and r.response.content]
    if not valid:
        return []

    min_latency = min(r.response.latency_s for r in valid) or 1e-6
    min_words = min(len(r.response.content.split()) for r in valid) or 1

    rows: List[IndicatorRow] = []
    for r in valid:
        words = len(r.response.content.split())
        quality = r.score.total
        speed = min_latency / r.response.latency_s if r.response.latency_s else 0.0
        concision = min_words / words if words else 0.0
        global_score = (
            INDICATOR_WEIGHTS["calidad"] * quality
            + INDICATOR_WEIGHTS["velocidad"] * speed
            + INDICATOR_WEIGHTS["concision"] * concision
        )
        rows.append(
            IndicatorRow(
                model_name=r.model.display_name,
                quality=round(quality, 3),
                speed=round(speed, 3),
                concision=round(concision, 3),
                global_score=round(global_score, 3),
                latency=round(r.response.latency_s, 2),
                words=words,
            )
        )
    rows.sort(key=lambda x: x.global_score, reverse=True)
    return rows


def _render_indicator_formula() -> None:
    st.markdown(
        "El indicador global **I** combina tres dimensiones normalizadas en "
        "el rango [0, 1], donde **1.0** representa el mejor valor observado "
        "entre los modelos comparados:"
    )
    st.latex(
        r"I \;=\; 0{,}55 \cdot Q \;+\; 0{,}30 \cdot V \;+\; 0{,}15 \cdot C"
    )
    st.markdown(
        "- **Q · Calidad** *(55 %)* — puntuación total del evaluador "
        "(palabras clave, unidades, pertinencia técnica, cálculo y "
        "adecuación de longitud al nivel detectado).\n"
        "- **V · Velocidad** *(30 %)* — `latencia_mín / latencia_modelo`. "
        "El modelo más rápido obtiene 1.0.\n"
        "- **C · Concisión** *(15 %)* — `palabras_mín / palabras_modelo`. "
        "La respuesta más breve obtiene 1.0."
    )


@st.dialog("Resultado de la comparativa", width="large")
def _show_result_modal(rows: List[IndicatorRow]) -> None:
    """Modal centrado con animación que muestra el modelo recomendado."""
    if not rows:
        st.warning("No hay respuestas válidas para mostrar.")
        return
    winner = rows[0]
    st.markdown(
        f"<div style='text-align:center;padding:0.5rem 0 1rem 0;'>"
        f"<div style='font-family:\"JetBrains Mono\",monospace;font-size:0.78rem;"
        f"letter-spacing:0.16em;color:#14B8A6;font-weight:700;"
        f"margin-bottom:0.5rem;'>MODELO RECOMENDADO</div>"
        f"<div style='font-family:Manrope,sans-serif;font-weight:700;"
        f"font-size:2rem;color:#0A1F3D;letter-spacing:-0.02em;"
        f"margin-bottom:0.6rem;'>{winner.model_name}</div>"
        f"<div style='display:flex;justify-content:center;gap:1.5rem;"
        f"font-family:Manrope,sans-serif;color:#475569;font-size:0.95rem;'>"
        f"<span><b style='color:#0F766E;'>I</b> = {winner.global_score:.3f}</span>"
        f"<span>Calidad {winner.quality:.2f}</span>"
        f"<span>Velocidad {winner.speed:.2f}</span>"
        f"<span>Concisión {winner.concision:.2f}</span>"
        f"</div></div>",
        unsafe_allow_html=True,
    )


def _render_winner_and_ranking(rows: List[IndicatorRow]) -> None:
    if not rows:
        st.warning("No hay respuestas válidas para calcular el indicador.")
        return

    winner = rows[0]
    st.markdown(
        f"<div class='tfg-card' style='border-left:4px solid var(--c-teal-500);"
        f"padding:1.1rem 1.3rem;'>"
        f"<div style='font-size:0.78rem;letter-spacing:0.08em;"
        f"text-transform:uppercase;color:var(--c-gray-500);font-weight:600;'>"
        f"Modelo recomendado</div>"
        f"<div style='font-size:1.4rem;font-weight:700;color:var(--c-navy-900);"
        f"margin-top:0.25rem;'>{winner.model_name}</div>"
        f"<div style='color:var(--c-gray-600);margin-top:0.4rem;'>"
        f"Indicador global <b>{winner.global_score:.3f}</b> · "
        f"Calidad {winner.quality:.2f} · "
        f"Velocidad {winner.speed:.2f} · "
        f"Concisión {winner.concision:.2f}"
        f"</div></div>",
        unsafe_allow_html=True,
    )

    # (Tabla de ranking eliminada — el modelo recomendado se muestra en la tarjeta superior;
    # las respuestas individuales aparecen abajo en "Análisis por modelo".)


def _render_per_model_breakdown(rows: List[IndicatorRow]) -> None:
    """Tabla con los valores de cada modelo que entran al indicador global.

    Permite trazar por qué se elige un modelo: dos modelos con la misma I
    pueden diferir en velocidad o concisión, y aquí se ve.
    """
    if not rows:
        return

    df = pd.DataFrame(
        [
            {
                "Modelo": r.model_name,
                "Calidad (Q)": r.quality,
                "Velocidad (V)": r.speed,
                "Concisión (C)": r.concision,
                "Indicador (I)": r.global_score,
            }
            for r in rows
        ]
    )

    def _highlight_winner(row: pd.Series) -> List[str]:
        if row.name == 0:
            return [
                "background-color: rgba(20, 184, 166, 0.12); font-weight: 600;"
            ] * len(row)
        return [""] * len(row)

    styled = df.style.apply(_highlight_winner, axis=1).format(
        {
            "Calidad (Q)": "{:.3f}",
            "Velocidad (V)": "{:.3f}",
            "Concisión (C)": "{:.3f}",
            "Indicador (I)": "{:.3f}",
        }
    )

    st.dataframe(styled, use_container_width=True, hide_index=True)


def _render_quality_breakdown(runs: List[ModelRun], indicators: List[IndicatorRow]) -> None:
    """Tabla con el desglose de las 5 dimensiones de Q por modelo.

    Permite ver con qué componentes se ha construido la nota de calidad de
    cada modelo: palabras clave, unidades, indicador técnico, cálculo y
    longitud. Útil para entender por qué un modelo gana en Q sobre otro.
    """
    if not runs:
        return

    # Indexamos los indicadores para recuperar la Q total por nombre
    q_total = {ind.model_name: ind.quality for ind in indicators}

    df = pd.DataFrame(
        [
            {
                "Modelo": run.model.display_name,
                "Palabras clave (K)": run.score.keywords,
                "Unidades (U)": run.score.units,
                "Indicador técnico (T)": run.score.technical,
                "Cálculo (Cálc)": run.score.calculation,
                "Longitud (L)": run.score.length,
                "Calidad (Q)": q_total.get(run.model.display_name, run.score.total),
            }
            for run in runs
            if not run.response.error
        ]
    )
    if df.empty:
        return

    # Ordenamos por Q descendente para que el mejor quede arriba
    df = df.sort_values("Calidad (Q)", ascending=False).reset_index(drop=True)

    def _highlight_winner(row: pd.Series) -> List[str]:
        if row.name == 0:
            return [
                "background-color: rgba(20, 184, 166, 0.12); font-weight: 600;"
            ] * len(row)
        return [""] * len(row)

    styled = df.style.apply(_highlight_winner, axis=1).format(
        {
            "Palabras clave (K)": "{:.2f}",
            "Unidades (U)": "{:.2f}",
            "Indicador técnico (T)": "{:.2f}",
            "Cálculo (Cálc)": "{:.2f}",
            "Longitud (L)": "{:.2f}",
            "Calidad (Q)": "{:.3f}",
        }
    )

    st.dataframe(styled, use_container_width=True, hide_index=True)


def _render_model_cards(runs: List[ModelRun], indicators: List[IndicatorRow]) -> None:
    idx = {r.model_name: r for r in indicators}
    for run in runs:
        name = run.model.display_name
        ind = idx.get(name)
        header = f"**{name}**"
        if ind is not None:
            header += f" · I = {ind.global_score:.3f}"
        elif run.response.error:
            header += " · error"
        with st.expander(header):
            if run.response.error:
                st.error(run.response.error)
                continue
            c1, c2, c3 = st.columns(3)
            c1.metric("Latencia", f"{run.response.latency_s:.2f} s")
            c2.metric("Palabras", len(run.response.content.split()))
            c3.metric("Puntuación", f"{run.score.total:.2f}")
            render_response(run.response.content)


def render() -> None:
    page_header(
        number="03",
        page_name="Comparativa de modelos",
        title_html="Misma consulta, <em>varios LLM</em>",
        lede="Lanza la pregunta a varios LLM y observa el modelo recomendado.",
    )

    # CSS local: pega el contenido al título y aumenta espacio label↔widget en cada paso
    st.markdown(
        """
        <style>
        /* Sube el contenido pegándolo al título "Misma consulta, varios LLM" */
        .caudal-page-head { margin-bottom: 0.2rem !important; }
        /* Etiqueta del multi-model selector (paso 1) */
        .st-key-compare_models + div [class*="st-key-mmchip-"] { margin-top: 0; }
        /* Más aire entre los labels nativos de Streamlit y sus widgets */
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

    models = multi_model_selector(label="1. Modelos a comparar", key="compare_models")
    if not models:
        return

    # Margen mínimo entre paso 1 y pasos 2/3
    st.markdown("<div style='height:0.2rem'></div>", unsafe_allow_html=True)

    # Si hay un resultado previo cacheado y el textarea está vacío, lo poblamos
    # con la consulta ejecutada para que el operador vea a qué query corresponde
    # el análisis mostrado abajo.
    _last_cached = st.session_state.get("compare_last_result")
    _text_key = "compare_query_text"
    if _last_cached and not st.session_state.get(_text_key, "").strip():
        st.session_state[_text_key] = _last_cached["query"]
        st.session_state.setdefault("compare_level", "Escribir manualmente")
        st.session_state["compare_last_default"] = ""

    query, lanzar = query_picker(
        key_prefix="compare",
        horizontal=True,
        label="3. Consulta del operador",
        level_label="2. Nivel de complejidad",
        inline_button_label="Ejecutar comparativa",
    )

    if lanzar and query.strip():
        classification = classify(query)
        base_prompt = prompt_for(classification.level)
        ds_context = get_active_dataset_context()
        prompt = f"{base_prompt}\n\n{ds_context}" if ds_context else base_prompt

        runs: List[ModelRun] = []
        user_prompt = f"Consulta del operador: {query}"
        with st.spinner("Consultando modelos…"):
            for model in models:
                resp = call_model(model, prompt, user_prompt)
                score = evaluate(resp.content, classification.level)
                runs.append(ModelRun(model=model, response=resp, score=score))

        # Persistimos la última ejecución
        st.session_state["compare_last_result"] = {
            "query": query,
            "classification": classification,
            "prompt": prompt,
            "runs": runs,
            "models_label": ", ".join(m.display_name for m in models),
            "dataset_label": st.session_state.get("scada_active", "—"),
        }
        # Guardar el modelo ganador para que el Router lo pre-seleccione
        winner_rows = _compute_indicators(runs)
        if winner_rows:
            st.session_state["recommended_model_name"] = winner_rows[0].model_name
        # Activar modal con el resultado
        st.session_state["compare_show_modal"] = True

    last = st.session_state.get("compare_last_result")
    if last is None:
        return

    # Mostrar modal con animación si se acaba de ejecutar
    if st.session_state.get("compare_show_modal"):
        _show_result_modal(_compute_indicators(last["runs"]))
        st.session_state["compare_show_modal"] = False

    indicator_rows = _compute_indicators(last["runs"])

    _render_winner_and_ranking(indicator_rows)

    st.markdown(
        "<div style='font-family:Manrope,sans-serif;font-weight:600;"
        "color:#0A1F3D;margin:1.2rem 0 0.5rem 0;font-size:0.95rem;'>"
        "Valores por modelo</div>",
        unsafe_allow_html=True,
    )
    _render_per_model_breakdown(indicator_rows)

    with st.expander("Detalles del cálculo"):
        st.markdown("**Fórmula del indicador global**")
        _render_indicator_formula()

        st.markdown("**Desglose de Q por modelo**")
        st.caption(
            "Cada valor de Q es la media ponderada de cinco componentes "
            "(palabras clave, unidades, indicador técnico, cálculo y longitud) "
            "con pesos adaptados al nivel detectado."
        )
        _render_quality_breakdown(last["runs"], indicator_rows)

        st.markdown("**Clasificación de la consulta**")
        st.markdown(
            f"Nivel detectado: **{last['classification'].level}** · confianza "
            f"{last['classification'].score}"
        )
        for r in last["classification"].reasons:
            st.caption("· " + r)

        st.markdown("**Prompt del sistema aplicado**")
        render_prompt(last["prompt"])
