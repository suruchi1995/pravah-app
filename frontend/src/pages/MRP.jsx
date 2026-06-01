import { useState } from 'react'
import { api } from '../api'
import { useAsync, PageHeader, Grid, Loading, ErrorBox } from '../components/ui'
import { FilterBar, rowPasses, deriveOptions } from '../components/FilterBar'

export default function MRP() {
  const { loading, data, error } = useAsync(() => api.mrp())
  const [filters, setFilters] = useState({ items: [], locations: [], periods: [] })
  if (loading) return <><PageHeader title="Supply Planning (MRP)" /><Loading /></>
  if (error) return <ErrorBox msg={error} />
  const cfg = deriveOptions(data, { item: true, location: false, period: true })
  const rows = data.filter(r => rowPasses(r, filters))
  const srcCell = p => <span style={{ color: p.value === 'make' ? '#2E5C8A' : '#c98a3c', fontWeight: 600 }}>{p.value}</span>
  const cols = [
    { field: 'level', headerName: 'BOM Level', maxWidth: 110 },
    { field: 'item_code', headerName: 'Component', maxWidth: 130 },
    { field: 'source', headerName: 'Make/Buy', maxWidth: 120, cellRenderer: srcCell },
    { field: 'period', headerName: 'Period', maxWidth: 120, valueFormatter: p => p.value.slice(0,7) },
    { field: 'gross_requirement', headerName: 'Gross Req', valueFormatter: p => Math.round(p.value) },
    { field: 'net_requirement', headerName: 'Net Req', valueFormatter: p => Math.round(p.value) },
  ]
  return (
    <>
      <PageHeader title="Supply Planning — MRP Explosion" subtitle="Finished-good plans exploded through the multi-level BOM into dependent demand for semi-finished, raw and packaging materials." />
      <FilterBar config={cfg} value={filters} onChange={setFilters} />
      <div className="p-8"><div className="card p-5"><Grid rows={rows} columns={cols} /></div></div>
    </>
  )
}
