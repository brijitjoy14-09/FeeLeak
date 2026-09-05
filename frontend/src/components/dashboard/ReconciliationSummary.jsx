import { formatNumber, formatPercent } from '../../utils/format'

/**
 * At-a-glance reconciliation state: a single proportional bar (matched vs.
 * exceptions, split into resolved/unresolved) plus labelled stat chips.
 */
function ReconciliationSummary({ summary }) {
  const { processed, matched, resolved, unresolved } = summary
  const exceptions = resolved + unresolved
  const pct = (part) => (processed > 0 ? (part / processed) * 100 : 0)

  const segments = [
    { key: 'matched', label: 'Matched', value: matched, tone: 'success' },
    { key: 'resolved', label: 'Resolved', value: resolved, tone: 'info' },
    { key: 'unresolved', label: 'Unresolved', value: unresolved, tone: 'danger' },
  ]

  const stats = [
    { label: 'Processed', value: processed, tone: 'neutral' },
    { label: 'Matched', value: matched, tone: 'success' },
    { label: 'Resolved', value: resolved, tone: 'info' },
    { label: 'Unresolved', value: unresolved, tone: 'danger' },
  ]

  return (
    <section className="panel recon-summary" aria-labelledby="recon-summary-h">
      <div className="panel-head">
        <h2 id="recon-summary-h" className="panel-title">
          Reconciliation Summary
        </h2>
        <span className="panel-sub">
          {formatPercent(pct(matched))} matched
        </span>
      </div>

      <div
        className="recon-bar"
        role="img"
        aria-label={`Of ${processed} processed records: ${matched} matched, ${resolved} resolved, ${unresolved} unresolved`}
      >
        {segments
          .filter((segment) => segment.value > 0)
          .map((segment) => (
            <span
              key={segment.key}
              className={`recon-seg seg-${segment.tone}`}
              style={{ width: `${pct(segment.value)}%` }}
            />
          ))}
      </div>

      <dl className="recon-stats">
        {stats.map((stat) => (
          <div key={stat.label} className={`recon-stat stat-${stat.tone}`}>
            <dt>{stat.label}</dt>
            <dd>{formatNumber(stat.value)}</dd>
          </div>
        ))}
      </dl>

      <p className="recon-foot">
        {formatNumber(exceptions)} exceptions raised from{' '}
        {formatNumber(processed)} processed records.
      </p>
    </section>
  )
}

export default ReconciliationSummary
