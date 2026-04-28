# Security Policy

## Supported versions

OpenWatch is in early development. Only the latest minor release receives
security fixes.

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✓         |

## Reporting a vulnerability

Please report security vulnerabilities privately Attri.

Include:
- A description of the issue
- Steps to reproduce
- Affected version(s)
- Impact assessment if you have one

Please do not file public GitHub issues for security vulnerabilities.

## Disclosure

We follow a coordinated disclosure model. Once a fix is available we will:
1. Release a patched version.
2. Publish a GitHub Security Advisory crediting the reporter (unless they
   prefer to remain anonymous).
3. Update the changelog with the CVE identifier when one has been assigned.

## Hardening notes for operators

- The default `CORSMiddleware` setting (`allow_origins=["*"]`) is intended for
  local development. Restrict origins before exposing OpenWatch publicly.
- The MCP `run_query` tool is SELECT-only but still permits arbitrary read
  access to the warehouse. Run OpenWatch behind authentication if the data
  contains anything sensitive.
- The SQLite database file should have filesystem permissions restricted to
  the OpenWatch process user.
