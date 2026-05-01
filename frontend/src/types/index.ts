export type JobStatus = 'DRAFT' | 'SCHEDULED' | 'RUNNING' | 'DONE' | 'PAUSED'
export type PostStatus = 'PENDING' | 'APPROVED' | 'POSTED' | 'FAILED'

export interface User {
  id: number
  username: string
}

export interface Job {
  id: number
  title: string
  raw_input: string
  parsed_config: ParsedConfig | null
  status: JobStatus
  created_at: string
  updated_at: string | null
  posts?: JobPost[]
  style_profile?: Record<string, string> | null
  total_posts?: number
  posted_count?: number
  failed_count?: number
}

export interface JobPost {
  id: number
  job_id: number
  day_index: number
  post_order: number
  content_text: string | null
  original_content_text: string | null
  image_url: string | null
  image_prompt: string | null
  image_style_note: string | null
  scheduled_time: string
  status: PostStatus
  fb_post_id: string | null
  error_message: string | null
  posted_at: string | null
  approved_at: string | null
}

export interface RegenerateImageRequest {
  image_style_note?: string
}

export interface ApprovePostRequest {
  image_style_note?: string
}

export interface ParsedConfig {
  title: string
  duration_days: number
  items_per_day: number
  post_time: string
  content_type: string
  has_images: boolean
  image_description: string
  tags: string[]
  notes: string
}

export interface JobPreview {
  job_id: number
  config: ParsedConfig
  posts: JobPost[]
}

export interface FacebookPage {
  page_id: string
  page_name: string | null
  token_expires_at: string | null
}
