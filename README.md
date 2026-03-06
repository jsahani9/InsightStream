InsightStream

InsightStream is a multi-agent AI system that generates personalized daily insights from AI, FinTech, and technology news.
It automatically ingests articles, removes duplicates, ranks them according to user preferences, summarizes key insights, verifies accuracy, and delivers a curated digest via email.

The system demonstrates agentic AI workflows, multi-model orchestration, and semantic retrieval pipelines using modern AI tooling.

Project Goals

The goal of InsightStream is to demonstrate how multi-agent AI architectures can transform large streams of information into personalized, high-quality insights.

The system replicates the workflow of a tech newsletter editorial team but automates it using AI agents.

Key Features
Multi-Agent Workflow

InsightStream uses multiple specialized agents that collaborate to process news.

Agents handle:

preference extraction

planning

classification

ranking

summarization

verification

Personalized News Digests

Users specify their interests in natural language.

Example:

AI research updates only
Skip startup valuations
Include fintech infrastructure

The system filters and ranks news accordingly.

Semantic Deduplication

Multiple sources often publish the same story.

InsightStream uses embedding similarity to:

remove duplicates

detect similar articles

calculate novelty scores

AI-Generated Insights

Articles are summarized into:

concise bullet summaries

key technical insights

"Why it matters" explanations

Verification Agent

A verification agent checks summaries against source articles to ensure:

factual accuracy

no hallucinated information

proper citation links

Email Delivery

The final curated digest is sent via email.

Each email includes:

structured sections

summarized insights

links to original articles

unsubscribe option

Architecture

InsightStream uses a multi-agent orchestration architecture.

Pipeline overview:

User Preferences
      ↓
Planner Agent
      ↓
Fetch Articles
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
AI Models Used
Task	Model
Preference Extraction	Claude Sonnet
Planning	Claude Sonnet
Article Classification	Llama 3.3 70B
Ranking	Llama 3.3 70B
Summarization	Claude Sonnet
Verification	Claude Sonnet
Semantic Deduplication	Amazon Titan Embeddings

Reasoning-heavy tasks use Claude while high-volume classification and ranking use Llama.

Technology Stack

Core technologies used in this project:

AI Frameworks

LangGraph (agent workflow orchestration)

LlamaIndex (document indexing and retrieval)

Models

AWS Bedrock

Claude Sonnet

Llama 3.3 70B

Amazon Titan Embeddings

Backend

FastAPI

PostgreSQL

Infrastructure

Docker

AWS

Role of LangGraph

LangGraph orchestrates the multi-agent workflow.

Each step of the pipeline is implemented as a graph node.

This enables:

stateful workflows

modular agent design

dynamic routing

easier debugging

Role of LlamaIndex

LlamaIndex handles the document processing pipeline.

It is used to:

convert articles into structured documents

build semantic indexes

retrieve relevant content

assist ranking logic

Role of PostgreSQL

PostgreSQL stores system data including:

user profiles

preferences

article metadata

sent history

unsubscribe status

This ensures users do not receive duplicate stories.

Project Structure
insightstream/
│
├── agents/
│   ├── preference_agent.py
│   ├── planner_agent.py
│   ├── classifier_agent.py
│   ├── ranking_agent.py
│   ├── summarizer_agent.py
│   ├── verifier_agent.py
│
├── graph/
│   ├── langgraph_pipeline.py
│
├── services/
│   ├── rss_fetcher.py
│   ├── email_sender.py
│   ├── bedrock_client.py
│
├── index/
│   ├── llamaindex_retriever.py
│
├── db/
│   ├── models.py
│   ├── queries.py
│
├── api/
│   ├── main.py
│
├── docker/
│
└── README.md
How It Works
1. User Onboarding

Users provide preferences in natural language.

The Preference Agent converts them into structured JSON and stores them in PostgreSQL.

2. Planning

The Planner Agent decides:

which news sources to fetch

how many articles to process

deduplication thresholds

3. News Ingestion

Articles are fetched from RSS feeds and converted into documents.

4. Classification

The Classifier Agent labels articles into categories such as:

AI

FinTech

Tech

5. Deduplication and Novelty

Embedding similarity detects duplicate stories and assigns novelty scores.

6. Ranking

Articles are ranked based on:

user preferences

novelty

relevance

recency

7. Summarization

The Summarizer Agent produces concise technical summaries.

8. Verification

The Verifier Agent checks summaries for accuracy.

9. Digest Delivery

A final curated digest is generated and emailed to the user.

Example Output

Example digest:

Top AI Insights Today

1. New Open-Source Model Outperforms GPT-4 Benchmarks
• Researchers released a model achieving higher reasoning scores.
• Why it matters: Could accelerate open AI research competition.

2. Stripe Launches AI-Powered Fraud Detection
• Stripe introduced new machine learning infrastructure.
• Why it matters: May reduce fraud costs for fintech platforms.
