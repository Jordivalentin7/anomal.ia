"""Banco de respuestas del modelo fine-tuneado del proyecto de referencia.

Carga las 27 respuestas literales generadas por Arnau-Muñoz et al. (2025)
con su Mixtral 8x7B Instruct fine-tuneado en la variante `ultra_expert`
(7.530 ejemplos de entrenamiento, su modelo más entrenado).

Si la consulta del operador coincide con una pregunta del banco oficial,
devolvemos su respuesta original en lugar de generar una nueva con un LLM.
Esto convierte la columna izquierda del Router en una **comparación directa
contra la solución del proyecto de referencia** (fine-tuning), frente a la
solución del TFG (router adaptativo de prompts) en la columna derecha.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Optional


def _bank_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "data", "reference_responses.json")


@dataclass(frozen=True)
class ReferenceEntry:
    """Respuesta del Mixtral fine-tuneado, con metadatos del paper."""
    question: str
    answer: str
    difficulty: str
    area: str
    response_time: float
    quality_score: float
    word_count: int


def _normalize(text: str) -> str:
    """Normaliza el texto para hacer matching robusto.

    Quita acentos, pasa a minúsculas, colapsa espacios y elimina puntuación
    final para tolerar pequeñas variaciones en la escritura.
    """
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = text.strip("¿?¡!.,; ")
    return text


@lru_cache(maxsize=1)
def _load_bank() -> Dict[str, ReferenceEntry]:
    """Carga el JSON del banco y devuelve un índice por pregunta normalizada."""
    path = _bank_path()
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    index: Dict[str, ReferenceEntry] = {}
    for r in data.get("responses", []):
        entry = ReferenceEntry(
            question=r["question"],
            answer=r["answer"],
            difficulty=r.get("difficulty", ""),
            area=r.get("area", ""),
            response_time=float(r.get("response_time", 0.0)),
            quality_score=float(r.get("quality_score", 0.0)),
            word_count=int(r.get("word_count", len(r["answer"].split()))),
        )
        index[_normalize(entry.question)] = entry
    return index


def lookup_reference(query: str) -> Optional[ReferenceEntry]:
    """Busca la respuesta del modelo de referencia para una consulta.

    Devuelve la entrada exacta del banco oficial si la consulta normalizada
    coincide; en caso contrario, None.
    """
    bank = _load_bank()
    return bank.get(_normalize(query))


def is_official_question(query: str) -> bool:
    """Indica si la consulta forma parte del banco oficial de 27 preguntas."""
    return lookup_reference(query) is not None


def bank_size() -> int:
    """Número total de respuestas oficiales cargadas."""
    return len(_load_bank())
