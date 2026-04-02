import json
from agents.planner_agent import run

print("=" * 50)
print("Running planner agent...")

state = {
    "structured_preferences": {
        "topics": ["AI", "FinTech", "Tech"],
        "sources": ["TechCrunch", "VentureBeat"],
    },
}

try:
    result = run(state)

    print(f"\nWeb articles found: {len(result['raw_articles'])}")
    print("-" * 50)
    for a in result["raw_articles"]:
        print(f"  • {a['title']}")

    print(f"\nFetch plan:")
    print(json.dumps(result["fetch_plan"], indent=2))

except Exception as e:
    print(f"FAILED: {e}")

print("=" * 50)
