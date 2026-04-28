# Contributing to OpenWatch

Thanks for your interest in contributing.

## Development setup

```bash
git clone https://github.com/Attri-Inc/openwatch.git
cd openwatch
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
python scripts/seed.py        # creates ./data/openwatch.db with sample rows
python -m uvicorn src.main:app --reload
```

REST API at `http://localhost:8788`. Interactive docs at `/docs`.

To run the MCP server:

```bash
python run_mcp.py             # stdio (default — for Claude Desktop / Code)
MCP_TRANSPORT=sse python run_mcp.py
```

## Running tests

```bash
pytest
```

## Linting

```bash
ruff check .
ruff format .
```

## Pull request guidelines

- One logical change per PR. Refactors and feature work go in separate PRs.
- Add or update tests for behavioural changes.
- Update `CHANGELOG.md` under `[Unreleased]`.
- Keep public API additions documented in `docs/`.

## Reporting bugs

Open an issue with:
- OpenWatch version (`pip show openwatch`)
- Python version
- Reproduction steps
- Expected vs actual behaviour

## Reporting security issues

See [SECURITY.md](SECURITY.md). Do not open a public issue for vulnerabilities.

## Code of conduct

Be excellent to each other.
