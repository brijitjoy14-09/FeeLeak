import { useMemo, useState } from 'react'
import { STATUS_FILTERS, STATUS_META } from '../../constants/reconciliation'
import { formatINR, formatNumber } from '../../utils/format'

const inr = (value) => formatINR(Number(value))

function StatusBadge({ status }) {
  const meta = STATUS_META[status] ?? { label: status, tone: 'neutral' }
  return <span className={`status-badge badge-${meta.tone}`}>{meta.label}</span>
}

function SummaryCards({ summary }) {
  const integrityIssues =
    summary.order_not_found +
    summary.duplicate_payment +
    summary.orphan_records.settlements +
    summary.orphan_records.refunds +
    summary.orphan_records.fees

  const cards = [
    { label: 'Total Payments', value: formatNumber(summary.total_payments), tone: 'neutral' },
    { label: 'Matched', value: formatNumber(summary.matched), tone: 'success' },
    { label: 'Mismatched', value: formatNumber(summary.mismatched), tone: 'danger' },
    { label: 'Missing Settlement', value: formatNumber(summary.missing_settlement), tone: 'warning' },
    { label: 'Data Integrity Issues', value: formatNumber(integrityIssues), tone: 'warning' },
    { label: 'Total Difference', value: inr(summary.total_difference), tone: 'danger' },
  ]

  return (
    <section className="recon-summary-grid" aria-label="Reconciliation summary">
      {cards.map((card) => (
        <article key={card.label} className={`summary-card tone-${card.tone}`}>
          <p className="summary-value">{card.value}</p>
          <p className="summary-label">{card.label}</p>
        </article>
      ))}
    </section>
  )
}

function ResultDetail({ result, onClose }) {
  return (
    <div className="detail-backdrop" role="dialog" aria-modal="true" aria-label={`Reconciliation detail for ${result.payment_id}`}>
      <div className="detail-panel">
        <div className="detail-head">
          <h3>{result.payment_id}</h3>
          <button type="button" className="btn btn-link" onClick={onClose} aria-label="Close details">
            Close
          </button>
        </div>

        <dl className="detail-grid">
          <div><dt>Order</dt><dd>{result.order_id}{result.order_found ? '' : ' (not found)'}</dd></div>
          <div><dt>Payment</dt><dd>{inr(result.payment_amount)}</dd></div>
          <div><dt>Refunds ({result.refund_count})</dt><dd>− {inr(result.total_refund)}</dd></div>
          <div><dt>Fees ({result.fee_count})</dt><dd>− {inr(result.total_fee)}</dd></div>
          <div><dt>Taxes</dt><dd>− {inr(result.total_tax)}</dd></div>
        </dl>

        <div className="calc">
          <div className="calc-row"><span>Payment</span><span>{inr(result.payment_amount)}</span></div>
          <div className="calc-row"><span>− Refunds</span><span>{inr(result.total_refund)}</span></div>
          <div className="calc-row"><span>− Fees</span><span>{inr(result.total_fee)}</span></div>
          <div className="calc-row"><span>− Taxes</span><span>{inr(result.total_tax)}</span></div>
          <div className="calc-row calc-total"><span>Expected Settlement</span><span>{inr(result.expected_settlement)}</span></div>
          <div className="calc-row"><span>Actual Settlement ({result.settlement_count})</span><span>{inr(result.actual_settlement)}</span></div>
          <div className="calc-row calc-diff"><span>Difference</span><span>{inr(result.difference)}</span></div>
        </div>

        <div className="detail-status">
          Status: <StatusBadge status={result.status} />
        </div>
      </div>
    </div>
  )
}

function ReconciliationResults({ summary, results }) {
  const [filter, setFilter] = useState('ALL')
  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState(null)

  const activeStatus = STATUS_FILTERS.find((f) => f.id === filter)?.status ?? null

  const filtered = useMemo(() => {
    const needle = search.trim().toLowerCase()
    return results.filter((row) => {
      if (activeStatus && row.status !== activeStatus) return false
      if (needle) {
        return (
          row.payment_id.toLowerCase().includes(needle) ||
          row.order_id.toLowerCase().includes(needle)
        )
      }
      return true
    })
  }, [results, activeStatus, search])

  return (
    <>
      <SummaryCards summary={summary} />

      <section className="panel" aria-labelledby="results-h">
        <div className="panel-head results-head">
          <h2 id="results-h" className="panel-title">
            Results
          </h2>
          <div className="results-controls">
            <label htmlFor="result-search" className="sr-only">
              Search by payment or order ID
            </label>
            <input
              id="result-search"
              type="search"
              className="search-input"
              placeholder="Search payment / order ID"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
            <label htmlFor="status-filter" className="sr-only">
              Filter by status
            </label>
            <select
              id="status-filter"
              className="filter-select"
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
            >
              {STATUS_FILTERS.map((option) => (
                <option key={option.id} value={option.id}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="table-scroll">
          <table className="data-table results-table">
            <thead>
              <tr>
                <th scope="col">Payment</th>
                <th scope="col">Order</th>
                <th scope="col" className="num">Expected</th>
                <th scope="col" className="num">Actual</th>
                <th scope="col" className="num">Difference</th>
                <th scope="col">Status</th>
                <th scope="col"></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((row) => (
                <tr key={row.payment_id}>
                  <th scope="row" className="mono">{row.payment_id}</th>
                  <td className="mono">{row.order_id}</td>
                  <td className="num">{inr(row.expected_settlement)}</td>
                  <td className="num">{inr(row.actual_settlement)}</td>
                  <td className="num diff">{inr(row.difference)}</td>
                  <td><StatusBadge status={row.status} /></td>
                  <td>
                    <button
                      type="button"
                      className="btn btn-link"
                      onClick={() => setSelected(row)}
                    >
                      Details
                    </button>
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={7} className="empty-row">
                    No results match the current filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {selected && (
        <ResultDetail result={selected} onClose={() => setSelected(null)} />
      )}
    </>
  )
}

export default ReconciliationResults
