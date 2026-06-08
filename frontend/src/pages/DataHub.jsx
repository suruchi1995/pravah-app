import { useState } from 'react'
import { api } from '../api'
import { useAsync, PageHeader, Grid, Loading, ErrorBox } from '../components/ui'
import { FilterBar } from '../components/FilterBar'
import { Upload, RotateCcw, Download, CheckCircle2, XCircle } from 'lucide-react'

const TABS = [
  { key: 'items', label: 'Items' },
  { key: 'locations', label: 'Locations' },
  { key: 'suppliers', label: 'Suppliers' },
  { key: 'bom', label: 'BOM' },
  { key: 'sourcing', label: 'Sourcing & Lanes' },
  { key: 'inventory', label: 'Inventory' },
  { key: 'demand_history', label: 'Demand History' },
  { key: 'resources', label: 'Resources' },
]

const FRIENDLY_LABELS = {
  unit_price_or_cost: 'Price per Unit (₹)',
  expiry_days: 'Shelf Life (days)',
  item_type: 'Type',
  from: 'From',
  to: 'To',
  kind: 'Relationship',
  lead_time_days: 'Lead Time (days)',
  min_lot_size: 'Min Lot Size',
  min_lot_uom: 'Min Lot UOM',
  hours_per_month: 'Capacity (hrs/mo)',
  usage_qty: 'Usage Qty (per parent UOM)',
  on_hand_qty: 'On-Hand Qty',
  supplier_code: 'Supplier',
  item_code: 'Item',
  location_code: 'Location',
  from_location: 'From',
  to_location: 'To',
  transport_mode: 'Transport Mode',
  unit_price: 'Unit Price (₹)',
  moq: 'MOQ',
  reliability: 'Reliability',
}

function friendlyCol(key) {
  return FRIENDLY_LABELS[key] || key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

export default function DataHub() {
  const [table, setTable] = useState('items')
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [filters, setFilters] = useState({ items: [], locations: [], periods: [] })

  // "sourcing" tab merges supplier-item mapping + supply lanes into one view
  const data = useAsync(async () => {
    if (table === 'sourcing') {
      const [sim, lanes] = await Promise.all([
        api.master('supplier_item_mapping'), api.lanes(),
      ])
      // unify into one shape: source/from -> item -> to + transmode + lead + moq
      const simRows = (sim || []).map(r => ({
        item_code: r.item_code, from: r.supplier_code, to: '(plant)',
        transport_mode: '—', lead_time_days: r.lead_time_days, moq: r.moq,
        unit_price: r.unit_price, kind: 'Supplier→Item',
      }))
      const laneRows = (lanes || []).map(r => ({
        item_code: r.item_code || '(all)', from: r.from_location, to: r.to_location,
        transport_mode: r.transport_mode, lead_time_days: r.lead_time_days,
        moq: r.min_lot_size, unit_price: null, kind: 'Lane',
      }))
      return [...laneRows, ...simRows]
    }
    return api.master(table)
  }, [table, result])

  async function onFile(e) {
    const f = e.target.files?.[0]; if (!f) return
    setBusy(true); setResult(null)
    try { setResult(await api.upload(f, 'apex')) }
    catch (err) { setResult({ ok: false, errors: [{ sheet: '-', message: err.message }] }) }
    setBusy(false); e.target.value = ''
  }

  async function reset() {
    setBusy(true); setResult(null)
    try {
      await api.resetDemo()
      setResult({ ok: true, message: 'Rebuilding all plans — about 30–90s. Please wait…' })
      const poll = setInterval(async () => {
        try {
          const st = await api.resetStatus()
          if (st.status === 'done') { clearInterval(poll); setBusy(false); setResult({ ok: true, message: 'Demo data rebuilt. All screens refreshed.' }) }
          else if (st.status?.startsWith('error')) { clearInterval(poll); setBusy(false); setResult({ ok: false, errors: [{ sheet: '-', message: st.status }] }) }
        } catch { }
      }, 4000)
    } catch (err) { setBusy(false); setResult({ ok: false, errors: [{ sheet: '-', message: err.message }] }) }
  }

  const allRows = data.data || []
  // global Item/Location filter (R2-6) — applies to any tab that has those columns
  const hasItem = allRows[0] && ('item_code' in allRows[0])
  const hasLoc = allRows[0] && ('location_code' in allRows[0] || 'to' in allRows[0] || 'from' in allRows[0])
  const rows = allRows.filter(r => {
    if (filters.items?.length) {
      const ic = r.item_code
      if (ic && !filters.items.includes(ic)) return false
    }
    if (filters.locations?.length) {
      const locVals = [r.location_code, r.to, r.from].filter(Boolean)
      if (locVals.length && !locVals.some(v => filters.locations.includes(v))) return false
    }
    return true
  })
  const itemOpts = [...new Set(allRows.map(r => r.item_code).filter(Boolean))].sort()
  const locOpts = [...new Set(allRows.flatMap(r => [r.location_code, r.to, r.from]).filter(Boolean))].sort()
  const filterCfg = (hasItem || hasLoc) ? {
    ...(hasItem ? { items: itemOpts } : {}),
    ...(hasLoc ? { locations: locOpts } : {}),
  } : null

  const rawCols = (rows && rows[0]) ? Object.keys(rows[0]) : []
  const cols = rawCols.map(k => ({ field: k, headerName: friendlyCol(k) }))

  return (
    <>
      <PageHeader title="Data Hub" subtitle="Upload your planning workbook. Strict validation rejects anything that would break the plan, and tells you exactly where.">
        <a href={api.templateUrl} className="flex items-center gap-2 text-sm px-3 py-2 rounded-lg border border-[#d6deea] text-brand hover:bg-brand/5">
          <Download size={16} /> Template
        </a>
        <label className="flex items-center gap-2 text-sm px-3 py-2 rounded-lg bg-brand text-white cursor-pointer hover:bg-branddk">
          <Upload size={16} /> Upload Excel
          <input type="file" accept=".xlsx" className="hidden" onChange={onFile} />
        </label>
        <button onClick={reset} disabled={busy} className="flex items-center gap-2 text-sm px-3 py-2 rounded-lg border border-[#d6deea] hover:bg-mist disabled:opacity-50">
          <RotateCcw size={16} /> {busy ? 'Working…' : 'Reset demo'}
        </button>
      </PageHeader>

      <div className="p-8 space-y-5">
        {result?.ok && (
          <div className="card p-4 flex items-start gap-3 border-l-4 border-sage">
            <CheckCircle2 className="text-sage mt-0.5" size={20} />
            <div><div className="font-semibold">{result.message}</div>
              {result.warnings?.length > 0 && <ul className="text-sm text-slate2 mt-2 list-disc ml-5">{result.warnings.map((w, i) => <li key={i}><b>{w.sheet}:</b> {w.message}</li>)}</ul>}
            </div>
          </div>
        )}
        {result && !result.ok && (
          <div className="card p-4 border-l-4 border-rust">
            <div className="flex items-center gap-2 text-rust font-semibold mb-2"><XCircle size={20} /> Upload rejected — {result.errors?.length} issue(s)</div>
            <div className="max-h-64 overflow-auto text-sm">
              <table className="w-full"><thead><tr className="text-left text-slate2"><th className="py-1 pr-4">Sheet</th><th className="py-1 pr-4">Row</th><th className="py-1">Problem</th></tr></thead>
                <tbody>{result.errors?.map((e, i) => <tr key={i} className="border-t border-[#eef2f6]"><td className="py-1 pr-4 font-mono text-xs">{e.sheet}</td><td className="py-1 pr-4">{e.row ?? '—'}</td><td className="py-1">{e.message}</td></tr>)}</tbody>
              </table>
            </div>
          </div>
        )}

        <div className="card p-5">
          <div className="flex gap-2 mb-4 flex-wrap">
            {TABS.map(t => (
              <button key={t.key} onClick={() => { setTable(t.key); setFilters({ items: [], locations: [], periods: [] }) }}
                className={`text-sm px-3 py-1.5 rounded-lg border ${table === t.key ? 'bg-brand text-white border-brand' : 'border-[#d6deea] text-slate2 hover:bg-mist'}`}>
                {t.label}
              </button>
            ))}
          </div>
          {filterCfg && (
            <div className="mb-4 -mx-5">
              <FilterBar config={filterCfg} value={filters} onChange={setFilters} />
            </div>
          )}
          {data.loading ? <Loading /> : <Grid rows={rows} columns={cols} height={480} />}
        </div>
      </div>
    </>
  )
}
