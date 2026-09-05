import {
  EXCEPTION_STATUS_META,
  EXCEPTION_TYPE_LABELS,
  RISK_LEVEL_META,
  SEVERITY_FILTER_OPTIONS,
  SEVERITY_META,
  STATUS_FILTER_OPTIONS,
  TYPE_FILTER_OPTIONS,
} from '../../constants/exceptions'
import { formatINR } from '../../utils/format'

const inr = (value) => formatINR(Number(value))

function Badge({ meta }) {
  return <span className={`status-badge badge-${meta.tone}`}>{meta.label}</span>
}

function ExceptionsTable({ exceptions, filters, onFilterChange, onSelect }) {
  const set = (key) => (event) =>
    onFilterChange({ ...filters, [key]: event.target.value })

  return (
    <section className="panel" aria-labelledby="exc-table-h">
      <div className="panel-head exc-table-head">
        <h2 id="exc-table-h" className="panel-title">
          Exception Queue
        </h2>
        <div className="exc-filters">
          <label htmlFor="exc-search" className="sr-only">
            Search exception, payment, or order ID
          </label>
          <input
            id="exc-search"
            type="search"
            className="search-input"
            placeholder="Search ID / payment / order"
            value={filters.search}
            onChange={set('search')}
          />
          <label htmlFor="exc-status" className="sr-only">
            Filter by status
          </label>
          <select id="exc-status" className="filter-select" value={filters.status} onChange={set('status')}>
            {STATUS_FILTER_OPTIONS.map((o) => (
              <option key={o.id} value={o.id}>
                {o.label}
              </option>
            ))}
          </select>
          <label htmlFor="exc-type" className="sr-only">
            Filter by type
          </label>
          <select id="exc-type" className="filter-select" value={filters.type} onChange={set('type')}>
            {TYPE_FILTER_OPTIONS.map((o) => (
              <option key={o.id} value={o.id}>
                {o.label}
              </option>
            ))}
          </select>
          <label htmlFor="exc-severity" className="sr-only">
            Filter by severity
          </label>
          <select id="exc-severity" className="filter-select" value={filters.severity} onChange={set('severity')}>
            {SEVERITY_FILTER_OPTIONS.map((o) => (
              <option key={o.id} value={o.id}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="table-scroll">
        <table className="data-table exc-table">
          <thead>
            <tr>
              <th scope="col">#</th>
              <th scope="col">Exception</th>
              <th scope="col">Type</th>
              <th scope="col">Payment</th>
              <th scope="col">Order</th>
              <th scope="col" className="num">Impact</th>
              <th scope="col" className="num">Potential Leakage</th>
              <th scope="col" className="num">Risk</th>
              <th scope="col">Severity</th>
              <th scope="col">Status</th>
              <th scope="col"></th>
            </tr>
          </thead>
          <tbody>
            {exceptions.map((exc, index) => (
              <tr key={exc.exception_id}>
                <td className="rank">{index + 1}</td>
                <th scope="row" className="mono">{exc.exception_id}</th>
                <td>{EXCEPTION_TYPE_LABELS[exc.type] ?? exc.type}</td>
                <td className="mono">{exc.payment_id ?? '—'}</td>
                <td className="mono">{exc.order_id ?? '—'}</td>
                <td className="num">{inr(exc.affected_amount)}</td>
                <td className="num diff">{inr(exc.potential_leakage)}</td>
                <td className="num">
                  <span className={`risk-pill risk-${(RISK_LEVEL_META[exc.risk_level]?.tone) ?? 'neutral'}`}>
                    {exc.risk_score}
                  </span>
                </td>
                <td><Badge meta={SEVERITY_META[exc.severity] ?? { label: exc.severity, tone: 'neutral' }} /></td>
                <td><Badge meta={EXCEPTION_STATUS_META[exc.status] ?? { label: exc.status, tone: 'neutral' }} /></td>
                <td>
                  <button type="button" className="btn btn-link" onClick={() => onSelect(exc)}>
                    Details
                  </button>
                </td>
              </tr>
            ))}
            {exceptions.length === 0 && (
              <tr>
                <td colSpan={11} className="empty-row">
                  No exceptions match the current filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}

export default ExceptionsTable
