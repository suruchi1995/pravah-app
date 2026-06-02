import { useState, useEffect } from 'react'
import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, Database, Layers, TrendingUp, Handshake, Boxes,
  GitBranch, Network, Gauge, Sparkles, Building2, Upload, Bot, Share2, Menu, X,
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
import NetworkPage from './pages/Network.jsx'

const NAV = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/data', label: 'Data Hub', icon: Database },
  { to: '/network', label: 'Network', icon: Share2 },
  { to: '/segmentation', label: 'Segmentation', icon: Layers },
  { to: '/forecast', label: 'Forecast', icon: TrendingUp },
  { to: '/handshake', label: 'Demand–Supply', icon: Handshake },
  { to: '/inventory', label: 'Inventory', icon: Boxes },
  { to: '/netting', label: 'Netting', icon: GitBranch },
  { to: '/mrp', label: 'Supply (MRP)', icon: Network },
  { to: '/capacity', label: 'Capacity', icon: Gauge },
  { to: '/optimizer', label: 'Optimizer', icon: Sparkles },
  { to: '/copilot', label: 'AI Copilot', icon: Bot },
]

export default function App() {
  const loc = useLocation()
  const [open, setOpen] = useState(false)   // mobile drawer state

  // close the drawer whenever the route changes (tapped a nav link)
  useEffect(() => { setOpen(false) }, [loc.pathname])

  return (
    <div className="flex min-h-screen">
      {/* Mobile top bar (hidden on md+) */}
      <div className="md:hidden fixed top-0 left-0 right-0 h-14 bg-branddk text-white flex items-center justify-between px-4 z-40">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-white/15 flex items-center justify-center">
            <Building2 size={16} />
          </div>
          <span className="font-display text-lg">Pravah</span>
        </div>
        <button onClick={() => setOpen(true)} aria-label="Open menu" className="p-2 -mr-2">
          <Menu size={22} />
        </button>
      </div>

      {/* Overlay behind the drawer on mobile */}
      {open && (
        <div className="md:hidden fixed inset-0 bg-black/40 z-40" onClick={() => setOpen(false)} aria-hidden="true" />
      )}

      {/* Sidebar: static on desktop, off-canvas drawer on mobile */}
      <aside className={`
        bg-branddk text-white flex flex-col w-60 shrink-0
        fixed inset-y-0 left-0 z-50 transform transition-transform duration-200
        md:static md:translate-x-0
        ${open ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="px-5 py-5 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-white/15 flex items-center justify-center">
              <Building2 size={18} />
            </div>
            <div>
              <div className="font-display text-xl leading-none">Pravah</div>
              <div className="text-[10px] uppercase tracking-widest text-white/50 mt-0.5">Planning OS</div>
            </div>
          </div>
          {/* close button only on mobile */}
          <button onClick={() => setOpen(false)} className="md:hidden p-1 text-white/70 hover:text-white" aria-label="Close menu">
            <X size={20} />
          </button>
        </div>
        <nav className="flex-1 py-3 overflow-y-auto">
          {NAV.map(({ to, label, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 px-5 py-2.5 text-sm transition ${
                  isActive ? 'bg-white/12 text-white border-l-2 border-amber2' : 'text-white/65 hover:text-white hover:bg-white/5 border-l-2 border-transparent'
                }`}>
              <Icon size={17} /> {label}
            </NavLink>
          ))}
        </nav>
        <div className="px-5 py-4 text-[11px] text-white/40 border-t border-white/10">
          Apex Nutraceuticals · demo tenant
        </div>
      </aside>

      {/* Main content. Pad top on mobile to clear the fixed top bar. */}
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
        </Routes>
      </main>
    </div>
  )
}
