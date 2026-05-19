import { useState, useEffect, useRef } from 'react'

/**
 * AdminPanel — Research panel with two tabs:
 *   📊 MÉTRICAS  — AERI + G-Eval scores per turn
 *   🧠 EMOCIONES — Emotional classification per turn
 */

// ── Metrics tab ───────────────────────────────────────────────────────────────

const METRICS = [
  { key: 'perspective_taking', label: 'Perspective Taking', abbr: 'PT', cls: 'g', note: '',              invert: false },
  { key: 'empathic_concern',   label: 'Empathic Concern',   abbr: 'EC', cls: 'g', note: '',              invert: false },
  { key: 'fantasy',            label: 'Fantasy',            abbr: 'FT', cls: 'g', note: '',              invert: false },
  { key: 'personal_distress',  label: 'Personal Distress',  abbr: 'PD', cls: 'r', note: '↓ menor=mejor', invert: true  },
]

function ScoreBar({ score, cls, invert }) {
  const pct = invert ? ((6 - score) / 5) * 100 : (score / 5) * 100
  const ref = useRef(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.style.width = '0%'
    const id = requestAnimationFrame(() =>
      requestAnimationFrame(() => { el.style.width = `${pct}%` })
    )
    return () => cancelAnimationFrame(id)
  }, [pct])

  return (
    <div className="ap-bar-wrap">
      <div ref={ref} className={`ap-bar-fill ap-${cls}`} style={{ width: '0%' }} />
    </div>
  )
}

function EvalCard({ turn, evaluation, text }) {
  if (!evaluation) return null
  const composite = evaluation.composite_score ?? 'N/A'

  return (
    <div className="ap-card">
      <p className="ap-response-preview">
        <span className="ap-preview-label">AIMO:</span> {text.slice(0, 100)}{text.length > 100 ? '…' : ''}
      </p>

      <div className="ap-card-hdr">
        <span className="ap-turn">TURNO {turn}</span>
        <div className="ap-composite-wrap">
          <span className="ap-composite-label">◆ SCORE COMPUESTO</span>
          <span className="ap-composite-score">{composite}<span className="ap-den">/5</span></span>
        </div>
      </div>

      <div className="ap-formula-hint">
        Ponderado: PT×0.30 + EC×0.30 + (6−PD)×0.25 + FT×0.15
      </div>

      <div className="ap-metrics-list">
        {METRICS.map(({ key, label, abbr, cls, note, invert }) => {
          const m = evaluation[key]
          if (!m) return null
          return (
            <div className="ap-metric" key={key}>
              <div className="ap-metric-row">
                <span className={`ap-abbr ap-${cls}`}>{abbr}</span>
                <span className="ap-metric-label">{label}</span>
                <span className={`ap-score ap-${cls}`}>{m.score}<span className="ap-den">/5</span></span>
                {note && <span className="ap-note">{note}</span>}
              </div>
              <ScoreBar score={m.score} cls={cls} invert={invert} />
              <p className="ap-just">» {m.justification}</p>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ── Risk tab ──────────────────────────────────────────────────────────────────

const RISK_META = {
  low:    { cls: 'risk-low',    label: 'BAJO',  emoji: '🟢' },
  medium: { cls: 'risk-medium', label: 'MEDIO', emoji: '🟡' },
  high:   { cls: 'risk-high',   label: 'ALTO',  emoji: '🔴' },
}

const ACTION_META = {
  continue: { cls: 'action-continue', label: 'CONTINUAR' },
  caution:  { cls: 'action-caution',  label: 'PRECAUCIÓN' },
  escalate: { cls: 'action-escalate', label: 'ESCALAR' },
}

function RiskCard({ turn, classification, text }) {
  if (!classification) return null
  const { risk_level, signals = [], recommended_action } = classification
  const risk   = RISK_META[risk_level]   ?? RISK_META.medium
  const action = ACTION_META[recommended_action] ?? ACTION_META.caution

  return (
    <div className="ap-card">
      <p className="ap-response-preview">
        <span className="ap-preview-label">AIMO:</span> {text.slice(0, 100)}{text.length > 100 ? '…' : ''}
      </p>

      <div className="ap-card-hdr">
        <span className="ap-turn">TURNO {turn}</span>
        <span className={`em-badge ${action.cls}`}>{action.label}</span>
      </div>

      <div className="em-grid">
        <div className="em-field">
          <span className="em-label">NIVEL DE RIESGO</span>
          <span className={`em-badge ${risk.cls}`}>
            {risk.emoji} {risk.label}
          </span>
        </div>
      </div>

      {signals.length > 0 && (
        <div className="em-signals">
          <span className="em-label">SEÑALES DETECTADAS</span>
          <ul className="em-signals-list">
            {signals.map((s, i) => (
              <li key={i} className="em-signal-item">» {s}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

// ── Main panel ────────────────────────────────────────────────────────────────

export default function AdminPanel({ messages, onClose }) {
  const [activeTab, setActiveTab] = useState('metricas')

  const aimoMessages = messages.filter(m => m.role === 'aimo')

  const evals = aimoMessages
    .map((m, i) => ({ turn: i + 1, evaluation: m.evaluation, text: m.text }))
    .filter(e => e.evaluation)

  const risks = aimoMessages
    .map((m, i) => ({ turn: i + 1, classification: m.classification, text: m.text }))
    .filter(e => e.classification)

  return (
    <div className="ap-overlay" onClick={onClose}>
      <div className="ap-panel admin-panel" onClick={e => e.stopPropagation()} role="dialog" aria-label="Panel de métricas">
        <div className="ap-header">
          <span className="ap-title">⭐ PANEL ADMIN — INVESTIGACIÓN</span>
          <button className="ap-close" onClick={onClose} aria-label="Cerrar panel">✕</button>
        </div>

        {/* Tabs */}
        <div className="ap-tabs">
          <button
            className={`ap-tab${activeTab === 'metricas' ? ' ap-tab-active' : ''}`}
            onClick={() => setActiveTab('metricas')}
          >
            📊 MÉTRICAS {evals.length > 0 && `(${evals.length})`}
          </button>
          <button
            className={`ap-tab${activeTab === 'riesgo' ? ' ap-tab-active' : ''}`}
            onClick={() => setActiveTab('riesgo')}
          >
            🔎 RIESGO {risks.length > 0 && `(${risks.length})`}
          </button>
        </div>

        <div className="ap-body">

          {activeTab === 'metricas' && (
            <>
              <div className="ap-info-banner" style={{ marginTop: 0 }}>
                <span>📊 AERI (Lee &amp; Yi, 2023) · Relevance · Semantically Appropriate · Pesos: Davis (1980) + Abd-alrazaq (2019)</span>
              </div>

              <div className="ap-alert-box">
                <span className="ap-alert-title">¡Empathic Concern (EC) eliminada!</span>
                <p className="ap-alert-text">
                  La métrica <em>Semantically Appropriate</em> es su superconjunto — cubre calidez empática + seguridad psicológica + ausencia de positividad tóxica.
                </p>
              </div>

              {evals.length === 0 ? (
                <div className="ap-empty">
                  <span>⭐</span>
                  <p>No hay evaluaciones aún.<br />Conversa con AIMO para ver<br />las métricas aquí.</p>
                </div>
              ) : (
                evals.map(({ turn, evaluation, text }) => (
                  <EvalCard key={turn} turn={turn} evaluation={evaluation} text={text} />
                ))
              )}
            </>
          )}

          {activeTab === 'riesgo' && (
            <>
              <div className="ap-info-banner" style={{ marginTop: 0 }}>
                <span>🔎 Clasificación de riesgo clínico · SPRC (2014) · WHO-DAS (2010) · aimo_classifier</span>
              </div>

              {risks.length === 0 ? (
                <div className="ap-empty">
                  <span>🔎</span>
                  <p>La clasificación de riesgo<br />aparecerá al finalizar<br />la conversación.</p>
                </div>
              ) : (
                risks.map(({ turn, classification, text }) => (
                  <RiskCard key={turn} turn={turn} classification={classification} text={text} />
                ))
              )}
            </>
          )}

        </div>

      </div>
    </div>
  )
}