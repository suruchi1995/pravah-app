import { useState } from 'react'
import { api } from '../api'
import { useAsync, PageHeader, Grid, Loading } from '../components/ui'
import { Upload, RotateCcw, Download, CheckCircle2, XCircle } from 'lucide-react'

const TABLES = ['items', 'locations', 'suppliers', 'bom', 'inventory', 'demand_history']

export default function DataHub() {
  const [table, setTable] = useState('items')
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const data = useAsync(() => api.master(table), [table, result])

  async function onFile(e) {
    const f = e.target.files?.[0]; if (!f) return
    setBusy(true); setResult(null)
    try {
      const r = await api.upload(f, 'apex')
      setResult(r)
    } catch (err) { setResult({ ok: false, errors: [{ sheet: '-', message: err.message }] }) }
    setBusy(false); e.target.value = ''
  }
  async function reset() {
    setBusy(true); setResult(null)
    try {
      await api.resetDemo()
      setResult({ ok: true, message: 'Rebuilding all plans and the optimizer — this takes ~30–90s. Please wait…' })
      // poll until the background job finishes
      const start = Date.now()
      const poll = setInterval(async () => {
        try {
          const st = await api.resetStatus()
          if (st.status === 'done') {
            clearInterval(poll); setBusy(false)
            setResult({ ok: true, message: 'Demo data rebuilt. All screens are refreshed.' })
          } else if (st.status && st.status.startsWith('error')) {
            clearInterval(poll); setBusy(false)
            setResult({ ok: false, errors: [{ sheet: '-', message: st.status }] })
          } else if (Date.now() - start > 180000) {
            clearInterval(poll); setBusy(false)
            setResult({ ok: true, message: 'Still working in the background — refresh the screens in a moment.' })
          }
        } catch { /* keep polling */ }
      }, 4000)
    } catch (err) {
      setBusy(false)
      setResult({ ok: false, errors: [{ sheet: '-', message: err.message }] })
    }
  }

  const cols = (data.data && data.data[0]) ? Object.keys(data.data[0]).map(k => ({ field: k })) : []

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
        <button onClick={reset} className="flex items-center gap-2 text-sm px-3 py-2 rounded-lg border border-[#d6deea] hover:bg-mist">
          <RotateCcw size={16} /> Reset demo
        </button>
      </PageHeader>

      <div className="p-8 space-y-5">
        {busy && <div className="card p-4 text-sm text-slate2">Working… validating, loading and re-planning.</div>}

        {result && result.ok && (
          <div className="card p-4 flex items-start gap-3 border-l-4 border-sage">
            <CheckCircle2 className="text-sage mt-0.5" size={20} />
            <div>
              <div className="font-semibold">{result.message || 'Upload accepted — plan regenerated.'}</div>
              {result.warnings?.length > 0 && (
                <ul className="text-sm text-slate2 mt-2 list-disc ml-5">
                  {result.warnings.map((w, i) => <li key={i}><b>{w.sheet}:</b> {w.message}</li>)}
                </ul>
              )}
            </div>
          </div>
        )}
        {result && !result.ok && (
          <div className="card p-4 border-l-4 border-rust">
            <div className="flex items-center gap-2 text-rust font-semibold mb-2"><XCircle size={20} /> Upload rejected — {result.errors.length} issue(s)</div>
            <div className="max-h-64 overflow-auto text-sm">
              <table className="w-full">
                <thead><tr className="text-left text-slate2"><th className="py-1 pr-4">Sheet</th><th className="py-1 pr-4">Row</th><th className="py-1">Problem</th></tr></thead>
                <tbody>
                  {result.errors.map((e, i) => (
                    <tr key={i} className="border-t border-[#eef2f6]">
                      <td className="py-1 pr-4 font-mono text-xs">{e.sheet}</td>
                      <td className="py-1 pr-4">{e.row ?? '—'}</td>
                      <td className="py-1">{e.message}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div className="card p-5">
          <div className="flex gap-2 mb-4 flex-wrap">
            {TABLES.map(t => (
              <button key={t} onClick={() => setTable(t)}
                className={`text-sm px-3 py-1.5 rounded-lg border ${table === t ? 'bg-brand text-white border-brand' : 'border-[#d6deea] text-slate2 hover:bg-mist'}`}>
                {t}
              </button>
            ))}
          </div>
          {data.loading ? <Loading /> : <Grid rows={data.data} columns={cols} height={460} />}
        </div>
      </div>
    </>
  )
}
