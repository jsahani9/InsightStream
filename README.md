# InsightStream

A multi-agent AI system that generates personalized daily insights from AI, FinTech, and technology news.

## Overview

InsightStream ingests news articles, removes duplicates, ranks them by user preferences, summarizes key insights, verifies accuracy, and delivers a curated digest via email.

## Agent Pipeline

```
User Preferences
→ Preference Extraction Agent
→ Planner Agent
→ Fetch Articles
→ Classifier Agent
→ Semantic Deduplication
→ Ranking Agent
→ Summarization Agent
→ Verification Agent
→ Digest Composition
→ Email Delivery
```

## Agentic Tools

| Tool                     | Used By                                      |
|--------------------------|----------------------------------------------|
| Web Search Tool          | Planner Agent                                |
| Database Query Tool      | Planner, Ranking, Deduplication, Delivery    |
| Summarization Retry Tool | Verification Agent (retry loop)              |

## Tech Stack

| Layer         | Technology                                                        |
|---------------|-------------------------------------------------------------------|
| Orchestration | LangGraph                                                         |
| Retrieval     | LlamaIndex                                                        |
| Models        | AWS Bedrock (Claude Sonnet 4.5, Llama 3.3 70B), OpenAI (GPT-5.1, GPT-5.2, Embeddings) |
| Backend       | FastAPI                                                           |
| Frontend      | Streamlit                                                         |
| Database      | PostgreSQL                                                        |
| Deployment    | Docker, AWS ECS                                                   |

## Project Structure

```
InsightStream/
├── agents/          # LangGraph agent definitions
├── tools/           # Agent tools (web search, DB query, retry)
├── graph/           # LangGraph pipeline and node wiring
├── services/        # Article fetching, deduplication, email delivery
├── db/              # SQLAlchemy models and session management
├── api/             # FastAPI app and route handlers
├── ui/              # Streamlit frontend
├── core/            # Config, logging, shared settings
├── prompts/         # Prompt templates per agent
├── utils/           # Shared utility functions
├── tests/           # Test suites
└── docker/          # Dockerfiles per service
```

## Setup

1. Copy `.env.example` to `.env` and fill in credentials.
2. Run `docker-compose up` to start all services.
3. Access the UI at `http://localhost:8501`.
4. The API runs at `http://localhost:8000`.

## Environment Variables

See `.env.example` for all required configuration.
