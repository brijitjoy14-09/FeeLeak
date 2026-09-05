# FeeLeak — Project Summary

> **Purpose of this document:** persistent technical context for AI agents.
> Read this file (and `TASK_LOG.md`) before making changes. It describes what
> **currently exists** — not future/aspirational functionality. Do not describe
> unbuilt features as if they are implemented.

---

## 1. Project Overview

FeeLeak is an AI-powered, multi-source financial reconciliation and leakage
detection platform for the **AI Finance Controller** use case. The repository
currently contains: (1) the Prompt 1 foundation (FastAPI + React/Vite health
check); (2) the Prompt 2 **Finance Controller Dashboard** on synthetic data
(§19); (3) Prompt 3 **Multi-Source Data Ingestion** (§20); (4) Prompt 4 **Core
Reconciliation Engine** — deterministic, Decimal-based (§21); (5) Prompt 5
**Exception Management** — deterministic exceptions with severity/priority,
review workflow, and leakage (§22); and (6) Prompt 6 **AI Investigation** — an
advisory, validated, evidence-grounded explanation layer with a mock provider
(§23). The deterministic engine remains the only source of financial truth; AI
never changes financial values or resolves exceptions.

## 2. Business Problem

Businesses receive money through payment processors and marketplaces where the
final settled amount is the result of many moving parts — gross payments,
refunds, platform/processor fees, and adjustments. Discrepancies between what
*should* have settled and what *actually* settled represent **financial
leakage** that is easy to miss at scale. Finance teams need a reliable,
auditable way to detect and explain these differences.

## 3. Product Objective

Eventually, FeeLeak will:

1. Ingest financial data from multiple sources.
2. Match related records across those sources.
3. Calculate expected financial values deterministically.
4. Compare expected values against actual settlement values.
5. Detect discrepancies.
6. Identify potential unexplained financial leakage.
7. Use AI to investigate and explain discrepancies.
8. Classify and prioritize exceptions.
9. Escalate uncertain cases for human finance-team review.
10. Provide finance-oriented analytics and insights.

Progress: **all ten steps are implemented** (Prompts 1–10). Steps 1–6 are
deterministic (§20, §21); step 7 is advisory AI investigation (§23); step 8 is
exception classification/prioritization with risk (§22); step 9 is human-review
escalation with a full audit trail (§22); step 10 is finance analytics, risk
priorities, executive insights, and the Copilot (§24). See §17 for status.

## 4. Target Use Case

AI Finance Controller — reconciling multiple financial sources:

- Orders
- Payments
- Refunds
- Fees
- Settlements

## 5. Technology Stack

| Layer        | Technology                                                      |
| ------------ | --------------------------------------------------------------- |
| Frontend     | React 19, Vite 8, React Router 7                                |
| FE charts    | Hand-built dependency-free SVG/CSS (no chart library)           |
| FE testing   | Vitest 3, @testing-library/react, jest-dom, jsdom               |
| FE linting   | oxlint (pre-existing)                                            |
| Backend      | Python 3.14, FastAPI, Uvicorn, Pydantic v2                       |
| CSV parsing  | pandas (ingestion); `python-multipart` for uploads              |
| Money        | Python `Decimal` for all ingested amounts + reconciliation math |
| BE testing   | pytest, httpx (via Starlette `TestClient`)                      |
| Transport    | REST / JSON over HTTP, CORS-restricted                          |
| Storage      | In-memory only (no database yet — see §15)                      |

## 6. Architecture

```text
React + Vite (frontend, :5173)
  ├─ /dashboard      → Finance Controller Dashboard (mock data)
  ├─ /reconciliation → Ingestion + Reconciliation (REAL backend data)
  └─ /exceptions /analytics /settings → ComingSoon
        │  REST /api/v1/...            │ GET /health (sidebar dot)
        ▼                              ▼
FastAPI (backend, :8000)
  api/ingestion.py ──► services/ingestion_service.py ─┐
  api/reconciliation.py ► services/reconciliation_service.py
        │                                              │
        └──────────► stores/data_store.py (in-memory singleton) ◄─┘
                       datasets + latest reconciliation run
```

- Components never call the backend directly — all calls go through
  `frontend/src/services/api.js` (env-driven `VITE_API_BASE_URL`, never
  hardcoded).
- **The dashboard** consumes mock data (`getDashboardData`) and does not call
  the backend. **The Reconciliation page** uses the real ingestion/
  reconciliation APIs.
- Backend layers are separated: thin routers → services (validation,
  normalization, reconciliation) → in-memory store. `main.py` only wires them.
- **Deterministic vs. AI logic** is a core principle — financial math is
  deterministic `Decimal` code; AI is future work (see §13, §14, §21).

## 7. Current Project Structure

```text
FeeLeak/
├── frontend/
│   ├── .env                     # VITE_API_BASE_URL (gitignored)
│   ├── .env.example             # tracked template
│   ├── index.html               # title: "FeeLeak — AI Finance Controller"
│   ├── package.json             # + react-router-dom, test scripts
│   ├── vite.config.js           # vitest config, esbuild jsx: automatic
│   └── src/
│       ├── main.jsx             # unchanged entry point
│       ├── App.jsx              # Router + AppLayout + routes
│       ├── App.css              # layout / sidebar / topbar styles
│       ├── App.test.jsx         # 4 connectivity/shell tests
│       ├── index.css            # design tokens + base (light/dark)
│       ├── services/api.js      # getHealth()
│       ├── hooks/useBackendHealth.js
│       ├── utils/format.js      # formatINR / formatNumber / formatPercent
│       ├── data/dashboardData.js # SYNTHETIC dashboard data (per period)
│       ├── constants/reconciliation.js  # SOURCES + status metadata
│       ├── components/
│       │   ├── layout/AppLayout.jsx, Sidebar.jsx
│       │   ├── dashboard/…               # Prompt 2 dashboard components
│       │   └── reconciliation/UploadPanel.jsx, DataSourcesPanel.jsx,
│       │       ReconciliationRunner.jsx, ReconciliationResults.jsx
│       ├── pages/
│       │   ├── Dashboard.jsx (+ .css, .test.jsx)
│       │   ├── Reconciliation.jsx (+ .css, .test.jsx)  # ingestion + engine UI
│       │   └── ComingSoon.jsx
│       └── test/setup.js
│
├── backend/
│   ├── venv/                    # pre-existing Python 3.14 venv (reused)
│   ├── app/
│   │   ├── main.py              # wiring: CORS, error handler, routers, /health
│   │   ├── config.py           # sources, schemas, currency, tolerance
│   │   ├── errors.py           # AppError + JSON error handler
│   │   ├── api/ingestion.py, reconciliation.py       # routers
│   │   ├── services/ingestion_service.py, reconciliation_service.py
│   │   ├── schemas/ingestion.py, reconciliation.py   # Pydantic models
│   │   └── stores/data_store.py                       # in-memory singleton
│   ├── tests/
│   │   ├── conftest.py         # store reset + upload helper
│   │   ├── test_main.py        # 3 foundation tests
│   │   ├── test_ingestion.py   # ingestion validation tests
│   │   ├── test_reconciliation.py  # engine unit + ground-truth tests
│   │   └── fixtures/*.csv      # coherent sample datasets
│   └── requirements.txt
│
├── README.md
├── PROJECT_SUMMARY.md
├── TASK_LOG.md
└── .gitignore
```

## 8. Implemented Features

**Prompt 1 (foundation):**

- FastAPI application with metadata (title/description/version).
- `GET /` and `GET /health` endpoints; Swagger UI at `/docs`.
- CORS restricted to the local frontend origins.
- Frontend API service layer + health-check hook; env-driven backend URL.

**Prompt 2 (Finance Controller Dashboard — synthetic data):**

- Routed app shell: fixed dark sidebar + main content (React Router 7).
- Navigation for Dashboard / Reconciliation / Exceptions / Analytics /
  Settings; only Dashboard is functional, others show a "Coming soon" page.
- Backend connectivity indicator moved into the sidebar footer (preserves the
  Prompt 1 health check).
- Dashboard at `/dashboard` (root redirects there): four KPI cards, a
  reconciliation summary bar, a records/match-rate trend chart, an exception
  distribution donut, and a recent-exceptions table.
- Period filter (Today / Last 7 Days / Last 30 Days) that re-derives all mock
  metrics, frontend-only.
- Reusable INR / number / percent formatters; structured mock data module.
- See §19 for full dashboard detail.

**Prompt 3 (Multi-Source Data Ingestion):**

- CSV upload, validation, normalization, and in-memory storage for the five
  sources (orders, payments, refunds, fees, settlements).
- Ingestion REST API under `/api/v1/ingestion` (upload/status/datasets/delete).
- Frontend Reconciliation page (`/reconciliation`) with an upload panel,
  dataset status table, per-source preview, and delete.
- See §20 for full ingestion detail.

**Prompt 4 (Core Reconciliation Engine):**

- Deterministic, Decimal-based reconciliation over the normalized datasets:
  per-payment expected/actual settlement, difference, and status.
- Reconciliation REST API under `/api/v1/reconciliation`
  (run/summary/results/result).
- Reconciliation UI extension: dataset readiness, run control, summary cards,
  filterable/searchable results table, and an explainable per-payment
  calculation detail modal.
- See §21 for full reconciliation detail.

**Prompt 5 (Exception Management):**

- Deterministic exceptions from reconciliation results (one per problem), with
  affected amount, potential leakage, severity, and priority; idempotent
  generation that preserves review state.
- Lifecycle (OPEN/IN_REVIEW/RESOLVED/ESCALATED) with validated transitions;
  resolution/escalation require a note.
- Exception REST API under `/api/v1/exceptions`; Finance Exception Queue UI
  (`/exceptions`) with summary KPIs, distributions, filters/search, and a detail
  modal. Dashboard gained a live real-data panel. See §22.

**Prompt 6 (AI Investigation — advisory only):**

- Evidence-bundle builder, provider abstraction + deterministic mock, and a
  validate → ground → safety pipeline producing a typed investigation result.
- AI investigation REST API under `/api/v1/exceptions/{id}/investigate` +
  `/investigation`; AI panel in the exception detail UI. See §23.

**Explicitly NOT implemented:** real (non-mock) LLM provider wiring; automatic
resolution or any AI-driven change to financial values/status; advanced leakage
categorization/prioritization beyond severity; a real dashboard data wiring
(the synthetic KPI cards remain, alongside a live panel); persistent database
storage; authentication; production deployment; external payment APIs;
Prompt 7 (Copilot / natural-language investigation).

## 9. API Endpoints

| Method | Path      | Response                              | Status |
| ------ | --------- | ------------------------------------- | ------ |
| GET    | `/`       | `{"message": "FeeLeak API is running"}` | 200  |
| GET    | `/health` | `{"status": "healthy"}`               | 200    |
| GET    | `/docs`   | Swagger UI (FastAPI default)          | 200    |

**Ingestion (Prompt 3, prefix `/api/v1/ingestion`):**

| Method | Path                      | Purpose                               |
| ------ | ------------------------- | ------------------------------------- |
| POST   | `/upload`                 | Upload a CSV (`source_type` + `file`) |
| GET    | `/status`                 | Loaded state + record counts per source |
| GET    | `/datasets`               | Metadata for loaded datasets (no rows) |
| GET    | `/datasets/{source_type}` | Normalized records (`?limit=`, default 100) |
| DELETE | `/datasets/{source_type}` | Remove a loaded dataset               |

**Reconciliation (Prompt 4, prefix `/api/v1/reconciliation`):**

| Method | Path                    | Purpose                                  |
| ------ | ----------------------- | ---------------------------------------- |
| POST   | `/run`                  | Run reconciliation over loaded datasets  |
| GET    | `/summary`              | Run metadata + summary + orphan records  |
| GET    | `/results`              | Results (`?status=`, `?search=`, `?limit=`) |
| GET    | `/results/{payment_id}` | One payment's reconciliation result      |

**Exceptions (Prompt 5, prefix `/api/v1/exceptions`):**

| Method | Path                    | Purpose                                    |
| ------ | ----------------------- | ------------------------------------------ |
| POST   | `/generate`             | (Re)generate exceptions (idempotent)       |
| GET    | `/summary`              | Counts, active KPIs, severity/type dists   |
| GET    | ``                      | List (`?status`,`?type`,`?severity`,`?search`,`?sort`,`?limit`) |
| GET    | `/{exception_id}`       | One exception                              |
| PATCH  | `/{exception_id}/status`| Transition status (note/reason enforced)   |

**AI Investigation (Prompt 6, prefix `/api/v1/exceptions`):**

| Method | Path                            | Purpose                          |
| ------ | ------------------------------- | -------------------------------- |
| POST   | `/{exception_id}/investigate`   | Run AI investigation (advisory)  |
| GET    | `/{exception_id}/investigation` | Latest investigation             |

All errors use the envelope `{"success": false, "error": {code, message,
details?}}` (codes in §20/§22/§23). CORS `allow_methods` includes `PATCH` (the
status endpoint uses it). The dashboard's synthetic KPI cards call none of these,
but its live panel reads reconciliation + exception summaries.

**Frontend routes** (React Router): `/` → redirect to `/dashboard`;
`/dashboard` (mock KPIs + live panel); `/reconciliation` (real ingestion +
reconciliation); `/exceptions` (real exceptions + AI); `/analytics`, `/settings`
(Coming soon); unknown paths redirect to `/dashboard`.

## 10. Frontend Configuration

- **Env var:** `VITE_API_BASE_URL` (default `http://localhost:8000`), read via
  `import.meta.env.VITE_API_BASE_URL`.
- `frontend/.env` holds the local value and is gitignored;
  `frontend/.env.example` is tracked.
- **Scripts:** `dev`, `build`, `lint`, `preview`, `test` (`vitest run`),
  `test:watch` (`vitest`).
- **Testing:** Vitest with `jsdom`, globals enabled, setup file
  `src/test/setup.js`. `esbuild.jsx: 'automatic'` is set so Vitest's esbuild
  transform resolves JSX without an explicit React import (Vite's own build
  uses oxc + plugin-react and ignores this option — this is expected).

## 11. Backend Configuration

- **App factory:** module-level `app` in `backend/app/main.py`.
- **Metadata:** title `FeeLeak API`, description
  `AI-powered financial reconciliation backend`, version `1.0.0`.
- **CORS:** `ALLOWED_ORIGINS = ["http://localhost:5173",
  "http://127.0.0.1:5173"]`; methods `GET, POST, PUT, PATCH, DELETE, OPTIONS`
  (PATCH is required by the exception status endpoint); kept as a list so
  production origins can be appended later. Unrestricted `"*"` is avoided.
- **AI config (Prompt 6):** `AI_PROVIDER` (default `mock`), `AI_API_KEY`,
  `AI_MODEL`, `AI_TIMEOUT_SECONDS` come from env vars; only the mock provider
  ships. Credentials are never exposed to the frontend.
- **venv:** pre-existing `backend/venv` (Python 3.14.3) is reused — do not
  create a new one.
- **Run:** `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`.

## 12. Testing

**Backend (`pytest`, 70 tests, all passing):**

- `test_main.py` (3): root, health, and app-import.
- `test_ingestion.py`: upload/validation/normalization + transaction safety.
- `test_reconciliation.py`: engine unit tests + ground-truth run.
- `test_exceptions.py` (16): detection per type, matched→zero, leakage rules,
  severity boundaries (499.99→CRITICAL cases), priority ordering, idempotency,
  transitions (valid/invalid), resolution/escalation required, summary excludes
  resolved.
- `test_investigations.py` (24): schema validation (bad classification/action/
  confidence/malformed evidence), evidence grounding (nonexistent/incorrect/
  invented/unsupported references rejected), safety (AUTO_RESOLVE@95 stays,
  @72→REVIEW, <70→ESCALATE, AI cannot change values or auto-resolve),
  INSUFFICIENT_EVIDENCE, provider failure, invalid response, API endpoints, and
  ground-truth classifications (MISSING_SETTLEMENT / ORDER_MAPPING_ERROR /
  DUPLICATE_TRANSACTION / INSUFFICIENT_EVIDENCE via the mock).

**Frontend (`vitest`, 19 tests across 4 files, all passing; API mocked —
no live backend needed):**

`src/App.test.jsx` — shell + connectivity (4):
1. App renders without crashing.
2. FeeLeak brand is displayed.
3. Shows **Connected** when the backend reports healthy.
4. Shows **Disconnected** without crashing when the backend call fails.

`src/pages/Dashboard.test.jsx` — dashboard (6):
1. Dashboard overview renders.
2. Default-period KPIs show `500`, `92.4%`, `38`, `₹24,850`.
3. Switching period to Last 30 Days updates metrics (`2,184`, `91.7%`).
4. Recent-exceptions table renders (`TXN-10021`, `Amount Mismatch`, `₹800`).
5. Dashboard still renders when the backend health check fails (mock data).
6. Navigation lists all five sections; only Dashboard is active.

`src/pages/Reconciliation.test.jsx` (5): ingestion/reconciliation UI states.

`src/pages/Exceptions.test.jsx` (4): queue renders with summary + table; detail
modal shows the deterministic calculation and the AI section; running AI shows
the advisory recommendation (status unchanged); resolve requires a note.

All suites were executed and passed (`npm test`, `pytest`). `npm run build` and
`oxlint` also pass. The full **ingest → reconcile → generate exceptions → review
(Start Review, Resolve with required note) → AI investigate** flow was verified
end-to-end in a live browser against the backend, including the dashboard live
panel and resolved-exception exclusion from active leakage.

## 13. Important Design Decisions

- **Service layer isolation:** components never call `fetch` directly; all
  backend access is via `services/api.js` + `hooks/useBackendHealth.js`.
- **Config over hardcoding:** backend URL comes only from `VITE_API_BASE_URL`.
- **Explicit CORS:** allow-list of dev origins, structured for later prod
  additions; never `allow_origins=["*"]`.
- **Thin `main.py`:** application wiring only; future business logic will live
  in dedicated routers/services, not in `main.py`.
- **Preserve existing setup:** the pre-existing Vite app, `node_modules`, and
  `backend/venv` were reused, not recreated. Existing CSS variables and dark
  mode were kept.
- **AI vs. deterministic logic** — see §14.

## 14. Financial Logic Principles

**Deterministic application code** (not AI) will own all financial arithmetic
so calculations stay testable, reproducible, and auditable. Examples: payment
amount, refund amount, fee amount, expected settlement, actual settlement, and
the difference between them.

Future reconciliation concept (not yet implemented):

```text
Payment − Refund − Fees ± Adjustments = Expected Settlement

Expected Settlement  vs.  Actual Settlement  →  unexplained difference
```

**AI responsibilities (future prompts only):** discrepancy investigation,
evidence-based explanation, exception classification, prioritization,
natural-language finance summaries, and recommendations for human review. AI
must **never** perform the basic financial arithmetic above.

> As of Prompt 4 the deterministic reconciliation engine **is implemented**
> (see §21) using `Decimal`. AI interpretation of its results is still future
> work.

## 15. Current Limitations

- **Storage is in-memory only.** Datasets, reconciliation results, exceptions,
  investigations, and the audit trail live in a single process-wide store and
  are lost on restart. No database has been introduced.
- **AI is advisory only** — a deterministic **mock** provider ships (no external
  LLM wired). AI never computes financial values, sets risk, or resolves
  exceptions; human confirmation is always required.
- **Synthetic datasets** — all data is demo CSV; no real payment-provider
  integration and no money movement.
- **The Prompt-2 dashboard KPI cards remain synthetic** (a clearly-labelled
  "Live Reconciliation & Exceptions" panel shows real data alongside them).
- Currency is INR-only (no FX). Only the latest reconciliation run is kept.
- No authentication (a demo `finance-controller` identity is used for audit).
- Risk **age** component is ~0 for freshly generated exceptions (synthetic data
  has no exception ageing); the formula supports age but it rarely contributes.
- AI insight/investigation are only as good as the supplied evidence; no real-AI
  accuracy claim is made (the mock is deterministic).

## 16. Future Implementation Roadmap

The FeeLeak MVP (Prompts 1–10) is complete. Genuine future work, none of which is
implemented: persistent database storage; a real LLM provider behind the existing
`AIInvestigationProvider` abstraction; wiring the Prompt-2 dashboard KPI cards to
live data; authentication/RBAC; multi-currency/FX; persistent reconciliation/run
history; production deployment. **Prompt 7 (Copilot), 8 (human review + audit),
9 (analytics/risk/insights), and 10 (integration/polish) are DONE.**

## 17. Current Development Status

**Prompts 1–10 — COMPLETE.** Foundation, dashboard, ingestion, reconciliation,
exception management, AI investigation, Finance Copilot, human review with
Resolve/Escalate/Reject + audit trail, analytics (summary, leakage trend,
financial impact, risk priorities), AI executive insights, and final integration.

Backend: **99 pytest tests pass**. Frontend: **24 vitest tests pass**;
`npm run build` and `oxlint` succeed. The complete workflow — ingest → reconcile
→ generate exceptions → AI investigate → human Resolve/Escalate/Reject → audit
→ analytics → risk priorities → Copilot — was verified end-to-end in a live
browser against the running backend.

## 18. Notes for the Next AI Agent

- Start by reading this file and `TASK_LOG.md`; do not assume features exist
  beyond §8.
- Reuse `backend/venv` and the existing frontend `node_modules`; do not
  reinitialize the project or Vite.
- Keep `backend/app/main.py` thin — add new backend logic in separate
  routers/services.
- Keep frontend backend-calls inside `services/` (extend `api.js`); read config
  from `VITE_API_BASE_URL`.
- Do not hardcode backend URLs; do not widen CORS to `"*"`.
- Keep all financial arithmetic deterministic and in `Decimal` (see §14, §21).
- **Backend layout:** `app/config.py` (schemas, tolerance, sources),
  `app/errors.py` (AppError + handler), `app/stores/data_store.py` (in-memory
  singleton `store`), `app/services/*` (ingestion, reconciliation),
  `app/schemas/*` (Pydantic), `app/api/*` (routers). `main.py` only wires these.
- **Reconciliation results are read from `store`** — Prompt 5 (exceptions/
  leakage) should consume `store.get_reconciliation()` results as evidence,
  not recompute financial facts.
- **Replacing dashboard mock data with a real API:** change only
  `getDashboardData(period)` in `data/dashboardData.js`; the component tree
  consumes the same shape (see §19). This is not yet done.
- Reuse the INR/number/percent helpers in `utils/format.js` for any new money
  or percentage display. Backend money is returned as 2dp strings — parse with
  `Number(...)` before `formatINR`.
- Note: on the dev machine a Vite server may already be listening on `:5173`;
  a second `npm run dev` will pick `:5174`. CORS only allows `:5173`, so use
  `:5173` for browser verification.
- Update **both** this file and `TASK_LOG.md` after making changes.

## 19. Finance Controller Dashboard (Prompt 2)

- **Route:** `/dashboard` (root and unknown paths redirect here). Rendered
  inside `AppLayout` (sidebar + main).
- **Components** (`src/components/dashboard/`): `DashboardHeader` (title +
  period `<select>` + "Synthetic data" badge), `KpiCard` (reused ×4),
  `ReconciliationSummary`, `ReconciliationTrend`, `ExceptionDistribution`,
  `RecentExceptions`. Layout/nav: `AppLayout`, `Sidebar`. Page: `Dashboard`.
- **Mock data** (`src/data/dashboardData.js`): keyed by period (`today`, `7d`,
  `30d`). Each period supplies `kpis`, `summary`, `trend[]`, `distribution[]`,
  `recentExceptions[]`. Clearly labelled synthetic/demo. `getDashboardData()`
  is the API seam. `PERIODS` and `DEFAULT_PERIOD` (`7d`) are exported.
- **KPI cards:** Records Processed (+Δ vs previous), Match Rate (with progress
  bar + `matched / total`), Exceptions (+ require-review), Potential Leakage
  (INR, + unresolved). Term used is "Potential Leakage" — never "confirmed
  loss".
- **Charts:** hand-built dependency-free SVG. Trend = bars (records) + line
  (match rate). Distribution = donut with legend (count + %). Summary = a
  single proportional matched/resolved/unresolved bar + stat chips.
- **Exception table:** semantic `<table>` with `scope`ed headers; status shown
  as a text badge (colour + label, never colour-only): Resolved/Review/
  Investigating/Unresolved.
- **Period filter:** `Today` / `Last 7 Days` / `Last 30 Days`; re-derives all
  metrics client-side.
- **Formatting:** `utils/format.js` — `formatINR` (Indian grouping,
  `₹1,12,400`), `formatNumber` (`2,184`), `formatPercent` (`92.4%`).
- **Responsive:** desktop-first; KPI grid 4→2→1, charts 2→1 columns; sidebar
  becomes a toggled drawer under 900px (menu button in the top bar).
- **Backend independence:** the dashboard consumes mock data and renders even
  when the backend is down; only the sidebar's connectivity dot depends on
  `/health`.
- **No fake AI, no real financial claims:** there is no AI-generated text; all
  figures are explicitly synthetic (badge + code comments).

## 20. Multi-Source Data Ingestion (Prompt 3)

**Data sources:** orders, payments, refunds, fees, settlements (defined once in
`app/config.py:SUPPORTED_SOURCES`).

**Architecture:**

```text
CSV Upload → API (app/api/ingestion.py)
           → Ingestion Service (app/services/ingestion_service.py)
             → validation → normalization
           → In-Memory Dataset Store (app/stores/data_store.py)
```

The API layer only parses the request and shapes the response; all
validation/normalization lives in the service; the store holds normalized data.

**Normalized schemas** (per source, canonical internal column names, from
`app/config.py:SOURCE_SCHEMAS`):

- orders: `order_id, order_date, customer_id, order_amount, currency, status`
- payments: `payment_id, order_id, payment_date, payment_amount, currency, payment_status`
- refunds: `refund_id, payment_id, refund_date, refund_amount, currency, refund_status`
- fees: `fee_id, payment_id, fee_date, fee_amount, tax_amount, currency, fee_type`
- settlements: `settlement_id, payment_id, settlement_date, settlement_amount, currency, settlement_status`

**Validation (whole dataset validated before anything is stored):**

- Required columns present → else `MISSING_COLUMNS` (lists missing).
- Amount fields numeric and non-negative, parsed to `Decimal` → else
  `INVALID_AMOUNT`.
- Date fields parse against accepted formats, normalized to `YYYY-MM-DD`
  (timestamps preserved as ISO) → else `INVALID_DATE`.
- Currency ∈ {INR} → else `INVALID_CURRENCY` (no FX conversion).
- Required identifiers present and non-empty → else `INVALID_DATA`.
- Empty file / no data rows → `EMPTY_FILE`; non-CSV → `INVALID_FILE_TYPE`;
  unknown source → `UNSUPPORTED_SOURCE`; unknown dataset → `DATASET_NOT_FOUND`.

**Normalization:** column headers canonicalized (trim, lowercase, spaces/hyphens
→ underscore — a controlled alias map, not fuzzy matching); strings trimmed;
currency upper-cased; identifiers preserved verbatim (e.g. `ORD-001` stays
`ORD-001`); amounts kept as `Decimal`.

**Storage:** in-memory only (`store.datasets[source_type]` = records + columns +
count + uploaded_at + filename + status). Uploading a source **replaces** the
prior dataset (never appends). A failed upload leaves the existing valid dataset
intact (validated fully before any store write). No database.

**Errors:** consistent envelope `{"success": false, "error": {code, message,
details?}}`; no Python stack traces reach the client.

**Frontend (`/reconciliation` page, Prompt 3 part):** `UploadPanel` (source
select + drag/drop + `.csv` pre-check + status messages), `DataSourcesPanel`
(status table, first-10 preview, delete). API methods in `services/api.js`:
`uploadDataset`, `getIngestionStatus`, `getDatasets`, `getDataset`,
`deleteDataset` (all via a shared `request()` that throws `ApiError` carrying
the backend error envelope).

**Sample fixtures:** `backend/tests/fixtures/{orders,payments,refunds,fees,
settlements}.csv` — a coherent dataset (see §21 ground truth).

## 21. Core Reconciliation Engine (Prompt 4)

**Primary unit = payment.** For each payment the engine aggregates related
records and computes settlement deterministically.

**Formula (all `Decimal`, never float):**

```text
Expected Settlement = Payment − Total Refunds − Total Fees − Total Taxes
Difference          = Expected Settlement − Actual Settlement
MATCHED  iff  abs(Difference) <= RECONCILIATION_TOLERANCE   (default ₹0.01)
```

Tolerance is defined once in `app/config.py:RECONCILIATION_TOLERANCE`.

**Relationship mapping & aggregation** (via O(1) indexes built once per run —
`orders_by_id`, `refunds_by_payment`, `fees_by_payment`,
`settlements_by_payment`, no nested scans):

- Order: `payment.order_id` → orders; `order_found` flag retained.
- Refunds: sum of all `refund_amount` for the payment (supports 0..n).
- Fees: sum of all `fee_amount`; Taxes: sum of all `tax_amount` (fee and tax are
  separate deductions per the schema).
- Settlements: sum of all `settlement_amount` (supports split settlements).

**Statuses** (`MATCHED`, `MISMATCH`, `MISSING_SETTLEMENT`, `ORDER_NOT_FOUND`,
`DUPLICATE_PAYMENT`) with a **deterministic priority** (first match wins):

```text
DUPLICATE_PAYMENT → ORDER_NOT_FOUND → MISSING_SETTLEMENT → MISMATCH → MATCHED
```

Same input always yields the same status and counts (idempotent — re-running
clears prior results, never duplicates).

**Data-integrity handling:**

- Missing order → `ORDER_NOT_FOUND` (payment retained, not discarded).
- No settlement → actual = ₹0 and `MISSING_SETTLEMENT` (not a generic mismatch;
  the value is never invented).
- Duplicate `payment_id` → `DUPLICATE_PAYMENT` (never silently overwritten).
- Orphan refund/fee/settlement (references a non-existent payment) → counted in
  `summary.orphan_records`, never attached to an unrelated payment.

**Evidence:** every result carries `payment_id, order_id, order_found,
order_amount, payment_amount, total_refund, total_fee, total_tax,
expected_settlement, actual_settlement, difference, abs_difference,
refund_count, fee_count, settlement_count, status` — enough for a future AI
layer to explain without recomputing. Money is serialized as 2dp strings.

**APIs:** `POST /api/v1/reconciliation/run` (requires all five datasets, else
`MISSING_DATASET` with `missing_sources`), `GET /summary`, `GET /results`
(filter `status`, `search`, `limit`), `GET /results/{payment_id}`. Results are
held in memory (latest run only) in `store.reconciliation`.

**Frontend (`/reconciliation` page, Prompt 4 part):** `ReconciliationRunner`
(per-source readiness ✓/✕ + Run button, disabled until all five loaded),
`ReconciliationResults` (summary cards, status filter + payment/order search,
results table with text status badges, and a per-payment **detail modal showing
the full deterministic calculation**). API methods: `runReconciliation`,
`getReconciliationSummary`, `getReconciliationResults`,
`getReconciliationResult`.

**Ground truth (fixture dataset, 8 payments):** matched 4, mismatch 2,
missing_settlement 1, order_not_found 1, duplicate_payment 0, orphans
settlements 1 / refunds 1 / fees 1; total_difference ₹8,092. Asserted by
`backend/tests/test_reconciliation.py::test_full_run_ground_truth`.

**No AI:** the engine is purely deterministic; no LLM is involved in any
financial calculation or status decision.

## 22. Exception Management (Prompt 5) + Human Review & Audit (Prompt 8)

**Exception types** (one primary exception per reconciliation problem, mapping
centralized in `config.py`): `AMOUNT_MISMATCH`, `MISSING_SETTLEMENT`,
`ORDER_NOT_FOUND`, `ORPHAN_SETTLEMENT`, `ORPHAN_REFUND`, `ORPHAN_FEE`,
`DUPLICATE_PAYMENT`. `MATCHED` results create no exception.

**Lifecycle & transitions** (`exception_service.update_status`):
`OPEN → IN_REVIEW | ESCALATED | REJECTED`; `IN_REVIEW → RESOLVED | ESCALATED |
REJECTED`; `ESCALATED → IN_REVIEW | RESOLVED | REJECTED`; `RESOLVED`/`REJECTED`
are terminal. Invalid transitions are rejected. `RESOLVED`/`ESCALATED`/`REJECTED`
each require a free-text reason (`RESOLUTION_REQUIRED` / `ESCALATION_REASON_REQUIRED`
/ `REJECTION_REASON_REQUIRED`).

**Leakage & affected amount** (Decimal): `potential_leakage = max(difference, 0)`
(difference = expected − actual). `AMOUNT_MISMATCH` affected = `abs(difference)`;
`MISSING_SETTLEMENT` affected = expected (= leakage); data-integrity exceptions
(`ORDER_NOT_FOUND`, `DUPLICATE_PAYMENT`, orphans) have `potential_leakage = 0`
and affected = the relevant record amount. Merchant-favourable differences are
never counted as leakage.

**Severity** (on leakage, else affected): `<500 LOW`, `<5000 MEDIUM`,
`<25000 HIGH`, `>=25000 CRITICAL`.

**Priority**: deterministic composite of severity band, financial impact, then a
per-type operational weight (higher = surfaced first).

**Risk score (Prompt 9)** — deterministic 0–100, `compute_risk(amount, severity,
age_days, status)`:
`risk = 0.50·amount + 0.25·severity + 0.15·age + 0.10·status` where amount is
`min(amount/₹25,000, 1)·100`, severity ∈ {25,50,75,100}, age is
`min(age_days/30, 1)·100` (≈0 for fresh synthetic exceptions), status ∈
{OPEN 60, IN_REVIEW 70, ESCALATED 100, RESOLVED/REJECTED 0}. Levels: `0–24 LOW,
25–49 MEDIUM, 50–74 HIGH, 75–100 CRITICAL`. Every exception exposes `risk_drivers`
(human-readable). Risk is a **prioritization** signal, not a fraud probability.

**Idempotent generation**: `POST /exceptions/generate` regenerates from the
latest reconciliation with stable IDs (`EXC-{payment_id}` / `EXC-{record_id}`),
preserving prior review state.

**Audit trail (Prompt 8)** — one append-only log (`audit_service`): records
`EXCEPTION_CREATED`, `AI_INVESTIGATION`, `REVIEW_STARTED`, `RESOLVED`,
`ESCALATED`, `REJECTED` with who (actor) / what (event + detail) / when
(timestamp) / why (reason). Exposed at `GET /exceptions/{id}/audit`. Human
decisions and AI events are clearly distinguished (actor `finance-controller`
vs `ai:mock`).

**Exception APIs**: `POST /generate`, `GET /summary` (counts, active KPIs,
severity/type distributions — active excludes RESOLVED/REJECTED), `GET ` (list
with `status`/`type`/`severity`/`search`/`sort`/`limit`), `GET /{id}`,
`PATCH /{id}/status`, `GET /{id}/audit`.

**UI**: `/exceptions` Finance Exception Queue (summary, distributions, filters,
risk column, priority sort) → detail modal (deterministic calculation, risk +
drivers, AI investigation panel, Resolve/Escalate/Reject with required-note
dialogs, human-decision line, audit history). Double-submit is prevented (buttons
disable while a request is in flight).

## 23. AI Investigation (Prompt 6) + AI Executive Insight (Prompt 9)

**Purpose**: advisory investigation/explanation only. AI never changes expected/
actual/difference/leakage/status and never resolves exceptions.

**Evidence bundle** (`evidence_service`): only records relevant to the exception
(exception, reconciliation result, order, payment, related refunds/fees/
settlements, or the orphan record), each traceable by source + id. A grounding
index of `(source, id) → amount` validates AI claims.

**Provider abstraction** (`ai/provider.py`): `AIInvestigationProvider` +
deterministic `MockAIInvestigationProvider`. Credentials/model come from env
(`AI_PROVIDER`, `AI_API_KEY`, `AI_MODEL`); only `mock` ships. A system prompt
(`ai/system_prompt.py`) establishes the safety contract for any real provider
(deterministic truth, untrusted records, no invented facts, JSON only).

**Structured result** (validated Pydantic): classification ∈ 9 controlled values
(`EXPECTED_FEE`, `REFUND_RELATED`, `DUPLICATE_TRANSACTION`, `MISSING_SETTLEMENT`,
`ORDER_MAPPING_ERROR`, `DATA_INTEGRITY_ISSUE`, `UNIDENTIFIED_ADJUSTMENT`,
`INSUFFICIENT_EVIDENCE`, `OTHER`); confidence 0–100; recommended_action ∈
{`AUTO_RESOLVE`, `REVIEW`, `ESCALATE`}; evidence, missing_evidence, summary,
root_cause, reason.

**Validation pipeline** (`investigation_service`): parse → schema-validate →
evidence-ground (cited records must exist with matching amounts, else
`AI_GROUNDING_FAILED`) → safety. **Safety**: confidence `<70 → ESCALATE`,
`70–89 AUTO_RESOLVE → REVIEW`, `≥90` proposal stands (still advisory). AUTO_RESOLVE
never auto-resolves. Controlled errors on provider failure / invalid response.

**AI executive insight** (`insight_service`): the backend first computes validated
metrics (analytics summary + distribution + risk priorities), then the provider
composes a summary using ONLY those numbers (no raw datasets to the LLM). Cited
priority exceptions must exist. On any AI failure → `available:false` +
"AI insight temporarily unavailable." — analytics never breaks.

**APIs**: `POST /exceptions/{id}/investigate`, `GET /exceptions/{id}/investigation`,
`GET /analytics/insight`.

## 24. Finance Analytics, Risk Prioritization & Copilot (Prompts 7 & 9)

**Analytics** (`analytics_service`, all Decimal, backend-authoritative):
- `GET /analytics/summary` — transactions_processed, matched, match_rate,
  total/unresolved/resolved/escalated/rejected exceptions, exception_rate,
  resolution_rate, potential_leakage. Never divides by zero. Supports
  `status`/`severity`/`classification`/`start_date`/`end_date` filters;
  `start_date > end_date → INVALID_DATE_RANGE`.
- `GET /analytics/leakage-trend` — daily active-leakage keyed on payment business
  date; returns `available:false` (no fabricated history) when no dated leakage.
- `GET /analytics/exception-distribution` — count + financial impact per
  classification, ranked by impact.
- `GET /analytics/risk-priorities?limit=` — unresolved exceptions ordered by risk
  desc, then discrepancy desc, then oldest first; server-validated limit.

**Copilot** (`copilot_service`, `POST /copilot/query`): deterministic keyword
intent detection (`EXCEPTION_INVESTIGATION`/`EXPLANATION`, `ANALYTICS_SUMMARY`,
`LEAKAGE_TREND`, `FINANCIAL_IMPACT`, `RISK_PRIORITIES`, `RESOLUTION_PERFORMANCE`)
→ calls only registered **read-only** tools → composes the answer deterministically
from tool results, so every number originates from the backend (never the LLM).
The Copilot cannot mutate anything, run SQL, or call unregistered functions.
Prompt-injection text in the user message cannot change the deterministic numbers.

**UI**: `/analytics` (9 summary cards, leakage trend line/area, financial-impact
bars, risk-priorities table linking into the exception detail, AI Finance Insight
card) and `/copilot` (chat with suggested prompts, showing intent + tools used).
The dashboard also carries a live real-data panel (Prompt 5/9 integration).

## 25. Final System Architecture, Completed Features & Stack (Prompt 10)

**Separation (mandatory):**
```
Financial Data → Deterministic Engine (reconciliation, calculations, exception
detection, risk, analytics, state transitions, audit) → AI Layer (investigation,
explanation, recommendation, executive insight, Copilot phrasing) → Human
Controller (review, resolve, escalate, reject) → Audit Trail → Executive Analytics
```
Financial correctness never depends on the LLM. AI output is validated + grounded
before display and can only recommend. Humans make all financial decisions; every
decision is audited.

**Completed features:** dashboard (mock KPIs + live panel); multi-source CSV
ingestion + validation + normalization; deterministic reconciliation; exception
detection with severity/priority/risk; AI investigation (advisory, validated,
grounded); Finance Copilot; human review with Resolve/Escalate/Reject; append-only
audit trail; analytics (summary, leakage trend, financial impact, risk priorities);
AI executive insights; end-to-end integration.

**Final technical stack:**
- Frontend: React 19 + Vite 8, React Router 7; dependency-free SVG/CSS charts;
  Vitest + Testing Library; oxlint.
- Backend: Python 3.14, FastAPI, Uvicorn, Pydantic v2; pandas (CSV); `Decimal`
  for all money.
- Data: in-memory process store (no database).
- AI: provider abstraction with a deterministic mock (env-configured; no real LLM
  wired). Validation + evidence grounding + confidence safety enforced backend-side.
- Testing: pytest (99), Vitest (24); `npm run build` + `oxlint` clean.

**Financial safety model:** the product uses "potential unexplained leakage" (not
"confirmed loss"/"fraud"/"stolen"); risk score is prioritization, not fraud
probability; AI is advisory; no money is ever moved.
