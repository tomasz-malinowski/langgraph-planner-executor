from __future__ import annotations
from graph import run_agent

tests = [
    {
        "query": "What were total sales in Q1?",
        "expect_any": ["Total sales:", "total |"],
    },
    {
        "query": "What's the weather in Warsaw and compute 12*(7+1).",
        "expect_any": ["Weather:", "Calculation:", "Warsaw"],
    },
    {
        "query": "Sum revenue by quarter using SQL and then tell me the result.",
        "expect_any": ["quarter | total", "Conclusion:"],
    },
]

def run_tests():
    passed = 0
    for i, t in enumerate(tests, 1):
        print(f"\n=== Test {i}: {t['query']} ===")
        out = run_agent(t["query"])
        print(out["final_answer"][:500])
        if any(s in out["final_answer"] for s in t["expect_any"]):
            print("✅ PASS")
            passed += 1
        else:
            print("❌ FAIL")
    print(f"\n{passed}/{len(tests)} passed.")

if __name__ == "__main__":
    run_tests()
