import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { PageHeader, Loading } from '../components/ui'
import { User, Shield, KeyRound, FileEdit, CheckCircle2, XCircle, Clock, Lock, LogOut } from 'lucide-react'

const STATUS_ICON = { submitted: <Clock size={14} className="text-amber2" />, approved: <CheckCircle2 size={14} className="text-sage" />, rejected: <XCircle size={14} className="text-rust" /> }
const STATUS_COLOR = { submitted: 'bg-amber2/10 text-amber2', approved: 'bg-sage/10 text-sage', rejected: 'bg-rust/10 text-rust' }

export default function Profile() {
  const navigate = useNavigate()
  const token = localStorage.getItem('pravah_token')
  let user = {}
  try { user = JSON.parse(localStorage.getItem('pravah_user') || '{}') } catch {}

  const [crs, setCrs] = useState([])
  const [loading, setLoading] = useState(true)
  const [pw, setPw] = useState({ current: '', next: '', confirm: '' })
  const [pwMsg, setPwMsg] = useState(null)
  const [busy, setBusy] = useState(false)

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

  async function changePw() {
    setPwMsg(null)
    if (pw.next.length < 6) { setPwMsg({ type: 'err', text: 'New password must be at least 6 characters.' }); return }
    if (pw.next !== pw.confirm) { setPwMsg({ type: 'err', text: 'New passwords do not match.' }); return }
    setBusy(true)
    try {
      const r = await api.changePassword(token, pw.current, pw.next)
      if (r.ok) { setPwMsg({ type: 'ok', text: 'Password changed successfully.' }); setPw({ current: '', next: '', confirm: '' }) }
      else setPwMsg({ type: 'err', text: r.detail || 'Could not change password.' })
    } catch { setPwMsg({ type: 'err', text: 'Could not change password.' }) }
    setBusy(false)
  }

  function signOut() {
    localStorage.removeItem('pravah_token')
    localStorage.removeItem('pravah_user')
    navigate('/login')
  }

  if (!token) {
    return (
      <>
        <PageHeader title="My Profile" />
        <div className="p-8">
          <div className="card p-8 text-center max-w-md mx-auto">
            <Lock className="mx-auto text-slate2 mb-3" size={32} />
            <h3 className="font-display text-xl mb-2">Sign in required</h3>
            <button onClick={() => navigate('/login')} className="mt-2 text-sm px-4 py-2 rounded-lg bg-brand text-white hover:bg-branddk">Go to sign in</button>
          </div>
        </div>
      </>
    )
  }

  const myChanges = crs.filter(c => c.requested_by === user.email)
  const myApprovals = crs.filter(c => c.reviewed_by === user.email)

  return (
    <>
      <PageHeader title="My Profile" subtitle="Your account, roles, the changes you've requested, and the approvals you've made.">
        <button onClick={signOut} className="flex items-center gap-2 text-sm px-3 py-2 rounded-lg border border-[#d6deea] text-slate2 hover:bg-mist">
          <LogOut size={15} /> Sign out
        </button>
      </PageHeader>
      <div className="p-8 space-y-6">
        {/* Identity */}
        <div className="card p-6">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-full bg-brand/10 flex items-center justify-center"><User size={26} className="text-brand" /></div>
            <div>
              <div className="font-display text-2xl text-ink">{user.name || user.email}</div>
              <div className="text-sm text-slate2">{user.email}</div>
            </div>
          </div>
          <div className="mt-4 flex items-center gap-2 flex-wrap">
            <Shield size={16} className="text-slate2" />
            {(user.roles || []).map(r => <span key={r} className="text-xs px-2.5 py-1 rounded-full bg-brand/10 text-brand capitalize">{r}</span>)}
          </div>
        </div>

        {/* Change password */}
        <div className="card p-6">
          <h3 className="font-display text-xl mb-4 flex items-center gap-2"><KeyRound size={18} className="text-brand" /> Change password</h3>
          {pwMsg && <div className={`mb-4 text-sm rounded-lg px-4 py-2 ${pwMsg.type === 'ok' ? 'bg-sage/10 text-sage' : 'bg-rust/10 text-rust'}`}>{pwMsg.text}</div>}
          <div className="grid grid-cols-3 gap-3 max-w-2xl">
            <input type="password" value={pw.current} onChange={e => setPw(p => ({ ...p, current: e.target.value }))} placeholder="Current password" className="text-sm border border-[#d6deea] rounded-lg px-3 py-2 focus:outline-none focus:border-brand" />
            <input type="password" value={pw.next} onChange={e => setPw(p => ({ ...p, next: e.target.value }))} placeholder="New password" className="text-sm border border-[#d6deea] rounded-lg px-3 py-2 focus:outline-none focus:border-brand" />
            <input type="password" value={pw.confirm} onChange={e => setPw(p => ({ ...p, confirm: e.target.value }))} placeholder="Confirm new" className="text-sm border border-[#d6deea] rounded-lg px-3 py-2 focus:outline-none focus:border-brand" />
          </div>
          <button onClick={changePw} disabled={busy || !pw.current || !pw.next} className="mt-3 text-sm px-4 py-2 rounded-lg bg-brand text-white hover:bg-branddk disabled:opacity-50">
            {busy ? 'Saving…' : 'Update password'}
          </button>
        </div>

        {/* My changes + approvals */}
        {loading ? <Loading /> : (
          <div className="grid grid-cols-2 gap-4">
            <div className="card p-6">
              <h3 className="font-display text-lg mb-3 flex items-center gap-2"><FileEdit size={18} className="text-brand" /> Changes I've requested ({myChanges.length})</h3>
              {myChanges.length === 0 ? <p className="text-sm text-slate2">No change requests yet.</p> : (
                <div className="space-y-2">
                  {myChanges.map(c => (
                    <div key={c.id} className="flex items-center gap-2 text-sm py-2 border-b border-[#eef2f6] last:border-0">
                      {STATUS_ICON[c.status]}
                      <span className="flex-1 min-w-0 truncate">{c.target}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_COLOR[c.status]}`}>{c.status}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="card p-6">
              <h3 className="font-display text-lg mb-3 flex items-center gap-2"><CheckCircle2 size={18} className="text-brand" /> Approvals I've made ({myApprovals.length})</h3>
              {myApprovals.length === 0 ? <p className="text-sm text-slate2">No approvals yet.</p> : (
                <div className="space-y-2">
                  {myApprovals.map(c => (
                    <div key={c.id} className="flex items-center gap-2 text-sm py-2 border-b border-[#eef2f6] last:border-0">
                      {STATUS_ICON[c.status]}
                      <span className="flex-1 min-w-0 truncate">{c.target}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_COLOR[c.status]}`}>{c.status}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </>
  )
}
