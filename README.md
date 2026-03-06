# InsightStream

> A multi-agent AI system that generates personalized daily insights from AI, FinTech, and technology news.

InsightStream automatically ingests articles, removes duplicates, ranks them by user preferences, summarizes key insights, verifies accuracy, and delivers a curated digest via email. It demonstrates agentic AI workflows, multi-model orchestration, and semantic retrieval pipelines using modern AI tooling.

---

## Features

- **Multi-Agent Workflow** — Specialized agents collaborate across the full pipeline: preference extraction, planning, classification, ranking, summarization, and verification.
- **Agentic Tool Use** — Agents dynamically call tools to observe state, make decisions, and act — rather than executing a fixed sequence of steps.
- **Personalized Digests** — Users define interests in natural language (e.g. *"AI research only, skip startup valuations"*). The system filters and ranks news accordingly.
- **Semantic Deduplication** — Embedding similarity detects duplicate stories across sources and assigns novelty scores.
- **AI-Generated Insights** — Articles are summarized into bullet points, key technical takeaways, and "why it matters" explanations.
- **Verification Agent with Retry Loop** — Cross-checks summaries against source articles. If accuracy fails, triggers re-summarization with stricter constraints.
- **Email Delivery** — Curated digest delivered with structured sections, source links, and an unsubscribe option.

---

## Architecture

InsightStream is designed as a truly agentic system — agents observe state, decide what action is needed, call the appropriate tool, inspect the result, and continue or retry. This is distinct from a fixed pipeline where steps execute in a predetermined sequence.
```
User Preferences
      ↓
Planner Agent ──────────────── [web_search_tool] [db_query_tool] [fetcher_tool]
      ↓
Fetch Articles (RSS + Dynamic Sources)
      ↓
Classifier Agent
      ↓
Semantic Deduplication ──────── [db_query_tool → get_recently_sent_articles()]
      ↓
Ranking Agent ───────────────── [db_query_tool → get_user_preferences()]
      ↓
Summarization Agent
      ↓
Verification Agent ──────────── [summarization_tool → retry if verification fails]
      ↓                                ↑
      └────────── retry loop ──────────┘
      ↓
Digest Composition
      ↓
Delivery Agent ──────────────── [email_tool] [db_query_tool → is_user_subscribed()]
```

### AI Models

| Task                    | Model                    |
|-------------------------|--------------------------|
| Preference Extraction   | Claude Sonnet            |
| Planning                | Claude Sonnet            |
| Article Classification  | Llama 3.3 70B            |
| Ranking                 | Llama 3.3 70B            |
| Summarization           | Claude Sonnet            |
| Verification            | Claude Sonnet            |
| Semantic Deduplication  | Amazon Titan Embeddings  |

Reasoning-heavy tasks use Claude; high-volume classification and ranking use Llama.

---

## Agentic Tools

InsightStream agents use a controlled set of tools to make dynamic decisions at runtime. Tools are scoped per agent — no agent has access to tools outside its responsibility.

### Web Search Tool
**Used by:** Planner Agent

| Field  | Detail |
|--------|--------|
| Input  | `query: str, max_results: int` |
| Output | `list[{title, url, snippet, published_at}]` |

Enables the Planner to detect trending topics, discover relevant sources dynamically, and decide which domains to prioritize for the day's digest — rather than relying on hardcoded RSS feeds alone.

---

### Database Query Tool
**Used by:** Planner Agent, Deduplication, Ranking Agent, Delivery Agent

Exposes safe, scoped functions — agents never execute raw SQL.

| Function | Description |
|----------|-------------|
| `get_user_preferences(user_id)` | Returns structured user interest profile |
| `get_recently_sent_articles(user_id)` | Returns article IDs sent in last N days |
| `is_user_subscribed(user_id)` | Returns subscription status before delivery |

Enables agents to query live state rather than relying on static context passed at pipeline start.

---

### Summarization Tool (Verifier Retry)
**Used by:** Verification Agent

| Field  | Detail |
|--------|--------|
| Input  | `article_text: str, failed_summary: str, constraints: list[str]` |
| Output | `revised_summary: str` |

If the Verification Agent detects inaccuracies or hallucinated content in a summary, it calls this tool to trigger re-summarization with stricter constraints — creating a real correction loop rather than a single-pass pipeline.

---

## Tech Stack

| Layer          | Technology                                                    |
|----------------|---------------------------------------------------------------|
| Orchestration  | LangGraph                                                     |
| Retrieval      | LlamaIndex                                                    |
| Models         | AWS Bedrock (Claude Sonnet, Llama 3.3 70B, Titan Embeddings) |
| Backend        | FastAPI                                                       |
| Database       | PostgreSQL                                                    |
| Infrastructure | Docker, AWS                                                   |

---

## Project Structure
```
insightstream/
│
├── agents/
│   ├── preference_agent.py
│   ├── planner_agent.py
│   ├── classifier_agent.py
│   ├── ranking_agent.py
│   ├── summarizer_agent.py
│   └── verifier_agent.py
│
├── tools/
│   ├── web_search_tool.py
│   ├── db_query_tool.py
│   └── summarization_tool.py
│
├── graph/
│   └── langgraph_pipeline.py
│
├── services/
│   ├── rss_fetcher.py
│   ├── email_sender.py
│   └── bedrock_client.py
│
├── index/
│   └── llamaindex_retriever.py
│
├── db/
│   ├── models.py
│   └── queries.py
│
├── api/
│   └── main.py
│
├── docker/
└── README.md
```

---

## How It Works

1. **User Onboarding** — Users provide preferences in natural language. The Preference Agent converts them into structured JSON and stores them in PostgreSQL.
2. **Planning** — The Planner Agent uses the web search tool to detect trending topics and the DB query tool to retrieve user preferences, dynamically deciding which sources to fetch and how to weight categories.
3. **News Ingestion** — Articles are fetched from RSS feeds and dynamically discovered sources, converted into structured documents via LlamaIndex.
4. **Classification** — The Classifier Agent labels articles into categories: AI, FinTech, Tech.
5. **Deduplication** — Embedding similarity detects duplicate stories. The DB query tool checks recently sent articles to ensure users never receive the same story twice.
6. **Ranking** — Articles are scored by live user preferences (via DB query tool), novelty, relevance, and recency.
7. **Summarization** — The Summarizer Agent generates concise technical summaries with "why it matters" context.
8. **Verification** — The Verifier Agent validates summaries against source articles. If inaccuracies are detected, it triggers the summarization tool to retry with stricter constraints.
9. **Delivery** — Subscription status is checked via DB query tool before the curated digest is composed and emailed.

---

## Example Output
```
Top AI Insights Today

1. New Open-Source Model Outperforms GPT-4 Benchmarks
   • Researchers released a model achieving higher reasoning scores.
   • Why it matters: Could accelerate open AI research competition.

2. Stripe Launches AI-Powered Fraud Detection
   • Stripe introduced new machine learning infrastructure.
   • Why it matters: May reduce fraud costs for fintech platforms.
```
