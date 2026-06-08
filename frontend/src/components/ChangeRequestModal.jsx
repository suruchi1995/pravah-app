import { useState } from 'react'
import { api } from '../api'
import { X, Send, Lock } from 'lucide-react'

// Reusable modal to submit an approval-gated change (override or field edit).
// Props:
//   open, onClose
//   title
//   change: { change_type, target, payload, old_value, new_value }  — the request to submit
//   canEdit: whether the current user may submit (planner/admin)
export function ChangeRequestModal({ open, onClose, title, change, canEdit }) {
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState(null)
  const token = localStorage.getItem('pravah_token')

  if (!open) return null

  async function submit() {
    setBusy(true); setResult(null)
    try {
      const r = await api.submitChange(token, change)
      if (r.ok) setResult({ ok: true, text: `Submitted for approval (request #${r.id}). It will apply and re-plan once an approver signs off.` })
      else setResult({ ok: false, text: r.detail || 'Could not submit.' })
    } catch { setResult({ ok: false, text: 'Could not submit. Are you signed in as a planner?' }) }
    setBusy(false)
  }

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="card p-6 max-w-md w-full" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-display text-xl">{title}</h3>
          <button onClick={onClose} className="text-slate2 hover:text-ink"><X size={20} /></button>
        </div>

        {!token ? (
          <div className="text-center py-4">
            <Lock className="mx-auto text-slate2 mb-2" size={28} />
            <p className="text-sm text-slate2">Sign in as a planner to propose changes.</p>
          </div>
        ) : !canEdit ? (
          <p className="text-sm text-slate2 py-4">Only planners and admins can propose changes. Your role is view-only here.</p>
        ) : result ? (
          <div className={`text-sm rounded-lg p-4 ${result.ok ? 'bg-sage/10 text-ink' : 'bg-rust/10 text-rust'}`}>{result.text}</div>
        ) : (
          <>
            <div className="bg-mist/50 rounded-lg p-3 text-sm mb-4">
              <div className="text-slate2">{change.target}</div>
              <div className="mt-1">{change.old_value} <span className="text-slate2">→</span> <span className="font-medium text-ink">{change.new_value}</span></div>
            </div>
            <p className="text-xs text-slate2 mb-4">This change is approval-gated. It won't affect the plan until an approver, manager, or admin signs off — then the plan re-runs automatically.</p>
            <button onClick={submit} disabled={busy} className="w-full flex items-center justify-center gap-2 text-sm py-2.5 rounded-lg bg-brand text-white hover:bg-branddk disabled:opacity-50">
              <Send size={15} /> {busy ? 'Submitting…' : 'Submit for approval'}
            </button>
          </>
        )}
        {result && <button onClick={onClose} className="mt-3 w-full text-sm py-2 rounded-lg border border-[#d6deea] hover:bg-mist">Close</button>}
      </div>
    </div>
  )
}

// helper: current user's roles from localStorage
export function currentRoles() {
  try { return JSON.parse(localStorage.getItem('pravah_user') || '{}').roles || [] } catch { return [] }
}
export function canEditData() {
  const r = currentRoles()
  return r.includes('planner') || r.includes('admin')
}
