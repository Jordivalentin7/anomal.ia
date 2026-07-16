"""Router adaptativo por complejidad.

Flujo:
    1. Clasifica la consulta del operador.
    2. Selecciona el prompt especializado para ese nivel.
    3. Invoca al proveedor/modelo elegido.
    4. Evalúa la respuesta con el sistema de cinco métricas.

Este componente es la propuesta central del TFG para mitigar el "valle de
interferencia": evita que un prompt genérico induzca sobreelaboración en
consultas básicas o respuestas superficiales en consultas expertas.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .classifier import ClassificationResult, classify
from .reference_bank import lookup_reference
from .config import ModelSpec
from .evaluation import EvalScore, evaluate
from .prompts import BASELINE_PROMPT, prompt_for
from .providers import LLMResponse, call_model
from .verification import (
    VerificationFinding,
    format_findings,
    verify_query_values,
)


@dataclass
class RouterOutcome:
    classification: ClassificationResult
    system_prompt: str
    llm_response: LLMResponse
    score: EvalScore
    mode: str  # "adaptativo" | "baseline"
    user_prompt: str = ""
    findings: List[VerificationFinding] | None = None
    # Cuando la respuesta del lado baseline proviene del modelo entrenado del
    # paper de referencia (Arnau-Muñoz et al.), `baseline_source` apunta al
    # origen ("reference") y `baseline_metadata` lleva los metadatos del paper.
    # En caso contrario es "generated" (baseline local con prompt genérico).
    baseline_source: Optional[str] = None
    baseline_metadata: Optional[dict] = None


def _with_context(prompt: str, dataset_context: str) -> str:
    """Añade el contexto del dataset activo al prompt del sistema."""
    if not dataset_context:
        return prompt
    return f"{prompt}\n\n{dataset_context}"


def run_adaptive(
    query: str,
    data_payload: str,
    model: ModelSpec,
    expected_keywords: Optional[List[str]] = None,
    expected_units: Optional[List[str]] = None,
    dataset_context: str = "",
) -> RouterOutcome:
    """Ejecuta el flujo con prompt especializado + verificación determinista."""
    classification = classify(query)
    system_prompt = _with_context(prompt_for(classification.level), dataset_context)
    findings = verify_query_values(query)
    user_prompt = _compose_user_prompt(query, data_payload, findings=findings)
    resp = call_model(model, system_prompt, user_prompt)
    score = evaluate(
        resp.content,
        level=classification.level,
        expected_keywords=expected_keywords,
        expected_units=expected_units,
    )
    return RouterOutcome(
        classification=classification,
        system_prompt=system_prompt,
        llm_response=resp,
        score=score,
        mode="adaptativo",
        user_prompt=user_prompt,
        findings=findings,
    )


def run_baseline(
    query: str,
    data_payload: str,
    model: ModelSpec,
    expected_keywords: Optional[List[str]] = None,
    expected_units: Optional[List[str]] = None,
    dataset_context: str = "",
) -> RouterOutcome:
    """Ejecuta el flujo de referencia (lado izquierdo de la comparación).

    Política en dos pasos:
      1. Si la consulta del operador coincide con una pregunta del banco
         oficial de evaluación (Arnau-Muñoz et al., 27 consultas), se devuelve
         **la respuesta literal del Mixtral fine-tuneado del paper** (variante
         ultra_expert, su modelo más entrenado). Esto convierte la comparación
         en directa: solución del proyecto de referencia (fine-tuning)
         frente a la solución del TFG (router adaptativo).
      2. Si la consulta no está en el banco oficial (el operador la ha
         escrito libremente), se cae al baseline tradicional: mismo modelo
         elegido + prompt genérico, sin clasificador ni verificación.
    """
    classification = classify(query)

    reference = lookup_reference(query)
    if reference is not None:
        synthetic_resp = LLMResponse(
            content=reference.answer,
            model="mixtral_water_ultra_expert (Arnau-Muñoz et al.)",
            provider="ollama (paper)",
            latency_s=reference.response_time,
            error=None,
        )
        score = evaluate(
            synthetic_resp.content,
            level=classification.level,
            expected_keywords=expected_keywords,
            expected_units=expected_units,
        )
        return RouterOutcome(
            classification=classification,
            system_prompt="(respuesta del Mixtral fine-tuneado del paper, sin prompt aplicado en este TFG)",
            llm_response=synthetic_resp,
            score=score,
            mode="baseline",
            user_prompt="(respuesta literal del paper; no se envía prompt de usuario en este TFG)",
            findings=None,
            baseline_source="reference",
            baseline_metadata={
                "source_model": "Mixtral 8x7B Instruct (fine-tuned)",
                "source_variant": "ultra_expert",
                "training_examples": 7530,
                "source_paper": "Arnau-Muñoz et al. (2025)",
                "difficulty": reference.difficulty,
                "area": reference.area,
                "word_count": reference.word_count,
                "quality_score_paper": reference.quality_score,
                "response_time_paper": reference.response_time,
            },
        )

    # Fallback: consulta libre del operador → generamos baseline localmente
    system_prompt = _with_context(BASELINE_PROMPT, dataset_context)
    user_prompt = _compose_user_prompt(query, data_payload, findings=None)
    resp = call_model(model, system_prompt, user_prompt)
    score = evaluate(
        resp.content,
        level=classification.level,
        expected_keywords=expected_keywords,
        expected_units=expected_units,
    )
    return RouterOutcome(
        classification=classification,
        system_prompt=system_prompt,
        llm_response=resp,
        score=score,
        mode="baseline",
        user_prompt=user_prompt,
        findings=None,
        baseline_source="generated",
        baseline_metadata=None,
    )


def _compose_user_prompt(
    query: str,
    data_payload: str,
    findings: List[VerificationFinding] | None,
) -> str:
    payload = data_payload.strip() or "(sin lectura adicional)"
    extra = format_findings(findings or [])
    return (
        f"Lectura SCADA actual: {payload}\n\n"
        f"Consulta del operador: {query.strip()}"
        f"{extra}"
    )
