import { useState } from 'react'
import { api } from '../api'
import { useAsync, PageHeader, Loading, ErrorBox } from '../components/ui'
import { FilterBar } from '../components/FilterBar'
import { useScenario } from '../context/ScenarioContext.jsx'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts'

const LABELS = { min_cost: 'Minimise Cost', max_service: 'Maximise Service', balanced: 'Balanced' }

export default function Optimizer() {
  const { loading, data, error } = useAsync(() => api.optimizer())
  const { scenario: sel, setScenario: setSel } = useScenario()
  const [filters, setFilters] = useState({ items: [], locations: [], periods: [] })
  if (loading) return <><PageHeader title="Optimization Workbench" /><Loading /></>
  if (error) return <ErrorBox msg={error} />

  const scenarios = Object.keys(data || {})
  if (scenarios.length === 0) {
    return (
      <>
        <PageHeader title="Optimization Workbench" subtitle="Google OR-Tools production plan under three objectives." />
        <div className="p-8">
          <div className="card p-8 text-center">
            <p className="text-slate2 mb-2">No optimization results yet.</p>
            <p className="text-sm text-slate2">Go to <b>Data Hub</b> and click <b>Reset demo</b> (or upload data) to run the planner, then return here.</p>
          </div>
        </div>
      </>
    )
  }
  const allSkus = [...new Set(Object.values(data).flatMap(s => (s.plan || []).map(p => p.item_code)))].sort()
  const activeItems = filters.items || []
  const skus = activeItems.length ? allSkus.filter(s => activeItems.includes(s)) : allSkus
  const compare = skus.map(sku => {
    const row = { sku }
    scenarios.forEach(sc => { row[sc] = Math.round((data[sc].plan || []).filter(p => p.item_code === sku).reduce((a, p) => a + p.quantity, 0)) })
    return row
  })
  const cur = data[sel] || data[scenarios[0]]
  const colors = { min_cost: '#2E5C8A', max_service: '#5b8a72', balanced: '#c98a3c' }

  return (
    <>
      <PageHeader title="Optimization Workbench" subtitle="Google OR-Tools production plan under three objectives. The scenarios genuinely diverge because capacity binds.">
        <div className="flex gap-2">
          {scenarios.map(sc => (
            <button key={sc} onClick={() => setSel(sc)}
              className={`text-sm px-3 py-2 rounded-lg border ${sel === sc ? 'bg-brand text-white border-brand' : 'border-[#d6deea] text-slate2 hover:bg-mist'}`}>
              {LABELS[sc] || sc}
            </button>
          ))}
        </div>
      </PageHeader>
      <FilterBar config={{ items: allSkus }} value={filters} onChange={setFilters} />
      <div className="p-8 space-y-6">
        <div className="card p-6 border-l-4" style={{ borderColor: colors[sel] }}>
          <div className="text-xs uppercase tracking-wide text-slate2">{LABELS[sel]} · {cur.status}</div>
          <p className="text-sm mt-2">{cur.reasoning}</p>
        </div>
        <div className="card p-6">
          <h3 className="font-display text-xl mb-1">Production mix by scenario</h3>
          <p className="text-sm text-slate2 mb-4">Same capacity, different choices about what to make and what to short.</p>
          <ResponsiveContainer width="100%" height={360}>
            <BarChart data={compare} margin={{ left: 10, right: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eef2f6" vertical={false} />
              <XAxis dataKey="sku" tick={{ fontSize: 11, fill: '#475569' }} />
              <YAxis tick={{ fontSize: 12, fill: '#475569' }} />
              <Tooltip /><Legend />
              {scenarios.map(sc => <Bar key={sc} dataKey={sc} name={LABELS[sc] || sc} fill={colors[sc]} radius={[3,3,0,0]} />)}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </>
  )
}
