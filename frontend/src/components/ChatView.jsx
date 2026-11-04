import { useEffect, useRef, useState } from 'react'
import Markdown from './Markdown.jsx'
import CopyButton from './CopyButton.jsx'
import { SendIcon, GlobeIcon, FileIcon } from './Icons.jsx'

const SUGGESTIONS = [
  'Summarise the main ideas in a few bullet points',
  'What are the key terms I should know?',
  'Explain the hardest concept simply',
  'What conclusions does the document reach?',
]

export default function ChatView({ messages, loading, onSend, files }) {
  const [input, setInput] = useState('')
  const endRef = useRef(null)
  const taRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, loading])

  useEffect(() => {
    const ta = taRef.current
    if (!ta) return
    ta.style.height = 'auto'
    ta.style.height = `${Math.min(ta.scrollHeight, 200)}px`
  }, [input])

  const submit = (text = input) => {
    const q = text.trim()
    if (!q || loading) return
    onSend(q)
    setInput('')
  }

  return (
    <div className="chat">
      <div className="chat-scroll">
        <div className="chat-inner">
          {messages.length === 0 && (
            <div className="chat-empty">
              <h2>What would you like to know?</h2>
              <p className="muted">
                Ask anything about {files.length === 1 ? <strong>{files[0]}</strong> : `your ${files.length} documents`}.
              </p>
              <div className="suggestions">
                {SUGGESTIONS.map((s) => (
                  <button key={s} className="suggestion" onClick={() => submit(s)}>{s}</button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (m.role === 'user' ? (
            <div key={i} className="msg msg-user">
              <div className="bubble">{m.content}</div>
              <div className="msg-actions"><CopyButton text={m.content} /></div>
            </div>
          ) : (
            <div key={i} className={`msg msg-assistant ${m.error ? 'msg-error' : ''}`}>
              <Markdown>{m.content}</Markdown>
              <div className="msg-meta">
                {m.sources?.map((s) => (
                  <span key={s} className="badge">
                    {m.is_internet_search ? <GlobeIcon size={12} /> : <FileIcon size={12} />}
                    {s}
                  </span>
                ))}
                {!m.error && <CopyButton text={m.content} />}
              </div>
            </div>
          )))}

          {loading && (
            <div className="msg msg-assistant">
              <div className="typing"><span /><span /><span /></div>
              <div className="muted small">Searching across your documents…</div>
            </div>
          )}
          <div ref={endRef} />
        </div>
      </div>

      <form className="composer" onSubmit={(e) => { e.preventDefault(); submit() }}>
        <div className="composer-box">
          <textarea
            ref={taRef}
            rows={1}
            value={input}
            placeholder="Ask a question about your documents…"
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit() }
            }}
          />
          <button type="submit" className="send-btn" disabled={!input.trim() || loading} aria-label="Send">
            <SendIcon size={18} />
          </button>
        </div>
        <div className="composer-hint muted">Enter to send · Shift+Enter for a new line</div>
      </form>
    </div>
  )
}
