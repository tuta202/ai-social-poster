import { useEffect, useCallback } from 'react'
import { createPortal } from 'react-dom'
import { motion, AnimatePresence } from 'framer-motion'

interface ImageViewerProps {
  src: string
  alt?: string
  onClose: () => void
}

export default function ImageViewer({ src, alt = 'Image', onClose }: ImageViewerProps) {
  const handleKey = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    },
    [onClose],
  )

  useEffect(() => {
    document.addEventListener('keydown', handleKey)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', handleKey)
      document.body.style.overflow = ''
    }
  }, [handleKey])

  return createPortal(
    <AnimatePresence>
      {/* Backdrop */}
      <motion.div
        key="viewer-backdrop"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.2 }}
        className="fixed inset-0 z-[99999] flex items-center justify-center p-4"
        onClick={onClose}
        style={{ background: 'rgba(0,0,0,0.88)', backdropFilter: 'blur(12px)' }}
      >
        {/* Image container — stops propagation so clicking image doesn't close */}
        <motion.div
          key="viewer-image"
          initial={{ opacity: 0, scale: 0.88 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.88 }}
          transition={{ type: 'spring', stiffness: 300, damping: 28 }}
          className="relative max-w-[90vw] max-h-[90vh]"
          onClick={e => e.stopPropagation()}
        >
          <img
            src={src}
            alt={alt}
            className="max-w-[90vw] max-h-[85vh] rounded-2xl shadow-2xl object-contain"
            style={{ boxShadow: '0 0 80px rgba(139,92,246,0.25)' }}
          />

          {/* Close button */}
          <button
            onClick={onClose}
            aria-label="Close image viewer"
            className="absolute -top-3 -right-3 w-8 h-8 flex items-center justify-center
                       rounded-full bg-gray-900 border border-purple-500/30
                       text-gray-400 hover:text-white hover:border-purple-400/60
                       transition-all duration-150 shadow-lg"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M1 1l12 12M13 1L1 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </button>

          {/* Hint */}
          <p className="absolute -bottom-8 left-0 right-0 text-center text-xs text-gray-600 select-none">
            Press <kbd className="px-1.5 py-0.5 rounded bg-gray-800 border border-gray-700 text-gray-500 font-mono text-[10px]">Esc</kbd> or click outside to close
          </p>
        </motion.div>
      </motion.div>
    </AnimatePresence>,
    document.body
  )
}
