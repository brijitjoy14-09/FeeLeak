import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import Copilot from './Copilot'
import * as api from '../services/api'

afterEach(() => vi.restoreAllMocks())

describe('Finance Copilot page', () => {
  it('renders heading and suggestions', () => {
    render(<Copilot />)
    expect(screen.getByRole('heading', { name: 'Finance Copilot' })).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'How much potential leakage was detected?' }),
    ).toBeInTheDocument()
  })

  it('sends a question and renders the backend answer verbatim', async () => {
    vi.spyOn(api, 'copilotQuery').mockResolvedValue({
      intent: 'ANALYTICS_SUMMARY',
      answer: 'There are 7 active exception(s) with ₹8,092 in potential unexplained leakage.',
      tools_used: ['get_analytics_summary'],
      data: {},
    })

    render(<Copilot />)
    fireEvent.click(
      screen.getByRole('button', { name: 'How much potential leakage was detected?' }),
    )

    await waitFor(() =>
      expect(
        screen.getByText(/₹8,092 in potential unexplained leakage/),
      ).toBeInTheDocument(),
    )
    expect(api.copilotQuery).toHaveBeenCalledWith(
      'How much potential leakage was detected?',
    )
  })
})
