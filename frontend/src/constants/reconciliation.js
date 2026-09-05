// Source types and reconciliation statuses — kept in one place so the UI and
// the backend stay consistent (these values match the FastAPI backend).

export const SOURCES = [
  { id: 'orders', label: 'Orders' },
  { id: 'payments', label: 'Payments' },
  { id: 'refunds', label: 'Refunds' },
  { id: 'fees', label: 'Fees' },
  { id: 'settlements', label: 'Settlements' },
]

// Backend reconciliation status -> display label + tone.
export const STATUS_META = {
  MATCHED: { label: 'Matched', tone: 'success' },
  MISMATCH: { label: 'Mismatch', tone: 'danger' },
  MISSING_SETTLEMENT: { label: 'Missing Settlement', tone: 'warning' },
  ORDER_NOT_FOUND: { label: 'Order Not Found', tone: 'warning' },
  DUPLICATE_PAYMENT: { label: 'Duplicate Payment', tone: 'warning' },
}

// UI filter options mapped to backend status values (null = all).
export const STATUS_FILTERS = [
  { id: 'ALL', label: 'All', status: null },
  { id: 'MATCHED', label: 'Matched', status: 'MATCHED' },
  { id: 'MISMATCH', label: 'Mismatch', status: 'MISMATCH' },
  { id: 'MISSING_SETTLEMENT', label: 'Missing Settlement', status: 'MISSING_SETTLEMENT' },
  { id: 'ORDER_NOT_FOUND', label: 'Data Integrity', status: 'ORDER_NOT_FOUND' },
]
