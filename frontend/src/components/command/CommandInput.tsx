import { useState } from 'react'
import { motion } from 'framer-motion'

const EXAMPLES = [
  'Tạo 10 bài học từ vựng N3 trong 10 ngày, mỗi ngày 1 bài lúc 08:00, có ảnh minh họa anime',
  'Tạo 5 bài học từ vựng chủ đề ăn uống, có ảnh minh họa sát theo nội dung từng từ vựng',
  'Create 7 motivational quotes for language learners, post 1 daily at 20:00, with minimalist photos',
  'Lên lịch chuỗi 14 mẹo ngữ pháp N4, mỗi ngày 2 bài lúc 12:00, kèm hashtag #jlpt #n4',
]

interface Props {
  onParse: (input: string) => void
  isLoading: boolean
  disabled?: boolean
}

export default function CommandInput({ onParse, isLoading, disabled }: Props) {
  const [value, setValue] = useState('')

  const handleSubmit = () => {
    if (value.trim().length < 5) return
    onParse(value.trim())
  }

  return (
    <div className="space-y-4">
      {/* Textarea */}
      <div className="relative">
        <textarea
          value={value}
          onChange={e => setValue(e.target.value)}
          disabled={disabled || isLoading}
          placeholder={`Describe your campaign in natural language...\n\ne.g. "Tạo 10 bài học từ vựng N2, mỗi bài có ảnh minh họa sát theo nội dung từ vựng đó..."`}
          rows={5}
          className="w-full bg-[#111827] border border-purple-500/20 rounded-2xl px-5 py-4
                     text-gray-100 placeholder-gray-600 text-sm leading-relaxed resize-none
                     focus:outline-none focus:border-cyan-500/60 focus:ring-1 focus:ring-cyan-500/20
                     disabled:opacity-50 transition-all duration-200"
        />
        <span className="absolute bottom-3 right-4 text-xs text-gray-600">
          {value.length}/2000
        </span>
      </div>

      {/* Example chips */}
      <div className="flex flex-wrap gap-2">
        <span className="text-xs text-gray-600 self-center">Try:</span>
        {EXAMPLES.map((ex, i) => (
          <button
            key={i}
            onClick={() => setValue(ex)}
            disabled={isLoading}
            className="text-xs px-3 py-1.5 rounded-full border border-purple-500/20
                       text-gray-500 hover:text-gray-300 hover:border-purple-500/40
                       hover:bg-purple-500/5 transition-all duration-200 text-left"
          >
            {ex.length > 45 ? ex.slice(0, 45) + '…' : ex}
          </button>
        ))}
      </div>

      {/* Parse button */}
      <motion.button
        onClick={handleSubmit}
        disabled={isLoading || disabled || value.trim().length < 5}
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className="w-full py-3.5 rounded-xl font-display font-semibold text-sm text-white
                   bg-gradient-to-r from-purple-600 to-cyan-600
                   hover:from-purple-500 hover:to-cyan-500
                   disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100
                   shadow-lg shadow-purple-500/20 hover:shadow-purple-500/40
                   transition-all duration-300"
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
            Parsing...
          </span>
        ) : (
          <span className="flex items-center justify-center gap-2">
            <span>⚡</span> Parse Campaign
          </span>
        )}
      </motion.button>
    </div>
  )
}
