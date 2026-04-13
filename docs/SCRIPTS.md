# Scripts & Workflow Reference

Current operational reference for repo-local scripts and agent workflows.

- Main build entry point: `.venv/bin/python scripts/build/v6_build.py {level} {num}`
- Validation pipeline after content exists: `npm run audit`, `npm run pipeline`, `npm run generate:json`
- This document intentionally omits retired pipelines and legacy script paths

---

## Startup Wrappers

Project-local wrappers for interactive agent sessions:

```bash
./start-claude.sh
./start-codex.sh
```

`start-codex.sh` launches Codex with:

- interactive Codex in dangerous bypass mode
- `CODEX_SESSION=1` so repo scripts can detect an interactive Codex session
- repo subprocess defaults unchanged unless you explicitly override env vars

Override before launch if needed:

```bash
CODEX_DISPATCH_MODE=workspace-write CODEX_BRIDGE_MODE=safe ./start-codex.sh
```

---

## Claude Code Hooks

Session hooks live in `claude_extensions/hooks/` and deploy to `.claude/hooks/`.

### `session-setup.sh`

Runs on every session start, new or resumed.

| # | Check | Severity | Details |
|---|---|---|---|
| 1 | Python venv | ISSUE | `.venv/bin/python` exists and is 3.12.x |
| 2 | Env vars | ISSUE | `CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS` is set |
| 3 | Message broker | INFO | SQLite DB for agent communication exists |
| 4 | Build state hygiene | INFO | Reports stale or active build state files |
| 5 | Memory budget | ISSUE/INFO | `MEMORY.md` line count vs project limits |
| 6 | Deploy drift | ISSUE | Diffs `claude_extensions/` vs `.claude/` |
| 7 | MCP sources health | ISSUE | Pings `127.0.0.1:8766` |
| 8 | `gemini` CLI | INFO | Verifies command exists and auth works |
| 9 | Open GitHub issues | INFO | Lists a small set of open issues |

### `enforce-venv.sh`

Intercepts bare `python` and `python3` shell calls and rewrites them to `.venv/bin/python`.

### `check-gemini-inbox.sh`

Polls the SQLite message broker for unread Gemini messages and surfaces them as additional context. It skips during pipeline runs.

---

## Token Usage Analytics

Analyze Claude Code token consumption across learn-ukrainian and kubedojo projects.

```bash
# All time
.venv/bin/python scripts/token_usage.py

# Last 7 days
SINCE_DAYS=7 .venv/bin/python scripts/token_usage.py

# Since specific date
SINCE_DATE=2026-04-03 .venv/bin/python scripts/token_usage.py
```

Parses `~/.claude/projects/` JSONL session files and writes `docs/token-usage/token_report.md` with totals, daily breakdown, costliest sessions, model mix, and subagent analysis.

---

## Wiki Knowledge Base

The wiki is the research layer: compiled reference articles consumed as inline context during module generation. Source retrieval is pre-baked into SQLite, so module generation does not depend on live external search.

### Architecture

```text
Plan YAML -> Discovery -> Sources DB (SQLite FTS5) -> Gemini compilation -> Wiki article (.md)
                         ^
                         +-- textbooks
                         +-- literary texts
                         +-- external articles
                         +-- Wikipedia
                         +-- dictionaries
```

All sources live in `data/sources.db`. No vector DB is involved here.

### Build Sources Database

```bash
.venv/bin/python scripts/wiki/build_sources_db.py
```

Rebuilds the unified SQLite database from textbook, literary, external, Wikipedia, and dictionary inputs.

### Fetch Wikipedia Articles

```bash
.venv/bin/python scripts/wiki/fetch_wikipedia.py --track folk
.venv/bin/python scripts/wiki/fetch_wikipedia.py --track hist
.venv/bin/python scripts/wiki/fetch_wikipedia.py --all
.venv/bin/python scripts/wiki/fetch_wikipedia.py --status
```

### Compile Wiki Articles

```bash
# Status and discovery
.venv/bin/python scripts/wiki/compile.py --status
.venv/bin/python scripts/wiki/compile.py --track a2 --list

# Single article
.venv/bin/python scripts/wiki/compile.py --track a2 --slug genitive-intro --dry-run
.venv/bin/python scripts/wiki/compile.py --track a2 --slug genitive-intro
.venv/bin/python scripts/wiki/compile.py --track a2 --slug genitive-intro --review

# Batch
.venv/bin/python scripts/wiki/compile.py --track a2 --all
.venv/bin/python scripts/wiki/compile.py --track a2 --all --review
.venv/bin/python scripts/wiki/compile.py --track a2 --all --limit 5 --review

# Maintenance
.venv/bin/python scripts/wiki/compile.py --track a2 --slug genitive-intro --force
.venv/bin/python scripts/wiki/compile.py --track folk --review-only
.venv/bin/python scripts/wiki/compile.py --update-index
```

Supported tracks: `a1`, `a2`, `b1`, `b2`, `c1`, `c2`, `folk`, `hist`, `bio`, `istorio`, `lit`, `lit-essay`, `lit-war`, `lit-hist-fic`, `lit-youth`, `lit-fantastika`, `lit-humor`, `lit-drama`, `oes`, `ruth`.

Track prompt families:

- `a1`: pedagogy briefs
- `a2-b2`: grammar briefs
- `c1-c2`: academic briefs
- seminar tracks: knowledge articles

### Quality Gate

```bash
.venv/bin/python scripts/wiki/quality_gate.py
.venv/bin/python scripts/wiki/quality_gate.py --track a2
.venv/bin/python scripts/wiki/quality_gate.py --fix
```

Checks short articles, leaked reasoning, fence wrapping, missing headings, and truncation.

### Fetch External Sources

```bash
.venv/bin/python scripts/wiki/fetch_external_sources.py --ulp-blogs
.venv/bin/python scripts/wiki/fetch_external_sources.py --all
.venv/bin/python scripts/wiki/fetch_external_sources.py --build-db
.venv/bin/python scripts/wiki/fetch_external_sources.py --status
```

### Services

```bash
./services.sh start
./services.sh start rag
./services.sh stop rag
./services.sh restart
./services.sh status
```

### Key Files

| File | Purpose |
|---|---|
| `scripts/wiki/compile.py` | Wiki compiler CLI |
| `scripts/wiki/compiler.py` | Compilation logic |
| `scripts/wiki/enrichment.py` | Source enrichment pipeline |
| `scripts/wiki/sources_db.py` | SQLite query layer |
| `scripts/wiki/build_sources_db.py` | Database builder |
| `scripts/wiki/fetch_wikipedia.py` | Wikipedia batch fetcher |
| `scripts/wiki/fetch_external_sources.py` | External source fetcher |
| `scripts/wiki/quality_gate.py` | Post-compile quality checker |
| `scripts/wiki/state.py` | Progress tracking |
| `.mcp/servers/sources/server.py` | MCP sources server |
| `.mcp.json` | MCP configuration |
| `data/sources.db` | Unified SQLite database |

---

## Related Documentation

| Document | Purpose |
|---|---|
| `.claude/rules/workflow.md` | Core workflow rules for agent sessions |
| `.claude/rules/pipeline.md` | Build and validation workflow guidance |
| `.claude/rules/rag-and-dictionaries.md` | MCP sources and dictionary lookup rules |
| `.claude/rules/ukrainian-linguistics.md` | Ukrainian language quality rules |
| `.claude/phases/gemini/README.md` | Gemini phase map |
| `.claude/phases/gemini/v6-write.md` | Current write phase reference |
| `.claude/phases/gemini/v6-review.md` | Current review phase reference |
| `.claude/quick-ref/ACTIVITY-SCHEMAS.md` | Activity schema quick reference |
| `docs/agent-runtime-guide.md` | Agent runtime architecture |
| `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` | Module richness requirements |
| `claude_extensions/consultation-queue/README.md` | Consultation queue format |

## Tool Inventory (Quick Reference)

### MCP sources tools

Full list: [`.claude/rules/rag-and-dictionaries.md`](../.claude/rules/rag-and-dictionaries.md). Core tools used daily:

- `mcp__rag__verify_word` - VESUM morphological check
- `mcp__rag__search_text` - textbook content search
- `mcp__rag__search_definitions` - SUM-11 explanatory dictionary
- `mcp__rag__search_style_guide` - Antonenko-Davydovych style guidance

### Deterministic audit checks

At `scripts/audit/checks/`:

- `cross_file_integrity.py` - vocabulary used in activities exists in vocabulary YAML
- `outline_compliance.py` - markdown section structure matches `meta.yaml` outline
- `activity_quality.py` - deterministic activity quality checks

### Build pipeline entry point

`.venv/bin/python scripts/build/v6_build.py {level} {num}` is the single end-to-end build entry point. It drives the write -> enrich -> review -> audit -> publish chain.

### Agent runtime

`scripts/agent_runtime/` is the universal adapter layer for Claude, Gemini, and Codex CLI invocations. See [`docs/agent-runtime-guide.md`](agent-runtime-guide.md).

### Delegate to background workers

```bash
.venv/bin/python scripts/delegate.py dispatch --agent {codex|gemini|claude} --task-id <id> --prompt-file <file>
```

Fire-and-forget execution with status polling and completion artifacts.

---

## Build & Validation Workflow

Use two entry points depending on the job:

| Need | Entry point |
|---|---|
| Full module build | `.venv/bin/python scripts/build/v6_build.py {level} {num}` |
| Validate existing content | `npm run audit`, `npm run pipeline`, `npm run generate:json` |

### `scripts/build/v6_build.py`

Single end-to-end build entry point.

```bash
# Single module
.venv/bin/python scripts/build/v6_build.py a1 5

# Range
.venv/bin/python scripts/build/v6_build.py a1 7 --range 14

# Resume from prior state
.venv/bin/python scripts/build/v6_build.py hist 12 --resume

# Run a specific step only
.venv/bin/python scripts/build/v6_build.py b1 9 --step review
```

Useful flags:

- `--writer` and `--reviewer` choose agent family
- `--step` runs a targeted phase
- `--resume` reuses saved progress
- `--no-skeleton` and `--no-chunk` alter generation behavior

#### Build monitoring with Claude Code `Monitor` tool

v6_build.py emits JSONL events on stdout (`module_start`, `phase_done`, `review_score`, `module_done`, `module_failed`, `batch_done`). Use the Claude Code `Monitor` tool to stream these as notifications:

```
Monitor(
    command=".venv/bin/python -u scripts/build/v6_build.py a1 1 --range 55 --resume 2>&1 | grep --line-buffered '^{\"event\"'",
    description="A1 build events",
    persistent=True,
    timeout_ms=3600000
)
```

For state queries without builds, use the Monitor API (`docs/MONITOR-API.md`):
```bash
curl -s http://localhost:8765/api/state/track-health/a1   # Full track health
curl -s http://localhost:8765/api/state/failing?track=a2   # Failing modules
curl -s http://localhost:8765/api/state/build-status        # All tracks build progress
```

### Validation flow for existing modules

```bash
# Audit level, module, or range
npm run audit -- b1
npm run audit -- b1 5
npm run audit -- b1 1-10

# Audit single file with saved log
scripts/audit_module.sh curriculum/l2-uk-en/a1/05-my-world-objects.md

# Full validation pipeline
npm run pipeline l2-uk-en a1 5

# Generate app JSON
npm run generate:json l2-uk-en a1 5
```

`pipeline.py` is the technical validation pipeline. It is not the same thing as the end-to-end build orchestrator in `scripts/build/v6_build.py`.

---

## Plans, Status, and Manifest

### Status generation

```bash
.venv/bin/python scripts/generate_level_status.py a1
npm run status:a1
npm run status:all
```

Generates human-readable status reports from cached per-module audit results.

### Manifest utilities

```bash
.venv/bin/python scripts/manifest_utils.py validate
.venv/bin/python scripts/manifest_utils.py validate-fs
.venv/bin/python scripts/manifest_utils.py validate-fs hist
.venv/bin/python scripts/manifest_utils.py stats
.venv/bin/python scripts/manifest_utils.py lookup trypillian-civilization
.venv/bin/python scripts/manifest_utils.py level hist
```

`curriculum.yaml` is the source of truth for ordering and slug lookup.

### Plan validation

```bash
.venv/bin/python scripts/validate_plan_config.py b1
.venv/bin/python scripts/validate_plan_config.py hist
```

Use this before content generation to verify plan files still match `scripts/audit/config.py` constraints.

### Migrations and readable plan output

```bash
.venv/bin/python scripts/migrate/migrate_to_v2.py b1
.venv/bin/python scripts/generate_mdx/generate_plan_markdown.py hist
.venv/bin/python scripts/generate_mdx/generate_plan_markdown.py --all
```

---

## Scripts Quick Reference

| Script | Purpose | Command |
|---|---|---|
| `scripts/build/v6_build.py` | End-to-end module build | `.venv/bin/python scripts/build/v6_build.py a1 5` |
| `scripts/audit_level.py` | Audit a level, module, or range | `npm run audit -- b1 1-10` |
| `scripts/audit_module.py` | Audit a single module file | `.venv/bin/python scripts/audit_module.py <file>` |
| `scripts/pipeline.py` | Technical validation pipeline | `npm run pipeline l2-uk-en a1 5` |
| `scripts/generate_mdx.py` | Generate Starlight MDX | `npm run generate l2-uk-en a1 5` |
| `scripts/generate_json.py` | Generate app JSON | `npm run generate:json l2-uk-en a1 5` |
| `scripts/validate_mdx.py` | Validate MDX integrity | `npm run validate:mdx l2-uk-en a1 5` |
| `scripts/validate_html.py` | Validate rendered HTML | `npm run validate:html l2-uk-en a1 5` |
| `scripts/generate_level_status.py` | Build status reports | `npm run status:b1` |
| `scripts/manifest_utils.py` | Manifest validation and lookup | `.venv/bin/python scripts/manifest_utils.py validate` |
| `scripts/validate_plan_config.py` | Validate plan config alignment | `.venv/bin/python scripts/validate_plan_config.py b1` |
| `scripts/sync_landing_pages.py` | Update landing pages | `npm run sync:landing` |
| `scripts/vocab/auto_vocab_extract.py` | Create vocabulary skeletons | `.venv/bin/python scripts/vocab/auto_vocab_extract.py <module.md>` |
| `scripts/vocab/vocab_enrich_nlp.py` | Enrich vocabulary YAML | `.venv/bin/python scripts/vocab/vocab_enrich_nlp.py <vocab.yaml>` |
| `scripts/vocab_init.py` | Initialize vocabulary DB | `npm run vocab:init` |
| `scripts/populate_vocab_db.py` | Scan modules into vocabulary DB | `npm run vocab:scan` |
| `scripts/assess_research.py` | Assess and upgrade research | `.venv/bin/python scripts/assess_research.py hist --upgrade` |
| `scripts/consultation_cli.py` | Review consultation proposals | `.venv/bin/python scripts/consultation_cli.py list` |
| `scripts/check_decisions.py` | Audit decision journal expiry | `.venv/bin/python scripts/check_decisions.py` |

---

## Core Scripts

### `audit_level.py`

Level-oriented wrapper around module auditing.

```bash
npm run audit -- b1
npm run audit -- b1 5
npm run audit -- b1 1-10
npm run audit -- b1 1,3,5,7
npm run audit -- b1 --fix
npm run audit -- b1 5 --verbose
```

Use this when you want one command for level, module, range, or mixed selections.

### `audit_module.sh`

Recommended wrapper around `audit_module.py`.

```bash
scripts/audit_module.sh curriculum/l2-uk-en/b1/09-aspect-future.md
```

It runs the audit and saves the log to `curriculum/l2-uk-en/{level}/audit/{slug}-audit.log`.

### `audit_module.py`

Comprehensive module checker.

```bash
.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/b1/06-*.md
```

It checks:

- frontmatter and required sections
- activity count and diversity
- vocabulary format
- grammar and level constraints
- Ukrainian quality
- activity hints vs actual activities
- integrated audit checks such as cross-file integrity and outline compliance

### `pipeline.py`

Technical validation pipeline for already-written content.

```bash
npm run pipeline l2-uk-en a1
npm run pipeline l2-uk-en a1 5
```

Stages:

1. lint
2. MDX generation
3. MDX validation
4. HTML validation

Requires `npm run dev:starlight` for HTML validation.

### `generate_mdx.py`

Generates MDX for Starlight:

```bash
npm run generate l2-uk-en
npm run generate l2-uk-en a1
npm run generate l2-uk-en a1 5
```

### `generate_json.py`

Generates JSON for the app:

```bash
npm run generate:json l2-uk-en
npm run generate:json l2-uk-en a1
npm run generate:json l2-uk-en a1 5
```

### `validate_mdx.py`

Checks MDX conversion integrity:

- activity types preserved
- vocabulary content preserved
- Ukrainian text preserved
- no silent content loss during conversion

```bash
npm run validate:mdx l2-uk-en a1
npm run validate:mdx l2-uk-en a1 5
```

### `validate_html.py`

Checks rendered HTML with a headless browser:

- page loads without HTTP errors
- interactive components render
- serious JS console errors are absent
- Ukrainian text is present

```bash
npm run validate:html l2-uk-en a1
npm run validate:html l2-uk-en a1 5
```

If the Starlight dev server is not running, this step skips gracefully.

### `sync_landing_pages.py`

Updates landing pages with current curriculum counts and status:

```bash
npm run sync:landing
npm run sync:landing:dry
```

Targets:

- `starlight/src/content/docs/intro.mdx`
- `starlight/src/content/docs/{level}/index.mdx`

### `manifest_utils.py`

Manifest inspection and validation CLI for `curriculum.yaml`.

Use it to validate filesystem alignment, get stats, and resolve modules by slug.

### `validate_plan_config.py`

Checks plan files against current config constraints. Run it before generation, especially when plans or global audit config changed.

---

## Vocabulary Pipeline

Vocabulary uses SQLite in `curriculum/l2-uk-en/vocabulary.db` plus per-module YAML files.

### Workflow order

```text
1. scripts/vocab/auto_vocab_extract.py
2. scripts/vocab/vocab_enrich_nlp.py
3. scripts/audit/checks/cross_file_integrity.py
4. scripts/audit/checks/outline_compliance.py
5. scripts/vocab_init.py
6. scripts/populate_vocab_db.py
```

### `scripts/vocab/auto_vocab_extract.py`

Creates skeleton vocabulary entries from module markdown.

```bash
.venv/bin/python scripts/vocab/auto_vocab_extract.py curriculum/l2-uk-en/hist/volodymyr-monomakh.md
.venv/bin/python scripts/vocab/auto_vocab_extract.py curriculum/l2-uk-en/hist/volodymyr-monomakh.md --dry-run
```

### `scripts/vocab/vocab_enrich_nlp.py`

Enriches vocabulary YAML with IPA, POS, and morphology-derived data.

```bash
.venv/bin/python scripts/vocab/vocab_enrich_nlp.py curriculum/l2-uk-en/hist/vocabulary/trypillian-civilization.yaml
.venv/bin/python scripts/vocab/vocab_enrich_nlp.py curriculum/l2-uk-en/hist/vocabulary/trypillian-civilization.yaml --dry-run
```

### `scripts/audit/checks/cross_file_integrity.py`

Runs inside `audit_module.py` and checks that activity vocabulary exists in cumulative vocabulary YAML.

### `scripts/audit/checks/outline_compliance.py`

Runs inside `audit_module.py` and checks that markdown structure follows `meta.yaml` outline targets.

### `scripts/vocab_init.py`

```bash
npm run vocab:init
npm run vocab:init:force
.venv/bin/python scripts/vocab_init.py l2-uk-en --force
```

### `scripts/populate_vocab_db.py`

```bash
npm run vocab:scan
.venv/bin/python scripts/populate_vocab_db.py
```

---

## Activity Quality Validation

Optional activity quality validation:
- `scripts/audit/generate_activity_quality_queue.py` creates the queue.
- `scripts/audit/finalize_activity_quality.py` creates the report.
- See `tests/test_activity_quality.py`.

---

## Research Quality Assessment

### `assess_research.py`

Research assessment and upgrade pipeline.

```bash
# Assess
.venv/bin/python scripts/assess_research.py a1
.venv/bin/python scripts/assess_research.py a1 5
.venv/bin/python scripts/assess_research.py a1 --gaps
.venv/bin/python scripts/assess_research.py --all

# Upgrade and downstream actions
.venv/bin/python scripts/assess_research.py a1 --upgrade
.venv/bin/python scripts/assess_research.py a1 --upgrade --dry-run
.venv/bin/python scripts/assess_research.py a1 --enrich
.venv/bin/python scripts/assess_research.py a1 --refresh

# Coverage
.venv/bin/python scripts/assess_research.py a1 --coverage
.venv/bin/python scripts/assess_research.py --all --coverage
.venv/bin/python scripts/assess_research.py c1 --coverage --strict
.venv/bin/python scripts/assess_research.py c1 --coverage --json
```

Use `--upgrade` to regenerate weak research, `--enrich` to push strong research into plans, and `--refresh` to rebuild content that depends on upgraded research.

---

## Consultation Approval Workflow

The consultation loop proposes prompt or template changes for human review.

### `scripts/consultation_cli.py`

```bash
.venv/bin/python scripts/consultation_cli.py list
.venv/bin/python scripts/consultation_cli.py show FILENAME.yaml
.venv/bin/python scripts/consultation_cli.py approve FILENAME.yaml
.venv/bin/python scripts/consultation_cli.py approve FILENAME.yaml --dry-run
.venv/bin/python scripts/consultation_cli.py reject FILENAME.yaml --reason "Superseded by newer proposal"
.venv/bin/python scripts/consultation_cli.py approve-all --confidence high
.venv/bin/python scripts/consultation_cli.py approve-all --confidence high --dry-run
```

Queue locations:

| Path | Purpose |
|---|---|
| `claude_extensions/consultation-queue/*.yaml` | Pending proposals |
| `claude_extensions/consultation-queue/applied/` | Approved proposals |
| `claude_extensions/consultation-queue/rejected/` | Rejected proposals |

---

## Decision Tracking

### `check_decisions.py`

Scans `docs/decisions/decisions.yaml` for expired or near-expiry decisions.

```bash
.venv/bin/python scripts/check_decisions.py
.venv/bin/python scripts/check_decisions.py --quiet
.venv/bin/python scripts/check_decisions.py --create-issues
```

This is also called by `session-setup.sh`.

---

## Playgrounds

| Entry | Purpose |
|---|---|
| `scripts/generate_playground_data.py` | Aggregate audit cache into playground data |
| `scripts/build_playgrounds.py` | Build HTML playgrounds with embedded data |
| `npm run playgrounds:data` | Regenerate `playgrounds/data/status.json` |
| `npm run playgrounds:build` | Rebuild playground HTML |

---

## Inter-Agent Communication

SQLite-backed message broker and CLI bridge for Claude, Gemini, and Codex.

### Bridge CLI

All bridge commands route through the runtime at `scripts/agent_runtime/`.

```bash
# Inbox and reads
.venv/bin/python scripts/ai_agent_bridge/__main__.py inbox
.venv/bin/python scripts/ai_agent_bridge/__main__.py inbox --for codex
.venv/bin/python scripts/ai_agent_bridge/__main__.py read <message_id>
.venv/bin/python scripts/ai_agent_bridge/__main__.py conversation <task_id>

# Send and process
.venv/bin/python scripts/ai_agent_bridge/__main__.py send "Your message" --type query --task-id my-task
.venv/bin/python scripts/ai_agent_bridge/__main__.py process <message_id> --model gemini-3-pro-preview
.venv/bin/python scripts/ai_agent_bridge/__main__.py interactive

# Dispatch with full execution access
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-gemini \
  "Activate skill final-review. ..." \
  --task-id fr-{slug} \
  --allow-write \
  --delimiters FINAL_REVIEW,FRICTION \
  --model gemini-3-pro-preview

# Quick Codex question
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-codex \
  "Review posted on #1177. Please read and respond." \
  --task-id issue-1177

# Recent Codex bridge/dispatch/delegate usage summary
.venv/bin/python scripts/ai_agent_bridge/__main__.py codex-usage --window 5h
.venv/bin/python scripts/ai_agent_bridge/__main__.py codex-usage --window 24h --entrypoint bridge --json

# Threaded Gemini conversation
.venv/bin/python scripts/ai_agent_bridge/__main__.py converse \
  "Let's plan the A1/1 build" \
  --task-id a1-1-planning \
  --model gemini-3.1-pro-preview
```

`codex-usage` reads recent `batch_state/api_usage/usage_codex-*.jsonl` records,
groups them by outcome and entrypoint, lists recent rate-limit events, and
reports whether `gpt-5.4` currently has bridge headroom.

### Codex sandbox control

```bash
export CODEX_CLI_MODE=danger
export CODEX_BRIDGE_MODE=safe
export CODEX_DISPATCH_MODE=workspace-write
```

Defaults:

- `ai_agent_bridge` Codex calls default to `safe`
- `dispatch.py` defaults to `safe` for `codex` and `workspace-write` for `codex-tools`
- `danger` maps to bypass mode

### Helper tools

```bash
.venv/bin/python scripts/tools/signal_claude.py "Your message here"
.venv/bin/python scripts/tools/message_viewer.py
```

`message_viewer.py` serves the archive viewer on `http://localhost:5055`.

### Message types

| Type | Purpose |
|---|---|
| `query` | Ask another agent a question |
| `response` | Return an answer |
| `request` | Request work |
| `handoff` | Transfer a task with context |
| `context` | Share state or findings |
| `feedback` | Review or comment |

---

## Common Workflows

| Workflow | Command |
|---|---|
| Build one module | `/module {level} {num}` |
| Full seminar rebuild | `/full-rebuild {track} {slug}` |
| Full core rebuild | `/full-rebuild-core {level} {num}` |
| Full v6 build via script | `.venv/bin/python scripts/build/v6_build.py {level} {num}` |
| Audit a module or range | `npm run audit -- {level} {num|range}` |
| Run technical validation | `npm run pipeline l2-uk-en {level} {num}` |
| Generate app JSON | `npm run generate:json l2-uk-en {level} {num}` |
| Sync landing pages | `npm run sync:landing` |
| Compile one wiki article | `.venv/bin/python scripts/wiki/compile.py --track {track} --slug {slug}` |
| Compile a wiki track with review | `.venv/bin/python scripts/wiki/compile.py --track {track} --all --review` |
