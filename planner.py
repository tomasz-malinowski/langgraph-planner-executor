from __future__ import annotations
import os, json, re
from typing import List, Dict, Any, Optional

USE_LLM = bool(os.getenv("OPENAI_API_KEY"))
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def rule_based_plan(query: str) -> List[Dict[str, Any]]:
    """Return a simple plan as a list of {tool, input, note} steps."""
    plan: List[Dict[str, Any]] = []
    q = query.lower()

    if "weather" in q or any(city in q for city in ["warsaw", "helsinki", "innsbruck"]):
        m = re.search(r"(warsaw|helsinki|innsbruck)", q)
        city = m.group(1) if m else "Warsaw"
        plan.append({"tool":"weather", "input": city, "note": "Get weather info."})

    if "sale" in q or "revenue" in q or "q1" in q or "sum" in q:
        if "q1" in q:
            sql = "SELECT SUM(amount) as total FROM sales WHERE quarter='Q1';"
        else:
            sql = "SELECT quarter, SUM(amount) as total FROM sales GROUP BY quarter ORDER BY quarter;"
        plan.append({"tool":"sql", "input": sql, "note":"Aggregate sales."})

    mexpr = re.search(r"([0-9\+\-\*\/\(\)\.\s]{5,})", query)
    if mexpr:
        plan.append({"tool":"calculator", "input": mexpr.group(1), "note":"Compute arithmetic."})

    if not plan:
        plan.append({"tool":"none", "input": query, "note":"No tools required; answer directly."})

    return plan

def llm_plan(query: str) -> List[Dict[str, Any]]:
    """Ask an LLM to produce a JSON plan with steps."""
    from openai import OpenAI
    client = OpenAI()

    system = (
        "You are a planning assistant. Create a minimal plan as JSON with a key 'steps', "
        "each step an object with fields: tool (one of: sql, calculator, weather, none), input (string), note (string). "
        "Only use available tools. If no tool is needed, return one step with tool='none'."
    )
    user = f"User query:\n{query}\nProduce JSON only."

    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role":"system","content":system},
            {"role":"user","content":user},
        ],
        temperature=0.1,
    )

    text = resp.choices[0].message.content.strip()
    m = re.search(r"\{.*\}", text, flags=re.S)
    data = {}
    if m:
        try:
            data = json.loads(m.group(0))
        except Exception:
            pass
    steps = data.get("steps") if isinstance(data, dict) else None
    if isinstance(steps, list):
        out = []
        for s in steps:
            tool = str(s.get("tool","none")).lower()
            if tool not in {"sql","calculator","weather","none"}:
                tool = "none"
            out.append({
                "tool": tool,
                "input": str(s.get("input","")).strip(),
                "note": str(s.get("note","")).strip(),
            })
        return out
    return rule_based_plan(query)

def make_plan(query: str) -> List[Dict[str, Any]]:
    if USE_LLM:
        try:
            return llm_plan(query)
        except Exception:
            return rule_based_plan(query)
    else:
        return rule_based_plan(query)
