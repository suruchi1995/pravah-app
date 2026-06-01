import { useState } from 'react'
import { api } from '../api'
import { useAsync, PageHeader, Grid, Loading, ErrorBox } from '../components/ui'
import { FilterBar, rowPasses, deriveOptions } from '../components/FilterBar'

export default function Inventory() {
  const { loading, data, error } = useAsync(() => api.inventoryTargets())
  const [filters, setFilters] = useState({ items: [], locations: [], periods: [] })
  if (loading) return <><PageHeader title="Inventory Planning" /><Loading /></>
  if (error) return <ErrorBox msg={error} />
  const cfg = deriveOptions(data, { item: true, location: true, period: false })
  const rows = data.filter(r => rowPasses(r, filters))
  const r0 = p => Math.round(p.value)
  const cols = [
    { field: 'item_code', headerName: 'SKU', maxWidth: 100 },
    { field: 'location_code', headerName: 'DC', maxWidth: 100 },
    { field: 'avg_monthly_demand', headerName: 'Avg Demand', valueFormatter: r0 },
    { field: 'safety_stock', headerName: 'Safety Stock', valueFormatter: r0 },
    { field: 'reorder_point', headerName: 'Reorder Point', valueFormatter: r0 },
    { field: 'target_inventory', headerName: 'Target (order-up-to)', valueFormatter: r0 },
    { field: 'days_cover', headerName: 'Days Cover', maxWidth: 120 },
    { field: 'reasoning', headerName: 'Logic', minWidth: 380, flex: 2 },
  ]
  return (
    <>
      <PageHeader title="Inventory Planning" subtitle="Safety stock, reorder point and order-up-to targets, derived from service levels and demand variability." />
      <FilterBar config={cfg} value={filters} onChange={setFilters} />
      <div className="p-8"><div className="card p-5"><Grid rows={rows} columns={cols} /></div></div>
    </>
  )
}
