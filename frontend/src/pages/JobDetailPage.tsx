import { useParams, useNavigate } from 'react-router-dom'
import { useEffect, useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import PageWrapper from '../components/layout/PageWrapper'
import TopNav from '../components/layout/TopNav'
import DayCard from '../components/dashboard/DayCard'
import JobStatusBadge from '../components/dashboard/JobStatusBadge'
import { api } from '../services/api'
import type { Job } from '../types'

function formatDate(str: string): string {
  const d = new Date(str)
  return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}/${d.getFullYear()}`
}

export default function JobDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const jobId = parseInt(id ?? '0', 10)

  const [job, setJob] = useState<Job | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [isActing, setIsActing] = useState(false)

  const fetchJob = useCallback(async () => {
    try {
      const res = await api.get(`/jobs/${jobId}`)
      setJob(res.data)
      setError('')
    } catch {
      setError('Không tải được job')
    } finally {
      setLoading(false)
    }
  }, [jobId])

  useEffect(() => {
    fetchJob()
    const interval = setInterval(fetchJob, 15_000)
    return () => clearInterval(interval)
  }, [fetchJob])

  const act = async (fn: () => Promise<void>) => {
    setIsActing(true)
    try { await fn() } finally { setIsActing(false) }
  }

  if (loading) {
    return (
      <PageWrapper>
        <TopNav />
        <div className="flex justify-center items-center h-64">
          <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
        </div>
      </PageWrapper>
    )
  }

  if (error || !job) {
    return (
      <PageWrapper>
        <TopNav />
        <div className="text-center py-20 space-y-2">
          <p className="text-red-400 text-sm">{error || 'Job not found'}</p>
          <button
            onClick={() => navigate('/dashboard')}
            className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
          >
            ← Quay lại Dashboard
          </button>
        </div>
      </PageWrapper>
    )
  }

  const posts = job.posts ?? []
  const posted = posts.filter(p => p.status === 'POSTED').length
  const total = posts.length
  const progress = total > 0 ? Math.round((posted / total) * 100) : 0
  const hasImages = job.parsed_config?.has_images ?? false
  const canPause = job.status === 'SCHEDULED' || job.status === 'RUNNING'
  const canResume = job.status === 'PAUSED'
  const canDelete = job.status === 'DRAFT'

  return (
    <PageWrapper>
      <TopNav />

      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Back */}
        <motion.button
          initial={{ opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
          onClick={() => navigate('/dashboard')}
          className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-300
                     mb-6 transition-colors"
        >
          ← Quay lại Dashboard
        </motion.button>

        <div className="flex gap-6 items-start">
          {/* ── Sidebar ── */}
          <motion.aside
            initial={{ opacity: 0, x: -16 }}
            animate={{ opacity: 1, x: 0 }}
            className="w-[280px] flex-shrink-0 space-y-4 sticky top-24"
          >
            {/* Info card */}
            <div className="backdrop-blur-sm bg-white/[0.03] border border-purple-500/15 rounded-2xl p-5 space-y-4">
              <div>
                <h1 className="font-display font-bold text-white text-lg leading-tight">
                  {job.title}
                </h1>
                <p className="text-xs text-gray-600 mt-1">Job #{job.id}</p>
              </div>

              <JobStatusBadge status={job.status} />

              {total > 0 && (
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>{posted}/{total} đã đăng</span>
                    <span>{progress}%</span>
                  </div>
                  <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-purple-600 to-cyan-500 rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${progress}%` }}
                      transition={{ duration: 0.6 }}
                    />
                  </div>
                </div>
              )}

              <div className="space-y-1.5 text-xs text-gray-500">
                <p>
                  Ngày tạo:{' '}
                  <span className="text-gray-400">{formatDate(job.created_at)}</span>
                </p>
                {job.parsed_config?.post_time && (
                  <p>
                    Giờ đăng:{' '}
                    <span className="text-gray-400">{job.parsed_config.post_time}</span>
                  </p>
                )}
              </div>
            </div>

            {/* Actions card */}
            {(canPause || canResume || canDelete) && (
              <div className="backdrop-blur-sm bg-white/[0.03] border border-purple-500/15 rounded-2xl p-4 space-y-2">
                {canPause && (
                  <button
                    onClick={() => act(() => api.post(`/jobs/${jobId}/pause`).then(fetchJob))}
                    disabled={isActing}
                    className="w-full text-xs px-3 py-2 rounded-lg bg-yellow-500/10 text-yellow-300
                               border border-yellow-500/20 hover:bg-yellow-500/20 transition-colors
                               disabled:opacity-50"
                  >
                    Tạm dừng
                  </button>
                )}
                {canResume && (
                  <button
                    onClick={() => act(() => api.post(`/jobs/${jobId}/resume`).then(fetchJob))}
                    disabled={isActing}
                    className="w-full text-xs px-3 py-2 rounded-lg bg-cyan-500/10 text-cyan-300
                               border border-cyan-500/20 hover:bg-cyan-500/20 transition-colors
                               disabled:opacity-50"
                  >
                    Tiếp tục
                  </button>
                )}
                {canDelete && (
                  <button
                    onClick={() => act(async () => {
                      await api.delete(`/jobs/${jobId}`)
                      navigate('/dashboard')
                    })}
                    disabled={isActing}
                    className="w-full text-xs px-3 py-2 rounded-lg bg-red-500/10 text-red-400
                               border border-red-500/20 hover:bg-red-500/20 transition-colors
                               disabled:opacity-50"
                  >
                    Xoá Job
                  </button>
                )}
              </div>
            )}
          </motion.aside>

          {/* ── Posts list ── */}
          <div className="flex-1 space-y-3 min-w-0">
            {posts.length === 0 ? (
              <p className="text-gray-600 text-sm text-center py-12">
                Chưa có bài đăng nào
              </p>
            ) : (
              posts.map((post, i) => (
                <motion.div
                  key={post.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.04 }}
                >
                  <DayCard
                    post={post}
                    jobId={jobId}
                    hasImages={hasImages}
                    onUpdate={fetchJob}
                  />
                </motion.div>
              ))
            )}
          </div>
        </div>
      </div>
    </PageWrapper>
  )
}
