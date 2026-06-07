import { useState } from 'react'
import { api } from '../api'
import { useAsync, PageHeader, Loading, ErrorBox, fmtMoney, fmtPct } from '../components/ui'
import { FilterBar } from '../components/FilterBar'

export default function Network() {
  const locs = useAsync(() => api.master('locations'))
  const sups = useAsync(() => api.master('suppliers'))
  const hs = useAsync(() => api.handshake())
  const seg = useAsync(() => api.segmentation())
  const lanes = useAsync(() => api.lanes())
  const [filters, setFilters] = useState({ items: [], locations: [], periods: [], zones: [] })

  if (locs.loading || sups.loading || hs.loading || lanes.loading) return <><PageHeader title="Supply Chain Network" /><Loading /></>
  if (locs.error) return <ErrorBox msg={locs.error} />

  const allLanes = lanes.data || []
  const itemOptions = [...new Set((seg.data || []).map(s => s.item_code))].sort()
  const locationOptions = (locs.data || []).map(l => l.location_code)
  const zoneOptions = [...new Set((locs.data || []).map(l => l.zone).filter(Boolean))]
  const locZoneMap = Object.fromEntries((locs.data || []).map(l => [l.location_code, l.zone]))
  const activeItems = filters.items || []
  const activeZones = filters.zones || []
  const activeLocs = filters.locations || []

  // filter HS
  const hsFiltered = (hs.data || []).filter(r => {
    if (activeItems.length && !activeItems.includes(r.item_code)) return false
    if (activeLocs.length && !activeLocs.includes(r.location_code)) return false
    if (activeZones.length && !activeZones.includes(locZoneMap[r.location_code])) return false
    return true
  })
  const byDC = {}
  for (const r of hsFiltered) {
    const d = byDC[r.location_code] || { demand: 0, supply: 0, gap: 0, risk: 0 }
    d.demand += r.demand_qty; d.supply += r.available_supply_qty
    d.gap += r.gap_qty; d.risk += r.revenue_at_risk
    byDC[r.location_code] = d
  }

  const plants = (locs.data || []).filter(l => l.location_type === 'Plant')
  const dcs = (locs.data || []).filter(l => l.location_type === 'DC').filter(l =>
    activeLocs.length ? activeLocs.includes(l.location_code) :
    activeZones.length ? activeZones.includes(locZoneMap[l.location_code]) : true
  )
  const suppliers = sups.data || []
  const nodeW = 150, nodeH = 46, topY = 90
  const supNodes = suppliers.map((s, i) => ({ ...s, x: 40, y: topY + i * 56, kind: 'sup' }))
  const plantNodes = plants.map((p, i) => ({ ...p, x: 270, y: topY + 30 + i * 72, kind: 'plant' }))
  const dcNodes = dcs.map((d, i) => ({ ...d, x: 500, y: topY + i * 80, kind: 'dc', m: byDC[d.location_code] }))
  const svgH = Math.max(supNodes.length * 56, dcNodes.length * 80, plantNodes.length * 72) + topY + 80
  const dcColor = m => { if (!m || m.demand === 0) return '#94a3b8'; const f = m.supply/m.demand; return f >= 0.85 ? '#5b8a72' : f >= 0.6 ? '#c98a3c' : '#b5544a' }

  // count lanes per pair
  const laneCountSupPlant = {}
  const laneCountPlantDC = {}
  allLanes.filter(l => activeItems.length ? activeItems.includes(l.item_code) || !l.item_code : true).forEach(l => {
    const k = `${l.from_location}-${l.to_location}`
    if (plants.some(p => p.location_code === l.to_location)) laneCountSupPlant[k] = (laneCountSupPlant[k]||0)+1
    if (dcs.some(d => d.location_code === l.to_location)) laneCountPlantDC[k] = (laneCountPlantDC[k]||0)+1
  })

  function Node({ n }) {
    const fill = n.kind === 'dc' ? dcColor(n.m) : n.kind === 'plant' ? '#2E5C8A' : '#c98a3c'
    return (
      <g>
        <rect x={n.x} y={n.y} width={nodeW} height={nodeH} rx={9} fill="#fff" stroke={fill} strokeWidth={1.5} />
        <rect x={n.x} y={n.y} width={5} height={nodeH} rx={2} fill={fill} />
        <text x={n.x+14} y={n.y+18} fontSize={12} fontWeight={600} fill="#1a2332">{n.location_name||n.supplier_name}</text>
        {n.kind==='dc' && n.m && <text x={n.x+14} y={n.y+34} fontSize={10} fill="#475569">fill {Math.round((n.m.supply/(n.m.demand||1))*100)}% · risk {n.m.risk>=1000?'₹'+Math.round(n.m.risk/1000)+'k':'₹'+Math.round(n.m.risk)}</text>}
        {n.kind==='sup' && <text x={n.x+14} y={n.y+34} fontSize={10} fill="#475569">{n.supplier_type}</text>}
        {n.kind==='plant' && <text x={n.x+14} y={n.y+34} fontSize={10} fill="#475569">{n.zone} · {n.state}</text>}
      </g>
    )
  }

  return (
    <>
      <PageHeader title="Supply Chain Network" subtitle="Suppliers → plants → DCs. Node colour = fill rate health. Lane thickness = number of item flows." />
      <FilterBar config={{ zones: zoneOptions, items: itemOptions, locations: locationOptions }} value={filters} onChange={setFilters} />
      <div className="p-8 space-y-5">
        <div className="flex gap-3 text-xs text-slate2 items-center flex-wrap">
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-[#c98a3c]" />Supplier</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-[#2E5C8A]" />Plant</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-[#5b8a72]" />DC healthy (≥85% fill)</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-[#c98a3c]" />DC tight</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-[#b5544a]" />DC short</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-[#94a3b8]" />DC no demand</span>
        </div>
        <div className="card p-4 overflow-auto">
          <svg width="100%" viewBox={`0 0 700 ${svgH}`} style={{minWidth:640}}>
            <text x={40} y={60} fontSize={12} fontWeight={700} fill="#1F3A5F">SUPPLIERS</text>
            <text x={270} y={60} fontSize={12} fontWeight={700} fill="#1F3A5F">PLANTS</text>
            <text x={500} y={60} fontSize={12} fontWeight={700} fill="#1F3A5F">DISTRIBUTION</text>
            {supNodes.map(s => plantNodes.map(p => {
              const k=`${s.supplier_code}-${p.location_code}`, cnt=laneCountSupPlant[k]||0
              return cnt>0 ? <line key={k} x1={s.x+nodeW} y1={s.y+nodeH/2} x2={p.x} y2={p.y+nodeH/2} stroke="#c98a3c" strokeWidth={Math.min(cnt*0.5+0.5,3)} opacity={0.6} /> : null
            }))}
            {plantNodes.map(p => dcNodes.map(d => {
              const k=`${p.location_code}-${d.location_code}`, cnt=laneCountPlantDC[k]||0
              const col=dcColor(d.m)
              return cnt>0 ? <line key={k} x1={p.x+nodeW} y1={p.y+nodeH/2} x2={d.x} y2={d.y+nodeH/2} stroke={col} strokeWidth={Math.min(cnt*0.3+0.8,3)} opacity={0.7} /> : null
            }))}
            {supNodes.map(n => <Node key={n.supplier_code} n={n} />)}
            {plantNodes.map(n => <Node key={n.location_code} n={n} />)}
            {dcNodes.map(n => <Node key={n.location_code} n={n} />)}
          </svg>
        </div>
        <div className="grid gap-4" style={{gridTemplateColumns:`repeat(${Math.min(dcNodes.length,3)},1fr)`}}>
          {dcNodes.map(d => (
            <div key={d.location_code} className="card p-4">
              <div className="font-display text-lg">{d.location_name}</div>
              <div className="text-xs text-slate2">{d.zone} zone</div>
              {d.m ? <div className="text-sm text-slate2 mt-2 space-y-0.5">
                <div>Demand: {Math.round(d.m.demand)} · Supply: {Math.round(d.m.supply)}</div>
                <div>Fill: {fmtPct(d.m.supply/(d.m.demand||1))} · Risk: <span className="text-rust">{fmtMoney(d.m.risk)}</span></div>
              </div> : <div className="text-sm text-slate2 mt-1">No demand in selection</div>}
              <div className="text-xs text-slate2 mt-2">{(allLanes.filter(l=>l.to_location===d.location_code&&(activeItems.length?activeItems.includes(l.item_code):true)).length)} active lanes</div>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}
