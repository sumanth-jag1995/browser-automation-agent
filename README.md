# Browser Automation AI Agent

Production-ready multi-agent browser automation system built from the PRD. It discovers user journeys, generates Playwright scripts, executes them, diagnoses failures, repairs scripts, detects visual regressions, and produces execution reports — all orchestrated with LangGraph.

## Features

- **Flow Discovery** — identifies 3–5 critical user journeys from URL + intent
- **Script Generator** — hybrid local storage: reuses cached scripts, generates only new/changed flows
- **Executor** — runs scripts in headless Chromium
- **Error Diagnosis** — classifies failures (selector, timeout, network, etc.)
- **Adaptive Repair** — auto-fixes selectors, timing, and retries (max 3)
- **Regression Monitor** — pixel-level screenshot comparison against baselines
- **Report Generator** — JSON execution reports
- **FastAPI** — `POST /run`, `GET /status/{run_id}`, `GET /report/{run_id}`
- **Docker** — full stack with Redis

## Quick Start

### Local (no Docker)

```bash
cd browser-automation-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
pytest tests/ -v
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Docker Compose

```bash
cd browser-automation-agent
docker compose up --build
```

API available at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

### Run an automation

```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "intent": "Test checkout flow"}'

curl http://localhost:8000/status/{run_id}
curl http://localhost:8000/report/{run_id}
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | — | Anthropic API key for Claude Sonnet 4.6 |
| `USE_MOCK_LLM` | `false` | Use deterministic mock responses (CI/offline) |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for run state |
| `MAX_RETRIES` | `3` | Max repair retries before human escalation |
| `MAX_REPAIR_BEFORE_REGENERATE` | `2` | Repairs per flow before full script regeneration |

Set `USE_MOCK_LLM=true` to run without an API key. Set `ANTHROPIC_API_KEY` for live LLM-powered discovery, diagnosis, and repair.

## Script Storage (Hybrid Strategy)

Scripts are stored locally under `scripts/{site}/`:

```
scripts/
  example_com/
    manifest.json    # flow hashes, sources, repair counts
    login.py
    checkout.py
```

**Hybrid rules:**
1. **Reuse** — if flow hash (`url + intent + flow`) matches stored manifest, load cached `.py`
2. **Generate** — new flow or changed hash → generate and save
3. **Repair** — on execution failure, repair and persist updated script
4. **Regenerate** — after 2 failed repairs for a flow, regenerate from scratch

## Architecture

```
START → Flow Discovery → Script Generator (hybrid cache) → Executor
  ├─ success → Regression Monitor → Report Generator → END
  └─ failure → Error Diagnosis → Adaptive Repair → Executor (retry)
       ├─ 2+ repairs failed → Regenerate Flow → Executor
       └─ retry_count >= 3 → Human Escalation → END
```

## Project Structure

```
browser-automation-agent/
├── agents/           # Seven specialized agents
├── orchestrator/     # LangGraph StateGraph
├── state/            # AgentState schema
├── prompts/          # LLM prompt templates
├── llm/              # Anthropic client + mock fallback
├── storage/          # Redis run store + local script store
├── scripts/          # Persisted Playwright scripts per site
├── screenshots/      # baseline/ and current/
├── reports/          # JSON execution reports
├── tests/            # Unit and integration tests
├── main.py           # FastAPI app
├── Dockerfile
└── docker-compose.yml
```
