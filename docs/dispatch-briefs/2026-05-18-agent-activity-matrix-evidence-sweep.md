# Dispatch brief — Agent activity matrix evidence sweep

**Agent:** Gemini gemini-3.0-flash-preview (unmetered routine extraction)
**Mode:** danger (commits + PR open; NO auto-merge)
**Worktree:** required (per #1952)
**Issue:** none (file as part of agent-activity-matrix work)
**Severity:** MEDIUM (enables data-driven routing across 5 agents)

---

## Why

The project has 5 agents (Claude, Codex, Gemini, DeepSeek, Grok) and we have rich empirical bakeoff data scattered across `audit/bakeoff-*` and `audit/2026-05-*` directories. The data is presently unindexed — routing decisions get made from half-remembered handoffs instead of a queryable evidence base.

User directive 2026-05-18: *"compile activity matrix + publish test results of each agent at different jobs."*

This brief produces the **evidence layer** for the matrix. The orchestrator (Claude) compiles the matrix itself; Gemini's job is to extract structured rows from existing bakeoff REPORTs + decisions + MEMORY references.

---

## What you build

A single file: **`audit/INDEX-bakeoff-evidence.md`** — structured catalogue of every bakeoff + agent-comparison run we've done, with rows for each task type × agent comparison.

### Sources to crawl

1. `audit/bakeoff-*/` — every directory matching this pattern. Look for `REPORT.md`, `SUMMARY.md`, or any *.md describing results.
2. `audit/2026-05-*-bakeoff*/` — newer naming convention.
3. `audit/2026-05-*-judge-calibration*/` — judge-calibration runs (multiple agents compared as reviewers).
4. `docs/decisions/*.md` — decisions that reference agent selection (filter for ones mentioning "writer", "reviewer", "agent", "claude-tools", "codex-tools", "gemini-tools", "bakeoff").
5. `memory/MEMORY.md` — read the `#M-0` per-task model assignment section verbatim into the index for cross-reference.
6. `scripts/config/agent_fallback_substitutions.yaml` — quote the substitutions block verbatim.

### Output structure (`audit/INDEX-bakeoff-evidence.md`)

```markdown
# Agent bakeoff evidence index

> Generated <YYYY-MM-DD> by Gemini dispatch (agent-activity-matrix evidence sweep).
> Source: audit/bakeoff-*/, audit/2026-05-*-bakeoff*, docs/decisions/, memory/MEMORY.md.

## 1. Bakeoff catalogue (chronological)

| Date | Bakeoff | Task type | Agents compared | Winner | Source path |
|---|---|---|---|---|---|
| 2026-05-12 | writer-selection v3 | V7 module writer | claude-tools, codex-tools | claude-tools | audit/bakeoff-2026-05-12-night/REPORT.md |
| ... | ... | ... | ... | ... | ... |

## 2. Per-bakeoff one-paragraph summary

### audit/bakeoff-2026-05-12-night
**Date:** 2026-05-12 ~02:20 CET
**Task:** V7 module writer on a1/my-morning
**Agents:** claude-tools, codex-tools
**Verdict:** claude-tools wins (1224-word module + 4 MCP tool calls + vesum_verified pass); codex-tools tool_calls_total=0 (theatre, MCP_TOOLS_NEVER_INVOKED guard fired).
**Key metric:** tool_calls_total (4 vs 0).
**Decision-card delta:** REVISED — docs/decisions/2026-05-06-writer-selection-codex-gpt55.md flipped from codex-tools to claude-tools.
**Limitations:** single-module sample; codex's tool theatre may be addressable with further prompt iteration.

### audit/2026-05-17-agent-bakeoff-evening
... (one paragraph per bakeoff)

## 3. Per-task evidence rollup

For each known task type, list every bakeoff that touched it + outcome:

### V7 module writing
- 2026-05-06 (audit/bakeoff-2026-05-05/REPORT.md): codex-tools wins 3-way (claude/gemini/codex)
- 2026-05-12 (audit/bakeoff-2026-05-12-night/REPORT.md): claude-tools wins 1v1 vs codex-tools (REVERSAL)
- (any later evidence...)

### V7 module reviewing (judge calibration)
- 2026-05-15 (audit/2026-05-15-grok-4.3-judge-calibration/...): grok eval
- 2026-05-17-h1 (audit/2026-05-17-judge-calibration-h1/COMPARISON.md): outcome
- 2026-05-17-h2 (audit/2026-05-17-judge-calibration-h2/...): outcome

### Adversarial review
- (any bakeoffs)

### Code dispatch (mechanical / novel-impl / architectural)
- (per-agent evidence from delegate.py runs)

### Q&A / discussion
- (ab discuss / ab ask-* evidence — may be limited)

## 4. Verbatim references

### MEMORY.md #M-0 (canonical assignment table)
```
<quote the entire #M-0 section verbatim>
```

### scripts/config/agent_fallback_substitutions.yaml
```yaml
<quote the entire substitutions: block verbatim>
```

### docs/decisions/ — agent-selection-relevant
- 2026-05-06-writer-selection-codex-gpt55.md — `<status as of latest line in file>`; brief verbatim quote of the "REVISED-AGAIN" line and the final ACCEPTED outcome.
- 2026-04-26-reboot-agent-responsibilities.md — `<status>`; verbatim quote of §1 (wiki writer = Gemini) and §2 (pipeline reviewer = Codex).
- (any others referencing agents)

## 5. Open gaps

List task types for which we have NO bakeoff evidence:
- ...
- ...
```

### Style guide for the index

- **Tables for catalogue rows**, prose for per-bakeoff summaries.
- One paragraph per bakeoff summary — terse, factual, ≤6 lines.
- Verbatim quotes for the MEMORY/YAML/decision references — don't paraphrase.
- File paths absolute from repo root (e.g. `audit/bakeoff-2026-05-12-night/REPORT.md`, not URLs).
- No emojis.
- HTML companion: don't generate `.html` for this artifact — it's ai-to-ai consumption (the matrix-compiler reads it next). Per #M-2.

---

## Verifiable claims (per #M-4)

| Claim | Tool + raw output |
|---|---|
| Every `audit/bakeoff-*/` dir is listed | `ls -d audit/bakeoff-* audit/2026-05-*-bakeoff* audit/2026-05-*-judge-calibration* 2>/dev/null` count vs catalogue row count |
| Every `docs/decisions/*.md` referencing an agent is listed | `grep -l -iE "(claude-tools|codex-tools|gemini-tools|deepseek|grok|bakeoff)" docs/decisions/*.md` count vs §4 entry count |
| MEMORY.md #M-0 quoted verbatim | `sha256sum` of the quoted block matches the original section's hash |
| Index file added | `git diff --stat origin/main` showing `audit/INDEX-bakeoff-evidence.md` (NEW) |
| Pre-commit clean | `.venv/bin/python -m pre_commit run --files audit/INDEX-bakeoff-evidence.md` raw output |
| Commit + PR | `git log -1 --oneline` + `gh pr view --json url` raw |

**No claim allowed without its raw output line.** Per #M-4.

---

## Worktree setup

Branch: `docs/agent-activity-matrix-evidence-sweep`. Path: `.worktrees/dispatch/gemini/agent-activity-matrix-evidence-sweep-<timestamp>/`.

## Verification (must run all BEFORE pushing)

```bash
# venv symlinked from main; run from worktree root
.venv/bin/python -m pre_commit run --files audit/INDEX-bakeoff-evidence.md
# Cross-check catalogue completeness:
ls -d audit/bakeoff-* audit/2026-05-*-bakeoff* audit/2026-05-*-judge-calibration* 2>/dev/null | wc -l
grep -c '^| 2026-' audit/INDEX-bakeoff-evidence.md
# These two numbers should be close (every bakeoff dir → at least one catalogue row).
git diff --stat origin/main
```

## Commit + PR

Conventional commit. Title: `docs(audit): index bakeoff evidence for agent activity matrix`. Body summarizes:
1. Why (matrix compilation needs evidence base)
2. Sources crawled (bakeoff dirs N, decisions M, MEMORY #M-0, agents.yaml, fallback YAML)
3. Per-task rollup highlights (top 3 task types by evidence density)
4. Open gaps (task types with no bakeoff data)
5. All verifiable-claims raw outputs

NO `--auto-merge`.

## Out of scope

- Don't propose ANY routing changes or new matrix structure — that's the orchestrator's job. You produce the evidence index ONLY.
- Don't run new bakeoffs.
- Don't edit `memory/MEMORY.md`, `docs/decisions/*.md`, `scripts/config/agent_fallback_substitutions.yaml` — read-only sources.
- Don't generate HTML — the index is ai-to-ai consumption.
- Don't include unrelated bakeoffs (e.g. corpus-eval bakeoffs that aren't agent-comparison) — agent-vs-agent only.

## Anti-fabrication preamble

If a bakeoff dir has NO summary file (`REPORT.md`, `SUMMARY.md`, etc.), list it in §5 (Open gaps) — DO NOT invent a winner from filename patterns. If a decision card has multiple ACCEPTED/REVISED rounds, quote the LATEST status line verbatim and label its date.

If `audit/2026-05-17-agent-bakeoff-evening/` has 65 raw output files but no summary, that's a real evidence gap — list it as such, don't synthesize a verdict from raw outputs.

## Notes for orchestrator (Claude, not Gemini)

* This is the evidence base for compiling `docs/best-practices/agent-activity-matrix.md`. Both happen in parallel.
* Estimated duration: 30-45 min (read ~15 bakeoff dirs + ~17 decision files + MEMORY/YAML quote + write structured markdown).
* On finalize: orchestrator reads the index and uses it as §0 evidence in the activity matrix document.
* Wiring downstream (`/api/activity-matrix`, dashboard, promote-protocol) is filed as separate follow-up.
