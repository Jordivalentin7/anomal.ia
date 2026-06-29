"""Utilidades de carga y análisis del flujo SCADA."""
from __future__ import annotations

import os
from typing import Dict, List

import pandas as pd

from .config import OPERATIONAL_RANGES


def dataset_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "data", "dataset_evaluacion.csv")


def load_dataset() -> pd.DataFrame:
    path = dataset_path()
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"No se encuentra el dataset por defecto en {path}."
        )
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.sort_values("timestamp", ascending=False).reset_index(drop=True)


def evaluate_row(row: pd.Series) -> Dict[str, str]:
    """Evalúa cada variable contra sus rangos y devuelve un veredicto por columna."""
    out: Dict[str, str] = {}
    for var, rng in OPERATIONAL_RANGES.items():
        if var not in row:
            continue
        v = float(row[var])
        if v < rng["min"] or v > rng["max"]:
            out[var] = "FUERA DE RANGO"
        else:
            out[var] = "NORMAL"
    return out


def summarize_row(row: pd.Series) -> str:
    """Formatea una lectura SCADA en texto compacto para consumo del LLM."""
    parts = []
    for var, rng in OPERATIONAL_RANGES.items():
        if var in row:
            parts.append(f"{var}={row[var]} {rng['unit']}")
    return ", ".join(parts) + f" (sensor={row.get('id_sensor', 'desconocido')})"


def anomaly_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Recuento por etiqueta real del dataset."""
    if "etiqueta_real" not in df.columns:
        return pd.DataFrame(columns=["etiqueta", "registros"])
    counts = df["etiqueta_real"].value_counts().rename_axis("etiqueta").reset_index(name="registros")
    return counts


def dataset_context(df: pd.DataFrame, label: str = "") -> str:
    """Resume el dataset activo en texto compacto para inyectar en el prompt del LLM.

    Permite al modelo razonar sobre datos reales (no solo conocimiento general),
    sea cual sea el dominio del CSV cargado.
    """
    if df is None or len(df) == 0:
        return ""

    lines: List[str] = ["Contexto del dataset activo:"]
    if label:
        lines.append(f"- Origen: {label}")
    lines.append(f"- Registros: {len(df)}")
    lines.append(f"- Columnas: {', '.join(df.columns.tolist())}")

    # Última lectura
    try:
        last = df.iloc[0]
        last_str = ", ".join(
            f"{c}={last[c]}" for c in df.columns if c not in ("timestamp",)
        )
        lines.append(f"- Última lectura: {last_str}")
    except Exception:  # noqa: BLE001
        pass

    # Rangos de columnas numéricas
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if numeric_cols:
        rng_lines = []
        for col in numeric_cols[:8]:
            try:
                rng_lines.append(
                    f"  {col}: min={df[col].min():.2f}, max={df[col].max():.2f}, media={df[col].mean():.2f}"
                )
            except Exception:  # noqa: BLE001
                continue
        if rng_lines:
            lines.append("- Estadísticas de variables numéricas:")
            lines.extend(rng_lines)

    # Distribución de etiquetas si existen
    if "etiqueta_real" in df.columns:
        counts = df["etiqueta_real"].value_counts().to_dict()
        labels_str = ", ".join(f"{k}={v}" for k, v in counts.items())
        lines.append(f"- Distribución de etiquetas: {labels_str}")

    return "\n".join(lines)
