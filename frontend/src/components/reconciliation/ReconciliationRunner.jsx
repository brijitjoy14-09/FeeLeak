import { SOURCES } from '../../constants/reconciliation'

/**
 * Dataset readiness + the Run Reconciliation control.
 * Presentation only — the parent owns the run action and its state.
 */
function ReconciliationRunner({ status, onRun, running, error }) {
  const sources = status?.sources ?? {}
  const missing = SOURCES.filter((s) => !sources[s.id]?.loaded)
  const allLoaded = missing.length === 0

  return (
    <section className="panel runner-panel" aria-labelledby="runner-h">
      <div className="panel-head">
        <h2 id="runner-h" className="panel-title">
          Run Reconciliation
        </h2>
      </div>

      <ul className="readiness">
        {SOURCES.map((source) => {
          const loaded = sources[source.id]?.loaded
          return (
            <li key={source.id} className={loaded ? 'ready' : 'not-ready'}>
              <span className="readiness-icon" aria-hidden="true">
                {loaded ? '✓' : '✕'}
              </span>
              <span className="readiness-label">{source.label}</span>
              <span className="readiness-state">
                {loaded ? 'Loaded' : 'Not Loaded'}
              </span>
            </li>
          )
        })}
      </ul>

      <button
        type="button"
        className="btn btn-primary"
        onClick={onRun}
        disabled={!allLoaded || running}
      >
        {running ? 'Running reconciliation…' : 'Run Reconciliation'}
      </button>

      {!allLoaded && (
        <p className="runner-hint" role="status">
          Load all required datasets to enable reconciliation. Missing:{' '}
          {missing.map((s) => s.label).join(', ')}.
        </p>
      )}

      {error && (
        <div className="upload-message msg-error" role="alert">
          <p>Reconciliation could not be completed.</p>
          <p className="msg-detail">{error.message}</p>
          {error.details?.missing_sources && (
            <p className="msg-detail">
              Missing required datasets: {error.details.missing_sources.join(', ')}
            </p>
          )}
        </div>
      )}
    </section>
  )
}

export default ReconciliationRunner
