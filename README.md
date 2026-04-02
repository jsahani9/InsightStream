# InsightStream

> Your personalized AI-powered news digest, delivered every morning at 9 AM.

InsightStream is a production-grade multi-agent AI system that monitors 41 news sources across AI, FinTech, Tech, Crypto, Markets, and World — filters the noise, summarizes what matters, and delivers a curated digest straight to your inbox every day.

**Live App:** http://insightstream-alb-2074513672.us-east-1.elb.amazonaws.com

---

## The Problem

There are thousands of news articles published every day. Reading through all of them to find what's actually relevant to you is impossible. Most news aggregators just show you everything — no personalization, no summarization, no curation.

InsightStream solves this by using a pipeline of specialized AI agents that understand your interests, find the most relevant stories, verify the summaries for accuracy, and deliver exactly what you care about — nothing else.

---

## How It Works

You tell InsightStream what you care about in plain English:

> *"I'm a software engineer interested in large language models, AI startups, and FinTech. I follow venture capital deals and generative AI research. Please avoid crypto and celebrity news."*

InsightStream extracts your categories, fetches articles from relevant sources, ranks them by relevance to your profile, summarizes each into 3 sharp bullet points, verifies them for accuracy, and emails you a clean digest every morning at 9 AM.

---

## Agent Pipeline

```
User Preferences (natural language)
        │
        ▼
┌─────────────────────────┐
│  Preference Extraction  │  Claude Sonnet 4.5 (Bedrock)
│  Agent                  │  Extracts categories from free text
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Planner Agent          │  GPT-5.1 (OpenAI)
│                         │  Selects which sources to fetch
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Article Fetcher        │  41 RSS feeds
│                         │  AI, Tech, FinTech, Crypto, Markets, World
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Classifier Agent       │  Llama 3.3 70B (Bedrock)
│                         │  Tags each article with a category
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Deduplication          │  Semantic similarity (threshold 0.75)
│                         │  Removes near-duplicate stories
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Ranking Agent          │  Llama 3.3 70B (Bedrock)
│                         │  Scores articles by user relevance
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Summarization Agent    │  Claude Sonnet 4.5 (Bedrock)
│                         │  3 bullet points per article, 1 sentence each
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Verification Agent     │  GPT-5.2 (OpenAI)
│                         │  Checks accuracy + category diversity
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Digest Composition     │  Formats the final digest
│  + Email Delivery       │  Sends via Gmail SMTP
└─────────────────────────┘
```

**Retry loops:**
- If too few articles are fetched → loops back to fetch more
- If summaries fail verification → loops back to re-summarize

---

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | LangGraph (stateful multi-agent graph with conditional edges) |
| AI Models | AWS Bedrock — Claude Sonnet 4.5, Llama 3.3 70B |
| AI Models | OpenAI — GPT-5.1 (planner), GPT-5.2 (verifier), text-embedding-3-large |
| Frontend | Streamlit (dark futuristic UI) |
| Database | Neon PostgreSQL — async via SQLAlchemy + asyncpg |
| News Sources | 41 RSS feeds via feedparser + Serper web search |
| Email | aiosmtplib — Gmail SMTP |
| Scheduler | APScheduler — 9 AM ET daily, all users in parallel |
| Deployment | Docker + AWS ECR + AWS ECS Fargate + Application Load Balancer |

---

## Features

- **Natural language preferences** — just describe what you want, no dropdowns or checkboxes
- **Dynamic categories** — the system extracts your interests and uses them throughout the pipeline
- **41 news sources** — covering AI, Tech, FinTech, Crypto, Markets, and World news
- **Semantic deduplication** — no more seeing the same story from 5 different outlets
- **Category diversity enforcement** — your digest always covers multiple topics, never just one
- **On-demand digests** — don't want to wait until 9 AM? Hit "Get News Now" anytime
- **Article history** — see everything that's been sent to you
- **Subscribe/Unsubscribe** — full control over your daily digest

---

## Project Structure

```
InsightStream/
├── agents/                        # 6 specialized AI agents
│   ├── preference_extraction_agent.py
│   ├── planner_agent.py
│   ├── classifier_agent.py
│   ├── ranking_agent.py
│   ├── summarization_agent.py
│   └── verification_agent.py
├── graph/                         # LangGraph pipeline
│   ├── pipeline.py                # Graph definition + conditional edges
│   ├── nodes.py                   # All node implementations
│   └── state.py                   # Shared pipeline state
├── services/                      # Core business logic
│   ├── article_fetcher.py         # RSS feed fetching (41 sources)
│   ├── deduplication.py           # Semantic deduplication
│   ├── digest_composition.py      # Digest formatting
│   └── email_delivery.py          # SMTP email sending
├── tools/                         # LangGraph agent tools
│   ├── web_search_tool.py         # Serper web search
│   ├── database_query_tool.py     # User preferences + history
│   └── summarization_retry_tool.py
├── db/                            # Database layer
│   ├── models.py                  # SQLAlchemy models
│   └── session.py                 # Async session management
├── core/                          # Shared config
│   ├── config.py                  # Pydantic settings from env
│   ├── constants.py               # RSS sources, defaults
│   └── bedrock_client.py          # AWS Bedrock client
├── alembic/                       # Database migrations
├── tests/                         # Test suites
├── app.py                         # Streamlit UI
├── scheduler.py                   # Daily digest scheduler
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Running Locally

**1. Clone the repo**
```bash
git clone https://github.com/jsahani9/InsightStream.git
cd InsightStream
```

**2. Create virtual environment**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**3. Set up environment variables**
```bash
cp .env.example .env
# Fill in your API keys in .env
```

**4. Run with Docker (recommended)**
```bash
docker-compose up --build
```

Access the app at `http://localhost:8501`

Or run services individually:
```bash
# Streamlit UI
streamlit run app.py

# Scheduler (keep running in background)
python scheduler.py
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Description |
|---|---|
| `DATABASE_URL` | Neon PostgreSQL async connection string |
| `AWS_ACCESS_KEY_ID` | AWS IAM credentials |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM credentials |
| `AWS_REGION` | AWS region (us-east-1) |
| `BEDROCK_CLAUDE_MODEL_ID` | Claude model ID on Bedrock |
| `BEDROCK_LLAMA_MODEL_ID` | Llama model ID on Bedrock |
| `OPENAI_API_KEY` | OpenAI API key |
| `OPENAI_PLANNER_MODEL` | Model for planner agent |
| `OPENAI_VERIFIER_MODEL` | Model for verifier agent |
| `OPENAI_EMBEDDING_MODEL` | Embedding model |
| `SERPER_API_KEY` | Serper.dev API key for web search |
| `SMTP_USERNAME` | Gmail address |
| `SMTP_PASSWORD` | Gmail app password |
| `EMAIL_FROM` | Sender email address |

---

## Deployment

InsightStream runs on **AWS ECS Fargate** — fully serverless, no EC2 instances to manage.

**Architecture:**
- Docker images stored in **AWS ECR**
- Two containers in one ECS Task: `streamlit` + `scheduler`
- **Application Load Balancer** routes public traffic to the Streamlit container
- Scheduler container runs 24/7 and fires at 9 AM ET daily

**To deploy updates:**
```bash
# Build for linux/amd64 (required for ECS Fargate)
docker buildx build --platform linux/amd64 -t insightstream-streamlit:amd64 --load .
docker tag insightstream-streamlit:amd64 911006138108.dkr.ecr.us-east-1.amazonaws.com/insightstream:streamlit
docker push 911006138108.dkr.ecr.us-east-1.amazonaws.com/insightstream:streamlit

docker buildx build --platform linux/amd64 -t insightstream-scheduler:amd64 --load .
docker tag insightstream-scheduler:amd64 911006138108.dkr.ecr.us-east-1.amazonaws.com/insightstream:scheduler
docker push 911006138108.dkr.ecr.us-east-1.amazonaws.com/insightstream:scheduler
```

Then go to ECS → Service → Update → Force new deployment.

---

## Authors

- [Jasveen Singh Sahani](https://github.com/jsahani9)
- [Aakash Sangwan](https://github.com/Aakashdeepsangwan)
