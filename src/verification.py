"""Capa de verificación determinista (pre-LLM).

Extrae valores con unidades de la consulta del operador y los compara con
los rangos operacionales. El veredicto se inyecta en el prompt como
"hecho establecido", evitando que el LLM invierta el veredicto en
preguntas del tipo "¿es seguro X mg/L?".
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from .config import OPERATIONAL_RANGES


# (parámetro, patrón regex que captura el valor)
# El orden importa: patrones más específicos primero para evitar que "kW"
# sea capturado por "kWh".
_VALUE_EXTRACTORS: List[tuple[str, str]] = [
    ("cloro_residual", r"(\d+(?:[.,]\d+)?)\s*mg\s*/\s*l"),
    ("presion_bar", r"(\d+(?:[.,]\d+)?)\s*bar"),
    ("consumo_kwh", r"(\d+(?:[.,]\d+)?)\s*kwh"),
    ("caudal_m3h", r"(\d+(?:[.,]\d+)?)\s*(?:m\s*3|m³)\s*/\s*h"),
    # pH requiere mencionar la palabra clave
    ("ph", r"ph\s*(?:de|=|:)?\s*(\d+(?:[.,]\d+)?)"),
]


@dataclass
class VerificationFinding:
    parameter: str
    value: float
    unit: str
    min: float
    max: float
    status: str  # "DENTRO DE RANGO" | "FUERA DE RANGO"

    def line(self) -> str:
        return (
            f"- {self.parameter} = {self.value} {self.unit} → {self.status} "
            f"(rango de referencia: {self.min}–{self.max} {self.unit})"
        )


def verify_query_values(query: str) -> List[VerificationFinding]:
    """Extrae valores con unidades reconocibles y los clasifica contra los
    rangos operacionales. Devuelve una lista vacía si no hay valores verificables.
    """
    text = query.lower()
    findings: List[VerificationFinding] = []
    seen_params: set[str] = set()

    for param, pattern in _VALUE_EXTRACTORS:
        if param in seen_params:
            continue
        m = re.search(pattern, text)
        if not m:
            continue
        try:
            value = float(m.group(1).replace(",", "."))
        except (ValueError, IndexError):
            continue
        rng = OPERATIONAL_RANGES.get(param)
        if not rng:
            continue
        status = (
            "DENTRO DE RANGO"
            if rng["min"] <= value <= rng["max"]
            else "FUERA DE RANGO"
        )
        findings.append(
            VerificationFinding(
                parameter=param,
                value=value,
                unit=rng["unit"],
                min=rng["min"],
                max=rng["max"],
                status=status,
            )
        )
        seen_params.add(param)

    return findings


def format_findings(findings: List[VerificationFinding]) -> str:
    """Formatea los hallazgos como bloque inyectable en el prompt del usuario."""
    if not findings:
        return ""
    lines = "\n".join(f.line() for f in findings)
    return (
        "\n\nVERIFICACIÓN NUMÉRICA PREVIA (resultado determinista, "
        "considéralo hecho establecido y no lo contradigas):\n"
        f"{lines}"
    )
