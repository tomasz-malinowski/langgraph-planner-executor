from __future__ import annotations
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from graph import run_agent

app = FastAPI(title="Planner→Executor Agent (LangGraph)")

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    plan: list
    scratchpad: list
    final_answer: str

@app.get("/", response_class=HTMLResponse)
def home():
    return """<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Planner→Executor Agent</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body { font-family: system-ui, sans-serif; max-width: 820px; margin: 2rem auto; padding: 0 1rem; }
    textarea { width: 100%; min-height: 90px; }
    pre { background: #f6f8fa; padding: 12px; overflow:auto; }
    button { padding: 8px 14px; cursor: pointer; }
    .row { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
    .examples button { background:#efefef; border:1px solid #ddd; }
  </style>
</head>
<body>
  <h1>Planner → Executor Agent</h1>
  <p>Type a query and the agent will plan tool calls (SQL / calculator / weather), execute them, and summarize.</p>
  <div class="examples">
    <div class="row">
      <span>Examples:</span>
      <button onclick="setQ(`What were total sales in Q1 and what is 12*(7+1)?`)">Q1 + math</button>
      <button onclick="setQ(`What's the weather in Warsaw and sum revenue by quarter?`)">Weather + SQL</button>
      <button onclick="setQ(`Compute 3*(4+5).`)">Calculator</button>
    </div>
  </div>
  <p><textarea id="q" placeholder="Ask me something..."></textarea></p>
  <p class="row">
    <button onclick="send()">Run</button>
    <a href="/docs" target="_blank">Open API docs</a>
    <a href="/healthz" target="_blank">Health check</a>
  </p>
  <h3>Result</h3>
  <pre id="out">—</pre>

<script>
function setQ(text){ document.getElementById('q').value = text; }
async function send(){
  const q = document.getElementById('q').value.trim();
  if (!q){ alert('Enter a query'); return; }
  const out = document.getElementById('out');
  out.textContent = 'Running...';
  try{
    const res = await fetch('/chat', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({query: q})
    });
    const data = await res.json();
    out.textContent = JSON.stringify(data, null, 2);
  }catch(err){
    out.textContent = 'Error: ' + err;
  }
}
</script>
</body>
</html>"""

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    result = run_agent(req.query)
    return result

@app.get("/healthz")
def healthz():
    return {"ok": True}
