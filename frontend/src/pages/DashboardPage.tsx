import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import PageWrapper from '../components/layout/PageWrapper'
import TopNav from '../components/layout/TopNav'
import JobCard from '../components/dashboard/JobCard'
import JobDetailPanel from '../components/dashboard/JobDetailPanel'
import { useJobStore } from '../stores/jobStore'
import { api } from '../services/api'
import type { Job } from '../types'

export default function DashboardPage() {
  const { jobs, currentJob, isLoading, setJobs, setLoading, setCurrentJob, updateJob, removeJob } = useJobStore()
  const [error, setError] = useState('')

  const fetchJobs = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const res = await api.get('/jobs/')
      setJobs(res.data)
    } catch {
      setError('Failed to load jobs')
    } finally {
      setLoading(false)
    }
  }, [setJobs, setLoading])

  useEffect(() => {
    fetchJobs()
    const interval = setInterval(fetchJobs, 30_000)
    return () => clearInterval(interval)
  }, [fetchJobs])

  const handleView = async (job: Job) => {
    try {
      const res = await api.get(`/jobs/${job.id}`)
      setCurrentJob(res.data)
    } catch {
      setCurrentJob(job)
    }
  }

  const handlePause = async (id: number) => {
    const res = await api.post(`/jobs/${id}/pause`)
    updateJob(res.data)
  }

  const handleResume = async (id: number) => {
    const res = await api.post(`/jobs/${id}/resume`)
    updateJob(res.data)
  }

  const handleDelete = async (id: number) => {
    await api.delete(`/jobs/${id}`)
    removeJob(id)
  }

  const statusOrder: Record<string, number> = {
    RUNNING: 0, SCHEDULED: 1, PAUSED: 2, DRAFT: 3, DONE: 4,
  }
  const sortedJobs = [...jobs].sort(
    (a, b) => (statusOrder[a.status] ?? 5) - (statusOrder[b.status] ?? 5)
  )

  const runningCount   = jobs.filter(j => j.status === 'RUNNING').length
  const scheduledCount = jobs.filter(j => j.status === 'SCHEDULED').length

  return (
    <PageWrapper>
      <TopNav />

      <main className="max-w-4xl mx-auto px-6 py-10 space-y-8">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <motion.h1
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-3xl font-display font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent"
            >
              Dashboard
            </motion.h1>
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.1 }}
              className="text-gray-500 text-sm mt-1"
            >
              {runningCount > 0
                ? `${runningCount} campaign${runningCount > 1 ? 's' : ''} running`
                : scheduledCount > 0
                ? `${scheduledCount} campaign${scheduledCount > 1 ? 's' : ''} scheduled`
                : 'No active campaigns'}
            </motion.p>
          </div>
          <Link
            to="/command"
            className="text-sm px-4 py-2 rounded-xl bg-gradient-to-r from-purple-600 to-cyan-600
                       text-white font-display font-semibold hover:from-purple-500 hover:to-cyan-500
                       shadow-lg shadow-purple-500/20 transition-all duration-300 hover:scale-105"
          >
            + New Job
          </Link>
        </div>

        {/* Stats row */}
        {jobs.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.15 }}
            className="grid grid-cols-2 sm:grid-cols-4 gap-3"
          >
            {[
              { label: 'Total Jobs', value: jobs.length,                                  color: 'text-white' },
              { label: 'Running',    value: runningCount,                                 color: 'text-cyan-400' },
              { label: 'Scheduled',  value: scheduledCount,                               color: 'text-blue-400' },
              { label: 'Done',       value: jobs.filter(j => j.status === 'DONE').length, color: 'text-green-400' },
            ].map(stat => (
              <div key={stat.label} className="backdrop-blur-sm bg-white/[0.03] border border-purple-500/10 rounded-xl p-3">
                <p className="text-xs text-gray-600 mb-1">{stat.label}</p>
                <p className={`font-display font-bold text-2xl ${stat.color}`}>{stat.value}</p>
              </div>
            ))}
          </motion.div>
        )}

        {/* Job list */}
        {isLoading && jobs.length === 0 ? (
          <div className="flex justify-center py-16">
            <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <p className="text-red-400 text-sm">{error}</p>
            <button onClick={fetchJobs} className="text-xs text-gray-600 hover:text-gray-400 mt-2 transition-colors">
              Retry
            </button>
          </div>
        ) : sortedJobs.length === 0 ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-20 space-y-4"
          >
            <div className="w-16 h-16 mx-auto rounded-2xl bg-purple-500/10 border border-purple-500/20
                            flex items-center justify-center text-2xl">
              📋
            </div>
            <p className="text-gray-500 text-sm">No campaigns yet</p>
            <Link
              to="/command"
              className="inline-block text-sm px-4 py-2 rounded-xl border border-purple-500/30
                         text-purple-300 hover:bg-purple-500/10 transition-colors"
            >
              Create your first campaign →
            </Link>
          </motion.div>
        ) : (
          <div className="space-y-3">
            {sortedJobs.map((job, i) => (
              <JobCard
                key={job.id}
                job={job}
                index={i}
                onView={handleView}
                onPause={handlePause}
                onResume={handleResume}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </main>

      <JobDetailPanel
        job={currentJob}
        onClose={() => setCurrentJob(null)}
      />
    </PageWrapper>
  )
}
