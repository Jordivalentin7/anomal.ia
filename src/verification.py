"""Capa de verificación determinista.

Dos modos de verificación:

  1. **Pre-LLM** (`verify_query_values`): extrae valores con unidades de la
     consulta del operador y los compara con los rangos operacionales. El
     veredicto se inyecta en el prompt como "hecho establecido", evitando
     que el LLM invierta el veredicto en preguntas tipo "¿es seguro X mg/L?".

  2. **Post-LLM** (`verify_arithmetic`): inspecciona la respuesta generada
     buscando fórmulas con resultado numérico (`X = a/b = 12.34`). Re-ejecuta
     el cálculo con un evaluador AST seguro y marca discrepancias. Cubre el
     caso conocido de modelos pequeños que arrastran errores de redondeo en
     cálculos encadenados (p. ej. potencia reactiva con factor de potencia).
"""
from __future__ import annotations

import ast
import math
import operator
import re
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

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


# ============================================================================
# Verificación aritmética post-LLM
# ============================================================================

@dataclass
class ArithmeticFinding:
    """Discrepancia detectada entre un cálculo del LLM y su recálculo exacto."""
    expression: str       # como aparece en la respuesta, p. ej. "sqrt(57.69² - 45²)"
    claimed: float        # valor reclamado por el LLM, p. ej. 35.84
    computed: float       # valor recalculado por Python, p. ej. 36.10
    rel_error_pct: float  # |computed - claimed| / |computed| * 100

    def line(self) -> str:
        return (
            f"'{self.expression}' → recálculo exacto **{self.computed:.4g}**, "
            f"la respuesta indica **{self.claimed:.4g}** "
            f"(diferencia {self.rel_error_pct:.2f}%)."
        )


# Operadores y funciones permitidos en el evaluador AST.
_ALLOWED_BINOPS: Dict[type, Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}

_ALLOWED_UNARYOPS: Dict[type, Callable[[float], float]] = {
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_ALLOWED_FUNCS: Dict[str, Callable[..., float]] = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "abs": abs,
}


def _eval_ast(node: ast.AST) -> float:
    """Evalúa un nodo AST permitiendo solo aritmética básica + funciones de math."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
        return _ALLOWED_BINOPS[type(node.op)](
            _eval_ast(node.left), _eval_ast(node.right)
        )
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARYOPS:
        return _ALLOWED_UNARYOPS[type(node.op)](_eval_ast(node.operand))
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in _ALLOWED_FUNCS
    ):
        args = [_eval_ast(a) for a in node.args]
        return _ALLOWED_FUNCS[node.func.id](*args)
    raise ValueError(f"Nodo AST no permitido: {ast.dump(node)}")


def _safe_eval(expr: str) -> Optional[float]:
    """Evalúa una expresión aritmética con AST. Devuelve None si no es válida."""
    try:
        tree = ast.parse(expr, mode="eval")
        return float(_eval_ast(tree.body))
    except Exception:  # noqa: BLE001
        return None


# Patrones de unidades a eliminar antes de evaluar.
_UNIT_PATTERN = re.compile(
    r"\b(?:[kKmMμu]?(?:Wh?|VAr|VA|Hz|Var|m³?/h|L/min|mg/L|µS/cm|ppm|"
    r"bar|°C|min|h|s|V|A|W))\b",
    re.IGNORECASE,
)

# Funciones matemáticas reconocidas.
_FUNC_NAMES: Tuple[str, ...] = ("log10", "sqrt", "sin", "cos", "tan", "log", "exp", "abs")

# Caracteres puramente aritméticos permitidos en una expresión.
_ARITH_CHARS_SET = set("0123456789.,+-*/×÷·²³√^()\\{}")

# Patrones para localizar operadores y números resultado.
_OP_PATTERN = re.compile(r"[=≈]")
_RESULT_PATTERN = re.compile(r"\s*([\-+]?\d[\d.,]*)")


def _normalize_expr(s: str) -> str:
    """Convierte una expresión textual del LLM en sintaxis Python evaluable."""
    s = s.strip()
    # Sintaxis LaTeX habitual de los LLM
    s = re.sub(r"\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}", r"(\1)/(\2)", s)
    s = re.sub(r"\\sqrt\s*\{([^{}]+)\}", r"sqrt(\1)", s)
    s = s.replace(r"\(", "").replace(r"\)", "")
    s = s.replace(r"\,", "").replace(r"\.", ".")
    # Símbolos Unicode → ASCII
    s = s.replace("²", "**2").replace("³", "**3")
    s = s.replace("×", "*").replace("·", "*").replace("÷", "/")
    s = s.replace("√", "sqrt")
    s = s.replace("^", "**")
    # Llaves residuales (de LaTeX o agrupación)
    s = s.replace("{", "(").replace("}", ")")
    # Eliminar unidades
    s = _UNIT_PATTERN.sub("", s)
    # Coma decimal española → punto
    s = re.sub(r"(\d),(\d)", r"\1.\2", s)
    # Colapsar espacios
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _parse_number(s: str) -> Optional[float]:
    s = s.strip().rstrip(".,;")
    s = re.sub(r"(\d),(\d)", r"\1.\2", s)
    try:
        return float(s)
    except ValueError:
        return None


def _walk_back_expression(text: str, end_exclusive: int) -> str:
    """Recorre `text` hacia atrás desde `end_exclusive` extrayendo la
    expresión aritmética inmediata. Se detiene al encontrar un carácter
    que no sea operador, dígito, paréntesis ni nombre de función conocida.

    Esto evita capturar texto narrativo previo como parte de la expresión.
    """
    i = end_exclusive - 1
    # Saltar espacios finales antes del operador
    while i >= 0 and text[i] in " \t":
        i -= 1
    end_inclusive = i

    while i >= 0:
        ch = text[i]
        if ch in _ARITH_CHARS_SET or ch in " \t":
            i -= 1
            continue
        if ch == "\n":
            break
        if ch.isalpha():
            # Intentar reconocer una función matemática que termine aquí
            matched = False
            for func in _FUNC_NAMES:
                start_idx = i + 1 - len(func)
                if start_idx >= 0 and text[start_idx:i + 1].lower() == func:
                    # Verificar frontera: char anterior no debe ser alfanumérico
                    boundary_ok = (
                        start_idx == 0
                        or not (text[start_idx - 1].isalpha() or text[start_idx - 1] == "_")
                    )
                    if boundary_ok:
                        i = start_idx - 1
                        matched = True
                        break
            if not matched:
                break
            continue
        break

    return text[i + 1:end_inclusive + 1].strip()


def verify_arithmetic(
    response_text: str,
    tolerance_pct: float = 0.5,
    max_findings: int = 5,
) -> List[ArithmeticFinding]:
    """Detecta cálculos en la respuesta y verifica su exactitud.

    Para cada `=` o `≈` en el texto:
      - Extrae el número que aparece a su derecha (`claimed`).
      - Camina hacia atrás extrayendo la expresión aritmética inmediata
        (dígitos, operadores, paréntesis y funciones matemáticas reconocidas
        — no captura texto narrativo previo).
      - Normaliza la expresión a sintaxis Python (sustituye ², ×, ÷, √, ^,
        notación LaTeX, etc.) y la evalúa con un evaluador AST seguro.
      - Si la diferencia relativa con `claimed` supera `tolerance_pct`,
        registra un hallazgo.

    Es deliberadamente conservador: si la expresión contiene variables sin
    valor, unidades no reconocidas o sintaxis ambigua, **no flagea**.
    Mejor falso negativo que falso positivo en demo.
    """
    findings: List[ArithmeticFinding] = []
    if not response_text:
        return findings

    # Preprocesado mínimo de LaTeX: convertir \approx en ≈ y \neq en !=,
    # quitar delimitadores \( \) y comandos \, \; \!. Mantenemos \frac y
    # \sqrt para que la normalización por expresión los maneje.
    response_text = response_text.replace(r"\approx", "≈")
    response_text = re.sub(r"\\(?:[,;!]|left|right)", " ", response_text)
    response_text = response_text.replace(r"\(", " ").replace(r"\)", " ")
    response_text = response_text.replace(r"\[", " ").replace(r"\]", " ")

    seen_exprs: set[str] = set()

    for m in _OP_PATTERN.finditer(response_text):
        if len(findings) >= max_findings:
            break
        op_pos = m.start()

        num_match = _RESULT_PATTERN.match(response_text, op_pos + 1)
        if not num_match:
            continue
        result_raw = num_match.group(1)

        expr_raw = _walk_back_expression(response_text, op_pos)
        if not expr_raw:
            continue

        normalized = _normalize_expr(expr_raw)
        if not normalized or normalized in seen_exprs:
            continue

        # Debe contener al menos un operador aritmético.
        if not re.search(r"[+\-*/]", normalized):
            continue

        # Tras quitar los nombres de función, no deben quedar letras
        # (eso indicaría variables sin valor o texto colado).
        residual = normalized
        for f in _FUNC_NAMES:
            residual = re.sub(rf"\b{f}\b", "", residual)
        if re.search(r"[a-zA-ZñÑ]", residual):
            continue

        computed = _safe_eval(normalized)
        if computed is None or not math.isfinite(computed):
            continue

        claimed = _parse_number(result_raw)
        if claimed is None or not math.isfinite(claimed):
            continue

        denom = max(abs(computed), 1e-6)
        rel_err = abs(computed - claimed) / denom * 100
        if rel_err <= tolerance_pct:
            continue

        seen_exprs.add(normalized)
        findings.append(
            ArithmeticFinding(
                expression=expr_raw,
                claimed=claimed,
                computed=computed,
                rel_error_pct=rel_err,
            )
        )

    return findings
