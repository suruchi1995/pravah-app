import { api } from '../api'
import { useAsync, PageHeader, Kpi, Loading, ErrorBox, fmtMoney, fmtPct } from '../components/ui'
import { IndianRupee, Target, Activity, AlertTriangle } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'

export default function Dashboard() {
  const s = useAsync(() => api.summary())
  const hs = useAsync(() => api.handshake())
  if (s.loading || hs.loading) return <><PageHeader title="Control Tower" /><Loading /></>
  if (s.error) return <ErrorBox msg={s.error} />

  const d = s.data
  const topRisk = (hs.data || []).slice(0, 8).map(r => ({
    name: `${r.item_code}·${r.location_code.replace('DC_', '')}`,
    risk: Math.round(r.revenue_at_risk),
  }))

  return (
    <>
      <PageHeader title="Control Tower"
        subtitle="Network-wide signal: where demand outruns supply, what it costs, and how plans respond." />
      <div className="p-8 space-y-6">
        <div className="flex gap-4 flex-wrap">
          <Kpi label="Finished Goods" value={d.finished_goods} sub="active SKUs planned" tone="brand" icon={Target} />
          <Kpi label="Revenue at Risk" value={fmtMoney(d.total_revenue_at_risk)} sub="first plan period" tone="rust" icon={IndianRupee} />
          <Kpi label="Avg Fill Rate" value={fmtPct(d.avg_fill_rate)} sub="demand coverage" tone="amber" icon={Activity} />
          <Kpi label="Forecast MAPE" value={d.avg_mape + '%'} sub="auto-selected models" tone="sage" icon={Activity} />
          <Kpi label="Bottlenecks" value={d.capacity_bottlenecks} sub="constrained resources" tone="rust" icon={AlertTriangle} />
        </div>

        <div className="card p-6">
          <h3 className="font-display text-xl mb-1">Revenue at Risk — top exposures</h3>
          <p className="text-sm text-slate2 mb-4">Gap × selling price, by SKU and distribution centre.</p>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={topRisk} margin={{ left: 10, right: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eef2f6" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#475569' }} />
              <YAxis tick={{ fontSize: 12, fill: '#475569' }} tickFormatter={v => '₹' + (v / 1000).toFixed(0) + 'k'} />
              <Tooltip formatter={v => fmtMoney(v)} />
              <Bar dataKey="risk" fill="#b5544a" radius={[5, 5, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card p-6">
          <h3 className="font-display text-xl mb-3">Optimization scenarios</h3>
          <div className="grid grid-cols-3 gap-4">
            {Object.entries(d.scenarios || {}).map(([k, v]) => (
              <div key={k} className="border border-[#e7ecf2] rounded-xl p-4">
                <div className="text-xs uppercase tracking-wide text-slate2">{k.replace('_', ' ')}</div>
                <div className="font-display text-lg mt-1 capitalize">{v.status.toLowerCase()}</div>
                <div className="text-xs text-slate2 mt-1">objective {Number(v.objective_value).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  )
}
