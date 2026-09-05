import { NavLink } from 'react-router-dom'
import { HEALTH_STATUS, useBackendHealth } from '../../hooks/useBackendHealth'

// Navigation model. `ready: false` sections are shown but marked "Soon".
const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', ready: true },
  { to: '/reconciliation', label: 'Reconciliation', ready: true },
  { to: '/exceptions', label: 'Exceptions', ready: true },
  { to: '/analytics', label: 'Analytics', ready: true },
  { to: '/copilot', label: 'Copilot', ready: true },
  { to: '/settings', label: 'Settings', ready: false },
]

const HEALTH_LABEL = {
  [HEALTH_STATUS.CHECKING]: 'Checking…',
  [HEALTH_STATUS.CONNECTED]: 'Connected',
  [HEALTH_STATUS.DISCONNECTED]: 'Disconnected',
}

function Sidebar({ open, onNavigate }) {
  const health = useBackendHealth()

  return (
    <aside
      className={`sidebar ${open ? 'is-open' : ''}`}
      aria-label="Primary navigation"
    >
      <div className="sidebar-brand">
        <span className="sidebar-logo" aria-hidden="true">
          F
        </span>
        <span className="sidebar-wordmark">
          FeeLeak
          <small>Finance Controller</small>
        </span>
      </div>

      <nav className="sidebar-nav" aria-label="Main">
        <ul>
          {NAV_ITEMS.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                onClick={onNavigate}
                className={({ isActive }) =>
                  `nav-link ${isActive ? 'is-active' : ''}`
                }
              >
                <span className="nav-label">{item.label}</span>
                {!item.ready && <span className="nav-badge">Soon</span>}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <div className="sidebar-footer">
        <span
          className={`health-dot health-${health}`}
          aria-hidden="true"
        />
        <span className="health-text">
          Backend: <strong>{HEALTH_LABEL[health]}</strong>
        </span>
      </div>
    </aside>
  )
}

export default Sidebar
