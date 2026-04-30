import { motion } from 'framer-motion'
import type { JobPost } from '../../types'
import PostCard from './PostCard'

interface ParsedConfigDisplay {
  title: string
  duration_days: number
  items_per_day: number
  post_time: string
  content_type: string
  has_images: boolean
  image_description: string
  tags: string[]
}

interface Props {
  jobId: number
  config: ParsedConfigDisplay
  posts: JobPost[]
  onConfirm: () => void
  isConfirming: boolean
  confirmStep?: string
  confirmProgress?: { current: number; total: number }
  onEditPost?: (postId: number, newText: string) => Promise<void>
}

export default function JobPreview({
  jobId, config, posts, onConfirm, isConfirming,
  confirmStep, confirmProgress, onEditPost,
}: Props) {
  const totalPosts = posts.length

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      {/* Campaign config summary */}
      <div className="backdrop-blur-md bg-white/5 border border-purple-500/20 rounded-2xl p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="font-display font-bold text-lg text-white">{config.title}</h3>
            <p className="text-gray-500 text-sm mt-0.5">Job #{jobId} · DRAFT</p>
          </div>
          <span className="text-xs px-2.5 py-1 rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30 font-medium">
            {config.content_type}
          </span>
        </div>

        {/* Stats grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: 'Duration',    value: `${config.duration_days} days` },
            { label: 'Posts/Day',   value: config.items_per_day.toString() },
            { label: 'Post Time',   value: config.post_time },
            { label: 'Total Posts', value: totalPosts.toString() },
          ].map(stat => (
            <div key={stat.label} className="bg-white/[0.03] border border-purple-500/10 rounded-xl p-3">
              <p className="text-xs text-gray-600 mb-1">{stat.label}</p>
              <p className="font-display font-bold text-white text-lg">{stat.value}</p>
            </div>
          ))}
        </div>

        {/* Tags + images indicator */}
        <div className="flex items-center gap-3 mt-4 flex-wrap">
          {config.has_images && (
            <span className="text-xs px-2 py-1 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              With Images
            </span>
          )}
          {config.tags.map(tag => (
            <span key={tag} className="text-xs px-2 py-1 rounded-full bg-gray-800 text-gray-400 border border-gray-700">
              #{tag}
            </span>
          ))}
        </div>

        {/* Image description */}
        {config.has_images && config.image_description && (
          <div className="mt-3 p-3 bg-cyan-500/5 border border-cyan-500/15 rounded-xl">
            <p className="text-xs text-gray-500 mb-1">Image Style</p>
            <p className="text-sm text-cyan-300">{config.image_description}</p>
          </div>
        )}
      </div>

      {/* Confirm button + progress */}
      <div className="backdrop-blur-md bg-white/5 border border-purple-500/20 rounded-2xl p-5 space-y-4">
        {isConfirming && confirmProgress && (
          <div className="space-y-2">
            <div className="flex justify-between text-xs text-gray-500">
              <span>{confirmStep || 'Generating content...'}</span>
              <span>{confirmProgress.current}/{confirmProgress.total}</span>
            </div>
            <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-purple-600 to-cyan-500 rounded-full"
                initial={{ width: 0 }}
                animate={{
                  width: confirmProgress.total > 0
                    ? `${(confirmProgress.current / confirmProgress.total) * 100}%`
                    : '0%'
                }}
                transition={{ duration: 0.3 }}
              />
            </div>
          </div>
        )}

        <motion.button
          onClick={onConfirm}
          disabled={isConfirming}
          whileHover={{ scale: isConfirming ? 1 : 1.02 }}
          whileTap={{ scale: isConfirming ? 1 : 0.98 }}
          className="w-full py-3.5 rounded-xl font-display font-semibold text-sm text-white
                     bg-gradient-to-r from-purple-600 to-cyan-600
                     hover:from-purple-500 hover:to-cyan-500
                     disabled:opacity-50 disabled:cursor-not-allowed
                     shadow-lg shadow-purple-500/20 transition-all duration-300"
        >
          {isConfirming ? (
            <span className="flex items-center justify-center gap-2">
              <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
              Generating Content...
            </span>
          ) : (
            '🚀 Confirm & Schedule'
          )}
        </motion.button>
      </div>

      {/* Posts preview list */}
      <div className="space-y-3">
        <h4 className="font-display font-semibold text-gray-400 text-sm uppercase tracking-wider">
          {totalPosts} Scheduled Posts
        </h4>
        {posts.map((post, i) => (
          <PostCard
            key={post.id}
            post={post}
            index={i}
            onEdit={onEditPost}
            showImage={config.has_images}
          />
        ))}
      </div>
    </motion.div>
  )
}
