"""
AIMO CLI Tester — v2
──────────────────────
Interactive test environment for the v2 3-stage pipeline.

Modes:
  1. Chat libre     — multi-turn conversation through the full pipeline
  2. Modo pruebas   — automated run of scenarios from data/escenarios_prueba.json
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(__file__))

from src.agente_contexto        import obtener_contexto
from src.agente_clasificador    import clasificar_riesgo
from src.agente_recomendaciones import generar_recomendaciones
from src.agente_evaluador       import evaluar_turno_contexto, evaluar_interaccion
from src.session_store          import (
    crear_sesion, registrar_turno, finalizar_sesion, guardar_sesion,
)


def _estimar_tokens_local(historial):
    return sum(len(m.get("content", "")) for m in historial) // 4


def _mostrar_evaluacion_intermedia(ev: dict | None, turno: int) -> None:
    if not ev:
        return
    print(f"\n  [Eval turno {turno}]")
    print(f"    Empatía:    {ev.get('empatia', {}).get('score', '?')}/5 — {ev.get('empatia', {}).get('justificacion', '')}")
    print(f"    Naturalidad:{ev.get('naturalidad', {}).get('score', '?')}/5 — {ev.get('naturalidad', {}).get('justificacion', '')}")
    print(f"    Pregunta:   {ev.get('adecuacion_pregunta', {}).get('score', '?')}/5 — {ev.get('adecuacion_pregunta', {}).get('justificacion', '')}")
    print(f"    Promedio:   {ev.get('score_promedio', '?')}/5")


def _mostrar_evaluacion_final(ev: dict | None) -> None:
    if not ev:
        print("\n  [Evaluación final no disponible]")
        return
    print("\n  [Evaluación final G-Eval GPT-4]")
    for key in ('perspective_taking', 'empathic_concern', 'fantasy', 'personal_distress'):
        item = ev.get(key, {})
        print(f"    {key}: {item.get('score', '?')}/5")
    print(f"    Composite: {ev.get('composite_score', '?')}/5")


def modo_chat():
    print("\n" + "*" * 60)
    print("MODO CHAT LIBRE — pipeline v2 completo")
    print("Escribe 'salir' para volver al menú.")
    print("*" * 60)

    historial     = None
    context_data  = None
    turno_num     = 0
    session_id    = "cli-chat"
    record        = crear_sesion(session_id)

    while True:
        user_input = input("\nTú: ").strip()
        if user_input.lower() in ('salir', 'exit', 'quit'):
            break

        turno_num += 1
        tokens_antes = _estimar_tokens_local(historial or [])

        visible, context_json, historial = obtener_contexto(
            user_input, historial, context_data,
        )

        tokens_despues = _estimar_tokens_local(historial)
        compresion = tokens_despues < tokens_antes and tokens_antes > 0

        if context_json:
            context_data = context_json

        print(f"\nAIMO: {visible}")

        # Intermediate evaluation
        ev_intermedia = evaluar_turno_contexto(user_input, visible, turno_num)
        _mostrar_evaluacion_intermedia(ev_intermedia, turno_num)

        registrar_turno(
            record, turno_num, user_input, visible,
            context_json, ev_intermedia, tokens_despues, compresion,
        )
        guardar_sesion(record)

        is_complete = bool(context_json and context_json.get("complete", False))
        if is_complete:
            print("\n" + "=" * 60)
            print("Contexto completo — ejecutando clasificación y recomendaciones...")
            print("=" * 60)

            clasificacion   = clasificar_riesgo(context_data)
            recomendaciones = generar_recomendaciones(context_data, clasificacion)

            print(f"\n[Clasificación] risk_level={clasificacion.get('risk_level')}")
            print(f"\nAIMO (recomendaciones):\n{recomendaciones}")

            ev_final = None
            if clasificacion.get("risk_level") != "high":
                context_str       = json.dumps(
                    {k: v for k, v in context_data.items() if k != 'complete'},
                    ensure_ascii=False,
                )
                clasificacion_str = json.dumps(clasificacion, ensure_ascii=False)
                ev_final = evaluar_interaccion(context_str, clasificacion_str, recomendaciones)
            _mostrar_evaluacion_final(ev_final)

            finalizar_sesion(record, clasificacion, recomendaciones, ev_final)
            guardar_sesion(record)
            break


def modo_pruebas():
    ruta_json = os.path.join(os.path.dirname(__file__), 'data', 'escenarios_prueba.json')
    try:
        with open(ruta_json, 'r', encoding='utf-8') as f:
            escenarios = json.load(f)
    except FileNotFoundError:
        print(f"No se encontró {ruta_json}")
        return

    print("\n" + "*" * 60)
    print(f"MODO PRUEBAS — {len(escenarios)} escenarios")
    print("*" * 60)

    for escenario in escenarios:
        print(f"\n▶  ESCENARIO {escenario['id_escenario']}: {escenario['estado_emocional']}")
        texto = escenario['texto_usuario']
        print(f"Usuario simulado: {texto}")

        session_id = f"test-{escenario['id_escenario']}"
        record     = crear_sesion(session_id)

        # Single-turn context test (escenarios are single messages)
        visible, context_json, historial = obtener_contexto(texto, None, None)
        print(f"\nAIMO: {visible}")

        ev_intermedia = evaluar_turno_contexto(texto, visible, 1)
        _mostrar_evaluacion_intermedia(ev_intermedia, 1)

        registrar_turno(record, 1, texto, visible, context_json, ev_intermedia,
                        _estimar_tokens_local(historial))
        guardar_sesion(record)

        input("\nPresiona ENTER para el siguiente escenario (Ctrl+C para salir)...")


def menu_principal():
    while True:
        print("\n" + "=" * 60)
        print("PROYECTO AIMO — ENTORNO DE PRUEBAS v2.0")
        print("=" * 60)
        print("1. Modo Chat Libre (pipeline v2 multi-turno)")
        print("2. Modo Pruebas (escenarios_prueba.json)")
        print("3. Salir")
        print("=" * 60)

        opcion = input("Elige una opción (1/2/3): ").strip()
        if opcion == '1':
            modo_chat()
        elif opcion == '2':
            modo_pruebas()
        elif opcion == '3':
            print("\nCerrando entorno de pruebas.")
            break
        else:
            print("Opción no válida.")


if __name__ == "__main__":
    menu_principal()
