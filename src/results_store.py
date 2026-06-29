"""Almacén persistente de resultados del Router para las consultas oficiales.

Cuando el operador ejecuta en el Router una consulta que pertenece al banco
de ejemplos (las 12 preguntas literales del paper de Arnau-Muñoz et al.),
se guarda automáticamente el resultado en `data/tfg_results.json`.

La vista "Resultados obtenidos" consume estos datos para presentar la
comparación cara a cara contra las respuestas oficiales del Mixtral
fine-tuneado.

Política de upsert: una sola entrada por consulta normalizada. Re-ejecutar
la misma pregunta sobrescribe el resultado anterior con el más reciente.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
from typing import Dict, Optional


def _store_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "data", "tfg_results.json")


def _normalize(text: str) -> str:
    """Misma normalización que reference_bank.py para emparejar consultas."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = text.strip("¿?¡!.,; ")
    return text


@dataclass
class StoredResult:
    """Snapshot persistente de una ejecución del router en una pregunta oficial."""
    query: str
    level: str  # nivel del banco (Básica / Intermedia / Avanzada / Experta)
    model_name: str
    response: str
    word_count: int
    latency_s: float
    quality_score: float
    classification_level: str  # nivel detectado por el clasificador
    classification_confidence: float
    classification_via: str  # "Heurística" | "LLM"
    timestamp: str


def _load_raw() -> Dict[str, dict]:
    path = _store_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("results", {})
    except (json.JSONDecodeError, OSError):
        return {}


def save_result(
    query: str,
    level: str,
    model_name: str,
    response: str,
    latency_s: float,
    quality_score: float,
    classification_level: str,
    classification_confidence: float,
    classification_via: str,
) -> None:
    """Persiste el resultado de una ejecución del router. Upsert por consulta."""
    results = _load_raw()
    key = _normalize(query)
    entry = StoredResult(
        query=query,
        level=level,
        model_name=model_name,
        response=response,
        word_count=len(response.split()),
        latency_s=round(latency_s, 3),
        quality_score=round(quality_score, 3),
        classification_level=classification_level,
        classification_confidence=round(classification_confidence, 3),
        classification_via=classification_via,
        timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    results[key] = asdict(entry)

    path = _store_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"results": results}, f, ensure_ascii=False, indent=2)


def _from_dict(d: dict) -> StoredResult:
    """Construye un StoredResult ignorando campos legacy (compatibilidad)."""
    valid = {f.name for f in fields(StoredResult)}
    return StoredResult(**{k: v for k, v in d.items() if k in valid})


def get_result_for(query: str) -> Optional[StoredResult]:
    """Devuelve el resultado guardado para una consulta, o None."""
    raw = _load_raw().get(_normalize(query))
    if raw is None:
        return None
    return _from_dict(raw)


def get_all_results() -> Dict[str, StoredResult]:
    """Devuelve todos los resultados guardados indexados por consulta normalizada."""
    return {k: _from_dict(v) for k, v in _load_raw().items()}


def clear_result(query: str) -> bool:
    """Elimina el resultado guardado para una consulta. Devuelve True si existía."""
    results = _load_raw()
    key = _normalize(query)
    if key not in results:
        return False
    results.pop(key)
    with open(_store_path(), "w", encoding="utf-8") as f:
        json.dump({"results": results}, f, ensure_ascii=False, indent=2)
    return True
