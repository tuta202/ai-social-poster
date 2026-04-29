import { create } from 'zustand'
import type { Job } from '../types'

interface JobState {
  jobs: Job[]
  currentJob: Job | null
  isLoading: boolean
  setJobs: (jobs: Job[]) => void
  setCurrentJob: (job: Job | null) => void
  setLoading: (v: boolean) => void
  updateJob: (updated: Job) => void
  removeJob: (id: number) => void
}

export const useJobStore = create<JobState>((set) => ({
  jobs: [],
  currentJob: null,
  isLoading: false,
  setJobs: (jobs) => set({ jobs }),
  setCurrentJob: (job) => set({ currentJob: job }),
  setLoading: (v) => set({ isLoading: v }),
  updateJob: (updated) => set((state) => ({
    jobs: state.jobs.map(j => j.id === updated.id ? updated : j),
    currentJob: state.currentJob?.id === updated.id ? updated : state.currentJob,
  })),
  removeJob: (id) => set((state) => ({
    jobs: state.jobs.filter(j => j.id !== id),
    currentJob: state.currentJob?.id === id ? null : state.currentJob,
  })),
}))
