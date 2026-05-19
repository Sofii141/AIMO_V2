import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

/**
 * RecommendationsModal — Shows the final AIMO recommendations in a
 * scrollable, readable panel. Auto-opens when the pipeline completes.
 * Renders Markdown (headings, numbered lists, blockquote) returned by
 * the recommendations agent.
 */
export default function RecommendationsModal({ text, onClose }) {
  if (!text) return null

  return (
    <div className="rec-overlay" onClick={onClose}>
      <div className="rec-panel" onClick={e => e.stopPropagation()} role="dialog" aria-label="Recomendaciones de AIMO">

        <div className="rec-header">
          <span className="rec-title">★ RECOMENDACIONES DE AIMO</span>
          <button className="ap-close" onClick={onClose} aria-label="Cerrar">✕</button>
        </div>

        <div className="rec-body rec-markdown">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {text}
          </ReactMarkdown>
        </div>

        <div className="rec-footer">
          <span className="rec-footer-note">★ CONVERSACIÓN FINALIZADA — Reinicia para comenzar de nuevo</span>
        </div>

      </div>
    </div>
  )
}
