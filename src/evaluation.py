"""Sistema de evaluación por cinco componentes.

Replica el marco descrito en Arnau-Muñoz et al. (Sec. 3.4):
    - Palabras clave
    - Unidades técnicas
    - Indicadores técnicos (recomendación, evaluación cualitativa, referencia)
    - Cálculo explícito (solo Avanzada/Experta)
    - Longitud apropiada

Los pesos se redistribuyen automáticamente en niveles sin cálculo.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List

from .config import LENGTH_TARGETS, METRIC_WEIGHTS


UNIT_PATTERNS = [
    r"\bmg/l\b",
    r"\bbar\b",
    r"\bkw\b",
    r"\bkwh\b",
    r"\bkvar?\b",
    r"\bkva\b",
    r"\bm\s?3\s?/\s?h\b|m³/h",
    r"\b(µ|u)s/cm\b",
    r"°c\b",
]

QUALITATIVE_PATTERNS = [
    r"\b(acept(able|ado)|correcto|adecuado|normal|"
    r"(fuera|dentro) (de|del) rango|en rango|"
    r"anómalo|anomalo|peligros[oa]|crítico|critico|recomendable|"
    r"seguro|alerta)\b",
]

RECOMMENDATION_PATTERNS = [
    # Fórmulas explícitas de recomendación
    r"\b(se recomienda|recomiendo|se sugiere|conviene|deber[íi]a|acci[oó]n:?|"
    r"se propone|es necesario)\b",
    # Verbos operativos en imperativo o infinitivo (lenguaje típico del operador)
    r"\b(ajust(a|ar|e|ad)|mant(ener|enga|enha|en)|revis(a|ar|e|ad)|"
    r"verif(ica|icar|ique)|reduc(e|ir|id)|aument(a|ar|e|ad)|"
    r"cal(ibra|ibrar|ibre)|monitoriz(a|ar|ación|e|ad)|activ(a|ar|e|ad)|"
    r"desactiv(a|ar|e|ad)|programar?|inspeccionar|dosific(a|ar|ación))\b",
]

REGULATION_PATTERNS = [
    r"\brd\s?140\b",
    r"\bnormativa\b",
    r"\breglament\w+\b",
    r"\bnorma\b",
]

CALCULATION_PATTERNS = [
    r"\d+[.,]?\d*\s*[+\-*/×÷=]",
    r"=\s*\d",
    r"√",
    r"\bpaso\s*\d",
    r"\bcos\s*[ϕφ]",
]


@dataclass
class EvalScore:
    keywords: float = 0.0
    units: float = 0.0
    technical: float = 0.0
    calculation: float = 0.0
    length: float = 0.0
    total: float = 0.0
    breakdown: Dict[str, float] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)


def _hit_ratio(text: str, expected: List[str]) -> float:
    if not expected:
        return 1.0
    text_l = text.lower()
    hits = sum(1 for k in expected if k.lower() in text_l)
    return hits / len(expected)


def _regex_hits(text: str, patterns: List[str]) -> int:
    return sum(1 for p in patterns if re.search(p, text, flags=re.IGNORECASE))


def _length_score(text: str, level: str) -> float:
    n = len(text.split())
    cfg = LENGTH_TARGETS[level]
    if n < cfg["min"] or n > cfg["max"]:
        return 0.2
    if cfg["optimal_low"] <= n <= cfg["optimal_high"]:
        return 1.0
    # Zona intermedia
    return 0.7


def evaluate(
    response: str,
    level: str,
    expected_keywords: List[str] | None = None,
    expected_units: List[str] | None = None,
) -> EvalScore:
    """Puntúa una respuesta según los cinco componentes ponderados."""
    text = response or ""
    weights = METRIC_WEIGHTS[level]
    score = EvalScore()

    # 1. Keywords
    score.keywords = _hit_ratio(text, expected_keywords or [])

    # 2. Units
    if expected_units:
        score.units = _hit_ratio(text, expected_units)
    else:
        score.units = min(1.0, _regex_hits(text, UNIT_PATTERNS) / 2)

    # 3. Technical (media de cuatro sub-indicadores: unidades, recomendación,
    #    evaluación cualitativa, referencia normativa)
    sub_scores = [
        1.0 if _regex_hits(text, UNIT_PATTERNS) else 0.0,
        1.0 if _regex_hits(text, RECOMMENDATION_PATTERNS) else 0.0,
        1.0 if _regex_hits(text, QUALITATIVE_PATTERNS) else 0.0,
        1.0 if _regex_hits(text, REGULATION_PATTERNS) else 0.0,
    ]
    score.technical = sum(sub_scores) / len(sub_scores)

    # 4. Calculation (solo Avanzada/Experta)
    if level in ("Avanzada", "Experta"):
        score.calculation = 1.0 if _regex_hits(text, CALCULATION_PATTERNS) >= 1 else 0.0

    # 5. Length
    score.length = _length_score(text, level)

    # Total ponderado
    score.total = (
        weights.keywords * score.keywords
        + weights.units * score.units
        + weights.technical * score.technical
        + weights.calculation * score.calculation
        + weights.length * score.length
    )

    score.breakdown = {
        "Palabras clave": round(score.keywords, 3),
        "Unidades": round(score.units, 3),
        "Indicador técnico": round(score.technical, 3),
        "Cálculo": round(score.calculation, 3),
        "Longitud": round(score.length, 3),
    }

    n_words = len(text.split())
    target = LENGTH_TARGETS[level]
    if n_words > target["max"]:
        score.notes.append(
            f"Respuesta de {n_words} palabras excede el máximo recomendado "
            f"({target['max']}) para nivel {level.lower()}: posible sobre-elaboración."
        )
    elif n_words < target["min"]:
        score.notes.append(
            f"Respuesta de {n_words} palabras por debajo del mínimo recomendado "
            f"({target['min']}) para nivel {level.lower()}."
        )

    return score
