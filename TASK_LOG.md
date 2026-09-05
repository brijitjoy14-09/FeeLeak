# FeeLeak — Task Log

## Prompt 1 — Project Foundation, Backend Setup & Documentation

### Status

Completed

### Objective

Establish the initial FeeLeak frontend/backend foundation and persistent AI
project documentation.

### Tasks Completed

- Inspected the existing project (frontend `package.json`, Vite config, source;
  backend `venv`) before making changes.
- Built the FastAPI backend inside the existing `backend/` directory (reusing
  the pre-existing `venv`, Python 3.14.3).
- Created `app/main.py` with API metadata, CORS, and `GET /` + `GET /health`.
- Wrote `requirements.txt` and installed dependencies into the existing venv.
- Wrote the backend pytest suite (3 tests) and ran it — all passing.
- Added a frontend API service layer and a `useBackendHealth` hook.
- Replaced the default Vite demo UI with a minimal FeeLeak app shell that shows
  live backend connection status; removed orphaned demo assets.
- Added `.env` / `.env.example` and wired the backend URL through
  `VITE_API_BASE_URL`.
- Added Vitest + Testing Library, configured it, and wrote 4 frontend tests
  (API mocked) — all passing.
- Created root `README.md`, `PROJECT_SUMMARY.md`, `TASK_LOG.md`, and
  `.gitignore`.
- Verified both apps end-to-end in a browser (Connected and Disconnected).

### Files Created

- `backend/app/__init__.py`
- `backend/app/main.py`
- `backend/tests/__init__.py`
- `backend/tests/test_main.py`
- `backend/requirements.txt`
- `frontend/.env`
- `frontend/.env.example`
- `frontend/src/services/api.js`
- `frontend/src/hooks/useBackendHealth.js`
- `frontend/src/test/setup.js`
- `frontend/src/App.test.jsx`
- `README.md`
- `PROJECT_SUMMARY.md`
- `TASK_LOG.md`
- `.gitignore`

### Files Modified

- `frontend/src/App.jsx` — replaced Vite demo with minimal FeeLeak shell.
- `frontend/src/App.css` — replaced demo styles with shell styles.
- `frontend/src/index.css` — simplified demo-specific `#root` rule; kept CSS
  variables and dark mode.
- `frontend/index.html` — title changed to `FeeLeak — AI Finance Controller`.
- `frontend/vite.config.js` — added Vitest config and `esbuild.jsx: 'automatic'`.
- `frontend/package.json` — added `test` and `test:watch` scripts and dev
  dependencies (vitest, @testing-library/react, jest-dom, jsdom).

### Files Removed

- `frontend/src/assets/hero.png`, `react.svg`, `vite.svg` (orphaned demo
  assets, no longer imported).
- `frontend/public/icons.svg` (orphaned demo asset).

### Backend

- FastAPI application: `backend/app/main.py`, title `FeeLeak API`, description
  `AI-powered financial reconciliation backend`, version `1.0.0`.
- API endpoints: `GET /` → `{"message": "FeeLeak API is running"}`;
  `GET /health` → `{"status": "healthy"}`; both 200. Swagger at `/docs`.
- CORS: allow-list `http://localhost:5173`, `http://127.0.0.1:5173`; methods
  `GET, POST, PUT, DELETE, OPTIONS`; no wildcard origin.
- Dependencies: fastapi, uvicorn[standard], python-multipart, pandas, pytest,
  httpx (installed into existing `backend/venv`).

### Frontend

- React application: minimal shell (`App.jsx`) showing FeeLeak identity and
  backend status; existing Vite/React 19 setup preserved.
- API service: `src/services/api.js` (`getHealth`) + `src/hooks/useBackendHealth.js`.
- Environment configuration: `.env` / `.env.example` with `VITE_API_BASE_URL`;
  read via `import.meta.env.VITE_API_BASE_URL`; no hardcoded URLs.
- Backend health check: calls `GET ${VITE_API_BASE_URL}/health` once on mount;
  shows "Connected" / "Disconnected" / "Checking..." and never crashes on
  network or HTTP errors.

### Tests Executed

- Backend: `pytest` (3 tests).
- Frontend: `npm test` → `vitest run` (4 tests).
- Frontend lint (`oxlint`) and production build (`vite build`) as sanity checks.
- Manual/browser: live Connected and Disconnected states, plus `curl` checks of
  `/`, `/health`, `/docs`, and a CORS preflight.

### Test Results

- Backend: **3 passed** (1 benign Starlette deprecation warning about httpx).
- Frontend: **4 passed**, no warnings.
- Lint: clean. Build: succeeded (Vite reports it uses oxc and ignores the
  esbuild `jsx` option — expected; that option only affects Vitest).
- `curl`: `/` and `/health` returned 200 with expected JSON; `/docs` 200; CORS
  preflight returned `access-control-allow-origin: http://localhost:5173`.
- Browser: page showed "Backend Status: Connected" with the backend up and
  "Backend Status: Disconnected" (no crash) with the backend stopped.

### Issues Encountered

- Frontend tests initially failed with `ReferenceError: React is not defined`
  (Vitest's esbuild transform used the classic JSX runtime).
- An `act(...)` warning appeared on tests that rendered `App` without awaiting
  the async health-check state update.
- A Vite dev server was already listening on `:5173` from a prior process, so a
  second `npm run dev` bound to `:5174`.

### Resolutions

- Set `esbuild: { jsx: 'automatic' }` in `vite.config.js` so Vitest resolves
  JSX without an explicit React import.
- Made the affected tests `await` the resolved status (e.g. `findByText`) to
  flush the update inside `act`.
- Verified in the browser against `:5173` (the CORS-allowed origin); stopped the
  extra `:5174` server. The pre-existing `:5173` server was left running.

### Deviations From Prompt

- Frontend test stack: the prompt left the framework open ("if none exists, add
  a lightweight setup"). None existed, so Vitest + Testing Library was added
  (natural fit for Vite) with `esbuild.jsx: 'automatic'` to make the transform
  work. No other deviations.

### Current Project State

Foundation complete and verified. FastAPI backend (`/`, `/health`, `/docs`,
CORS) runs on `:8000`; React + Vite frontend runs on `:5173` and reports the
live backend status via `VITE_API_BASE_URL`. Backend (3) and frontend (4) tests
pass. Root `README.md`, `PROJECT_SUMMARY.md`, `TASK_LOG.md`, and `.gitignore`
exist. No reconciliation, AI, dashboard, database, or auth features were built.

### Notes For Prompt 2

- Read `PROJECT_SUMMARY.md` first — it is the authoritative current state.
- The dashboard is Prompt 2's job. Keep `backend/app/main.py` thin: add new
  endpoints in dedicated routers/services, not in `main.py`.
- Extend the frontend service layer (`src/services/`) for new API calls; keep
  reading config from `VITE_API_BASE_URL`; do not hardcode URLs or widen CORS.
- Keep all financial arithmetic deterministic; AI is for investigation/
  explanation only (see PROJECT_SUMMARY §14) — and not until a later prompt.
- Reuse the existing `backend/venv` and frontend `node_modules`; do not
  reinitialize the project.
- Dev note: a Vite server may already be on `:5173`; use that port for browser
  checks since CORS only allows `:5173`.

---

## Prompt 2 — FeeLeak Finance Controller Dashboard

### Status

Completed

### Objective

Build the first real FeeLeak user-facing Finance Controller Dashboard
(synthetic data), decoupled so mock data can later be swapped for a real API.

### Tasks Completed

- Re-read `PROJECT_SUMMARY.md` / `TASK_LOG.md` and verified the actual codebase
  matched the Prompt 1 state before changing anything.
- Added React Router 7 and an app shell (sidebar + main) with routed pages.
- Built the dashboard at `/dashboard` from six reusable components.
- Created a structured, period-keyed synthetic mock-data module.
- Added reusable INR / number / percent formatters.
- Built dependency-free SVG charts (trend combo + distribution donut).
- Implemented the Today / Last 7 Days / Last 30 Days period filter.
- Added "Coming soon" placeholder pages for the other four nav sections.
- Preserved the Prompt 1 backend health check as a sidebar indicator.
- Wrote 6 dashboard tests; updated the 4 shell/connectivity tests.
- Ran frontend tests, backend tests, lint, and production build; verified the
  dashboard live in a browser (both connected and mock-only states).
- Updated `PROJECT_SUMMARY.md` (§19 added; §§1,5,6,7,8,9,12,15,16,17,18).

### Files Created

- `frontend/src/utils/format.js`
- `frontend/src/data/dashboardData.js`
- `frontend/src/components/layout/AppLayout.jsx`
- `frontend/src/components/layout/Sidebar.jsx`
- `frontend/src/components/dashboard/DashboardHeader.jsx`
- `frontend/src/components/dashboard/KpiCard.jsx`
- `frontend/src/components/dashboard/ReconciliationSummary.jsx`
- `frontend/src/components/dashboard/ReconciliationTrend.jsx`
- `frontend/src/components/dashboard/ExceptionDistribution.jsx`
- `frontend/src/components/dashboard/RecentExceptions.jsx`
- `frontend/src/pages/Dashboard.jsx`
- `frontend/src/pages/Dashboard.css`
- `frontend/src/pages/Dashboard.test.jsx`
- `frontend/src/pages/ComingSoon.jsx`

### Files Modified

- `frontend/src/App.jsx` — now a Router + `AppLayout` + routes.
- `frontend/src/App.css` — replaced shell styles with layout/sidebar/topbar.
- `frontend/src/index.css` — professional finance design tokens (light/dark).
- `frontend/src/App.test.jsx` — updated for the new shell (connectivity now in
  the sidebar); still 4 tests.
- `frontend/package.json` / `package-lock.json` — added `react-router-dom`.

### Dashboard Features

- Sidebar navigation: Dashboard (active) + Reconciliation / Exceptions /
  Analytics / Settings (marked "Soon", route to a Coming-soon page).
- Four KPI cards: Records Processed (Δ vs previous), Match Rate (progress bar +
  matched/total), Exceptions (require-review), Potential Leakage (INR +
  unresolved).
- Reconciliation Summary: proportional matched/resolved/unresolved bar + stat
  chips (Processed/Matched/Resolved/Unresolved).
- Reconciliation Trend: SVG bars (records/day) + match-rate line overlay.
- Exception Distribution: SVG donut + legend with counts and percentages.
- Recent Exceptions: accessible table with text status badges.
- Period filter (Today / Last 7 Days / Last 30 Days), frontend-only.
- Consistent INR (Indian grouping) + percentage formatting; responsive layout
  (sidebar collapses to a drawer < 900px); basic a11y (labelled select, scoped
  table headers, progressbar roles, text-paired status colours).

### Mock Data

- `frontend/src/data/dashboardData.js` — synthetic, per-period (`today`, `7d`,
  `30d`) with `kpis`, `summary`, `trend`, `distribution`, `recentExceptions`.
- Default period `7d`: 500 processed, 92.4% match, 38 exceptions, ₹24,850
  potential leakage. Clearly labelled synthetic; `getDashboardData(period)` is
  the seam a real API will replace.

### Tests Executed

- Frontend: `npm test` (`vitest run`) — 2 files, 10 tests.
- Backend regression: `pytest` — 3 tests.
- `npm run lint` (oxlint) and `npm run build` (vite build).
- Manual browser verification on `:5173` with the backend on `:8000`.

### Test Results

- Frontend: **10 passed** (4 shell/connectivity + 6 dashboard), no warnings.
- Backend: **3 passed** (1 benign Starlette httpx deprecation warning).
- Lint: **clean**. Build: **succeeded** (`vite build`, 40 modules).
- Browser: dashboard rendered fully; period switch to Last 30 Days showed
  `2,184`, `91.7%`, and `₹1,12,400` (correct lakh grouping); sidebar showed
  Backend Connected with the API up.

### Issues Encountered

- Vitest `act(...)` warnings on synchronous tests because the sidebar's
  async health check resolved after render.
- oxlint flagged reassigning a `let offset` accumulator during render in the
  donut component.

### Resolutions

- Made those tests `await` a post-health-check assertion to flush the update.
- Refactored the donut to compute segment offsets via a prefix-sum (no
  post-render mutation); lint is clean.

### Deviations From Prompt

- Added `react-router-dom` (Prompt 2 explicitly allows adding routing if not
  present; none existed). It is lightweight and used for the `/dashboard`
  route + nav.
- Charts are hand-built SVG rather than a chart library — deliberately, to
  avoid a heavy dependency (prompt §33) while keeping full control of styling.
- Updated (not removed) the Prompt 1 `App.test.jsx`: the old shell it tested
  was replaced by the dashboard, so the tests now assert the same connectivity
  behaviour in its new sidebar location.

### Current Project State

FeeLeak now has a professional Finance Controller Dashboard at `/dashboard`
running on synthetic data, independent of the backend. Prompt 1 endpoints
(`/`, `/health`, `/docs`, CORS) are unchanged and still pass. All tests pass
(frontend 10, backend 3); lint and production build succeed. Documentation is
updated. No reconciliation engine, real data, AI, database, auth, or ingestion
exists.

### Notes For Prompt 3

- Prompt 3 = **Multi-Source Data Ingestion** (CSV/file upload, parsing,
  validation, normalization for orders/payments/refunds/fees/settlements).
- To connect the dashboard to real numbers later, replace
  `getDashboardData(period)` in `data/dashboardData.js` — the component tree
  consumes the same structured shape, so no UI redesign is needed.
- Keep `backend/app/main.py` thin; add ingestion endpoints in separate
  routers/services. Reuse `backend/venv` and frontend `node_modules`.
- Reuse `utils/format.js` for money/percentage display; keep financial
  arithmetic deterministic (PROJECT_SUMMARY §14).
- Dev note: use `:5173` for browser checks (CORS allows only `:5173`); a
  stale Vite server there will push a new `npm run dev` to `:5174`.

---

## Prompt 3 — Multi-Source Financial Data Ingestion

### Status

Completed

### Objective

Implement CSV ingestion, validation, normalization, and in-memory storage for
Orders, Payments, Refunds, Fees, and Settlements.

### Tasks Completed

- Verified the existing project state (Prompts 1–2) before changing anything.
- Added a layered backend: `config.py`, `errors.py`, in-memory `data_store`,
  ingestion service, Pydantic schemas, and an ingestion router.
- Implemented full-dataset validation (columns, amounts, dates, currency,
  identifiers, empty file, file type, source) with a structured error envelope.
- Implemented normalization (column aliasing, trimming, currency upper-casing,
  date → YYYY-MM-DD, amounts → Decimal; identifiers preserved verbatim).
- Implemented transaction safety (validate fully before store; replacement, not
  append; failed replacement preserves the existing dataset).
- Built the frontend Reconciliation page (Prompt 3 part): upload panel with
  source select + drag/drop + `.csv` pre-check + status messages; data-sources
  status table with preview and delete; extended the API service layer.
- Activated the Reconciliation nav item and route.
- Created coherent sample CSV fixtures for all five sources.

### Files Created

- Backend: `app/config.py`, `app/errors.py`, `app/stores/data_store.py`,
  `app/services/ingestion_service.py`, `app/schemas/ingestion.py`,
  `app/api/ingestion.py`, `tests/conftest.py`, `tests/test_ingestion.py`,
  `tests/fixtures/{orders,payments,refunds,fees,settlements}.csv`.
- Frontend: `src/constants/reconciliation.js`,
  `src/components/reconciliation/{UploadPanel,DataSourcesPanel}.jsx`,
  `src/pages/Reconciliation.jsx`, `src/pages/Reconciliation.css`,
  `src/pages/Reconciliation.test.jsx`.

### Files Modified

- Backend: `app/main.py` (wire error handler + ingestion router).
- Frontend: `src/services/api.js` (ingestion methods + `ApiError`),
  `src/App.jsx` (route), `src/components/layout/Sidebar.jsx` (nav ready),
  `src/index.css` (shared `.panel`/`.sr-only`/`.table-scroll` primitives).

### Supported Sources

- Orders, Payments, Refunds, Fees, Settlements.

### APIs Implemented

- `POST /api/v1/ingestion/upload`, `GET /status`, `GET /datasets`,
  `GET /datasets/{source_type}` (`?limit`), `DELETE /datasets/{source_type}`.

### Validation Implemented

- Required columns; numeric + non-negative amounts (Decimal); valid dates;
  INR-only currency; non-empty identifiers; empty-file, file-type, and
  source-type checks. Codes: MISSING_COLUMNS, INVALID_AMOUNT, INVALID_DATE,
  INVALID_CURRENCY, INVALID_DATA, EMPTY_FILE, INVALID_FILE_TYPE,
  UNSUPPORTED_SOURCE, DATASET_NOT_FOUND.

### Tests Executed

- Backend `pytest` (ingestion tests within the 30-test suite).
- Frontend `vitest` (Reconciliation page tests); `npm run build`; `oxlint`.
- Manual: uploaded all five fixtures via API + verified UI status/preview/delete.

### Test Results

- All passing. Failed-replacement-preserves-existing and replacement-not-append
  both verified.

### Issues Encountered

- Shared panel/table CSS lived only in `Dashboard.css`.

### Resolutions

- Promoted the shared primitives into `index.css` so the Reconciliation page is
  not coupled to the dashboard's stylesheet.

### Deviations From Prompt

- Per the user's instruction ("I'll do the manual testing"), automated frontend
  ingestion tests were kept light (a focused Reconciliation page suite) rather
  than the full Test 1–9 list; backend ingestion tests are comprehensive.
- Reconciliation `run` requires all five datasets (returns MISSING_DATASET
  otherwise), matching the prompt's complete-workflow example.

### Current Project State

Ingestion is fully working end-to-end. Storage is in-memory only (no DB).

### Notes For Prompt 4

- Read normalized datasets from `store.records(source_type)`; amounts are
  `Decimal`. Do not recompute or re-validate — ingestion guarantees clean data.

---

## Prompt 4 — Core Multi-Source Reconciliation Engine

### Status

Completed

### Objective

Implement deterministic reconciliation across Orders, Payments, Refunds, Fees,
and Settlements.

### Reconciliation Formula

Payment − Refunds − Fees − Taxes = Expected Settlement
Expected Settlement − Actual Settlement = Difference
MATCHED iff abs(Difference) <= RECONCILIATION_TOLERANCE (₹0.01, configurable).

### Statuses Implemented

- MATCHED, MISMATCH, MISSING_SETTLEMENT, ORDER_NOT_FOUND, DUPLICATE_PAYMENT.
- Priority: DUPLICATE_PAYMENT → ORDER_NOT_FOUND → MISSING_SETTLEMENT → MISMATCH
  → MATCHED. Orphan refund/fee/settlement records reported in the summary.

### APIs Implemented

- `POST /api/v1/reconciliation/run`, `GET /summary`, `GET /results`
  (`?status`, `?search`, `?limit`), `GET /results/{payment_id}`.

### Files Created

- Backend: `app/services/reconciliation_service.py`,
  `app/schemas/reconciliation.py`, `app/api/reconciliation.py`,
  `tests/test_reconciliation.py`.
- Frontend: `src/components/reconciliation/{ReconciliationRunner,
  ReconciliationResults}.jsx`.

### Files Modified

- Backend: `app/main.py` (wire reconciliation router); `app/config.py`
  (tolerance already present).
- Frontend: `src/services/api.js` (reconciliation methods),
  `src/pages/Reconciliation.jsx` (runner + results + run state).

### Tests Executed

- Backend `pytest` — 30 tests total (engine unit tests + ground-truth run).
- Frontend `vitest` — 15 tests; `npm run build`; `oxlint`. Live browser E2E.

### Test Results

- 30 backend + 15 frontend passing; build + lint clean.

### Ground Truth Evaluation

- Fixture run (8 payments): matched 4, mismatch 2, missing_settlement 1,
  order_not_found 1, duplicate_payment 0, orphans settlements 1 / refunds 1 /
  fees 1, total_difference ₹8,092 — asserted in `test_full_run_ground_truth`
  and confirmed identical via the live API and UI.

### Issues Encountered

- oxlint flagged a synchronous-looking setState in the page's mount effect.

### Resolutions

- Restructured the mount fetch to the canonical async-in-effect pattern with an
  `active` guard; lint is clean.

### Deviations From Prompt

- Testing kept simple per the user's instruction: engine unit tests + one
  ground-truth integration run (no separate exhaustive frontend suite). All
  critical deterministic behavior is covered by backend tests.

### Current Project State

Deterministic reconciliation works end-to-end (ingest → run → summary → results
→ explainable detail). Results are in-memory (latest run only). No AI, no
leakage classification, no database.

### Notes For Prompt 5

- Prompt 5 = Exception Detection, Leakage Quantification & Finance Review.
- Consume `store.get_reconciliation()` results as evidence — every result already
  carries the full calculation; do NOT recompute financial facts or use AI for
  the deterministic numbers.
- Money crosses the API as 2dp strings; parse before formatting on the frontend.
- Reuse the status set/priority; add leakage/exception concepts on top rather
  than changing the engine's deterministic output.

## Prompt 5 — Exception Management

### Status
Completed.

### Objective
Turn deterministic reconciliation results into reviewable exceptions with
affected amount, potential leakage, severity, and priority, plus a review
lifecycle — all deterministic, no AI.

### Tasks Completed
- Exception generation (idempotent, stable IDs, preserves review state), one
  primary exception per reconciliation problem; MATCHED → none.
- Leakage = max(difference,0); affected amount per type; severity thresholds;
  deterministic priority; lifecycle OPEN/IN_REVIEW/RESOLVED/ESCALATED with
  validated transitions and required resolution/escalation notes.
- Exception REST API + Finance Exception Queue UI (summary, distributions,
  filters/search, detail modal with the deterministic calculation and review
  actions). Dashboard gained a live real-data panel.

### APIs
`POST /api/v1/exceptions/generate`, `GET /summary`, `GET `, `GET /{id}`,
`PATCH /{id}/status`.

### Files Created (backend)
`services/exception_service.py`, `schemas/exceptions.py`, `api/exceptions.py`,
`tests/test_exceptions.py`. (frontend) `constants/exceptions.js`,
`components/exceptions/*`, `pages/Exceptions.jsx/.css/.test.jsx`,
`components/dashboard/LiveStatusPanel.jsx`.

### Tests / Results
`test_exceptions.py` (16) — detection per type, leakage, severity boundaries,
priority ordering, idempotency, transitions, required notes. All pass.

### Deviations
Kept the existing state model (OPEN→IN_REVIEW before RESOLVED) rather than the
prompt's illustrative OPEN→RESOLVED, per "use the existing state model".

## Prompt 6 — AI Investigation (advisory)

### Status
Completed.

### Objective
Add an advisory, validated, evidence-grounded AI investigation layer that never
changes financial values or resolves exceptions.

### Tasks Completed
- Evidence-bundle builder (only relevant records, traceable); provider
  abstraction + deterministic mock; system prompt (safety contract);
  validate → ground → confidence-safety pipeline; typed investigation result;
  investigation API + AI panel in the exception detail UI.

### AI Provider
`mock` (deterministic; env-configured `AI_PROVIDER`/`AI_API_KEY`/`AI_MODEL`); no
real LLM wired. Credentials never exposed to the frontend.

### Safety
Confidence <70 → ESCALATE; 70–89 AUTO_RESOLVE → REVIEW; ≥90 stands (advisory).
AUTO_RESOLVE never auto-resolves. Grounding rejects invented/incorrect records.

### Files Created (backend)
`ai/provider.py`, `ai/system_prompt.py`, `services/evidence_service.py`,
`services/investigation_service.py`, `schemas/investigation.py`,
`api/investigations.py`, `tests/test_investigations.py`. (frontend)
`components/exceptions/AiInvestigation.jsx`.

### Tests / Results
`test_investigations.py` (24) — schema validation, evidence grounding, safety,
provider failure, invalid response, API, ground-truth classifications. All pass.

### Deviations
None.

## Prompt 7 — Finance Controller Copilot

### Status
Completed.

### Objective
A controlled decision-support Copilot answering finance questions from
registered read-only backend tools, preserving numeric integrity.

### Features
Deterministic keyword intent detection (EXCEPTION_INVESTIGATION/EXPLANATION,
ANALYTICS_SUMMARY, LEAKAGE_TREND, FINANCIAL_IMPACT, RISK_PRIORITIES,
RESOLUTION_PERFORMANCE) → registered read-only tools → deterministic answer
composition. No mutation, no SQL, no unregistered tools.

### Tools
get_exception, get_investigation, get_analytics_summary, get_leakage_trend,
get_exception_financial_impact, get_risk_priorities, get_resolution_performance.

### Guardrails
Answers are templated from backend tool results (every number from the backend);
user-message prompt injection cannot change deterministic numbers.

### Files Created
Backend `services/copilot_service.py`, `schemas/copilot.py`, `api/copilot.py`.
Frontend `pages/Copilot.jsx/.css/.test.jsx`.

### Tests / Results
`test_copilot.py` (intent mapping, numeric integrity, injection, unregistered
tool blocked). All pass.

### Deviations
Copilot tools are strictly read-only (investigate is not triggered) to keep the
Copilot non-mutating.

## Prompt 8 — Human-in-the-Loop Finance Operations

### Status
Completed.

### Objective
Complete human review with Resolve/Escalate/**Reject** and a single append-only
audit trail; AI clearly distinguished from human decisions.

### Human Decisions
Added REJECTED terminal state (reason required). Transitions:
OPEN/IN_REVIEW/ESCALATED → REJECTED. Each decision records reviewer + reason.

### Audit Trail
`audit_service` (one system) records EXCEPTION_CREATED, AI_INVESTIGATION,
REVIEW_STARTED, RESOLVED, ESCALATED, REJECTED (who/what/when/why). Exposed at
`GET /exceptions/{id}/audit` and rendered as a timeline in the detail modal.
Double-submit prevented (buttons disable during requests).

### Files Created/Modified
Backend `services/audit_service.py`; modified `config.py`, `data_store.py`,
`exception_service.py`, `investigation_service.py`, `schemas/exceptions.py`,
`api/exceptions.py`. Frontend `ExceptionDetail.jsx` (reject, audit, risk, human
decision), `constants/exceptions.js`, `ExceptionsTable.jsx` (risk column).

### Tests / Results
`test_audit.py` (reject requires reason, reject sets state, audit lifecycle, AI
audit event, analytics reflects human decision). All pass.

### Deviations
None.

## Prompt 9 — Finance Analytics, Leakage Trends, Risk Prioritization & Executive Insights

### Status
Completed.

### Analytics / Metrics
`analytics_service`: summary (match/exception/resolution rates, leakage; no
divide-by-zero; filters + date-range validation), leakage trend (daily, keyed on
payment date; `available:false` when undated), exception distribution (count +
impact, ranked by impact), risk priorities.

### Risk Scoring
`risk = 0.50·amount + 0.25·severity + 0.15·age + 0.10·status` (each 0–100);
levels 0–24 LOW / 25–49 MEDIUM / 50–74 HIGH / 75–100 CRITICAL. Tie-break: risk
desc → discrepancy desc → oldest first. Deterministic + explainable (drivers).

### APIs
`GET /analytics/summary|leakage-trend|exception-distribution|risk-priorities|insight`.

### AI Insights
`insight_service` builds validated metrics then the provider composes an
executive summary using only those numbers; grounding on cited exceptions;
graceful `available:false` on AI failure (analytics never breaks).

### Frontend
`pages/Analytics.jsx` — 9 summary cards, leakage-trend chart, financial-impact
bars, risk-priorities table (links into exception detail), AI Finance Insight.

### Files Created
Backend `services/analytics_service.py`, `services/insight_service.py`,
`formatting.py`, `schemas/analytics.py`, `api/analytics.py`,
`tests/test_analytics.py`. Frontend `pages/Analytics.jsx/.css/.test.jsx`.

### Tests / Results
`test_analytics.py` (15) + insight tests in `test_copilot.py` — rates, leakage,
distribution, risk determinism/ordering/tie, filters, date validation, trend
availability, insight uses backend metrics, insight failure graceful. All pass.

### Deviations
Distribution "Refund Mismatch" example adapted to the actual exception types.

## Prompt 10 — Final Integration, End-to-End Validation & Polish

### Status
Completed.

### Final Features Verified (live browser, against running backend)
Ingest → reconcile → generate exceptions → open exception → AI investigate →
review evidence + recommendation → Resolve / Escalate / Reject with reasons →
audit trail → analytics (summary, leakage trend, impact, risk) → AI insight →
Copilot question answered from deterministic backend data. Analytics updated
automatically after each human decision (e.g. leakage dropped when an exception
was resolved). Verified without any manual database editing.

### Improvements
- Fixed a real CORS bug: added `PATCH` to `allow_methods` (status endpoint).
- Nav activated for Analytics + Copilot; risk column added to the queue; audit
  timeline + human-decision line + risk drivers in the detail modal.
- Added `backend/.env.example`; confirmed no secrets in source; `.gitignore`
  covers `.env`, `venv`, `node_modules`, `__pycache__`, `dist`, `.pytest_cache`.

### Testing
- Backend: `pytest` → **99 passed**.
- Frontend: `vitest run` → **24 passed**; `npm run build` succeeds; `oxlint` clean.

### Demo Dataset / Ground Truth
`backend/tests/fixtures/*.csv` (8 payments): 4 MATCHED, 2 MISMATCH, 1
MISSING_SETTLEMENT, 1 ORDER_NOT_FOUND, plus 1 orphan settlement/refund/fee.
Reconciliation total difference ₹8,092; asserted by
`test_reconciliation.py::test_full_run_ground_truth` and analytics tests.

### Known Limitations
In-memory storage; mock AI only (no real LLM); synthetic data; Prompt-2 dashboard
KPI cards remain synthetic (live panel shows real data); no auth; INR-only.

### Final Project State
FeeLeak MVP complete. Deterministic where correctness matters, AI where
explanation adds value, human-controlled for decisions, auditable throughout.

### Future Improvements
Persistent DB; real LLM provider behind the existing abstraction; wire dashboard
KPI cards to live data; auth/RBAC; multi-currency; run history; deployment.
