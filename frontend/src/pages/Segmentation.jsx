import { useState } from 'react'
import { api } from '../api'
import { useAsync, PageHeader, Grid, Loading, ErrorBox, fmtMoney } from '../components/ui'
import { FilterBar, rowPasses, deriveOptions } from '../components/FilterBar'

export default function Segmentation() {
  const { loading, data, error } = useAsync(() => api.segmentation())
  const [filters, setFilters] = useState({ items: [], locations: [], periods: [] })
  if (loading) return <><PageHeader title="Segmentation" /><Loading /></>
  if (error) return <ErrorBox msg={error} />

  const cfg = deriveOptions(data, { item: true, location: false, period: false })
  const rows = data.filter(r => rowPasses(r, filters))

  const cells = {}
  for (const a of ['A', 'B', 'C']) for (const x of ['X', 'Y', 'Z']) cells[a + x] = []
  rows.forEach(r => cells[r.abc_xyz]?.push(r.item_code))

  const cols = [
    { field: 'item_code', headerName: 'SKU', maxWidth: 110 },
    { field: 'abc_xyz', headerName: 'Class', maxWidth: 90 },
    { field: 'annual_value', headerName: 'Annual Value', valueFormatter: p => fmtMoney(p.value) },
    { field: 'cov', headerName: 'CoV', maxWidth: 90, valueFormatter: p => p.value?.toFixed(2) },
    { field: 'reasoning', headerName: 'Reasoning', minWidth: 360, flex: 2 },
  ]
  const tone = { A: '#2E5C8A', B: '#5b8a72', C: '#94a3b8' }

  return (
    <>
      <PageHeader title="Segmentation" subtitle="ABC by annual value, XYZ by demand variability — computed from history, not assigned." />
      <FilterBar config={cfg} value={filters} onChange={setFilters} />
      <div className="p-8 space-y-6">
        <div className="card p-6">
          <h3 className="font-display text-xl mb-4">ABC × XYZ matrix</h3>
          <div className="grid grid-cols-[40px_1fr_1fr_1fr] gap-2">
            <div></div>
            {['X — stable', 'Y — variable', 'Z — erratic'].map(h => <div key={h} className="text-xs text-slate2 text-center pb-1">{h}</div>)}
            {['A', 'B', 'C'].map(a => (
              <>
                <div key={a} className="flex items-center justify-center font-display text-lg" style={{ color: tone[a] }}>{a}</div>
                {['X', 'Y', 'Z'].map(x => (
                  <div key={a + x} className="border border-[#e7ecf2] rounded-lg p-3 min-h-[68px] bg-mist/40">
                    <div className="flex flex-wrap gap-1">
                      {cells[a + x].map(s => (
                        <span key={s} className="text-xs px-1.5 py-0.5 rounded bg-white border border-[#e0e7ef]">{s}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </>
            ))}
          </div>
        </div>
        <div className="card p-5"><Grid rows={rows} columns={cols} /></div>
      </div>
    </>
  )
}
