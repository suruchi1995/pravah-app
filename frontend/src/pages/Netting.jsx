import { useState } from 'react'
import { api } from '../api'
 import { ScenarioNote } from '../context/ScenarioContext.jsx'
import { useAsync, PageHeader, Grid, Loading, ErrorBox } from '../components/ui'
import { FilterBar, rowPasses } from '../components/FilterBar'
import { Info } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts'

const FGS = ['FG001','FG002','FG003','FG004','FG005','FG006','FG007','FG008','FG009','FG010']

export default function Netting() {
  const [item, setItem] = useState('FG001')
  const [filters, setFilters] = useState({ items: [], locations: [], periods: [] })
  const [showHelp, setShowHelp] = useState(false)
  const { loading, data, error } = useAsync(() => api.netting('apex', item), [item])
  if (loading) return <><PageHeader title="Netting Workbench" /><Loading /></>
  if (error) return <ErrorBox msg={error} />

  const periodCfg = { periods: [...new Set((data || []).map(r => r.period))].sort() }
  const rows = (data || []).filter(r => rowPasses(r, filters, { perKey: 'period' }))
  const chart = rows.map(r => ({ period: r.period.slice(0,7), Gross: Math.round(r.gross_requirement), Planned: Math.round(r.planned_order) }))
  const r0 = p => Math.round(p.value)
  const cols = [
    { field: 'period', headerName: 'Period', maxWidth: 120, valueFormatter: p => p.value.slice(0,7) },
    { field: 'gross_requirement', headerName: 'Gross Requirement', valueFormatter: r0 },
    { field: 'safety_stock', headerName: 'Safety Stock', valueFormatter: r0 },
    { field: 'on_hand', headerName: 'On Hand', valueFormatter: r0 },
    { field: 'scheduled_receipts', headerName: 'Scheduled Receipts', valueFormatter: r0 },
    { field: 'net_requirement', headerName: 'Net Requirement', valueFormatter: r0 },
    { field: 'planned_order', headerName: 'Planned Order', valueFormatter: r0 },
    { field: 'reasoning', headerName: 'Reasoning', minWidth: 380, flex: 2 },
  ]
  return (
    <>
      <PageHeader title="Netting Workbench" subtitle="Time-phased MRP netting: gross + safety − on-hand − receipts, rounded up to MOQ.">
        <button onClick={() => setShowHelp(h => !h)} className="flex items-center gap-1.5 text-sm px-3 py-2 rounded-lg border border-[#d6deea] text-slate2 hover:bg-mist">
          <Info size={15} /> What is this?
        </button>
        <select value={item} onChange={e => setItem(e.target.value)} className="text-sm border border-[#d6deea] rounded-lg px-2 py-2">
          {FGS.map(s => <option key={s}>{s}</option>)}
        </select>
      </PageHeader>
      <FilterBar config={periodCfg} value={filters} onChange={setFilters} />
      <ScenarioNote page="netting" />
      <div className="p-8 space-y-6">
        {showHelp && (
          <div className="card p-5 border-l-4 border-brand text-sm space-y-2">
            <p><b>What netting does:</b> for each period it computes how much new supply to order so demand and safety stock are covered.</p>
            <p><b>Formula:</b> Net requirement = Gross requirement + Safety stock − On-hand inventory − Scheduled receipts. Planned order = Net requirement rounded up to the MOQ.</p>
            <p><b>Where the inputs come from:</b></p>
            <ul className="list-disc ml-5 space-y-1">
              <li><b>Gross requirement</b> — from the demand plan (forecast ± override) for finished goods, or exploded BOM dependent demand for components.</li>
              <li><b>Scheduled receipts</b> — open purchase orders + in-progress production orders already expected to arrive (from the orders sheets; client-provided).</li>
              <li><b>On-hand</b> — current inventory (client-provided).</li>
              <li><b>Safety stock</b> — derived in Inventory Planning from demand variability + service level.</li>
              <li><b>Planned order</b> — what the system recommends you create (new PO or production order).</li>
            </ul>
          </div>
        )}
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
        <div className="card p-5"><Grid rows={rows} columns={cols} height={360} /></div>
      </div>
    </>
  )
}
