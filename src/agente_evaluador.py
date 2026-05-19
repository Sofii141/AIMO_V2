"""
G-Eval Evaluator — AIMO
────────────────────────
Two evaluation modes:

  1. evaluar_turno_contexto (GPT-3.5-turbo) — called on EVERY context-gathering
     turn.  Evaluates empathy, naturalness, and question quality.  Cheap and
     fast; designed for per-turn academic analysis without inflating costs.

  2. evaluar_interaccion (GPT-4) — called ONLY when final recommendations are
     delivered (low/medium risk).  Full AERI battery (PT, FT, EC, PD).

Model choice rationale:
  - GPT-3.5-turbo for intermediate turns: ~15x cheaper than GPT-4, sufficient
    for the simpler 3-criterion evaluation during context gathering.
  - GPT-4 for final evaluation: maximum judge quality for the composite score
    used in academic reporting.

Composite score weights (Xu & Jiang, 2024 — AERI):
  PT=30%, EC=30%, PD=25% (inverted), FT=15%
"""

import os
import json
import re
from src.config_api import get_openai_client
from src.logger import get_logger

logger = get_logger("aimo.evaluador")

OPENAI_EVAL_MODEL_FINAL       = "gpt-4"
OPENAI_EVAL_MODEL_INTERMEDIO  = "gpt-3.5-turbo"


# ── Shared helpers ────────────────────────────────────────────────────────────

def _load_prompt(filename: str) -> str:
    ruta = os.path.join(os.path.dirname(__file__), '..', 'prompts', filename)
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("No se encontró prompt: %s", filename)
        return ""


def _extract_json(raw: str) -> dict | None:
    if not raw:
        return None
    raw = re.sub(r'```(?:json)?', '', raw).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find('{')
        if start == -1:
            return None
        depth = 0
        for i, ch in enumerate(raw[start:], start):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(raw[start:i + 1])
                    except json.JSONDecodeError:
                        return None
    return None


def _call_evaluator(
    system_prompt: str,
    user_content: str,
    label: str,
    model: str,
) -> dict | None:
    try:
        client = get_openai_client()
    except RuntimeError as e:
        logger.warning("Evaluador omitido [%s]: %s", label, e)
        return None

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_content},
            ],
            temperature=0.1,
            max_tokens=400,
        )
        raw = completion.choices[0].message.content or ""
        logger.debug("[%s] raw → %.200s", label, raw)
        result = _extract_json(raw)
        if result:
            logger.info("[%s] score=%s", label, result.get("score") or result.get("score_promedio"))
        else:
            logger.warning("[%s] JSON no parseado", label)
        return result
    except Exception as e:
        logger.error("[%s] Error: %s", label, e)
        return None


# ── 1. Intermediate evaluator (GPT-3.5-turbo) ────────────────────────────────

def evaluar_turno_contexto(
    mensaje_usuario: str,
    respuesta_agente: str,
    numero_turno: int,
) -> dict | None:
    """
    Lightweight per-turn evaluation during context gathering.

    Uses GPT-3.5-turbo for cost efficiency (~15x cheaper than GPT-4).
    Evaluates: empathy, naturalness, question quality.

    Parameters
    ----------
    mensaje_usuario : str
        The student's message for this turn.
    respuesta_agente : str
        The context agent's visible response.
    numero_turno : int
        Turn number (for logging).

    Returns
    -------
    dict with empatia, naturalidad, adecuacion_pregunta (each with score +
    justificacion) and score_promedio, or None if evaluation unavailable.
    """
    system_prompt = _load_prompt("evaluador_contexto_v1.txt")
    if not system_prompt:
        return None

    user_content = (
        f"TURNO #{numero_turno}\n\n"
        f"MENSAJE DEL ESTUDIANTE:\n{mensaje_usuario}\n\n"
        f"RESPUESTA DEL ASISTENTE:\n{respuesta_agente}"
    )

    logger.info("Evaluando turno %d con %s", numero_turno, OPENAI_EVAL_MODEL_INTERMEDIO)
    result = _call_evaluator(
        system_prompt,
        user_content,
        f"contexto-turno-{numero_turno}",
        OPENAI_EVAL_MODEL_INTERMEDIO,
    )

    if result:
        # Compute score_promedio if not returned by model
        if "score_promedio" not in result:
            scores = [
                result.get("empatia", {}).get("score"),
                result.get("naturalidad", {}).get("score"),
                result.get("adecuacion_pregunta", {}).get("score"),
            ]
            valid = [s for s in scores if s is not None]
            result["score_promedio"] = round(sum(valid) / len(valid), 2) if valid else None

    return result


# ── 2. Final evaluator (GPT-4) ────────────────────────────────────────────────

def evaluar_interaccion(
    contexto_texto: str,
    clasificacion_texto: str,
    recomendaciones_texto: str = "",
) -> dict | None:
    """
    Full G-Eval battery using GPT-4.

    Called ONLY when final recommendations are generated (low/medium risk).

    Parameters
    ----------
    contexto_texto : str
        JSON string of the structured context from agente_contexto.
    clasificacion_texto : str
        JSON string of the risk classification from agente_clasificador.
    recomendaciones_texto : str
        Final recommendations text shown to the student.

    Returns
    -------
    dict with all metrics + composite_score, or None if all calls fail.
    """
    model_response = recomendaciones_texto or clasificacion_texto

    contenido_eval = (
        f"Contexto recopilado del estudiante:\n{contexto_texto}\n\n"
        f"Clasificación de riesgo psicológico:\n{clasificacion_texto}\n\n"
        f"Respuesta del asistente (recomendaciones mostradas al estudiante):\n{model_response}"
    )

    logger.info("Evaluación final AERI con %s", OPENAI_EVAL_MODEL_FINAL)

    aeri_prompt = _load_prompt('evaluador_v1.txt')
    aeri_result = _call_evaluator(aeri_prompt, contenido_eval, "AERI", OPENAI_EVAL_MODEL_FINAL)

    if not aeri_result:
        logger.warning("Evaluación final AERI no disponible")
        return None

    evaluation: dict = {}
    for key in ('perspective_taking', 'fantasy', 'empathic_concern', 'personal_distress'):
        if key in aeri_result:
            evaluation[key] = aeri_result[key]

    if not evaluation:
        logger.warning("Evaluación final AERI sin métricas válidas")
        return None

    # Composite score — AERI canonical 4-dimension weights
    METRIC_WEIGHTS = {
        "perspective_taking": 0.30,
        "empathic_concern":   0.30,
        "personal_distress":  0.25,  # inverted: (6 - score)
        "fantasy":             0.15,
    }

    pt  = evaluation.get('perspective_taking', {}).get('score')
    ft  = evaluation.get('fantasy',            {}).get('score')
    ec  = evaluation.get('empathic_concern',   {}).get('score')
    pd_ = evaluation.get('personal_distress',  {}).get('score')

    weighted_sum = 0.0
    total_weight = 0.0

    if pt is not None:
        weighted_sum += pt * METRIC_WEIGHTS["perspective_taking"]
        total_weight += METRIC_WEIGHTS["perspective_taking"]
    if ec is not None:
        weighted_sum += ec * METRIC_WEIGHTS["empathic_concern"]
        total_weight += METRIC_WEIGHTS["empathic_concern"]
    if pd_ is not None:
        weighted_sum += (6 - pd_) * METRIC_WEIGHTS["personal_distress"]
        total_weight += METRIC_WEIGHTS["personal_distress"]
    if ft is not None:
        weighted_sum += ft * METRIC_WEIGHTS["fantasy"]
        total_weight += METRIC_WEIGHTS["fantasy"]

    composite = round(weighted_sum / total_weight, 2) if total_weight > 0 else None
    evaluation['composite_score']  = composite
    evaluation['weighting_scheme'] = 'xu2024_aeri'

    logger.info("Composite score final: %s/5", composite)
    return evaluation
