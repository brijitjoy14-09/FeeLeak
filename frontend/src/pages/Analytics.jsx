import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import './Analytics.css'
import {
  EXCEPTION_TYPE_LABELS,
  RISK_LEVEL_META,
} from '../constants/exceptions'
import {
  getAnalyticsInsight,
  getAnalyticsSummary,
  getExceptionDistribution,
  getLeakageTrend,
  getRiskPriorities,
} from '../services/api'
import { formatINR, formatNumber, formatPercent } from '../utils/format'

const inr = (value) => formatINR(Number(value))

// ---- Leakage trend (dependency-free SVG line + area) ----------------------
function LeakageTrend({ trend }) {
  if (!trend?.available || !trend.data?.length) {
    return (
      <section className="panel" aria-labelledby="trend-h">
        <div className="panel-head">
          <h2 id="trend-h" className="panel-title">Leakage Trend</h2>
        </div>
        <p className="an-empty">
          {trend?.message ?? 'Trend data unavailable for the current data.'}
        </p>
      </section>
    )
  }

  const W = 640
  const H = 240
  const PAD = { t: 20, r: 16, b: 34, l: 56 }
  const points = trend.data.map((d) => ({ date: d.date, value: Number(d.potential_leakage) }))
  const max = Math.max(...points.map((p) => p.value), 1)
  const plotW = W - PAD.l - PAD.r
  const plotH = H - PAD.t - PAD.b
  const x = (i) => PAD.l + (points.length === 1 ? plotW / 2 : (plotW * i) / (points.length - 1))
  const y = (v) => PAD.t + plotH * (1 - v / max)
  const line = points.map((p, i) => `${x(i)},${y(p.value)}`).join(' ')
  const area = `${PAD.l},${PAD.t + plotH} ${line} ${x(points.length - 1)},${PAD.t + plotH}`

  return (
    <section className="panel" aria-labelledby="trend-h">
      <div className="panel-head">
        <h2 id="trend-h" className="panel-title">Leakage Trend</h2>
        <span className="panel-sub">Potential leakage per day</span>
      </div>
      <svg className="chart-svg" viewBox={`0 0 ${W} ${H}`} role="img"
        aria-label="Potential leakage over time">
        <line x1={PAD.l} y1={PAD.t + plotH} x2={W - PAD.r} y2={PAD.t + plotH} className="chart-axis" />
        <polygon points={area} className="trend-area" />
        <polyline points={line} className="trend-line" />
        {points.map((p, i) => (
          <g key={p.date}>
            <circle cx={x(i)} cy={y(p.value)} r="3.5" className="trend-dot">
              <title>{`${p.date}: ${inr(p.value)}`}</title>
            </circle>
            <text x={x(i)} y={H - 12} className="chart-x-label">{p.date.slice(5)}</text>
          </g>
        ))}
        <text x={PAD.l - 8} y={y(max)} className="chart-y-label">{inr(max)}</text>
        <text x={PAD.l - 8} y={PAD.t + plotH} className="chart-y-label">₹0</text>
      </svg>
    </section>
  )
}

// ---- Financial impact by classification (horizontal bars) -----------------
function ImpactChart({ distribution }) {
  const data = distribution?.data ?? []
  if (data.length === 0) {
    return (
      <section className="panel" aria-labelledby="impact-h">
        <div className="panel-head"><h2 id="impact-h" className="panel-title">Financial Impact</h2></div>
        <p className="an-empty">No financial exceptions match the selected filters.</p>
      </section>
    )
  }
  const max = Math.max(...data.map((d) => Number(d.amount)), 1)
  return (
    <section className="panel" aria-labelledby="impact-h">
      <div className="panel-head">
        <h2 id="impact-h" className="panel-title">Financial Impact by Classification</h2>
      </div>
      <ul className="impact-list">
        {data.map((d) => (
          <li key={d.classification} className="impact-row">
            <span className="impact-label">
              {EXCEPTION_TYPE_LABELS[d.classification] ?? d.classification}
            </span>
            <span className="impact-track" aria-hidden="true">
              <span className="impact-fill" style={{ width: `${(Number(d.amount) / max) * 100}%` }} />
            </span>
            <span className="impact-amount">{inr(d.amount)}</span>
            <span className="impact-count">{d.count}×</span>
          </li>
        ))}
      </ul>
    </section>
  )
}

function Analytics() {
  const navigate = useNavigate()
  const [summary, setSummary] = useState(null)
  const [trend, setTrend] = useState(null)
  const [distribution, setDistribution] = useState(null)
  const [risks, setRisks] = useState(null)
  const [insight, setInsight] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    Promise.allSettled([
      getAnalyticsSummary(),
      getLeakageTrend(),
      getExceptionDistribution(),
      getRiskPriorities({ limit: 10 }),
      getAnalyticsInsight(),
    ]).then(([s, t, d, r, i]) => {
      if (!active) return
      if (s.status === 'fulfilled') setSummary(s.value)
      else setError(s.reason)
      if (t.status === 'fulfilled') setTrend(t.value)
      if (d.status === 'fulfilled') setDistribution(d.value)
      if (r.status === 'fulfilled') setRisks(r.value)
      if (i.status === 'fulfilled') setInsight(i.value)
      setLoading(false)
    })
    return () => {
      active = false
    }
  }, [])

  const cards = summary
    ? [
        { label: 'Transactions Processed', value: formatNumber(summary.transactions_processed), tone: 'neutral' },
        { label: 'Match Rate', value: formatPercent(summary.match_rate), tone: 'success' },
        { label: 'Total Exceptions', value: formatNumber(summary.total_exceptions), tone: 'neutral' },
        { label: 'Unresolved', value: formatNumber(summary.unresolved_exceptions), tone: 'warning' },
        { label: 'Resolved', value: formatNumber(summary.resolved_exceptions), tone: 'success' },
        { label: 'Escalated', value: formatNumber(summary.escalated_exceptions), tone: 'danger' },
        { label: 'Rejected', value: formatNumber(summary.rejected_exceptions), tone: 'neutral' },
        { label: 'Resolution Rate', value: formatPercent(summary.resolution_rate), tone: 'info' },
        { label: 'Potential Leakage', value: inr(summary.potential_leakage), tone: 'danger' },
      ]
    : []

  return (
    <div className="analytics">
      <header className="page-header">
        <p className="page-eyebrow">AI Finance Controller</p>
        <h1 className="page-title">Analytics</h1>
        <p className="page-lead">
          Deterministic finance analytics computed by the backend. Potential
          leakage is unexplained discrepancy, not confirmed loss.
        </p>
      </header>

      {error && (
        <div className="upload-message msg-error" role="alert">
          <p>Could not load analytics.</p>
          <p className="msg-detail">{error.message}</p>
        </div>
      )}

      {loading && !summary && <p className="an-empty">Loading analytics…</p>}

      {summary && (
        <>
          <section className="an-summary-grid" aria-label="Analytics summary">
            {cards.map((c) => (
              <article key={c.label} className={`summary-card tone-${c.tone}`}>
                <p className="summary-value">{c.value}</p>
                <p className="summary-label">{c.label}</p>
              </article>
            ))}
          </section>

          <AiInsight insight={insight} onOpen={(id) => navigate('/exceptions', { state: { focus: id } })} />

          <div className="an-two-col">
            <LeakageTrend trend={trend} />
            <ImpactChart distribution={distribution} />
          </div>

          <RiskTable risks={risks} onOpen={(id) => navigate('/exceptions', { state: { focus: id } })} />
        </>
      )}
    </div>
  )
}

function AiInsight({ insight, onOpen }) {
  return (
    <section className="panel ai-insight-panel" aria-labelledby="insight-h">
      <div className="panel-head">
        <h2 id="insight-h" className="panel-title">AI Finance Insight</h2>
        <span className="panel-sub">AI-generated · advisory</span>
      </div>
      {!insight || !insight.available ? (
        <p className="an-empty">
          {insight?.message ?? 'AI insight temporarily unavailable.'}
        </p>
      ) : (
        <div className="insight-body">
          <p className="insight-summary">{insight.insight.summary}</p>
          {insight.insight.key_findings.length > 0 && (
            <ul className="insight-findings">
              {insight.insight.key_findings.map((f, i) => (
                <li key={i}>{f}</li>
              ))}
            </ul>
          )}
          {insight.insight.priority_exceptions.length > 0 && (
            <div className="insight-priorities">
              <span className="insight-priorities-label">Priority exceptions:</span>
              {insight.insight.priority_exceptions.map((id) => (
                <button key={id} type="button" className="chip" onClick={() => onOpen(id)}>
                  {id}
                </button>
              ))}
            </div>
          )}
          <p className="ai-disclaimer">
            AI-generated from validated backend metrics. Advisory only — verify
            before acting.
          </p>
        </div>
      )}
    </section>
  )
}

function RiskTable({ risks, onOpen }) {
  const data = risks?.data ?? []
  return (
    <section className="panel" aria-labelledby="risk-h">
      <div className="panel-head">
        <h2 id="risk-h" className="panel-title">Risk Priorities</h2>
        <span className="panel-sub">Unresolved, highest risk first</span>
      </div>
      {data.length === 0 ? (
        <p className="an-empty">No unresolved exceptions to prioritize.</p>
      ) : (
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col">Exception</th>
                <th scope="col" className="num">Risk</th>
                <th scope="col" className="num">Discrepancy</th>
                <th scope="col">Classification</th>
                <th scope="col">Severity</th>
                <th scope="col">Status</th>
                <th scope="col"></th>
              </tr>
            </thead>
            <tbody>
              {data.map((r) => {
                const meta = RISK_LEVEL_META[r.risk_level] ?? { tone: 'neutral' }
                return (
                  <tr key={r.exception_id}>
                    <th scope="row" className="mono">{r.exception_id}</th>
                    <td className="num">
                      <span className={`risk-pill risk-${meta.tone}`}>{r.risk_score}</span>
                    </td>
                    <td className="num">{inr(r.discrepancy)}</td>
                    <td>{EXCEPTION_TYPE_LABELS[r.classification] ?? r.classification}</td>
                    <td>{r.severity}</td>
                    <td>{r.status}</td>
                    <td>
                      <button type="button" className="btn btn-link" onClick={() => onOpen(r.exception_id)}>
                        Open
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default Analytics
