import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { PageHeader, Loading } from '../components/ui'
import { UserPlus, Shield, KeyRound, UserX, UserCheck, Copy, Lock } from 'lucide-react'

const ALL_ROLES = ['admin', 'planner', 'approver', 'management', 'viewer']

export default function Admin() {
  const navigate = useNavigate()
  const token = localStorage.getItem('pravah_token')
  let me = {}
  try { me = JSON.parse(localStorage.getItem('pravah_user') || '{}') } catch {}
  const isAdmin = Array.isArray(me.roles) && me.roles.includes('admin')

  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [refresh, setRefresh] = useState(0)
  const [form, setForm] = useState({ email: '', full_name: '', roles: ['viewer'] })
  const [msg, setMsg] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!token || !isAdmin) { setLoading(false); return }
    let cancelled = false
    setLoading(true)
    api.listUsers(token).then(d => { if (!cancelled) setUsers(Array.isArray(d) ? d : []) })
      .catch(() => { if (!cancelled) setUsers([]) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [refresh, token, isAdmin])

  async function addUser() {
    if (!form.email || !form.full_name) { setMsg({ type: 'err', text: 'Name and email are required.' }); return }
    setBusy(true); setMsg(null)
    try {
      const r = await api.createUser(token, form)
      if (r.ok) {
        setMsg({ type: 'ok', text: `User created. Temporary password: ${r.temp_password}`, pw: r.temp_password })
        setForm({ email: '', full_name: '', roles: ['viewer'] })
        setRefresh(x => x + 1)
      } else setMsg({ type: 'err', text: r.detail || 'Failed to create user.' })
    } catch (e) { setMsg({ type: 'err', text: 'Failed to create user.' }) }
    setBusy(false)
  }

  async function act(action, email) {
    setBusy(true); setMsg(null)
    try {
      const r = await api.userAction(token, action, email)
      if (r.temp_password) setMsg({ type: 'ok', text: `New temporary password for ${email}: ${r.temp_password}`, pw: r.temp_password })
      setRefresh(x => x + 1)
    } catch {}
    setBusy(false)
  }

  function toggleRole(role) {
    setForm(f => ({ ...f, roles: f.roles.includes(role) ? f.roles.filter(r => r !== role) : [...f.roles, role] }))
  }

  if (!token || !isAdmin) {
    return (
      <>
        <PageHeader title="Admin" />
        <div className="p-8">
          <div className="card p-8 text-center max-w-md mx-auto">
            <Lock className="mx-auto text-slate2 mb-3" size={32} />
            <h3 className="font-display text-xl mb-2">Admins only</h3>
            <p className="text-sm text-slate2 mb-4">This workspace is restricted to administrators.</p>
            {!token && <button onClick={() => navigate('/login')} className="text-sm px-4 py-2 rounded-lg bg-brand text-white hover:bg-branddk">Sign in</button>}
          </div>
        </div>
      </>
    )
  }

  return (
    <>
      <PageHeader title="Admin — User Management" subtitle="Register users, assign roles, and manage access. New users get a temporary password and must change it on first login." />
      <div className="p-8 space-y-6">
        {msg && (
          <div className={`card p-4 flex items-start gap-3 border-l-4 ${msg.type === 'ok' ? 'border-sage' : 'border-rust'}`}>
            <div className="flex-1">
              <div className={`text-sm ${msg.type === 'ok' ? 'text-ink' : 'text-rust'}`}>{msg.text}</div>
              {msg.pw && <div className="text-xs text-slate2 mt-1">Copy and share this securely — it won't be shown again.</div>}
            </div>
            {msg.pw && <button onClick={() => navigator.clipboard?.writeText(msg.pw)} className="text-xs flex items-center gap-1 px-2 py-1 rounded border border-[#d6deea] hover:bg-mist"><Copy size={12} /> Copy</button>}
          </div>
        )}

        {/* Add user */}
        <div className="card p-6">
          <h3 className="font-display text-xl mb-4 flex items-center gap-2"><UserPlus size={20} className="text-brand" /> Add user</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs uppercase tracking-wide text-slate2 mb-1 block">Full name</label>
              <input value={form.full_name} onChange={e => setForm(f => ({ ...f, full_name: e.target.value }))}
                className="w-full border border-[#d6deea] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand" placeholder="Priya Sharma" />
            </div>
            <div>
              <label className="text-xs uppercase tracking-wide text-slate2 mb-1 block">Email</label>
              <input type="email" value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                className="w-full border border-[#d6deea] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand" placeholder="priya@company.com" />
            </div>
          </div>
          <div className="mt-4">
            <label className="text-xs uppercase tracking-wide text-slate2 mb-2 block">Roles</label>
            <div className="flex gap-2 flex-wrap">
              {ALL_ROLES.map(role => (
                <button key={role} onClick={() => toggleRole(role)}
                  className={`text-sm px-3 py-1.5 rounded-lg border capitalize ${form.roles.includes(role) ? 'bg-brand text-white border-brand' : 'border-[#d6deea] text-slate2 hover:bg-mist'}`}>
                  {role}
                </button>
              ))}
            </div>
          </div>
          <button onClick={addUser} disabled={busy} className="mt-4 text-sm px-4 py-2 rounded-lg bg-brand text-white hover:bg-branddk disabled:opacity-50">
            {busy ? 'Creating…' : 'Create user'}
          </button>
        </div>

        {/* User list */}
        <div className="card p-6">
          <h3 className="font-display text-xl mb-4 flex items-center gap-2"><Shield size={20} className="text-brand" /> Users ({users.length})</h3>
          {loading ? <Loading /> : (
            <div className="space-y-2">
              {users.map(u => (
                <div key={u.email} className={`flex items-center gap-3 p-3 rounded-xl border ${u.is_active ? 'border-[#e7ecf2]' : 'border-[#e7ecf2] bg-mist/40 opacity-60'}`}>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-ink">{u.full_name} {!u.is_active && <span className="text-xs text-rust">(inactive)</span>}</div>
                    <div className="text-xs text-slate2">{u.email}</div>
                  </div>
                  <div className="flex gap-1 flex-wrap">
                    {u.roles.map(r => <span key={r} className="text-xs px-2 py-0.5 rounded-full bg-brand/10 text-brand capitalize">{r}</span>)}
                  </div>
                  {u.must_change_password && <span className="text-xs text-amber2">must reset pw</span>}
                  <div className="flex gap-1">
                    <button onClick={() => act('reset-password', u.email)} title="Reset password" className="p-2 rounded-lg hover:bg-mist text-slate2"><KeyRound size={15} /></button>
                    {u.is_active
                      ? <button onClick={() => act('deactivate', u.email)} title="Deactivate" className="p-2 rounded-lg hover:bg-mist text-rust"><UserX size={15} /></button>
                      : <button onClick={() => act('activate', u.email)} title="Activate" className="p-2 rounded-lg hover:bg-mist text-sage"><UserCheck size={15} /></button>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  )
}
