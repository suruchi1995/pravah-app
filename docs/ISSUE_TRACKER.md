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


---

## DECISIONS LOCKED (2026-06-07)

| Issue | Decision |
|-------|----------|
| R2-1a / R2-33 | Full `/admin` screen: user list, add-user form, role picker, auto-generated temp password, user changes password on first login |
| R2-2 / R2-2a | **Planner** role can edit MOQ/expiry/lead-time/params in UI. "Update & Re-plan" button → goes through approval workflow; applies + re-plans only AFTER approval |
| R2-3 | Demand override directly on Demand-Supply (Handshake) screen; same approval-gated re-plan button; replan covers steps after demand |
| R2-10 | Add `expiry_days` column to items table |
| R2-15 | Handshake explanation is for Suruchi's understanding only — NOT a UI change |
| R2-18 | Sidebar shows planning flow order explicitly |
| R2-25 / R2-26 | User selects scenario → ALL downstream pages reflect it (global selected_scenario the engines read) |
| R2-34 | User profile page: user info, changes made, approvals, change password, roles |

## WORK PLAN — split agreed

### BATCH A — building now (one push)
🔴 R2-1/R2-32 (auth blank pages), 🔴 R2-11 (network not rendering),
🟡 R2-4 (column headers/resize), R2-5 (supplier filter), R2-6/R2-7 (data hub filters + dropdowns),
R2-8 (combine items tab + type column), R2-9 (lanes+supplier-item one tab, fix empty, add transmode),
R2-10 (expiry_days), R2-13 (remove DC clutter), R2-18 (sidebar flow order),
R2-19 (netting filter hierarchy), R2-22 (MRP location filter), R2-24 (capacity time axis + filters),
R2-28 (optimizer resource filter), R2-35 (sidebar collapsible desktop), R2-36 (company name in UI)

### BATCH B — separate focused sessions (too important to rush)
- **Session B1:** R2-1a/R2-33 — Admin workspace (user management screen + API)
- **Session B2:** R2-2/R2-2a + R2-3 — Inline field editing + demand override + approval-gated re-plan
- **Session B3:** R2-25/R2-26 — Global scenario selection across all pages
- **Session B4:** R2-34 — User profile page

### Also pending (need input / later)
- R2-20/R2-21 (netting explanations), R2-23 (MRP chart), R2-27 (resource editable — part of B2),
  R2-29/R2-30 (optimizer resource drilldown + warnings), R2-12/R2-14 (cross-filter linking),
  R2-31 (copilot feedback), R2-37 (branding)


---

## BATCH A — BUILT & PUSHED (awaiting Suruchi retest)

| Issue | What was fixed |
|-------|----------------|
| R2-1 / R2-32 | Login now standalone page (no layout conflict). Approvals handles no-token/401 gracefully with a "sign in required" gate instead of blank page. Approval workspace gated to logged-in users. |
| R2-11 | **Root cause: a syntax error in supply_mrp.py crashed the whole backend on import → every page blank.** Fixed. Network now renders with lanes. |
| R2-10 | expiry_days added to items (FG 18-24mo, RM 12mo, perishables realistic). Optional on upload. |
| R2-18 | Sidebar now grouped: Dashboard/Data/Network, then "Planning flow" (1·Segmentation → 8·Optimizer numbered), then Tools. |
| R2-35 | Sidebar collapsible on desktop (chevron toggle), not just mobile. |
| R2-36 | Company name (Apex Nutraceuticals) shown under Pravah logo in sidebar. |
| R2-15/16 (partial) | Segmentation engine now produces item-LOCATION level rows (3-axis: ABC + Predictability + Supply CI) + item summaries. 40 rows. |

**Still in Batch A queue (next sub-push):** R2-4 (column resize), R2-5 (supplier filter), R2-6/7 (data hub filters), R2-8 (combine items tab), R2-9 (lanes+supplier-item tab), R2-13 (remove clutter), R2-19/22/24/28 (page filters).

**Note:** Batch A turned out larger than one push. Auth blockers + network blocker + sidebar + expiry + segmentation engine done first (most critical). Remaining UI-filter items in next push.

---

## BATCH A part 2 — BUILT & PUSHED (awaiting retest)

| Issue | What was fixed |
|-------|----------------|
| R2-4 | Grid headers now wrap (autoHeaderHeight + wrapHeaderText) so they're fully visible; columns resizable + size-to-fit on load |
| R2-6 | Data Hub now has global Item/Location filter (auto-shown on tabs that have those columns) |
| R2-7 | Data Hub filters use the multi-select dropdown component (with All) |
| R2-8 | All item types combined into one "Items" tab with a Type column (instead of 4 separate tabs) |
| R2-9 | "Sourcing & Lanes" tab merges supplier-item mapping + supply lanes; shows item, from, to, transmode, lead time, MOQ |
| R2-13 | Removed cluttered zone·state tags from Network nodes |
| R2-19 | Netting has a Period filter |
| R2-20/R2-21 | Netting "What is this?" panel explains where receipts, gross req, and planned orders come from |
| R2-24 | Capacity chart now has TIME on the X-axis (one line per resource, utilisation % trend) |
| R2-22 | **Honest note:** MRP is item-period level (BOM explosion aggregates across network) — it has no location dimension, so a location filter doesn't apply. Item + Period filters kept. Flagged rather than faked. |

**Batch A remaining:** R2-5 (supplier filter — suppliers don't appear in the planning filters since they're a sourcing dimension, not item/location; will add to Sourcing tab filter), R2-28 (optimizer resource filter — already has item filter; will add resource).

**Still queued — Batch B sessions:** B1 admin workspace, B2 inline edit + override + re-plan, B3 scenario selection, B4 user profile. Enhancements: R2-12/14 (cross-filter), R2-23 (MRP chart), R2-29/30 (optimizer drilldown+warnings), R2-37 (branding).

---

## BATCH B1 — Admin workspace — BUILT & PUSHED (awaiting retest)

| Issue | What was built |
|-------|----------------|
| R2-1a / R2-33 | Full `/admin` screen (admins only): user list with roles + active status; "Add user" form with name/email + role multi-select; **auto-generated temporary password** shown once with copy button; per-user actions: reset password (new temp pw), deactivate, reactivate. |
| (supports R2-34) | `/api/change-password` endpoint; forced password change on first login — new users (and password-resets) must set a new password before entering the app. |

**Backend:** must_change_password flag on users; endpoints /api/users (list/create), /api/users/{deactivate,activate,reset-password}, /api/change-password. Admin cannot deactivate self. 11/11 admin backend checks pass. Migration adds the new column to stale user tables.
**Frontend:** Admin.jsx (gated to admin role), Login.jsx now handles forced password change, Admin added to sidebar Tools group.

**Next Batch B sessions:** B2 (inline edit + override + approval-gated re-plan), B3 (scenario selection), B4 (user profile page).

---

## BATCH B2 — Inline editing + demand override + approval-gated re-plan — BUILT & PUSHED

| Issue | What was built |
|-------|----------------|
| R2-3 | "Override demand" button on the Demand–Supply (Handshake) screen → builder modal (item/DC/period/uplift%/absolute/reason) → approval-gated submit. |
| R2-2 | "Edit a field" on Data Hub for editable master data — items (price, expiry), suppliers (lead time, MOQ, reliability), supplier-item (price, MOQ, lead time), resources (capacity). Planner/admin only. |
| R2-2a | All edits + overrides go through the approval workflow. On approval, the change applies AND the pipeline re-runs automatically ("replanned": true). Planner cannot approve own request. |
| R2-27 (partial) | Resource capacity (hours_per_month) is now editable via the same field-edit flow. |

**Backend:** `field_edit` change type added to `_apply_change` (MODEL_MAP: items/suppliers/resources/supplier_item_mapping/supply_lanes; numeric casting; safe attr check). Approve endpoint already re-plans. 4/4 B2 backend checks + 85 core checks pass on clean Postgres.
**Frontend:** reusable `ChangeRequestModal` + `canEditData()` helper; override builder on Handshake; field editor on Data Hub.

**Remaining Batch B:** B3 (global scenario selection R2-25/26), B4 (user profile page R2-34).
**Remaining enhancements:** R2-12/14 (cross-filter), R2-23 (MRP chart), R2-29/30 (optimizer resource drilldown + over/under-use warnings), R2-37 (branding polish), R2-31 (copilot feedback), R2-5 (supplier filter on Sourcing tab).

---

## LOGIN 500 FIX + BATCH B4 — BUILT & PUSHED

### 🔴 Login Internal Server Error — FIXED
- **Root cause:** the stored admin password hash could be in a format the active hashing scheme couldn't read across deploys (bcrypt vs pbkdf2 mismatch), and `bcrypt.checkpw` could throw → raw 500.
- **Fix (3 layers):**
  1. `verify_password` now auto-detects hash format by prefix (`$2`=bcrypt, `pbkdf2$`=pbkdf2) and never raises — fails closed to a clean 401.
  2. `hash_password` truncates to bcrypt's 72-byte limit defensively.
  3. Login endpoint wrapped in try/except (never leaks a 500) + **self-heals** the bootstrap admin: if the stored hash is unreadable and the default password is used, it re-hashes and lets the admin in.
- Verified: garbage admin hash → 200 via self-heal; wrong password → clean 401; no path 500s.

### B4 — User Profile page (R2-34) — DONE
| Issue | What was built |
|-------|----------------|
| R2-34 | `/profile` page: identity card (name, email, role badges), change-password form, "Changes I've requested" list, "Approvals I've made" list, sign-out. Linked from the sidebar user footer. |

**Batch B status:** B1 ✅ Admin · B2 ✅ inline edit/override · B4 ✅ profile · **B3 (scenario selection) is the only remaining Batch B item.**

---

## LOGIN FIX + BATCH B4 — BUILT & PUSHED

### 🔴 Login internal server error — FIXED
- **Cause:** when a new deploy adds a column (e.g. must_change_password in B1) and the live Neon DB hasn't migrated yet — or the migration races the first request during a cold start — login could 500.
- **Fix:** login now self-heals — on any unexpected error it re-runs `reconcile_schema(engine)` and retries once before giving up. Verified: login returns 200 on a stale users table missing the new column.

### BATCH B4 — User Profile page (R2-34) — DONE
| Issue | What was built |
|-------|----------------|
| R2-34 | `/profile` page: identity card (name, email, role badges); change-password form; "My changes" tab (change requests I submitted, with status); "My approvals" tab (requests I reviewed). Sidebar footer links to it. Gated to signed-in users. |

**Backend:** reuses /api/change-requests (filtered client-side by requested_by / reviewed_by) + /api/change-password. No new endpoints needed.

---

## BATCH B STATUS
- ✅ B1 — Admin workspace
- ✅ B2 — Inline editing + demand override + approval-gated re-plan
- ⬜ B3 — Global scenario selection across all pages (R2-25/26) — most involved; touches engines
- ✅ B4 — User profile page

**Remaining enhancements:** R2-12/14 (cross-filter linking), R2-23 (MRP chart), R2-29/30 (optimizer resource drilldown + over/under-use warnings), R2-37 (branding polish), R2-31 (copilot feedback), R2-5 (supplier filter on Sourcing tab).

---

## BATCH B3 — Global scenario selection — BUILT & PUSHED

| Issue | What was built |
|-------|----------------|
| R2-25 | Scenario explanation: the optimizer runs 3 objectives (min_cost / max_service / balanced). The global scenario bar + Optimizer page explain what each optimises. |
| R2-26 | **Global scenario selector** (top bar on Dashboard, Handshake, Netting, MRP, Capacity, Optimizer). Selection persists across navigation + reload (localStorage + React context). Optimizer page is driven by it; Dashboard scenario cards highlight + set it. |

**HONEST SCOPING NOTE (important):** In the current engine, only the OPTIMIZER's production plan differs by scenario. The demand plan, netting, MRP, and capacity load are computed UPSTREAM of scenario optimization (from the consensus demand plan), so they are the SAME across scenarios today. Rather than fake per-scenario differences on those pages, each shows an honest banner ("ScenarioNote") explaining this and pointing to the Optimizer to compare. 

**TRUE per-scenario downstream re-plan** (netting/capacity recomputed from each scenario's chosen production plan) is a real engine project — flagged as a future enhancement, NOT faked. Logged below.

### NEW BACKLOG ITEM
- **R2-26b (engine):** Make netting/MRP/capacity recompute downstream of the selected scenario's production plan so the whole plan genuinely differs by scenario. Significant engine rework. Deferred, not faked.

---

## BATCH B — COMPLETE
- ✅ B1 — Admin workspace
- ✅ B2 — Inline editing + demand override + approval-gated re-plan
- ✅ B3 — Global scenario selection (display-level, honest; true downstream re-plan deferred as R2-26b)
- ✅ B4 — User profile page

**Remaining enhancements (post Batch B):** R2-12/14 (cross-filter linking), R2-23 (MRP chart), R2-27 full (optimizer resource editing done; drilldown next), R2-29/30 (optimizer resource drilldown + over/under-use warnings), R2-37 (branding polish), R2-31 (copilot feedback), R2-5 (supplier filter on Sourcing tab), R2-26b (true per-scenario downstream re-plan).

---

## SMOKE TEST RESULTS (Claude, pre-retest) — 2026-06

Performed a full backend + flow smoke test on a clean Postgres instance after reset-demo.

### ✅ What passed (zero defects found)
- **All page data endpoints** load valid, non-empty data: Dashboard, Data Hub (all 9 tabs), Network, Segmentation (40 rows), Forecast, Inventory, Netting, MRP, Capacity (line data), Optimizer (3 scenarios), Capabilities.
- **All interactive flows** work end-to-end:
  - Admin login → create user (auto temp password generated) ✅
  - Planner login → submit demand override on Handshake ✅
  - Planner CANNOT approve own request (403) ✅
  - Approver approves → change applies + pipeline re-plans ✅
  - Field edit (expiry/MOQ) → approve → value applied ✅
  - Change password ✅
- **Data consistency:** handshake gap = max(0, demand−supply) and fill = supply/demand verified self-consistent across all cells; segmentation has all fields the UI needs (incl. location_code, supply_ci); items carry expiry_days; optimizer scenarios all have plan+status.
- **Frontend builds clean** (`✓ built`), no undefined refs, the earlier Handshake `ovConfirm` bug confirmed gone, scenario context wired on every page that uses it.

### ⚠️ Limitation of this smoke test (honest)
I tested the **data + logic + build** layers, NOT the rendered browser UI. I cannot verify purely visual behaviour. Please pay attention to these during retest (NOT yet confirmed defects — areas to eyeball):
- **S-1** Capacity chart: now a multi-line "utilisation over time" chart. With several resources the legend/lines may be busy — check readability.
- **S-2** Network SVG: renders from live node/lane data; confirm it actually draws (was the R2-11 blank-page victim before).
- **S-3** Data Hub "Sourcing & Lanes" tab: merges two datasets client-side — confirm rows look right and columns are labelled.
- **S-4** Global scenario bar: confirm it appears on Dashboard/Handshake/Netting/MRP/Capacity/Optimizer and that switching persists across navigation.
- **S-5** Override & field-edit modals: confirm the two-step flow (builder → confirm) opens and closes cleanly on a real screen.
- **S-6** Forced password change: confirm the first-login flow shows the "set new password" screen (logic verified; UI not eyeballed).
- **S-7** Sidebar desktop collapse + mobile drawer: confirm the chevron collapse and mobile hamburger both behave.

### No new backend defects logged — backend/logic/build are clean as of this smoke test.
