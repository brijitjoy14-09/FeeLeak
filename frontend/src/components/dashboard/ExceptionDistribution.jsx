import { formatPercent } from '../../utils/format'

// Donut chart of exception categories (dependency-free SVG).
const SIZE = 180
const STROKE = 26
const R = (SIZE - STROKE) / 2
const CIRC = 2 * Math.PI * R
const COLORS = [
  'var(--cat-1)',
  'var(--cat-2)',
  'var(--cat-3)',
  'var(--cat-4)',
  'var(--cat-5)',
  'var(--cat-6)',
]

function ExceptionDistribution({ distribution }) {
  const total = distribution.reduce((sum, d) => sum + d.count, 0)

  // Prefix-sum of preceding fractions gives each segment's start offset,
  // computed without mutating an outer variable during render.
  const segments = distribution.map((item, i) => {
    const fraction = total > 0 ? item.count / total : 0
    const precedingFraction = distribution
      .slice(0, i)
      .reduce((sum, d) => sum + (total > 0 ? d.count / total : 0), 0)
    return {
      ...item,
      color: COLORS[i % COLORS.length],
      pct: fraction * 100,
      dash: fraction * CIRC,
      offset: precedingFraction * CIRC,
    }
  })

  return (
    <section className="panel chart-panel" aria-labelledby="dist-h">
      <div className="panel-head">
        <h2 id="dist-h" className="panel-title">
          Exception Distribution
        </h2>
        <span className="panel-sub">{total} total</span>
      </div>

      <div className="donut-wrap">
        <svg
          className="donut-svg"
          viewBox={`0 0 ${SIZE} ${SIZE}`}
          role="img"
          aria-label={`Exception distribution across ${distribution.length} categories, ${total} total`}
        >
          <circle
            cx={SIZE / 2}
            cy={SIZE / 2}
            r={R}
            fill="none"
            stroke="var(--border)"
            strokeWidth={STROKE}
          />
          {segments
            .filter((seg) => seg.count > 0)
            .map((seg) => (
              <circle
                key={seg.category}
                cx={SIZE / 2}
                cy={SIZE / 2}
                r={R}
                fill="none"
                stroke={seg.color}
                strokeWidth={STROKE}
                strokeDasharray={`${seg.dash} ${CIRC - seg.dash}`}
                strokeDashoffset={-seg.offset}
                transform={`rotate(-90 ${SIZE / 2} ${SIZE / 2})`}
              />
            ))}
          <text x="50%" y="47%" className="donut-total">
            {total}
          </text>
          <text x="50%" y="61%" className="donut-caption">
            Exceptions
          </text>
        </svg>

        <ul className="donut-legend">
          {segments.map((seg) => (
            <li key={seg.category}>
              <span
                className="legend-swatch"
                style={{ background: seg.color }}
                aria-hidden="true"
              />
              <span className="legend-name">{seg.category}</span>
              <span className="legend-count">{seg.count}</span>
              <span className="legend-pct">{formatPercent(seg.pct)}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  )
}

export default ExceptionDistribution
