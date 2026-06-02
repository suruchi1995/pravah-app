"""
Auth — self-hosted, no external service.
========================================
- Passwords hashed with bcrypt (never stored raw).
- Login issues a JWT (signed token the browser holds; sent as Bearer header).
- Roles checked per-endpoint. A user may hold multiple roles.

Secret for signing tokens comes from JWT_SECRET env var (set on Render).
Falls back to a dev secret locally so tests run.
"""
import os, sys, time, hmac, hashlib, base64, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend import models as m

JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-in-render")
TOKEN_TTL_SECONDS = 60 * 60 * 12  # 12 hours

# ---- password hashing (bcrypt via passlib if available, else hashlib fallback) ----
try:
    import bcrypt
    def hash_password(pw: str) -> str:
        return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
    def verify_password(pw: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(pw.encode(), hashed.encode())
        except Exception:
            return False
except ImportError:
    # fallback: PBKDF2 (still salted+hashed; bcrypt preferred in prod)
    def hash_password(pw: str) -> str:
        salt = os.urandom(16)
        dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 100000)
        return "pbkdf2$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(dk).decode()
    def verify_password(pw: str, hashed: str) -> bool:
        try:
            _, salt_b64, dk_b64 = hashed.split("$")
            salt = base64.b64decode(salt_b64)
            dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 100000)
            return hmac.compare_digest(base64.b64encode(dk).decode(), dk_b64)
        except Exception:
            return False


# ---- minimal JWT (HS256), no external lib ----
def _b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def _b64u_decode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))

def make_token(user) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user.email, "tenant": user.tenant_id, "roles": user.roles,
        "name": user.full_name, "exp": int(time.time()) + TOKEN_TTL_SECONDS,
    }
    h = _b64u(json.dumps(header).encode())
    p = _b64u(json.dumps(payload).encode())
    sig = _b64u(hmac.new(JWT_SECRET.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest())
    return f"{h}.{p}.{sig}"

def verify_token(token: str):
    try:
        h, p, sig = token.split(".")
        expected = _b64u(hmac.new(JWT_SECRET.encode(), f"{h}.{p}".encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(_b64u_decode(p))
        if payload.get("exp", 0) < time.time():
            return None
        return payload
    except Exception:
        return None


# ---- permissions ----
APPROVER_ROLES = {"approver", "management", "admin"}
EDITOR_ROLES = {"planner", "admin"}
ADMIN_ROLES = {"admin"}

def can_approve(roles): return bool(set(roles) & APPROVER_ROLES)
def can_edit(roles):    return bool(set(roles) & EDITOR_ROLES)
def is_admin(roles):    return bool(set(roles) & ADMIN_ROLES)


def authenticate(session, email, password):
    user = session.query(m.User).filter_by(email=email.lower().strip(), is_active=True).first()
    if user and verify_password(password, user.password_hash):
        return user
    return None


def seed_admin(session, tenant_id="demo", email="admin@pravah.app", password="changeme123",
               name="Demo Admin"):
    """Ensure a bootstrap admin exists so the app is never locked out.
    Password should be changed immediately in production."""
    if not session.query(m.Tenant).filter_by(tenant_id=tenant_id).first():
        session.add(m.Tenant(tenant_id=tenant_id, name=f"{tenant_id} tenant"))
    if not session.query(m.User).filter_by(email=email).first():
        session.add(m.User(
            tenant_id=tenant_id, email=email, password_hash=hash_password(password),
            full_name=name, roles_csv="admin,planner,approver,management", is_active=True))
    session.commit()
