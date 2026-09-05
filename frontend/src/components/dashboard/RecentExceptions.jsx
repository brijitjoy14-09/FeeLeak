import { formatINR } from '../../utils/format'

// Status → visual tone (paired with the status text, never color-only).
const STATUS_TONE = {
  Resolved: 'success',
  Review: 'warning',
  Investigating: 'info',
  Unresolved: 'danger',
}

function RecentExceptions({ rows }) {
  return (
    <section className="panel table-panel" aria-labelledby="recent-h">
      <div className="panel-head">
        <h2 id="recent-h" className="panel-title">
          Recent Exceptions
        </h2>
        <span className="panel-sub">{rows.length} shown</span>
      </div>

      <div className="table-scroll">
        <table className="exc-table">
          <caption className="sr-only">
            Recent reconciliation exceptions (synthetic data)
          </caption>
          <thead>
            <tr>
              <th scope="col">Transaction</th>
              <th scope="col">Type</th>
              <th scope="col" className="num">
                Expected
              </th>
              <th scope="col" className="num">
                Actual
              </th>
              <th scope="col" className="num">
                Difference
              </th>
              <th scope="col">Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id}>
                <th scope="row" className="txn-id">
                  {row.id}
                </th>
                <td>{row.type}</td>
                <td className="num">{formatINR(row.expected)}</td>
                <td className="num">{formatINR(row.actual)}</td>
                <td className="num diff">{formatINR(row.difference)}</td>
                <td>
                  <span
                    className={`status-badge badge-${
                      STATUS_TONE[row.status] ?? 'neutral'
                    }`}
                  >
                    {row.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

export default RecentExceptions
