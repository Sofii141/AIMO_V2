/**
 * App — Componente raíz de AIMO.
 *
 * Gestiona el flujo de fases de la conversación, el historial de mensajes,
 * y los modales de investigación (AdminPanel, ThinkLog, RecommendationsModal).
 *
 * Fases:
 *   intro      — pausa inicial antes de habilitar el input
 *   user_turn  — esperando mensaje del usuario
 *   loading    — petición en curso al backend
 *   responding — AIMO escribiendo la respuesta (typewriter en chat)
 *   complete   — pipeline finalizado, input deshabilitado
 */
import { useState, useEffect, useRef } from "react";
import WorldBackground from "./components/WorldBackground";
import AimoCharacter from "./components/AimoCharacter";
import SpeechBubble from "./components/SpeechBubble";
import MessageItem from "./components/MessageItem";
import UserInput from "./components/UserInput";
import AdminPanel from "./components/AdminPanel";
import ThinkLog from "./components/ThinkLog";
import RecommendationsModal from "./components/RecommendationsModal";
import "./App.css";

const PHASES = {
  INTRO:    "intro",
  USER:     "user_turn",
  LOAD:     "loading",
  RESPOND:  "responding",
  COMPLETE: "complete",
};

const USE_API = true;

/** Tope de turnos de recolección — debe coincidir con MAX_GATHERING_TURNS en api.py */
const MAX_GATHERING_TURNS = 5;

/** Respuesta mock para desarrollo sin backend */
function mockResponse() {
  return {
    response:
      "Escucho que estás cargando algo que pesa. No tienes que enfrentarlo solo. ¿Qué es lo que sientes con más fuerza ahora mismo?",
    evaluation: {
      perspective_taking: {
        score: 4,
        justification:
          "El agente refleja el estado emocional del usuario de forma contextualizada.",
      },
      fantasy: {
        score: 3,
        justification: "La respuesta usa lenguaje empático funcional.",
      },
      empathic_concern: {
        score: 5,
        justification:
          '"No tienes que enfrentarlo solo" transmite calidez genuina.',
      },
      personal_distress: {
        score: 1,
        justification: "El agente mantiene compostura total.",
      },
    },
  };
}

export default function App() {
  // ── API Base URL ───────────────────────────────────────────────────────────
  const API_BASE = import.meta.env.VITE_API_URL || '';

  // ── Estado de la conversación ──────────────────────────────────────────────
  const [phase,          setPhase]          = useState(PHASES.INTRO);
  const [messages,       setMessages]       = useState([]);
  const [typingMsgIndex, setTypingMsgIndex] = useState(-1);

  // ── Estado de modales ──────────────────────────────────────────────────────
  const [adminOpen,        setAdminOpen]        = useState(false);
  const [thinkOpen,        setThinkOpen]        = useState(false);
  const [recsOpen,         setRecsOpen]         = useState(false);

  // ── Estado del pipeline (añadido por compañeros) ───────────────────────────
  /** Texto de las recomendaciones finales generadas al cerrar el pipeline */
  const [finalRecs,        setFinalRecs]        = useState(null);
  /** true cuando el backend indica que la conversación ha terminado */
  const [pipelineComplete, setPipelineComplete] = useState(false);

  // ── Refs ───────────────────────────────────────────────────────────────────
  const sessionId      = useRef(`s_${Date.now()}`);
  const convoBottomRef = useRef(null);

  // ── Efectos ────────────────────────────────────────────────────────────────
  useEffect(() => {
    // Pausa breve de intro; la burbuja de AIMO es estática, no necesita typewriter
    const t = setTimeout(() => setPhase(PHASES.USER), 600);
    return () => clearTimeout(t);
  }, []);

  useEffect(() => {
    // Only snap to bottom when a new user message is added.
    // AIMO's typing scroll is handled inside MessageItem (per character).
    convoBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  // ── Handlers ───────────────────────────────────────────────────────────────

  const handleSend = async (userMsg) => {
    setPhase(PHASES.LOAD);
    setMessages((prev) => [...prev, { role: "user", text: userMsg }]);

    try {
      let data;
      if (USE_API) {
        const res = await fetch(`${API_BASE}/api/chat`, {
          method:  "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message:    userMsg,
            session_id: sessionId.current,
          }),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        data = await res.json();
      } else {
        await new Promise((r) => setTimeout(r, 1800));
        data = mockResponse();
      }

      // Cuando el pipeline cierra (phase === "complete"), data.response contiene
      // las recomendaciones finales en Markdown. Esas se muestran en el modal,
      // no en el chat — el chat recibe solo una despedida corta.
      const pipelineDone = data.phase === "complete";
      const chatText = pipelineDone
        ? "He preparado un mensaje con lo que escuché y algunas ideas para ti. Ábrelo cuando quieras."
        : data.response;

      const newMsg = {
        role:           "aimo",
        text:           chatText,
        evaluation:     data.evaluation     ?? null,
        classification: data.classification ?? null,
        thinking:       data.thinking       ?? null,
      };

      setMessages((prev) => {
        const next = [...prev, newMsg];
        setTypingMsgIndex(next.length - 1);
        return next;
      });
      setPhase(PHASES.RESPOND);

      if (pipelineDone) {
        setFinalRecs(data.response ?? null);
        setPipelineComplete(true);
        if (data.response) setRecsOpen(true);
      }

    } catch (err) {
      console.error("[AIMO]", err);
      const errMsg =
        "¡Ups! Tuve un problema de conexión. ¿Puedes intentarlo de nuevo?";
      setMessages((prev) => {
        const next = [...prev, { role: "aimo", text: errMsg }];
        setTypingMsgIndex(next.length - 1);
        return next;
      });
      setPhase(PHASES.RESPOND);
    }
  };

  /** Llamado por MessageItem cuando termina su animación typewriter */
  const handleTypingDone = () => {
    setTypingMsgIndex(-1);
    setPhase(pipelineComplete ? PHASES.COMPLETE : PHASES.USER);
  };

  const handleReset = async () => {
    if (USE_API) {
      try {
        await fetch(`${API_BASE}/api/reset`, {
          method:  "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: sessionId.current }),
        });
      } catch (err) {
        console.error("[AIMO reset]", err);
      }
    }
    sessionId.current = `s_${Date.now()}`;
    setMessages([]);
    setTypingMsgIndex(-1);
    setFinalRecs(null);
    setPipelineComplete(false);
    setRecsOpen(false);
    setPhase(PHASES.USER);
  };

  const evalCount = messages.filter(
    (m) => m.role === "aimo" && m.evaluation,
  ).length;

  const isComplete = phase === PHASES.COMPLETE || pipelineComplete;

  // Turnos del usuario ya enviados (mensajes con role === "user").
  const userTurnsSent  = messages.filter((m) => m.role === "user").length;
  const turnsRemaining = Math.max(MAX_GATHERING_TURNS - userTurnsSent, 0);

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="game-root">
      <WorldBackground />

      {/* ── Header ── */}
      <header className="app-header">
        <div className="app-brand" aria-label="AIMO">
          <span className="brand-pixel" aria-hidden />
          <span className="brand-name">AIMO</span>
        </div>

        <div className="top-right-hud">
          <button
            className="hud-btn"
            onClick={handleReset}
            aria-label="Reiniciar conversación"
          >
            <span className="admin-icon">↺</span>
            <span className="admin-label">REINICIAR</span>
          </button>

          <button
            className="hud-btn"
            onClick={() => setThinkOpen(true)}
            aria-label="Cadena de pensamiento"
          >
            <span className="admin-icon">💭</span>
            <span className="admin-label">THINK</span>
          </button>

          <button
            className="hud-btn"
            onClick={() => setAdminOpen(true)}
            aria-label="Panel de métricas AERI"
          >
            <span className="admin-icon">⭐</span>
            <span className="admin-label">ADMIN</span>
            {evalCount > 0 && <span className="admin-badge">{evalCount}</span>}
          </button>
        </div>
      </header>

      {/* ── Main: columna AIMO + columna chat ── */}
      <main className="app-main">
        <section className={`character-col phase-${phase}`}>
          <div className="speech-wrap-aimo">
            <SpeechBubble phase={phase} />
          </div>
          <AimoCharacter phase={phase} />
          <p className="aimo-disclaimer">
            AIMO puede cometer errores. Sus respuestas son orientativas y no reemplazan la atención de un profesional de salud mental.
          </p>
        </section>

        <section className="chat-col">
          <div className="chat-title">
            <span className="chat-title-label">CONVERSACIÓN</span>
            <span className="chat-title-disclaimer">
              AIMO puede cometer errores · No reemplaza a un profesional
            </span>
          </div>
          {!isComplete && (
            <div className="chat-limit-banner" role="status">
              <span className="chat-limit-icon" aria-hidden>📌</span>
              <span className="chat-limit-text">
                Tienes <strong>{MAX_GATHERING_TURNS} mensajes</strong> para contarle a AIMO lo que sientes —
                {' '}cuéntale lo más importante (qué te pasa, cómo te afecta y desde cuándo) para que pueda
                acompañarte mejor.
              </span>
              <span className="chat-limit-counter" aria-label="Mensajes restantes">
                {turnsRemaining}/{MAX_GATHERING_TURNS}
              </span>
            </div>
          )}
          <div className="chat-scroll" role="log" aria-live="polite">
            {messages.length === 0 ? (
              <div className="chat-empty">AIMO está listo para escucharte.</div>
            ) : (
              messages.map((msg, i) => (
                <MessageItem
                  key={i}
                  message={msg}
                  isTyping={i === typingMsgIndex}
                  onTypingDone={
                    i === typingMsgIndex ? handleTypingDone : undefined
                  }
                />
              ))
            )}
            {phase === PHASES.LOAD && (
              <div className="msg-bubble-wrap wrap-aimo">
                <div className="msg-pixel-bubble bubble-aimo typing-indicator">
                  <span className="dot-pulse" />
                  <span className="dot-pulse" />
                  <span className="dot-pulse" />
                </div>
              </div>
            )}
            <div ref={convoBottomRef} />
          </div>
        </section>
      </main>

      {/* ── Footer: input del usuario ── */}
      <footer className="rpg-input-col">
        <UserInput
          enabled={phase === PHASES.USER}
          complete={isComplete}
          onSend={handleSend}
        />
        <p className="footer-disclaimer">
          AIMO puede cometer errores · No reemplaza a un profesional de salud mental
        </p>
      </footer>

      {/* ── Modales de investigación ── */}
      {thinkOpen && (
        <ThinkLog messages={messages} onClose={() => setThinkOpen(false)} />
      )}

      {adminOpen && (
        <AdminPanel messages={messages} onClose={() => setAdminOpen(false)} />
      )}

      {recsOpen && (
        <RecommendationsModal
          text={finalRecs}
          onClose={() => setRecsOpen(false)}
        />
      )}

      {/* Botón flotante para reabrir recomendaciones tras cerrar el modal */}
      {pipelineComplete && !recsOpen && (
        <button
          className="rec-reopen-btn"
          onClick={() => setRecsOpen(true)}
          aria-label="Ver recomendaciones"
        >
          ★ VER RECOMENDACIONES
        </button>
      )}
    </div>
  );
}