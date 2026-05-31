import { api } from '../api'
import { useAsync, PageHeader, Grid, Loading, ErrorBox, fmtPct } from '../components/ui'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine, Cell } from 'recharts'

export default function Capacity() {
  const { loading, data, error } = useAsync(() => api.capacity())
  if (loading) return <><PageHeader title="Capacity Planning" /><Loading /></>
  if (error) return <ErrorBox msg={error} />

  const periods = [...new Set(data.map(r => r.period))].sort()
  const p0 = periods[0]
  const first = data.filter(r => r.period === p0).map(r => ({
    resource: r.resource_code.replace('_LINE', '').replace('_01', '1').replace('_02', '2'),
    util: Math.round(r.utilization * 100), status: r.constraint_status,
  }))
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
      <PageHeader title="Capacity Planning" subtitle="Finite-capacity load by resource. The binding constraint sets the ceiling the optimizer must plan around." />
      <div className="p-8 space-y-6">
        <div className="card p-6">
          <h3 className="font-display text-xl mb-4">Resource utilisation — {p0?.slice(0,7)}</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={first} margin={{ left: 10, right: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eef2f6" vertical={false} />
              <XAxis dataKey="resource" tick={{ fontSize: 11, fill: '#475569' }} />
              <YAxis tick={{ fontSize: 12, fill: '#475569' }} tickFormatter={v => v + '%'} domain={[0, 'dataMax']} />
              <Tooltip formatter={v => v + '%'} />
              <ReferenceLine y={100} stroke="#b5544a" strokeDasharray="4 4" label={{ value: 'capacity', fontSize: 11, fill: '#b5544a' }} />
              <ReferenceLine y={85} stroke="#c98a3c" strokeDasharray="3 3" />
              <Bar dataKey="util" radius={[5,5,0,0]}>
                {first.map((e, i) => <Cell key={i} fill={barColor(e.status)} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="card p-5"><Grid rows={data} columns={cols} /></div>
      </div>
    </>
  )
}
