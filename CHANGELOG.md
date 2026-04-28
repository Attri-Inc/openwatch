# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] — 2026-04-28

### Added
- FastAPI REST surface with 23 read-only endpoints across 7 routers
  (dashboard, sessions, users, projects, messages, compliance, agents).
- MCP server (`src/mcp_server.py`) exposing 14 tools over stdio or SSE,
  including a `run_query` SELECT-only escape hatch.
- SQLite warehouse with three logical groups: `cowork__*` (Claude Code
  ingestion), `compliance__*` (Anthropic Compliance API), `agent__*`
  (agent run history).
- Dockerfile + docker-compose for local development.
- `scripts/seed.py` for bootstrapping a fresh dev database with sample
  rows; `scripts/schema.sql` ships the canonical table definitions.
- `pyproject.toml` packaging.

[Unreleased]: https://github.com/Attri-Inc/openwatch/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Attri-Inc/openwatch/releases/tag/v0.1.0
