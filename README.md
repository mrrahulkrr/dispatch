# Dispatch — AI-Powered Intelligence Digest Platform

🌟 **Live Demo:** [https://dispatch-nmlntvdybwrptg7effnocc.streamlit.app/](https://dispatch-nmlntvdybwrptg7effnocc.streamlit.app/)

⚙️ **Live Backend API (Swagger):** [https://dispatch-backend-7nuz.onrender.com/docs](https://dispatch-backend-7nuz.onrender.com/docs)

Dispatch is an **agentic AI system** that automatically monitors real-world government, research, and financial data sources — then reads, filters, summarizes, and explains the documents that matter to you.

You give it a topic (like "artificial intelligence regulation" or "AAPL"), and it deploys an AI agent that:

1. **Pulls documents** from live public APIs (Congress bills, Federal Register, SEC filings, arXiv papers)
2. **Classifies** which documents are actually relevant to your topic using embeddings + LLM
3. **Summarizes** each relevant document in a clean, readable format
4. **Writes an impact note** explaining why each document matters to you specifically
5. **Saves the digest** to a Postgres database for future reference

Think of it as a **personal intelligence briefing service** — like a research analyst that works 24/7, reading hundreds of government and research documents so you don't have to.

---

## What Problem Does This Solve?

Every day, thousands of government documents, research papers, and financial filings are published. No human can read them all. Dispatch solves this by:

- **Eliminating information overload** — it reads everything and surfaces only what matters to your specific topic
- **Saving hours of manual research** — instead of searching 5+ government websites, you get one clean digest
- **Providing context, not just links** — every document comes with a plain-English summary and a "why this matters" impact note

---

## Project Structure

```
dispatch/
├── backend/                  # FastAPI server + AI pipeline
│   ├── api/
│   │   └── main.py           # REST API endpoints
│   ├── graph/
│   │   ├── state.py          # Pipeline state definition
│   │   ├── graph.py          # LangGraph pipeline builder
│   │   └── nodes.py          # The 5 pipeline steps (ingest → classify → summarize → impact → deliver)
│   ├── llm/
│   │   └── llm_client.py     # Multi-provider LLM client (Gemini, Groq, OpenRouter)
│   ├── db/
│   │   ├── models.py         # Postgres table schema (Digest model)
│   │   └── session.py        # Database connection setup
│   ├── sections/             # Agent configurations
│   │   ├── base.py           # SectionConfig dataclass
│   │   ├── policy_radar/     # Monitors bills, regulations, federal register
│   │   ├── research_radar/   # Monitors arXiv papers
│   │   ├── markets_radar/    # Monitors SEC EDGAR filings
│   │   └── statements_radar/ # (Placeholder — not yet built)
│   ├── evals/                # Classification quality testing
│   │   ├── run_evals.py      # Precision/Recall/F1 scorer
│   │   ├── golden_dataset*.json  # Test datasets
│   │   └── eval_results_*.json   # Saved evaluation results
│   ├── requirements.txt
│   └── Dockerfile            # (Placeholder)
│
├── mcp_server/               # MCP tool server (data source connectors)
│   ├── server.py             # FastMCP server that registers all tools
│   ├── tools/
│   │   ├── utils.py          # Shared HTTP client and boilerplate
│   │   ├── congress.py       # US Congress API
│   │   ├── uk_parliament.py  # UK Parliament API
│   │   ├── eu_journal.py     # EU Official Journal (SPARQL)
│   │   ├── india_markets.py  # India Markets API
│   │   └── canada_parliament.py # Canada Parliament API
│   └── requirements.txt
│
├── frontend/                 # Streamlit web UI
│   ├── app.py                # Main entrypoint and router
│   ├── api_client.py         # Backend communication
│   ├── views.py              # Page rendering logic
│   └── components.py         # Reusable UI elements
│
├── tests/                    # Unit + integration tests
│   ├── test_nodes.py         # Tests for each pipeline step
│   ├── test_mcp_tools.py     # Tests for MCP tool connectors
│   └── test_graph_integration.py  # End-to-end pipeline test
│
└── .env.local                # Your API keys (ignored in git)
```

---

## Quick Start (Docker)

The absolute fastest way to get Dispatch running is using Docker. It automatically spins up the Postgres Database, the FastAPI Backend, the MCP Tool Server, and the Streamlit Frontend.

### Prerequisites

- **Docker** and **Docker Compose**
- API keys for at least one LLM provider (Gemini, Groq, or OpenRouter)

### 1. Set Up Environment Variables

Copy the example environment file:
```bash
cp .env.example .env.local
```

Open `.env.local` and add your LLM API keys. You don't need to change `DATABASE_URL` (Docker handles it).

### 2. Start the Platform

Run this command from the project root:

```bash
docker-compose up --build
```

### 3. Open the Dashboard

Once the containers are running, open your browser:
- **Frontend UI**: [http://localhost:8501](http://localhost:8501)
- **Backend API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Manual Installation (Without Docker)

If you prefer to run it locally without Docker:

1. Ensure **PostgreSQL** is running on your machine.
2. Add your keys to `.env.local`.
3. Install dependencies:
   ```bash
   pip install -r backend/requirements.txt
   pip install -r mcp_server/requirements.txt
   pip install streamlit
   ```
4. Start the backend: `python -m uvicorn backend.api.main:app --reload`
5. Start the frontend: `python -m streamlit run frontend/app.py`

### 5. Run Tests

```bash
python -m pytest tests/ -v
```

### 6. Run Evaluations

```bash
python -m backend.evals.run_evals --section policy-radar
python -m backend.evals.run_evals --section research-radar
python -m backend.evals.run_evals --section markets-radar
```

---

## Available Agents

| Agent | What It Monitors | Data Sources |
|-------|-----------------|--------------|
| **Policy Radar** | U.S. federal bills, regulations, federal register notices | Congress.gov, Regulations.gov, Federal Register |
| **Research Radar** | Scientific research papers | arXiv |
| **Markets Radar** | SEC financial filings (8-K, 10-K) | SEC EDGAR |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/sections` | List all available agents |
| `POST` | `/sections/{slug}/runs` | Deploy an agent for a topic |
| `GET` | `/sections/{slug}/runs/{run_id}` | Get a specific run's state |
| `GET` | `/sections/{slug}/digests` | Get saved historical digests |
| `GET` | `/evals/{slug}` | Get evaluation metrics for an agent |

---

## LLM Providers

Dispatch uses a **fallback chain** for reliability:

1. **Gemini** (primary) — `gemini-3.1-flash-lite`
2. **Groq** (fast fallback) — `llama-3.1-8b-instant`
3. **OpenRouter** (last resort) — `meta-llama/llama-3.1-8b-instruct:free`

If one provider fails or rate-limits, it automatically tries the next one. A global semaphore limits concurrent LLM calls to prevent rate limiting.

---

## License

This project is for personal / educational use.
