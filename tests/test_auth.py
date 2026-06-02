"""
Auth + approval-workflow tests. Run: python3 tests/test_auth.py
Uses SQLite in-memory so it runs anywhere (same models as Postgres).
"""
import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import warnings; warnings.filterwarnings("ignore")
_dbfile = os.path.join(tempfile.gettempdir(), "pravah_auth_test.db")
if os.path.exists(_dbfile):
    os.remove(_dbfile)
os.environ["DATABASE_URL"] = f"sqlite:///{_dbfile}"

from fastapi.testclient import TestClient
from backend.main import app, Session
from backend import models as m, auth
from backend.seed_loader import load
from planning.run_all import run_pipeline

checks = []
def chk(name, cond): checks.append((name, bool(cond)))

with Session() as s:
    load(s); run_pipeline(s, "apex")
    s.add(m.User(tenant_id="apex", email="planner@apex.com", password_hash=auth.hash_password("pass123"),
                 full_name="Priya", roles_csv="planner", is_active=True))
    s.add(m.User(tenant_id="apex", email="boss@apex.com", password_hash=auth.hash_password("pass123"),
                 full_name="Manish", roles_csv="approver", is_active=True))
    s.commit()
    p0 = sorted({d.period for d in s.query(m.DemandPlan).filter_by(tenant_id="apex", item_code="FG001")})[0]

c = TestClient(app)
H = lambda t: {"Authorization": "Bearer " + t}

chk("bad login rejected", c.post("/api/login", json={"email": "planner@apex.com", "password": "x"}).status_code == 401)
pt = c.post("/api/login", json={"email": "planner@apex.com", "password": "pass123"}).json()["token"]
bt = c.post("/api/login", json={"email": "boss@apex.com", "password": "pass123"}).json()["token"]
at = c.post("/api/login", json={"email": "admin@pravah.app", "password": "changeme123"}).json()["token"]
chk("protected endpoint blocked w/o token", c.get("/api/parameters").status_code == 401)
chk("me returns identity", c.get("/api/me", headers=H(pt)).json().get("sub") == "planner@apex.com")

sub = c.post("/api/change-requests", headers=H(pt), json={
    "change_type": "demand_override", "target": "FG001/DC_DEL",
    "payload": {"item_code": "FG001", "location_code": "DC_DEL", "period": p0,
                "override_qty": 40, "override_type": "uplift_pct", "reason": "listing"},
    "old_value": "fc", "new_value": "+40%"}).json()
chk("planner submits change", sub.get("ok"))
crid = sub["id"]
chk("planner CANNOT approve own change", c.post(f"/api/change-requests/{crid}/approve", headers=H(pt), json={"note": ""}).status_code == 403)
appr = c.post(f"/api/change-requests/{crid}/approve", headers=H(bt), json={"note": "ok"}).json()
chk("approver approves + replans", appr.get("ok") and appr.get("replanned"))

with Session() as s:
    dp = s.query(m.DemandPlan).filter_by(tenant_id="apex", item_code="FG001", location_code="DC_DEL", period=p0).first()
    chk("approved override flows into plan", dp and dp.override_qty and dp.override_qty > dp.statistical_qty)

chk("audit log records approval", any(a["action"] == "approve_change" for a in c.get("/api/audit-log", headers=H(bt)).json()))
chk("admin creates user", c.post("/api/users", headers=H(at), json={"email": "v@a.com", "password": "p", "full_name": "V", "roles": ["viewer"]}).json().get("ok"))
chk("planner cannot create user", c.post("/api/users", headers=H(pt), json={"email": "z@a.com", "password": "p", "full_name": "Z", "roles": ["viewer"]}).status_code == 403)
chk("reject works", c.post("/api/change-requests", headers=H(pt), json={"change_type": "parameter", "target": "x", "payload": {"name": "ses_alpha", "value": 0.5}}).json().get("ok"))

passed = sum(1 for _, ok in checks if ok)
print(f"\nAUTH TESTS: {passed}/{len(checks)} passed\n" + "-" * 40)
failed = False
for name, ok in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    if not ok: failed = True
sys.exit(1 if failed else 0)
