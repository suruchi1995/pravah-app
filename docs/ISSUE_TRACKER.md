# Pravah — Testing Issue Tracker

**Owner:** Suruchi | **Started:** 2026-06 testing week
**How we work:** Suruchi tests → logs an issue → we discuss → analyse → solve → push → Suruchi re-tests on live → mark Certified.

## Status lifecycle
`IDENTIFIED` → `DISCUSSING` → `ANALYSED` → `IN PROGRESS` → `FIXED (awaiting test)` → `CERTIFIED ✅` (or `WON'T FIX` / `DEFERRED`)

## Severity
🔴 Blocker · 🟠 Major · 🟡 Minor · 🔵 Enhancement

---

## Summary table

| ID | Area | Issue (short) | Severity | Status |
|----|------|---------------|----------|--------|
| 1 | Auth | Login page + approvals don't exist on live | 🟠 Major | IDENTIFIED |
| 2 | Filters | Add hierarchy in filter (e.g. whole North zone together) | 🔵 Enh | IDENTIFIED |
| 3 | Dashboard | More informative — more/better KPIs (Finished Goods isn't a KPI) | 🟠 Major | IDENTIFIED |
| 4 | Dashboard | KPI cards should be clickable → deep-dive to source screen | 🔵 Enh | IDENTIFIED |
| 5 | Dashboard | Bottleneck card → click shows real issue + suggested fix | 🔵 Enh | IDENTIFIED |
| 6 | Dashboard | Add filters: Item, Location, Time | 🟠 Major | IDENTIFIED |
| 7 | Data Hub | Add global filter; local filters need dropdowns too (everywhere) | 🟡 Minor | IDENTIFIED |
| 8 | Data Hub | UOM inconsistent in UI; are we using UOM in demand/production calc? Standardise (ask kg) or add UOM conversion DB | 🟠 Major | IDENTIFIED |
| 9 | Data Hub | Better headings; "unit price or cost" → "price per unit" | 🟡 Minor | IDENTIFIED |
| 10 | Data / Model | Where do we capture: MOQ, lane lead-time (origin→dest), resources producing FG, where-produced, transmode, expiry? Add lanes concept. Expiry in item dim. | 🟠 Major | IDENTIFIED |
| 11 | Network | Are suppliers/packaging used by any item? If not, fix data | 🟠 Major | IDENTIFIED |
| 12 | Network | Add location filter | 🟡 Minor | IDENTIFIED |
| 13 | Network | "Something is missing" (to be specified) | 🟡 Minor | IDENTIFIED |
| 14 | Segmentation | Less reasoning text; more charts | 🔵 Enh | IDENTIFIED |
| 15 | Segmentation | Do CI / predictability / supply-capability segmentation at item-location level | 🟠 Major | IDENTIFIED |
| 16 | Segmentation | Add location; segment at item-location level | 🟠 Major | IDENTIFIED |
| 17 | Segmentation | Add top/least item & location to focus on | 🔵 Enh | IDENTIFIED |

---

## Issue detail log

### Issue #1 — Auth login page + approvals don't exist on live
- **Area:** Auth
- **Reported:** Login/approval UI not visible on the live app.
- **Status:** IDENTIFIED
- **Notes:** Backend auth (login, roles, approval workflow, audit) is BUILT & tested (11/11) but the read endpoints are deliberately left open and there is NO frontend login screen yet. This is expected — we held it for the testing week. Decision needed: build the login UI + approval inbox now, or after testing week.
- **Resolution:** _pending_

### Issue #2 — Filter hierarchy (zones)
- **Area:** Filters
- **Reported:** Want to view whole North zone data together (hierarchy in filters).
- **Status:** IDENTIFIED
- **Notes:** Locations have a `zone` field already. Need: zone → DC hierarchy in the FilterBar (select a zone = all its DCs).
- **Resolution:** _pending_

### Issue #3 — Dashboard more informative / better KPIs
- **Area:** Dashboard
- **Reported:** Finished Goods count isn't a real KPI; want more meaningful metrics.
- **Status:** IDENTIFIED
- **Notes:** Candidate KPIs: total revenue at risk, avg fill rate, forecast MAPE, # SKUs at risk, # bottlenecks, on-time/cover days, inventory value. Need to agree the headline set.
- **Resolution:** _pending_

### Issue #4 — Clickable KPI cards (deep dive)
- **Area:** Dashboard
- **Reported:** Clicking a KPI (e.g. Avg Fill Rate) should navigate to the screen showing that calculation.
- **Status:** IDENTIFIED
- **Resolution:** _pending_

### Issue #5 — Bottleneck card → real issue + suggestion
- **Area:** Dashboard
- **Reported:** Clicking the Bottleneck KPI should show the actual constrained resource and a recommended action.
- **Status:** IDENTIFIED
- **Resolution:** _pending_

### Issue #6 — Dashboard filters (Item/Location/Time)
- **Area:** Dashboard
- **Reported:** Dashboard has no filters.
- **Status:** IDENTIFIED
- **Resolution:** _pending_

### Issue #7 — Data Hub filters + dropdowns everywhere
- **Area:** Data Hub / global
- **Reported:** Data Hub needs the global filter; local filters should also have dropdowns (easier). Apply consistently across all screens.
- **Status:** IDENTIFIED
- **Resolution:** _pending_

### Issue #8 — UOM consistency + usage in calculations
- **Area:** Data Hub / engine
- **Reported:** Different UOMs shown; should be consistent. Are we using UOM in demand/production calc? Proposal: ask clients to fill in kg; if they can't, need a UOM conversion table.
- **Status:** IDENTIFIED
- **Notes:** IMPORTANT correctness question — need to check whether engines assume a single UOM. If mixed UOM exists without conversion, calculations could be wrong.
- **Resolution:** _pending_

### Issue #9 — Headings / labels
- **Area:** Data Hub
- **Reported:** Improve headings; "unit price or cost" → "price per unit".
- **Status:** IDENTIFIED
- **Resolution:** _pending_

### Issue #10 — Missing data concepts (MOQ, lanes, transmode, expiry, where-produced)
- **Area:** Data model / contract
- **Reported:** Where are we capturing MOQ, lane lead-time (origin→destination), resources that produce each FG, where each item is produced, transport mode, expiry date? Proposal: add a "lanes" concept (item shipped/produced/procured from X to Y via transmode, with min lot size + lead time). Expiry can live in item dimension. Ask these in the 7/9 templates.
- **Status:** IDENTIFIED
- **Notes:** Significant data-model extension. Need to map what exists vs what's missing, then decide template changes.
- **Resolution:** _pending_

### Issue #11 — Suppliers/packaging not used by any item?
- **Area:** Network / data
- **Reported:** It looks like no item uses suppliers or packaging materials. If true, fix the demo data so the BOM/sourcing actually connects.
- **Status:** IDENTIFIED
- **Notes:** Need to inspect BOM + supplier_item_mapping to confirm whether RM/PM and suppliers are actually linked to FGs.
- **Resolution:** _pending_

### Issue #12 — Network location filter
- **Area:** Network
- **Reported:** Add a location filter to the Network page.
- **Status:** IDENTIFIED
- **Resolution:** _pending_

### Issue #13 — Network "something is missing"
- **Area:** Network
- **Reported:** Suruchi senses something missing — to be specified.
- **Status:** IDENTIFIED
- **Resolution:** _pending_

### Issue #14 — Segmentation: fewer words, more charts
- **Area:** Segmentation
- **Reported:** Reasoning text is too detailed; want more charts instead.
- **Status:** IDENTIFIED
- **Resolution:** _pending_

### Issue #15 — Segmentation: CI / predictability / supply-capability
- **Area:** Segmentation
- **Reported:** Move beyond ABC/XYZ to product segmentation that includes criticality/CI, predictability, and supply capability — more useful for planners & CEO at item-location level.
- **Status:** IDENTIFIED
- **Resolution:** _pending_

### Issue #16 — Segmentation at item-location level
- **Area:** Segmentation
- **Reported:** Add location; segment at the lowest (item-location) level to see which item impacts which location most.
- **Status:** IDENTIFIED
- **Resolution:** _pending_

### Issue #17 — Segmentation: top/least focus items
- **Area:** Segmentation
- **Reported:** Show top item, least item, top/least location to focus on.
- **Status:** IDENTIFIED
- **Resolution:** _pending_


---

## Status update — 2026-06 batch

- **Issue #1:** IN PROGRESS — Login screen + Approvals inbox built. Auth endpoints deployed (additive). Frontend login page at /login. Approvals page in nav. **Awaiting test on live site.**
- **Issue #2:** FIXED — Zone added as filter hierarchy in FilterBar. All pages with location filter now show Zone → Location hierarchy.
- **Issue #3:** FIXED — Dashboard KPIs replaced: Revenue at Risk, Avg Fill Rate, SKUs at Risk, Forecast MAPE, Capacity Bottlenecks. Finished Goods removed.
- **Issue #4:** FIXED — All KPI cards are clickable and navigate to the relevant screen.
- **Issue #5:** FIXED — Bottleneck card shows popup with resource name, utilisation, and specific suggested fix. Also navigates to Capacity page.
- **Issue #6:** FIXED — Dashboard has Item/Location/Period/Zone filters. KPIs and chart filter accordingly.
- **Issue #7:** FIXED — DataHub tabs expanded (FG/RM/PM/SFG/All/Lanes/Supplier-Item). Column labels humanised everywhere.
- **Issue #8:** DISCUSSED — UOM labels now shown on all quantity columns. BOM quantities are already in component UOM (correct by convention). UOM conversion table deferred to next session.
- **Issue #9:** FIXED — "unit_price_or_cost" → "Price per Unit (₹)", all column headers humanised.
- **Issue #10:** FIXED — supply_lanes table added (item-specific origin→destination, transmode, lead time, min lot). 42 demo lanes seeded (supplier→plant + plant→DC per FG). Shown in Data Hub + Network.
- **Issue #11:** FIXED — PM items visible in Data Hub (PM tab). Supplier-Item mapping tab added. Supply lanes show explicit supplier→RM/PM→plant→DC flows.
- **Issue #12:** FIXED — Network page has Zone + Location + Item filters.
- **Issue #14:** FIXED — Segmentation rewritten: ABC bar chart + XYZ pie chart + matrix. CoV column removed. Less text, charts lead.
- **Issue #17:** FIXED — Top 5 items by value, bottom 3, erratic (Z) items shown as focus lists.