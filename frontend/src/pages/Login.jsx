import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { Building2 } from 'lucide-react'

export default function Login({ onLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const navigate = useNavigate()

  async function submit() {
    if (!email || !password) { setError('Please enter email and password.'); return }
    setBusy(true); setError('')
    try {
      const r = await api.login(email, password)
      if (r.token) {
        localStorage.setItem('pravah_token', r.token)
        localStorage.setItem('pravah_user', JSON.stringify(r.user))
        onLogin && onLogin(r.user)
        navigate('/')
      } else {
        setError(r.detail || 'Login failed.')
      }
    } catch (e) {
      setError('Could not reach the server. Please try again.')
    }
    setBusy(false)
  }

  return (
    <div className="min-h-screen bg-branddk flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-sm">
        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-branddk flex items-center justify-center">
            <Building2 size={22} className="text-white" />
          </div>
          <div>
            <div className="font-display text-2xl text-ink">Pravah</div>
            <div className="text-xs uppercase tracking-widest text-slate2">Planning OS</div>
          </div>
        </div>
        <h2 className="font-display text-xl text-ink mb-6">Sign in</h2>
        {error && <div className="mb-4 text-sm text-rust bg-rust/10 rounded-lg px-4 py-3">{error}</div>}
        <div className="space-y-4">
          <div>
            <label className="text-xs uppercase tracking-wide text-slate2 mb-1 block">Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)}
              onKeyDown={e => e.key==='Enter' && submit()}
              className="w-full border border-[#d6deea] rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-brand"
              placeholder="you@company.com" />
          </div>
          <div>
            <label className="text-xs uppercase tracking-wide text-slate2 mb-1 block">Password</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)}
              onKeyDown={e => e.key==='Enter' && submit()}
              className="w-full border border-[#d6deea] rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-brand"
              placeholder="••••••••" />
          </div>
          <button onClick={submit} disabled={busy}
            className="w-full bg-brand text-white rounded-xl py-2.5 text-sm font-medium hover:bg-branddk disabled:opacity-50 mt-2">
            {busy ? 'Signing in…' : 'Sign in'}
          </button>
        </div>
        <p className="text-xs text-slate2 mt-6 text-center">Contact your admin to create an account.</p>
      </div>
    </div>
  )
}
