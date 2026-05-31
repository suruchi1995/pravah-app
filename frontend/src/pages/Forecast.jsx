import { useState } from 'react'
import { api } from '../api'
import { useAsync, PageHeader, Loading, ErrorBox } from '../components/ui'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend, ReferenceLine } from 'recharts'

const FGS = ['FG001', 'FG002', 'FG003', 'FG004', 'FG005', 'FG006', 'FG007', 'FG008', 'FG009', 'FG010']
const DCS = ['DC_DEL', 'DC_MUM', 'DC_BLR']

export default function Forecast() {
  const [item, setItem] = useState('FG001')
  const [loc, setLoc] = useState('DC_DEL')
  const hist = useAsync(() => api.master('demand_history'), [])
  const fc = useAsync(() => api.forecast('apex', item, loc), [item, loc])

  if (hist.loading || fc.loading) return <><PageHeader title="Forecast Workbench" /><Loading /></>
  if (fc.error) return <ErrorBox msg={fc.error} />

  const h = (hist.data || []).filter(r => r.item_code === item && r.location_code === loc)
    .map(r => ({ period: r.period.slice(0, 7), actual: r.quantity }))
  const f = (fc.data || []).map(r => ({ period: r.period.slice(0, 7), forecast: Math.round(r.forecast_qty) }))
  const merged = [...h, ...f]
  const meta = fc.data?.[0]

  return (
    <>
      <PageHeader title="Forecast Workbench" subtitle="Five models compete on backtested accuracy; the winner is auto-selected per series.">
        <select value={item} onChange={e => setItem(e.target.value)} className="text-sm border border-[#d6deea] rounded-lg px-2 py-2">
          {FGS.map(s => <option key={s}>{s}</option>)}
        </select>
        <select value={loc} onChange={e => setLoc(e.target.value)} className="text-sm border border-[#d6deea] rounded-lg px-2 py-2">
          {DCS.map(s => <option key={s}>{s}</option>)}
        </select>
      </PageHeader>
      <div className="p-8 space-y-6">
        {meta && (
          <div className="flex gap-3 flex-wrap">
            <span className="px-3 py-1.5 rounded-lg bg-brand/10 text-brand text-sm font-medium">Model: {meta.selected_model}</span>
            <span className="px-3 py-1.5 rounded-lg bg-sage/10 text-sage text-sm font-medium">MAPE: {meta.mape}%</span>
            <span className="px-3 py-1.5 rounded-lg bg-amber2/10 text-amber2 text-sm font-medium">Bias: {meta.bias}</span>
          </div>
        )}
        <div className="card p-6">
          <h3 className="font-display text-xl mb-1">{item} @ {loc}</h3>
          <p className="text-sm text-slate2 mb-4">{meta?.reasoning}</p>
          <ResponsiveContainer width="100%" height={360}>
            <LineChart data={merged} margin={{ left: 10, right: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eef2f6" vertical={false} />
              <XAxis dataKey="period" tick={{ fontSize: 11, fill: '#475569' }} />
              <YAxis tick={{ fontSize: 12, fill: '#475569' }} />
              <Tooltip />
              <Legend />
              {h.length > 0 && <ReferenceLine x={h[h.length - 1].period} stroke="#c98a3c" strokeDasharray="4 4" label={{ value: 'forecast →', fontSize: 11, fill: '#c98a3c' }} />}
              <Line type="monotone" dataKey="actual" stroke="#2E5C8A" strokeWidth={2} dot={false} name="History" />
              <Line type="monotone" dataKey="forecast" stroke="#b5544a" strokeWidth={2.5} strokeDasharray="5 4" dot={{ r: 3 }} name="Forecast" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </>
  )
}
