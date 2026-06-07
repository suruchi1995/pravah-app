# Pravah — Testing Issue Tracker

**Owner:** Suruchi | **Updated:** 2026-06-07 (Round 2 testing)
**How we work:** Suruchi tests → logs issue → we discuss → analyse → solve → push → Suruchi re-tests → mark Certified.

## Status lifecycle
`IDENTIFIED` → `DISCUSSING` → `ANALYSED` → `IN PROGRESS` → `FIXED (awaiting test)` → `CERTIFIED ✅` | `DEFERRED` | `WON'T FIX`

## Severity
🔴 Blocker · 🟠 Major · 🟡 Minor · 🔵 Enhancement

---

## ROUND 1 ISSUES — STATUS

| ID | Area | Issue | Sev | Status |
|----|------|-------|-----|--------|
| R1-1 | Auth | Login page + approvals UI | 🟠 | FIXED — awaiting retest (blank page bug reported in R2) |
| R1-2 | Filters | Zone hierarchy | 🔵 | FIXED — awaiting retest |
| R1-3 | Dashboard | Better KPIs | 🟠 | FIXED — awaiting retest |
| R1-4 | Dashboard | Clickable KPI cards | 🔵 | FIXED — awaiting retest |
| R1-5 | Dashboard | Bottleneck popup | 🔵 | FIXED — awaiting retest |
| R1-6 | Dashboard | Filters | 🟠 | FIXED — awaiting retest |
| R1-7 | Data Hub | PM/RM/SFG tabs | 🟡 | FIXED — new issues found in R2 |
| R1-8 | UOM | UOM conversion table | 🟠 | IN PROGRESS (building now) |
| R1-9 | Data Hub | Better labels | 🟡 | FIXED — awaiting retest |
| R1-10 | Data/Model | Supply Lanes | 🟠 | FIXED — lanes empty issue in R2 |
| R1-11 | Network | PM/suppliers visible | 🟠 | FIXED — network not rendering in R2 |
| R1-12 | Network | Location filter | 🟡 | FIXED — awaiting retest |
| R1-13 | Network | Something missing | 🟡 | DEFERRED |
| R1-14 | Segmentation | Charts first | 🔵 | FIXED — click interaction reported in R2 |
| R1-15 | Segmentation | CI/predictability model | 🟠 | IN PROGRESS (building now) |
| R1-16 | Segmentation | Item-location level | 🟠 | IN PROGRESS (building now) |
| R1-17 | Segmentation | Top/least focus items | 🔵 | FIXED — awaiting retest |

---

## ROUND 2 ISSUES — NEW (from 2026-06-07 testing)

| ID | Area | Issue | Sev | Status |
|----|------|-------|-----|--------|
| R2-1 | Auth | Login page shows blank; approvals blank page | 🔴 | IDENTIFIED |
| R2-1a | Auth | Admin workspace — where to register users, assign roles, generate passwords | 🟠 | IDENTIFIED |
| R2-2 | Auth/Roles | Certain fields (MOQ, expiry, lead time, params) editable by one role only | 🟠 | IDENTIFIED |
| R2-2a | Data | After user edits field — "Update data" button to push to Neon + re-run plan | 🟠 | IDENTIFIED |
| R2-3 | Demand Plan | Where is demand override UI? | 🟠 | IDENTIFIED |
| R2-4 | UI/Global | Column headers not fully visible; can't resize columns easily | 🟡 | IDENTIFIED |
| R2-5 | Filters | Supplier data not in filter | 🟡 | IDENTIFIED |
| R2-6 | Data Hub | Add Item/Location filter to global filter | 🟠 | IDENTIFIED |
| R2-7 | Data Hub | Local filter still no dropdown list | 🟡 | IDENTIFIED |
| R2-8 | Data Hub | Combine all items into one tab with item_type column | 🟡 | IDENTIFIED |
| R2-9 | Data Hub | Supply Lane + Supplier-Item → one tab; lanes empty; needs: item/from/to/transmode | 🟠 | IDENTIFIED |
| R2-10 | Data Hub | Expiry dates missing; transmode missing | 🟠 | IDENTIFIED |
| R2-11 | Network | Network not rendering (blank/broken) | 🔴 | IDENTIFIED |
| R2-12 | Network | Bottom DC cards → navigate to filtered page | 🔵 | IDENTIFIED |
| R2-13 | Network | Remove DC type tags (too cluttered) | 🟡 | IDENTIFIED |
| R2-14 | Segmentation | Click A in chart → all widgets filter to A items | 🔵 | IDENTIFIED |
| R2-15 | Demand-Supply | Where is supply coming from in UI? Explain handshake logic. Demand override should be here | 🟠 | IDENTIFIED |
| R2-16 | Inventory | Where is safety stock maintained? Is it from customer? Editable in Data Hub? | 🟠 | IDENTIFIED |
| R2-17 | Inventory | Show all formula variables (safety stock, reorder, target, days) | 🟠 | IDENTIFIED |
| R2-18 | Inventory | Shouldn't Netting come before Inventory in the flow? | 🟡 | IDENTIFIED |
| R2-19 | Netting | Filter: All option + zonal + location + time hierarchy | 🟡 | IDENTIFIED |
| R2-20 | Netting | Where do receipts come from? Explain PO/production/sales orders | 🟠 | IDENTIFIED |
| R2-21 | Netting | Explain what planned orders means / where it comes from | 🟠 | IDENTIFIED |
| R2-22 | Supply (MRP) | Add location filter | 🟡 | IDENTIFIED |
| R2-23 | Supply (MRP) | Add chart/diagram linking to table | 🔵 | IDENTIFIED |
| R2-24 | Capacity | Time on X axis; location + time filters (all hierarchy) | 🟠 | IDENTIFIED |
| R2-25 | Capacity | Explain 3 scenarios — variables/parameters used | 🟠 | IDENTIFIED |
| R2-26 | Capacity | User chooses scenario → all pages reflect results | 🟠 | IDENTIFIED |
| R2-27 | Optimizer | Resource data — where does it come from? Add to Data Hub + make editable | 🟠 | IDENTIFIED |
| R2-28 | Optimizer | Add resource filter | 🟡 | IDENTIFIED |
| R2-29 | Optimizer | Click resource → navigate to items using it + fill rate | 🔵 | IDENTIFIED |
| R2-30 | Optimizer | Warning: resource overused or underused | 🟠 | IDENTIFIED |
| R2-31 | AI Copilot | (Testing feedback pending) | 🟡 | IDENTIFIED |
| R2-32 | Approvals | Blank page; workspace only visible to approval role | 🔴 | IDENTIFIED |
| R2-33 | Admin | Admin workspace: register users, assign roles, auto-generate password | 🟠 | IDENTIFIED |
| R2-34 | User Page | User settings: view changes, approvals, change password, see roles | 🔵 | IDENTIFIED |
| R2-35 | UI/Global | Left sidebar should be collapsible (on desktop too, not just mobile) | 🟡 | IDENTIFIED |
| R2-36 | UI/Global | Company name visible somewhere in the UI | 🟡 | IDENTIFIED |
| R2-37 | UI/Global | UI should represent a company using Pravah (branding) | 🔵 | IDENTIFIED |

---

## PRIORITY TRIAGE — What to work on next

### 🔴 BLOCKERS (fix immediately)
- **R2-1 / R2-32** — Login blank, Approvals blank. Nothing else matters if auth is broken.
- **R2-11** — Network not rendering.

### 🟠 MAJORS — discussion needed before building
- **R2-1a / R2-33** — Admin workspace design
- **R2-2 / R2-2a** — Role-based field editing + "push changes" button
- **R2-3** — Demand override UI location
- **R2-9 / R2-10** — Supply lane data completeness (expiry, transmode)
- **R2-15** — Handshake explanation + override placement
- **R2-16/17** — Inventory: safety stock source + formula transparency
- **R2-25/26** — Scenario selection affecting all pages
- **R2-27** — Optimizer resource data source

### 🟡 MINORS — build without discussion
- R2-4 (column resize), R2-5 (supplier filter), R2-6/7 (filter improvements),
  R2-8 (items tab), R2-13 (network clutter), R2-19 (netting filter),
  R2-22 (MRP location filter), R2-24 (capacity time axis + filter),
  R2-28 (optimizer resource filter), R2-35 (sidebar collapsible desktop),
  R2-36 (company name)

### 🔵 ENHANCEMENTS — after majors
- R2-12, R2-14, R2-23, R2-29, R2-30, R2-34, R2-37

---

## Issue detail — Round 2 (key ones)

### R2-1 / R2-32 — Auth blank pages
- Both login and approvals render blank. Root cause: likely a JS crash on load.
  Approvals calls `/api/change-requests` with a Bearer token from localStorage —
  if localStorage is empty (no login happened), the fetch returns 401 and the
  component crashes instead of redirecting to /login.
- **Fix:** Add auth guard (redirect to /login if no token), fix Approvals to handle 401.

### R2-1a / R2-33 — Admin workspace
- **Suruchi's ask:** A screen where admin can register new users, assign roles,
  auto-generate a temporary password, and the user changes it on first login.
- **Design needed:** Admin page at /admin with: user list, "Add user" form
  (name, email, role selection, auto-generate password), deactivate user, reset password.

### R2-2 / R2-2a — Role-based field editing + push button
- Certain fields (MOQ, expiry, lead time, parameters) should only be editable
  by specific roles (e.g. planner+).
- After editing, an "Update & Re-plan" button pushes the change to Neon
  and triggers the pipeline (not a full data upload — a targeted field update).

### R2-3 — Demand override UI
- Currently overrides are loaded via CSV. Suruchi wants to set them IN the UI
  on the Demand-Supply screen (type a new demand qty → submits a change request
  → goes through approval → pipeline re-runs).

### R2-9 / R2-10 — Supply lanes data
- Lanes tab is empty or incomplete. Supply lanes need: item_code, from_location,
  to_location, transport_mode. Expiry days and transmode need to be in items/lanes.

### R2-11 — Network not rendering
- The Network page SVG fails to render. Likely a data-shape issue — nodes or
  edges have null/undefined coordinates or the SVG viewBox is wrong.

### R2-15 — Handshake explanation
- What is supply coming from? Answer: on-hand inventory + planned receipts.
- What is the handshake? It compares consensus demand (forecast ± override)
  vs available supply = on-hand + open POs being received + production orders.
  Gap = demand - supply. Fill rate = supply/demand. Revenue at risk = gap × price.
- Demand override should be possible from this screen (links to R2-3).

### R2-16/17 — Inventory formulas
- Safety stock: calculated from demand variability + service level target.
  Is NOT provided by customer — it's derived. Should be visible in Data Hub
  as a derived/planner-adjustable parameter.
- Formula: safety_stock = z × σ × √(lead_time); reorder = avg_demand × lead_time + SS;
  target = reorder + avg_demand; days = target / (avg_demand/30).

### R2-18 — Netting vs Inventory order
- Suruchi asks if Netting should come before Inventory.
- **Answer:** In standard MRP, the order is: Forecast → Demand Plan → Inventory
  (sets safety stock targets) → Netting (gross - on_hand - SS - receipts = net)
  → MRP explosion. So Inventory BEFORE Netting is correct. But the sidebar order
  can be clarified with better labels to show the flow.

### R2-25/26 — Scenario selection
- User should pick which optimizer scenario they want, and ALL pages (MRP, capacity,
  handshake) should reflect that scenario's plan — not just the Optimizer page.
- This is a significant feature: requires a "selected_scenario" parameter that the
  engines read when generating downstream outputs.

### R2-27 — Optimizer resource data
- Resource data (lines, hours) should come from users via Data Hub.
  Currently it's in the dataset but not editable in the UI.
  Make it editable in Data Hub (like parameters).
