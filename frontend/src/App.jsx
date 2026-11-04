import { useCallback, useState } from 'react'
import * as api from './api.js'
import Sidebar from './components/Sidebar.jsx'
import UploadView from './components/UploadView.jsx'
import ChatView from './components/ChatView.jsx'
import NotesView from './components/NotesView.jsx'
import QuizView from './components/QuizView.jsx'
import FlashcardsView from './components/FlashcardsView.jsx'
import { MenuIcon, XIcon } from './components/Icons.jsx'

const emptyGenerated = { notes: null, quiz: null, flashcards: null }

export default function App() {
  const [session, setSession] = useState(null) // { id, stats }
  const [tab, setTab] = useState('chat')
  const [messages, setMessages] = useState([])
  const [generated, setGenerated] = useState(emptyGenerated)
  const [busy, setBusy] = useState({}) // { chat: true, notes: true, ... }
  const [error, setError] = useState(null)
  const [showUpload, setShowUpload] = useState(false)
  const [navOpen, setNavOpen] = useState(false)

  const resetAll = useCallback(() => {
    if (session) api.deleteSession(session.id)
    setSession(null)
    setMessages([])
    setGenerated(emptyGenerated)
    setTab('chat')
    setShowUpload(false)
  }, [session])

  const handleError = useCallback((err) => {
    if (err.status === 404 && /session/i.test(err.message)) {
      setSession(null)
      setMessages([])
      setGenerated(emptyGenerated)
    }
    setError(err.message || 'Something went wrong.')
  }, [])

  const onUpload = async (files) => {
    setBusy((b) => ({ ...b, upload: true }))
    setError(null)
    try {
      const res = await api.uploadDocuments(files)
      if (session) api.deleteSession(session.id)
      setSession({ id: res.session_id, stats: res.stats })
      setMessages([])
      setGenerated(emptyGenerated)
      setTab('chat')
      setShowUpload(false)
    } catch (err) {
      handleError(err)
    } finally {
      setBusy((b) => ({ ...b, upload: false }))
    }
  }

  const onSend = async (query) => {
    setMessages((m) => [...m, { role: 'user', content: query }])
    setBusy((b) => ({ ...b, chat: true }))
    try {
      const res = await api.sendMessage(session.id, query)
      setMessages((m) => [...m, res.message])
      setSession((s) => ({ ...s, stats: res.stats }))
    } catch (err) {
      setMessages((m) => [...m, { role: 'assistant', content: err.message, error: true }])
      // The error is already shown inline; only escalate an expired session.
      if (err.status === 404) handleError(err)
    } finally {
      setBusy((b) => ({ ...b, chat: false }))
    }
  }

  const onClearChat = async () => {
    setMessages([])
    try {
      const res = await api.clearChat(session.id)
      setSession((s) => ({ ...s, stats: res.stats }))
    } catch (err) {
      handleError(err)
    }
  }

  const onGenerate = async (kind) => {
    setBusy((b) => ({ ...b, [kind]: true }))
    setError(null)
    try {
      const res = await api.generate(session.id, kind)
      setGenerated((g) => ({ ...g, [kind]: res.data }))
    } catch (err) {
      handleError(err)
    } finally {
      setBusy((b) => ({ ...b, [kind]: false }))
    }
  }

  const selectTab = (t) => {
    setTab(t)
    setShowUpload(false)
    setNavOpen(false)
  }

  const viewProps = (kind) => ({
    data: generated[kind],
    loading: !!busy[kind],
    onGenerate: () => onGenerate(kind),
    downloadUrl: session ? api.downloadUrl(session.id, kind) : null,
  })

  let content
  if (!session || showUpload) {
    content = (
      <UploadView
        loading={!!busy.upload}
        onUpload={onUpload}
        replacing={!!session}
        onCancel={session ? () => setShowUpload(false) : null}
      />
    )
  } else if (tab === 'chat') {
    content = <ChatView messages={messages} loading={!!busy.chat} onSend={onSend} files={session.stats.files} />
  } else if (tab === 'notes') {
    content = <NotesView {...viewProps('notes')} />
  } else if (tab === 'quiz') {
    content = <QuizView {...viewProps('quiz')} />
  } else {
    content = <FlashcardsView {...viewProps('flashcards')} />
  }

  return (
    <div className={`app ${navOpen ? 'nav-open' : ''}`}>
      <header className="topbar">
        <button className="icon-btn" onClick={() => setNavOpen(true)} aria-label="Open menu"><MenuIcon /></button>
        <span className="brand-name">MindFolio</span>
      </header>

      <Sidebar
        session={session}
        tab={showUpload ? null : tab}
        onTab={selectTab}
        busy={busy}
        generated={generated}
        onAddDocs={() => { setShowUpload(true); setNavOpen(false) }}
        onClearChat={onClearChat}
        onReset={resetAll}
        onClose={() => setNavOpen(false)}
        canClear={messages.length > 0}
      />
      <div className="scrim" onClick={() => setNavOpen(false)} />

      <main className="main">
        {error && (
          <div className="toast" role="alert">
            <span>{error}</span>
            <button className="icon-btn" onClick={() => setError(null)} aria-label="Dismiss"><XIcon size={15} /></button>
          </div>
        )}
        {content}
      </main>
    </div>
  )
}
