import { render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import Reconciliation from './Reconciliation'
import * as api from '../services/api'

beforeEach(() => {
  // Default: no datasets loaded yet.
  vi.spyOn(api, 'getIngestionStatus').mockResolvedValue({
    sources: {
      orders: { loaded: false, records: 0 },
      payments: { loaded: false, records: 0 },
      refunds: { loaded: false, records: 0 },
      fees: { loaded: false, records: 0 },
      settlements: { loaded: false, records: 0 },
    },
  })
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('Reconciliation page', () => {
  it('renders the page heading', async () => {
    render(<Reconciliation />)
    expect(
      screen.getByRole('heading', { name: 'Reconciliation', level: 1 }),
    ).toBeInTheDocument()
    await waitFor(() => expect(api.getIngestionStatus).toHaveBeenCalled())
  })

  it('offers all five source types in the upload selector', async () => {
    render(<Reconciliation />)
    const select = screen.getByLabelText('Source')
    const options = within(select).getAllByRole('option').map((o) => o.textContent)
    expect(options).toEqual([
      'Orders',
      'Payments',
      'Refunds',
      'Fees',
      'Settlements',
    ])
    await waitFor(() => expect(api.getIngestionStatus).toHaveBeenCalled())
  })

  it('disables Run Reconciliation while required datasets are missing', async () => {
    render(<Reconciliation />)
    const runButton = await screen.findByRole('button', {
      name: /Run Reconciliation/,
    })
    expect(runButton).toBeDisabled()
  })

  it('disables Upload until a file is selected', async () => {
    render(<Reconciliation />)
    expect(screen.getByRole('button', { name: 'Upload' })).toBeDisabled()
    await waitFor(() => expect(api.getIngestionStatus).toHaveBeenCalled())
  })

  it('shows the empty state before reconciliation is run', async () => {
    render(<Reconciliation />)
    expect(
      screen.getByRole('heading', { name: /No reconciliation results yet/ }),
    ).toBeInTheDocument()
    await waitFor(() => expect(api.getIngestionStatus).toHaveBeenCalled())
  })
})
