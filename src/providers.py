"""Capa de proveedores LLM.

Encapsula el acceso a Mistral AI y Groq (Llama) detrás de una misma interfaz,
devolviendo texto y metadatos (latencia, modelo) para una evaluación homogénea.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import List, Optional

from dotenv import load_dotenv

try:
    from mistralai import Mistral
except ImportError:  # pragma: no cover
    Mistral = None  # type: ignore

try:
    from groq import Groq
except ImportError:  # pragma: no cover
    Groq = None  # type: ignore

from .config import ModelSpec

load_dotenv()


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    latency_s: float
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None


class ProviderRegistry:
    """Gestiona clientes de proveedores con inicialización perezosa."""

    def __init__(self) -> None:
        self._mistral: Optional[object] = None
        self._groq: Optional[object] = None

    @property
    def mistral(self):
        if self._mistral is None:
            key = os.getenv("MISTRAL_API_KEY")
            if key and Mistral is not None:
                self._mistral = Mistral(api_key=key)
        return self._mistral

    @property
    def groq(self):
        if self._groq is None:
            key = os.getenv("GROQ_API_KEY")
            if key and Groq is not None:
                self._groq = Groq(api_key=key)
        return self._groq

    def is_available(self, provider: str) -> bool:
        if provider == "mistral":
            return self.mistral is not None
        if provider == "groq":
            return self.groq is not None
        return False


_registry = ProviderRegistry()


def available_providers() -> List[str]:
    out = []
    if _registry.is_available("mistral"):
        out.append("mistral")
    if _registry.is_available("groq"):
        out.append("groq")
    return out


def call_model(
    spec: ModelSpec,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.0,
    max_tokens: int = 800,
) -> LLMResponse:
    """Llamada unificada a un modelo, devolviendo texto y métricas básicas."""
    start = time.time()
    try:
        if spec.provider == "mistral":
            client = _registry.mistral
            if client is None:
                return LLMResponse(
                    content="",
                    model=spec.model_id,
                    provider=spec.provider,
                    latency_s=0.0,
                    error="MISTRAL_API_KEY no está configurada en el archivo .env",
                )
            resp = client.chat.complete(
                model=spec.model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            text = resp.choices[0].message.content

        elif spec.provider == "groq":
            client = _registry.groq
            if client is None:
                return LLMResponse(
                    content="",
                    model=spec.model_id,
                    provider=spec.provider,
                    latency_s=0.0,
                    error="GROQ_API_KEY no está configurada en el archivo .env",
                )
            resp = client.chat.completions.create(
                model=spec.model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            text = resp.choices[0].message.content

        else:
            return LLMResponse(
                content="",
                model=spec.model_id,
                provider=spec.provider,
                latency_s=0.0,
                error=f"Proveedor no soportado: {spec.provider}",
            )

        return LLMResponse(
            content=text or "",
            model=spec.model_id,
            provider=spec.provider,
            latency_s=time.time() - start,
        )

    except Exception as exc:  # noqa: BLE001
        return LLMResponse(
            content="",
            model=spec.model_id,
            provider=spec.provider,
            latency_s=time.time() - start,
            error=f"{type(exc).__name__}: {exc}",
        )
