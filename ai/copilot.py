"""
AI Copilot
==========
Answers planning questions from STORED engine outputs.

- If ANTHROPIC_API_KEY is set (server env var only), calls Claude with a grounded
  context built from real facts + a strict "use only these facts" instruction.
- If not set, returns a deterministic, rule-based answer over the same facts so the
  product always works (and the demo never depends on a key being present).

The browser NEVER calls Anthropic directly and never sees the key; it calls our
backend, which holds the key as an environment variable.
"""
import os, sys, re, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend import models as m
from backend.config import (DEFAULT_TENANT, ANTHROPIC_API_KEY, GROQ_API_KEY, GROQ_MODEL)
from ai.context import gather_facts, facts_for_sku, build_context_text

SYSTEM = (
    "You are Pravah's supply-chain planning copilot. Answer concisely and "
    "concretely using ONLY the planning facts provided. Never invent numbers. "
    "When you cite a figure, it must come from the facts. If the facts don't "
    "cover the question, say what's missing. Prefer a short answer plus one or "
    "two specific, actionable recommendations grounded in the data."
)

SUGGESTED = [
    "Why am I stocking out?",
    "What is my revenue at risk?",
    "Which products should I prioritise producing?",
    "Where is my capacity bottleneck?",
    "What's the difference between the cost and service plans?",
    "Why is FG006 short?",
]


def _detect_sku(question):
    mt = re.search(r"\b(FG0\d{2}|SFG00\d|RM0\d{2}|PM00\d)\b", question.upper())
    return mt.group(1) if mt else None


def _llm_answer(question, context_text):
    """Call Anthropic Messages API. Returns text or raises."""
    import httpx
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 700,
        "system": SYSTEM + "\n\n" + context_text,
        "messages": [{"role": "user", "content": question}],
    }
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    r = httpx.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers, timeout=40)
    r.raise_for_status()
    data = r.json()
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")


def _groq_answer(question, context_text):
    """Call Groq (OpenAI-compatible chat completions). Returns text or raises."""
    import httpx
    payload = {
        "model": GROQ_MODEL,
        "max_tokens": 700,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": SYSTEM + "\n\n" + context_text},
            {"role": "user", "content": question},
        ],
    }
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    r = httpx.post("https://api.groq.com/openai/v1/chat/completions",
                   json=payload, headers=headers, timeout=40)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]


def _rule_based_answer(question, facts, session, tenant):
    q = question.lower()
    sku = _detect_sku(question)

    if sku:
        f = facts_for_sku(session, sku, tenant)
        gaps = [h for h in f.get("handshake", []) if h["gap"] > 0]
        if gaps:
            worst = max(gaps, key=lambda x: x["revenue_at_risk"])
            seg = f.get("segment", "n/a")
            return (f"{sku} (segment {seg}) is short primarily at {worst['dc']}: demand "
                    f"{worst['demand']} vs available supply {worst['supply']} — a gap of "
                    f"{worst['gap']} units ({worst['fill_rate']*100:.0f}% fill), putting "
                    f"Rs {worst['revenue_at_risk']:,.0f} of revenue at risk. "
                    f"Recommended action: {worst['recommendation']}")
        return f"{sku} has no supply gap in the current plan — available supply covers demand."

    if "revenue at risk" in q or "revenue risk" in q or ("risk" in q and "revenue" in q):
        top = facts["top_gaps"][:3]
        tops = "; ".join(f"{g['sku']}@{g['dc']} Rs {g['revenue_at_risk']:,.0f}" for g in top)
        return (f"Total revenue at risk is Rs {facts['total_revenue_at_risk']:,.0f} "
                f"(margin at risk Rs {facts['total_margin_at_risk']:,.0f}). "
                f"Biggest exposures: {tops}.")

    if "stock" in q or "short" in q or "stockout" in q:
        top = facts["top_gaps"][:3]
        items = "; ".join(f"{g['sku']} @ {g['dc']} (fill {g['fill_rate']*100:.0f}%, gap {g['gap']})" for g in top)
        return (f"The biggest shortfalls are: {items}. Across the network, "
                f"Rs {facts['total_revenue_at_risk']:,.0f} of revenue is at risk. The common "
                f"driver is the filling line bottleneck limiting what can be produced for the peak period.")

    if "bottleneck" in q or "capacity" in q:
        if facts["bottlenecks"]:
            b = facts["bottlenecks"][0]
            return (f"The binding capacity constraint is {b['resource']} at "
                    f"{b['utilization']*100:.0f}% utilisation ({b['status']}). It caps how much "
                    f"can be produced in the peak period, which is why some demand goes unmet.")
        return "No resource is currently at or above the tight-capacity threshold."

    if "prioriti" in q or "produce" in q or "what should i" in q:
        seg = sorted(facts["segmentation"], key=lambda x: -x["annual_value"])[:4]
        names = ", ".join(f"{s['sku']} ({s['class']})" for s in seg)
        return (f"Prioritise high-value A-items first: {names}. These carry the most annual value, "
                f"so protecting their service level preserves the most revenue when capacity is tight.")

    if "cost" in q and "service" in q:
        sc = {s["scenario"]: s["reasoning"] for s in facts["scenarios"]}
        return (f"Min-cost plan: {sc.get('min_cost','n/a')} "
                f"Max-service plan: {sc.get('max_service','n/a')} "
                f"The cost plan shorts low-margin SKUs; the service plan produces them at higher cost to lift fill.")

    # default
    return (f"Here's the current planning picture: Rs {facts['total_revenue_at_risk']:,.0f} revenue at risk, "
            f"forecast accuracy {facts.get('avg_mape','?')}% MAPE, and "
            f"{len(facts['bottlenecks'])} capacity bottleneck(s). Ask about a specific SKU "
            f"(e.g. 'why is FG006 short?'), revenue at risk, bottlenecks, or the optimizer scenarios.")


def ask(session, question, tenant=DEFAULT_TENANT):
    facts = gather_facts(session, tenant)
    context_text = build_context_text(facts)
    used_llm = False
    provider = None
    # preference: Groq, then Anthropic, then deterministic fallback
    if GROQ_API_KEY:
        try:
            answer = _groq_answer(question, context_text); used_llm = True; provider = "groq"
        except Exception:
            answer = _rule_based_answer(question, facts, session, tenant)
    elif ANTHROPIC_API_KEY:
        try:
            answer = _llm_answer(question, context_text); used_llm = True; provider = "anthropic"
        except Exception:
            answer = _rule_based_answer(question, facts, session, tenant)
    else:
        answer = _rule_based_answer(question, facts, session, tenant)
    return {"answer": answer, "grounded_on": context_text, "used_llm": used_llm,
            "provider": provider, "suggested": SUGGESTED}


if __name__ == "__main__":
    from backend.config import DATABASE_URL
    eng = m.make_engine(DATABASE_URL); Session = m.make_session_factory(eng)
    with Session() as ssn:
        for q in ["Why am I stocking out?", "Why is FG006 short?",
                  "What is my revenue at risk?", "Where is my capacity bottleneck?",
                  "What's the difference between the cost and service plans?"]:
            r = ask(ssn, q)
            print(f"\nQ: {q}\nA: {r['answer']}")
