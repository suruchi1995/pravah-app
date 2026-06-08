import { useState } from 'react'
import { api } from '../api'
 import { ScenarioNote } from '../context/ScenarioContext.jsx'
import { useAsync, PageHeader, Grid, Loading, ErrorBox, fmtPct } from '../components/ui'
import { FilterBar, rowPasses } from '../components/FilterBar'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine, Legend } from 'recharts'

const COLORS = ['#2E5C8A', '#b5544a', '#5b8a72', '#c98a3c', '#7c5cbf', '#3c8c9c']

export default function Capacity() {
  const { loading, data, error } = useAsync(() => api.capacity())
  const [filters, setFilters] = useState({ items: [], locations: [], periods: [] })
  if (loading) return <><PageHeader title="Capacity Planning" /><Loading /></>
  if (error) return <ErrorBox msg={error} />

  const cfg = {
    items: [...new Set(data.map(r => r.resource_code))].sort(),
    periods: [...new Set(data.map(r => r.period))].sort(),
  }
  const rows = data.filter(r => rowPasses(r, filters, { itemKey: 'resource_code', locKey: '_none', perKey: 'period' }))

  // R2-24: time on X-axis. One line per resource, utilisation % over periods.
  const periods = [...new Set(rows.map(r => r.period))].sort()
  const resources = [...new Set(rows.map(r => r.resource_code))].sort()
  const chartData = periods.map(p => {
    const row = { period: p.slice(0, 7) }
    resources.forEach(res => {
      const rec = rows.find(r => r.period === p && r.resource_code === res)
      if (rec) row[res] = Math.round(rec.utilization * 100)
    })
    return row
  })

  const barColor = s => s === 'OVERLOADED' ? '#b5544a' : s === 'TIGHT' ? '#c98a3c' : '#5b8a72'
  const statusCell = p => <span style={{ color: barColor(p.value), fontWeight: 600 }}>{p.value}</span>
  const cols = [
    { field: 'resource_code', headerName: 'Resource' },
    { field: 'period', headerName: 'Period', valueFormatter: p => p.value.slice(0,7) },
    { field: 'load_hours', headerName: 'Load (h)', valueFormatter: p => Math.round(p.value) },
    { field: 'available_hours', headerName: 'Available (h)', valueFormatter: p => Math.round(p.value) },
    { field: 'utilization', headerName: 'Utilisation', valueFormatter: p => fmtPct(p.value) },
    { field: 'constraint_status', headerName: 'Status', cellRenderer: statusCell },
  ]
  return (
    <>
      <PageHeader title="Capacity Planning" subtitle="Finite-capacity load over time. Above 100% = overloaded; that resource is the binding constraint the optimizer must plan around." />
      <FilterBar config={{ items: cfg.items, periods: cfg.periods }} value={filters} onChange={setFilters} />
      <ScenarioNote page="capacity" />
      <div className="p-8 space-y-6">
        <div className="card p-6">
          <h3 className="font-display text-xl mb-4">Utilisation over time — by resource</h3>
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={chartData} margin={{ left: 10, right: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eef2f6" />
              <XAxis dataKey="period" tick={{ fontSize: 11, fill: '#475569' }} />
              <YAxis tick={{ fontSize: 12, fill: '#475569' }} tickFormatter={v => v + '%'} />
              <Tooltip formatter={v => v + '%'} />
              <Legend />
              <ReferenceLine y={100} stroke="#b5544a" strokeDasharray="4 4" label={{ value: 'capacity 100%', fontSize: 11, fill: '#b5544a' }} />
              <ReferenceLine y={85} stroke="#c98a3c" strokeDasharray="3 3" />
              {resources.map((res, i) => (
                <Line key={res} type="monotone" dataKey={res} stroke={COLORS[i % COLORS.length]} strokeWidth={2} dot={{ r: 3 }} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="card p-5"><Grid rows={rows} columns={cols} /></div>
      </div>
    </>
  )
}
