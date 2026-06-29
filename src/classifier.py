"""Clasificador híbrido de complejidad de consultas.

Pipeline en dos fases:
  1. Heurística rápida (regex lingüísticos sobre el texto). Se devuelve sin
     coste cuando el match es inequívoco: consultas Básicas directas
     (verificación binaria) o Intermedias con criterio normativo/operativo.
  2. Si el patrón es ambiguo (varios niveles disparan a la vez, aparecen
     patrones Avanzada/Experta donde la heurística es menos fiable, o no
     hay patrones que disparen), se escala a un LLM clasificador rápido
     (Llama 3.1 8B Instant en Groq) anclado por *few-shot* en el banco
     oficial de evaluación de Arnau-Muñoz et al. (27 consultas reales).

Si el LLM falla por cualquier motivo (API caída, sin API key, respuesta
malformada), se devuelve el resultado heurístico como degradación elegante.
Esto garantiza que el sistema **siempre devuelve una clasificación**.

Niveles: Básica, Intermedia, Avanzada, Experta (taxonomía del artículo).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Optional, Tuple

from .config import OPERATIONAL_RANGES

_VARIABLE_ALIASES = {
    "ph": ["ph"],
    "cloro_residual": ["cloro", "desinfección", "hipoclorito"],
    "presion_bar": ["presion", "presión", "bar"],
    "consumo_kwh": ["consumo", "kwh", "energía", "energia", "potencia"],
    "caudal_m3h": ["caudal", "flujo", "m3/h", "m³/h"],
}

# Cada patrón se asocia a una etiqueta humana corta que se muestra en la UI
# como justificación de la clasificación, en lugar del regex crudo.
_BASIC_PATTERNS: List[Tuple[str, str]] = [
    (r"\b(es|está|son|estan)\b.*\b(correcto|seguro|normal|válido|valido|dentro|fuera)\b",
     "verificación binaria de un valor"),
    (r"\b(sí o no|si o no)\b", "pregunta cerrada (sí/no)"),
    (r"^¿?(cumple|verifica|valida)", "verificación directa"),
]

_INTERMEDIATE_PATTERNS: List[Tuple[str, str]] = [
    (r"\b(rd ?140|normativa|reglamento|umbral|límite|limite|regulación|regulacion)\b",
     "referencia normativa o reglamentaria"),
    (r"\bsegún\b", "apela a un criterio externo"),
    (r"\bconforme\b", "exigencia de conformidad"),
    (r"\b(es|son|está|estan)\s+(aceptable[s]?|adecuad[oa]s?|suficiente[s]?)\b",
     "evaluación contra criterio operativo"),
]

_ADVANCED_PATTERNS: List[Tuple[str, str]] = [
    (r"\bcalcul(a|ar|o|e|emos)\b", "solicita un cálculo explícito"),
    (r"\bcuánto|cuanto\b", "pregunta cuantitativa"),
    (r"\befici(encia|ente)\b", "métrica de eficiencia"),
    (r"\b(kva|kvar)\b", "unidad eléctrica (kVA/kVAr)"),
    (r"\breactiva\b", "potencia reactiva mencionada"),
]

_EXPERT_PATTERNS: List[Tuple[str, str]] = [
    (r"\bdiagn(ó|o)stico\b", "solicita un diagnóstico"),
    (r"\brecomienda(s|r)?\b", "solicita una recomendación"),
    (r"\b(por qu(é|e)|causa|motivo)\b", "pregunta por la causa o motivo"),
    (r"\bdecid(ir|e|imos)\b", "implica una decisión operativa"),
    (r"\boptimiz(a|ar|ación|acion)\b", "solicita optimización"),
    (r"\bcompar(a|ar|ativa)\b", "solicita comparación"),
    (r"\bpredic(ción|cion|e|ir)\b", "solicita predicción"),
    (r"\banomal[íi]a\b", "menciona anomalía"),
    (r"\bhip[oó]tesis\b", "solicita hipótesis"),
    (r"\bprioriz(a|ar|arías|ar[íi]as)\b", "solicita priorización"),
    (r"\bdiferencial\b", "análisis diferencial"),
    (r"\bminimiz(a|ar)\b", "objetivo de minimización"),
    (r"\bgarantizar?\b", "exigencia de garantía"),
    (r"\b(cu[áa]l|cu[áa]nto|cu[áa]ndo) ser[áa]\b", "pregunta predictiva sobre el futuro"),
    (r"\b(ser[áa]|habr[áa]|tendremos|alcanzar[áa])\b.*\b(demanda|consumo|caudal|pico)\b",
     "predicción de demanda/consumo"),
    (r"\bdemanda\s+(a\s+las|en\s+\d|nocturna|matutina|punta|valle)\b",
     "demanda específica por franja horaria"),
    (r"\bpron[óo]stico\b", "solicita pronóstico"),
    (r"\bestimaci[óo]n\b", "solicita estimación"),
    (r"\ba\s+\d{1,2}\s*°\s*c\b", "incluye temperatura como contexto"),
    (r"\b(s[áa]bado|domingo|lunes|martes|mi[eé]rcoles|jueves|viernes)\s+(de|a|en)\b",
     "incluye día de la semana como contexto"),
    (r"\b(qu[eé]|cu[áa]l)\s+(pozo|bomba|v[áa]lvula|opci[óo]n|alternativa)\b",
     "selección entre alternativas operativas"),
    (r"\bcu[áa]l\s+de\s+(los|las|estos|estas)\b", "selección dentro de un conjunto"),
    (r"\bm[áa]s\s+(eficiente|adecuad[oa]|efectiv[oa]|rentable|conveniente|barato|r[áa]pido)\b",
     "criterio comparativo de eficiencia"),
    (r"\b(activar|encender|arrancar)\s+(primero|antes)\b", "secuenciación de arranque"),
    (r"\bdeber[íi]a\s+(activar|encender|ajustar|priorizar|arrancar|intervenir)\b",
     "decisión de intervención"),
    (r"\ben\s+qu[eé]\s+orden\b", "priorización por orden"),
    (r"\bpotencia reactiva\b", "cálculo del triángulo de potencias"),
    (r"\bqu[eé]\s+(est[áa]\s+)?(pas(a|ando)|ocurr(e|iendo)|sucede)\b",
     "diagnóstico abierto (¿qué ocurre?)"),
    (r"\b(pero|aunque|sin embargo)\s+solo\b", "contraste típico de anomalía"),
    (r"\bqu[eé]\s+hipótesis\b", "solicita hipótesis explícita"),
]


@dataclass
class ClassificationResult:
    level: str
    score: float
    reasons: List[str]
    variables_detected: List[str]


def _count_variables(text: str) -> List[str]:
    t = text.lower()
    found: List[str] = []
    for var, aliases in _VARIABLE_ALIASES.items():
        if any(a in t for a in aliases):
            found.append(var)
    return found


def _match_any(patterns: List[Tuple[str, str]], text: str) -> List[str]:
    """Devuelve la etiqueta humana de cada patrón que hace match con el texto."""
    return [label for pattern, label in patterns if re.search(pattern, text)]


# ============================================================================
# FASE 1 — Heurística rápida (regex)
# ============================================================================

def _classify_heuristic(query: str) -> ClassificationResult:
    """Clasificación determinista por patrones lingüísticos.

    Cascada de especificidad decreciente:
        experta > avanzada (cálculo) > intermedia (normativa) > básica.
    Si nada dispara, se aplica fallback a Básica corta (1 variable, ≤15 palabras)
    o Intermedia por defecto (zona segura contra sobreelaboración).
    """
    text = query.strip().lower()
    reasons: List[str] = []

    vars_detected = _count_variables(text)
    n_vars = len(vars_detected)

    hits_expert = _match_any(_EXPERT_PATTERNS, text)
    hits_advanced = _match_any(_ADVANCED_PATTERNS, text)
    hits_intermediate = _match_any(_INTERMEDIATE_PATTERNS, text)
    hits_basic = _match_any(_BASIC_PATTERNS, text)

    if hits_expert or n_vars >= 3:
        reasons.append(
            "Se detectan indicadores de razonamiento experto"
            f" ({', '.join(hits_expert) or 'múltiples variables'})"
        )
        level = "Experta"
        score = 0.9
    elif hits_advanced:
        reasons.append(
            "La consulta sugiere un cálculo cuantitativo explícito"
            f" ({', '.join(hits_advanced)})"
        )
        level = "Avanzada"
        score = 0.8
    elif hits_intermediate:
        reasons.append(
            "Se menciona normativa o umbral reglamentario: "
            + ", ".join(hits_intermediate)
        )
        level = "Intermedia"
        score = 0.75
    elif hits_basic:
        reasons.append("Consulta binaria o verificación directa de un valor")
        level = "Básica"
        score = 0.8
    elif n_vars == 1 and len(text.split()) <= 15:
        reasons.append("Consulta corta sobre una única variable")
        level = "Básica"
        score = 0.6
    else:
        reasons.append("Sin indicadores claros; se aplica nivel intermedio por defecto")
        level = "Intermedia"
        score = 0.5

    if n_vars:
        reasons.append(
            f"Variables detectadas ({n_vars}): "
            + ", ".join(OPERATIONAL_RANGES.get(v, {}).get("unit", v) + f" [{v}]" for v in vars_detected)
        )

    return ClassificationResult(
        level=level,
        score=round(score, 2),
        reasons=reasons,
        variables_detected=vars_detected,
    )


# ============================================================================
# FASE 2 — Clasificador LLM (escalado en ambigüedad)
# ============================================================================

_CLASSIFIER_SYSTEM_PROMPT = """Clasifica la consulta del operador SCADA en uno de estos niveles:

- "Básica": verificación sí/no de un único valor contra un rango conocido.
- "Intermedia": evaluación contra criterio normativo u operativo ("aceptable", "cumple RD 140").
- "Avanzada": cálculo numérico explícito, balance, eficiencia o comparación cuantitativa.
- "Experta": diagnóstico abierto, optimización entre alternativas, predicción contextual o decisión multivariable.

Ejemplos (banco oficial Arnau-Muñoz et al., 2025):

BÁSICA:
- ¿Cómo evalúo agua con pH 7.2?
- ¿Es seguro cloro residual de 0.3 mg/L?
- ¿Es normal presión de 35 bar?

INTERMEDIA:
- ¿Los nitratos de 28 mg/L son aceptables?
- ¿Factor de potencia 0.78 es aceptable?
- ¿El agua con pH 7.2, cloro 0.4 mg/L, nitratos 28 mg/L cumple RD 140/2003?

AVANZADA:
- ¿Cuál es la eficiencia de un pozo con 45 kW produciendo 180 L/min?
- Si entrada es 300 L/min y salida 280 L/min, ¿cuál es el balance?
- Compara Falconera (45kW, 180L/min) vs Beniopa (50kW, 175L/min)

EXPERTA:
- Con potencia 45 kW y factor potencia 0.78, ¿cuál es la potencia reactiva?
- Tengo 3 pozos: Falconera, Beniopa, Llombart. ¿En qué orden activo?
- El pozo consume 45 kW pero solo produce 120 L/min. ¿Qué pasa?

Devuelve SOLO un JSON: {"level":"Básica|Intermedia|Avanzada|Experta","confidence":<0.0-1.0>,"reason":"<una frase corta>"}. Sin markdown, sin texto antes o después."""


def _get_classifier_model():
    """Selecciona el modelo más rápido disponible para clasificación.

    Prioriza Llama 3.1 8B Instant (Groq, ~50 ms) por velocidad; cae a
    Mistral Small si Groq no está configurado, y a cualquier otro modelo
    del catálogo como último recurso.
    """
    from .config import MODEL_CATALOG
    from .providers import available_providers

    provs = set(available_providers())
    preferred_ids = ["llama-3.1-8b-instant", "mistral-small-latest"]
    for pid in preferred_ids:
        for m in MODEL_CATALOG:
            if m.model_id == pid and m.provider in provs:
                return m
    for m in MODEL_CATALOG:
        if m.provider in provs:
            return m
    return None


def _parse_classifier_json(text: str) -> dict:
    """Extrae el JSON de la respuesta del LLM, tolerante a envoltorios."""
    text = (text or "").strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]
        while lines and lines[-1].strip().startswith("```"):
            lines.pop()
        text = "\n".join(lines)
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        text = text[start:end + 1]
    return json.loads(text)


_LEVEL_NORMALIZATION = {
    "básica": "Básica", "basica": "Básica", "basic": "Básica",
    "intermedia": "Intermedia", "intermediate": "Intermedia",
    "avanzada": "Avanzada", "advanced": "Avanzada",
    "experta": "Experta", "expert": "Experta",
}


def _normalize_level(s: str) -> str:
    return _LEVEL_NORMALIZATION.get((s or "").strip().lower(), "Intermedia")


@lru_cache(maxsize=256)
def _classify_llm(query: str) -> ClassificationResult:
    """Clasificación por LLM con few-shot del banco oficial.

    Cacheada con LRU para que repetir la misma consulta sea instantáneo en la
    misma sesión. Lanza excepción si el modelo no responde correctamente; el
    decorador no cachea excepciones, así que un fallo no envenena la caché.
    """
    from .providers import call_model

    model = _get_classifier_model()
    if model is None:
        raise RuntimeError("No hay modelo clasificador disponible (sin API keys)")

    user_prompt = f"Consulta: {query}"

    resp = call_model(
        model,
        _CLASSIFIER_SYSTEM_PROMPT,
        user_prompt,
        temperature=0.0,
        max_tokens=100,
    )

    if resp.error:
        raise RuntimeError(resp.error)

    parsed = _parse_classifier_json(resp.content)

    level = _normalize_level(parsed.get("level", ""))
    try:
        confidence = float(parsed.get("confidence", 0.7))
    except (TypeError, ValueError):
        confidence = 0.7
    confidence = max(0.0, min(1.0, confidence))
    reason = (parsed.get("reason") or "").strip() or "Clasificación por LLM"

    vars_detected = _count_variables(query.lower())
    reasons = [f"[LLM · {model.display_name}] {reason}"]
    if vars_detected:
        reasons.append(
            f"Variables detectadas ({len(vars_detected)}): "
            + ", ".join(
                OPERATIONAL_RANGES.get(v, {}).get("unit", v) + f" [{v}]"
                for v in vars_detected
            )
        )

    return ClassificationResult(
        level=level,
        score=round(confidence, 2),
        reasons=reasons,
        variables_detected=vars_detected,
    )


# ============================================================================
# Orquestador público
# ============================================================================

def classify(query: str) -> ClassificationResult:
    """Clasificador híbrido: heurística rápida + escalado a LLM en ambigüedad.

    Casos en los que se usa SOLO la heurística (latencia 0, coste 0):
        - Patrón Básica único, sin solapamiento con Intermedia/Avanzada/Experta.
        - Patrón Intermedia (normativa o criterio operativo) sin patrones de
          cálculo (Avanzada) o de diagnóstico (Experta).

    En el resto de casos (Avanzada/Experta detectados, varios niveles
    solapados, o fallback sin patrones) se consulta al LLM clasificador.
    Si el LLM falla por cualquier motivo, se devuelve la heurística como
    degradación elegante para no romper la app.
    """
    text = query.strip().lower()

    h_basic = _match_any(_BASIC_PATTERNS, text)
    h_intermediate = _match_any(_INTERMEDIATE_PATTERNS, text)
    h_advanced = _match_any(_ADVANCED_PATTERNS, text)
    h_expert = _match_any(_EXPERT_PATTERNS, text)

    has_higher = bool(h_advanced or h_expert)

    if h_basic and not h_intermediate and not has_higher:
        return _classify_heuristic(query)

    if h_intermediate and not has_higher:
        return _classify_heuristic(query)

    try:
        return _classify_llm(query)
    except Exception as exc:
        fallback = _classify_heuristic(query)
        fallback.reasons.append(
            f"LLM clasificador no disponible; se usa heurística como fallback ({type(exc).__name__}: {exc})"
        )
        return fallback
