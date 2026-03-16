from tools.web_search_tool import web_search

print("=" * 50)
print("Query: AI news today")

try:
    results = web_search("AI news today", max_results=5)
    print(f"Success. Results found: {len(results)}")

    for i, result in enumerate(results, start=1):
        print("-" * 50)
        print(f"{i}. {result['title']}")
        print(f"URL: {result['url']}")
        print(f"Snippet: {result['snippet']}")
        print(f"Published: {result['published_at']}")
except Exception as e:
    print(f"FAILED: {e}")

print("=" * 50)