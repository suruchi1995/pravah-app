import { useState } from 'react'
import { api } from '../api'
import { useAsync, PageHeader, Grid, Loading, ErrorBox } from '../components/ui'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts'

const FGS = ['FG001','FG002','FG003','FG004','FG005','FG006','FG007','FG008','FG009','FG010']

export default function Netting() {
  const [item, setItem] = useState('FG001')
  const { loading, data, error } = useAsync(() => api.netting('apex', item), [item])
  if (loading) return <><PageHeader title="Netting Workbench" /><Loading /></>
  if (error) return <ErrorBox msg={error} />
  const chart = data.map(r => ({ period: r.period.slice(0,7), Gross: Math.round(r.gross_requirement), Planned: Math.round(r.planned_order) }))
  const r0 = p => Math.round(p.value)
  const cols = [
    { field: 'period', headerName: 'Period', maxWidth: 120, valueFormatter: p => p.value.slice(0,7) },
    { field: 'gross_requirement', headerName: 'Gross', valueFormatter: r0 },
    { field: 'safety_stock', headerName: 'Safety', valueFormatter: r0 },
    { field: 'on_hand', headerName: 'On Hand', valueFormatter: r0 },
    { field: 'scheduled_receipts', headerName: 'Receipts', valueFormatter: r0 },
    { field: 'net_requirement', headerName: 'Net', valueFormatter: r0 },
    { field: 'planned_order', headerName: 'Planned Order', valueFormatter: r0 },
    { field: 'reasoning', headerName: 'Reasoning', minWidth: 380, flex: 2 },
  ]
  return (
    <>
      <PageHeader title="Netting Workbench" subtitle="Time-phased MRP netting: gross + safety − on-hand − receipts, rounded up to MOQ.">
        <select value={item} onChange={e => setItem(e.target.value)} className="text-sm border border-[#d6deea] rounded-lg px-2 py-2">
          {FGS.map(s => <option key={s}>{s}</option>)}
        </select>
      </PageHeader>
      <div className="p-8 space-y-6">
        <div className="card p-6">
          <h3 className="font-display text-xl mb-4">{item} — gross requirement vs planned orders</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={chart}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eef2f6" vertical={false} />
              <XAxis dataKey="period" tick={{ fontSize: 11, fill: '#475569' }} />
              <YAxis tick={{ fontSize: 12, fill: '#475569' }} />
              <Tooltip /><Legend />
              <Bar dataKey="Gross" fill="#94a3b8" radius={[4,4,0,0]} />
              <Bar dataKey="Planned" fill="#2E5C8A" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="card p-5"><Grid rows={data} columns={cols} height={360} /></div>
      </div>
    </>
  )
}
