import { useState } from 'react'
import { motion } from 'framer-motion'
import type { JobPost } from '../../types'

interface Props {
  post: JobPost
  index: number
  onEdit?: (postId: number, newText: string) => Promise<void>
  onApprove?: (postId: number, editedText?: string) => Promise<void>
  showImage?: boolean
  showApprove?: boolean
}

export default function PostCard({
  post, index, onEdit, onApprove, showImage = true, showApprove = false,
}: Props) {
  const [isEditing, setIsEditing]     = useState(false)
  const [editText, setEditText]       = useState(post.content_text ?? '')
  const [isSaving, setIsSaving]       = useState(false)
  const [isApproving, setIsApproving] = useState(false)

  const contentText = post.content_text

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

  const handleApprove = async () => {
    if (!onApprove) return
    setIsApproving(true)
    try {
      const edited = isEditing && editText !== (post.content_text ?? '')
        ? editText
        : undefined
      await onApprove(post.id, edited)
      setIsEditing(false)
    } finally {
      setIsApproving(false)
    }
  }

  const statusColors: Record<string, string> = {
    PENDING:  'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
    APPROVED: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
    POSTED:   'text-green-400 bg-green-500/10 border-green-500/20',
    FAILED:   'text-red-400 bg-red-500/10 border-red-500/20',
  }

  const isPending  = post.status === 'PENDING'
  const isApproved = post.status === 'APPROVED'
  const isPosted   = post.status === 'POSTED'
  const hasContent = contentText !== null && contentText !== ''

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04 }}
      className={`backdrop-blur-sm border rounded-xl p-4 space-y-3 transition-colors
        ${isPending && showApprove && hasContent
          ? 'bg-yellow-500/5 border-yellow-500/20 hover:border-yellow-500/40'
          : isApproved
          ? 'bg-blue-500/5 border-blue-500/20'
          : 'bg-white/[0.03] border-purple-500/15 hover:border-purple-500/30'
        }`}
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
          <span className={`text-xs px-2 py-0.5 rounded-full border font-medium
            ${statusColors[post.status] ?? 'text-gray-400'}`}>
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

      {/* Content — null guard */}
      {!hasContent ? (
        <div className="py-3 text-center">
          <p className="text-gray-600 text-sm italic">
            Content will be generated closer to post time...
          </p>
        </div>
      ) : isEditing ? (
        <div className="space-y-2">
          <textarea
            value={editText}
            onChange={e => setEditText(e.target.value)}
            rows={5}
            className="w-full bg-[#111827] border border-cyan-500/30 rounded-lg px-3 py-2
                       text-gray-200 text-sm resize-none focus:outline-none
                       focus:ring-1 focus:ring-cyan-500/40"
          />
          <div className="flex gap-2 justify-between items-center">
            <button
              onClick={() => { setIsEditing(false); setEditText(contentText ?? '') }}
              className="text-xs px-3 py-1.5 rounded-lg text-gray-500 hover:text-gray-300 transition-colors"
            >
              Cancel
            </button>
            <div className="flex gap-2">
              {onEdit && !showApprove && (
                <button
                  onClick={handleSave}
                  disabled={isSaving}
                  className="text-xs px-3 py-1.5 rounded-lg bg-cyan-600/20 text-cyan-300
                             border border-cyan-500/30 hover:bg-cyan-600/30 transition-colors
                             disabled:opacity-50"
                >
                  {isSaving ? 'Saving...' : 'Save'}
                </button>
              )}
              {showApprove && isPending && onApprove && (
                <button
                  onClick={handleApprove}
                  disabled={isApproving}
                  className="text-xs px-4 py-1.5 rounded-lg
                             bg-gradient-to-r from-purple-600 to-cyan-600
                             text-white font-medium hover:from-purple-500 hover:to-cyan-500
                             transition-all disabled:opacity-50"
                >
                  {isApproving ? 'Approving...' : 'Save & Approve'}
                </button>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="group relative">
          <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
            {contentText}
          </p>
          {(onEdit || (showApprove && isPending)) && !isPosted && (
            <button
              onClick={() => { setIsEditing(true); setEditText(contentText ?? '') }}
              className="absolute top-0 right-0 text-xs text-gray-600 hover:text-cyan-400
                         opacity-0 group-hover:opacity-100 transition-all"
            >
              Edit
            </button>
          )}
        </div>
      )}

      {/* Approve button — only for PENDING posts with content */}
      {showApprove && isPending && hasContent && !isEditing && onApprove && (
        <motion.button
          onClick={handleApprove}
          disabled={isApproving}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="w-full py-2 rounded-lg text-sm font-display font-semibold
                     bg-gradient-to-r from-purple-600/80 to-cyan-600/80
                     hover:from-purple-500 hover:to-cyan-500
                     text-white border border-purple-500/30
                     disabled:opacity-50 transition-all duration-200"
        >
          {isApproving ? (
            <span className="flex items-center justify-center gap-2">
              <span className="w-3 h-3 border-2 border-white/40 border-t-white rounded-full animate-spin" />
              Approving...
            </span>
          ) : (
            'Approve to Publish'
          )}
        </motion.button>
      )}

      {/* Approved indicator */}
      {isApproved && (
        <p className="text-xs text-blue-400 text-center">
          Approved — will post at scheduled time
        </p>
      )}

      {/* Image prompt hint */}
      {post.image_prompt && (
        <p className="text-xs text-gray-600 italic truncate">
          Image: {post.image_prompt.slice(0, 80)}...
        </p>
      )}

      {/* Error message */}
      {post.error_message && (
        <p className="text-xs text-red-400 bg-red-500/10 rounded px-2 py-1">
          Error: {post.error_message}
        </p>
      )}
    </motion.div>
  )
}
