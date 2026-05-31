"""Central config. DATABASE_URL from env (Neon in prod); SQLite fallback for local/tests."""
import os

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///pravah.db")
DEFAULT_TENANT = os.environ.get("DEFAULT_TENANT", "apex")

# LLM provider for the Copilot (optional). Order of preference: Groq, then Anthropic.
# Keys live ONLY as server env vars — never in code or the frontend.
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
# Default Groq model — fast, free-tier friendly. Override with GROQ_MODEL env var.
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
