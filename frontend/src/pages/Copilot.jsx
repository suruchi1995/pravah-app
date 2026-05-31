import { useState, useRef, useEffect } from 'react'
import { api } from '../api'
import { PageHeader } from '../components/ui'
import { Send, Sparkles, User } from 'lucide-react'

export default function Copilot() {
  const [messages, setMessages] = useState([
    { role: 'assistant', text: "Ask me about your plan — stockouts, revenue at risk, capacity, or any SKU. I answer only from the live planning results." },
  ])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [suggested, setSuggested] = useState([
    'Why am I stocking out?', 'What is my revenue at risk?',
    'Where is my capacity bottleneck?', 'Why is FG006 short?',
  ])
  const endRef = useRef(null)
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  async function send(q) {
    const question = (q ?? input).trim()
    if (!question || busy) return
    setMessages(m => [...m, { role: 'user', text: question }])
    setInput(''); setBusy(true)
    try {
      const r = await api.copilot(question)
      setMessages(m => [...m, { role: 'assistant', text: r.answer, llm: r.used_llm }])
      if (r.suggested) setSuggested(r.suggested)
    } catch (e) {
      setMessages(m => [...m, { role: 'assistant', text: 'Sorry — I could not reach the planning data just now.' }])
    }
    setBusy(false)
  }

  return (
    <>
      <PageHeader title="AI Copilot" subtitle="Grounded in your live planning outputs — it reads the engines, it doesn't guess." />
      <div className="p-8 max-w-4xl">
        <div className="card flex flex-col" style={{ height: '64vh' }}>
          <div className="flex-1 overflow-auto p-6 space-y-4">
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-ink text-white' : 'bg-brand/12 text-brand'}`}>
                  {msg.role === 'user' ? <User size={16} /> : <Sparkles size={16} />}
                </div>
                <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed max-w-[78%] ${msg.role === 'user' ? 'bg-ink text-white' : 'bg-mist text-ink'}`}>
                  {msg.text}
                  {msg.role === 'assistant' && msg.llm === false && (
                    <div className="text-[10px] text-slate2 mt-1.5 uppercase tracking-wide">deterministic · grounded in plan data</div>
                  )}
                </div>
              </div>
            ))}
            {busy && <div className="text-sm text-slate2 pl-11">Thinking…</div>}
            <div ref={endRef} />
          </div>

          <div className="border-t border-[#e7ecf2] p-4">
            <div className="flex flex-wrap gap-2 mb-3">
              {suggested.map((s, i) => (
                <button key={i} onClick={() => send(s)} disabled={busy}
                  className="text-xs px-3 py-1.5 rounded-full border border-[#d6deea] text-slate2 hover:bg-brand/5 hover:text-brand disabled:opacity-50">
                  {s}
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <input value={input} onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && send()}
                placeholder="Ask about your plan…"
                className="flex-1 border border-[#d6deea] rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-brand" />
              <button onClick={() => send()} disabled={busy}
                className="px-4 py-2.5 rounded-xl bg-brand text-white hover:bg-branddk disabled:opacity-50 flex items-center gap-2">
                <Send size={16} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
