"""
AIMO Flask API — v3
────────────────────
3-stage pipeline:
  1. Context Agent  (aimo_answer.txt)           — multi-turn conversation
  2. Classifier     (aimo_classifier.txt)        — clinical risk assessment
  3. Recommendations (aimo_recommendations.txt) — final personalized output

Moderation (OpenAI omni-moderation-latest, free):
  Every AIMO response — intermediate and final — is checked before delivery.
  Categories blocked: self-harm/instructions, hate/threatening,
  harassment/threatening, violence/graphic.
  On trigger: safe fallback shown to student; incident logged in session record.

Per-turn evaluation (GPT-3.5-turbo) runs on every context-gathering turn.
Final evaluation (GPT-4) runs when recommendations are delivered (low/medium risk).
All sessions are persisted as JSON in data/sessions/ for academic analysis.

Endpoints:
  POST /api/chat   { "message": "...", "session_id": "..." }
                   → { "response": "...", "phase": "gathering|complete",
                       "evaluation": {...}|null,
                       "evaluacion_intermedia": {...}|null,
                       "classification": {...}|null,
                       "moderacion_activa": bool }

  POST /api/reset  { "session_id": "..." }
                   → { "ok": true }
"""

import json
import sys
import os
from dotenv import load_dotenv

from flask import Flask, request, jsonify
from flask_cors import CORS

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from src.agente_contexto        import obtener_contexto, _estimar_tokens
from src.agente_clasificador    import clasificar_riesgo
from src.agente_recomendaciones import generar_recomendaciones
from src.agente_evaluador       import evaluar_interaccion, evaluar_turno_contexto
from src.moderador              import moderar_salida, FALLBACK_MENSAJE
from src.session_store          import (
    crear_sesion, registrar_turno, finalizar_sesion, guardar_sesion,
)
from src.logger import get_logger

logger = get_logger("aimo.api")

# Maximum gathering turns before forcing the pipeline to advance to
# classification + recommendations. Keeps session length bounded and
# preserves a predictable UX. Mirrored in the frontend banner.
MAX_GATHERING_TURNS = 5

app = Flask(__name__)

CORS(app,
     origins=["http://localhost:3000", "http://localhost:5173",
              "https://aimo-amber.vercel.app", "https://aimo-production-c6ad.up.railway.app"],
     methods=["GET", "POST", "OPTIONS"],
     allow_headers=["Content-Type"])

# In-memory session state (pipeline data + academic record).
# {
#   "context_history": list | None,
#   "context_data":    dict | None,
#   "phase":           "gathering" | "complete",
#   "turn_count":      int,
#   "academic_record": dict,
# }
_sessions: dict = {}


def _construir_moderacion_record(es_segura: bool, categorias: list[str]) -> dict:
    return {"activo": not es_segura, "categorias": categorias}


@app.route("/api/chat", methods=["POST"])
def chat():
    data       = request.get_json(silent=True) or {}
    mensaje    = data.get("message", "").strip()
    session_id = data.get("session_id", "default")

    if not mensaje:
        return jsonify({"error": "El campo 'message' es obligatorio."}), 400

    if session_id not in _sessions:
        _sessions[session_id] = {
            "context_history": None,
            "context_data":    None,
            "phase":           "gathering",
            "turn_count":      0,
            "academic_record": crear_sesion(session_id),
        }

    session = _sessions[session_id]

    # ── Phase: complete ───────────────────────────────────────────────────────
    if session["phase"] == "complete":
        return jsonify({
            "response": (
                "Ya hemos completado nuestra conversación. "
                "Si deseas comenzar de nuevo, puedes reiniciar la sesión."
            ),
            "phase":                 "complete",
            "evaluation":            None,
            "evaluacion_intermedia": None,
            "classification":        None,
            "moderacion_activa":     False,
        })

    # ── Phase: gathering ──────────────────────────────────────────────────────
    session["turn_count"] += 1
    turno_num = session["turn_count"]
    logger.info("Sesión %s — turno %d", session_id, turno_num)

    tokens_antes = _estimar_tokens(session["context_history"] or [])

    visible_response, context_json, context_history = obtener_contexto(
        mensaje,
        session["context_history"],
        session["context_data"],
    )

    tokens_despues = _estimar_tokens(context_history)
    compresion = tokens_despues < tokens_antes and tokens_antes > 0

    session["context_history"] = context_history
    if context_json:
        session["context_data"] = context_json

    is_complete = bool(context_json and context_json.get("complete", False))

    # Hard cap: force completion when the gathering turn limit is reached,
    # even if the LLM did not mark complete=true. Bounds session cost and
    # matches the user-facing banner in the frontend.
    if not is_complete and turno_num >= MAX_GATHERING_TURNS:
        logger.info(
            "Cap de %d turnos alcanzado en sesión %s — forzando cierre",
            MAX_GATHERING_TURNS, session_id,
        )
        is_complete = True
        if session["context_data"] is None:
            session["context_data"] = context_json or {}
        if isinstance(session["context_data"], dict):
            session["context_data"]["complete"] = True

    # ── Moderation: intermediate response ────────────────────────────────────
    es_segura_inter, cats_inter = moderar_salida(visible_response)
    mod_record_inter = _construir_moderacion_record(es_segura_inter, cats_inter)

    if not es_segura_inter:
        logger.warning(
            "Moderación INTERMEDIA activada — turno %d, sesión %s, cats: %s",
            turno_num, session_id, cats_inter,
        )
        visible_response = FALLBACK_MENSAJE

    # ── Intermediate evaluation (GPT-3.5-turbo) ───────────────────────────────
    evaluacion_intermedia = None
    if es_segura_inter:
        # Only evaluate if the response was not replaced by the fallback
        try:
            evaluacion_intermedia = evaluar_turno_contexto(mensaje, visible_response, turno_num)
        except Exception as e:
            logger.warning("Evaluación intermedia falló en turno %d: %s", turno_num, e)

    # Register turn in academic record
    registrar_turno(
        record=session["academic_record"],
        numero_turno=turno_num,
        mensaje_usuario=mensaje,
        respuesta_agente=visible_response,
        context_snapshot=context_json,
        evaluacion_intermedia=evaluacion_intermedia,
        tokens_estimados=tokens_despues,
        compresion_activada=compresion,
        moderacion=mod_record_inter,
    )
    guardar_sesion(session["academic_record"])

    if not is_complete:
        _sessions[session_id] = session
        return jsonify({
            "response":              visible_response,
            "phase":                 "gathering",
            "evaluation":            None,
            "evaluacion_intermedia": evaluacion_intermedia,
            "classification":        None,
            "moderacion_activa":     not es_segura_inter,
        })

    # ── Context complete: classifier + recommendations ────────────────────────
    context_data = session["context_data"]

    clasificacion   = clasificar_riesgo(context_data)
    recomendaciones = generar_recomendaciones(context_data, clasificacion)

    # ── Moderation: final recommendations ────────────────────────────────────
    es_segura_final, cats_final = moderar_salida(recomendaciones)
    mod_record_final = _construir_moderacion_record(es_segura_final, cats_final)

    if not es_segura_final:
        logger.warning(
            "Moderación FINAL activada — sesión %s, cats: %s",
            session_id, cats_final,
        )
        recomendaciones = FALLBACK_MENSAJE

    # ── Final evaluation (GPT-4, low/medium risk, only if response safe) ─────
    evaluacion_final = None
    if clasificacion.get("risk_level") != "high" and es_segura_final:
        try:
            context_str       = json.dumps(
                {k: v for k, v in context_data.items() if k != 'complete'},
                ensure_ascii=False,
            )
            clasificacion_str = json.dumps(clasificacion, ensure_ascii=False)
            raw_eval = evaluar_interaccion(context_str, clasificacion_str, recomendaciones)

            if isinstance(raw_eval, dict):
                evaluacion_final = raw_eval
            elif isinstance(raw_eval, str):
                start = raw_eval.find("{")
                end   = raw_eval.rfind("}") + 1
                if start != -1 and end > start:
                    evaluacion_final = json.loads(raw_eval[start:end])
        except Exception as e:
            logger.error("Evaluación final fallida: %s", e)

    # Finalize and persist academic record
    finalizar_sesion(
        session["academic_record"],
        clasificacion,
        recomendaciones,
        evaluacion_final,
        moderacion_final=mod_record_final,
    )
    guardar_sesion(session["academic_record"])

    session["phase"] = "complete"
    _sessions[session_id] = session

    logger.info(
        "Sesión %s completada — risk=%s, composite=%s, mod_final=%s",
        session_id,
        clasificacion.get("risk_level"),
        (evaluacion_final or {}).get("composite_score"),
        not es_segura_final,
    )

    return jsonify({
        "response":              recomendaciones,
        "phase":                 "complete",
        "evaluation":            evaluacion_final,
        "evaluacion_intermedia": evaluacion_intermedia,
        "classification":        clasificacion,
        "moderacion_activa":     not es_segura_final,
    })


@app.route("/api/reset", methods=["POST"])
def reset():
    data       = request.get_json(silent=True) or {}
    session_id = data.get("session_id", "default")
    _sessions.pop(session_id, None)
    logger.info("Sesión %s reiniciada", session_id)
    return jsonify({"ok": True})


if __name__ == "__main__":
    print("═" * 50)
    print("  AIMO API v3 — http://localhost:5000")
    print("═" * 50)
    app.run(debug=True, port=5000)
