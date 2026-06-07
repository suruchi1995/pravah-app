import { useState, useRef, useEffect } from 'react'
import { ChevronDown, Check } from 'lucide-react'

// A multi-select dropdown with an "All" option. Closed state shows a summary.
function MultiSelect({ label, options, selected, onChange }) {
  const [open, setOpen] = useState(false)
  const ref = useRef(null)
  useEffect(() => {
    const h = e => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', h)
    return () => document.removeEventListener('mousedown', h)
  }, [])

  const allSelected = selected.length === 0 || selected.length === options.length
  const summary = allSelected ? 'All' : selected.length === 1 ? selected[0] : `${selected.length} selected`

  function toggle(opt) {
    if (selected.includes(opt)) onChange(selected.filter(o => o !== opt))
    else onChange([...selected, opt])
  }
  function selectAll() { onChange([]) } // empty = all

  return (
    <div className="relative" ref={ref}>
      <span className="text-xs text-slate2 mr-2">{label}</span>
      <button onClick={() => setOpen(o => !o)}
        className="inline-flex items-center gap-2 text-sm px-3 py-1.5 rounded-lg border border-[#d6deea] bg-white hover:bg-mist min-w-[120px] justify-between">
        <span className={allSelected ? 'text-slate2' : 'text-ink font-medium'}>{summary}</span>
        <ChevronDown size={14} className="text-slate2" />
      </button>
      {open && (
        <div className="absolute z-30 mt-1 w-56 max-h-72 overflow-auto bg-white border border-[#d6deea] rounded-xl shadow-lg p-1">
          <button onClick={selectAll}
            className={`w-full flex items-center gap-2 text-sm px-3 py-2 rounded-lg hover:bg-mist ${allSelected ? 'text-brand font-medium' : 'text-ink'}`}>
            <span className="w-4">{allSelected && <Check size={14} />}</span> All
          </button>
          <div className="h-px bg-[#eef2f6] my-1" />
          {options.map(opt => {
            const on = !allSelected && selected.includes(opt)
            return (
              <button key={opt} onClick={() => toggle(opt)}
                className={`w-full flex items-center gap-2 text-sm px-3 py-2 rounded-lg hover:bg-mist ${on ? 'text-brand font-medium' : 'text-ink'}`}>
                <span className="w-4">{on && <Check size={14} />}</span> {opt}
              </button>
            )
          })}
        </div>
      )}
    </div>
  )
}

// FilterBar renders the filters this page needs. `config` = { items, locations, periods, zones } option arrays.
// `value` = { items:[], locations:[], periods:[], zones:[] }; empty array means "all".
export function FilterBar({ config, value, onChange }) {
  if (!config) return null
  // when a zone is selected, it implies all its DCs — handled in rowPasses
  return (
    <div className="flex items-center gap-5 px-8 py-3 bg-white border-b border-[#e7ecf2] flex-wrap">
      <span className="text-xs uppercase tracking-wide text-slate2 font-semibold">Filters</span>
      {config.zones && (
        <MultiSelect label="Zone" options={config.zones} selected={value.zones || []}
          onChange={v => onChange({ ...value, zones: v })} />
      )}
      {config.items && (
        <MultiSelect label="Item" options={config.items} selected={value.items || []}
          onChange={v => onChange({ ...value, items: v })} />
      )}
      {config.locations && (
        <MultiSelect label="Location" options={config.locations} selected={value.locations || []}
          onChange={v => onChange({ ...value, locations: v })} />
      )}
      {config.periods && (
        <MultiSelect label="Period" options={config.periods} selected={value.periods || []}
          onChange={v => onChange({ ...value, periods: v })} />
      )}
    </div>
  )
}

// helper: does a row pass the active filters? empty filter array = all pass.
// zoneMap = { DC_DEL: 'North', DC_MUM: 'West', ... } for zone filtering
export function rowPasses(row, value, { itemKey = 'item_code', locKey = 'location_code', perKey = 'period', zoneMap = {} } = {}) {
  const items = value.items || [], locs = value.locations || [], pers = value.periods || [], zones = value.zones || []
  if (items.length && row[itemKey] != null && !items.includes(row[itemKey])) return false
  if (pers.length && row[perKey] != null && !pers.includes(row[perKey])) return false
  // location filter: direct match OR zone match
  if (locs.length && row[locKey] != null && !locs.includes(row[locKey])) return false
  if (zones.length && row[locKey] != null) {
    const rowZone = zoneMap[row[locKey]]
    if (rowZone && !zones.includes(rowZone)) return false
  }
  return true
}

// derive available options from a dataset
export function deriveOptions(rows, { item = true, location = true, period = false } = {}) {
  const cfg = {}
  if (item) cfg.items = [...new Set(rows.map(r => r.item_code).filter(Boolean))].sort()
  if (location) cfg.locations = [...new Set(rows.map(r => r.location_code).filter(Boolean))].sort()
  if (period) cfg.periods = [...new Set(rows.map(r => r.period).filter(Boolean))].sort()
  return cfg
}
