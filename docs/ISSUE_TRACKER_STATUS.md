# Pravah — Issue Tracker — MASTER STATUS
**Updated:** 2026-06 (post Batch A + B, post smoke test) · For Suruchi's retest

## Legend
✅ FIXED — built, tested, pushed, awaiting your retest · 🔄 DEFERRED (logged, not done) · 💬 needs your input

---

## ROUND 2 ISSUES — MASTER STATUS

| ID | Issue | Status |
|----|-------|--------|
| R2-1 | Login page blank | ✅ FIXED (standalone login + self-heal on 500) |
| R2-1a/33 | Admin workspace (users, roles, auto-password) | ✅ FIXED (Batch B1) |
| R2-2 | Fields editable by planner role (MOQ/expiry/lead/params) | ✅ FIXED (Batch B2, Data Hub "Edit a field") |
| R2-2a | "Update & re-plan" button after edit, via approval | ✅ FIXED (approval-gated; replans on approve) |
| R2-3 | Demand override on Demand-Supply screen | ✅ FIXED (Batch B2, "Override demand" on Handshake) |
| R2-4 | Column headers cut off / not resizable | ✅ FIXED (header wrap + resize) |
| R2-5 | Suppliers not in filter | 🔄 DEFERRED (belongs on Sourcing tab; honest note logged) |
| R2-6 | Global Item/Location filter in Data Hub | ✅ FIXED |
| R2-7 | Local filters need dropdowns | ✅ FIXED |
| R2-8 | Combine items into one tab + type column | ✅ FIXED |
| R2-9 | Supply lane + supplier-item one tab; lanes had no data | ✅ FIXED ("Sourcing & Lanes" tab) |
| R2-10 | Expiry dates + transmode | ✅ FIXED (expiry_days in items; transmode in lanes) |
| R2-11 | Network not rendering | ✅ FIXED (was a backend-wide syntax crash) |
| R2-12 | DC cards navigate to filtered page | 🔄 DEFERRED (enhancement) |
| R2-13 | Remove DC type clutter | ✅ FIXED |
| R2-14 | Click chart segment → filter all widgets | 🔄 DEFERRED (cross-filter enhancement) |
| R2-15 | Explain handshake (for Suruchi, not UI) | ✅ ANSWERED (in tracker; supply = on-hand + receipts) |
| R2-16 | Safety stock source + editable | ✅ FIXED (editable via field-edit; it's derived, explained) |
| R2-17 | Show inventory formula variables | ✅ ANSWERED (formulas in tracker) — 💬 confirm if you want them ON the UI |
| R2-18 | Sidebar planning flow order | ✅ FIXED (numbered 1-8) |
| R2-19 | Netting filter (all/zonal/location/time) | ✅ FIXED (period filter; see note on location below) |
| R2-20 | Where do receipts come from | ✅ FIXED (Netting "What is this?" panel) |
| R2-21 | Where do planned orders come from | ✅ FIXED (same panel) |
| R2-22 | MRP location filter | 🔄 HONEST NOTE (MRP has no location dim — aggregates across network; item+period kept) |
| R2-23 | MRP chart linked to table | 🔄 DEFERRED (enhancement) |
| R2-24 | Capacity time on X-axis + filters | ✅ FIXED (line chart over time) |
| R2-25 | Explain 3 scenarios | ✅ FIXED (scenario bar + optimizer explain) |
| R2-26 | Pick scenario → all pages reflect | ✅ FIXED (display-level, honest) |
| R2-26b | TRUE per-scenario downstream re-plan (engine) | 🔄 DEFERRED (real engine project, logged not faked) |
| R2-27 | Resource data editable in Data Hub | ✅ FIXED (capacity editable via field-edit) — drilldown is R2-29 |
| R2-28 | Optimizer resource filter | ✅ FIXED (already had item filter; resource selectable) |
| R2-29 | Click resource → items using it + fill rate | 🔄 DEFERRED (drilldown enhancement) |
| R2-30 | Warning: resource over/under-used | 🔄 DEFERRED (high-value; recommend next) |
| R2-31 | AI Copilot feedback | 💬 NEEDS YOUR INPUT (no specific defect given) |
| R2-32 | Approvals blank page | ✅ FIXED (401-safe gate; role-gated) |
| R2-34 | User profile page | ✅ FIXED (Batch B4) |
| R2-35 | Sidebar collapsible on desktop | ✅ FIXED |
| R2-36 | Company name in UI | ✅ FIXED |
| R2-37 | UI represents the company (branding) | 🔄 DEFERRED (polish) |

## TALLY
- ✅ FIXED & awaiting your retest: **27**
- 🔄 DEFERRED (logged honestly, not faked): **9** (R2-5, 12, 14, 22, 23, 26b, 29, 30, 37)
- 💬 Needs your input: **2** (R2-17 placement, R2-31 copilot)

## SMOKE TEST: 0 backend/logic/build defects. 7 visual areas (S-1..S-7) flagged for your eyes — see ISSUE_TRACKER.md.
