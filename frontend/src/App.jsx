import { useState, useEffect } from 'react'
import { Routes, Route, NavLink, useLocation, Navigate } from 'react-router-dom'
import {
  LayoutDashboard, Database, Layers, TrendingUp, Handshake, Boxes,
  GitBranch, Network, Gauge, Sparkles, Building2, Bot, Share2, Menu, X,
  ClipboardCheck, ChevronLeft, ChevronRight, ShieldCheck, User,
} from 'lucide-react'
import Dashboard from './pages/Dashboard.jsx'
import DataHub from './pages/DataHub.jsx'
import Segmentation from './pages/Segmentation.jsx'
import Forecast from './pages/Forecast.jsx'
import HandshakePage from './pages/Handshake.jsx'
import InventoryPage from './pages/Inventory.jsx'
import Netting from './pages/Netting.jsx'
import MRP from './pages/MRP.jsx'
import Capacity from './pages/Capacity.jsx'
import Optimizer from './pages/Optimizer.jsx'
import Copilot from './pages/Copilot.jsx'
import Login from './pages/Login.jsx'
import Approvals from './pages/Approvals.jsx'
import Admin from './pages/Admin.jsx'
import Profile from './pages/Profile.jsx'
import NetworkPage from './pages/Network.jsx'

// Sidebar grouped to show the planning flow order explicitly (R2-18)
const NAV_GROUPS = [
  { heading: null, items: [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
    { to: '/data', label: 'Data Hub', icon: Database },
    { to: '/network', label: 'Network', icon: Share2 },
  ]},
  { heading: 'Planning flow', items: [
    { to: '/segmentation', label: '1 · Segmentation', icon: Layers },
    { to: '/forecast', label: '2 · Forecast', icon: TrendingUp },
    { to: '/handshake', label: '3 · Demand–Supply', icon: Handshake },
    { to: '/inventory', label: '4 · Inventory', icon: Boxes },
    { to: '/netting', label: '5 · Netting', icon: GitBranch },
    { to: '/mrp', label: '6 · Supply (MRP)', icon: Network },
    { to: '/capacity', label: '7 · Capacity', icon: Gauge },
    { to: '/optimizer', label: '8 · Optimizer', icon: Sparkles },
  ]},
  { heading: 'Tools', items: [
    { to: '/copilot', label: 'AI Copilot', icon: Bot },
    { to: '/approvals', label: 'Approvals', icon: ClipboardCheck },
    { to: '/admin', label: 'Admin', icon: ShieldCheck },
  ]},
]

function getUser() {
  try { return JSON.parse(localStorage.getItem('pravah_user') || 'null') } catch { return null }
}

function Sidebar({ open, setOpen, collapsed, setCollapsed, user }) {
  const companyName = 'Apex Nutraceuticals'  // TODO: from tenant config
  return (
    <aside className={`
      bg-branddk text-white flex flex-col shrink-0
      fixed inset-y-0 left-0 z-50 transform transition-all duration-200
      md:static md:translate-x-0
      ${open ? 'translate-x-0' : '-translate-x-full'}
      ${collapsed ? 'md:w-16' : 'w-60'}
    `}>
      <div className="px-4 py-5 border-b border-white/10 flex items-center justify-between">
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-8 h-8 rounded-lg bg-white/15 flex items-center justify-center shrink-0">
            <Building2 size={18} />
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <div className="font-display text-xl leading-none">Pravah</div>
              <div className="text-[10px] uppercase tracking-widest text-white/50 mt-0.5 truncate">{companyName}</div>
            </div>
          )}
        </div>
        <button onClick={() => setOpen(false)} className="md:hidden p-1 text-white/70 hover:text-white" aria-label="Close menu"><X size={20} /></button>
        <button onClick={() => setCollapsed(c => !c)} className="hidden md:block p-1 text-white/50 hover:text-white" aria-label="Collapse sidebar">
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>
      <nav className="flex-1 py-2 overflow-y-auto">
        {NAV_GROUPS.map((group, gi) => (
          <div key={gi} className="mb-1">
            {group.heading && !collapsed && (
              <div className="px-5 pt-3 pb-1 text-[10px] uppercase tracking-widest text-white/35">{group.heading}</div>
            )}
            {group.items.map(({ to, label, icon: Icon, end }) => (
              <NavLink key={to} to={to} end={end} title={collapsed ? label : undefined}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-5 py-2 text-sm transition ${
                    isActive ? 'bg-white/12 text-white border-l-2 border-amber2' : 'text-white/65 hover:text-white hover:bg-white/5 border-l-2 border-transparent'
                  } ${collapsed ? 'justify-center px-0' : ''}`}>
                <Icon size={17} className="shrink-0" /> {!collapsed && <span className="truncate">{label}</span>}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>
      <div className="px-4 py-3 border-t border-white/10">
        {user ? (
          <NavLink to="/profile" className="flex items-center gap-2 text-white/70 hover:text-white text-xs">
            <span className="w-7 h-7 rounded-full bg-white/15 flex items-center justify-center shrink-0"><User size={14} /></span>
            {!collapsed && <span className="truncate">{user.name || user.email}</span>}
          </NavLink>
        ) : (
          !collapsed && <NavLink to="/login" className="text-xs text-white/50 hover:text-white">Sign in →</NavLink>
        )}
      </div>
    </aside>
  )
}

function MainLayout() {
  const loc = useLocation()
  const [open, setOpen] = useState(false)
  const [collapsed, setCollapsed] = useState(false)
  const user = getUser()
  useEffect(() => { setOpen(false) }, [loc.pathname])

  return (
    <div className="flex min-h-screen">
      <div className="md:hidden fixed top-0 left-0 right-0 h-14 bg-branddk text-white flex items-center justify-between px-4 z-40">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-white/15 flex items-center justify-center"><Building2 size={16} /></div>
          <span className="font-display text-lg">Pravah</span>
        </div>
        <button onClick={() => setOpen(true)} aria-label="Open menu" className="p-2 -mr-2"><Menu size={22} /></button>
      </div>
      {open && <div className="md:hidden fixed inset-0 bg-black/40 z-40" onClick={() => setOpen(false)} />}
      <Sidebar open={open} setOpen={setOpen} collapsed={collapsed} setCollapsed={setCollapsed} user={user} />
      <main className="flex-1 min-w-0 pt-14 md:pt-0">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/data" element={<DataHub />} />
          <Route path="/network" element={<NetworkPage />} />
          <Route path="/segmentation" element={<Segmentation />} />
          <Route path="/forecast" element={<Forecast />} />
          <Route path="/handshake" element={<HandshakePage />} />
          <Route path="/inventory" element={<InventoryPage />} />
          <Route path="/netting" element={<Netting />} />
          <Route path="/mrp" element={<MRP />} />
          <Route path="/capacity" element={<Capacity />} />
          <Route path="/optimizer" element={<Optimizer />} />
          <Route path="/copilot" element={<Copilot />} />
          <Route path="/approvals" element={<Approvals />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/*" element={<MainLayout />} />
    </Routes>
  )
}
