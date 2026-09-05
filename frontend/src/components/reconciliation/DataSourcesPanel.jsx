import { useState } from 'react'
import { deleteDataset, getDataset } from '../../services/api'
import { SOURCES } from '../../constants/reconciliation'
import { formatNumber } from '../../utils/format'

/**
 * Shows load status for each source with per-source preview + delete.
 * `status` is the /ingestion/status payload; parent refreshes it on change.
 */
function DataSourcesPanel({ status, onChanged }) {
  const [preview, setPreview] = useState(null) // { source, records, columns }
  const [previewLoading, setPreviewLoading] = useState(null)
  const [busy, setBusy] = useState(null)

  const sources = status?.sources ?? {}

  async function handlePreview(sourceId) {
    if (preview?.source === sourceId) {
      setPreview(null)
      return
    }
    setPreviewLoading(sourceId)
    try {
      const data = await getDataset(sourceId, 10)
      setPreview({
        source: sourceId,
        records: data.records,
        columns: data.columns,
      })
    } catch {
      setPreview(null)
    } finally {
      setPreviewLoading(null)
    }
  }

  async function handleDelete(sourceId) {
    setBusy(sourceId)
    try {
      await deleteDataset(sourceId)
      if (preview?.source === sourceId) setPreview(null)
      onChanged?.()
    } finally {
      setBusy(null)
    }
  }

  return (
    <section className="panel" aria-labelledby="sources-h">
      <div className="panel-head">
        <h2 id="sources-h" className="panel-title">
          Data Sources
        </h2>
      </div>

      <div className="table-scroll">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col">Source</th>
              <th scope="col">Status</th>
              <th scope="col" className="num">
                Records
              </th>
              <th scope="col">Actions</th>
            </tr>
          </thead>
          <tbody>
            {SOURCES.map((source) => {
              const info = sources[source.id]
              const loaded = info?.loaded
              return (
                <tr key={source.id}>
                  <th scope="row">{source.label}</th>
                  <td>
                    <span
                      className={`status-badge badge-${loaded ? 'success' : 'neutral'}`}
                    >
                      {loaded ? 'Loaded' : 'Not Loaded'}
                    </span>
                  </td>
                  <td className="num">
                    {loaded ? formatNumber(info.records) : '—'}
                  </td>
                  <td>
                    <div className="row-actions">
                      <button
                        type="button"
                        className="btn btn-link"
                        disabled={!loaded || previewLoading === source.id}
                        onClick={() => handlePreview(source.id)}
                      >
                        {preview?.source === source.id ? 'Hide' : 'Preview'}
                      </button>
                      <button
                        type="button"
                        className="btn btn-link btn-danger"
                        disabled={!loaded || busy === source.id}
                        onClick={() => handleDelete(source.id)}
                      >
                        {busy === source.id ? 'Deleting…' : 'Delete'}
                      </button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {preview && (
        <div className="preview">
          <p className="preview-head">
            Preview — {preview.source}{' '}
            <span className="preview-sub">
              showing first {preview.records.length} records
            </span>
          </p>
          <div className="table-scroll">
            <table className="data-table preview-table">
              <thead>
                <tr>
                  {preview.columns.map((col) => (
                    <th key={col} scope="col">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.records.map((record, index) => (
                  <tr key={index}>
                    {preview.columns.map((col) => (
                      <td key={col}>{record[col]}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  )
}

export default DataSourcesPanel
