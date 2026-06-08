import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { PageHeader, Loading } from '../components/ui'
import { User, Shield, KeyRound, FileEdit, CheckCircle2, XCircle, Clock, Lock } from 'lucide-react'

const STATUS_ICON = { submitted: <Clock size={15} className="text-amber2" />, approved: <CheckCircle2 size={15} className="text-sage" />, rejected: <XCircle size={15} className="text-rust" /> }
const STATUS_COLOR = { submitted: 'bg-amber2/10 text-amber2', approved: 'bg-sage/10 text-sage', rejected: 'bg-rust/10 text-rust' }

export default function Profile() {
  const navigate = useNavigate()
  const token = localStorage.getItem('pravah_token')
  let me = {}
  try { me = JSON.parse(localStorage.getItem('pravah_user') || '{}') } catch {}

  const [crs, setCrs] = useState([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('mine')
  // change password
  const [pw, setPw] = useState({ current: '', next: '' })
  const [pwMsg, setPwMsg] = useState(null)
  const [pwBusy, setPwBusy] = useState(false)

  useEffect(() => {
    if (!token) { setLoading(false); return }
    let cancelled = false
    fetch('/api/change-requests', { headers: { Authorization: 'Bearer ' + token } })
      .then(r => r.ok ? r.json() : [])
      .then(d => { if (!cancelled) setCrs(Array.isArray(d) ? d : []) })
      .catch(() => { if (!cancelled) setCrs([]) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [token])

  async function changePassword() {
    if (pw.next.length < 6) { setPwMsg({ ok: false, text: 'New password must be at least 6 characters.' }); return }
    setPwBusy(true); setPwMsg(null)
    try {
      const r = await api.changePassword(token, pw.current, pw.next)
      if (r.ok) { setPwMsg({ ok: true, text: 'Password changed.' }); setPw({ current: '', next: '' }) }
      else setPwMsg({ ok: false, text: r.detail || 'Could not change password.' })
    } catch { setPwMsg({ ok: false, text: 'Could not change password.' }) }
    setPwBusy(false)
  }

  if (!token) {
    return (
      <>
        <PageHeader title="My Profile" />
        <div className="p-8">
          <div className="card p-8 text-center max-w-md mx-auto">
            <Lock className="mx-auto text-slate2 mb-3" size={32} />
            <h3 className="font-display text-xl mb-2">Sign in required</h3>
            <p className="text-sm text-slate2 mb-4">Sign in to view your profile, changes, and approvals.</p>
            <button onClick={() => navigate('/login')} className="text-sm px-4 py-2 rounded-lg bg-brand text-white hover:bg-branddk">Go to sign in</button>
          </div>
        </div>
      </>
    )
  }

  const mine = crs.filter(c => c.requested_by === me.email)
  const myApprovals = crs.filter(c => c.reviewed_by === me.email)
  const list = tab === 'mine' ? mine : myApprovals

  return (
    <>
      <PageHeader title="My Profile" subtitle="Your account, roles, change history, and approvals." />
      <div className="p-8 space-y-6 max-w-4xl">
        {/* Identity card */}
        <div className="card p-6 flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-brand/10 flex items-center justify-center"><User size={26} className="text-brand" /></div>
          <div className="flex-1">
            <div className="font-display text-2xl text-ink">{me.name || me.email}</div>
            <div className="text-sm text-slate2">{me.email}</div>
          </div>
          <div className="text-right">
            <div className="text-xs uppercase tracking-wide text-slate2 mb-1 flex items-center gap-1 justify-end"><Shield size={13} /> Roles</div>
            <div className="flex gap-1 flex-wrap justify-end">
              {(me.roles || []).map(r => <span key={r} className="text-xs px-2 py-0.5 rounded-full bg-brand/10 text-brand capitalize">{r}</span>)}
            </div>
          </div>
        </div>

        {/* Change password */}
        <div className="card p-6">
          <h3 className="font-display text-lg mb-4 flex items-center gap-2"><KeyRound size={18} className="text-brand" /> Change password</h3>
          {pwMsg && <div className={`mb-3 text-sm rounded-lg px-3 py-2 ${pwMsg.ok ? 'bg-sage/10 text-ink' : 'bg-rust/10 text-rust'}`}>{pwMsg.text}</div>}
          <div className="grid grid-cols-2 gap-3 max-w-lg">
            <input type="password" value={pw.current} onChange={e => setPw(x => ({ ...x, current: e.target.value }))} placeholder="Current password" className="text-sm border border-[#d6deea] rounded-lg px-3 py-2 focus:outline-none focus:border-brand" />
            <input type="password" value={pw.next} onChange={e => setPw(x => ({ ...x, next: e.target.value }))} placeholder="New password" className="text-sm border border-[#d6deea] rounded-lg px-3 py-2 focus:outline-none focus:border-brand" />
          </div>
          <button onClick={changePassword} disabled={pwBusy || !pw.current || !pw.next} className="mt-3 text-sm px-4 py-2 rounded-lg bg-brand text-white hover:bg-branddk disabled:opacity-50">
            {pwBusy ? 'Saving…' : 'Update password'}
          </button>
        </div>

        {/* Changes / approvals */}
        <div className="card p-6">
          <div className="flex gap-2 mb-4">
            <button onClick={() => setTab('mine')} className={`text-sm px-3 py-1.5 rounded-lg border ${tab === 'mine' ? 'bg-brand text-white border-brand' : 'border-[#d6deea] text-slate2 hover:bg-mist'}`}>
              <FileEdit size={14} className="inline mr-1" /> My changes ({mine.length})
            </button>
            <button onClick={() => setTab('approvals')} className={`text-sm px-3 py-1.5 rounded-lg border ${tab === 'approvals' ? 'bg-brand text-white border-brand' : 'border-[#d6deea] text-slate2 hover:bg-mist'}`}>
              <CheckCircle2 size={14} className="inline mr-1" /> My approvals ({myApprovals.length})
            </button>
          </div>
          {loading ? <Loading /> : list.length === 0 ? (
            <p className="text-sm text-slate2">{tab === 'mine' ? "You haven't submitted any changes yet." : "You haven't reviewed any changes yet."}</p>
          ) : (
            <div className="space-y-2">
              {list.map(c => (
                <div key={c.id} className="flex items-center gap-3 text-sm py-2 border-b border-[#eef2f6] last:border-0">
                  {STATUS_ICON[c.status]}
                  <span className="font-medium">{c.target}</span>
                  <span className="text-slate2">{c.old_value} → {c.new_value}</span>
                  <span className={`ml-auto text-xs px-2 py-0.5 rounded-full ${STATUS_COLOR[c.status]}`}>{c.status}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  )
}
