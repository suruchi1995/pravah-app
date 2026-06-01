import { useState } from 'react'
import { api } from '../api'
import { useAsync, PageHeader, Loading, ErrorBox, fmtMoney, fmtPct } from '../components/ui'
import { FilterBar } from '../components/FilterBar'

export default function Network() {
  const locs = useAsync(() => api.master('locations'))
  const sups = useAsync(() => api.master('suppliers'))
  const hs = useAsync(() => api.handshake())
  const seg = useAsync(() => api.segmentation())
  const [filters, setFilters] = useState({ items: [], locations: [], periods: [] })

  if (locs.loading || sups.loading || hs.loading) return <><PageHeader title="Supply Chain Network" /><Loading /></>
  if (locs.error) return <ErrorBox msg={locs.error} />

  const itemOptions = [...new Set((seg.data || []).map(s => s.item_code))].sort()
  const activeItems = filters.items || []

  // aggregate handshake by DC, filtered by selected items
  const hsFiltered = (hs.data || []).filter(r => activeItems.length === 0 || activeItems.includes(r.item_code))
  const byDC = {}
  for (const r of hsFiltered) {
    const d = byDC[r.location_code] || { demand: 0, supply: 0, gap: 0, risk: 0 }
    d.demand += r.demand_qty; d.supply += r.available_supply_qty
    d.gap += r.gap_qty; d.risk += r.revenue_at_risk
    byDC[r.location_code] = d
  }

  const plants = (locs.data || []).filter(l => l.location_type === 'Plant')
  const dcs = (locs.data || []).filter(l => l.location_type === 'DC')
  const suppliers = sups.data || []

  // layout coordinates
  const colX = { sup: 60, plant: 290, dc: 520 }
  const nodeW = 150, nodeH = 46, gapY = 64, topY = 90
  const yFor = (i, n, total) => topY + i * gapY + (total - n) * gapY / 2 // simple stacking

  const supNodes = suppliers.map((s, i) => ({ ...s, x: colX.sup, y: topY + i * 52, kind: 'sup' }))
  const plantNodes = plants.map((p, i) => ({ ...p, x: colX.plant, y: topY + 40 + i * 70, kind: 'plant' }))
  const dcNodes = dcs.map((d, i) => ({ ...d, x: colX.dc, y: topY + i * 80, kind: 'dc', m: byDC[d.location_code] }))

  const svgH = Math.max(supNodes.length * 52, dcNodes.length * 80) + topY + 80

  const dcColor = m => {
    if (!m || m.demand === 0) return '#5b8a72'
    const fill = m.supply / m.demand
    return fill >= 0.85 ? '#5b8a72' : fill >= 0.6 ? '#c98a3c' : '#b5544a'
  }

  function Node({ n }) {
    const fill = n.kind === 'dc' ? dcColor(n.m) : n.kind === 'plant' ? '#2E5C8A' : '#c98a3c'
    const bg = n.kind === 'dc' ? '#fff' : '#fff'
    return (
      <g>
        <rect x={n.x} y={n.y} width={nodeW} height={nodeH} rx={9} fill={bg} stroke={fill} strokeWidth={1.5} />
        <rect x={n.x} y={n.y} width={5} height={nodeH} rx={2} fill={fill} />
        <text x={n.x + 16} y={n.y + 19} fontSize={12.5} fontWeight={600} fill="#1a2332">
          {n.location_name || n.supplier_name}
        </text>
        {n.kind === 'dc' && n.m && (
          <text x={n.x + 16} y={n.y + 36} fontSize={10.5} fill="#475569">
            fill {Math.round((n.m.supply / (n.m.demand || 1)) * 100)}% · risk {n.m.risk >= 1000 ? '₹' + Math.round(n.m.risk / 1000) + 'k' : '₹' + Math.round(n.m.risk)}
          </text>
        )}
        {n.kind === 'sup' && (
          <text x={n.x + 16} y={n.y + 36} fontSize={10.5} fill="#475569">
            lead {n.lead_time_days}d · MOQ {n.moq}
          </text>
        )}
        {n.kind === 'plant' && (
          <text x={n.x + 16} y={n.y + 36} fontSize={10.5} fill="#475569">mix · fill · pack</text>
        )}
      </g>
    )
  }

  return (
    <>
      <PageHeader title="Supply Chain Network" subtitle="Suppliers → plants → distribution centres. Node colour shows fill rate; pick items to focus the view." />
      <FilterBar config={{ items: itemOptions }} value={filters} onChange={setFilters} />
      <div className="p-8 space-y-5">
        <div className="flex gap-3 text-xs text-slate2 items-center">
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm" style={{ background: '#c98a3c' }} />Supplier</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm" style={{ background: '#2E5C8A' }} />Plant</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm" style={{ background: '#5b8a72' }} />DC healthy</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm" style={{ background: '#c98a3c' }} />DC tight</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm" style={{ background: '#b5544a' }} />DC short</span>
        </div>
        <div className="card p-4 overflow-auto">
          <svg width="100%" viewBox={`0 0 700 ${svgH}`} style={{ minWidth: 640 }}>
            <text x={colX.sup} y={60} fontSize={12} fontWeight={700} fill="#1F3A5F">SUPPLIERS</text>
            <text x={colX.plant} y={60} fontSize={12} fontWeight={700} fill="#1F3A5F">PLANTS</text>
            <text x={colX.dc} y={60} fontSize={12} fontWeight={700} fill="#1F3A5F">DISTRIBUTION</text>
            {/* edges supplier -> plant */}
            {supNodes.map(s => plantNodes.map(p => (
              <line key={s.supplier_code + p.location_code} x1={s.x + nodeW} y1={s.y + nodeH / 2}
                x2={p.x} y2={p.y + nodeH / 2} stroke="#d6deea" strokeWidth={0.8} />
            )))}
            {/* edges plant -> dc */}
            {plantNodes.map(p => dcNodes.map(d => (
              <line key={p.location_code + d.location_code} x1={p.x + nodeW} y1={p.y + nodeH / 2}
                x2={d.x} y2={d.y + nodeH / 2}
                stroke={dcColor(d.m) === '#b5544a' ? '#b5544a' : '#d6deea'}
                strokeWidth={dcColor(d.m) === '#b5544a' ? 1.4 : 0.8} />
            )))}
            {supNodes.map(n => <Node key={n.supplier_code} n={n} />)}
            {plantNodes.map(n => <Node key={n.location_code} n={n} />)}
            {dcNodes.map(n => <Node key={n.location_code} n={n} />)}
          </svg>
        </div>
        <div className="grid grid-cols-3 gap-4">
          {dcNodes.map(d => (
            <div key={d.location_code} className="card p-4">
              <div className="font-display text-lg">{d.location_name}</div>
              {d.m ? (
                <div className="text-sm text-slate2 mt-1 space-y-0.5">
                  <div>Demand: {Math.round(d.m.demand)}</div>
                  <div>Supply: {Math.round(d.m.supply)}</div>
                  <div>Fill: {fmtPct(d.m.supply / (d.m.demand || 1))}</div>
                  <div className="text-rust">Risk: {fmtMoney(d.m.risk)}</div>
                </div>
              ) : <div className="text-sm text-slate2 mt-1">No demand in selection</div>}
            </div>
          ))}
        </div>
      </div>
    </>
  )
}
