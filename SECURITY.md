# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.0.x   | ✅ Active development |

## Reporting a Vulnerability

HALF is an early-stage framework. If you discover a security vulnerability,
please do **NOT** open a public issue. Instead, email: **josh@turintechsolutions.com**

You should receive a response within 48 hours. If you don't, follow up.

### What to include

- Type of vulnerability
- Steps to reproduce
- Affected versions
- Potential impact
- Suggested fix (if available)

## Security Features

HALF includes the following security measures by design:

### CVE Mitigations

| CVE | Component | Mitigation |
|-----|-----------|------------|
| CVE-2025-67644 | LangGraph SQLite | Metadata allowlist validates all filter keys before execution |
| CVE-2026-28277 | LangGraph msgpack | JSON-safe serialization prevents RCE via malicious objects |

### Execution Sandbox

- Code runs in isolated Docker/Podman containers
- Obsidian vault mounted read-only to sandbox
- Network access stripped from execution containers
- Dangerous shell commands blocked via deny list
- Path traversal attempts rejected by pre-execution hooks

### Supply Chain Security

- Dependencies pinned with exact versions in `uv.lock`
- Weekly dependency audits via GitHub Actions
- Dependency licenses verified before production release
- No postinstall scripts executed during dependency resolution

### Secret Management

- No hardcoded secrets in codebase
- `.env` files in `.gitignore`
- Secret detection in CI pipeline (trufflehog)
- Environment variables for all sensitive configuration
