import { useState } from 'react'
import { api } from '../api'
import { useAsync, PageHeader, Grid, Loading, ErrorBox, fmtMoney, fmtPct } from '../components/ui'
import { FilterBar, rowPasses, deriveOptions } from '../components/FilterBar'

export default function Handshake() {
  const { loading, data, error } = useAsync(() => api.handshake())
  const [filters, setFilters] = useState({ items: [], locations: [], periods: [] })
  if (loading) return <><PageHeader title="Demand–Supply Handshake" /><Loading /></>
  if (error) return <ErrorBox msg={error} />

  const cfg = deriveOptions(data, { item: true, location: true, period: true })
  const rows = data.filter(r => rowPasses(r, filters))
  const totalRisk = rows.reduce((a, r) => a + r.revenue_at_risk, 0)
  const gaps = rows.filter(r => r.gap_qty > 0).length

  const fillCell = p => {
    const v = p.value
    const color = v >= 0.85 ? '#5b8a72' : v >= 0.6 ? '#c98a3c' : '#b5544a'
    return <span style={{ color, fontWeight: 600 }}>{fmtPct(v)}</span>
  }
  const cols = [
    { field: 'item_code', headerName: 'SKU', maxWidth: 100 },
    { field: 'location_code', headerName: 'DC', maxWidth: 100 },
    { field: 'demand_qty', headerName: 'Demand', valueFormatter: p => Math.round(p.value) },
    { field: 'available_supply_qty', headerName: 'Supply', valueFormatter: p => Math.round(p.value) },
    { field: 'gap_qty', headerName: 'Gap', valueFormatter: p => Math.round(p.value) },
    { field: 'fill_rate', headerName: 'Fill', cellRenderer: fillCell, maxWidth: 110 },
    { field: 'revenue_at_risk', headerName: 'Revenue @ Risk', valueFormatter: p => fmtMoney(p.value) },
    { field: 'recommendation', headerName: 'Recommendation', minWidth: 340, flex: 2 },
  ]
  return (
    <>
      <PageHeader title="Demand–Supply Handshake" subtitle="Where demand outruns available supply — quantified as revenue and margin at risk, with a recommended action." />
      <FilterBar config={cfg} value={filters} onChange={setFilters} />
      <div className="p-8 space-y-5">
        <div className="flex gap-4">
          <div className="card p-5 flex-1"><div className="text-xs uppercase text-slate2">Total Revenue at Risk</div><div className="font-display text-3xl text-rust mt-1">{fmtMoney(totalRisk)}</div></div>
          <div className="card p-5 flex-1"><div className="text-xs uppercase text-slate2">SKU·DC with a Gap</div><div className="font-display text-3xl mt-1">{gaps}<span className="text-lg text-slate2">/{rows.length}</span></div></div>
        </div>
        <div className="card p-5"><Grid rows={rows} columns={cols} height={520} /></div>
      </div>
    </>
  )
}
