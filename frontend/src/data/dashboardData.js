// ---------------------------------------------------------------------------
// SYNTHETIC / MOCK DASHBOARD DATA — NOT REAL FINANCIAL RESULTS.
//
// Prompt 2 uses frontend-only demo data. There is no reconciliation engine
// yet. Every value below is illustrative. The shape of each period's payload
// intentionally mirrors what a future metrics/exceptions API will return, so
// Prompt 3+ can replace `getDashboardData()` with a real fetch WITHOUT
// changing the dashboard components (they consume this structure as-is).
//
// Future (not implemented here):
//   Expected Settlement = Payment − Refunds − Fees ± Adjustments
//   Discrepancy         = Expected Settlement − Actual Settlement
// ---------------------------------------------------------------------------

/** Period options offered by the dashboard filter. */
export const PERIODS = [
  { id: 'today', label: 'Today' },
  { id: '7d', label: 'Last 7 Days' },
  { id: '30d', label: 'Last 30 Days' },
]

/** Default period shown on first load. */
export const DEFAULT_PERIOD = '7d'

// Categories shared across periods; each period supplies its own counts.
const EXCEPTION_CATEGORIES = [
  'Missing Settlement',
  'Amount Mismatch',
  'Refund Mismatch',
  'Duplicate Transaction',
  'Unknown Adjustment',
  'Other',
]

function distribution(counts) {
  return EXCEPTION_CATEGORIES.map((category, i) => ({
    category,
    count: counts[i],
  }))
}

// Synthetic dataset keyed by period id. Each entry is self-contained.
const DASHBOARD_DATA = {
  today: {
    kpis: {
      recordsProcessed: 82,
      changeVsPreviousPct: 8.2,
      matchRate: 94.1,
      matched: 77,
      totalForMatch: 82,
      exceptions: 5,
      exceptionsToReview: 2,
      potentialLeakage: 4120,
      unresolvedLeakage: 2600,
    },
    summary: { processed: 82, matched: 77, resolved: 3, unresolved: 2 },
    trend: [
      { label: '9 AM', records: 8, matchRate: 95.0 },
      { label: '11 AM', records: 14, matchRate: 93.2 },
      { label: '1 PM', records: 11, matchRate: 94.6 },
      { label: '3 PM', records: 17, matchRate: 92.9 },
      { label: '5 PM', records: 13, matchRate: 95.1 },
      { label: '7 PM', records: 10, matchRate: 94.0 },
      { label: '9 PM', records: 9, matchRate: 93.8 },
    ],
    distribution: distribution([1, 1, 1, 0, 1, 1]),
    recentExceptions: [
      {
        id: 'TXN-10042',
        type: 'Amount Mismatch',
        expected: 3200,
        actual: 2950,
        difference: 250,
        status: 'Review',
      },
      {
        id: 'TXN-10039',
        type: 'Missing Settlement',
        expected: 1800,
        actual: 0,
        difference: 1800,
        status: 'Unresolved',
      },
      {
        id: 'TXN-10036',
        type: 'Refund Mismatch',
        expected: 2400,
        actual: 2050,
        difference: 350,
        status: 'Investigating',
      },
      {
        id: 'TXN-10031',
        type: 'Unknown Adjustment',
        expected: 1500,
        actual: 1380,
        difference: 120,
        status: 'Resolved',
      },
    ],
  },

  '7d': {
    kpis: {
      recordsProcessed: 500,
      changeVsPreviousPct: 12.5,
      matchRate: 92.4,
      matched: 462,
      totalForMatch: 500,
      exceptions: 38,
      exceptionsToReview: 11,
      potentialLeakage: 24850,
      unresolvedLeakage: 18200,
    },
    summary: { processed: 500, matched: 462, resolved: 27, unresolved: 11 },
    trend: [
      { label: 'Mon', records: 58, matchRate: 90.2 },
      { label: 'Tue', records: 72, matchRate: 91.4 },
      { label: 'Wed', records: 64, matchRate: 92.0 },
      { label: 'Thu', records: 81, matchRate: 93.1 },
      { label: 'Fri', records: 75, matchRate: 92.8 },
      { label: 'Sat', records: 69, matchRate: 93.4 },
      { label: 'Sun', records: 81, matchRate: 94.0 },
    ],
    distribution: distribution([5, 9, 7, 3, 8, 6]),
    recentExceptions: [
      {
        id: 'TXN-10021',
        type: 'Amount Mismatch',
        expected: 10000,
        actual: 9200,
        difference: 800,
        status: 'Review',
      },
      {
        id: 'TXN-10018',
        type: 'Missing Settlement',
        expected: 5500,
        actual: 0,
        difference: 5500,
        status: 'Unresolved',
      },
      {
        id: 'TXN-10015',
        type: 'Refund Mismatch',
        expected: 7200,
        actual: 6000,
        difference: 1200,
        status: 'Investigating',
      },
      {
        id: 'TXN-10012',
        type: 'Duplicate Transaction',
        expected: 3500,
        actual: 7000,
        difference: 3500,
        status: 'Review',
      },
      {
        id: 'TXN-10007',
        type: 'Unknown Adjustment',
        expected: 4200,
        actual: 4050,
        difference: 150,
        status: 'Resolved',
      },
    ],
  },

  '30d': {
    kpis: {
      recordsProcessed: 2184,
      changeVsPreviousPct: 6.9,
      matchRate: 91.7,
      matched: 2003,
      totalForMatch: 2184,
      exceptions: 181,
      exceptionsToReview: 47,
      potentialLeakage: 112400,
      unresolvedLeakage: 74300,
    },
    summary: { processed: 2184, matched: 2003, resolved: 134, unresolved: 47 },
    trend: [
      { label: 'Wk-1', records: 486, matchRate: 90.6 },
      { label: 'Wk-2', records: 512, matchRate: 91.2 },
      { label: 'Wk-3', records: 548, matchRate: 92.1 },
      { label: 'Wk-4', records: 538, matchRate: 92.8 },
      { label: 'Wk-5', records: 100, matchRate: 93.0 },
      { label: 'Wk-6', records: 0, matchRate: 0 },
      { label: 'Wk-7', records: 0, matchRate: 0 },
    ],
    distribution: distribution([24, 41, 33, 18, 39, 26]),
    recentExceptions: [
      {
        id: 'TXN-09984',
        type: 'Amount Mismatch',
        expected: 15200,
        actual: 13600,
        difference: 1600,
        status: 'Review',
      },
      {
        id: 'TXN-09961',
        type: 'Missing Settlement',
        expected: 22000,
        actual: 0,
        difference: 22000,
        status: 'Unresolved',
      },
      {
        id: 'TXN-09950',
        type: 'Refund Mismatch',
        expected: 9800,
        actual: 8100,
        difference: 1700,
        status: 'Investigating',
      },
      {
        id: 'TXN-09937',
        type: 'Duplicate Transaction',
        expected: 6400,
        actual: 12800,
        difference: 6400,
        status: 'Review',
      },
      {
        id: 'TXN-09925',
        type: 'Unknown Adjustment',
        expected: 7300,
        actual: 7150,
        difference: 150,
        status: 'Resolved',
      },
    ],
  },
}

// Trim the 30d trend to weeks that actually have data (keeps the chart honest).
DASHBOARD_DATA['30d'].trend = DASHBOARD_DATA['30d'].trend.filter(
  (point) => point.records > 0,
)

/**
 * Return the dashboard dataset for a given period id.
 *
 * This is the single seam future prompts will replace with a real API call
 * (e.g. `await getDashboardMetrics(period)`) — the returned shape stays the
 * same, so components do not need to change.
 */
export function getDashboardData(period) {
  return DASHBOARD_DATA[period] ?? DASHBOARD_DATA[DEFAULT_PERIOD]
}

export { DASHBOARD_DATA }
