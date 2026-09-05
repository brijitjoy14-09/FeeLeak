import { useEffect, useState } from 'react'
import { SEVERITY_META, EXCEPTION_TYPE_LABELS } from '../../constants/exceptions'
import {
  ApiError,
  getExceptionsSummary,
  getReconciliationSummary,
} from '../../services/api'
import { formatINR, formatNumber, formatPercent } from '../../utils/format'

const inr = (value) => formatINR(Number(value))

function MiniDist({ title, data, lookup }) {
  const entries = Object.entries(data).filter(([, count]) => count > 0)
  const total = entries.reduce((sum, [, count]) => sum + count, 0)
  if (total === 0) return null
  return (
    <div className="dist-block">
      <h3 className="dist-title">{title}</h3>
      <ul className="dist-list">
        {entries
          .sort((a, b) => b[1] - a[1])
          .map(([key, count]) => (
            <li key={key} className="dist-row">
              <span className="dist-label">{lookup(key)}</span>
              <span className="dist-track" aria-hidden="true">
                <span className="dist-fill" style={{ width: `${(count / total) * 100}%` }} />
              </span>
              <span className="dist-count">{count}</span>
            </li>
          ))}
      </ul>
    </div>
  )
}

/**
 * Live reconciliation + exception metrics from the backend. Distinct from the
 * synthetic KPI cards above — this reflects real ingested/reconciled data.
 * Renders a gentle prompt when reconciliation has not been run yet.
 */
function LiveStatusPanel() {
  const [recon, setRecon] = useState(null)
  const [exceptions, setExceptions] = useState(null)
  const [unavailable, setUnavailable] = useState(false)

  useEffect(() => {
    let active = true
    getReconciliationSummary()
      .then(async (data) => {
        if (!active) return
        setRecon(data.summary)
        try {
          const exc = await getExceptionsSummary()
          if (active) setExceptions(exc)
        } catch {
          /* exceptions summary is optional here */
        }
      })
      .catch((err) => {
        if (!active) return
        if (err instanceof ApiError && err.code === 'NO_RECONCILIATION') {
          setUnavailable(true)
        } else {
          setUnavailable(true)
        }
      })
    return () => {
      active = false
    }
  }, [])

  if (unavailable) {
    return (
      <section className="panel live-panel" aria-label="Live status">
        <div className="panel-head">
          <h2 className="panel-title">Live Reconciliation &amp; Exceptions</h2>
          <span className="panel-sub">Real data</span>
        </div>
        <p className="live-empty">
          No reconciliation has been run yet. Go to Reconciliation to load data,
          run reconciliation, and generate exceptions — live metrics will appear
          here.
        </p>
      </section>
    )
  }

  if (!recon) return null

  const matchRate =
    recon.total_payments > 0 ? (recon.matched / recon.total_payments) * 100 : 0

  const kpis = [
    { label: 'Total Transactions', value: formatNumber(recon.total_payments), tone: 'neutral' },
    { label: 'Match Rate', value: formatPercent(matchRate), tone: 'success' },
    {
      label: 'Active Exceptions',
      value: formatNumber(exceptions ? exceptions.active_exceptions : 0),
      tone: 'warning',
    },
    {
      label: 'Potential Leakage',
      value: inr(exceptions ? exceptions.potential_leakage : 0),
      tone: 'danger',
    },
    {
      label: 'Open Reviews',
      value: formatNumber(exceptions ? exceptions.open + exceptions.in_review : 0),
      tone: 'info',
    },
  ]

  return (
    <section className="panel live-panel" aria-label="Live status">
      <div className="panel-head">
        <h2 className="panel-title">Live Reconciliation &amp; Exceptions</h2>
        <span className="panel-sub">Real data</span>
      </div>

      <div className="live-kpis">
        {kpis.map((kpi) => (
          <div key={kpi.label} className={`live-kpi tone-${kpi.tone}`}>
            <p className="live-kpi-value">{kpi.value}</p>
            <p className="live-kpi-label">{kpi.label}</p>
          </div>
        ))}
      </div>

      {exceptions && exceptions.total_exceptions > 0 && (
        <div className="live-dists">
          <MiniDist
            title="Severity (active)"
            data={exceptions.severity_distribution}
            lookup={(k) => SEVERITY_META[k]?.label ?? k}
          />
          <MiniDist
            title="Exception Type (active)"
            data={exceptions.type_distribution}
            lookup={(k) => EXCEPTION_TYPE_LABELS[k] ?? k}
          />
        </div>
      )}
    </section>
  )
}

export default LiveStatusPanel
