import { useState } from 'react'
import { api } from '../api'
 import { ScenarioNote } from '../context/ScenarioContext.jsx'
import { useAsync, PageHeader, Grid, Loading, ErrorBox, fmtMoney, fmtPct } from '../components/ui'
import { FilterBar, rowPasses, deriveOptions } from '../components/FilterBar'
import { ChangeRequestModal, canEditData } from '../components/ChangeRequestModal'
import { SlidersHorizontal } from 'lucide-react'

export default function Handshake() {
  const { loading, data, error } = useAsync(() => api.handshake())
  const [filters, setFilters] = useState({ items: [], locations: [], periods: [] })
  const [ovOpen, setOvOpen] = useState(false)
  const [ovConfirmOpen, setOvConfirmOpen] = useState(false)
  // override form state
  const [ov, setOv] = useState({ item_code: '', location_code: '', period: '', type: 'uplift_pct', value: '', reason: '' })
  if (loading) return <><PageHeader title="Demand–Supply Handshake" /><Loading /></>
  if (error) return <ErrorBox msg={error} />

  const cfg = deriveOptions(data, { item: true, location: true, period: true })
  const rows = data.filter(r => rowPasses(r, filters))
  const totalRisk = rows.reduce((a, r) => a + r.revenue_at_risk, 0)
  const gaps = rows.filter(r => r.gap_qty > 0).length
  const items = [...new Set(data.map(r => r.item_code))].sort()
  const locs = [...new Set(data.map(r => r.location_code))].sort()
  const periods = [...new Set(data.map(r => r.period))].sort()
  const editable = canEditData()

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

  const change = {
    change_type: 'demand_override',
    target: `Demand override: ${ov.item_code} @ ${ov.location_code}, ${ov.period?.slice(0,7)}`,
    payload: {
      item_code: ov.item_code, location_code: ov.location_code, period: ov.period,
      override_qty: parseFloat(ov.value) || 0, override_type: ov.type, reason: ov.reason,
    },
    old_value: 'statistical forecast',
    new_value: ov.type === 'uplift_pct' ? `+${ov.value}% uplift` : `${ov.value} units (absolute)`,
  }
  const overrideValid = ov.item_code && ov.location_code && ov.period && ov.value

  return (
    <>
      <PageHeader title="Demand–Supply Handshake" subtitle="Where demand outruns available supply — quantified as revenue and margin at risk, with a recommended action.">
        <button onClick={() => setOvOpen(true)} className="flex items-center gap-2 text-sm px-3 py-2 rounded-lg bg-brand text-white hover:bg-branddk">
          <SlidersHorizontal size={15} /> Override demand
        </button>
      </PageHeader>
      <FilterBar config={cfg} value={filters} onChange={setFilters} />
      <ScenarioNote page="handshake" />

      {/* Override builder modal */}
      {ovOpen && !ovConfirmOpen && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={() => setOvOpen(false)}>
          <div className="card p-6 max-w-md w-full" onClick={e => e.stopPropagation()}>
            <h3 className="font-display text-xl mb-4">Override demand</h3>
            <p className="text-xs text-slate2 mb-4">Adjust the consensus demand for a SKU at a DC. This is approval-gated — it re-plans only after sign-off.</p>
            <div className="space-y-3">
              <div className="grid grid-cols-3 gap-2">
                <select value={ov.item_code} onChange={e => setOv(o => ({ ...o, item_code: e.target.value }))} className="text-sm border border-[#d6deea] rounded-lg px-2 py-2">
                  <option value="">Item…</option>{items.map(i => <option key={i}>{i}</option>)}
                </select>
                <select value={ov.location_code} onChange={e => setOv(o => ({ ...o, location_code: e.target.value }))} className="text-sm border border-[#d6deea] rounded-lg px-2 py-2">
                  <option value="">DC…</option>{locs.map(l => <option key={l}>{l}</option>)}
                </select>
                <select value={ov.period} onChange={e => setOv(o => ({ ...o, period: e.target.value }))} className="text-sm border border-[#d6deea] rounded-lg px-2 py-2">
                  <option value="">Period…</option>{periods.map(p => <option key={p} value={p}>{p.slice(0,7)}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <select value={ov.type} onChange={e => setOv(o => ({ ...o, type: e.target.value }))} className="text-sm border border-[#d6deea] rounded-lg px-2 py-2">
                  <option value="uplift_pct">Uplift %</option>
                  <option value="absolute">Absolute qty</option>
                </select>
                <input type="number" value={ov.value} onChange={e => setOv(o => ({ ...o, value: e.target.value }))}
                  placeholder={ov.type === 'uplift_pct' ? 'e.g. 25' : 'e.g. 800'}
                  className="text-sm border border-[#d6deea] rounded-lg px-3 py-2" />
              </div>
              <input value={ov.reason} onChange={e => setOv(o => ({ ...o, reason: e.target.value }))}
                placeholder="Reason (e.g. promo launch)" className="w-full text-sm border border-[#d6deea] rounded-lg px-3 py-2" />
              <button disabled={!overrideValid} onClick={() => setOvConfirmOpen(true)}
                className="w-full text-sm py-2.5 rounded-lg bg-brand text-white hover:bg-branddk disabled:opacity-50">
                Review & submit
              </button>
            </div>
          </div>
        </div>
      )}

      <ChangeRequestModal
        open={ovOpen && ovConfirmOpen}
        onClose={() => { setOvOpen(false); setOvConfirmOpen(false) }}
        title="Submit demand override"
        change={change}
        canEdit={editable}
      />

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
