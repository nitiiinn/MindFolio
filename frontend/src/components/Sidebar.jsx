import { ChatIcon, NotesIcon, QuizIcon, CardsIcon, FileIcon, PlusIcon, TrashIcon, RefreshIcon, XIcon } from './Icons.jsx'

const NAV = [
  { key: 'chat', label: 'Chat', Icon: ChatIcon },
  { key: 'notes', label: 'Study Notes', Icon: NotesIcon },
  { key: 'quiz', label: 'MCQ Quiz', Icon: QuizIcon },
  { key: 'flashcards', label: 'Flashcards', Icon: CardsIcon },
]

export default function Sidebar({ session, tab, onTab, busy, generated, onAddDocs, onClearChat, onReset, onClose, canClear }) {
  const stats = session?.stats

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">M</div>
        <span className="brand-name">MindFolio</span>
        <button className="icon-btn sidebar-close" onClick={onClose} aria-label="Close menu"><XIcon /></button>
      </div>

      <nav className="nav">
        {NAV.map(({ key, label, Icon }) => (
          <button
            key={key}
            className={`nav-item ${tab === key ? 'active' : ''}`}
            onClick={() => onTab(key)}
            disabled={!session}
          >
            <Icon />
            <span>{label}</span>
            {busy[key] && <span className="dot-pulse" aria-label="Working" />}
            {!busy[key] && generated[key] && <span className="nav-ready" title="Ready" />}
          </button>
        ))}
      </nav>

      {stats && (
        <>
          <div className="section-label">Knowledge base</div>
          <div className="stats">
            <Stat value={stats.files.length} label="Docs" />
            <Stat value={stats.pages} label="Pages" />
            <Stat value={stats.chunks} label="Chunks" />
            <Stat value={stats.queries} label="Queries" />
          </div>

          <div className="section-label">Loaded files</div>
          <ul className="file-list">
            {stats.files.map((f) => (
              <li key={f} title={f}><FileIcon size={15} /><span>{f}</span></li>
            ))}
          </ul>
        </>
      )}

      <div className="sidebar-footer">
        {session && (
          <>
            <button className="btn btn-ghost" onClick={onAddDocs}><PlusIcon size={16} /> New documents</button>
            <div className="row">
              <button className="btn btn-ghost" onClick={onClearChat} disabled={!canClear}><RefreshIcon size={15} /> Clear chat</button>
              <button className="btn btn-ghost danger" onClick={onReset}><TrashIcon size={15} /> Reset</button>
            </div>
          </>
        )}
        {!session && <p className="muted small">Upload PDFs to unlock chat, notes, quizzes and flashcards.</p>}
      </div>
    </aside>
  )
}

function Stat({ value, label }) {
  return (
    <div className="stat">
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  )
}
