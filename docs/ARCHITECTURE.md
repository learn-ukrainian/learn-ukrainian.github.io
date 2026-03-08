# Learn Ukrainian — System Architecture

> Last updated: 2026-03-08 | Issue: #796

## Overview

Learn Ukrainian is an AI-powered content factory that generates Ukrainian language learning materials. Two AI agents (Gemini builds, Claude reviews) produce curriculum content through a deterministic pipeline with 34 quality gates.

**Scale**: ~600 modules across 10 tracks, ~143K LOC in `scripts/`, 25 JSON schemas.

## System Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                        PIPELINE v5 (build_module_v5.py)              │
│  research → discover → sandbox → content → activities → validate     │
│                                              → [review] → mdx        │
└─────────┬──────────┬────────────┬──────────┬────────────┬───────────┘
          │          │            │          │            │
    ┌─────▼───┐ ┌───▼────┐ ┌────▼───┐ ┌───▼────┐ ┌────▼─────┐
    │ Gemini  │ │  RAG   │ │ VESUM  │ │ Claude │ │  Audit   │
    │ (build) │ │ (data) │ │(morph) │ │(review)│ │ (gates)  │
    └─────────┘ └────────┘ └────────┘ └────────┘ └──────────┘
```

## Three-Layer Content Architecture

```
plans/{level}/{slug}.yaml    →  IMMUTABLE source of truth (human-owned)
{level}/{slug}.md + yaml     →  BUILD artifacts (AI-generated)
{level}/status/{slug}.json   →  AUDIT cache (system-generated)
```

| Layer | Location | Owner | Mutability |
|-------|----------|-------|------------|
| **Plans** | `curriculum/l2-uk-en/plans/` | Human architect | Immutable (version-bumped with approval) |
| **Build** | `curriculum/l2-uk-en/{level}/` | AI agents (Gemini) | Mutable (rebuilt by pipeline) |
| **Status** | `curriculum/l2-uk-en/{level}/status/` | Audit system | Auto-generated, cached |

## Subsystems (11)

### 1. Pipeline (`scripts/pipeline_v5.py` + `scripts/pipeline/`)
**~11K LOC** | Entry: `scripts/build_module_v5.py`

The sole build pipeline. v3/v4 are retired.

| Phase | LLM | Purpose |
|-------|-----|---------|
| **research** | Gemini | Web research, meta outline, friction hooks |
| **discover** | Gemini | YouTube discovery, transcript scoring |
| **sandbox** | _(none)_ | VESUM-validated word bank (deterministic) |
| **content** | Gemini | Full lesson prose with lexical sandbox |
| **activities** | Gemini | Interactive activities + vocabulary YAML |
| **validate** | Gemini | Morphological validator + Russicism check + fix loop |
| **review** | **Claude** | Cross-agent adversarial review (optional, max 2 fix attempts) |
| **mdx** | _(none)_ | Deterministic markdown → Docusaurus MDX |

Non-blocking phases: discover, sandbox, validate, review.

Supporting modules:
- `scripts/pipeline/state.py` — State machine (phase tracking, restarts)
- `scripts/pipeline/parsing.py` — Markdown/YAML parsing
- `scripts/pipeline/screen.py` — Content screening
- `scripts/pipeline/fixes.py` — Post-phase deterministic fixes
- `scripts/pipeline_lib.py` — Shared pipeline utilities (legacy, being decomposed)

### 2. Audit System (`scripts/audit/`)
**~23K LOC** | Entry: `scripts/audit_module.py`

34 specialized check modules enforcing quality gates.

```
scripts/audit/
├── core.py                    # Orchestrator (AuditContext + AuditState pattern)
├── config.py                  # Level-specific thresholds (word targets, gate minimums)
├── gates.py                   # Gate evaluation + recommendation engine
├── report.py                  # Terminal + markdown report generation
├── status_cache.py            # Status JSON caching
├── naturalness_check.py       # LLM-based naturalness scoring
├── template_parser.py         # Template YAML parsing
└── checks/                    # 34 individual check modules
    ├── activities.py           # Activity validation (types, schemas, complexity)
    ├── morphological_validator.py  # VESUM grammar checking
    ├── yaml_schema_validation.py   # YAML schema enforcement
    ├── review_validation.py    # LLM review integrity
    ├── template_compliance.py  # Template structure compliance
    ├── content_quality_pipeline.py # Content quality scoring
    ├── cross_file_integrity.py # Plan↔content↔vocab consistency
    ├── vocabulary.py           # Vocabulary gate checks
    ├── review_gaming.py        # Anti-gaming (ping-pong, content recall)
    └── ... (24 more)
```

**Key gates**: Words ≥ target, activities ≥ minimum, unique types, engagement boxes, vocab count, naturalness ≥ 8/10.

### 3. RAG System (`scripts/rag/` + `.mcp/servers/rag/`)
**~8K LOC** | MCP server at `.mcp/servers/rag/server.py`

Data sources indexed in Qdrant (local vector DB) + live HTTP queries.

| Source | Type | Collection | MCP Tool |
|--------|------|------------|----------|
| Textbooks (1.2K chunks) | RAG | `textbook_chunks` | `search_text` |
| Literary sources | RAG | `literary_texts` | `search_literary` |
| VESUM (415K lemmas) | SQLite | `data/vesum/` | `verify_word`, `verify_lemma` |
| Ukrainian Wikipedia | Live | — | `query_wikipedia` |
| GRAC corpus (2B tokens) | Live | — | `query_grac` |
| ULIF paradigms | Live | — | `query_ulif` |
| r2u dictionary | Live | — | `query_r2u` |
| Pravopys 2019 | Reference | — | `query_pravopys` |

Ingestion pipeline:
- `ingest.py` / `ingest_literary.py` — Chunk and embed textbook/literary content
- `embed.py` — Embedding generation (cached with pickle)
- `import_vesum.py` — VESUM dictionary import to SQLite
- `scrape_*.py` — Web scrapers (litopys, ukrlib, wikisource, izbornyk)
- `extract_text.py` / `extract_images.py` — PDF content extraction

### 4. API Server (`scripts/api/`)
**~6K LOC** | FastAPI + WebSocket

Dashboard and monitoring for pipeline operations.

```
scripts/api/
├── main.py              # FastAPI app, WebSocket, shared endpoints
├── dashboard_router.py  # Module listing, track scanning, detail views
├── state_router.py      # Pipeline state management (unified v5 format)
├── blue_router.py       # Claude team endpoints
├── gold_router.py       # Gemini team endpoints
├── admin_router.py      # Admin operations
├── comms_router.py      # Notifications
├── rag_router.py        # RAG search integration
├── images_router.py     # Image serving
└── config.py            # API configuration
```

### 5. Scoring System (`scripts/scoring/`)
**~3.5K LOC**

Module quality scoring with weighted criteria aggregation.

- `aggregator.py` — Score aggregation (CC=105, needs decomposition)
- `metrics.py` — Metric definitions
- `caps.py` — Score caps and constraints
- `report.py` — Score reporting
- `sampling.py` — Statistical sampling
- Also: `scripts/calculate_richness.py` — Content richness scoring (dryness flags, module type detection)

### 6. Code Generation (`scripts/generate_*.py`)
**~6.5K LOC**

- `generate_mdx.py` — Markdown → Docusaurus MDX (main track)
- `generate_mdx_direct.py` — MDX for l2-uk-direct track
- `generate_json.py` — Module → JSON for Vibe app
- `generate_plan_markdown.py` — Plan YAML → human-readable markdown

### 7. Batch Operations (`scripts/batch_*.py`)
**~6K LOC**

- `batch_gemini_runner.py` — Dispatches Gemini builds across modules
- `batch_dispatcher.py` — Job orchestration
- `batch_gemini_config.py` — Model defaults per track/level
- `batch_fix_review.py` — Batch review fixing
- `batch_research.py` — Batch research phase
- `batch_report.py` — Batch status reporting

### 8. Agent Bridge (`scripts/ai_agent_bridge.py`)
**~2K LOC**

Inter-agent communication (Claude ↔ Gemini). Uses gemini-cli subprocess.

### 9. RAG Ingestion (`scripts/rag/scrape_*.py`, `ingest_*.py`)
**~4.8K LOC**

Web scrapers and data ingestors for populating RAG collections.

### 10. Prompt Templates (`claude_extensions/phases/` + `gemini_extensions/skills/`)
**~8.7K LOC** (54 prompt/template files)

Phase-specific prompts injected into LLM calls during pipeline execution.

### 11. Playgrounds (`scripts/api/` static files + dashboards)
**~4.8K LOC**

Interactive HTML dashboards for exploring pipeline data.

## AI Agent Architecture

```
┌─────────────────────┐     ┌─────────────────────┐
│   Claude (Blue)     │     │   Gemini (Gold)      │
│   - Architect       │◄───►│   - Content builder  │
│   - Reviewer        │     │   - Researcher       │
│   - Code author     │     │   - Activity creator  │
└─────────────────────┘     └─────────────────────┘
         │                           │
         ▼                           ▼
┌─────────────────────┐     ┌─────────────────────┐
│ claude_extensions/   │     │ gemini_extensions/   │
│ ├── commands/        │     │ └── skills/          │
│ ├── skills/          │     │     ├── full-rebuild-*│
│ ├── phases/          │     │     ├── hetman/       │
│ ├── quick-ref/       │     │     └── final-review/ │
│ └── rules/           │     └─────────────────────┘
└─────────────────────┘
```

**Rule**: An LLM must NEVER review its own work. Gemini builds → Claude reviews.

**Extensions source of truth**:
- `claude_extensions/` → deployed to `.claude/` via `npm run claude:deploy`
- `gemini_extensions/` → deployed to `.gemini/` (manual copy)

## MCP Servers

| Server | Location | Purpose |
|--------|----------|---------|
| **RAG** | `.mcp/servers/rag/server.py` | Textbook search, VESUM verification, literary sources, live queries |
| **Message Broker** | `.mcp/servers/message-broker/server.py` | Inter-agent message queue |

## Curriculum Tracks

### Main Track: `l2-uk-en` (Ukrainian for English speakers)

| Level | Modules | Status |
|-------|---------|--------|
| A1 | 63 | Complete |
| A2 | 67 | Complete |
| B1 | 92 | Complete |
| B2 | 59 | Complete |
| C1 | 1 | Early draft |
| C2 | 0 | Not started |

### Seminar Tracks

| Track | Modules | Description |
|-------|---------|-------------|
| HIST | 140 | Ukrainian history |
| BIO | 76 | Famous Ukrainians |
| ISTORIO | 3 | Historiography |
| LIT | 0 | Literature |
| OES | 0 | Old East Slavic |
| RUTH | 0 | Ruthenian |

### Secondary Track: `l2-uk-direct`

L1-agnostic Ukrainian (A1→B2). Separate schemas, no English. See `docs/l2-uk-direct/ARCHITECTURE.md`.

## Schemas (`schemas/`)

- Activity schemas: base + per-level variants (A1–C2 + seminar tracks)
- Module schemas: plan, status, meta
- Vocabulary schemas: standard + direct track
- Vibe integration: `vibe-module.schema.json`

## Quality Systems

| System | Type | Gates? | Entry Point |
|--------|------|--------|-------------|
| **Audit** | Deterministic | Yes (blocking) | `scripts/audit_module.py` |
| **Morphological Validator** | VESUM-based | Yes (blocking) | `scripts/audit/checks/morphological_validator.py` |
| **Lexical Sandbox** | VESUM-based | Non-blocking | `scripts/lexical_sandbox.py` |
| **Russicism Detection** | Rule-based | Yes (blocking) | Part of validate phase |
| **Content Quality** | LLM-based | No (informational) | `scripts/audit/checks/content_quality_pipeline.py` |
| **Naturalness** | LLM-based | Yes (≥8/10) | `scripts/audit/naturalness_check.py` |

## Key Design Decisions

1. **Pipeline v5 is the ONLY pipeline** — v3/v4 retired, code in `scripts/retired/`
2. **VESUM is ground truth** — 415K lemmas, ~6M forms. All Ukrainian words verified against it
3. **Plans are immutable** — Content changes require plan version bump + human approval
4. **Deterministic where possible** — Sandbox, MDX gen, fixes are LLM-free
5. **Cross-agent review** — Gemini never reviews its own output
6. **34 audit gates** — All must pass for a module to be considered complete
7. **Word targets are minimums** — Never reduce targets, expand content

## File Structure

```
learn-ukrainian/
├── curriculum/l2-uk-en/           # Content (plans + build artifacts + status)
│   ├── plans/{level}/{slug}.yaml  # Immutable plans
│   ├── {level}/{slug}.md          # Lesson prose
│   ├── {level}/activities/        # Activity YAML
│   ├── {level}/vocabulary/        # Vocabulary YAML
│   ├── {level}/meta/              # Build metadata
│   └── {level}/status/            # Audit cache
├── scripts/                       # All Python code (~143K LOC)
│   ├── build_module_v5.py         # Pipeline v5 CLI
│   ├── pipeline_v5.py             # Pipeline v5 implementation
│   ├── pipeline/                  # Pipeline support modules
│   ├── audit/                     # Audit system (34 checks)
│   ├── rag/                       # RAG indexing + querying
│   ├── api/                       # FastAPI dashboard server
│   ├── scoring/                   # Quality scoring
│   ├── batch_*.py                 # Batch operations
│   ├── generate_*.py              # Code generation (MDX, JSON, plan markdown)
│   └── ai_agent_bridge.py         # Inter-agent communication
├── claude_extensions/             # Claude Code config (source of truth)
├── gemini_extensions/             # Gemini config (source of truth)
├── .mcp/servers/                  # MCP servers (RAG, message broker)
├── schemas/                       # JSON schemas (25 files)
├── docs/                          # Documentation
│   ├── best-practices/            # Standards and guides
│   ├── l2-uk-en/templates/        # 37 module templates
│   └── resources/                 # Trusted sources, external resources
└── docusaurus/                    # Web output (Docusaurus + React components)
```

## Related Documentation

| Topic | Location |
|-------|----------|
| Pipeline commands | `docs/SCRIPTS.md` |
| Track architecture | `docs/best-practices/track-architecture.md` |
| Audit standards | `docs/best-practices/audit-standards.md` |
| Module quality | `docs/best-practices/module-content-quality.md` |
| Agent cooperation | `docs/best-practices/agent-cooperation.md` |
| Markdown format | `docs/MARKDOWN-FORMAT.md` |
| Activity YAML | `docs/ACTIVITY-YAML-REFERENCE.md` |
| Monitoring API | `docs/MONITOR-API.md` |
| Trusted sources | `docs/resources/trusted_sources.yaml` |
