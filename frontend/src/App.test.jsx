import { render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import * as api from './services/api'

beforeEach(() => {
  // The dashboard's live panel calls the backend on mount; keep it offline.
  vi.spyOn(api, 'getReconciliationSummary').mockRejectedValue(
    new api.ApiError('no reconciliation', { code: 'NO_RECONCILIATION' }),
  )
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('App shell + backend connectivity', () => {
  it('renders without crashing', async () => {
    vi.spyOn(api, 'getHealth').mockResolvedValue({ status: 'healthy' })
    const { container } = render(<App />)
    expect(container).toBeTruthy()
    await screen.findByText('Connected')
  })

  it('shows the FeeLeak brand', async () => {
    vi.spyOn(api, 'getHealth').mockResolvedValue({ status: 'healthy' })
    render(<App />)
    expect(screen.getByText('FeeLeak')).toBeInTheDocument()
    await screen.findByText('Connected')
  })

  it('shows Connected when the backend is healthy', async () => {
    vi.spyOn(api, 'getHealth').mockResolvedValue({ status: 'healthy' })
    render(<App />)
    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument()
    })
  })

  it('shows Disconnected without crashing when the backend fails', async () => {
    vi.spyOn(api, 'getHealth').mockRejectedValue(new Error('Network error'))
    render(<App />)
    await waitFor(() => {
      expect(screen.getByText('Disconnected')).toBeInTheDocument()
    })
    // Dashboard content still renders — the app does not depend on the backend.
    expect(screen.getByText('Overview')).toBeInTheDocument()
  })
})
