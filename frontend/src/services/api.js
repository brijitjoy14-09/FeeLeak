// API service layer for communicating with the FeeLeak backend.
// All backend URLs are derived from the VITE_API_BASE_URL environment
// variable so components never hardcode the backend origin.

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL

/**
 * Error thrown for non-OK API responses. Carries the backend's structured
 * error envelope so the UI can display code/message/details clearly.
 */
export class ApiError extends Error {
  constructor(message, { code, details, status } = {}) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.details = details
    this.status = status
  }
}

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, options)
  } catch {
    throw new ApiError('Could not reach the backend.', { code: 'NETWORK_ERROR' })
  }

  let data = null
  try {
    data = await response.json()
  } catch {
    // Non-JSON response; leave data null.
  }

  if (!response.ok) {
    const error = data?.error ?? {}
    throw new ApiError(error.message || `Request failed (${response.status})`, {
      code: error.code,
      details: error.details,
      status: response.status,
    })
  }
  return data
}

// ---- Health (Prompt 1) -----------------------------------------------------
export async function getHealth() {
  const response = await fetch(`${API_BASE_URL}/health`)
  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`)
  }
  return response.json()
}

// ---- Ingestion (Prompt 3) --------------------------------------------------
export async function uploadDataset(sourceType, file) {
  const form = new FormData()
  form.append('source_type', sourceType)
  form.append('file', file)
  return request('/api/v1/ingestion/upload', { method: 'POST', body: form })
}

export function getIngestionStatus() {
  return request('/api/v1/ingestion/status')
}

export function getDatasets() {
  return request('/api/v1/ingestion/datasets')
}

export function getDataset(sourceType, limit = 10) {
  return request(`/api/v1/ingestion/datasets/${sourceType}?limit=${limit}`)
}

export function deleteDataset(sourceType) {
  return request(`/api/v1/ingestion/datasets/${sourceType}`, { method: 'DELETE' })
}

// ---- Reconciliation (Prompt 4) --------------------------------------------
export function runReconciliation() {
  return request('/api/v1/reconciliation/run', { method: 'POST' })
}

export function getReconciliationSummary() {
  return request('/api/v1/reconciliation/summary')
}

export function getReconciliationResults({ status, search, limit } = {}) {
  const params = new URLSearchParams()
  if (status) params.set('status', status)
  if (search) params.set('search', search)
  if (limit) params.set('limit', String(limit))
  const query = params.toString()
  return request(`/api/v1/reconciliation/results${query ? `?${query}` : ''}`)
}

export function getReconciliationResult(paymentId) {
  return request(`/api/v1/reconciliation/results/${paymentId}`)
}

// ---- Exceptions (Prompt 5) -------------------------------------------------
export function generateExceptions() {
  return request('/api/v1/exceptions/generate', { method: 'POST' })
}

export function getExceptionsSummary() {
  return request('/api/v1/exceptions/summary')
}

export function getExceptions({ status, type, severity, search, sort, limit } = {}) {
  const params = new URLSearchParams()
  if (status) params.set('status', status)
  if (type) params.set('type', type)
  if (severity) params.set('severity', severity)
  if (search) params.set('search', search)
  if (sort) params.set('sort', sort)
  if (limit) params.set('limit', String(limit))
  const query = params.toString()
  return request(`/api/v1/exceptions${query ? `?${query}` : ''}`)
}

export function getException(exceptionId) {
  return request(`/api/v1/exceptions/${exceptionId}`)
}

export function updateExceptionStatus(exceptionId, { status, note } = {}) {
  return request(`/api/v1/exceptions/${exceptionId}/status`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status, note }),
  })
}

// ---- AI Investigation (Prompt 6) ------------------------------------------
export function investigateException(exceptionId) {
  return request(`/api/v1/exceptions/${exceptionId}/investigate`, { method: 'POST' })
}

export function getInvestigation(exceptionId) {
  return request(`/api/v1/exceptions/${exceptionId}/investigation`)
}

export function getExceptionAudit(exceptionId) {
  return request(`/api/v1/exceptions/${exceptionId}/audit`)
}

// ---- Analytics (Prompt 9) --------------------------------------------------
function toQuery(params) {
  const search = new URLSearchParams()
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      search.set(key, String(value))
    }
  })
  const query = search.toString()
  return query ? `?${query}` : ''
}

export function getAnalyticsSummary(filters = {}) {
  return request(`/api/v1/analytics/summary${toQuery(filters)}`)
}

export function getLeakageTrend() {
  return request('/api/v1/analytics/leakage-trend')
}

export function getExceptionDistribution(filters = {}) {
  return request(`/api/v1/analytics/exception-distribution${toQuery(filters)}`)
}

export function getRiskPriorities(filters = {}) {
  return request(`/api/v1/analytics/risk-priorities${toQuery(filters)}`)
}

export function getAnalyticsInsight() {
  return request('/api/v1/analytics/insight')
}

// ---- Finance Controller Copilot (Prompt 7) --------------------------------
export function copilotQuery(message) {
  return request('/api/v1/copilot/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  })
}
