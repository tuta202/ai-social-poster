import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import PageWrapper from '../components/layout/PageWrapper'
import TopNav from '../components/layout/TopNav'
import CommandInput from '../components/command/CommandInput'
import ProgressStepper from '../components/command/ProgressStepper'
import JobPreview from '../components/preview/JobPreview'
import { useAuthStore } from '../stores/authStore'
import { api, ssePost } from '../services/api'
import type { JobPost } from '../types'

interface PreviewState {
  jobId: number
  config: {
    title: string
    duration_days: number
    items_per_day: number
    post_time: string
    content_type: string
    has_images: boolean
    image_description: string
    tags: string[]
  }
  posts: JobPost[]
}

type ParseStep = 'idle' | 'parsing' | 'scheduling' | 'done' | 'error'

export default function CommandPage() {
  const navigate = useNavigate()
  const { token } = useAuthStore()

  // Parse state
  const [parseStep, setParseStep] = useState<ParseStep>('idle')
  const [parseError, setParseError] = useState('')
  const [preview, setPreview] = useState<PreviewState | null>(null)

  // Confirm state
  const [isConfirming, setIsConfirming] = useState(false)
  const [confirmStep, setConfirmStep] = useState('')
  const [confirmProgress, setConfirmProgress] = useState({ current: 0, total: 0 })

  // ── Parse handler ──────────────────────────────────────────────────────
  const handleParse = async (input: string) => {
    setParseStep('parsing')
    setParseError('')
    setPreview(null)

    try {
      await ssePost(
        '/jobs/parse',
        { raw_input: input },
        (event: string, data: Record<string, unknown>) => {
          if (event === 'step') {
            const step = data.step as string
            if (step === 'parsing') setParseStep('parsing')
            else if (step === 'scheduling') setParseStep('scheduling')
          } else if (event === 'done') {
            setPreview({
              jobId: data.job_id as number,
              config: data.config as PreviewState['config'],
              posts: data.posts as JobPost[],
            })
            setParseStep('done')
            setTimeout(() => {
              document.getElementById('job-preview')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
            }, 300)
          } else if (event === 'error') {
            setParseError((data.message as string) || 'Parse failed')
            setParseStep('error')
          }
        },
        token ?? undefined,
      )
    } catch (err) {
      setParseError(err instanceof Error ? err.message : 'Unknown error')
      setParseStep('error')
    }
  }

  // ── Confirm handler ────────────────────────────────────────────────────
  const handleConfirm = async () => {
    if (!preview) return
    setIsConfirming(true)
    setConfirmProgress({ current: 0, total: preview.posts.length })

    try {
      await ssePost(
        `/jobs/${preview.jobId}/confirm`,
        {},
        (event: string, data: Record<string, unknown>) => {
          if (event === 'step') {
            setConfirmStep((data.message as string) || '')
            if (typeof data.current === 'number') {
              setConfirmProgress({
                current: data.current as number,
                total: (data.total as number) || preview.posts.length,
              })
            }
          } else if (event === 'done') {
            navigate('/dashboard')
          } else if (event === 'error') {
            setParseError((data.message as string) || 'Confirm failed')
            setIsConfirming(false)
          }
        },
        token ?? undefined,
      )
    } catch (err) {
      setParseError(err instanceof Error ? err.message : 'Confirm failed')
      setIsConfirming(false)
    }
  }

  // ── Edit post handler ──────────────────────────────────────────────────
  const handleEditPost = async (postId: number, newText: string) => {
    if (!preview) return
    await api.put(`/jobs/${preview.jobId}/posts/${postId}`, { content_text: newText })
    setPreview(prev => prev ? {
      ...prev,
      posts: prev.posts.map(p => p.id === postId ? { ...p, content_text: newText } : p),
    } : null)
  }

  // ── Reset ──────────────────────────────────────────────────────────────
  const handleReset = () => {
    setParseStep('idle')
    setParseError('')
    setPreview(null)
    setIsConfirming(false)
  }

  const isParsing = parseStep === 'parsing' || parseStep === 'scheduling'

  return (
    <PageWrapper>
      <TopNav />
      <main className="max-w-3xl mx-auto px-6 py-10 space-y-8">

        {/* Header */}
        <div className="text-center space-y-2">
          <motion.h1
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-3xl font-display font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent"
          >
            Command Center
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="text-gray-500 text-sm"
          >
            Describe your campaign in natural language — AI handles the rest
          </motion.p>
        </div>

        {/* Input card */}
        <AnimatePresence>
          {parseStep !== 'done' && (
            <motion.div
              key="input-card"
              exit={{ opacity: 0, y: -10 }}
              className="backdrop-blur-md bg-white/5 border border-purple-500/20 rounded-2xl p-6 space-y-5"
            >
              <CommandInput
                onParse={handleParse}
                isLoading={isParsing}
                disabled={isConfirming}
              />

              {/* Progress stepper — shows when actively parsing */}
              <AnimatePresence>
                {parseStep !== 'idle' && (
                  <motion.div
                    key="stepper"
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="pt-2 border-t border-purple-500/10"
                  >
                    <ProgressStepper
                      currentStep={parseStep}
                      errorMessage={parseError}
                    />
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )}
        </AnimatePresence>

        {/* "Parse new campaign" button when preview is shown */}
        {parseStep === 'done' && !isConfirming && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-end">
            <button
              onClick={handleReset}
              className="text-sm text-gray-500 hover:text-gray-300 transition-colors flex items-center gap-1"
            >
              ← Parse new campaign
            </button>
          </motion.div>
        )}

        {/* Job Preview */}
        <AnimatePresence>
          {preview && (
            <motion.div
              key="preview"
              id="job-preview"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
            >
              <JobPreview
                jobId={preview.jobId}
                config={preview.config}
                posts={preview.posts}
                onConfirm={handleConfirm}
                isConfirming={isConfirming}
                confirmStep={confirmStep}
                confirmProgress={confirmProgress}
                onEditPost={handleEditPost}
              />
            </motion.div>
          )}
        </AnimatePresence>

      </main>
    </PageWrapper>
  )
}
