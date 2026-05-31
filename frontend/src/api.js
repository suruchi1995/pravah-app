const BASE = '/api'

async function get(path) {
  const r = await fetch(`${BASE}${path}`)
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
  return r.json()
}

export const api = {
  health: () => get('/health'),
  summary: (t = 'apex') => get(`/summary?tenant=${t}`),
  segmentation: (t = 'apex') => get(`/segmentation?tenant=${t}`),
  forecast: (t = 'apex', item, loc) => get(`/forecast?tenant=${t}${item ? `&item=${item}` : ''}${loc ? `&location=${loc}` : ''}`),
  handshake: (t = 'apex') => get(`/handshake?tenant=${t}`),
  inventoryTargets: (t = 'apex') => get(`/inventory-targets?tenant=${t}`),
  netting: (t = 'apex', item) => get(`/netting?tenant=${t}${item ? `&item=${item}` : ''}`),
  mrp: (t = 'apex') => get(`/mrp?tenant=${t}`),
  capacity: (t = 'apex') => get(`/capacity?tenant=${t}`),
  optimizer: (t = 'apex') => get(`/optimizer?tenant=${t}`),
  master: (table, t = 'apex') => get(`/master/${table}?tenant=${t}`),
  resetDemo: (t = 'apex') => fetch(`${BASE}/reset-demo?tenant=${t}`, { method: 'POST' }).then(r => r.json()),
  templateUrl: `${BASE}/template`,
  upload: async (fileObj, tenant) => {
    const fd = new FormData()
    fd.append('file', fileObj)
    const r = await fetch(`${BASE}/upload?tenant=${tenant}`, { method: 'POST', body: fd })
    return r.json()
  },
}
