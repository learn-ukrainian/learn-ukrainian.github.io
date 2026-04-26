# Learn Ukrainian — System Architecture

> Last updated: 2026-03-15 | Issue: #892
>
> ⚠️ **LEGACY V5/V6-ERA DOC.** This document predates the EPIC #1577 reboot and describes the V5/V6 pipeline + the "Gemini builds → Claude reviews" agent paradigm, both of which are being replaced. Reboot-era authority lives in:
> - [`docs/north-star.md`](../north-star.md) — what we're building and why
> - [`docs/lesson-contract.md`](../lesson-contract.md) — what artifacts the pipeline must produce
> - [`docs/decisions/2026-04-26-reboot-agent-responsibilities.md`](../decisions/2026-04-26-reboot-agent-responsibilities.md) — agent-role assignments (writer TBD, reviewer = Codex, wiki = Gemini)
> - [`scripts/build/linear_pipeline.py`](../../scripts/build/linear_pipeline.py) — the new pipeline (Phase 4 in flight, PR #1594)
>
> Read this doc only for V5/V6 historical context. Specific lines below that hardcode "Gemini builds → Claude reviews" are V5/V6 paradigm and are NOT current reboot policy.

## Overview

Learn Ukrainian is an AI-powered content factory that generates Ukrainian language learning materials. **In the V5/V6 era covered by this doc**, two AI agents (Gemini builds, Claude reviews) produced curriculum content through a deterministic pipeline with quality gates and adversarial cross-review. **In the reboot**, the writer is TBD (decided at Phase 5+ approach), the reviewer is Codex, and an LLM still never reviews its own work.

**Scale**: ~1700 modules across 23 tracks, ~143K LOC in `scripts/`, 25 JSON schemas.

## System Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                     PIPELINE v5 (build_module_v5.py)                   │
│                                                                        │
│  ┌──────────┐  ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌──────────┐  │
│  │ research │→ │ content │→ │validate │→ │activities│→ │  review  │→ mdx
│  └──────────┘  └─────────┘  └─────────┘  └──────────┘  └──────────┘  │
│       │         ↑ preflight    │              │           ↑ builder    │
│       │         ↑ learner      │              │           ↑ notes      │
│       │         ↑ state        │              │                       │
│  ┌────▼────┐  ┌─▼──────┐  ┌──▼─────┐  ┌────▼────┐  ┌──▼───────┐   │
│  │ Gemini  │  │ Gemini │  │ Determ │  │ Gemini  │  │  Claude  │   │
│  │(research)│  │(write) │  │(VESUM) │  │(YAML)   │  │(review)  │   │
│  └─────────┘  └────────┘  └────────┘  └─────────┘  └──────────┘   │
└────────────────────────────────────────────────────────────────────────┘
         │              │                                    │
    ┌────▼────┐    ┌────▼────┐                         ┌────▼────┐
    │   RAG   │    │ VESUM   │                         │  Audit  │
    │(textbooks│    │(415K    │                         │(34 gates│
    │ wiki,lit)│    │ lemmas) │                         │         │
    └─────────┘    └─────────┘                         └─────────┘
```

## Pipeline Phases (v5)

| # | Phase | Agent | Purpose | Pre-conditions |
|---|-------|-------|---------|----------------|
| 1 | **research** | Gemini | Web research, textbook search, meta outline | Plan exists |
| 2 | **discover** | Gemini | YouTube discovery (non-blocking) | — |
| 3 | **content** | Gemini | Lesson prose + vocabulary | Preflight passes, learner state injected |
| 4 | **validate** | Deterministic | VESUM morphology, Russicism detection, euphony | Content exists |
| 5 | **activities** | Gemini | Interactive activities YAML (reads written content) | Content validated |
| 6 | **review** | **Claude** | Cross-agent adversarial review of content + activities | All build phases complete |
| 7 | **mdx** | Deterministic | Markdown → Starlight MDX | Review done or skipped |

**Key design**: Activities come AFTER validate so they're grounded in the validated content. Review comes LAST so it sees the complete module.

### Pre-Content Gates (run before content phase)

| Gate | Script | What it checks |
|------|--------|----------------|
| **Preflight** | `pipeline/prompt_preflight.py` | Gemini reviews its own prompt for contradictions. Auto-fixes HIGH issues. |
| **Semantic Russianisms** | `pipeline/semantic_russianisms.py` | Catches words in plan with Russian meanings (e.g., лук=onion → цибуля) |
| **Learner State** | `pipeline/learner_state.py` | Injects cumulative vocabulary + grammar from all previous modules |

### Content Phase Enhancements

| Feature | What it does |
|---------|-------------|
| **Builder Notes** | Gemini outputs structured YAML (deviations, frictions, unverified terms) |
| **Prompt restructuring** | Goal → Context → Outline → Guidelines → Constraints (not constraints-first) |
| **Split mode** | Content and activities are separate phases (default), not one pass |

## Three-Layer Content Architecture

```
plans/{level}/{slug}.yaml    →  Source of truth (reviewed before lock)
{level}/{slug}.md + yaml     →  BUILD artifacts (AI-generated)
{level}/status/{slug}.json   →  AUDIT cache (system-generated)
```

| Layer | Location | Owner | Lifecycle |
|-------|----------|-------|-----------|
| **Plans** | `curriculum/l2-uk-en/plans/` | Human + LLM (reviewed) | DRAFT → REVIEWED → LOCKED |
| **Build** | `curriculum/l2-uk-en/{level}/` | Gemini | Rebuilt by pipeline |
| **Status** | `curriculum/l2-uk-en/{level}/status/` | Audit system | Auto-generated |

## AI Agent Architecture

```
┌─────────────────────────┐        ┌─────────────────────────┐
│   Claude (Blue Team)     │        │   Gemini (Gold Team)     │
│   - Architect            │  ask-  │   - Content builder      │
│   - Reviewer             │◄─────►│   - Researcher           │
│   - Code author          │ gemini │   - Activity creator     │
│   - Quality gate         │converse│   - Adversarial reviewer │
│                          │        │     (of Claude's work)   │
│   CLAUDE.md              │        │   GEMINI.md              │
│   (mission, rules, RAG)  │        │   (mission, scoring,     │
│                          │        │    RAG tools, coop)      │
└─────────────────────────┘        └─────────────────────────┘
```

**Rule (V5/V6 era)**: An LLM must NEVER review its own work. Gemini builds → Claude reviews. **Reboot-era equivalent**: same constraint, different agents — writer-of-the-moment builds → Codex reviews. See [`docs/decisions/2026-04-26-reboot-agent-responsibilities.md`](../decisions/2026-04-26-reboot-agent-responsibilities.md).

### Cooperation Tooling

| Tool | Command | Purpose |
|------|---------|---------|
| **One-shot** | `ask-gemini "msg" --task-id issue-N` | Reviews, simple requests |
| **Multi-turn** | `converse "msg" --task-id "topic"` | Co-design, planning, iteration |
| **Builder Notes** | `===BUILDER_NOTES_START===` | Structured handoff after builds |

The bridge is NOT an MCP tool. It uses SQLite broker DB + subprocess spawning. Claude always initiates.

## Subsystems

### 1. Pipeline (`scripts/build/pipeline_v5.py` + `scripts/pipeline/`)
**~11K LOC** | Entry: `scripts/build_module_v5.py`

Supporting modules:
- `pipeline/state.py` — Phase tracking, restarts
- `pipeline/parsing.py` — Markdown/YAML parsing
- `pipeline/screen.py` — Content screening
- `pipeline/fixes.py` — FIND/REPLACE fix application
- `pipeline/prompt_preflight.py` — Prompt review + auto-fix
- `pipeline/learner_state.py` — Cumulative vocab + grammar manifest
- `pipeline/semantic_russianisms.py` — Semantic false friend detection
- `pipeline/consultation.py` — Template improvement loop
- `pipeline_lib.py` — Shared utilities

### 2. Audit System (`scripts/audit/`)
**~23K LOC** | Entry: `scripts/audit_module.py` | 34 check modules

### 3. RAG System (`scripts/rag/` + `.mcp/servers/sources/`)
**~8K LOC** | MCP server at port 8766

| Source | MCP Tool |
|--------|----------|
| Textbooks (1.2K chunks) | `search_text` |
| Literary sources | `search_literary` |
| VESUM (415K lemmas) | `verify_word`, `verify_lemma` |
| Ukrainian Wikipedia | `query_wikipedia` (5 modes) |
| GRAC corpus | `query_grac` |
| Pravopys 2019 | `query_pravopys` |
| r2u dictionary | `query_r2u` |
| ULIF paradigms | `query_ulif` |

### 4. API Server (`scripts/api/`)
**~6K LOC** | FastAPI + WebSocket | Port 8765

### 5. Agent Bridge (`scripts/ai_agent_bridge/`)
**~2K LOC** | Claude↔Gemini communication via subprocess + SQLite broker

### 6. Prompt Templates (`claude_extensions/phases/gemini/`)
**~54 files** | Phase-specific prompts injected during pipeline execution

Key templates:
- `beginner-full-rag.md` — Beginner content (220 lines, restructured)
- `beginner-activities.md` — Beginner activities (separate phase)
- `review-structured.md` — Claude D.1 review
- `review-repair.md` — Claude D.2 fix

### 7. Batch Operations, Scoring, Code Generation, Playgrounds
See `docs/SCRIPTS.md` for full reference.

## Curriculum Tracks

### Core Language: `l2-uk-en` (A1→C2)
Ukrainian for English-speaking teens and adults.

### Seminar Tracks (B2–C1)
HIST, BIO, ISTORIO, LIT, OES, RUTH — history, literature, biography.

### Secondary: `l2-uk-direct` (A1→B2)
L1-agnostic Ukrainian. Separate schemas, no English.

## Quality Systems

| System | Type | Entry Point |
|--------|------|-------------|
| Audit (34 gates) | Deterministic | `scripts/audit_module.py` |
| VESUM morphology | Dictionary | `audit/checks/morphological_validator.py` |
| Russicism detection | Rule-based | Part of validate phase |
| Semantic Russianisms | Dictionary | `pipeline/semantic_russianisms.py` |
| Preflight | LLM + auto-fix | `pipeline/prompt_preflight.py` |
| Content review | LLM (Claude) | Review phase |
| Builder notes | LLM (Gemini) | Extracted from build output |

## Key Design Decisions

1. **Pipeline v5 is the ONLY pipeline** — v3/v4 retired
2. **VESUM is ground truth** — 415K lemmas, all Ukrainian words verified
3. **Plans reviewed before lock** — DRAFT → REVIEWED → LOCKED lifecycle
4. **Split build** — Content and activities are separate phases (default)
5. **Activities after validate** — Grounded in validated content
6. **Review sees everything** — Content + activities + vocabulary
7. **Cross-agent review** — V5/V6: Gemini builds, Claude reviews. Reboot: writer TBD, Codex reviews. Never self-review either way.
8. **Preflight auto-fix** — Fix prompt contradictions before wasting a build
9. **Learner state injection** — Gemini knows what the student knows
10. **Builder notes** — Structured handoff from Gemini to Claude

## Related Documentation

| Topic | Location |
|-------|----------|
| Pipeline commands | `docs/SCRIPTS.md` |
| Agent cooperation | `docs/best-practices/agent-cooperation.md` |
| Cooperation protocol | `docs/CLAUDE-GEMINI-COOPERATION.md` |
| Audit standards | `docs/best-practices/audit-standards.md` |
| Track architecture | `docs/best-practices/track-architecture.md` |
| Activity YAML | `docs/ACTIVITY-YAML-REFERENCE.md` |
| Monitoring API | `docs/MONITOR-API.md` |
