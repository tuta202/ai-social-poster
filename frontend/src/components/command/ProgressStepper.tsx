import { motion } from 'framer-motion'

export type Step = {
  key: string
  label: string
  description: string
}

const STEPS: Step[] = [
  { key: 'parsing',    label: 'Parse',    description: 'Analysing your command...' },
  { key: 'scheduling', label: 'Schedule', description: 'Building post schedule...' },
  { key: 'done',       label: 'Preview',  description: 'Ready to review!' },
]

interface Props {
  currentStep: string   // 'idle' | 'parsing' | 'scheduling' | 'done' | 'error'
  errorMessage?: string
}

export default function ProgressStepper({ currentStep, errorMessage }: Props) {
  const stepIndex = STEPS.findIndex(s => s.key === currentStep)
  const isDone = currentStep === 'done'
  const isError = currentStep === 'error'

  return (
    <div className="w-full">
      {/* Step indicators */}
      <div className="flex items-center justify-between mb-4">
        {STEPS.map((step, i) => {
          const isActive = i === stepIndex
          const isCompleted = stepIndex > i || isDone
          return (
            <div key={step.key} className="flex items-center flex-1">
              {/* Circle */}
              <div className="flex flex-col items-center gap-1">
                <motion.div
                  animate={{
                    scale: isActive ? [1, 1.1, 1] : 1,
                    transition: { repeat: isActive ? Infinity : 0, duration: 1.2 },
                  }}
                  className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold border-2 transition-all duration-500 ${
                    isCompleted
                      ? 'bg-gradient-to-br from-purple-600 to-cyan-500 border-transparent text-white'
                      : isActive
                      ? 'border-purple-500 bg-purple-500/20 text-purple-300'
                      : 'border-gray-700 bg-gray-800/50 text-gray-600'
                  }`}
                >
                  {isCompleted ? '✓' : i + 1}
                </motion.div>
                <span className={`text-xs font-medium ${
                  isCompleted || isActive ? 'text-gray-300' : 'text-gray-600'
                }`}>
                  {step.label}
                </span>
              </div>

              {/* Connector line */}
              {i < STEPS.length - 1 && (
                <div className="flex-1 h-0.5 mx-2 bg-gray-800 overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-purple-600 to-cyan-500"
                    initial={{ width: '0%' }}
                    animate={{ width: isCompleted ? '100%' : '0%' }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Status message */}
      <div className="text-center min-h-6">
        {isError ? (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-red-400 text-sm"
          >
            {errorMessage || 'An error occurred'}
          </motion.p>
        ) : currentStep !== 'idle' && !isDone ? (
          <motion.p
            key={currentStep}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-cyan-400 text-sm flex items-center justify-center gap-2"
          >
            <span className="w-3 h-3 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
            {STEPS.find(s => s.key === currentStep)?.description}
          </motion.p>
        ) : isDone ? (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-green-400 text-sm"
          >
            Campaign ready — review below
          </motion.p>
        ) : null}
      </div>
    </div>
  )
}
