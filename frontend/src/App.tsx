import { Routes, Route, Navigate } from 'react-router-dom'

const Placeholder = ({ name }: { name: string }) => (
  <div className="min-h-screen bg-navy-950 bg-dot-grid flex items-center justify-center">
    <div className="glass rounded-2xl p-8 text-center">
      <h1 className="text-gradient font-display text-3xl font-bold mb-2">PostPilot AI</h1>
      <p className="text-gray-400">{name} — coming soon</p>
    </div>
  </div>
)

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Placeholder name="Login" />} />
      <Route path="/command" element={<Placeholder name="Command" />} />
      <Route path="/dashboard" element={<Placeholder name="Dashboard" />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  )
}
