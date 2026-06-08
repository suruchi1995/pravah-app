import { useEffect, useState } from 'react'
import { AgGridReact } from 'ag-grid-react'
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-quartz.css'

export function useAsync(fn, deps = []) {
  const [state, setState] = useState({ loading: true, data: null, error: null })
  useEffect(() => {
    let alive = true
    setState({ loading: true, data: null, error: null })
    fn().then(d => alive && setState({ loading: false, data: d, error: null }))
        .catch(e => alive && setState({ loading: false, data: null, error: e.message }))
    return () => { alive = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
  return state
}

export function PageHeader({ title, subtitle, children }) {
  return (
    <div className="flex items-end justify-between px-8 pt-7 pb-5 border-b border-[#e7ecf2] bg-white">
      <div>
        <h1 className="font-display text-3xl text-ink leading-tight">{title}</h1>
        {subtitle && <p className="text-slate2 text-sm mt-1 max-w-2xl">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-2">{children}</div>
    </div>
  )
}

const ACCENT = {
  brand: ['#e8f0f8', '#2E5C8A'], sage: ['#e8f1ec', '#5b8a72'],
  amber: ['#f7eede', '#c98a3c'], rust: ['#f6e7e5', '#b5544a'],
}
export function Kpi({ label, value, sub, tone = 'brand', icon: Icon }) {
  const [bg, fg] = ACCENT[tone]
  return (
    <div className="card p-5 flex-1 min-w-[180px]">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs uppercase tracking-wide text-slate2">{label}</span>
        {Icon && <span className="kpi-accent" style={{ background: bg, color: fg }}><Icon size={18} /></span>}
      </div>
      <div className="font-display text-3xl text-ink">{value}</div>
      {sub && <div className="text-xs text-slate2 mt-1">{sub}</div>}
    </div>
  )
}

export function Grid({ rows, columns, height = 520 }) {
  return (
    <div className="ag-theme-quartz" style={{ height, width: '100%' }}>
      <AgGridReact
        rowData={rows || []}
        columnDefs={columns}
        defaultColDef={{
          sortable: true,
          filter: true,
          resizable: true,
          minWidth: 130,
          flex: 1,
          wrapHeaderText: true,       // header text wraps instead of truncating (R2-4)
          autoHeaderHeight: true,     // header grows to fit wrapped text
        }}
        pagination={true}
        paginationPageSize={20}
        animateRows={true}
        onGridReady={params => { params.api.sizeColumnsToFit() }}
      />
    </div>
  )
}

export function Loading() {
  return <div className="p-8 text-slate2">Loading…</div>
}
export function ErrorBox({ msg }) {
  return <div className="m-8 p-4 rounded-lg bg-rust/10 text-rust text-sm">Error: {msg}</div>
}

export function fmtMoney(n) {
  if (n == null) return '—'
  return '₹' + Number(n).toLocaleString('en-IN', { maximumFractionDigits: 0 })
}
export function fmtPct(n) {
  if (n == null) return '—'
  return (Number(n) * 100).toFixed(1) + '%'
}
