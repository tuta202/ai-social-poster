import { useState } from 'react'
import { motion } from 'framer-motion'
import type { JobPost } from '../../types'

interface Props {
  post: JobPost
  index: number
  onEdit?: (postId: number, newText: string) => Promise<void>
  showImage?: boolean
}

export default function PostCard({ post, index, onEdit, showImage = true }: Props) {
  const [isEditing, setIsEditing] = useState(false)
  const [editText, setEditText] = useState(post.content_text)
  const [isSaving, setIsSaving] = useState(false)

  const scheduledDate = new Date(post.scheduled_time)
  const dateStr = scheduledDate.toLocaleDateString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric',
  })
  const timeStr = scheduledDate.toLocaleTimeString('en-US', {
    hour: '2-digit', minute: '2-digit',
  })

  const handleSave = async () => {
    if (!onEdit) return
    setIsSaving(true)
    try {
      await onEdit(post.id, editText)
      setIsEditing(false)
    } finally {
      setIsSaving(false)
    }
  }

  const statusColors: Record<string, string> = {
    PENDING: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
    POSTED:  'text-green-400 bg-green-500/10 border-green-500/20',
    FAILED:  'text-red-400 bg-red-500/10 border-red-500/20',
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04 }}
      className="backdrop-blur-sm bg-white/[0.03] border border-purple-500/15
                 rounded-xl p-4 space-y-3 hover:border-purple-500/30 transition-colors"
    >
      {/* Header row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xs font-display font-bold text-purple-400">
            Day {post.day_index}
          </span>
          {post.post_order > 1 && (
            <span className="text-xs text-gray-600">#{post.post_order}</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">{dateStr} · {timeStr}</span>
          <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${statusColors[post.status] ?? 'text-gray-400'}`}>
            {post.status}
          </span>
        </div>
      </div>

      {/* Image */}
      {showImage && post.image_url && (
        <img
          src={post.image_url}
          alt={`Post day ${post.day_index}`}
          className="w-full h-40 object-cover rounded-lg border border-purple-500/10"
        />
      )}

      {/* Content text */}
      {isEditing ? (
        <div className="space-y-2">
          <textarea
            value={editText}
            onChange={e => setEditText(e.target.value)}
            rows={4}
            className="w-full bg-[#111827] border border-cyan-500/30 rounded-lg px-3 py-2
                       text-gray-200 text-sm resize-none focus:outline-none
                       focus:ring-1 focus:ring-cyan-500/40"
          />
          <div className="flex gap-2 justify-end">
            <button
              onClick={() => { setIsEditing(false); setEditText(post.content_text) }}
              className="text-xs px-3 py-1.5 rounded-lg text-gray-500 hover:text-gray-300 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="text-xs px-3 py-1.5 rounded-lg bg-cyan-600/20 text-cyan-300
                         border border-cyan-500/30 hover:bg-cyan-600/30 transition-colors
                         disabled:opacity-50"
            >
              {isSaving ? 'Saving…' : 'Save'}
            </button>
          </div>
        </div>
      ) : (
        <div className="group relative">
          <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
            {post.content_text || (
              <span className="text-gray-600 italic">Content will be generated on confirm…</span>
            )}
          </p>
          {onEdit && post.content_text && (
            <button
              onClick={() => setIsEditing(true)}
              className="absolute top-0 right-0 text-xs text-gray-600 hover:text-cyan-400
                         opacity-0 group-hover:opacity-100 transition-all"
            >
              ✏️ Edit
            </button>
          )}
        </div>
      )}

      {/* Image prompt hint */}
      {post.image_prompt && (
        <p className="text-xs text-gray-600 italic truncate">
          🎨 {post.image_prompt.slice(0, 80)}…
        </p>
      )}
    </motion.div>
  )
}
