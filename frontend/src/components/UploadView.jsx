import { useEffect, useRef, useState } from 'react'
import { UploadIcon, FileIcon, XIcon, ChatIcon, NotesIcon, QuizIcon, CardsIcon } from './Icons.jsx'

const STEPS = ['Reading PDFs', 'Splitting into chunks', 'Embedding text', 'Building vector store', 'Setting up retriever']

function formatSize(bytes) {
  const kb = bytes / 1024
  return kb > 1024 ? `${(kb / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(kb))} KB`
}

export default function UploadView({ loading, onUpload, replacing, onCancel }) {
  const [files, setFiles] = useState([])
  const [dragging, setDragging] = useState(false)
  const [step, setStep] = useState(0)
  const inputRef = useRef(null)

  // The API processes in one call, so step through the stages on a timer for feedback.
  useEffect(() => {
    if (!loading) { setStep(0); return }
    const id = setInterval(() => setStep((s) => Math.min(s + 1, STEPS.length - 1)), 2200)
    return () => clearInterval(id)
  }, [loading])

  const addFiles = (list) => {
    const pdfs = Array.from(list).filter((f) => f.type === 'application/pdf' || f.name.toLowerCase().endsWith('.pdf'))
    setFiles((prev) => {
      const names = new Set(prev.map((f) => f.name))
      return [...prev, ...pdfs.filter((f) => !names.has(f.name))]
    })
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    if (!loading) addFiles(e.dataTransfer.files)
  }

  return (
    <div className="upload-view">
      <div className="hero">
        <h1>{replacing ? 'Load new documents' : 'Learn from any PDF'}</h1>
        <p>Upload one or more PDFs, then chat with them or turn them into notes, quizzes and flashcards.</p>
      </div>

      <div
        className={`dropzone ${dragging ? 'dragging' : ''} ${loading ? 'disabled' : ''}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => !loading && inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          multiple
          hidden
          onChange={(e) => { addFiles(e.target.files); e.target.value = '' }}
        />
        <div className="dropzone-icon"><UploadIcon size={26} /></div>
        <div className="dropzone-title">Drop PDFs here or <span className="link">browse</span></div>
        <div className="muted small">PDF only · multiple files supported</div>
      </div>

      {files.length > 0 && (
        <ul className="chips">
          {files.map((f) => (
            <li key={f.name} className="chip">
              <FileIcon size={14} />
              <span className="chip-name">{f.name}</span>
              <span className="muted">{formatSize(f.size)}</span>
              {!loading && (
                <button className="chip-x" onClick={() => setFiles(files.filter((x) => x !== f))} aria-label={`Remove ${f.name}`}>
                  <XIcon size={12} />
                </button>
              )}
            </li>
          ))}
        </ul>
      )}

      {loading ? (
        <div className="progress-card">
          <div className="progress-bar"><div style={{ width: `${((step + 1) / (STEPS.length + 1)) * 100}%` }} /></div>
          <div className="progress-text"><span className="spinner" />{STEPS[step]}…</div>
        </div>
      ) : (
        <div className="upload-actions">
          {onCancel && <button className="btn btn-ghost" onClick={onCancel}>Cancel</button>}
          <button className="btn btn-primary" disabled={!files.length} onClick={() => onUpload(files)}>
            Process {files.length > 0 ? `${files.length} document${files.length > 1 ? 's' : ''}` : 'documents'}
          </button>
        </div>
      )}

      {!replacing && (
        <div className="features">
          <Feature Icon={ChatIcon} title="Chat" text="Ask questions, get answers grounded in your files and fact-checked." />
          <Feature Icon={NotesIcon} title="Notes" text="Key concepts, definitions and summaries, organised for you." />
          <Feature Icon={QuizIcon} title="Quiz" text="Multiple-choice practice with instant feedback." />
          <Feature Icon={CardsIcon} title="Flashcards" text="Flip-to-reveal cards for quick revision." />
        </div>
      )}
    </div>
  )
}

function Feature({ Icon, title, text }) {
  return (
    <div className="feature">
      <Icon size={18} />
      <div>
        <div className="feature-title">{title}</div>
        <div className="muted small">{text}</div>
      </div>
    </div>
  )
}
