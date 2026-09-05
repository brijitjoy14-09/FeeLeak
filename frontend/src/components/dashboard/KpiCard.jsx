/**
 * Generic KPI card. Consumes already-formatted display strings so it stays
 * presentation-only and reusable for real API data later.
 *
 * Props:
 *  - label:    metric name (e.g. "Match Rate")
 *  - value:    formatted primary value (e.g. "92.4%")
 *  - support:  secondary line (e.g. "462 / 500 matched")
 *  - tone:     "neutral" | "success" | "warning" | "danger"
 *  - delta:    optional { text, direction: "up" | "down" }
 *  - progress: optional number 0–100 → renders a small bar
 *  - testId:   optional data-testid on the card root
 */
function KpiCard({
  label,
  value,
  support,
  tone = 'neutral',
  delta,
  progress,
  testId,
}) {
  return (
    <article className={`kpi-card tone-${tone}`} data-testid={testId}>
      <p className="kpi-label">{label}</p>
      <p className="kpi-value">{value}</p>

      {typeof progress === 'number' && (
        <div
          className="kpi-progress"
          role="progressbar"
          aria-valuenow={Math.round(progress)}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`${label} ${Math.round(progress)} percent`}
        >
          <span
            className="kpi-progress-fill"
            style={{ width: `${Math.min(Math.max(progress, 0), 100)}%` }}
          />
        </div>
      )}

      {delta && (
        <p className={`kpi-delta delta-${delta.direction}`}>
          <span aria-hidden="true">{delta.direction === 'down' ? '▾' : '▴'}</span>{' '}
          {delta.text}
        </p>
      )}

      {support && <p className="kpi-support">{support}</p>}
    </article>
  )
}

export default KpiCard
