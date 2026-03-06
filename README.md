# InsightStream

> A multi-agent AI system that generates personalized daily insights from AI, FinTech, and technology news.

InsightStream automatically ingests articles, removes duplicates, ranks them by user preferences, summarizes key insights, verifies accuracy, and delivers a curated digest via email. It demonstrates agentic AI workflows, multi-model orchestration, and semantic retrieval pipelines using modern AI tooling.

---

## Features

- **Multi-Agent Workflow** — Specialized agents collaborate across the full pipeline: preference extraction, planning, classification, ranking, summarization, and verification.
- **Personalized Digests** — Users define interests in natural language (e.g. *"AI research only, skip startup valuations"*). The system filters and ranks news accordingly.
- **Semantic Deduplication** — Embedding similarity detects duplicate stories across sources and assigns novelty scores.
- **AI-Generated Insights** — Articles are summarized into bullet points, key technical takeaways, and "why it matters" explanations.
- **Verification Agent** — Cross-checks summaries against source articles to prevent hallucinated content.
- **Email Delivery** — Curated digest delivered with structured sections, source links, and an unsubscribe option.

---

## Architecture

```
User Preferences
      ↓
Planner Agent
      ↓
Fetch Articles (RSS)
      ↓
Classifier Agent
      ↓
Semantic Deduplication
      ↓
Ranking Agent
      ↓
Summarization Agent
      ↓
Verification Agent
      ↓
Digest Composition
      ↓
Email Delivery
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

## Tech Stack

| Layer          | Technology                              |
|----------------|------------------------------------------|
| Orchestration  | LangGraph                               |
| Retrieval      | LlamaIndex                              |
| Models         | AWS Bedrock (Claude Sonnet, Llama 3.3 70B, Titan Embeddings) |
| Backend        | FastAPI                                 |
| Database       | PostgreSQL                              |
| Infrastructure | Docker, AWS                             |

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
2. **Planning** — The Planner Agent determines which sources to fetch, article volume, and deduplication thresholds.
3. **News Ingestion** — Articles are fetched from RSS feeds and converted into structured documents via LlamaIndex.
4. **Classification** — The Classifier Agent labels articles into categories: AI, FinTech, Tech.
5. **Deduplication** — Embedding similarity detects duplicate stories and calculates novelty scores.
6. **Ranking** — Articles are scored by user preferences, novelty, relevance, and recency.
7. **Summarization** — The Summarizer Agent generates concise technical summaries with "why it matters" context.
8. **Verification** — The Verifier Agent validates summaries against source articles for factual accuracy.
9. **Delivery** — A final curated digest is composed and emailed to the user.

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
