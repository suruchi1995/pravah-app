import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useAsync, PageHeader, Loading, ErrorBox, fmtMoney, fmtPct } from '../components/ui'
import { FilterBar, rowPasses, deriveOptions } from '../components/FilterBar'
import { useScenario } from '../context/ScenarioContext.jsx'
import { IndianRupee, Target, Activity, AlertTriangle, TrendingUp, X } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'

function BottleneckModal({ bottlenecks, onClose }) {
  if (!bottlenecks?.length) return null
  const worst = bottlenecks[0]
  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="card p-6 max-w-lg w-full" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-display text-xl text-rust">Capacity Bottleneck</h3>
          <button onClick={onClose} className="text-slate2 hover:text-ink"><X size={20} /></button>
        </div>
        <div className="space-y-3">
          {bottlenecks.map((b, i) => (
            <div key={i} className="border border-[#e7ecf2] rounded-xl p-4">
              <div className="font-semibold text-ink">{b.resource_code}</div>
              <div className="text-sm text-slate2 mt-1">Period: {b.period?.slice(0,7)} · Utilisation: <span className="text-rust font-bold">{Math.round(b.utilization*100)}%</span> · Status: {b.constraint_status}</div>
              <div className="mt-2 text-sm bg-amber2/10 text-amber2 rounded-lg p-3">
                <b>Suggested fix:</b> {b.utilization > 1.1
                  ? `This line is ${Math.round((b.utilization-1)*100)}% over capacity. Consider: (1) adding a second shift, (2) splitting production across periods, or (3) using the Optimizer to reallocate production.`
                  : `This line is tight. Prioritise high-margin SKUs and use the Optimizer's Balanced scenario to minimise shortfalls.`}
              </div>
            </div>
          ))}
        </div>
        <button onClick={onClose} className="mt-4 w-full text-sm py-2 rounded-lg border border-[#d6deea] hover:bg-mist">Close</button>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { scenario, setScenario } = useScenario()
  const [filters, setFilters] = useState({ items: [], locations: [], periods: [] })
  const [showBottleneck, setShowBottleneck] = useState(false)
  const s = useAsync(() => api.summary())
  const hs = useAsync(() => api.handshake())
  const cap = useAsync(() => api.capacity())

  if (s.loading || hs.loading) return <><PageHeader title="Control Tower" /><Loading /></>
  if (s.error) return <ErrorBox msg={s.error} />

  const d = s.data
  const allHS = hs.data || []
  const cfg = deriveOptions(allHS, { item: true, location: true, period: true })
  const filtered = allHS.filter(r => rowPasses(r, filters))

  const totalRisk = filtered.reduce((a, r) => a + r.revenue_at_risk, 0)
  const avgFill = filtered.length ? filtered.reduce((a, r) => a + r.fill_rate, 0) / filtered.length : 0
  const skusAtRisk = new Set(filtered.filter(r => r.gap_qty > 0).map(r => r.item_code)).size
  const bottlenecks = (cap.data || []).filter(r => r.constraint_status === 'OVERLOADED' || r.constraint_status === 'TIGHT')
  const topRisk = [...filtered].sort((a,b) => b.revenue_at_risk - a.revenue_at_risk).slice(0,8).map(r => ({
    name: `${r.item_code}·${r.location_code.replace('DC_','')}`,
    risk: Math.round(r.revenue_at_risk),
  }))

  const KPI = ({ label, value, sub, tone, icon: Icon, onClick }) => {
    const bg = { brand:'#e8f0f8', sage:'#e8f1ec', amber:'#f7eede', rust:'#f6e7e5' }[tone]
    const fg = { brand:'#2E5C8A', sage:'#5b8a72', amber:'#c98a3c', rust:'#b5544a' }[tone]
    return (
      <div onClick={onClick} className={`card p-5 flex-1 min-w-[160px] ${onClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''}`}>
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs uppercase tracking-wide text-slate2">{label}</span>
          {Icon && <span className="kpi-accent" style={{ background: bg, color: fg }}><Icon size={18} /></span>}
        </div>
        <div className="font-display text-3xl text-ink">{value}</div>
        {sub && <div className="text-xs text-slate2 mt-1">{sub}</div>}
        {onClick && <div className="text-xs text-brand mt-2">Click to explore →</div>}
      </div>
    )
  }

  return (
    <>
      <PageHeader title="Control Tower" subtitle="Network-wide signal: where demand outruns supply, what it costs, what's constrained." />
      <FilterBar config={cfg} value={filters} onChange={setFilters} />
      {showBottleneck && <BottleneckModal bottlenecks={bottlenecks} onClose={() => setShowBottleneck(false)} />}

      <div className="p-8 space-y-6">
        <div className="flex gap-4 flex-wrap">
          <KPI label="Revenue at Risk" value={fmtMoney(totalRisk)} sub="demand not met × price" tone="rust" icon={IndianRupee} onClick={() => navigate('/handshake')} />
          <KPI label="Avg Fill Rate" value={fmtPct(avgFill)} sub="supply ÷ demand" tone="amber" icon={Activity} onClick={() => navigate('/handshake')} />
          <KPI label="SKUs at Risk" value={skusAtRisk} sub="items with a supply gap" tone="rust" icon={Target} onClick={() => navigate('/handshake')} />
          <KPI label="Forecast MAPE" value={(d.avg_mape || 0) + '%'} sub="auto-selected models" tone="sage" icon={TrendingUp} onClick={() => navigate('/forecast')} />
          <KPI label="Capacity Bottlenecks" value={bottlenecks.length} sub="tight or overloaded resources" tone={bottlenecks.length > 0 ? 'rust' : 'sage'} icon={AlertTriangle} onClick={bottlenecks.length ? () => setShowBottleneck(true) : null} />
        </div>

        <div className="card p-6">
          <h3 className="font-display text-xl mb-1">Revenue at Risk — top exposures</h3>
          <p className="text-sm text-slate2 mb-4">Gap × selling price, by SKU and distribution centre. Click a bar to investigate.</p>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={topRisk} margin={{ left: 10, right: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eef2f6" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#475569' }} />
              <YAxis tick={{ fontSize: 12, fill: '#475569' }} tickFormatter={v => '₹' + (v/1000).toFixed(0) + 'k'} />
              <Tooltip formatter={v => fmtMoney(v)} />
              <Bar dataKey="risk" fill="#b5544a" radius={[5,5,0,0]} cursor="pointer" onClick={() => navigate('/handshake')} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card p-6">
          <h3 className="font-display text-xl mb-3">Optimization scenarios</h3>
          <div className="grid grid-cols-3 gap-4">
            {Object.entries(d.scenarios || {}).map(([k,v]) => (
              <div key={k}
                className={`border rounded-xl p-4 cursor-pointer transition ${scenario === k ? 'border-brand ring-1 ring-brand bg-brand/5' : 'border-[#e7ecf2] hover:border-brand'}`}
                onClick={() => { setScenario(k); navigate('/optimizer') }}>
                <div className="text-xs uppercase tracking-wide text-slate2">{k.replace('_',' ')}{scenario === k && ' · selected'}</div>
                <div className="font-display text-lg mt-1 capitalize">{v.status?.toLowerCase()}</div>
                <div className="text-xs text-slate2 mt-1">Click to select &amp; explore →</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  )
}
