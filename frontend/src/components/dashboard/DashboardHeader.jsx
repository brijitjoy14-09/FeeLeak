import { PERIODS } from '../../data/dashboardData'

/**
 * Dashboard title block + period filter.
 * Presentation only — the selected period is owned by the page.
 */
function DashboardHeader({ period, onPeriodChange }) {
  return (
    <header className="dash-header">
      <div className="dash-header-titles">
        <p className="dash-eyebrow">AI Finance Controller</p>
        <h1 className="dash-title">Overview</h1>
      </div>

      <div className="dash-header-actions">
        <span
          className="demo-badge"
          title="All figures on this dashboard are synthetic demo data, not real financial results."
        >
          Synthetic data
        </span>

        <div className="period-filter">
          <label htmlFor="period-select" className="period-label">
            Period
          </label>
          <select
            id="period-select"
            className="period-select"
            value={period}
            onChange={(event) => onPeriodChange(event.target.value)}
          >
            {PERIODS.map((option) => (
              <option key={option.id} value={option.id}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>
    </header>
  )
}

export default DashboardHeader
