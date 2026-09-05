import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import Analytics from './Analytics'
import * as api from '../services/api'

beforeEach(() => {
  vi.spyOn(api, 'getAnalyticsSummary').mockResolvedValue({
    transactions_processed: 8,
    matched_transactions: 4,
    match_rate: 50.0,
    total_exceptions: 7,
    unresolved_exceptions: 7,
    resolved_exceptions: 0,
    escalated_exceptions: 0,
    rejected_exceptions: 0,
    exception_rate: 87.5,
    resolution_rate: 0.0,
    potential_leakage: '8092.00',
  })
  vi.spyOn(api, 'getLeakageTrend').mockResolvedValue({
    granularity: 'day',
    available: true,
    data: [
      { date: '2026-08-01', potential_leakage: '264.00' },
      { date: '2026-08-02', potential_leakage: '7764.00' },
    ],
  })
  vi.spyOn(api, 'getExceptionDistribution').mockResolvedValue({
    data: [{ classification: 'MISSING_SETTLEMENT', count: 1, amount: '7764.00' }],
  })
  vi.spyOn(api, 'getRiskPriorities').mockResolvedValue({
    total: 1,
    returned: 1,
    data: [{
      exception_id: 'EXC-PAY003', risk_score: 40, risk_level: 'MEDIUM',
      risk_drivers: [], discrepancy: '7764.00', potential_leakage: '7764.00',
      classification: 'MISSING_SETTLEMENT', severity: 'HIGH', status: 'OPEN',
    }],
  })
  vi.spyOn(api, 'getAnalyticsInsight').mockResolvedValue({
    available: true,
    insight: {
      summary: '8 transactions processed at a 50.0% match rate.',
      key_findings: ['Largest impact: Missing Settlement.'],
      priority_exceptions: ['EXC-PAY003'],
    },
  })
})

afterEach(() => vi.restoreAllMocks())

const renderAnalytics = () =>
  render(<MemoryRouter><Analytics /></MemoryRouter>)

describe('Analytics page', () => {
  it('renders summary cards from backend data', async () => {
    renderAnalytics()
    await waitFor(() => expect(screen.getByText('Transactions Processed')).toBeInTheDocument())
    expect(screen.getByText('50.0%')).toBeInTheDocument()
    expect(screen.getByText('₹8,092')).toBeInTheDocument()
  })

  it('renders the risk priorities table and AI insight', async () => {
    renderAnalytics()
    await waitFor(() => expect(screen.getByText('Risk Priorities')).toBeInTheDocument())
    expect(screen.getAllByText('EXC-PAY003').length).toBeGreaterThan(0)
    expect(screen.getByText('AI Finance Insight')).toBeInTheDocument()
    expect(
      screen.getByText('8 transactions processed at a 50.0% match rate.'),
    ).toBeInTheDocument()
  })

  it('shows a graceful message when AI insight is unavailable', async () => {
    api.getAnalyticsInsight.mockResolvedValue({
      available: false,
      message: 'AI insight temporarily unavailable.',
    })
    renderAnalytics()
    await waitFor(() =>
      expect(screen.getByText('AI insight temporarily unavailable.')).toBeInTheDocument(),
    )
  })
})
