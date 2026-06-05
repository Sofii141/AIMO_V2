"""
Session Store — AIMO (opt-in academic analysis)
────────────────────────────────────────────────
Builds an in-memory session record (per-turn evaluations, context object,
risk classification, final metrics). Writing that record to disk is OPT-IN
and DISABLED BY DEFAULT.

⚠️  Conversation data is NEVER written to disk in production. Persistence only
happens when the environment variable AIMO_PERSIST_SESSIONS is explicitly set
to a truthy value (1/true/yes/on) — intended solely for local academic
analysis. Production deployments leave this variable unset, so no sensitive
mental-health conversation content ever touches the filesystem.

When enabled, each session file: data/sessions/{session_id}.json

Schema overview:
  session_id              : str
  inicio                  : ISO timestamp
  fin                     : ISO timestamp (set on finalize)
  duracion_segundos       : int (set on finalize)
  total_turnos            : int
  fase_final              : "gathering" | "complete"
  moderacion_final_activo : bool — True if moderation triggered on final output
  turnos                  : list of turn records (see registrar_turno)
  clasificacion           : risk classification dict (set on finalize)
  recomendaciones         : final recommendations text (set on finalize)
  evaluacion_final        : G-Eval final metrics dict (set on finalize)
  metadata                : models used, flags, etc.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from src.logger import get_logger

logger = get_logger("aimo.session_store")

# Directory used ONLY when persistence is explicitly enabled. It is created
# lazily inside guardar_sesion(), never at import time, so production never
# creates an empty sessions directory on disk.
_SESSIONS_DIR = Path(__file__).parent.parent / "data" / "sessions"


def _persistence_enabled() -> bool:
    """True only when AIMO_PERSIST_SESSIONS is explicitly truthy.

    Defaults to False so that production (where the variable is unset) never
    persists any conversation data.
    """
    return os.getenv("AIMO_PERSIST_SESSIONS", "false").strip().lower() in (
        "1", "true", "yes", "on",
    )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _session_path(session_id: str) -> Path:
    safe_id = "".join(c for c in session_id if c.isalnum() or c in "-_")
    return _SESSIONS_DIR / f"{safe_id}.json"


def crear_sesion(session_id: str) -> dict:
    """Creates a new in-memory session record (not yet saved to disk)."""
    return {
        "session_id":               session_id,
        "inicio":                   _now_iso(),
        "fin":                      None,
        "duracion_segundos":        None,
        "total_turnos":             0,
        "fase_final":               "gathering",
        "moderacion_final_activo":  False,
        "turnos":                   [],
        "clasificacion":            None,
        "recomendaciones":          None,
        "evaluacion_final":         None,
        "metadata": {
            "modelos": {
                "contexto":             "llama-3.3-70b-versatile",
                "clasificador":         "llama-3.3-70b-versatile",
                "recomendaciones_low":  "llama-3.3-70b-versatile",
                "recomendaciones_med":  "bedrock/configured-via-env",
                "evaluador_intermedio": "gpt-3.5-turbo",
                "evaluador_final":      "gpt-4",
                "moderador":            "omni-moderation-latest",
            },
            "compresion_activada":             False,
            "evaluacion_intermedia_habilitada": True,
            "moderacion_habilitada":            True,
        },
    }


def registrar_turno(
    record: dict,
    numero_turno: int,
    mensaje_usuario: str,
    respuesta_agente: str,
    context_snapshot: dict | None,
    evaluacion_intermedia: dict | None,
    tokens_estimados: int,
    compresion_activada: bool = False,
    moderacion: dict | None = None,
) -> None:
    """
    Appends a turn entry to the session record (in-place).

    moderacion, when provided, should be:
      {"activo": bool, "categorias": list[str]}
      activo=True means moderation triggered and fallback was shown.
    """
    if compresion_activada:
        record["metadata"]["compresion_activada"] = True

    turno = {
        "numero":                numero_turno,
        "timestamp":             _now_iso(),
        "fase":                  "gathering",
        "usuario":               mensaje_usuario,
        "asistente":             respuesta_agente,
        "context_snapshot":      context_snapshot,
        "evaluacion_intermedia": evaluacion_intermedia,
        "tokens_estimados":      tokens_estimados,
        "moderacion":            moderacion,
    }
    record["turnos"].append(turno)
    record["total_turnos"] = len(record["turnos"])


def finalizar_sesion(
    record: dict,
    clasificacion: dict | None,
    recomendaciones: str | None,
    evaluacion_final: dict | None,
    moderacion_final: dict | None = None,
) -> None:
    """
    Marks the session as complete and sets final fields (in-place).

    moderacion_final, when provided:
      {"activo": bool, "categorias": list[str]}
    """
    fin = _now_iso()
    inicio_dt = datetime.fromisoformat(record["inicio"])
    fin_dt    = datetime.fromisoformat(fin)
    duracion  = int((fin_dt - inicio_dt).total_seconds())

    record["fin"]               = fin
    record["duracion_segundos"] = duracion
    record["fase_final"]        = "complete"
    record["clasificacion"]     = clasificacion
    record["recomendaciones"]   = recomendaciones
    record["evaluacion_final"]  = evaluacion_final

    if moderacion_final:
        record["moderacion_final_activo"] = moderacion_final.get("activo", False)
        record["moderacion_final_detalle"] = moderacion_final


def guardar_sesion(record: dict) -> None:
    """Writes the session record to disk as JSON — ONLY when persistence is
    explicitly enabled via AIMO_PERSIST_SESSIONS.

    In production the variable is unset, so this is a no-op and no conversation
    data is ever written to disk.
    """
    if not _persistence_enabled():
        logger.debug(
            "Persistencia deshabilitada — sesión %s no se guarda en disco",
            record.get("session_id"),
        )
        return

    _SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = _session_path(record["session_id"])
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        logger.info("Sesión guardada: %s (%d turnos)", path.name, record["total_turnos"])
    except Exception as e:
        logger.error("Error guardando sesión %s: %s", record["session_id"], e)
