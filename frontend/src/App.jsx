import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import AppLayout from './components/layout/AppLayout'
import Analytics from './pages/Analytics'
import ComingSoon from './pages/ComingSoon'
import Copilot from './pages/Copilot'
import Dashboard from './pages/Dashboard'
import Exceptions from './pages/Exceptions'
import Reconciliation from './pages/Reconciliation'

function App() {
  return (
    <BrowserRouter>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/reconciliation" element={<Reconciliation />} />
          <Route path="/exceptions" element={<Exceptions />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/copilot" element={<Copilot />} />
          <Route path="/settings" element={<ComingSoon title="Settings" />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AppLayout>
    </BrowserRouter>
  )
}

export default App
