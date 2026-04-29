import { useState } from 'react'
import { motion } from 'framer-motion'
import type { Job } from '../../types'
import JobStatusBadge from './JobStatusBadge'

interface Props {
  job: Job
  index: number
  onView: (job: Job) => void
  onPause: (id: number) => Promise<void>
  onResume: (id: number) => Promise<void>
  onDelete: (id: number) => Promise<void>
}

export default function JobCard({ job, index, onView, onPause, onResume, onDelete }: Props) {
  const [isActing, setIsActing] = useState(false)

  const act = async (fn: () => Promise<void>) => {
    setIsActing(true)
    try { await fn() } finally { setIsActing(false) }
  }

  const canPause  = job.status === 'SCHEDULED' || job.status === 'RUNNING'
  const canResume = job.status === 'PAUSED'
  const canDelete = job.status === 'DRAFT'

  const total   = job.total_posts   ?? 0
  const posted  = job.posted_count  ?? 0
  const failed  = job.failed_count  ?? 0
  const pending = total - posted - failed
  const progress = total > 0 ? Math.round((posted / total) * 100) : 0

  const createdDate = new Date(job.created_at).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  })

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="backdrop-blur-md bg-white/5 border border-purple-500/15 rounded-2xl p-5
                 hover:border-purple-500/30 transition-colors group"
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-4">
        <div className="min-w-0">
          <h3 className="font-display font-semibold text-white truncate">{job.title}</h3>
          <p className="text-xs text-gray-600 mt-0.5">Created {createdDate} · Job #{job.id}</p>
        </div>
        <JobStatusBadge status={job.status} />
      </div>

      {/* Progress bar (only for non-DRAFT) */}
      {job.status !== 'DRAFT' && total > 0 && (
        <div className="mb-4 space-y-1.5">
          <div className="flex justify-between text-xs text-gray-600">
            <span>{posted} posted · {failed > 0 ? `${failed} failed · ` : ''}{pending} pending</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-purple-600 to-cyan-500 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.6, delay: index * 0.05 }}
            />
          </div>
          {failed > 0 && (
            <div
              className="h-1 rounded-full bg-red-500/60"
              style={{ width: `${Math.round((failed / total) * 100)}%` }}
            />
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => onView(job)}
          className="text-xs px-3 py-1.5 rounded-lg bg-purple-500/10 text-purple-300
                     border border-purple-500/20 hover:bg-purple-500/20 transition-colors"
        >
          View Posts
        </button>

        {canPause && (
          <button
            onClick={() => act(() => onPause(job.id))}
            disabled={isActing}
            className="text-xs px-3 py-1.5 rounded-lg bg-yellow-500/10 text-yellow-300
                       border border-yellow-500/20 hover:bg-yellow-500/20 transition-colors
                       disabled:opacity-50"
          >
            Pause
          </button>
        )}

        {canResume && (
          <button
            onClick={() => act(() => onResume(job.id))}
            disabled={isActing}
            className="text-xs px-3 py-1.5 rounded-lg bg-cyan-500/10 text-cyan-300
                       border border-cyan-500/20 hover:bg-cyan-500/20 transition-colors
                       disabled:opacity-50"
          >
            Resume
          </button>
        )}

        {canDelete && (
          <button
            onClick={() => act(() => onDelete(job.id))}
            disabled={isActing}
            className="text-xs px-3 py-1.5 rounded-lg bg-red-500/10 text-red-400
                       border border-red-500/20 hover:bg-red-500/20 transition-colors
                       disabled:opacity-50 ml-auto"
          >
            Delete
          </button>
        )}
      </div>
    </motion.div>
  )
}
