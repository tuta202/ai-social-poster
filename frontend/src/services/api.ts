import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export const approvePost = async (
  jobId: number,
  postId: number,
  imageStyleNote?: string,
): Promise<import('../types').JobPost> => {
  const body: Record<string, string> = {}
  if (imageStyleNote) body.image_style_note = imageStyleNote
  const res = await api.post(`/jobs/${jobId}/posts/${postId}/approve`, body)
  return res.data
}

export const updatePostText = async (
  jobId: number,
  postId: number,
  text: string,
): Promise<import('../types').JobPost> => {
  const res = await api.put(`/jobs/${jobId}/posts/${postId}`, { content_text: text })
  return res.data
}

export const regenerateImage = async (
  jobId: number,
  postId: number,
  imageStyleNote?: string,
): Promise<import('../types').JobPost> => {
  const body: Record<string, string> = {}
  if (imageStyleNote) body.image_style_note = imageStyleNote
  const res = await api.post(`/jobs/${jobId}/posts/${postId}/regenerate-image`, body)
  return res.data
}

/**
 * SSE fetch helper — native fetch for streaming (axios buffers responses).
 */
export async function ssePost<T = unknown>(
  path: string,
  body: unknown,
  onEvent: (event: string, data: T) => void,
  token?: string,
): Promise<void> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error((err as { detail?: string }).detail || 'Request failed')
  }

  const reader = res.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let currentEvent = 'message'

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''

    for (const line of lines) {
      if (line.startsWith('event:')) {
        currentEvent = line.slice(6).trim()
      } else if (line.startsWith('data:')) {
        try {
          const data = JSON.parse(line.slice(5).trim())
          onEvent(currentEvent, data as T)
        } catch {
          // ignore malformed data lines
        }
      }
    }
  }
}
