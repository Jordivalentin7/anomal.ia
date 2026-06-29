"""Componentes auxiliares reutilizables de la interfaz."""
from __future__ import annotations

from contextlib import nullcontext
from typing import Callable, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st

from ..config import MODEL_CATALOG, ModelSpec
from ..providers import available_providers
from ..scada import dataset_context, load_dataset


SCADA_DEFAULT_KEY = "Por defecto · dataset_evaluacion.csv"


def get_active_dataset() -> Tuple[str, Optional[pd.DataFrame]]:
    """Devuelve (nombre, DataFrame) del dataset activo guardado en session_state.

    Si no hay nada activo, devuelve el dataset por defecto.
    """
    name = st.session_state.get("scada_active", SCADA_DEFAULT_KEY)
    uploaded = st.session_state.get("scada_uploaded", {})

    if name in uploaded:
        return name, uploaded[name]
    try:
        return SCADA_DEFAULT_KEY, load_dataset()
    except Exception:  # noqa: BLE001
        return SCADA_DEFAULT_KEY, None


def get_active_dataset_context() -> str:
    """Texto descriptivo del dataset activo, listo para inyectar en un prompt LLM."""
    name, df = get_active_dataset()
    if df is None:
        return ""
    return dataset_context(df, label=name)


# Banco de consultas de ejemplo tomadas literalmente del banco oficial de
# evaluación del proyecto Mixtral Water Management (Arnau-Muñoz et al.).
# Selección de 3 consultas por nivel de complejidad.
EXAMPLE_QUERIES: Dict[str, List[str]] = {
    "Básica": [
        "¿Cómo evalúo agua con pH 7.2?",
        "¿Es seguro cloro residual de 0.3 mg/L?",
        "¿Es normal presión de 35 bar?",
    ],
    "Intermedia": [
        "¿Los nitratos de 28 mg/L son aceptables?",
        "¿El agua con pH 7.2, cloro 0.4 mg/L, nitratos 28 mg/L cumple RD 140/2003?",
        "¿Factor de potencia 0.78 es aceptable?",
    ],
    "Avanzada": [
        "¿Cuál es la eficiencia de un pozo con 45 kW produciendo 180 L/min?",
        "Si entrada es 300 L/min y salida 280 L/min, ¿cuál es el balance?",
        "Compara Falconera (45kW, 180L/min) vs Beniopa (50kW, 175L/min)",
    ],
    "Experta": [
        "Con potencia 45 kW y factor potencia 0.78, ¿cuál es la potencia reactiva?",
        "Tengo 3 pozos: Falconera (45kW, 180L/min), Beniopa (50kW, 175L/min), Llombart (40kW, 140L/min). ¿En qué orden activo?",
        "El pozo consume 45 kW pero solo produce 120 L/min. ¿Qué pasa?",
    ],
}


def query_picker(
    key_prefix: str,
    default_height: int = 110,
    label: str = "Consulta del operador",
    level_label: str = "Nivel de complejidad",
    example_label: str = "Consulta de ejemplo",
    horizontal: bool = False,
    inline_button_label: Optional[str] = None,
    inline_extra: Optional[Callable[[], None]] = None,
):
    """Selector en cascada (nivel → ejemplo) con campo de texto editable.

    Si `inline_button_label` se proporciona, también renderiza un botón a la
    derecha del textarea y devuelve la tupla (query, clicked). Si no, devuelve
    solo la query (str) — comportamiento legacy.
    """
    levels = ["Escribir manualmente"] + list(EXAMPLE_QUERIES.keys())

    # Borde suave teal alrededor de toda la sección de consulta
    section_key = f"{key_prefix}_query_section"
    st.markdown(
        f"""
        <style>
        .st-key-{section_key} {{
            border: 1px solid rgba(20, 184, 166, 0.35);
            border-radius: 14px;
            padding: 1.1rem 1.3rem 1.2rem 1.3rem;
            background: rgba(20, 184, 166, 0.03);
            margin-bottom: 0.4rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    section_ctx = st.container(key=section_key)

    if horizontal:
        with section_ctx:
            col_left, col_right = st.columns(
                [2, 3], gap="medium", vertical_alignment="top"
            )
    else:
        col_left = section_ctx
        col_right = section_ctx

    # Izquierda: nivel (más estrecho via sub-columna) + textarea (+botón) debajo
    with col_left:
        if horizontal:
            sub_level, _ = st.columns([4, 1], gap="small")
            with sub_level:
                level = st.selectbox(
                    level_label,
                    levels,
                    key=f"{key_prefix}_level",
                )
        else:
            level = st.selectbox(
                level_label,
                levels,
                key=f"{key_prefix}_level",
            )

    # Derecha: consulta de ejemplo. Para garantizar que el botón NO se mueva,
    # renderizamos siempre un selectbox real (placeholder deshabilitado cuando
    # el nivel es "Escribir manualmente"). Así el alto exacto coincide.
    desired_default = ""
    if level != "Escribir manualmente":
        examples = EXAMPLE_QUERIES[level]
        with col_right:
            selected = st.selectbox(
                example_label,
                examples,
                key=f"{key_prefix}_example",
            )
        desired_default = selected
    elif horizontal:
        with col_right:
            st.selectbox(
                example_label,
                options=["—"],
                disabled=True,
                key=f"{key_prefix}_example_placeholder",
            )

    marker_key = f"{key_prefix}_last_default"
    text_key = f"{key_prefix}_query_text"
    if st.session_state.get(marker_key) != desired_default:
        st.session_state[text_key] = desired_default
        st.session_state[marker_key] = desired_default

    with col_left:
        # Margen vertical entre el dropdown de nivel y el textarea
        st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)
        query_value = st.text_area(label, key=text_key, height=default_height)

    if inline_button_label:
        with col_right:
            # Espaciador grande para bajar el botón a la altura del textarea
            st.markdown(
                "<div style='height:70px;'></div>", unsafe_allow_html=True
            )
            # Botón pegado al borde derecho de la columna
            _, btn_col = st.columns([3, 2], gap="small")
            with btn_col:
                clicked = st.button(
                    inline_button_label,
                    key=f"{key_prefix}_inline_btn",
                    type="primary",
                    use_container_width=True,
                )
        return query_value, clicked
    return query_value


def page_header(
    number: str,
    page_name: str,
    title_html: str,
    lede: str = "",
    is_hero: bool = False,
) -> None:
    """Cabecera editorial de 3 niveles: breadcrumb + kicker + título + lede.

    Args:
        number: número de sección en 2 dígitos ("01", "02", ...).
        page_name: nombre largo de la página (aparece en breadcrumb y kicker).
        title_html: título real de la página; admite <em>...</em> para énfasis.
        lede: párrafo introductorio opcional.
        is_hero: True para la portada (H1 64px); False para páginas internas (H2 32px).
    """
    page_upper = page_name.upper()
    tag = "h1" if is_hero else "h2"
    head_class = "caudal-page-head caudal-page-head-hero" if is_hero else "caudal-page-head"
    title_class = (
        "caudal-page-title caudal-page-title-hero" if is_hero else "caudal-page-title"
    )
    lede_class = "caudal-lede caudal-lede-hero" if is_hero else "caudal-lede"

    parts = [f"<section class='{head_class}'>"]
    parts.append(f"<{tag} class='{title_class}'>{title_html}</{tag}>")
    if lede:
        parts.append(f"<p class='{lede_class}'>{lede}</p>")
    parts.append("</section>")

    st.markdown("".join(parts), unsafe_allow_html=True)


def section_header(number: str, title: str, caption: str = "") -> None:
    num_clean = number.rstrip(".")
    header_html = (
        "<div class='caudal-section-head'>"
        f"<span class='caudal-section-num'>SEC · {num_clean}</span>"
        f"<h1 class='caudal-section-title'>{title}</h1>"
        "</div>"
    )
    st.markdown(header_html, unsafe_allow_html=True)
    if caption:
        st.markdown(f"<div class='tfg-caption'>{caption}</div>", unsafe_allow_html=True)


def tag(label: str, variant: str = "") -> str:
    klass = "tfg-tag"
    if variant == "alert":
        klass += " tfg-tag-alert"
    elif variant == "ok":
        klass += " tfg-tag-ok"
    return f"<span class='{klass}'>{label}</span>"


def render_response(content: str) -> None:
    if not content:
        st.info("Respuesta vacía.")
        return
    # Usamos un contenedor con borde y dejamos que st.markdown renderice
    # el contenido nativamente. Así los **bold**, listas y enlaces salen
    # bien formados en lugar de mostrarse como texto crudo con asteriscos.
    with st.container(border=True):
        st.markdown(content)


def render_prompt(prompt: str) -> None:
    st.markdown(
        f"<div class='tfg-card-muted'>{prompt}</div>",
        unsafe_allow_html=True,
    )


def available_models() -> list[ModelSpec]:
    provs = set(available_providers())
    return [m for m in MODEL_CATALOG if m.provider in provs]


def model_selector_chips(
    label: str = "Modelo",
    key: str = "model_selector_chips",
) -> Optional[ModelSpec]:
    """Selector de un único modelo como tarjetas-chip (mismo estilo que multi).

    Solo una tarjeta puede estar activa simultáneamente (radio behavior).
    """
    models = available_models()
    if not models:
        st.warning(
            "No hay proveedores configurados. Defina MISTRAL_API_KEY o "
            "GROQ_API_KEY en el archivo .env."
        )
        return None

    state_key = f"{key}_selected"
    if state_key not in st.session_state:
        st.session_state[state_key] = models[0].display_name

    selected_name: str = st.session_state[state_key]

    # CSS base para los chips (mismo estilo que multi_model_selector)
    st.markdown(
        """
        <style>
        [class*="st-key-mschip-"] button {
            border-radius: 12px !important;
            padding: 0.6rem 0.9rem !important;
            height: 68px !important;
            min-height: 68px !important;
            background: #F1F5F9 !important;
            color: #64748B !important;
            border: 1px solid #E2E8F0 !important;
            transition: all 0.15s ease !important;
            box-shadow: none !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
        }
        [class*="st-key-mschip-"] button:hover {
            border-color: #14B8A6 !important;
            color: #0F766E !important;
            background: #F0FDFA !important;
            transform: translateY(-1px);
        }
        [class*="st-key-mschip-"] button p {
            margin: 0 !important;
            text-align: center !important;
            line-height: 1.2 !important;
        }
        [class*="st-key-mschip-"] button p:nth-of-type(1) {
            font-size: 0.9rem !important;
            font-weight: 600 !important;
        }
        [class*="st-key-mschip-"] button p:nth-of-type(2) {
            font-size: 0.7rem !important;
            font-weight: 400 !important;
            opacity: 0.7;
            margin-top: 0.2rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # CSS dinámico: estilo activo (teal) para la tarjeta seleccionada
    active_rules = []
    for i, model in enumerate(models):
        if model.display_name == selected_name:
            active_rules.append(
                f".st-key-mschip-{i} button, "
                f".st-key-mschip-{i} button:hover, "
                f".st-key-mschip-{i} button:focus, "
                f".st-key-mschip-{i} button:active "
                "{ background: #14B8A6 !important; color: #FFFFFF !important; "
                "border-color: #0F766E !important; "
                "box-shadow: 0 2px 8px rgba(20, 184, 166, 0.25) !important; }"
                f".st-key-mschip-{i} button p {{ color: #FFFFFF !important; }}"
            )
    if active_rules:
        st.markdown(
            "<style>" + "\n".join(active_rules) + "</style>",
            unsafe_allow_html=True,
        )

    if label:
        st.markdown(
            f"<div style='font-size:0.88rem;color:#475569;"
            f"margin-bottom:0.7rem;font-weight:500;'>{label}</div>",
            unsafe_allow_html=True,
        )

    def _select(name: str) -> None:
        st.session_state[state_key] = name

    cols = st.columns(len(models))
    for i, model in enumerate(models):
        name, company = _model_label_parts(model)
        is_active = model.display_name == selected_name
        icon = "✓" if is_active else "✕"
        with cols[i]:
            st.button(
                f"{icon}  {name}\n\n{company}",
                key=f"mschip-{i}",
                on_click=_select,
                args=(model.display_name,),
                use_container_width=True,
            )

    for m in models:
        if m.display_name == selected_name:
            return m
    return models[0]


def model_selector(
    label: str = "Modelo",
    key: str = "model_selector",
    default: str | None = None,
) -> ModelSpec | None:
    models = available_models()
    if not models:
        st.warning(
            "No hay proveedores configurados. Defina MISTRAL_API_KEY o "
            "GROQ_API_KEY en el archivo .env."
        )
        return None
    names = [m.display_name for m in models]
    idx = names.index(default) if default in names else 0
    choice = st.selectbox(label, names, index=idx, key=key)
    return next(m for m in models if m.display_name == choice)


_PROVIDER_COMPANY = {
    "mistral": "Mistral AI",
    "groq": "Groq",
}


def _model_label_parts(model: ModelSpec) -> Tuple[str, str]:
    """Devuelve (nombre limpio, empresa/origen) para mostrar en el chip."""
    company = _PROVIDER_COMPANY.get(model.provider, model.provider.title())
    name = model.display_name
    if "(" in name:
        # "Mixtral 8x7B (Mistral AI)" → "Mixtral 8x7B"
        name = name.split("(")[0].strip()
    return name, company


def multi_model_selector(
    label: str = "Modelos a comparar",
    key: str = "multi_model_selector",
) -> list[ModelSpec]:
    """Selector multi-modelo como tarjetas-chip toggleables del mismo tamaño.

    Cada chip muestra el nombre del modelo (arriba) y su empresa (abajo).
    Inactivo: gris con ✕. Activo: teal con ✓. Mejor UX que un dropdown.
    """
    models = available_models()
    if not models:
        st.warning(
            "No hay proveedores configurados. Defina MISTRAL_API_KEY o "
            "GROQ_API_KEY en el archivo .env."
        )
        return []

    state_key = f"{key}_selected"
    if state_key not in st.session_state:
        st.session_state[state_key] = set(
            m.display_name for m in models[: min(2, len(models))]
        )

    selected: set[str] = st.session_state[state_key]

    # CSS base para las tarjetas-chip (estado inactivo, mismo tamaño todas)
    st.markdown(
        """
        <style>
        [class*="st-key-mmchip-"] button {
            border-radius: 12px !important;
            padding: 0.6rem 0.9rem !important;
            height: 68px !important;
            min-height: 68px !important;
            background: #F1F5F9 !important;
            color: #64748B !important;
            border: 1px solid #E2E8F0 !important;
            transition: all 0.15s ease !important;
            box-shadow: none !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
        }
        [class*="st-key-mmchip-"] button:hover {
            border-color: #14B8A6 !important;
            color: #0F766E !important;
            background: #F0FDFA !important;
            transform: translateY(-1px);
        }
        [class*="st-key-mmchip-"] button p {
            margin: 0 !important;
            text-align: center !important;
            line-height: 1.2 !important;
        }
        [class*="st-key-mmchip-"] button p:nth-of-type(1) {
            font-size: 0.9rem !important;
            font-weight: 600 !important;
        }
        [class*="st-key-mmchip-"] button p:nth-of-type(2) {
            font-size: 0.7rem !important;
            font-weight: 400 !important;
            opacity: 0.7;
            margin-top: 0.2rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # CSS dinámico: estilo activo (teal) para las tarjetas seleccionadas
    active_rules = []
    for i, model in enumerate(models):
        if model.display_name in selected:
            active_rules.append(
                f".st-key-mmchip-{i} button, "
                f".st-key-mmchip-{i} button:hover, "
                f".st-key-mmchip-{i} button:focus, "
                f".st-key-mmchip-{i} button:active "
                "{ background: #14B8A6 !important; color: #FFFFFF !important; "
                "border-color: #0F766E !important; "
                "box-shadow: 0 2px 8px rgba(20, 184, 166, 0.25) !important; }"
                f".st-key-mmchip-{i} button p {{ color: #FFFFFF !important; }}"
            )
    if active_rules:
        st.markdown(
            "<style>" + "\n".join(active_rules) + "</style>",
            unsafe_allow_html=True,
        )

    if label:
        st.markdown(
            f"<div style='font-size:0.88rem;color:#475569;"
            f"margin-bottom:0.7rem;font-weight:500;'>{label}</div>",
            unsafe_allow_html=True,
        )

    def _toggle(name: str) -> None:
        s = st.session_state[state_key]
        if name in s:
            s.discard(name)
        else:
            s.add(name)

    cols = st.columns(len(models))
    for i, model in enumerate(models):
        is_active = model.display_name in selected
        icon = "✓" if is_active else "✕"
        name, company = _model_label_parts(model)
        with cols[i]:
            st.button(
                f"{icon}  {name}\n\n{company}",
                key=f"mmchip-{i}",
                on_click=_toggle,
                args=(model.display_name,),
                use_container_width=True,
            )

    return [m for m in models if m.display_name in selected]
