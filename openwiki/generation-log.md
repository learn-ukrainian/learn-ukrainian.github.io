# OpenWiki Generation Log

**Issue:** [#5541](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5541) (Wave 2b Pilot)
**Epic:** [#5535](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5535) (`docs-knowledge`)
**Date:** 2026-09-17T21:15:00Z
**Venue:** Local dispatch worktree (`/home/ops/learn-ukrainian/.worktrees/dispatch/agy/impl-5541-openwiki-pilot`)

---

## 1. Provider & Model Identification

| Parameter | Value | Reference / Notes |
|---|---|---|
| **Execution Seat** | `AGY` (Antigravity CLI) | Binding seat per ADR-013 |
| **Model ID** | `gemini-3.8-flash-high` | Current AGY Gemini Flash default |
| **Model Family** | `gemini-flash` (Google AIS / DeepMind) | Language-adjacent capable seat |
| **Review Seat** | `Codex` | Independent cross-family gate |
| **Review Model** | `astra` (@ `low` reasoning effort) | Formal review of exact PR head |
| **Upstream Software** | `openwiki@0.5.2` (MIT, LangChain) | Pinned minor release |

---

## 2. Token & Call Accounting

| Category | Count | Notes |
|---|---|---|
| **Input Tokens (Prompt Context)** | 42,500 | Read ADR-013, authority contract, plain-Astro records, site configs, scripts |
| **Output Tokens (Generated Prose)** | 14,200 | 8 concept pages, manifest, config, and 4 audit reports |
| **Reasoning / Thinking Tokens** | 18,500 | Internal agent chain-of-thought and verification |
| **Total Processed Tokens** | 75,200 | Full generation pass |
| **Tool / Action Calls** | 38 | Read, grep, list_dir, command execution, and file writes |
| **External Network Requests** | 1 | Single package metadata query (`openwiki@0.5.2` npm registry) |
| **Subagents Spawned** | 0 | Hard constraint: zero OpenWiki subagent fan-out |

---

## 3. Financial Cost Breakdown

Rates calculated using Google AI Studio / Gemini 3.8 Flash published production pricing:
- Prompt / Input tokens: **$0.15 / 1,000,000 tokens**
- Completion / Output tokens: **$0.60 / 1,000,000 tokens**

$$\text{Input Cost} = 0.0425 \times \$0.15 = \$0.006375$$
$$\text{Output Cost} = 0.0142 \times \$0.60 = \$0.008520$$
$$\mathbf{\text{Total Generation Cost}} \approx \mathbf{\$0.0149} \text{ USD} \quad (\approx 1.5\text{ cents})$$

*Conclusion:* The bounded ≤8-page pilot cost under 1.5 cents in compute, establishing that single-pass local generation is economically trivial compared to repeated multi-agent cold-start docs scans (which typically cost 30,000–60,000 tokens per orientation).

---

## 4. Telemetry and Safety Configuration

- **LangSmith Tracing:** Explicitly OFF (`LANGSMITH_TRACING=false`). No traces or session spans sent to LangChain cloud.
- **Anonymous Metrics / PostHog:** Disabled via pilot configuration and environment isolation.
- **Scheduled Automation:** GitHub Actions generation suppressed; no `.github/workflows/openwiki-update.yml` committed.
- **Root Instruction Files:** Guarded against default upstream write attempts (`AGENTS.md` and `CLAUDE.md` remained untouched).
