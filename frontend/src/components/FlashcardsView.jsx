import { useCallback, useEffect, useMemo, useState } from 'react'
import GenerateShell from './GenerateShell.jsx'
import { CardsIcon, ChevronLeft, ChevronRight, ShuffleIcon } from './Icons.jsx'

export default function FlashcardsView(props) {
  const sourceCards = useMemo(() => props.data?.cards || [], [props.data])
  const [cards, setCards] = useState(sourceCards)
  const [index, setIndex] = useState(0)
  const [flipped, setFlipped] = useState(false)

  useEffect(() => { setCards(sourceCards); setIndex(0); setFlipped(false) }, [sourceCards])

  const go = useCallback((delta) => {
    setFlipped(false)
    setIndex((i) => (i + delta + cards.length) % cards.length)
  }, [cards.length])

  const shuffle = () => {
    const next = [...cards]
    for (let i = next.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1))
      ;[next[i], next[j]] = [next[j], next[i]]
    }
    setCards(next)
    setIndex(0)
    setFlipped(false)
  }

  useEffect(() => {
    if (!cards.length) return
    const onKey = (e) => {
      if (e.target.closest('input, textarea')) return
      if (e.key === 'ArrowRight') go(1)
      else if (e.key === 'ArrowLeft') go(-1)
      else if (e.key === ' ') { e.preventDefault(); setFlipped((f) => !f) }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [cards.length, go])

  const card = cards[index]

  return (
    <GenerateShell
      {...props}
      title="Flashcards"
      subtitle="Flip-to-reveal question and answer cards for quick revision."
      Icon={CardsIcon}
      cta={{ label: 'Generate flashcards', text: 'Create revision flashcards from your documents.' }}
      includes="8–15 cards · Facts · Concepts · Relationships"
    >
      {!card ? (
        <p className="muted">The AI didn't return any flashcards. This can happen when the documents have little real content. Try regenerating.</p>
      ) : (
        <div className="flash">
          <button
            className={`flashcard ${flipped ? 'flipped' : ''}`}
            onClick={() => setFlipped((f) => !f)}
            aria-label={flipped ? 'Show question' : 'Show answer'}
          >
            <div className="flashcard-inner">
              <div className="face front">
                <span className="face-label">Question</span>
                <p>{card.question}</p>
                <span className="face-hint muted small">Click or press Space to reveal</span>
              </div>
              <div className="face back">
                <span className="face-label">Answer</span>
                <p>{card.answer}</p>
              </div>
            </div>
          </button>

          <div className="flash-controls">
            <button className="icon-btn lg" onClick={() => go(-1)} aria-label="Previous card"><ChevronLeft /></button>
            <span className="flash-count">{index + 1} / {cards.length}</span>
            <button className="icon-btn lg" onClick={() => go(1)} aria-label="Next card"><ChevronRight /></button>
            <button className="btn btn-ghost btn-sm" onClick={shuffle}><ShuffleIcon size={14} /> Shuffle</button>
          </div>

          <div className="flash-dots">
            {cards.map((_, i) => (
              <button
                key={i}
                className={`flash-dot ${i === index ? 'active' : ''}`}
                onClick={() => { setIndex(i); setFlipped(false) }}
                aria-label={`Card ${i + 1}`}
              />
            ))}
          </div>
        </div>
      )}
    </GenerateShell>
  )
}
