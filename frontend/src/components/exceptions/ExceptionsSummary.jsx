import { SEVERITY_META, EXCEPTION_TYPE_LABELS } from '../../constants/exceptions'
import { formatINR, formatNumber } from '../../utils/format'

const inr = (value) => formatINR(Number(value))

function DistributionBar({ title, data, metaLookup }) {
  const entries = Object.entries(data).filter(([, count]) => count > 0)
  const total = entries.reduce((sum, [, count]) => sum + count, 0)
  if (total === 0) {
    return (
      <div className="dist-block">
        <h3 className="dist-title">{title}</h3>
        <p className="dist-empty">No active exceptions.</p>
      </div>
    )
  }
  return (
    <div className="dist-block">
      <h3 className="dist-title">{title}</h3>
      <ul className="dist-list">
        {entries
          .sort((a, b) => b[1] - a[1])
          .map(([key, count]) => (
            <li key={key} className="dist-row">
              <span className="dist-label">{metaLookup(key)}</span>
              <span className="dist-track" aria-hidden="true">
                <span
                  className="dist-fill"
                  style={{ width: `${(count / total) * 100}%` }}
                />
              </span>
              <span className="dist-count">{count}</span>
            </li>
          ))}
      </ul>
    </div>
  )
}

function ExceptionsSummary({ summary }) {
  const cards = [
    { label: 'Open', value: formatNumber(summary.open), tone: 'warning' },
    { label: 'In Review', value: formatNumber(summary.in_review), tone: 'info' },
    { label: 'Escalated', value: formatNumber(summary.escalated), tone: 'danger' },
    { label: 'Resolved', value: formatNumber(summary.resolved), tone: 'success' },
    { label: 'Potential Leakage', value: inr(summary.potential_leakage), tone: 'danger' },
    { label: 'Affected Amount', value: inr(summary.total_affected_amount), tone: 'neutral' },
  ]

  return (
    <>
      <section className="exc-summary-grid" aria-label="Exception summary">
        {cards.map((card) => (
          <article key={card.label} className={`summary-card tone-${card.tone}`}>
            <p className="summary-value">{card.value}</p>
            <p className="summary-label">{card.label}</p>
          </article>
        ))}
      </section>

      <section className="panel dist-panel" aria-label="Distributions">
        <DistributionBar
          title="Severity (active)"
          data={summary.severity_distribution}
          metaLookup={(key) => SEVERITY_META[key]?.label ?? key}
        />
        <DistributionBar
          title="Exception Type (active)"
          data={summary.type_distribution}
          metaLookup={(key) => EXCEPTION_TYPE_LABELS[key] ?? key}
        />
      </section>
    </>
  )
}

export default ExceptionsSummary
