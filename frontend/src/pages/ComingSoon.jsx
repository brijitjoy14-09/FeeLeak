/**
 * Placeholder for modules that are navigable but not yet built
 * (Reconciliation, Exceptions, Analytics, Settings). Future prompts will
 * replace these with real pages.
 */
function ComingSoon({ title }) {
  return (
    <section className="coming-soon">
      <span className="cs-badge">Coming soon</span>
      <h1>{title}</h1>
      <p>
        This module is not available yet. It will be enabled in a future
        release of FeeLeak.
      </p>
    </section>
  )
}

export default ComingSoon
