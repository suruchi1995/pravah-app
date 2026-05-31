"""
End-to-end API test — every screen's endpoint + the upload validate/reject flow.
Run: python3 tests/test_api.py
"""
import os, sys, io
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import warnings; warnings.filterwarnings("ignore")
from fastapi.testclient import TestClient
from backend.main import app

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
c = TestClient(app)
checks = []
def check(name, cond, detail=""):
    checks.append((name, bool(cond), detail))

# fresh demo
c.post("/api/reset-demo")

check("health ok", c.get("/api/health").json()["status"] == "ok")

s = c.get("/api/summary").json()
check("summary has 10 FGs", s["finished_goods"] == 10)
check("summary revenue-at-risk > 0", s["total_revenue_at_risk"] > 0)
check("summary has a bottleneck", s["capacity_bottlenecks"] >= 1)

check("segmentation 10 rows", len(c.get("/api/segmentation").json()) == 10)
check("forecast series 6 months", len(c.get("/api/forecast?item=FG001&location=DC_DEL").json()) == 6)
check("handshake 30 rows", len(c.get("/api/handshake").json()) == 30)
check("inventory targets 30", len(c.get("/api/inventory-targets").json()) == 30)
check("netting FG001 has rows", len(c.get("/api/netting?item=FG001").json()) > 0)
check("mrp has rows", len(c.get("/api/mrp").json()) > 0)
check("capacity has rows", len(c.get("/api/capacity").json()) > 0)
opt = c.get("/api/optimizer").json()
check("optimizer 3 scenarios", set(opt.keys()) == {"min_cost", "max_service", "balanced"})
check("each scenario has a plan", all(len(v["plan"]) > 0 for v in opt.values()))

# template downloads
t = c.get("/api/template")
check("template downloads", t.status_code == 200 and len(t.content) > 1000)

# upload valid -> new tenant planned independently
with open(os.path.join(ROOT, "Pravah_Apex_Dataset_v2.xlsx"), "rb") as f:
    r = c.post("/api/upload?tenant=e2e_client",
               files={"file": ("d.xlsx", f.read(),
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
check("valid upload accepted", r.json().get("ok") is True, str(r.json())[:200])
check("uploaded tenant planned", c.get("/api/summary?tenant=e2e_client").json()["finished_goods"] == 10)

# upload broken -> rejected with actionable error
import openpyxl
wb = openpyxl.load_workbook(os.path.join(ROOT, "Pravah_Apex_Dataset_v2.xlsx"))
wb["bom"].append(["x", "FG001", "RM_GHOST", 5, "", ""])
buf = io.BytesIO(); wb.save(buf); buf.seek(0)
r = c.post("/api/upload?tenant=e2e_bad",
           files={"file": ("b.xlsx", buf.read(),
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
j = r.json()
check("broken upload rejected", j.get("ok") is False)
check("rejection names the ghost ref", any("RM_GHOST" in e["message"] for e in j.get("errors", [])))

passed = sum(1 for _, ok, _ in checks if ok)
print(f"\nAPI E2E TESTS: {passed}/{len(checks)} passed\n" + "-"*50)
failed = False
for name, ok, detail in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f"  -> {detail}" if not ok else ""))
    if not ok: failed = True
sys.exit(1 if failed else 0)
