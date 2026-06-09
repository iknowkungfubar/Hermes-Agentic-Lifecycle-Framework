# Phase 3: Quality Assurance

**Objective:** Ensure correctness, security, and robustness through comprehensive testing and red-teaming.

## Steps

- **3A: Test Suite Completeness** — FR coverage matrix, gap test generation
- **3B: Security Hardening** — SAST scan (bandit, semgrep) + 4-agent adversarial red-teaming
- **3C: Integration & Contract Tests** — End-to-end journeys, schema verification, load tests

## Red-Teaming Agents

1. **Pentester** — SQL injection, XSS, CSRF, SSRF, IDOR, auth bypass
2. **Cryptographer** — Password hashing, JWT, session management, rate limiting
3. **Infrastructure** — Docker, CI/CD, CORS, env handling, supply chain
4. **AI/Model** — Prompt injection, output validation, data poisoning

## Gate Check (G3)

- G3.1: Coverage ≥80% line, ≥70% branch
- G3.2: All FRs have tests
- G3.3: No CRITICAL security findings
- G3.5: Integration tests pass
- G3.7: No secrets in codebase
