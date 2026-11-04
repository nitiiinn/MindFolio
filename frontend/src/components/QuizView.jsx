import { useEffect, useMemo, useState } from 'react'
import GenerateShell from './GenerateShell.jsx'
import { QuizIcon, CheckIcon, XIcon } from './Icons.jsx'

// Options arrive as "A) text" — split into letter + text.
function parseOption(opt) {
  const m = opt.match(/^([A-D])\)\s*(.*)$/)
  return m ? { letter: m[1], text: m[2] } : { letter: opt[0], text: opt }
}

const clean = (s) => s.replace(/\*\*/g, '').trim()

export default function QuizView(props) {
  const questions = useMemo(() => props.data?.questions || [], [props.data])
  const [answers, setAnswers] = useState({})

  useEffect(() => setAnswers({}), [questions])

  const answered = Object.keys(answers).length
  const correct = questions.reduce((n, q, i) => n + (answers[i] === q.correct ? 1 : 0), 0)

  return (
    <GenerateShell
      {...props}
      title="MCQ Practice Quiz"
      subtitle="Test yourself with multiple-choice questions and instant feedback."
      Icon={QuizIcon}
      cta={{ label: 'Generate practice quiz', text: 'Create a multiple-choice quiz from your documents.' }}
      includes="15–25 questions · 4 options each · Explanations"
    >
      {questions.length === 0 ? (
        <p className="muted">The AI didn't return any questions. This can happen when the documents have little real content. Try regenerating.</p>
      ) : (
        <>
          <div className="quiz-score">
            <div>
              <strong>{correct}</strong> / {answered} correct
              <span className="muted"> · {questions.length - answered} remaining</span>
            </div>
            <div className="progress-bar"><div style={{ width: `${(answered / questions.length) * 100}%` }} /></div>
            {answered > 0 && <button className="btn btn-ghost btn-sm" onClick={() => setAnswers({})}>Restart</button>}
          </div>

          <ol className="quiz">
            {questions.map((q, i) => {
              const picked = answers[i]
              const done = picked !== undefined
              return (
                <li key={i} className="quiz-q">
                  <div className="quiz-num">Question {i + 1}</div>
                  <div className="quiz-text">{clean(q.question)}</div>
                  <div className="options">
                    {q.options.map((raw) => {
                      const { letter, text } = parseOption(raw)
                      const isCorrect = letter === q.correct
                      let cls = 'option'
                      if (done && isCorrect) cls += ' correct'
                      else if (done && picked === letter) cls += ' wrong'
                      return (
                        <button
                          key={letter}
                          className={cls}
                          disabled={done}
                          onClick={() => setAnswers((a) => ({ ...a, [i]: letter }))}
                        >
                          <span className="option-letter">
                            {done && isCorrect ? <CheckIcon size={14} /> : done && picked === letter ? <XIcon size={14} /> : letter}
                          </span>
                          <span>{clean(text)}</span>
                        </button>
                      )
                    })}
                  </div>
                  {done && q.explanation && (
                    <div className={`explanation ${picked === q.correct ? 'ok' : 'bad'}`}>
                      <strong>{picked === q.correct ? 'Correct.' : `Answer: ${q.correct}.`}</strong> {clean(q.explanation)}
                    </div>
                  )}
                </li>
              )
            })}
          </ol>
        </>
      )}
    </GenerateShell>
  )
}
