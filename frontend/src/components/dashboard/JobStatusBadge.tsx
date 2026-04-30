import type { JobStatus, PostStatus } from '../../types'

const STATUS_CONFIG: Record<JobStatus, { label: string; classes: string }> = {
  DRAFT:     { label: 'Draft',     classes: 'text-gray-400 bg-gray-500/10 border-gray-500/20' },
  SCHEDULED: { label: 'Scheduled', classes: 'text-blue-400 bg-blue-500/10 border-blue-500/20' },
  RUNNING:   { label: 'Running',   classes: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20' },
  DONE:      { label: 'Done',      classes: 'text-green-400 bg-green-500/10 border-green-500/20' },
  PAUSED:    { label: 'Paused',    classes: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20' },
}

interface Props {
  status: JobStatus
  size?: 'sm' | 'md'
}

export default function JobStatusBadge({ status, size = 'md' }: Props) {
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG.DRAFT
  const sizeClass = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-2.5 py-1'
  return (
    <span className={`inline-flex items-center rounded-full border font-medium ${sizeClass} ${config.classes}`}>
      {config.label}
    </span>
  )
}

const POST_STATUS_CONFIG: Record<PostStatus, { label: string; classes: string }> = {
  PENDING:  { label: 'Pending',  classes: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20' },
  APPROVED: { label: 'Approved', classes: 'text-blue-400 bg-blue-500/10 border-blue-500/20' },
  POSTED:   { label: 'Posted',   classes: 'text-green-400 bg-green-500/10 border-green-500/20' },
  FAILED:   { label: 'Failed',   classes: 'text-red-400 bg-red-500/10 border-red-500/20' },
}

interface PostStatusProps {
  status: PostStatus
  size?: 'sm' | 'md'
}

export function PostStatusBadge({ status, size = 'sm' }: PostStatusProps) {
  const config = POST_STATUS_CONFIG[status] ?? POST_STATUS_CONFIG.PENDING
  const sizeClass = size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-2.5 py-1'
  return (
    <span className={`inline-flex items-center rounded-full border font-medium ${sizeClass} ${config.classes}`}>
      {config.label}
    </span>
  )
}
