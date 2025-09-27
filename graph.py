from __future__ import annotations
from typing import TypedDict, List, Dict, Any, Optional, Literal
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
from planner import make_plan
from tools import TOOLS


class AgentState(TypedDict, total=False):
    query: str
    plan: List[Dict[str, Any]]
    step_index: int
    scratchpad: List[Dict[str, Any]]
    final_answer: str
    needs_replan: bool


def planner_node(state: AgentState) -> AgentState:
    if state.get("plan") and not state.get("needs_replan"):
        return state
    plan = make_plan(state["query"])
    return {
        **state,
        "plan": plan,
        "step_index": 0,
        "needs_replan": False,
    }

def executor_node(state: AgentState) -> AgentState:
    plan = state.get("plan", [])
    idx = int(state.get("step_index", 0))

    if idx >= len(plan):
        #nothing to execute
        return state

    step = plan[idx]
    tool = (step.get("tool") or "none").lower()
    tool_input = step.get("input") or ""

    if tool == "none":
        out = f"No tools required. Consider answering directly based on the query."
    else:
        if tool not in TOOLS:
            out = f"Unknown tool '{tool}'. Triggering replan."
            return {**state, "needs_replan": True}
        out = TOOLS[tool]["func"](tool_input)

    new_scratch = list(state.get("scratchpad", []))
    new_scratch.append({"tool": tool, "input": tool_input, "output": out})

    return {
        **state,
        "scratchpad": new_scratch,
        "step_index": idx + 1,
    }

def should_continue(state: AgentState) -> Literal["executor","finalize","planner"]:
    #If asked to replan, go to planner
    if state.get("needs_replan"):
        return "planner"
    plan = state.get("plan", [])
    idx = int(state.get("step_index", 0))
    if idx < len(plan):
        return "executor"
    return "finalize"

def finalizer_node(state: AgentState) -> AgentState:
    query = state["query"]
    scratch = state.get("scratchpad", [])
    lines = [f"Query: {query}", ""]
    for i, s in enumerate(scratch, 1):
        lines.append(f"Step {i}: tool={s['tool']} input={s['input']}")
        lines.append(f"Output: {s['output']}")
        lines.append("")
    conclusion = "Conclusion:\n"
    if any(s["tool"]=="sql" for s in scratch):
        import re
        joined = "\n".join(s["output"] for s in scratch if s["tool"]=="sql")
        m = re.search(r"total\s*\|\s*([0-9\.]+)", joined, flags=re.I)
        if m:
            conclusion += f"- Total sales: {m.group(1)}\n"
    if any(s["tool"]=="calculator" for s in scratch):
        calc_out = [s["output"] for s in scratch if s["tool"]=="calculator"][-1]
        conclusion += f"- Calculation: {calc_out}\n"
    if any(s["tool"]=="weather" for s in scratch):
        w = [s["output"] for s in scratch if s["tool"]=="weather"][-1]
        conclusion += f"- Weather: {w}\n"
    if conclusion.strip() == "Conclusion:":
        conclusion += "- No tool outputs to summarize; answer directly."
    lines.append(conclusion)
    final = "\n".join(lines)
    return {**state, "final_answer": final}


def build_graph():
    g = StateGraph(AgentState)

    g.add_node("planner", planner_node)
    g.add_node("executor", executor_node)
    g.add_node("finalize", finalizer_node)

    g.set_entry_point("planner")

    g.add_conditional_edges(
        "planner",
        should_continue,
        {"executor": "executor", "finalize": "finalize", "planner": "planner"},
    )
    g.add_conditional_edges(
        "executor",
        should_continue,
        {"executor": "executor", "finalize": "finalize", "planner": "planner"},
    )
    g.add_edge("finalize", END)

    app = g.compile()
    return app

GRAPH_APP = build_graph()

def run_agent(query: str) -> dict:
    state: AgentState = {
        "query": query,
        "plan": [],
        "scratchpad": [],
        "step_index": 0,
        "needs_replan": False,
    }
    out = GRAPH_APP.invoke(state)
    return {
        "plan": out.get("plan", []),
        "scratchpad": out.get("scratchpad", []),
        "final_answer": out.get("final_answer", ""),
    }
