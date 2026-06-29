"""Configuración central del proyecto.

Define los proveedores de modelos disponibles, los rangos operacionales de
referencia de la red de agua y los parámetros de evaluación alineados con la
taxonomía propuesta en Arnau-Muñoz et al. (Mixtral Water Management).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class ModelSpec:
    provider: str
    model_id: str
    display_name: str
    origin: str
    notes: str


MODEL_CATALOG: List[ModelSpec] = [
    ModelSpec(
        provider="mistral",
        model_id="open-mixtral-8x7b",
        display_name="Mixtral 8x7B (Mistral AI)",
        origin="Europa / Francia",
        notes="Modelo de referencia del estudio base. Mixture of Experts.",
    ),
    ModelSpec(
        provider="mistral",
        model_id="mistral-small-latest",
        display_name="Mistral Small",
        origin="Europa / Francia",
        notes="Modelo compacto orientado a inferencia rápida.",
    ),
    ModelSpec(
        provider="mistral",
        model_id="mistral-medium-latest",
        display_name="Mistral Medium",
        origin="Europa / Francia",
        notes="Equilibrio entre coste y capacidad de razonamiento.",
    ),
    ModelSpec(
        provider="groq",
        model_id="llama-3.3-70b-versatile",
        display_name="Llama 3.3 70B (Groq)",
        origin="Meta AI · Inferencia Groq",
        notes="Referencia de alto rendimiento para comparativa.",
    ),
    ModelSpec(
        provider="groq",
        model_id="llama-3.1-8b-instant",
        display_name="Llama 3.1 8B Instant (Groq)",
        origin="Meta AI · Inferencia Groq",
        notes="Modelo ligero para contraste de capacidad.",
    ),
]


def model_by_name(display_name: str) -> ModelSpec:
    for m in MODEL_CATALOG:
        if m.display_name == display_name:
            return m
    raise KeyError(display_name)


# --- Rangos operacionales de referencia (red de agua) ---
OPERATIONAL_RANGES: Dict[str, Dict[str, float]] = {
    "ph": {"min": 6.5, "max": 9.5, "unit": "pH"},
    "cloro_residual": {"min": 0.2, "max": 1.0, "unit": "mg/L"},
    "presion_bar": {"min": 2.0, "max": 6.0, "unit": "bar"},
    "consumo_kwh": {"min": 40.0, "max": 55.0, "unit": "kWh"},
    "caudal_m3h": {"min": 130.0, "max": 170.0, "unit": "m³/h"},
}


COMPLEXITY_LEVELS: List[str] = ["Básica", "Intermedia", "Avanzada", "Experta"]


# Pesos por métrica según nivel de complejidad (Arnau-Muñoz et al., Sec. 3.4)
@dataclass(frozen=True)
class MetricWeights:
    keywords: float
    units: float
    technical: float
    calculation: float
    length: float


METRIC_WEIGHTS: Dict[str, MetricWeights] = {
    "Básica": MetricWeights(0.45, 0.15, 0.20, 0.00, 0.20),
    "Intermedia": MetricWeights(0.45, 0.15, 0.20, 0.00, 0.20),
    "Avanzada": MetricWeights(0.40, 0.15, 0.20, 0.15, 0.10),
    "Experta": MetricWeights(0.40, 0.15, 0.20, 0.15, 0.10),
}


# Rangos de longitud recomendados (palabras) por nivel
LENGTH_TARGETS: Dict[str, Dict[str, int]] = {
    "Básica": {"min": 10, "max": 50, "optimal_low": 15, "optimal_high": 35},
    "Intermedia": {"min": 20, "max": 90, "optimal_low": 30, "optimal_high": 70},
    "Avanzada": {"min": 40, "max": 180, "optimal_low": 60, "optimal_high": 140},
    "Experta": {"min": 60, "max": 250, "optimal_low": 90, "optimal_high": 200},
}
