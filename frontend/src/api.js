const BASE = '/api'

// Parse a response body safely. An empty/truncated body (cold start, 502, timeout)
// must NOT crash the app with "Unexpected end of JSON input".
async function parseJson(r) {
  const text = await r.text()
  if (!text) {
    throw new Error(`Empty response (${r.status}). The server may be waking up.`)
  }
  try {
    return JSON.parse(text)
  } catch {
    throw new Error(`Server returned a non-JSON response (${r.status}). It may be waking up — please retry.`)
  }
}

// fetch with a timeout + one automatic retry, to ride out Render free-tier cold starts.
async function fetchResilient(url, opts = {}, { retries = 2, timeoutMs = 60000 } = {}) {
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const ctrl = new AbortController()
      const timer = setTimeout(() => ctrl.abort(), timeoutMs)
      const r = await fetch(url, { ...opts, signal: ctrl.signal })
      clearTimeout(timer)
      if (r.status >= 500 && attempt < retries) {
        await new Promise(res => setTimeout(res, 3000))  // backend waking; wait & retry
        continue
      }
      return r
    } catch (e) {
      if (attempt < retries) {
        await new Promise(res => setTimeout(res, 3000))
        continue
      }
      throw new Error('Could not reach the server. It may be waking up — please retry in a moment.')
    }
  }
}

async function get(path) {
  const r = await fetchResilient(`${BASE}${path}`)
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
  return parseJson(r)
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
  copilot: async (question, tenant = 'apex') => {
    const r = await fetchResilient(`${BASE}/copilot`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, tenant }),
    })
    if (!r.ok) throw new Error(`${r.status}`)
    return parseJson(r)
  },
  resetDemo: (t = 'apex') => fetchResilient(`${BASE}/reset-demo?tenant=${t}`, { method: 'POST' }).then(parseJson),
  resetStatus: (t = 'apex') => fetchResilient(`${BASE}/reset-status?tenant=${t}`).then(parseJson),
  templateUrl: `${BASE}/template`,
  upload: async (fileObj, tenant) => {
    const fd = new FormData()
    fd.append('file', fileObj)
    const r = await fetchResilient(`${BASE}/upload?tenant=${tenant}`, { method: 'POST', body: fd },
      { retries: 0, timeoutMs: 120000 })  // upload: no auto-retry (don't double-upload), long timeout
    return parseJson(r)
  },
}
