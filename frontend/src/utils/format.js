// Reusable display formatters for the FeeLeak dashboard.
// Kept deterministic (no Intl locale dependence) so output is stable
// across environments and in tests.

/**
 * Group an integer string using the Indian numbering system
 * (last three digits, then groups of two): 120500 -> "1,20,500".
 */
function groupIndian(intStr) {
  if (intStr.length <= 3) return intStr
  const last3 = intStr.slice(-3)
  const rest = intStr.slice(0, -3).replace(/\B(?=(\d{2})+(?!\d))/g, ',')
  return `${rest},${last3}`
}

/**
 * Format a number with Indian digit grouping (no currency symbol).
 * 2184 -> "2,184". Returns "—" for nullish/invalid input.
 */
export function formatNumber(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return '—'
  }
  const num = Number(value)
  const sign = num < 0 ? '-' : ''
  return `${sign}${groupIndian(String(Math.trunc(Math.abs(num))))}`
}

/**
 * Format an amount as Indian Rupees: 24850 -> "₹24,850",
 * 120500 -> "₹1,20,500", 0 -> "₹0".
 * Pass { decimals } to show fixed decimal places.
 */
export function formatINR(value, { decimals = 0 } = {}) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return '—'
  }
  const num = Number(value)
  const sign = num < 0 ? '-' : ''
  const fixed = Math.abs(num).toFixed(decimals)
  const [intPart, decPart] = fixed.split('.')
  const grouped = groupIndian(intPart)
  return `${sign}₹${grouped}${decPart ? `.${decPart}` : ''}`
}

/**
 * Format a percentage value with a single decimal place by default.
 * 92.4 -> "92.4%". Returns "—" for nullish/invalid input.
 */
export function formatPercent(value, { decimals = 1 } = {}) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return '—'
  }
  return `${Number(value).toFixed(decimals)}%`
}
