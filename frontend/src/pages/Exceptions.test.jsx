import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import Exceptions from './Exceptions'
import * as api from '../services/api'

const renderExceptions = () =>
  render(
    <MemoryRouter>
      <Exceptions />
    </MemoryRouter>,
  )

const EXC = {
  exception_id: 'EXC-PAY002',
  payment_id: 'PAY002',
  order_id: 'ORD002',
  source_kind: 'payment',
  record_id: null,
  type: 'AMOUNT_MISMATCH',
  status: 'OPEN',
  severity: 'LOW',
  priority: 1,
  expected_amount: '5264.00',
  actual_amount: '5000.00',
  difference: '264.00',
  affected_amount: '264.00',
  potential_leakage: '264.00',
  risk_score: 12,
  risk_level: 'LOW',
  risk_drivers: ['Discrepancy: ₹264', 'LOW severity', 'Unresolved status'],
  description: 'Settlement differs from expected by ₹264.00 for payment PAY002.',
  created_at: '2026-08-25T10:00:00+05:30',
  reviewed_at: null,
  reviewed_by: null,
  resolution: null,
  escalation_reason: null,
  rejection_reason: null,
}

const SUMMARY = {
  total_exceptions: 1,
  open: 1,
  in_review: 0,
  resolved: 0,
  escalated: 0,
  active_exceptions: 1,
  total_affected_amount: '264.00',
  potential_leakage: '264.00',
  severity_distribution: { LOW: 1, MEDIUM: 0, HIGH: 0, CRITICAL: 0 },
  type_distribution: { AMOUNT_MISMATCH: 1 },
}

beforeEach(() => {
  vi.spyOn(api, 'getExceptionsSummary').mockResolvedValue(SUMMARY)
  vi.spyOn(api, 'getExceptions').mockResolvedValue({
    total: 1,
    returned: 1,
    exceptions: [EXC],
  })
  vi.spyOn(api, 'getReconciliationResult').mockResolvedValue({
    payment_amount: '5500.00',
    total_refund: '0.00',
    total_fee: '200.00',
    total_tax: '36.00',
    expected_settlement: '5264.00',
    actual_settlement: '5000.00',
    difference: '264.00',
    refund_count: 0,
    fee_count: 1,
    settlement_count: 1,
  })
  vi.spyOn(api, 'getInvestigation').mockRejectedValue(
    new api.ApiError('none', { code: 'INVESTIGATION_NOT_FOUND' }),
  )
  vi.spyOn(api, 'getExceptionAudit').mockResolvedValue({ events: [] })
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('Finance Exception Queue', () => {
  it('renders the page with summary and table', async () => {
    renderExceptions()
    expect(
      screen.getByRole('heading', { name: 'Finance Exception Queue' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Generate Exceptions' })).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.getByText('EXC-PAY002')).toBeInTheDocument()
    })
    expect(screen.getAllByText('Amount Mismatch').length).toBeGreaterThan(0)
  })

  it('opens the detail modal with the deterministic calculation', async () => {
    renderExceptions()
    await screen.findByText('EXC-PAY002')
    fireEvent.click(screen.getByRole('button', { name: 'Details' }))

    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).getByText('Expected Settlement')).toBeInTheDocument()
    expect(within(dialog).getByText('₹5,264')).toBeInTheDocument()
    // AI section present, not yet investigated.
    expect(within(dialog).getByRole('heading', { name: 'AI Investigation' })).toBeInTheDocument()
    expect(
      within(dialog).getByRole('button', { name: 'Investigate Exception' }),
    ).toBeInTheDocument()
  })

  it('runs AI investigation and shows the advisory recommendation', async () => {
    vi.spyOn(api, 'investigateException').mockResolvedValue({
      investigation: {
        investigation_id: 'INV-EXC-PAY002-1',
        exception_id: 'EXC-PAY002',
        classification: 'INSUFFICIENT_EVIDENCE',
        summary: 'The residual is unexplained.',
        root_cause: 'No adjustment record explains the difference.',
        confidence: 60,
        evidence: [{ source: 'payments', id: 'PAY002', amount: '5500.00' }],
        missing_evidence: ['No adjustment record explains the remaining difference.'],
        recommended_action: 'ESCALATE',
        reason: 'The discrepancy is unexplained by available evidence.',
      },
    })

    renderExceptions()
    await screen.findByText('EXC-PAY002')
    fireEvent.click(screen.getByRole('button', { name: 'Details' }))
    const dialog = await screen.findByRole('dialog')

    fireEvent.click(within(dialog).getByRole('button', { name: 'Investigate Exception' }))

    await waitFor(() => {
      expect(within(dialog).getByText('Insufficient Evidence')).toBeInTheDocument()
    })
    expect(within(dialog).getByText('60%')).toBeInTheDocument()
    expect(within(dialog).getByText('AI Recommendation')).toBeInTheDocument()
    // The AI never changes exception status — Start Review is still offered.
    expect(within(dialog).getByRole('button', { name: 'Start Review' })).toBeInTheDocument()
  })

  it('requires a note to resolve (manual control preserved)', async () => {
    renderExceptions()
    await screen.findByText('EXC-PAY002')
    fireEvent.click(screen.getByRole('button', { name: 'Details' }))
    const dialog = await screen.findByRole('dialog')

    // OPEN → Start Review is offered; Resolve is not (invalid from OPEN).
    expect(within(dialog).getByRole('button', { name: 'Start Review' })).toBeInTheDocument()
    expect(within(dialog).queryByRole('button', { name: 'Resolve' })).toBeNull()
  })
})
