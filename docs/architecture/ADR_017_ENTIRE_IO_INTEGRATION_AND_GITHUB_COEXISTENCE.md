# ADR 017: Entire.io AI-Driven Workload Migration & GitHub Coexistence Architecture

> **Status**: APPROVED  
> **Date**: July 24, 2026  
> **Authors**: Sol (`gpt-5.6-sol`), Lead Architect & Antigravity  
> **Target Track**: Infrastructure & Fleet DevOps (`infra-hramatka` stream)

---

## 1. Context & Motivation

As our AI-driven development fleet expands across multiple model families (Codex, Gemini 3.6 Flash, Claude Opus, Grok), traditional Git workflows require enhanced agentic orchestration, continuous prompt telemetry, and automated PR review gating. 

We are adopting **Entire.io** as our primary AI-driven agentic development environment. Entire.io coexists seamlessly with GitHub, serving as the execution and orchestration plane while GitHub remains our immutable source of truth and repository origin.

---

## 2. Coexistence Architecture: Entire.io + GitHub

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          ENTIRE.IO AI PLANE                             │
│  • Autonomous Agent Fleet Orchestration (Codex, Gemini, Claude)        │
│  • Continuous Prompt Telemetry & Multi-Agent Deliberation               │
│  • Automated Layout A Worktree Dispatch (.worktrees/dispatch/...)       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                         (Bi-Directional Sync)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         GITHUB ORIGIN (PRIMARY)                         │
│  • Primary Git Remote (`origin/main`)                                   │
│  • Immutable Commit History & Release Tags                              │
│  • Automated CI/CD Actions & PR Review Gates                            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Key Integration Rules

1. **GitHub Remains Source of Truth**:
   - All code, documentation, and dataset manifests originate and settle on GitHub (`origin/main`).
   - Entire.io pushes feature branches (`gemini/*`, `codex/*`, `claude/*`) and creates GitHub Pull Requests automatically.

2. **Layout A Subtree Worktree Isolation Preserved**:
   - Entire.io agent execution workers strictly maintain our subtree worktree directory structure: `.worktrees/dispatch/<agent>/<task-id>/`.
   - Primary `main` branch on local checkouts remains 100% clean.

3. **Mandatory `X-Agent` Commit Trailers**:
   - Every commit produced within Entire.io MUST carry an `X-Agent` trailer:
     ```
     X-Agent: <agent-family>/<task-id>
     ```
   - Entire.io pre-commit hooks run `.venv/bin/python scripts/audit/lint_agent_trailer.py` to enforce compliance.

4. **Quality Gates & Linters**:
   - Entire.io executes deterministic Quality Gates (`scripts/audit/hramatka_qg_rules.py`) before submitting PRs to GitHub.

---

## 4. Migration & Onboarding Sequence

1. **Step 1**: Connect GitHub repositories (`learn-ukrainian` and `learn-ukrainian-infra-private`) to Entire.io via GitHub App integration.
2. **Step 2**: Configure Entire.io agent workspace definitions to use `.venv/bin/python` for all script invocations.
3. **Step 3**: Route active Hramatka App tickets (Epic #4542) through Entire.io agent workers.

---

*Architectural Decision Record 017 ratified by Sol (`gpt-5.6-sol`), Lead Architect.*
