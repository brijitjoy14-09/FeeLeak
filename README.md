# FeeLeak — AI Finance Controller

FeeLeak is an **AI-powered, multi-source financial reconciliation and leakage
detection platform**. It reconciles orders, payments, refunds, fees, and
settlements deterministically, detects potential unexplained discrepancies,
uses AI to *investigate and explain* them, keeps a human finance controller in
control of every decision, and records a complete audit trail — then rolls it
all up into analytics, risk prioritization, and a Finance Copilot.

> **Core principle:** financial correctness is **deterministic** and never
> depends on the LLM. AI only investigates, explains, and recommends. Humans
> decide. Everything is audited.

---

## Problem

Money arrives through processors and marketplaces where the settled amount is
the result of many moving parts — gross payment − refunds − fees − taxes ±
adjustments. Differences between what *should* have settled and what *actually*
did are **financial leakage** that is easy to miss at scale. Finance teams need
a reliable, auditable way to find and explain them.

## Solution

```
Financial Data
   ↓  Multi-source ingestion (CSV validate + normalize)
Deterministic Reconciliation  (Decimal; expected vs actual)
   ↓
Matched  /  Exceptions  (severity · priority · risk)
   ↓  AI Investigation (advisory, validated, evidence-grounded)
AI Recommendation
   ↓  Human Review  →  Resolve / Escalate / Reject
Audit Trail
   ↓
Analytics · Leakage Trend · Financial Impact · Risk Priorities · AI Insight
   ↓
Finance Controller Copilot
```

## Architecture (deterministic ▸ AI ▸ human ▸ audit)

```
Financial Data
      ▼
Deterministic Engine   reconciliation · calculations · exception detection ·
      ▼                risk · analytics · state transitions · audit
AI Layer               investigation · explanation · recommendation ·
      ▼                executive insight · Copilot phrasing
Human Controller       review · resolve · escalate · reject
      ▼
Audit Trail  ▸  Executive Analytics
```

AI output is **schema-validated, evidence-grounded, and confidence-gated** before
it is ever shown, and it can only *recommend*. The AI never changes a financial
value, sets a risk score, or resolves an exception.

## Features

- **Multi-source ingestion** — CSV upload for orders/payments/refunds/fees/
  settlements with column, type, amount, date, currency, and identifier
  validation; whole-dataset transaction safety.
- **Deterministic reconciliation** — per-payment expected vs actual settlement,
  difference, and status (matched / mismatch / missing settlement / order-not-
  found / duplicate / orphans), all in `Decimal`.
- **Exception management** — severity, deterministic priority, 0–100 **risk
  score** with explainable drivers; lifecycle OPEN → IN_REVIEW → RESOLVED /
  ESCALATED / REJECTED with required reasons.
- **AI investigation** — advisory classification, confidence, evidence, missing
  evidence, and recommendation, validated and grounded to real records.
- **Human review + audit trail** — Resolve / Escalate / Reject; append-only
  audit of who/what/when/why; double-submit protection.
- **Analytics** — summary KPIs, daily leakage trend, financial impact by
  classification, deterministic risk priorities, and an AI executive insight.
- **Finance Copilot** — natural-language questions answered from registered
  read-only backend tools (numbers always from the backend, never the LLM).

## Tech Stack

| Layer     | Technology |
| --------- | ---------- |
| Frontend  | React 19, Vite 8, React Router 7; dependency-free SVG/CSS charts |
| Backend   | Python 3.14, FastAPI, Uvicorn, Pydantic v2 |
| Money     | Python `Decimal` (never float for financial math) |
| CSV       | pandas |
| AI        | Provider abstraction + deterministic **mock** (env-configured; no real LLM wired) |
| Storage   | In-memory process store (no database) |
| Testing   | pytest (backend), Vitest + Testing Library (frontend), oxlint |

## Project Structure

```
FeeLeak/
├── backend/
│   ├── app/
│   │   ├── main.py                 # wiring: CORS, error handler, routers
│   │   ├── config.py               # sources, schemas, tolerance, severity,
│   │   │                           #   risk, statuses, AI + copilot config
│   │   ├── errors.py               # AppError + JSON error envelope
│   │   ├── formatting.py           # INR formatting for backend text
│   │   ├── ai/                     # provider abstraction, mock, system prompt
│   │   ├── services/               # ingestion, reconciliation, exception,
│   │   │                           #   evidence, investigation, analytics,
│   │   │                           #   insight, copilot, audit
│   │   ├── schemas/                # Pydantic request/response models
│   │   ├── api/                    # ingestion, reconciliation, exceptions,
│   │   │                           #   investigations, analytics, copilot
│   │   └── stores/data_store.py    # in-memory singleton
│   ├── tests/                      # pytest + fixtures/*.csv
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # router + layout
│   │   ├── services/api.js         # all backend calls (VITE_API_BASE_URL)
│   │   ├── constants/, utils/, hooks/
│   │   ├── components/             # layout, dashboard, reconciliation, exceptions
│   │   └── pages/                  # Dashboard, Reconciliation, Exceptions,
│   │                               #   Analytics, Copilot
│   └── .env.example
├── README.md · PROJECT_SUMMARY.md · TASK_LOG.md
```

## Setup

### Backend

```bash
cd backend
source venv/bin/activate            # pre-existing Python 3.14 venv
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend: <http://localhost:8000> · Swagger: <http://localhost:8000/docs>

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: <http://localhost:5173>

## Environment Variables

- **Frontend** (`frontend/.env`, template `.env.example`):
  `VITE_API_BASE_URL=http://localhost:8000`
- **Backend** (`backend/.env.example`, optional): `AI_PROVIDER=mock`,
  `AI_API_KEY=`, `AI_MODEL=mock-model`, `AI_TIMEOUT_SECONDS=20`. Defaults run the
  deterministic mock; never commit real secrets.

## Demo Workflow

1. Open the app → **Reconciliation**.
2. Upload the sample CSVs from `backend/tests/fixtures/` (orders, payments,
   refunds, fees, settlements).
3. **Run Reconciliation** → see match rate and results.
4. Go to **Exceptions** → **Generate Exceptions**.
5. Open a high-risk exception → see the deterministic calculation.
6. **Investigate Exception** (AI) → classification, confidence, evidence,
   recommendation (advisory).
7. **Start Review**, then **Resolve** / **Escalate** / **Reject** with a reason.
8. See the **Audit History** update; **Analytics** and risk update automatically.
9. Open **Analytics** → leakage trend, financial impact, risk priorities, AI
   insight.
10. Open **Copilot** → ask *"Which exceptions should I investigate first?"* — the
    answer comes from deterministic backend data.

## Testing

```bash
# Backend
cd backend && source venv/bin/activate && pytest        # 99 tests

# Frontend
cd frontend && npm test                                 # 24 tests (vitest)
npm run build                                            # production build
npm run lint                                             # oxlint
```

## AI Architecture

- **Provider abstraction** (`app/ai/provider.py`): `AIInvestigationProvider` +
  a deterministic `MockAIInvestigationProvider`. A real LLM would slot in here,
  reading credentials from env — nothing else changes.
- **Evidence bundle** (`evidence_service`): only records relevant to an
  exception, each traceable by source + id; a grounding index validates claims.
- **Validation pipeline** (`investigation_service`): parse → schema-validate →
  evidence-ground → confidence safety (`<70 ESCALATE`, `70–89 AUTO_RESOLVE →
  REVIEW`, `≥90` stands, advisory only). AUTO_RESOLVE never auto-resolves.
- **Executive insight** (`insight_service`): the backend computes validated
  metrics first; the AI composes a summary using *only* those numbers; failures
  degrade gracefully (`"AI insight temporarily unavailable"`).
- **Prompt-injection safety**: financial record text is untrusted data — the
  system prompt forbids following instructions inside records, and deterministic
  calculations/Copilot answers never depend on that text.

## Financial Safety Model

- Language is **"potential unexplained leakage"**, never "confirmed loss",
  "fraud", or "stolen".
- **Risk score is a prioritization signal**, not a probability of fraud.
- AI is **advisory**; a human finance controller makes every financial decision,
  and every decision is audited.
- **No money is ever moved** — FeeLeak is a detection/investigation/analytics
  tool.

## Known Limitations

In-memory storage (no database); AI is a deterministic mock (no real LLM wired);
all data is synthetic demo CSV; the Prompt-2 dashboard KPI cards remain synthetic
(a live real-data panel sits alongside them); INR-only; no authentication (a demo
`finance-controller` identity is used for the audit trail). See
`PROJECT_SUMMARY.md` §15.
