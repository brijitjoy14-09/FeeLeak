import { useCallback, useEffect, useState } from 'react'
import './Reconciliation.css'
import DataSourcesPanel from '../components/reconciliation/DataSourcesPanel'
import ReconciliationResults from '../components/reconciliation/ReconciliationResults'
import ReconciliationRunner from '../components/reconciliation/ReconciliationRunner'
import UploadPanel from '../components/reconciliation/UploadPanel'
import {
  getIngestionStatus,
  getReconciliationResults,
  runReconciliation,
} from '../services/api'

/**
 * Reconciliation control center: ingest datasets (Prompt 3) and run the
 * deterministic reconciliation engine (Prompt 4). All data comes from the
 * backend; this page owns fetch/run state and passes data to presentation
 * components.
 */
function Reconciliation() {
  const [status, setStatus] = useState(null)
  const [statusError, setStatusError] = useState(null)

  const [running, setRunning] = useState(false)
  const [runError, setRunError] = useState(null)
  const [runMessage, setRunMessage] = useState('')

  const [summary, setSummary] = useState(null)
  const [results, setResults] = useState([])

  const refreshStatus = useCallback(async () => {
    try {
      const data = await getIngestionStatus()
      setStatus(data)
      setStatusError(null)
    } catch (err) {
      setStatusError(err)
    }
  }, [])

  useEffect(() => {
    let active = true
    getIngestionStatus()
      .then((data) => {
        if (active) {
          setStatus(data)
          setStatusError(null)
        }
      })
      .catch((err) => {
        if (active) setStatusError(err)
      })
    return () => {
      active = false
    }
  }, [])

  async function handleRun() {
    setRunning(true)
    setRunError(null)
    setRunMessage('')
    try {
      const runData = await runReconciliation()
      const resultsData = await getReconciliationResults({ limit: 10000 })
      setSummary(runData.summary)
      setResults(resultsData.results)
      setRunMessage(
        `Reconciliation completed — ${runData.summary.total_payments} payments processed.`,
      )
    } catch (err) {
      setRunError(err)
      setSummary(null)
      setResults([])
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="reconciliation">
      <header className="page-header">
        <p className="page-eyebrow">AI Finance Controller</p>
        <h1 className="page-title">Reconciliation</h1>
        <p className="page-lead">
          Ingest financial sources, then run deterministic reconciliation across
          orders, payments, refunds, fees, and settlements.
        </p>
      </header>

      {statusError && (
        <div className="upload-message msg-error" role="alert">
          <p>Could not load dataset status.</p>
          <p className="msg-detail">{statusError.message}</p>
        </div>
      )}

      <div className="recon-top-grid">
        <UploadPanel onUploaded={refreshStatus} />
        <ReconciliationRunner
          status={status}
          onRun={handleRun}
          running={running}
          error={runError}
        />
      </div>

      <DataSourcesPanel status={status} onChanged={refreshStatus} />

      {runMessage && !runError && (
        <p className="run-success" role="status">
          {runMessage}
        </p>
      )}

      {summary ? (
        <ReconciliationResults summary={summary} results={results} />
      ) : (
        <section className="panel empty-state">
          <h2 className="panel-title">No reconciliation results yet</h2>
          <p>
            Load all required datasets and run reconciliation to begin. Results
            will appear here.
          </p>
        </section>
      )}
    </div>
  )
}

export default Reconciliation
