"""Página 2 — Monitorización SCADA."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from ..scada import load_dataset
from .common import page_header


DEFAULT_KEY = "Por defecto · dataset_evaluacion.csv"


def _read_uploaded_csv(uploaded_file) -> pd.DataFrame:
    # Aseguramos puntero al inicio (UploadedFile puede haber sido leído antes)
    try:
        uploaded_file.seek(0)
    except Exception:  # noqa: BLE001
        pass
    df = pd.read_csv(uploaded_file)
    if "timestamp" in df.columns:
        try:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp", ascending=False).reset_index(drop=True)
        except (ValueError, TypeError):
            pass
    return df


def _ensure_state() -> None:
    if "scada_uploaded" not in st.session_state:
        st.session_state["scada_uploaded"] = {}
    if "scada_active" not in st.session_state:
        st.session_state["scada_active"] = DEFAULT_KEY


def _on_file_upload() -> None:
    """Callback al subir un archivo. Se ejecuta antes de re-renderizar.

    Tras procesar, se incrementa un contador que forma parte del `key` del
    file_uploader. Esto fuerza a Streamlit a recrear el widget desde cero, así
    el botón "Upload" se mantiene siempre visible (sin chip de archivo subido,
    sin botón "+").
    """
    counter = st.session_state.get("scada_upload_counter", 0)
    uploader_key = f"scada_upload_{counter}"
    uploaded = st.session_state.get(uploader_key)
    if uploaded is None:
        return
    if "scada_uploaded" not in st.session_state:
        st.session_state["scada_uploaded"] = {}
    try:
        if uploaded.name in st.session_state["scada_uploaded"]:
            st.session_state["scada_active"] = uploaded.name
        else:
            df_new = _read_uploaded_csv(uploaded)
            st.session_state["scada_uploaded"][uploaded.name] = df_new
            st.session_state["scada_active"] = uploaded.name
    except Exception as exc:  # noqa: BLE001
        st.session_state["_scada_upload_error"] = f"{type(exc).__name__}: {exc}"
    finally:
        # Recreamos el widget con un key nuevo en el próximo render
        st.session_state["scada_upload_counter"] = counter + 1


def _delete_active() -> None:
    name = st.session_state.get("scada_active", DEFAULT_KEY)
    if name == DEFAULT_KEY:
        return
    st.session_state["scada_uploaded"].pop(name, None)
    st.session_state["scada_active"] = DEFAULT_KEY


def render() -> None:
    page_header(
        number="02",
        page_name="Monitorización SCADA",
        title_html="Dataset sintético de <em>sensores</em>",
    )

    _ensure_state()
    available = [DEFAULT_KEY] + list(st.session_state["scada_uploaded"].keys())
    current = st.session_state["scada_active"]
    if current not in available:
        current = DEFAULT_KEY
        st.session_state["scada_active"] = current

    # CSS: compactar todo el bloque SCADA (header pequeño, controles pegados, tabla amplia)
    st.markdown(
        """
        <style>
        /* Quita margen del header para subir todo */
        .caudal-page-head { margin-bottom: 0.4rem !important; }
        /* Selector + uploader: alineación + sin padding extra */
        [data-testid="stHorizontalBlock"]:has([data-testid="stFileUploader"]) {
            align-items: center !important;
            margin-top: 0 !important;
            margin-bottom: 0.3rem !important;
        }
        [data-testid="stFileUploaderDropzone"] {
            min-height: 38px !important;
            padding: 0.25rem 0.6rem !important;
        }
        [data-testid="stFileUploader"] section {
            padding: 0 !important;
        }
        [data-testid="stFileUploaderDropzoneInstructions"] {
            display: none !important;
        }
        /* Ocultar la tarjeta-chip del archivo subido (nombre + X eliminar) */
        [data-testid="stFileChip"],
        [data-testid="stFileChipName"],
        [data-testid="stFileChipDeleteBtn"] {
            display: none !important;
        }
        /* Element-container del uploader y selector: sin margen vertical */
        [data-testid="stMain"] [data-testid="stElementContainer"]:has([data-testid="stFileUploader"]),
        [data-testid="stMain"] [data-testid="stElementContainer"]:has([data-testid="stSelectbox"]) {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # === Selector + uploader compacto ===
    col_sel, col_up = st.columns([3, 4], gap="small", vertical_alignment="center")
    with col_sel:
        active = st.selectbox(
            label="active_select",
            options=available,
            index=available.index(current),
            label_visibility="collapsed",
        )
        st.session_state["scada_active"] = active
    with col_up:
        upload_counter = st.session_state.get("scada_upload_counter", 0)
        st.file_uploader(
            label="Subir CSV",
            type=["csv"],
            key=f"scada_upload_{upload_counter}",
            label_visibility="collapsed",
            on_change=_on_file_upload,
        )

    # Solo mostramos errores. La carga exitosa se refleja directamente en
    # el selector y en el pill del topbar (sin mensaje extra).
    st.session_state.pop("_scada_upload_ok", None)
    err = st.session_state.pop("_scada_upload_error", None)
    if err:
        st.error(f"No se pudo leer el CSV: {err}")

    # === Carga del dataset activo ===
    if active == DEFAULT_KEY:
        try:
            df = load_dataset()
        except FileNotFoundError as exc:
            st.error(str(exc))
            return
    else:
        df = st.session_state["scada_uploaded"][active]

    # === Tabla (altura reducida para evitar scroll de página) ===
    st.dataframe(df, use_container_width=True, height=520)
