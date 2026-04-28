# OpenWatch Vision

## The problem

Enterprises adopting Claude (and other agentic LLMs) face an observability
gap that traditional APM and log-management products were never built for.
Anthropic's Admin Console exposes spend per key but cannot answer questions
like *"which engineer wrote the most code with Claude this week"*, *"did
any prompt contain customer PII"*, or *"reproduce the exact session that
triggered yesterday's $80 cost spike"*. SIEMs ingest logs but lack the
agent-aware schema to make sense of tool calls, sub-agents, MCP servers,
and audit events.

OpenWatch fills that gap.

## What OpenWatch is

A **read-only warehouse + lens** over everything an organisation's AI
agents do, exposed through both a REST API and a Model Context Protocol
(MCP) server so it can be queried by humans *and* by agents.

Three logical data planes:

- **`cowork__*`** — Claude Code session activity ingested from each
  developer's machine: prompts, completions, tool calls, file reads,
  audit events. Closes the gap that Anthropic's native Compliance API
  doesn't cover.
- **`compliance__*`** — Anthropic's official Compliance API feed:
  Claude.com chat activity, file uploads, project edits, login events.
- **`agent__*`** — execution log for governance agents (PII redaction,
  cost anomaly, audit continuity, etc.) that act on the warehouse.

## Principles

1. **Read-only by design.** OpenWatch never mutates the underlying
   activity. It is a system of record, not a system of action.
2. **Agent-callable from day one.** Every REST endpoint has an MCP twin.
   Agents can introspect what's happening with the same fidelity humans
   get from the dashboard.
3. **Local-first.** Ships as SQLite + a single Python process. Self-hosted
   on customer infrastructure. No data leaves the operator's network.
4. **Composable.** OpenWatch is the data layer. Bring your own ingestion
   pipeline, your own dashboards, your own governance agents — or use the
   ones that ship with the project.
5. **Auditable.** Every claim in the warehouse traces back to a raw
   source artefact (file path + byte offset for `cowork__*`, Anthropic
   activity ID for `compliance__*`, run UUID for `agent__*`).

## What OpenWatch is *not*

- Not an APM. It does not trace HTTP requests or measure infrastructure
  health.
- Not a SIEM. It does not ingest arbitrary log streams.
- Not an LLM proxy. It records what agents do; it does not stand between
  agents and their model providers.
- Not a multi-tenant SaaS. Each deployment is single-tenant by default.

## Roadmap

### v0.1 (current)
REST + MCP over SQLite, manual ingestion via the cowork-intelligence-package
agent and Anthropic Compliance API sync jobs.

### v0.2
- Postgres backend option for multi-writer ingestion.
- LiteLLM-compatible proxy integration so agent runs auto-emit `agent__*`
  rows without bespoke wiring.
- First-party governance agents: PII redaction, prompt policy checker,
  cost anomaly, audit continuity.

### v0.3
- Multi-tenant deployments.
- Authentication (API keys + OIDC).
- Webhook outbound for high-severity detections.

### v1.0
- Stable schema commitment.
- Pluggable ingestion adapters (Cursor, Cline, Aider, generic OpenAI-style
  proxy).
- Production-grade horizontal scale-out.