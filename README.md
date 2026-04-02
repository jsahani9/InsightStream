# InsightStream

A multi-agent AI system that delivers personalized daily news digests across AI, FinTech, Tech, Crypto, Markets, and more — straight to your inbox at 9 AM every day.

Built with LangGraph, AWS Bedrock, OpenAI, and deployed on AWS ECS Fargate.

**Live:** http://insightstream-alb-2074513672.us-east-1.elb.amazonaws.com

---

## What it does

1. Extracts your interests from natural language (e.g. "I follow LLMs, FinTech, and crypto")
2. Plans which news sources to fetch based on your categories
3. Fetches articles from 41 RSS feeds across AI, Tech, FinTech, Crypto, Markets, and World
4. Classifies, deduplicates, and ranks articles by relevance to your preferences
5. Summarizes each article into 3 sharp bullet points
6. Verifies summaries for accuracy and diversity across categories
7. Composes and delivers a personalized digest to your email

---

## Pipeline

```
START
  → Preference Extraction   (Claude Sonnet 4.5 via Bedrock)
  → Planner                 (GPT-5.1 via OpenAI)
  → Fetch Articles          (41 RSS feeds via Serper)
  → Classifier              (Llama 3.3 70B via Bedrock)
  → Deduplication           (semantic similarity, threshold 0.75)
  → Ranking                 (Llama 3.3 70B via Bedrock)
  → Enrich & Filter
  → Summarization           (Claude Sonnet 4.5 via Bedrock)
  → Verification            (GPT-5.2 via OpenAI)
  → Digest Composition
  → Email Delivery
END
```

Retry loops: ranking → fetch (if too few articles), verification → summarization (if summaries fail)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | LangGraph |
| Models | AWS Bedrock (Claude Sonnet 4.5, Llama 3.3 70B), OpenAI (GPT-5.1, GPT-5.2, text-embedding-3-large) |
| Frontend | Streamlit |
| Database | Neon PostgreSQL (async via SQLAlchemy + asyncpg) |
| Email | aiosmtplib (Gmail SMTP) |
| Web Search | Serper API |
| Scheduler | APScheduler (9 AM ET daily, parallel delivery) |
| Deployment | Docker, AWS ECR, AWS ECS Fargate, ALB |

---

## Project Structure

```
InsightStream/
├── agents/               # 6 LangGraph agents
│   ├── preference_extraction_agent.py
│   ├── planner_agent.py
│   ├── classifier_agent.py
│   ├── ranking_agent.py
│   ├── summarization_agent.py
│   └── verification_agent.py
├── graph/                # LangGraph pipeline wiring
│   ├── pipeline.py
│   ├── nodes.py
│   └── state.py
├── services/             # Core services
│   ├── article_fetcher.py
│   ├── deduplication.py
│   ├── digest_composition.py
│   └── email_delivery.py
├── tools/                # Agent tools
│   ├── web_search_tool.py
│   ├── database_query_tool.py
│   └── summarization_retry_tool.py
├── db/                   # Database models and session
├── core/                 # Config and constants
├── tests/                # Test suites
├── app.py                # Streamlit UI
├── scheduler.py          # Daily digest scheduler
├── Dockerfile
└── docker-compose.yml
```

---

## Running Locally

**1. Clone and set up environment**
```bash
git clone https://github.com/jsahani9/InsightStream.git
cd InsightStream
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Configure environment variables**
```bash
cp .env.example .env
# Fill in your API keys in .env
```

**3. Run with Docker**
```bash
docker-compose up --build
```

Access the app at `http://localhost:8501`

---

## Environment Variables

See `.env.example` for all required variables. Key ones:

| Variable | Description |
|---|---|
| `DATABASE_URL` | Neon PostgreSQL connection string |
| `AWS_ACCESS_KEY_ID` | AWS credentials for Bedrock |
| `AWS_SECRET_ACCESS_KEY` | AWS credentials for Bedrock |
| `OPENAI_API_KEY` | OpenAI API key |
| `SERPER_API_KEY` | Serper web search API key |
| `SMTP_USERNAME` / `SMTP_PASSWORD` | Gmail SMTP credentials |

---

## Deployment

Deployed on AWS ECS Fargate with an Application Load Balancer.

- **Streamlit container** — serves the web UI
- **Scheduler container** — runs 24/7, fires digest pipeline at 9 AM ET for all subscribed users in parallel

To deploy updates:
```bash
# Rebuild and push AMD64 images
docker buildx build --platform linux/amd64 -t insightstream-streamlit:amd64 --load .
docker tag insightstream-streamlit:amd64 911006138108.dkr.ecr.us-east-1.amazonaws.com/insightstream:streamlit
docker push 911006138108.dkr.ecr.us-east-1.amazonaws.com/insightstream:streamlit
# Then force a new deployment in ECS
```

---

## Authors

- [Jasveen Singh Sahani](https://github.com/jsahani9)
- [Aakash Sangwan](https://github.com/Aakashdeepsangwan)
