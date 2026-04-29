import { motion, AnimatePresence } from 'framer-motion'
import type { Job } from '../../types'
import PostCard from '../preview/PostCard'
import JobStatusBadge from './JobStatusBadge'

interface Props {
  job: Job | null
  onClose: () => void
}

export default function JobDetailPanel({ job, onClose }: Props) {
  return (
    <AnimatePresence>
      {job && (
        <>
          {/* Backdrop */}
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
          />

          {/* Panel */}
          <motion.div
            key="panel"
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 300 }}
            className="fixed right-0 top-0 h-full w-full max-w-lg bg-[#0D1120] border-l
                       border-purple-500/20 z-50 flex flex-col"
          >
            {/* Panel header */}
            <div className="flex items-center justify-between p-6 border-b border-purple-500/10">
              <div>
                <h2 className="font-display font-bold text-white truncate max-w-xs">{job.title}</h2>
                <div className="flex items-center gap-2 mt-1">
                  <JobStatusBadge status={job.status} size="sm" />
                  <span className="text-xs text-gray-600">Job #{job.id}</span>
                </div>
              </div>
              <button
                onClick={onClose}
                className="w-8 h-8 flex items-center justify-center rounded-lg
                           text-gray-500 hover:text-gray-300 hover:bg-white/5 transition-colors"
              >
                &#x2715;
              </button>
            </div>

            {/* Posts list — scrollable */}
            <div className="flex-1 overflow-y-auto p-6 space-y-3">
              {!job.posts || job.posts.length === 0 ? (
                <p className="text-gray-600 text-sm text-center py-8">No posts yet</p>
              ) : (
                job.posts.map((post, i) => (
                  <PostCard
                    key={post.id}
                    post={post}
                    index={i}
                    showImage={!!post.image_url}
                  />
                ))
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
