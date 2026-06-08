import { useState } from 'react'
import { api } from '../api'
import { useAsync, PageHeader, Loading, ErrorBox, fmtMoney } from '../components/ui'
import { FilterBar, rowPasses, deriveOptions } from '../components/FilterBar'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell, PieChart, Pie, Legend } from 'recharts'

const ABC_COLOR = { A: '#2E5C8A', B: '#5b8a72', C: '#94a3b8' }
const XYZ_COLOR = { X: '#5b8a72', Y: '#c98a3c', Z: '#b5544a' }

export default function Segmentation() {
  const { loading, data, error } = useAsync(() => api.segmentation())
  const [filters, setFilters] = useState({ items: [], locations: [], periods: [] })
  if (loading) return <><PageHeader title="Segmentation" /><Loading /></>
  if (error) return <ErrorBox msg={error} />

  const cfg = deriveOptions(data, { item: true, location: false, period: false })
  // The engine now returns both item-level summary rows (location='ALL') and
  // item-location rows. Use the ALL rows for the item-level charts/matrix.
  const itemRows = (data || []).filter(r => r.location_code === 'ALL')
  const rows = itemRows.filter(r => rowPasses(r, filters))

  // ABC bar chart data
  const abcData = ['A','B','C'].map(cls => ({
    class: cls,
    count: rows.filter(r => r.abc_class === cls).length,
    value: rows.filter(r => r.abc_class === cls).reduce((a,r) => a+r.annual_value, 0),
  }))

  // XYZ pie data
  const xyzData = ['X','Y','Z'].map(cls => ({
    name: cls === 'X' ? 'Stable (X)' : cls === 'Y' ? 'Variable (Y)' : 'Erratic (Z)',
    value: rows.filter(r => r.xyz_class === cls).length,
    color: XYZ_COLOR[cls],
  }))

  // ABC×XYZ matrix
  const matrix = {}
  for (const a of ['A','B','C']) for (const x of ['X','Y','Z']) matrix[a+x] = []
  rows.forEach(r => matrix[r.abc_xyz]?.push(r.item_code))

  // Focus lists
  const topValue = [...rows].sort((a,b) => b.annual_value - a.annual_value).slice(0,5)
  const leastValue = [...rows].sort((a,b) => a.annual_value - b.annual_value).slice(0,3)
  const mostErratic = rows.filter(r => r.xyz_class === 'Z')

  return (
    <>
      <PageHeader title="Segmentation" subtitle="ABC by annual value, XYZ by demand variability — computed from history, not assigned." />
      <FilterBar config={cfg} value={filters} onChange={setFilters} />
      <div className="p-8 space-y-6">

        {/* Charts row */}
        <div className="grid grid-cols-2 gap-4">
          <div className="card p-5">
            <h3 className="font-display text-lg mb-3">Annual Value by ABC Class</h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={abcData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#eef2f6" vertical={false} />
                <XAxis dataKey="class" />
                <YAxis tickFormatter={v => '₹'+(v/1e6).toFixed(1)+'M'} />
                <Tooltip formatter={(v,n) => n==='value' ? fmtMoney(v) : v} />
                <Bar dataKey="value" name="Annual Value" radius={[5,5,0,0]}>
                  {abcData.map((e,i) => <Cell key={i} fill={ABC_COLOR[e.class]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="card p-5">
            <h3 className="font-display text-lg mb-3">Demand Variability (XYZ)</h3>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={xyzData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({name,value}) => `${name}: ${value}`}>
                  {xyzData.map((e,i) => <Cell key={i} fill={e.color} />)}
                </Pie>
                <Legend />
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Matrix */}
        <div className="card p-6">
          <h3 className="font-display text-xl mb-4">ABC × XYZ matrix</h3>
          <div className="grid grid-cols-[40px_1fr_1fr_1fr] gap-2">
            <div></div>
            {['X — stable','Y — variable','Z — erratic'].map(h => <div key={h} className="text-xs text-slate2 text-center pb-1">{h}</div>)}
            {['A','B','C'].map(a => (<>
              <div key={a} className="flex items-center justify-center font-display text-lg" style={{color:ABC_COLOR[a]}}>{a}</div>
              {['X','Y','Z'].map(x => (
                <div key={a+x} className={`border rounded-lg p-3 min-h-[60px] ${a==='A'&&x==='Z' ? 'border-rust/40 bg-rust/5' : 'border-[#e7ecf2] bg-mist/40'}`}>
                  <div className="flex flex-wrap gap-1">
                    {matrix[a+x].map(s => <span key={s} className="text-xs px-1.5 py-0.5 rounded bg-white border border-[#e0e7ef]">{s}</span>)}
                  </div>
                </div>
              ))}
            </>))}
          </div>
          <p className="text-xs text-slate2 mt-3">⚠️ AZ items (top-right) = high value + erratic demand — need the most planning attention.</p>
        </div>

        {/* Focus lists */}
        <div className="grid grid-cols-3 gap-4">
          <div className="card p-5">
            <h3 className="font-semibold text-ink mb-3">🎯 Top items to focus on</h3>
            <div className="space-y-2">
              {topValue.map(r => <div key={r.item_code} className="flex justify-between text-sm"><span className="font-medium">{r.item_code} <span className="text-xs text-slate2">({r.abc_xyz})</span></span><span>{fmtMoney(r.annual_value)}</span></div>)}
            </div>
          </div>
          <div className="card p-5">
            <h3 className="font-semibold text-ink mb-3">📉 Lowest value items</h3>
            <div className="space-y-2">
              {leastValue.map(r => <div key={r.item_code} className="flex justify-between text-sm"><span className="font-medium">{r.item_code} <span className="text-xs text-slate2">({r.abc_xyz})</span></span><span>{fmtMoney(r.annual_value)}</span></div>)}
            </div>
          </div>
          <div className="card p-5">
            <h3 className="font-semibold text-ink mb-3">⚡ Erratic (Z) items — watch closely</h3>
            {mostErratic.length ? <div className="space-y-2">
              {mostErratic.map(r => <div key={r.item_code} className="text-sm"><span className="font-medium">{r.item_code}</span> <span className="text-xs text-slate2">({r.abc_xyz})</span></div>)}
            </div> : <p className="text-sm text-slate2">No erratic items — good!</p>}
          </div>
        </div>
      </div>
    </>
  )
}
