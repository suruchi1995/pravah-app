import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard, Database, Layers, TrendingUp, Handshake, Boxes,
  GitBranch, Network, Gauge, Sparkles, Building2, Upload,
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

const NAV = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/data', label: 'Data Hub', icon: Database },
  { to: '/segmentation', label: 'Segmentation', icon: Layers },
  { to: '/forecast', label: 'Forecast', icon: TrendingUp },
  { to: '/handshake', label: 'Demand–Supply', icon: Handshake },
  { to: '/inventory', label: 'Inventory', icon: Boxes },
  { to: '/netting', label: 'Netting', icon: GitBranch },
  { to: '/mrp', label: 'Supply (MRP)', icon: Network },
  { to: '/capacity', label: 'Capacity', icon: Gauge },
  { to: '/optimizer', label: 'Optimizer', icon: Sparkles },
]

export default function App() {
  const loc = useLocation()
  return (
    <div className="flex min-h-screen">
      <aside className="w-60 shrink-0 bg-branddk text-white flex flex-col">
        <div className="px-5 py-5 border-b border-white/10">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-white/15 flex items-center justify-center">
              <Building2 size={18} />
            </div>
            <div>
              <div className="font-display text-xl leading-none">Pravah</div>
              <div className="text-[10px] uppercase tracking-widest text-white/50 mt-0.5">Planning OS</div>
            </div>
          </div>
        </div>
        <nav className="flex-1 py-3">
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

      <main className="flex-1 min-w-0">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/data" element={<DataHub />} />
          <Route path="/segmentation" element={<Segmentation />} />
          <Route path="/forecast" element={<Forecast />} />
          <Route path="/handshake" element={<HandshakePage />} />
          <Route path="/inventory" element={<InventoryPage />} />
          <Route path="/netting" element={<Netting />} />
          <Route path="/mrp" element={<MRP />} />
          <Route path="/capacity" element={<Capacity />} />
          <Route path="/optimizer" element={<Optimizer />} />
        </Routes>
      </main>
    </div>
  )
}
