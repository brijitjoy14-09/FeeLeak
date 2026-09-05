import { useEffect, useState } from 'react'
import {
  AI_ACTION_META,
  AI_CLASSIFICATION_LABELS,
} from '../../constants/exceptions'
import { ApiError, getInvestigation, investigateException } from '../../services/api'

/**
 * AI investigation panel for an exception detail view.
 * AI output is advisory only — it never changes the exception here.
 */
function AiInvestigation({ exceptionId }) {
  const [investigation, setInvestigation] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    let active = true
    getInvestigation(exceptionId)
      .then((data) => {
        if (active) setInvestigation(data.investigation)
      })
      .catch((err) => {
        // 404 (no investigation yet) is expected; ignore it.
        if (active && !(err instanceof ApiError && err.code === 'INVESTIGATION_NOT_FOUND')) {
          setError(err)
        }
      })
    return () => {
      active = false
    }
  }, [exceptionId])

  async function runInvestigation() {
    setLoading(true)
    setError(null)
    try {
      const data = await investigateException(exceptionId)
      setInvestigation(data.investigation)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  const actionMeta = investigation
    ? AI_ACTION_META[investigation.recommended_action] ?? {
        label: investigation.recommended_action,
        tone: 'neutral',
      }
    : null

  return (
    <section className="ai-panel" aria-labelledby="ai-h">
      <div className="ai-head">
        <h3 id="ai-h">AI Investigation</h3>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={runInvestigation}
          disabled={loading}
        >
          {loading
            ? 'Analyzing…'
            : investigation
              ? 'Re-investigate'
              : 'Investigate Exception'}
        </button>
      </div>

      {loading && (
        <p className="ai-loading" role="status">
          Analyzing financial evidence…
        </p>
      )}

      {error && (
        <div className="upload-message msg-error" role="alert">
          <p>AI investigation could not be completed.</p>
          <p className="msg-detail">{error.message}</p>
        </div>
      )}

      {!loading && !investigation && !error && (
        <p className="ai-empty">No investigation has been performed.</p>
      )}

      {investigation && !loading && (
        <div className="ai-result">
          <div className="ai-grid">
            <div>
              <dt>Classification</dt>
              <dd>
                {AI_CLASSIFICATION_LABELS[investigation.classification] ??
                  investigation.classification}
              </dd>
            </div>
            <div>
              <dt>AI Confidence</dt>
              <dd>{investigation.confidence}%</dd>
            </div>
          </div>

          <div className="ai-block">
            <dt>Summary</dt>
            <dd>{investigation.summary}</dd>
          </div>
          <div className="ai-block">
            <dt>Root Cause</dt>
            <dd>{investigation.root_cause}</dd>
          </div>

          <div className="ai-recommendation">
            <span className="ai-rec-label">AI Recommendation</span>
            <span className={`status-badge badge-${actionMeta.tone}`}>
              {actionMeta.label}
            </span>
            <span className="ai-rec-reason">{investigation.reason}</span>
          </div>

          <div className="ai-block">
            <dt>Evidence Used</dt>
            <dd>
              {investigation.evidence.length === 0 ? (
                <span className="ai-muted">None cited.</span>
              ) : (
                <ul className="ai-evidence">
                  {investigation.evidence.map((item, index) => (
                    <li key={`${item.source}-${item.id}-${index}`}>
                      <span className="ai-ev-source">{item.source}</span>{' '}
                      <span className="mono">{item.id}</span>
                      {item.amount != null && (
                        <span className="ai-ev-amount"> · {item.amount}</span>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </dd>
          </div>

          <div className="ai-block">
            <dt>Missing Evidence</dt>
            <dd>
              {investigation.missing_evidence.length === 0 ? (
                <span className="ai-muted">None reported.</span>
              ) : (
                <ul className="ai-missing">
                  {investigation.missing_evidence.map((note, index) => (
                    <li key={index}>{note}</li>
                  ))}
                </ul>
              )}
            </dd>
          </div>

          <p className="ai-disclaimer">
            AI-generated investigation based on available financial evidence.
            Verify before resolving. This is AI confidence, not certainty.
          </p>
        </div>
      )}
    </section>
  )
}

export default AiInvestigation
