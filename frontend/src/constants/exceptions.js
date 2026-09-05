// Exception + AI investigation UI metadata, kept consistent with the backend.

export const EXCEPTION_STATUS_META = {
  OPEN: { label: 'Open', tone: 'warning' },
  IN_REVIEW: { label: 'In Review', tone: 'info' },
  RESOLVED: { label: 'Resolved', tone: 'success' },
  ESCALATED: { label: 'Escalated', tone: 'danger' },
  REJECTED: { label: 'Rejected', tone: 'neutral' },
}

export const RISK_LEVEL_META = {
  LOW: { label: 'Low', tone: 'neutral' },
  MEDIUM: { label: 'Medium', tone: 'info' },
  HIGH: { label: 'High', tone: 'warning' },
  CRITICAL: { label: 'Critical', tone: 'danger' },
}

export const SEVERITY_META = {
  LOW: { label: 'Low', tone: 'neutral' },
  MEDIUM: { label: 'Medium', tone: 'info' },
  HIGH: { label: 'High', tone: 'warning' },
  CRITICAL: { label: 'Critical', tone: 'danger' },
}

export const EXCEPTION_TYPE_LABELS = {
  AMOUNT_MISMATCH: 'Amount Mismatch',
  MISSING_SETTLEMENT: 'Missing Settlement',
  ORDER_NOT_FOUND: 'Order Not Found',
  ORPHAN_SETTLEMENT: 'Orphan Settlement',
  ORPHAN_REFUND: 'Orphan Refund',
  ORPHAN_FEE: 'Orphan Fee',
  DUPLICATE_PAYMENT: 'Duplicate Payment',
}

export const STATUS_FILTER_OPTIONS = [
  { id: 'ALL', label: 'All', value: null },
  { id: 'OPEN', label: 'Open', value: 'OPEN' },
  { id: 'IN_REVIEW', label: 'In Review', value: 'IN_REVIEW' },
  { id: 'RESOLVED', label: 'Resolved', value: 'RESOLVED' },
  { id: 'ESCALATED', label: 'Escalated', value: 'ESCALATED' },
]

export const TYPE_FILTER_OPTIONS = [
  { id: 'ALL', label: 'All Types', value: null },
  ...Object.entries(EXCEPTION_TYPE_LABELS).map(([value, label]) => ({
    id: value,
    label,
    value,
  })),
]

export const SEVERITY_FILTER_OPTIONS = [
  { id: 'ALL', label: 'All Severities', value: null },
  { id: 'LOW', label: 'Low', value: 'LOW' },
  { id: 'MEDIUM', label: 'Medium', value: 'MEDIUM' },
  { id: 'HIGH', label: 'High', value: 'HIGH' },
  { id: 'CRITICAL', label: 'Critical', value: 'CRITICAL' },
]

// Valid next statuses per current status → drives the action buttons shown.
export const NEXT_ACTIONS = {
  OPEN: [
    { status: 'IN_REVIEW', label: 'Start Review', tone: 'primary' },
    { status: 'ESCALATED', label: 'Escalate', tone: 'danger', requiresNote: 'escalation' },
    { status: 'REJECTED', label: 'Reject', tone: 'secondary', requiresNote: 'rejection' },
  ],
  IN_REVIEW: [
    { status: 'RESOLVED', label: 'Resolve', tone: 'success', requiresNote: 'resolution' },
    { status: 'ESCALATED', label: 'Escalate', tone: 'danger', requiresNote: 'escalation' },
    { status: 'REJECTED', label: 'Reject', tone: 'secondary', requiresNote: 'rejection' },
  ],
  ESCALATED: [
    { status: 'IN_REVIEW', label: 'Resume Review', tone: 'primary' },
    { status: 'RESOLVED', label: 'Resolve', tone: 'success', requiresNote: 'resolution' },
    { status: 'REJECTED', label: 'Reject', tone: 'secondary', requiresNote: 'rejection' },
  ],
  RESOLVED: [],
  REJECTED: [],
}

// Note-dialog labels keyed by the action's requiresNote value.
export const NOTE_LABELS = {
  resolution: 'Resolution note (required)',
  escalation: 'Escalation reason (required)',
  rejection: 'Rejection reason (required)',
}

// AI recommendation display metadata.
export const AI_ACTION_META = {
  AUTO_RESOLVE: { label: 'Auto-Resolve', tone: 'success' },
  REVIEW: { label: 'Review', tone: 'warning' },
  ESCALATE: { label: 'Escalate', tone: 'danger' },
}

export const AI_CLASSIFICATION_LABELS = {
  EXPECTED_FEE: 'Expected Fee',
  REFUND_RELATED: 'Refund Related',
  DUPLICATE_TRANSACTION: 'Duplicate Transaction',
  MISSING_SETTLEMENT: 'Missing Settlement',
  ORDER_MAPPING_ERROR: 'Order Mapping Error',
  DATA_INTEGRITY_ISSUE: 'Data Integrity Issue',
  UNIDENTIFIED_ADJUSTMENT: 'Unidentified Adjustment',
  INSUFFICIENT_EVIDENCE: 'Insufficient Evidence',
  OTHER: 'Other',
}
