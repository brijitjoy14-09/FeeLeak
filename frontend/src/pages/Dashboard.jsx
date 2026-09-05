import { useMemo, useState } from 'react'
import './Dashboard.css'
import DashboardHeader from '../components/dashboard/DashboardHeader'
import ExceptionDistribution from '../components/dashboard/ExceptionDistribution'
import KpiCard from '../components/dashboard/KpiCard'
import LiveStatusPanel from '../components/dashboard/LiveStatusPanel'
import RecentExceptions from '../components/dashboard/RecentExceptions'
import ReconciliationSummary from '../components/dashboard/ReconciliationSummary'
import ReconciliationTrend from '../components/dashboard/ReconciliationTrend'
import { DEFAULT_PERIOD, getDashboardData } from '../data/dashboardData'
import { formatINR, formatNumber, formatPercent } from '../utils/format'

/**
 * Finance Controller Dashboard.
 *
 * Owns the selected period, resolves the (currently mock) dataset for it, and
 * passes structured/formatted data into presentation components. The
 * `getDashboardData` seam is the single place a real API will plug in later.
 */
function Dashboard() {
  const [period, setPeriod] = useState(DEFAULT_PERIOD)
  const data = useMemo(() => getDashboardData(period), [period])
  const { kpis } = data

  return (
    <div className="dashboard">
      <DashboardHeader period={period} onPeriodChange={setPeriod} />

      <LiveStatusPanel />

      <section className="kpi-grid" aria-label="Key metrics">
        <KpiCard
          testId="kpi-records"
          label="Records Processed"
          value={formatNumber(kpis.recordsProcessed)}
          tone="neutral"
          delta={{
            text: `${formatPercent(kpis.changeVsPreviousPct)} vs previous period`,
            direction: kpis.changeVsPreviousPct >= 0 ? 'up' : 'down',
          }}
        />
        <KpiCard
          testId="kpi-match"
          label="Match Rate"
          value={formatPercent(kpis.matchRate)}
          tone="success"
          progress={kpis.matchRate}
          support={`${formatNumber(kpis.matched)} / ${formatNumber(
            kpis.totalForMatch,
          )} matched`}
        />
        <KpiCard
          testId="kpi-exceptions"
          label="Exceptions"
          value={formatNumber(kpis.exceptions)}
          tone="warning"
          support={`${formatNumber(kpis.exceptionsToReview)} require review`}
        />
        <KpiCard
          testId="kpi-leakage"
          label="Potential Leakage"
          value={formatINR(kpis.potentialLeakage)}
          tone="danger"
          support={`${formatINR(kpis.unresolvedLeakage)} unresolved`}
        />
      </section>

      <ReconciliationSummary summary={data.summary} />

      <section className="charts-grid">
        <ReconciliationTrend trend={data.trend} />
        <ExceptionDistribution distribution={data.distribution} />
      </section>

      <RecentExceptions rows={data.recentExceptions} />
    </div>
  )
}

export default Dashboard
