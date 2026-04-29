import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAuthStore } from '../stores/authStore'
import { api } from '../services/api'
import PageWrapper from '../components/layout/PageWrapper'

export default function LoginPage() {
  const navigate = useNavigate()
  const { setAuth, token } = useAuthStore()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    if (token) navigate('/command', { replace: true })
  }, [token, navigate])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)
    try {
      const res = await api.post('/auth/login', { username, password })
      setAuth(res.data.user, res.data.access_token)
      navigate('/command', { replace: true })
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })
          ?.response?.data?.detail ?? 'Login failed. Please try again.'
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <PageWrapper className="flex items-center justify-center p-4">
      {/* Ambient glow blobs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/3 w-96 h-96 bg-purple-600/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/3 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
        className="relative w-full max-w-md"
      >
        {/* Card */}
        <div className="backdrop-blur-md bg-white/5 border border-purple-500/20 rounded-2xl p-8 shadow-2xl">

          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-purple-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-purple-500/30">
              <span className="text-white text-2xl font-bold font-display">P</span>
            </div>
            <h1 className="text-2xl font-display font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
              PostPilot AI
            </h1>
            <p className="text-gray-500 text-sm mt-1">Sign in to your workspace</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="admin"
                required
                autoFocus
                className="w-full bg-[#111827] border border-purple-500/20 rounded-xl px-4 py-3
                           text-gray-100 placeholder-gray-600 text-sm
                           focus:outline-none focus:border-cyan-500/60 focus:ring-1 focus:ring-cyan-500/30
                           transition-all duration-200"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full bg-[#111827] border border-purple-500/20 rounded-xl px-4 py-3
                           text-gray-100 placeholder-gray-600 text-sm
                           focus:outline-none focus:border-cyan-500/60 focus:ring-1 focus:ring-cyan-500/30
                           transition-all duration-200"
              />
            </div>

            {/* Error */}
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-2.5"
              >
                {error}
              </motion.div>
            )}

            {/* Submit */}
            <motion.button
              type="submit"
              disabled={isLoading}
              whileHover={{ scale: isLoading ? 1 : 1.02 }}
              whileTap={{ scale: isLoading ? 1 : 0.98 }}
              className="w-full py-3 rounded-xl font-display font-semibold text-sm text-white
                         bg-gradient-to-r from-purple-600 to-cyan-600
                         hover:from-purple-500 hover:to-cyan-500
                         disabled:opacity-50 disabled:cursor-not-allowed
                         shadow-lg shadow-purple-500/20 hover:shadow-purple-500/40
                         transition-all duration-300 mt-2"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  Signing in...
                </span>
              ) : (
                'Sign In'
              )}
            </motion.button>
          </form>
        </div>

        {/* Footer note */}
        <p className="text-center text-gray-600 text-xs mt-4">
          PostPilot AI — Automated Facebook Publishing
        </p>
      </motion.div>
    </PageWrapper>
  )
}
