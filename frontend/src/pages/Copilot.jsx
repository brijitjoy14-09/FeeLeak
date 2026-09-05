import { useRef, useState } from 'react'
import './Copilot.css'
import { copilotQuery } from '../services/api'

const SUGGESTIONS = [
  'How much potential leakage was detected?',
  'Which exceptions should I investigate first?',
  'Which category has the biggest financial impact?',
  'What is the current resolution rate?',
]

/**
 * Finance Controller Copilot — a controlled information interface. Answers come
 * from registered read-only backend tools; the Copilot never changes records,
 * resolves exceptions, or invents numbers.
 */
function Copilot() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const inputRef = useRef(null)

  async function ask(question) {
    const text = question.trim()
    if (!text || sending) return
    setMessages((prev) => [...prev, { role: 'user', text }])
    setInput('')
    setSending(true)
    try {
      const result = await copilotQuery(text)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: result.answer,
          intent: result.intent,
          tools: result.tools_used,
        },
      ])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', text: err.message || 'Something went wrong.', error: true },
      ])
    } finally {
      setSending(false)
      inputRef.current?.focus()
    }
  }

  return (
    <div className="copilot">
      <header className="page-header">
        <p className="page-eyebrow">AI Finance Controller</p>
        <h1 className="page-title">Finance Copilot</h1>
        <p className="page-lead">
          Ask about exceptions, leakage, financial impact, risk priorities, and
          resolution performance. Every figure comes from the deterministic
          backend — the Copilot cannot change records or resolve exceptions.
        </p>
      </header>

      <section className="panel copilot-panel">
        <div className="copilot-thread" aria-live="polite">
          {messages.length === 0 && (
            <div className="copilot-welcome">
              <p>Ask a question to get started, or try one of these:</p>
              <div className="copilot-suggestions">
                {SUGGESTIONS.map((s) => (
                  <button key={s} type="button" className="chip" onClick={() => ask(s)}>
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`copilot-msg copilot-${m.role}`}>
              <div className={`copilot-bubble ${m.error ? 'is-error' : ''}`}>
                {m.text.split('\n').map((line, j) => (
                  <p key={j}>{line}</p>
                ))}
                {m.role === 'assistant' && m.intent && (
                  <p className="copilot-meta">
                    intent: {m.intent} · tools: {(m.tools || []).join(', ') || '—'}
                  </p>
                )}
              </div>
            </div>
          ))}
          {sending && (
            <div className="copilot-msg copilot-assistant">
              <div className="copilot-bubble">
                <p className="copilot-thinking">Consulting backend tools…</p>
              </div>
            </div>
          )}
        </div>

        <form
          className="copilot-input"
          onSubmit={(e) => {
            e.preventDefault()
            ask(input)
          }}
        >
          <label htmlFor="copilot-q" className="sr-only">Ask the Finance Copilot</label>
          <input
            id="copilot-q"
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about leakage, risk, exceptions…"
            autoComplete="off"
          />
          <button type="submit" className="btn btn-primary" disabled={sending || !input.trim()}>
            {sending ? 'Asking…' : 'Ask'}
          </button>
        </form>
      </section>
    </div>
  )
}

export default Copilot
