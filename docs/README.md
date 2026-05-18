# Learn Ukrainian — Documentation Map

> **Purpose:** Canonical entry point for AI agents orienting cold. Lists the authoritative docs by topic, in priority order. **Read THIS first, not the 36 top-level files alphabetically.**

## Cold-start sequence (fastest orient)

1. **Monitor API** (zero-token state). Try first:
   - `curl -s http://localhost:8765/api/state/manifest`
   - `curl -s http://localhost:8765/api/orient`
   - `curl -s 'http://localhost:8765/api/rules?format=markdown'` (if rules hash changed)
   - `curl -s 'http://localhost:8765/api/session/current?format=markdown'` (if session hash changed)
2. **Behavioral rules:** `memory/MEMORY.md` (cross-session, hard-won lessons)
3. **Agent-specific instructions:** `CLAUDE.md` (Claude), `AGENTS.md` (other AI), `GEMINI.md` (Gemini)
4. **Active task:** latest `docs/session-state/*.md` (chronological handoffs; newest first via `ls -t`)

If Monitor API is down, fall back to: `memory/MEMORY.md` → `CLAUDE.md` → latest `docs/session-state/*.md`.

---

## Spec inheritance — V5/V6 baseline cascades to V7

**Important:** V5/V6 documentation is **historical reference, not deleted policy**. The pipeline is layered:

- V5/V6 baseline specs (pedagogy, lesson contract, quality standards, agent cooperation, audit gates) remain authoritative for anything V7 has not explicitly overridden.
- V7 is a delta layer: it changes the build orchestration (worktrees, linear pipeline, MCP retrieval, new writer architecture) but inherits V5/V6 for pedagogy, content quality, dictionary discipline, etc.
- If V7-era docs don't address a topic, fall back to V5/V6 era docs. They still apply.

When in doubt: V7 doc overrides → V6 doc fills in → V5 doc fills in.

---

## Authoritative docs by topic

### Mission, learner, lesson contract

- `docs/north-star.md` — what we're building and why (DRAFT v3, signed off 2026-05-04 by Codex+Gemini). Authoritative.
- `docs/lesson-contract.md` — what shape every lesson takes (DRAFT v3, same sign-off). Authoritative.

### Pipeline architecture

- `claude_extensions/rules/pipeline.md` (deployed to `.claude/rules/pipeline.md`, `.codex/rules/pipeline.md`, etc.) — **current V7 policy.** Reviewer/writer assignment, decision-card links.
- `docs/architecture/ARCHITECTURE.md` — **V5/V6 era** per its own banner at line 5. Still authoritative for pedagogy + agent-cooperation patterns V7 didn't override.
- `docs/architecture/RFC-410-MANIFEST-DRIVEN-ARCHITECTURE.md` — manifest-driven curriculum structure (Approved 2026-01-17).
- `docs/architecture/adr/*.md` — sequential architectural decision records.
- `docs/decisions/*.md` — dated decision journal (signal-rich, chronological).

### Best practices (per-topic)

`docs/best-practices/` has 33 files. Most-load-bearing:

- `agent-activity-matrix.md` — canonical task-type × agent routing matrix (v1.1, 2026-05-17)
- `module-content-quality.md` — content standards
- `audit-standards.md` — gate definitions
- `vocabulary-activity-standards.md` — vocab + activity formats
- `activity-pedagogy.md` — level → activity type matrix
- `agent-cooperation.md` — inter-agent protocol
- `harness-engineering.md` — orchestration patterns
- `deterministic-over-hallucination.md` — anti-fabrication rule (MEMORY #M-4)
- `prompt-engineering.md`, `context-engineering.md` — agent-prompt design
- `code-quality.md`, `git-hygiene.md`, `gitflow.md` — engineering practices
- `decision-journal.md`, `adr-management.md` — governance

### Behavioral / rules

- `claude_extensions/rules/*.md` — source (canonical). `.claude/`, `.agent/`, `.codex/`, `.gemini/` are deploy targets.
- `claude_extensions/rules/goal-driven-runs.md` — `/goal` convention (#1884)
- `claude_extensions/rules/mcp-sources-and-dictionaries.md` — MCP tool inventory
- `claude_extensions/rules/critical-rules.md` (loaded via Monitor API, see `_load-via-api.md`)

### Tracks

- `docs/best-practices/track-architecture.md` — track structure
- `docs/l2-uk-en/` — Ukrainian for English-speakers (main track)
- `docs/l2-uk-direct/` — Ukrainian L1-agnostic (separate schemas)

### State of the project

- `docs/session-state/` — chronological session handoffs. `ls -t` for newest. Read top-1 to top-3 for context.
- `docs/MASTER-PLAN.md` — priority sequencing
- `audit/` (top-level, NOT `docs/audits/`) — build-produced reports + recurring audits

### Operational

- `docs/SCRIPTS.md` — commands and scripts
- `docs/MONITOR-API.md` — Monitor API endpoints
- `docs/agent-runtime-guide.md` — agent CLI invocation adapter layer

---

## Navigation hazards (known issues, 2026-05-18)

1. **36 top-level docs/ files, no semantic grouping.** Authoritative `north-star.md` sits among April archives. Use this README as primary index.
2. **18 HTML/MD duplicate pairs.** Prefer `.md` for AI-consumption; `.html` is a human-rendering companion only.
3. **Rule deploy drift risk.** `claude_extensions/rules/*.md` is source; deployed copies may lag if `scripts/deploy_prompts.sh` hasn't been run. Verify with `diff claude_extensions/rules/X.md .claude/rules/X.md`.
4. **V5/V6 era docs not in `_legacy/`.** `docs/architecture/ARCHITECTURE.md` is legacy but at canonical path. Read its own banner before treating as current.
5. **`docs/architecture/adr/` vs `docs/decisions/`.** ADRs are architectural decisions; decisions are operational/policy. Both authoritative within scope.

A full spec-gap audit + reorganization plan exists at `audit/2026-05-18-docs-gaps-and-reorganization/REPORT.md`.

---

## When this README is wrong

If you're an AI agent and this README contradicts what you find in a specific authoritative doc, **trust the specific doc**. Open an issue to fix the README. The chain of authority is: dated decision cards > current rules > best-practices > this README.
