import { useEffect, useState } from 'react'
import {
  EXCEPTION_STATUS_META,
  EXCEPTION_TYPE_LABELS,
  NEXT_ACTIONS,
  NOTE_LABELS,
  RISK_LEVEL_META,
  SEVERITY_META,
} from '../../constants/exceptions'
import {
  getExceptionAudit,
  getReconciliationResult,
  updateExceptionStatus,
} from '../../services/api'
import { formatINR } from '../../utils/format'
import AiInvestigation from './AiInvestigation'

const inr = (value) => (value == null ? '—' : formatINR(Number(value)))

function Badge({ meta }) {
  return <span className={`status-badge badge-${meta.tone}`}>{meta.label}</span>
}

function ExceptionDetail({ exception, onClose, onUpdated }) {
  const [current, setCurrent] = useState(exception)
  const [recon, setRecon] = useState(null)
  const [audit, setAudit] = useState([])
  const [pending, setPending] = useState(null) // action object requiring a note
  const [note, setNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const loadAudit = () =>
    getExceptionAudit(current.exception_id)
      .then((data) => setAudit(data.events))
      .catch(() => setAudit([]))

  useEffect(() => {
    let active = true
    if (exception.payment_id) {
      getReconciliationResult(exception.payment_id)
        .then((data) => {
          if (active) setRecon(data)
        })
        .catch(() => {
          // Orphan payments have no reconciliation result; fall back to fields.
        })
    }
    getExceptionAudit(exception.exception_id)
      .then((data) => active && setAudit(data.events))
      .catch(() => active && setAudit([]))
    return () => {
      active = false
    }
  }, [exception.payment_id, exception.exception_id])

  async function applyStatus(status, noteText) {
    setBusy(true)
    setError(null)
    try {
      const updated = await updateExceptionStatus(current.exception_id, {
        status,
        note: noteText,
      })
      setCurrent(updated)
      setPending(null)
      setNote('')
      loadAudit()
      onUpdated?.()
    } catch (err) {
      setError(err)
    } finally {
      setBusy(false)
    }
  }

  function handleAction(action) {
    setError(null)
    if (action.requiresNote) {
      setPending(action)
      setNote('')
    } else {
      applyStatus(action.status)
    }
  }

  const actions = NEXT_ACTIONS[current.status] ?? []
  const statusMeta =
    EXCEPTION_STATUS_META[current.status] ?? { label: current.status, tone: 'neutral' }
  const severityMeta =
    SEVERITY_META[current.severity] ?? { label: current.severity, tone: 'neutral' }
  const riskMeta =
    RISK_LEVEL_META[current.risk_level] ?? { label: current.risk_level, tone: 'neutral' }

  return (
    <div
      className="detail-backdrop"
      role="dialog"
      aria-modal="true"
      aria-label={`Exception ${current.exception_id}`}
    >
      <div className="detail-panel exc-detail">
        <div className="detail-head">
          <div>
            <h3 className="mono">{current.exception_id}</h3>
            <p className="exc-detail-sub">
              {EXCEPTION_TYPE_LABELS[current.type] ?? current.type}
            </p>
          </div>
          <button type="button" className="btn btn-link" onClick={onClose} aria-label="Close details">
            Close
          </button>
        </div>

        <div className="exc-badges">
          <Badge meta={statusMeta} />
          <Badge meta={severityMeta} />
          <span
            className={`status-badge badge-${riskMeta.tone}`}
            title={(current.risk_drivers || []).join(' · ')}
          >
            Risk {current.risk_score} · {riskMeta.label}
          </span>
          <span className="exc-priority">Payment: {current.payment_id ?? '—'}</span>
          <span className="exc-priority">Order: {current.order_id ?? '—'}</span>
        </div>

        {current.risk_drivers && current.risk_drivers.length > 0 && (
          <p className="risk-drivers">
            Risk drivers: {current.risk_drivers.join(' · ')}
          </p>
        )}

        <p className="exc-description">{current.description}</p>

        {/* Deterministic financial evidence (never recomputed here) */}
        <div className="calc">
          {recon ? (
            <>
              <div className="calc-row"><span>Payment</span><span>{inr(recon.payment_amount)}</span></div>
              <div className="calc-row"><span>− Refunds ({recon.refund_count})</span><span>{inr(recon.total_refund)}</span></div>
              <div className="calc-row"><span>− Fees ({recon.fee_count})</span><span>{inr(recon.total_fee)}</span></div>
              <div className="calc-row"><span>− Taxes</span><span>{inr(recon.total_tax)}</span></div>
              <div className="calc-row calc-total"><span>Expected Settlement</span><span>{inr(recon.expected_settlement)}</span></div>
              <div className="calc-row"><span>Actual Settlement ({recon.settlement_count})</span><span>{inr(recon.actual_settlement)}</span></div>
              <div className="calc-row calc-diff"><span>Difference</span><span>{inr(recon.difference)}</span></div>
            </>
          ) : (
            <>
              <div className="calc-row"><span>Expected</span><span>{inr(current.expected_amount)}</span></div>
              <div className="calc-row"><span>Actual</span><span>{inr(current.actual_amount)}</span></div>
              <div className="calc-row calc-diff"><span>Difference</span><span>{inr(current.difference)}</span></div>
              <div className="calc-row"><span>Affected Amount</span><span>{inr(current.affected_amount)}</span></div>
            </>
          )}
          <div className="calc-row calc-leak">
            <span>Potential Leakage</span>
            <span>{inr(current.potential_leakage)}</span>
          </div>
        </div>

        {/* Review actions */}
        <div className="review-actions">
          {actions.length === 0 ? (
            <p className="ai-muted">This exception is resolved. No further actions.</p>
          ) : (
            actions.map((action) => (
              <button
                key={action.status}
                type="button"
                className={`btn btn-${action.tone}`}
                onClick={() => handleAction(action)}
                disabled={busy}
              >
                {action.label}
              </button>
            ))
          )}
        </div>

        {current.reviewed_by && (
          <p className="review-meta">
            <strong>Human decision</strong> · last updated by {current.reviewed_by}
            {current.resolution ? ` · Resolution: ${current.resolution}` : ''}
            {current.escalation_reason ? ` · Reason: ${current.escalation_reason}` : ''}
            {current.rejection_reason ? ` · Rejected: ${current.rejection_reason}` : ''}
          </p>
        )}

        {pending && (
          <div className="note-dialog">
            <label htmlFor="review-note">
              {NOTE_LABELS[pending.requiresNote] ?? 'Reason (required)'}
            </label>
            <textarea
              id="review-note"
              rows={3}
              value={note}
              onChange={(event) => setNote(event.target.value)}
              placeholder="Explain your decision…"
            />
            <div className="note-actions">
              <button type="button" className="btn btn-secondary" onClick={() => setPending(null)} disabled={busy}>
                Cancel
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => applyStatus(pending.status, note)}
                disabled={busy || note.trim().length === 0}
              >
                {busy ? 'Saving…' : `Confirm ${pending.label}`}
              </button>
            </div>
          </div>
        )}

        {error && (
          <div className="upload-message msg-error" role="alert">
            <p>{error.message}</p>
          </div>
        )}

        <AiInvestigation exceptionId={current.exception_id} />

        <section className="audit-panel" aria-labelledby="audit-h">
          <h3 id="audit-h">Audit History</h3>
          {audit.length === 0 ? (
            <p className="ai-muted">No audit events yet.</p>
          ) : (
            <ul className="audit-list">
              {audit.map((event) => (
                <li key={event.audit_id} className="audit-item">
                  <span className="audit-type">{event.event_type.replace(/_/g, ' ')}</span>
                  <span className="audit-actor">{event.actor}</span>
                  {event.detail && <span className="audit-detail">{event.detail}</span>}
                  {event.reason && <span className="audit-reason">“{event.reason}”</span>}
                  <span className="audit-time">{event.timestamp?.slice(0, 19).replace('T', ' ')}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  )
}

export default ExceptionDetail
