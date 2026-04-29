import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import PageWrapper from '../components/layout/PageWrapper'
import TopNav from '../components/layout/TopNav'
import { api } from '../services/api'
import type { FacebookPage } from '../types'

export default function FacebookSetupPage() {
  const [page, setPage]           = useState<FacebookPage | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [token, setToken]         = useState('')
  const [pageId, setPageId]       = useState('')
  const [isSaving, setIsSaving]   = useState(false)
  const [message, setMessage]     = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  useEffect(() => {
    api.get('/facebook/page')
      .then(r => setPage(r.data))
      .catch(() => setPage(null))
      .finally(() => setIsLoading(false))
  }, [])

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSaving(true)
    setMessage(null)
    try {
      const res = await api.post('/facebook/setup-token', {
        short_lived_token: token,
        page_id: pageId,
      })
      setPage(res.data)
      setToken('')
      setMessage({ type: 'success', text: `Connected to "${res.data.page_name}"!` })
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setMessage({ type: 'error', text: detail || 'Setup failed. Check token and page ID.' })
    } finally {
      setIsSaving(false)
    }
  }

  const handleDisconnect = async () => {
    await api.delete('/facebook/page').catch(() => {})
    setPage(null)
    setMessage({ type: 'success', text: 'Facebook page disconnected.' })
  }

  return (
    <PageWrapper>
      <TopNav />
      <main className="max-w-xl mx-auto px-6 py-10 space-y-8">

        <div className="text-center space-y-2">
          <motion.h1
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-3xl font-display font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent"
          >
            Facebook Setup
          </motion.h1>
          <p className="text-gray-500 text-sm">Connect your Facebook Page to enable auto-posting</p>
        </div>

        {/* Connected page status */}
        {!isLoading && page && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="backdrop-blur-md bg-green-500/5 border border-green-500/20 rounded-2xl p-5"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Connected Page</p>
                <p className="font-display font-bold text-white">{page.page_name || page.page_id}</p>
                <p className="text-xs text-gray-600 mt-0.5">ID: {page.page_id}</p>
                <p className="text-xs text-green-400 mt-1">Permanent token · auto-posting enabled</p>
              </div>
              <span className="text-2xl">✅</span>
            </div>
            <button
              onClick={handleDisconnect}
              className="mt-4 text-xs text-red-400 hover:text-red-300 transition-colors"
            >
              Disconnect
            </button>
          </motion.div>
        )}

        {/* Setup form */}
        <div className="backdrop-blur-md bg-white/5 border border-purple-500/20 rounded-2xl p-6 space-y-5">
          <h2 className="font-display font-semibold text-white">
            {page ? 'Update Connection' : 'Connect Facebook Page'}
          </h2>

          {/* How-to guide */}
          <div className="bg-[#111827] border border-purple-500/10 rounded-xl p-4 text-xs text-gray-500 space-y-1">
            <p className="font-medium text-gray-400 mb-2">How to get your token:</p>
            <p>1. Go to <span className="text-cyan-400">developers.facebook.com/tools/explorer</span></p>
            <p>2. Select your App → click "Generate Access Token"</p>
            <p>3. Grant permissions: <span className="text-purple-300">pages_manage_posts, pages_read_engagement</span></p>
            <p>4. Copy the token and your Page ID below</p>
          </div>

          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">
                Short-lived User Access Token
              </label>
              <input
                type="text"
                value={token}
                onChange={e => setToken(e.target.value)}
                placeholder="EAAxxxxxxxx..."
                required
                className="w-full bg-[#111827] border border-purple-500/20 rounded-xl px-4 py-3
                           text-gray-100 placeholder-gray-600 text-sm
                           focus:outline-none focus:border-cyan-500/60 focus:ring-1 focus:ring-cyan-500/30
                           transition-all duration-200"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-400 mb-1.5 uppercase tracking-wider">
                Facebook Page ID
              </label>
              <input
                type="text"
                value={pageId}
                onChange={e => setPageId(e.target.value)}
                placeholder="123456789012345"
                required
                className="w-full bg-[#111827] border border-purple-500/20 rounded-xl px-4 py-3
                           text-gray-100 placeholder-gray-600 text-sm
                           focus:outline-none focus:border-cyan-500/60 focus:ring-1 focus:ring-cyan-500/30
                           transition-all duration-200"
              />
            </div>

            {message && (
              <motion.div
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                className={`text-sm px-4 py-2.5 rounded-lg border ${
                  message.type === 'success'
                    ? 'text-green-400 bg-green-500/10 border-green-500/20'
                    : 'text-red-400 bg-red-500/10 border-red-500/20'
                }`}
              >
                {message.text}
              </motion.div>
            )}

            <motion.button
              type="submit"
              disabled={isSaving || !token.trim() || !pageId.trim()}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="w-full py-3 rounded-xl font-display font-semibold text-sm text-white
                         bg-gradient-to-r from-purple-600 to-cyan-600
                         hover:from-purple-500 hover:to-cyan-500
                         disabled:opacity-40 disabled:cursor-not-allowed
                         shadow-lg shadow-purple-500/20 transition-all duration-300"
            >
              {isSaving ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  Connecting...
                </span>
              ) : 'Connect Page'}
            </motion.button>
          </form>
        </div>
      </main>
    </PageWrapper>
  )
}
