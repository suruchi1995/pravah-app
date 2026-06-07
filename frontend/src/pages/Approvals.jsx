import { useState } from 'react'
import { api } from '../api'
import { useAsync, PageHeader, Loading, ErrorBox } from '../components/ui'
import { CheckCircle2, XCircle, Clock } from 'lucide-react'

const STATUS_ICON = { submitted: <Clock size={16} className="text-amber2" />, approved: <CheckCircle2 size={16} className="text-sage" />, rejected: <XCircle size={16} className="text-rust" /> }
const STATUS_COLOR = { submitted: 'bg-amber2/10 text-amber2', approved: 'bg-sage/10 text-sage', rejected: 'bg-rust/10 text-rust' }

export default function Approvals() {
  const token = localStorage.getItem('pravah_token')
  const user = JSON.parse(localStorage.getItem('pravah_user') || '{}')
  const H = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
  const [note, setNote] = useState({})
  const [busy, setBusy] = useState(null)
  const [refresh, setRefresh] = useState(0)
  const { loading, data: crs, error } = useAsync(() =>
    fetch('/api/change-requests', { headers: H }).then(r => r.json()), [refresh])

  async function action(id, act) {
    setBusy(id + act)
    await fetch(`/api/change-requests/${id}/${act}`, { method: 'POST', headers: H, body: JSON.stringify({ note: note[id] || '' }) })
    setBusy(null); setRefresh(r => r + 1)
  }

  const canApprove = user.roles?.some(r => ['approver','management','admin'].includes(r))

  if (loading) return <><PageHeader title="Approval Inbox" /><Loading /></>
  if (error) return <ErrorBox msg={error} />

  const submitted = (crs || []).filter(c => c.status === 'submitted')
  const history = (crs || []).filter(c => c.status !== 'submitted')

  return (
    <>
      <PageHeader title="Approval Inbox" subtitle="Pending parameter and demand override changes that need review before going live." />
      <div className="p-8 space-y-6">
        {!canApprove && <div className="card p-4 text-sm text-slate2">You have viewer or planner access. Only approvers, management, and admins can approve or reject changes.</div>}
        <div className="card p-5">
          <h3 className="font-display text-xl mb-4">Pending ({submitted.length})</h3>
          {submitted.length === 0 && <p className="text-sm text-slate2">No pending changes — all clear.</p>}
          <div className="space-y-4">
            {submitted.map(cr => (
              <div key={cr.id} className="border border-[#e7ecf2] rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  {STATUS_ICON[cr.status]}
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLOR[cr.status]}`}>{cr.status}</span>
                  <span className="text-xs text-slate2">#{cr.id} · {cr.change_type} · by {cr.requested_by}</span>
                </div>
                <div className="text-sm font-medium">{cr.target}</div>
                <div className="text-sm text-slate2 mt-1">{cr.old_value} → <span className="text-ink font-medium">{cr.new_value}</span></div>
                {canApprove && (
                  <div className="mt-3 flex items-center gap-2">
                    <input value={note[cr.id] || ''} onChange={e => setNote(n => ({ ...n, [cr.id]: e.target.value }))}
                      placeholder="Review note (optional)" className="flex-1 text-sm border border-[#d6deea] rounded-lg px-3 py-1.5 focus:outline-none focus:border-brand" />
                    <button onClick={() => action(cr.id, 'approve')} disabled={!!busy} className="text-sm px-3 py-1.5 rounded-lg bg-sage text-white hover:opacity-90 disabled:opacity-50">Approve</button>
                    <button onClick={() => action(cr.id, 'reject')} disabled={!!busy} className="text-sm px-3 py-1.5 rounded-lg bg-rust text-white hover:opacity-90 disabled:opacity-50">Reject</button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
        <div className="card p-5">
          <h3 className="font-display text-xl mb-4">History</h3>
          {history.length === 0 && <p className="text-sm text-slate2">No history yet.</p>}
          <div className="space-y-2">
            {history.map(cr => (
              <div key={cr.id} className="flex items-center gap-3 text-sm py-2 border-b border-[#eef2f6] last:border-0">
                {STATUS_ICON[cr.status]}
                <span className="font-medium">{cr.target}</span>
                <span className="text-slate2">{cr.old_value} → {cr.new_value}</span>
                <span className={`ml-auto text-xs px-2 py-0.5 rounded-full ${STATUS_COLOR[cr.status]}`}>{cr.status}</span>
                {cr.reviewed_by && <span className="text-xs text-slate2">by {cr.reviewed_by}</span>}
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  )
}
