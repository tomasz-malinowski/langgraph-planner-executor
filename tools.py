from __future__ import annotations
import sqlite3
import re
from typing import Any, Dict


def init_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE sales(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quarter TEXT,
            amount REAL,
            product TEXT
        );
    """)
    sample = [
        ("Q1", 12000.0, "widget"),
        ("Q1", 8000.0,  "gadget"),
        ("Q2", 15000.0, "widget"),
        ("Q2", 7000.0,  "gadget"),
        ("Q3", 18000.0, "widget"),
        ("Q3", 6000.0,  "gadget"),
        ("Q4", 22000.0, "widget"),
        ("Q4", 9000.0,  "gadget"),
    ]
    cur.executemany("INSERT INTO sales(quarter, amount, product) VALUES (?, ?, ?)", sample)
    conn.commit()
    return conn

SQL_CONN = init_db()

def sql_query(query: str) -> str:
    if not re.match(r"(?i)^\s*select\s+", query):
        return "SQL tool allows only SELECT statements."
    try:
        cur = SQL_CONN.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
        if not rows:
            return "No rows."
        # Render simple table
        lines = [" | ".join(cols)]
        for r in rows:
            lines.append(" | ".join(str(x) for x in r))
        return "\n".join(lines)
    except Exception as e:
        return f"SQL error: {e}"

def calculator(expr: str) -> str:
    import re
    expr = expr.strip()
    if expr.endswith("."):
        if not re.search(r"\d\.\d+$", expr):
            expr = expr[:-1]

    if not re.match(r"^[0-9\+\-\*\/\(\)\.\s]+$", expr):
        return "Invalid expression. Allowed: digits and + - * / ( ) ."
    try:
        val = eval(expr, {"__builtins__": {}}, {})
        return str(val)
    except Exception as e:
        return f"Calc error: {e}"


WEATHER = {
    "warsaw": "Warsaw: 22°C, clear, light breeze",
    "London": "London: 16°C, cloudy, chance of rain",
    "Berlin": "Berlin: 19°C, partly cloudy, mild wind",
}

def weather_lookup(city: str) -> str:
    key = city.strip().lower()
    return WEATHER.get(key, f"No weather data for '{city}'. Try: Warsaw, London, Berlin.")


Tool = Dict[str, Any]

TOOLS: Dict[str, Tool] = {
    "sql": {
        "name": "sql",
        "description": "Query the sales SQLite DB. Only SELECT allowed. Example: SELECT SUM(amount) as total FROM sales WHERE quarter='Q1';",
        "func": sql_query,
    },
    "calculator": {
        "name": "calculator",
        "description": "Evaluate simple arithmetic like 12*(7+1). Allowed: digits and + - * / ( ) .",
        "func": calculator,
    },
    "weather": {
        "name": "weather",
        "description": "Lookup stubbed weather by city name (Warsaw, Helsinki, Innsbruck).",
        "func": weather_lookup,
    },
}
