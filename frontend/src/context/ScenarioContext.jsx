import { createContext, useContext, useState, useCallback } from 'react'

// Global selected optimizer scenario, shared across all pages (R2-25/26).
// Persisted to localStorage so it survives navigation and reloads.
const ScenarioContext = createContext({ scenario: 'balanced', setScenario: () => {} })

const VALID = ['min_cost', 'max_service', 'balanced']
const LABELS = { min_cost: 'Minimise Cost', max_service: 'Maximise Service', balanced: 'Balanced' }

export function ScenarioProvider({ children }) {
  const [scenario, setScenarioState] = useState(() => {
    const saved = localStorage.getItem('pravah_scenario')
    return VALID.includes(saved) ? saved : 'balanced'
  })
  const setScenario = useCallback((s) => {
    if (!VALID.includes(s)) return
    localStorage.setItem('pravah_scenario', s)
    setScenarioState(s)
  }, [])
  return (
    <ScenarioContext.Provider value={{ scenario, setScenario }}>
      {children}
    </ScenarioContext.Provider>
  )
}

export function useScenario() {
  return useContext(ScenarioContext)
}

// Honest banner: shown on pages whose data is computed upstream of the optimizer
// and therefore does NOT differ by scenario. Avoids faking per-scenario differences.
export function ScenarioNote({ page }) {
  const { scenario } = useScenario()
  const driven = {
    handshake: false, netting: false, mrp: false, capacity: false,
  }
  // these pages reflect the consensus demand plan, which is the same input to every
  // scenario. Only the Optimizer's production plan differs by scenario today.
  return (
    <div className="mx-8 mt-4 text-xs text-slate2 bg-mist/60 border border-[#e7ecf2] rounded-lg px-4 py-2">
      Scenario: <b className="text-ink">{LABELS[scenario]}</b>. This view shows the demand-driven plan,
      which is the shared input to all scenarios — the scenarios diverge at the Optimizer (production allocation under capacity). Open the Optimizer to compare how each scenario allocates production.
    </div>
  )
}

export const SCENARIO_LABELS = LABELS
export const SCENARIOS = VALID
