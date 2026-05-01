import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import type { JobPost } from '../../types'
import { PostStatusBadge } from './JobStatusBadge'
import { updatePostText, regenerateImage, approvePost } from '../../services/api'

interface DayCardProps {
  post: JobPost
  jobId: number
  hasImages: boolean
  onUpdate: () => void
}

function formatDateTime(str: string): string {
  const d = new Date(str)
  const day = String(d.getDate()).padStart(2, '0')
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const year = d.getFullYear()
  const hours = String(d.getHours()).padStart(2, '0')
  const mins = String(d.getMinutes()).padStart(2, '0')
  return `${day}/${month}/${year} ${hours}:${mins}`
}

export default function DayCard({ post, jobId, hasImages, onUpdate }: DayCardProps) {
  const [editText, setEditText] = useState(post.content_text ?? '')
  const [isDirty, setIsDirty] = useState(false)
  const [isSavingText, setIsSavingText] = useState(false)
  const [imageStyleNote, setImageStyleNote] = useState(post.image_style_note ?? '')
  const [isGeneratingImage, setIsGeneratingImage] = useState(false)
  const [isApproving, setIsApproving] = useState(false)
  const [error, setError] = useState('')
  const [imageError, setImageError] = useState('')

  useEffect(() => {
    if (!isDirty) setEditText(post.content_text ?? '')
  }, [post.content_text, isDirty])

  useEffect(() => {
    setImageStyleNote(post.image_style_note ?? '')
  }, [post.image_style_note])

  const handleSaveText = async () => {
    setIsSavingText(true)
    setError('')
    try {
      await updatePostText(jobId, post.id, editText)
      setIsDirty(false)
      onUpdate()
    } catch {
      setError('Lưu thất bại, thử lại')
    } finally {
      setIsSavingText(false)
    }
  }

  const handleGenImage = async () => {
    setIsGeneratingImage(true)
    setImageError('')
    try {
      await regenerateImage(jobId, post.id, imageStyleNote || undefined)
      onUpdate()
    } catch {
      setImageError('Gen ảnh thất bại. Vui lòng thử lại.')
    } finally {
      setIsGeneratingImage(false)
    }
  }

  const handleApprove = async () => {
    setIsApproving(true)
    setError('')
    try {
      await approvePost(jobId, post.id, imageStyleNote || undefined)
      onUpdate()
    } catch {
      setError('Approve thất bại, thử lại')
    } finally {
      setIsApproving(false)
    }
  }

  const isPending = post.status === 'PENDING'
  const isApproved = post.status === 'APPROVED'
  const isPosted = post.status === 'POSTED'
  const isFailed = post.status === 'FAILED'
  const hasContent = post.content_text !== null && post.content_text !== ''
  const canApprove = hasImages ? post.image_url !== null : true

  const dayLabel = (
    <span className="text-sm font-display font-semibold text-purple-400">
      Day {post.day_index}
      {post.post_order > 1 && (
        <span className="text-gray-500 font-normal text-xs ml-1">#{post.post_order}</span>
      )}
    </span>
  )

  // Case 5: FAILED
  if (isFailed) {
    return (
      <div className="backdrop-blur-sm bg-red-500/5 border border-red-500/20 rounded-xl p-4 space-y-2">
        <div className="flex items-center justify-between">
          {dayLabel}
          <PostStatusBadge status="FAILED" />
        </div>
        {post.error_message && (
          <p className="text-xs text-red-400">{post.error_message}</p>
        )}
      </div>
    )
  }

  // Case 1: Not yet generated (Day 2+)
  if (!hasContent) {
    return (
      <div className="backdrop-blur-sm bg-white/[0.02] border border-purple-500/10 rounded-xl p-4 space-y-1">
        <div className="flex items-center justify-between">
          {dayLabel}
          <PostStatusBadge status={post.status} />
        </div>
        <p className="text-xs text-gray-500">Dự kiến: {formatDateTime(post.scheduled_time)}</p>
        <p className="text-xs text-gray-600 italic">
          Nội dung sẽ được tạo tự động 60 phút trước giờ đăng
        </p>
      </div>
    )
  }

  // Case 3 & 4: APPROVED or POSTED (read-only)
  if (isApproved || isPosted) {
    return (
      <div className={`backdrop-blur-sm border rounded-xl p-4 space-y-3
        ${isPosted ? 'bg-green-500/5 border-green-500/20' : 'bg-blue-500/5 border-blue-500/20'}`}
      >
        <div className="flex items-center justify-between">
          {dayLabel}
          <div className="flex items-center gap-2">
            <PostStatusBadge status={post.status} />
            <span className="text-xs text-gray-500">{formatDateTime(post.scheduled_time)}</span>
          </div>
        </div>

        <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
          {post.content_text}
        </p>

        {post.image_url && (
          <img
            src={post.image_url}
            alt={`Day ${post.day_index}`}
            className="w-full max-h-64 object-cover rounded-lg border border-purple-500/10"
          />
        )}

        <p className="text-xs text-gray-500">
          {isPosted
            ? `Đã đăng lúc: ${post.posted_at ? formatDateTime(post.posted_at) : '—'}`
            : `Đã duyệt lúc: ${post.approved_at ? formatDateTime(post.approved_at) : '—'}`}
        </p>

        {isPosted && post.fb_post_id && (
          <a
            href={`https://www.facebook.com/${post.fb_post_id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
          >
            Xem trên Facebook →
          </a>
        )}
      </div>
    )
  }

  // Case 2: PENDING with content — inline edit + image gen + approve
  return (
    <div className="backdrop-blur-sm bg-yellow-500/5 border border-yellow-500/20 rounded-xl p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        {dayLabel}
        <div className="flex items-center gap-2">
          <PostStatusBadge status="PENDING" />
          <span className="text-xs text-gray-500">{formatDateTime(post.scheduled_time)}</span>
        </div>
      </div>

      {/* Text edit */}
      <div className="space-y-2">
        <textarea
          value={editText}
          onChange={e => {
            setEditText(e.target.value)
            setIsDirty(e.target.value !== (post.content_text ?? ''))
          }}
          rows={6}
          className="w-full bg-[#111827] border border-purple-500/20 rounded-lg px-3 py-2
                     text-gray-200 text-sm resize-none focus:outline-none
                     focus:ring-1 focus:ring-purple-500/40"
        />
        {isDirty && (
          <div className="flex justify-end">
            <button
              onClick={handleSaveText}
              disabled={isSavingText}
              className="text-xs px-3 py-1.5 rounded-lg bg-cyan-600/20 text-cyan-300
                         border border-cyan-500/30 hover:bg-cyan-600/30 transition-colors
                         disabled:opacity-50"
            >
              {isSavingText ? 'Đang lưu...' : 'Lưu text'}
            </button>
          </div>
        )}
      </div>

      {/* Image section */}
      {hasImages && (
        <div className="border-t border-purple-500/10 pt-3 space-y-2">
          {post.image_url && (
            <img
              src={post.image_url}
              alt={`Day ${post.day_index}`}
              className="w-full max-h-64 object-cover rounded-lg border border-purple-500/10"
            />
          )}

          {/* Day 2+ with missing image: scheduler may not have run or failed */}
          {!post.image_url && post.day_index > 1 ? (
            <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-3 space-y-2">
              <p className="text-xs text-yellow-300/80">
                Ảnh chưa được tạo. Scheduler sẽ tự gen trước giờ đăng,
                hoặc bạn có thể gen thủ công ngay bây giờ.
              </p>
              <input
                type="text"
                value={imageStyleNote}
                onChange={e => setImageStyleNote(e.target.value)}
                placeholder="Ghi chú về ảnh (tuỳ chọn)"
                className="w-full bg-[#111827] border border-yellow-500/20 rounded-lg px-3 py-1.5
                           text-gray-200 text-xs focus:outline-none focus:ring-1
                           focus:ring-yellow-500/40 placeholder:text-gray-600"
              />
              <button
                onClick={handleGenImage}
                disabled={isGeneratingImage}
                className="text-xs px-3 py-1.5 rounded-lg bg-yellow-500/20 text-yellow-300
                           border border-yellow-500/30 hover:bg-yellow-500/30 transition-colors
                           disabled:opacity-50 flex items-center gap-1"
              >
                {isGeneratingImage ? (
                  <>
                    <span className="w-3 h-3 border-2 border-yellow-300/40 border-t-yellow-300 rounded-full animate-spin" />
                    Đang gen...
                  </>
                ) : 'Gen ảnh ngay'}
              </button>
              {imageError && <p className="text-xs text-red-400">{imageError}</p>}
            </div>
          ) : (
            /* Day 1 (no image) or any day (has image): regular input + button */
            <>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={imageStyleNote}
                  onChange={e => setImageStyleNote(e.target.value)}
                  placeholder="Ghi chú về ảnh (tuỳ chọn: bớt anime, thêm pastel...)"
                  className="flex-1 bg-[#111827] border border-purple-500/20 rounded-lg px-3 py-1.5
                             text-gray-200 text-xs focus:outline-none focus:ring-1
                             focus:ring-purple-500/40 placeholder:text-gray-600"
                />
                <button
                  onClick={handleGenImage}
                  disabled={isGeneratingImage}
                  className="text-xs px-3 py-1.5 rounded-lg bg-purple-600/20 text-purple-300
                             border border-purple-500/30 hover:bg-purple-600/30 transition-colors
                             disabled:opacity-50 whitespace-nowrap flex items-center gap-1"
                >
                  {isGeneratingImage ? (
                    <>
                      <span className="w-3 h-3 border-2 border-purple-300/40 border-t-purple-300 rounded-full animate-spin" />
                      Đang gen...
                    </>
                  ) : post.image_url ? 'Gen lại ảnh' : 'Gen ảnh'}
                </button>
              </div>
              {imageError && <p className="text-xs text-red-400">{imageError}</p>}
            </>
          )}
        </div>
      )}

      {/* Error */}
      {error && (
        <p className="text-xs text-red-400 bg-red-500/10 rounded px-2 py-1">{error}</p>
      )}

      {/* Approve */}
      <div className="border-t border-purple-500/10 pt-3">
        {!canApprove && (
          <p className="text-xs text-gray-500 mb-2 text-center">
            Vui lòng gen ảnh trước khi approve
          </p>
        )}
        <motion.button
          onClick={handleApprove}
          disabled={isApproving || !canApprove}
          whileHover={canApprove ? { scale: 1.02 } : {}}
          whileTap={canApprove ? { scale: 0.98 } : {}}
          className="w-full py-2 rounded-lg text-sm font-display font-semibold
                     bg-gradient-to-r from-purple-600/80 to-cyan-600/80
                     hover:from-purple-500 hover:to-cyan-500
                     text-white border border-purple-500/30
                     disabled:opacity-40 disabled:cursor-not-allowed
                     transition-all duration-200"
        >
          {isApproving ? (
            <span className="flex items-center justify-center gap-2">
              <span className="w-3 h-3 border-2 border-white/40 border-t-white rounded-full animate-spin" />
              Đang approve...
            </span>
          ) : 'Approve & Lưu'}
        </motion.button>
      </div>
    </div>
  )
}
