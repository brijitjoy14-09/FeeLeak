import { useEffect, useState } from 'react'
import { getHealth } from '../services/api'

// Connection states surfaced to the UI.
export const HEALTH_STATUS = {
  CHECKING: 'checking',
  CONNECTED: 'connected',
  DISCONNECTED: 'disconnected',
}

/**
 * Check backend connectivity once on mount via the /health endpoint.
 *
 * Returns one of HEALTH_STATUS. Any network or HTTP error is caught and
 * reported as DISCONNECTED so the application never crashes when the
 * backend is unavailable.
 */
export function useBackendHealth() {
  const [status, setStatus] = useState(HEALTH_STATUS.CHECKING)

  useEffect(() => {
    let active = true

    getHealth()
      .then((data) => {
        if (!active) return
        setStatus(
          data && data.status === 'healthy'
            ? HEALTH_STATUS.CONNECTED
            : HEALTH_STATUS.DISCONNECTED,
        )
      })
      .catch(() => {
        if (!active) return
        setStatus(HEALTH_STATUS.DISCONNECTED)
      })

    return () => {
      active = false
    }
  }, [])

  return status
}
