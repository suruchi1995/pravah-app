"""Central config. DATABASE_URL from env (Neon in prod); SQLite fallback for local/tests."""
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///pravah.db")
DEFAULT_TENANT = os.environ.get("DEFAULT_TENANT", "apex")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")  # set only as server env var
