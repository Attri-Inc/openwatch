# OpenWatch

**The agent observability layer where every Claude session is auditable.**

Open-source, local-first observability and governance for AI agents.
SQLite-backed warehouse. REST API + MCP server. Read-only by design.

[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/MCP-14%20tools-purple)](https://modelcontextprotocol.io)

---

## Why OpenWatch?

Anthropic's Admin Console shows you spend per API key. SIEMs ingest logs but
have no schema for tool calls, sub-agents, or audit events. Traditional APM
products were never built for agentic workloads. OpenWatch fills the gap: a
purpose-built warehouse for what your AI agents actually do, queryable by
both humans and agents.

| | **OpenWatch** | **Anthropic Console** | **Datadog** | **Splunk** |
|---|---|---|---|---|
| **Built for** | AI agents | Single Anthropic account | Infra/services | Enterprise logs |
| **Cost attribution** | per user · project · tool · session | per API key | per host | per event |
| **Tool-call fidelity** | full input/output capture | ✗ | ✗ | ✗ |
| **Sub-agent tracking** | first-class | ✗ | ✗ | ✗ |
| **Session reconstruction** | byte-offset back to source artefact | summary only | trace only | log search |
| **MCP native** | ✓ (14 tools) | ✗ | ✗ | ✗ |
| **Self-hosted** | ✓ SQLite, zero deps | ✗ SaaS only | ✗ SaaS only | mixed |
| **Read-only by design** | ✓ | ✓ | mixed | mixed |
| **License** | Apache 2.0 | Proprietary | Proprietary | Proprietary |

---

## Quick Start

```bash
git clone https://github.com/Attri-Inc/openwatch.git
cd openwatch
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
python scripts/seed.py            # bootstrap a fresh dev DB with sample rows
python -m uvicorn src.main:app --reload
```

REST API: `http://localhost:8788` · Interactive docs: `/docs`

### Run with Docker

```bash
docker compose up --build
```

Data persists in the named volume `openwatch-data`.

### Connect from Claude Desktop / Code

```bash
python run_mcp.py                 # stdio transport (default)
```

For Claude Code:
```bash
claude mcp add openwatch -s user -- python /absolute/path/to/openwatch/run_mcp.py
```

See [docs/claude-connector.md](docs/claude-connector.md) for the full setup.

---

## Architecture

OpenWatch is two processes over one warehouse:

```
                ┌────────────────────────────────────────┐
                │           SQLite warehouse             │
                │  cowork__*  compliance__*  agent__*    │
                └───────────────┬────────────────────────┘
                                │ read-only
                ┌───────────────┴────────────────┐
                ▼                                ▼
       FastAPI REST (8788)              MCP server (8789)
       23 endpoints, 7 routers           14 tools, stdio + SSE
                │                                │
                ▼                                ▼
         dashboards, UIs                  Claude Desktop, Code,
         BI tools                         agent frameworks
```

Three logical data planes:

| Group | Source | Captures |
|---|---|---|
| `cowork__*` | [cowork-intelligence-package](https://github.com/Attri-Inc/cowork-intelligence-package) agent on each developer machine | Claude Code prompts, completions, tool calls, file reads, audit events |
| `compliance__*` | Anthropic Compliance API sync job | Claude.com chat activity, file uploads, project edits, login events |
| `agent__*` | Governance agents writing run records | Run history, stage outputs, evidentiary artefacts |

---

## REST API

All endpoints are `GET` (read-only) under `/api/v1`. Highlights:

| Router | Routes |
|---|---|
| `dashboard` | `/summary`, `/cost-timeseries`, `/tool-usage`, `/activity-timeline` |
| `sessions` | list, detail, `/messages`, `/tools`, `/audit-trail`, `/summary` |
| `users` | per-user activity ranked by cost |
| `projects` | per-project sessions and stats |
| `messages` | full-text search |
| `compliance` | Claude.com activity log + chat retrieval |
| `agents` | run history with stage and output detail |

Full schema at `/docs` (auto-generated OpenAPI).

---

## MCP Tools

14 tools mirror the REST surface, plus a SQL escape hatch:

`get_usage_summary` · `get_cost_breakdown` · `get_tool_usage_stats` ·
`get_activity_timeline` · `list_sessions` · `get_session_detail` ·
`get_session_summary` · `get_user_activity` · `get_projects` ·
`search_messages` · `search_audit_events` · `get_compliance_activities` ·
`get_agent_runs` · **`run_query`** *(SELECT-only)*

---

## Project Status

OpenWatch is **alpha** (v0.1). The schema and APIs may change before
v1.0. See [VISION.md](VISION.md) for the roadmap.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Bug reports, PRs, and design
discussions welcome.

## Security

See [SECURITY.md](SECURITY.md). Report vulnerabilities privately to
**security@attri.ai**.

## License

Apache 2.0 — see [LICENSE](LICENSE).
