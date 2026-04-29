import { create } from 'zustand'
import type { Job } from '../types'

interface JobState {
  jobs: Job[]
  currentJob: Job | null
  setJobs: (jobs: Job[]) => void
  setCurrentJob: (job: Job | null) => void
}

export const useJobStore = create<JobState>((set) => ({
  jobs: [],
  currentJob: null,
  setJobs: (jobs) => set({ jobs }),
  setCurrentJob: (job) => set({ currentJob: job }),
}))
