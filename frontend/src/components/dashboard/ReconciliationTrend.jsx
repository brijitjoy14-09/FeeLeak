import { formatPercent } from '../../utils/format'

// Lightweight, dependency-free SVG combo chart:
//   bars  = records processed per bucket
//   line  = match rate (%) per bucket
const W = 640
const H = 260
const PAD = { top: 24, right: 16, bottom: 34, left: 16 }

function niceMax(value) {
  if (value <= 0) return 10
  const step = Math.pow(10, Math.floor(Math.log10(value)))
  return Math.ceil(value / step) * step
}

function ReconciliationTrend({ trend }) {
  const plotW = W - PAD.left - PAD.right
  const plotH = H - PAD.top - PAD.bottom
  const n = trend.length
  const slot = plotW / Math.max(n, 1)
  const barW = Math.min(slot * 0.5, 44)

  const maxRecords = niceMax(Math.max(...trend.map((d) => d.records), 0))
  const yFor = (records) => PAD.top + plotH * (1 - records / maxRecords)

  // Match rate mapped onto a zoomed band so the line reads clearly.
  const rates = trend.map((d) => d.matchRate).filter((r) => r > 0)
  const rMin = Math.min(80, ...(rates.length ? rates : [80]))
  const rMax = 100
  const yForRate = (rate) =>
    PAD.top + plotH * (1 - (rate - rMin) / (rMax - rMin))

  const linePoints = trend
    .map((d, i) => `${PAD.left + slot * i + slot / 2},${yForRate(d.matchRate)}`)
    .join(' ')

  const avgRate =
    rates.reduce((sum, r) => sum + r, 0) / Math.max(rates.length, 1)

  return (
    <section className="panel chart-panel" aria-labelledby="trend-h">
      <div className="panel-head">
        <h2 id="trend-h" className="panel-title">
          Reconciliation Trend
        </h2>
        <span className="panel-sub">
          Avg match rate {formatPercent(avgRate)}
        </span>
      </div>

      <div className="chart-legend">
        <span className="legend-item">
          <span className="legend-swatch swatch-bar" aria-hidden="true" />
          Records processed
        </span>
        <span className="legend-item">
          <span className="legend-swatch swatch-line" aria-hidden="true" />
          Match rate
        </span>
      </div>

      <svg
        className="chart-svg"
        viewBox={`0 0 ${W} ${H}`}
        role="img"
        aria-label="Records processed per period with match rate overlay"
        preserveAspectRatio="xMidYMid meet"
      >
        {/* baseline */}
        <line
          x1={PAD.left}
          y1={PAD.top + plotH}
          x2={W - PAD.right}
          y2={PAD.top + plotH}
          className="chart-axis"
        />

        {trend.map((d, i) => {
          const x = PAD.left + slot * i + slot / 2
          const y = yFor(d.records)
          return (
            <g key={d.label}>
              <rect
                x={x - barW / 2}
                y={y}
                width={barW}
                height={PAD.top + plotH - y}
                rx="4"
                className="chart-bar"
              />
              <text x={x} y={y - 6} className="chart-bar-value">
                {d.records}
              </text>
              <text
                x={x}
                y={H - 12}
                className="chart-x-label"
              >
                {d.label}
              </text>
            </g>
          )
        })}

        {/* match-rate line + points */}
        <polyline points={linePoints} className="chart-line" />
        {trend.map((d, i) => (
          <circle
            key={`pt-${d.label}`}
            cx={PAD.left + slot * i + slot / 2}
            cy={yForRate(d.matchRate)}
            r="3.5"
            className="chart-line-dot"
          />
        ))}
      </svg>
    </section>
  )
}

export default ReconciliationTrend
