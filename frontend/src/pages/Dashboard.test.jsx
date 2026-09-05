import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from '../App'
import * as api from '../services/api'

// The dashboard uses mock data and must not depend on the backend. We still
// mock getHealth so the sidebar's health check never hits the network in tests.
beforeEach(() => {
  vi.spyOn(api, 'getHealth').mockResolvedValue({ status: 'healthy' })
  // The dashboard's live panel calls these on mount; keep them off the network.
  vi.spyOn(api, 'getReconciliationSummary').mockRejectedValue(
    new api.ApiError('no reconciliation', { code: 'NO_RECONCILIATION' }),
  )
  vi.spyOn(api, 'getExceptionsSummary').mockResolvedValue({
    total_exceptions: 0,
    open: 0,
    in_review: 0,
    resolved: 0,
    escalated: 0,
    active_exceptions: 0,
    total_affected_amount: '0.00',
    potential_leakage: '0.00',
    severity_distribution: {},
    type_distribution: {},
  })
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('Finance Controller Dashboard', () => {
  // Test 1 — renders
  it('renders the dashboard overview', async () => {
    render(<App />)
    expect(screen.getByText('Overview')).toBeInTheDocument()
    expect(
      screen.getByRole('heading', { name: 'Reconciliation Summary' }),
    ).toBeInTheDocument()
    await screen.findByText('Connected') // flush sidebar health check
  })

  // Test 2 — KPI values for the default period (Last 7 Days)
  it('shows the default-period KPI values', async () => {
    render(<App />)
    expect(screen.getByTestId('kpi-records')).toHaveTextContent('500')
    expect(screen.getByTestId('kpi-match')).toHaveTextContent('92.4%')
    expect(screen.getByTestId('kpi-exceptions')).toHaveTextContent('38')
    expect(screen.getByTestId('kpi-leakage')).toHaveTextContent('₹24,850')
    await screen.findByText('Connected')
  })

  // Test 3 — period filter updates metrics
  it('updates metrics when the period changes to Last 30 Days', async () => {
    render(<App />)
    const select = screen.getByLabelText('Period')

    fireEvent.change(select, { target: { value: '30d' } })

    await waitFor(() => {
      expect(screen.getByTestId('kpi-records')).toHaveTextContent('2,184')
    })
    expect(screen.getByTestId('kpi-match')).toHaveTextContent('91.7%')
  })

  // Test 4 — recent exceptions table
  it('renders recent exception records', async () => {
    render(<App />)
    const table = screen.getByRole('table')
    expect(within(table).getByText('TXN-10021')).toBeInTheDocument()
    expect(within(table).getByText('Amount Mismatch')).toBeInTheDocument()
    expect(within(table).getByText('₹800')).toBeInTheDocument()
    await screen.findByText('Connected')
  })

  // Test 5 — dashboard still renders when the backend is unavailable
  it('renders even when the backend health check fails', async () => {
    api.getHealth.mockRejectedValueOnce(new Error('Network error'))
    render(<App />)
    expect(screen.getByText('Overview')).toBeInTheDocument()
    expect(screen.getByTestId('kpi-records')).toHaveTextContent('500')
    await waitFor(() => {
      expect(screen.getByText('Disconnected')).toBeInTheDocument()
    })
  })

  // Test 6 — navigation lists all sections, only Dashboard active
  it('renders navigation with only Dashboard active', async () => {
    render(<App />)
    const nav = screen.getByRole('navigation', { name: 'Main' })
    const links = within(nav).getAllByRole('link')
    expect(links).toHaveLength(6)

    const labels = links.map((link) => link.textContent)
    expect(labels).toEqual(
      expect.arrayContaining([
        expect.stringContaining('Dashboard'),
        expect.stringContaining('Reconciliation'),
        expect.stringContaining('Exceptions'),
        expect.stringContaining('Analytics'),
        expect.stringContaining('Copilot'),
        expect.stringContaining('Settings'),
      ]),
    )

    const dashboardLink = within(nav).getByRole('link', { name: /Dashboard/ })
    expect(dashboardLink).toHaveAttribute('aria-current', 'page')

    const reconciliationLink = within(nav).getByRole('link', {
      name: /Reconciliation/,
    })
    expect(reconciliationLink).not.toHaveAttribute('aria-current', 'page')

    await screen.findByText('Connected')
  })
})
