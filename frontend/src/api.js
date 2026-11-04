const BASE = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, options)
  if (!res.ok) {
    let detail = `Request failed (${res.status})`
    try {
      const body = await res.json()
      if (body.detail) detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    } catch { /* non-JSON error */ }
    const err = new Error(detail)
    err.status = res.status
    throw err
  }
  return res.json()
}

const json = (body) => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})

export function uploadDocuments(files) {
  const form = new FormData()
  files.forEach((f) => form.append('files', f))
  return request('/api/upload', { method: 'POST', body: form })
}

export const sendMessage = (sessionId, query) =>
  request('/api/chat', json({ session_id: sessionId, query }))

export const generate = (sessionId, kind) =>
  request(`/api/generate/${kind}`, json({ session_id: sessionId }))

export const clearChat = (sessionId) =>
  request(`/api/session/${sessionId}/clear-chat`, { method: 'POST' })

export const deleteSession = (sessionId) =>
  request(`/api/session/${sessionId}`, { method: 'DELETE' }).catch(() => {})

export const downloadUrl = (sessionId, kind) => `${BASE}/api/download/${sessionId}/${kind}`
