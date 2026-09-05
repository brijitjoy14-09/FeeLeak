import { useState } from 'react'
import Sidebar from './Sidebar'

/**
 * App frame: fixed sidebar + main content area with a compact top bar.
 * The top bar exposes a menu toggle used to reveal the sidebar on narrow
 * screens (the sidebar is always visible on desktop via CSS).
 */
function AppLayout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="app-shell">
      <Sidebar open={sidebarOpen} onNavigate={() => setSidebarOpen(false)} />

      {sidebarOpen && (
        <button
          type="button"
          className="sidebar-scrim"
          aria-label="Close navigation"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <div className="app-main">
        <header className="topbar">
          <button
            type="button"
            className="menu-toggle"
            aria-label="Toggle navigation"
            aria-expanded={sidebarOpen}
            onClick={() => setSidebarOpen((v) => !v)}
          >
            <span aria-hidden="true">☰</span>
          </button>
          <span className="topbar-title">Finance Controller</span>
        </header>

        <main className="app-content">{children}</main>
      </div>
    </div>
  )
}

export default AppLayout
