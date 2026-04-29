export type JobStatus = 'DRAFT' | 'SCHEDULED' | 'RUNNING' | 'DONE' | 'PAUSED'
export type PostStatus = 'PENDING' | 'POSTED' | 'FAILED'

export interface User {
  id: number
  username: string
}

export interface Job {
  id: number
  title: string
  raw_input: string
  status: JobStatus
  created_at: string
  posts?: JobPost[]
}

export interface JobPost {
  id: number
  job_id: number
  day_index: number
  post_order: number
  content_text: string
  image_url: string | null
  image_prompt: string | null
  scheduled_time: string
  status: PostStatus
  fb_post_id: string | null
}

export interface ParsedConfig {
  title: string
  duration_days: number
  items_per_day: number
  post_time: string
  content_type: string
  has_images: boolean
  tags: string[]
  notes: string
}

export interface JobPreview {
  job_id: number
  config: ParsedConfig
  posts: JobPost[]
}
