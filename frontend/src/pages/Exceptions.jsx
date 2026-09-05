import { useCallback, useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import './Exceptions.css'
import ExceptionDetail from '../components/exceptions/ExceptionDetail'
import ExceptionsSummary from '../components/exceptions/ExceptionsSummary'
import ExceptionsTable from '../components/exceptions/ExceptionsTable'
import {
  generateExceptions,
  getException,
  getExceptions,
  getExceptionsSummary,
} from '../services/api'

const INITIAL_FILTERS = { status: 'ALL', type: 'ALL', severity: 'ALL', search: '' }

function mapFilters(filters) {
  return {
    status: filters.status === 'ALL' ? null : filters.status,
    type: filters.type === 'ALL' ? null : filters.type,
    severity: filters.severity === 'ALL' ? null : filters.severity,
    search: filters.search.trim() || null,
    limit: 1000,
  }
}

/**
 * Finance Exception Queue: generate exceptions from the latest reconciliation,
 * triage them, review/resolve/escalate, and run AI investigation. All data is
 * real backend data.
 */
function Exceptions() {
  const [summary, setSummary] = useState(null)
  const [exceptions, setExceptions] = useState([])
  const [filters, setFilters] = useState(INITIAL_FILTERS)
  const [selected, setSelected] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [message, setMessage] = useState(null)
  const [error, setError] = useState(null)

  const loadSummary = useCallback(async () => {
    try {
      setSummary(await getExceptionsSummary())
    } catch (err) {
      setError(err)
    }
  }, [])

  const loadList = useCallback(async (activeFilters) => {
    try {
      const data = await getExceptions(mapFilters(activeFilters))
      setExceptions(data.exceptions)
    } catch (err) {
      setError(err)
    }
  }, [])

  useEffect(() => {
    let active = true
    getExceptionsSummary()
      .then((data) => active && setSummary(data))
      .catch((err) => active && setError(err))
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    let active = true
    getExceptions(mapFilters(filters))
      .then((data) => active && setExceptions(data.exceptions))
      .catch((err) => active && setError(err))
    return () => {
      active = false
    }
  }, [filters])

  // Deep-link: open a specific exception when navigated from Analytics/Copilot.
  const location = useLocation()
  const focusId = location.state?.focus
  useEffect(() => {
    let active = true
    if (focusId) {
      getException(focusId)
        .then((exc) => active && setSelected(exc))
        .catch(() => {})
    }
  }, [focusId])

  async function handleGenerate() {
    setGenerating(true)
    setError(null)
    setMessage(null)
    try {
      const result = await generateExceptions()
      setSummary(result.summary)
      await loadList(filters)
      setMessage(
        `Generated ${result.summary.total_exceptions} exceptions from the latest reconciliation.`,
      )
    } catch (err) {
      setError(err)
    } finally {
      setGenerating(false)
    }
  }

  async function refreshAfterUpdate() {
    await Promise.all([loadSummary(), loadList(filters)])
  }

  const hasExceptions = summary && summary.total_exceptions > 0

  return (
    <div className="exceptions">
      <header className="page-header">
        <div className="page-header-row">
          <div>
            <p className="page-eyebrow">AI Finance Controller</p>
            <h1 className="page-title">Finance Exception Queue</h1>
          </div>
          <button
            type="button"
            className="btn btn-primary"
            onClick={handleGenerate}
            disabled={generating}
          >
            {generating ? 'Generating…' : 'Generate Exceptions'}
          </button>
        </div>
        <p className="page-lead">
          Exceptions are derived deterministically from reconciliation results.
          AI can investigate and explain them; a human finance controller
          decides how to resolve.
        </p>
      </header>

      {error && (
        <div className="upload-message msg-error" role="alert">
          <p>{error.message}</p>
          {error.code === 'RECONCILIATION_NOT_RUN' && (
            <p className="msg-detail">
              Run reconciliation first (Reconciliation page), then generate
              exceptions.
            </p>
          )}
        </div>
      )}

      {message && !error && (
        <p className="run-success" role="status">
          {message}
        </p>
      )}

      {hasExceptions ? (
        <>
          <ExceptionsSummary summary={summary} />
          <ExceptionsTable
            exceptions={exceptions}
            filters={filters}
            onFilterChange={setFilters}
            onSelect={setSelected}
          />
        </>
      ) : (
        <section className="panel empty-state">
          <h2 className="panel-title">No exceptions yet</h2>
          <p>
            Load datasets and run reconciliation, then click{' '}
            <strong>Generate Exceptions</strong> to populate the queue.
          </p>
        </section>
      )}

      {selected && (
        <ExceptionDetail
          key={selected.exception_id}
          exception={selected}
          onClose={() => setSelected(null)}
          onUpdated={refreshAfterUpdate}
        />
      )}
    </div>
  )
}

export default Exceptions
