# Scripts & Workflow Reference

Current operational reference for repo-local scripts and agent workflows.

- Main build entry point: `.venv/bin/python scripts/build/v7_build.py {level} {slug} --worktree`
- Validation pipeline after content exists: `npm run audit`, `npm run pipeline`, `npm run generate:json`
- This document intentionally omits retired pipelines and legacy script paths

Before guessing CLI flags, run the tool's `--help`. The repo standard lives in
`claude_extensions/rules/cli-help-standard.md`, and touched CLIs are expected to
meet it so agents can use them without source-diving.

---

## Startup Wrappers

Project-local wrappers for interactive agent sessions:

```bash
./start-claude.sh      # native Anthropic Claude Code (original config)
./start-claudex.sh     # Claude Code UI → GPT-5.6 Sol via CLIProxyAPI (interactive)
./start-kimicc.sh      # Claude Code UI → Kimi K3 / K2.7 (interactive)
./start-codex.sh       # native Codex
./start-grok.sh        # native Grok Build TUI
```

Native Kimi Code (separate app/CLI, OAuth subscription) is the **headless / fleet**
lane via `scripts/delegate.py --agent kimi` and `ab ask-kimi`. Interactive native
Kimi is `kimi` from `~/.kimi-code/bin` (or a dedicated `start-kimi.sh` when that
wrapper is present) — not `start-kimicc.sh`.

### Parallel routes and original Claude config

`start-claudex.sh` and `start-kimicc.sh` route through process-scoped
configuration (Moonshot Method 1 / CLIProxyAPI pattern). They **never rewrite**
`~/.claude/settings.json`; Claudex additionally passes a checked-in status-line
overlay with `--settings`. That means:

- `./start-claude.sh` always keeps the original Anthropic / Claude Code setup
- You can run native Claude and KimiCC (or Claudex) in **parallel terminals**
- Tools like [cc-switch](https://github.com/farion1231/cc-switch) that pin
  `ANTHROPIC_*` into `settings.json env` will **block** these launchers until
  those keys are removed (or you use `--isolate-config` / `CLAUDE_CONFIG_DIR`)

### Claudex (GPT-5.6 interactive)

`start-claudex.sh` keeps Claude Code's interface while routing the lead model
to GPT-5.6 Sol through a local CLIProxyAPI server. **Interactive only** —
headless GPT work stays on `./start-codex.sh` / bridge. Compaction is certified
by the `sol_lead` profile: **272k window, 258.4k auto-compact**. The launcher
passes both values to Claude Code so an unrecognized gateway model does not
fall back to Claude Code's default assumed window.

Subagents default to Terra; select another tier without changing the Sol lead:

```bash
./start-claudex.sh
./start-claudex.sh --subagent terra
./start-claudex.sh --subagent luna --epic harness
CLAUDEX_SUBAGENT=terra ./start-claudex.sh
```

On macOS, install and connect CLIProxyAPI once before launching:

```bash
brew install cliproxyapi
brew services start cliproxyapi
cliproxyapi --codex-login
```

See the [CLIProxyAPI quick start](https://help.router-for.me/introduction/quick-start)
for upstream installation details.

The launcher uses `http://127.0.0.1:8317` and CLIProxyAPI's documented dummy
client token by default. Override them with `CLAUDEX_BASE_URL` and
`CLAUDEX_AUTH_TOKEN`; credentials are inherited only by the launched process
and are never written to the repository. `--subagent` accepts `sol`, `terra`,
or `luna` (and their full `gpt-5.6-*` model IDs).

Claudex forces the project status overlay for that process so an unrelated
user-level status line cannot mask it. The main row shows model, repository,
branch, observed context usage/window, effort, and route mismatches. Background
subagents get one live row each with state, task description, and token count.

### KimiCC (Kimi via Claude Code UI, interactive)

`start-kimicc.sh` is **Claude Code UI + Kimi models** (not the native Kimi TUI).
Use it when you want Claude Code ergonomics with K3 or K2.7 in a second
terminal while native Claude runs in the first.

```bash
export MOONSHOT_API_KEY=sk-…   # https://platform.kimi.ai/console/api-keys
./start-kimicc.sh                    # K3, 1M window / ~996k compact
./start-kimicc.sh --model k2.7       # K2.7 Code, 256k / ~249k compact
./start-kimicc.sh --model k2.7-highspeed
./start-kimicc.sh --endpoint coding  # Kimi Code subscription base URL
./start-kimicc.sh --isolate-config   # optional CLAUDE_CONFIG_DIR=$HOME/.claude-kimicc
```

| Model alias | Platform model id | Context | Auto-compact |
| --- | --- | --- | --- |
| `k3` (default) | `kimi-k3[1m]` | 1 048 576 | 996 147 |
| `k2.7` | `kimi-k2.7-code` | 262 144 | 249 036 |
| `k2.7-highspeed` | `kimi-k2.7-code-highspeed` | 262 144 | 249 036 |

**Headless / fleet Kimi stays on the native Kimi Code app** (`delegate.py --agent kimi`,
`ab ask-kimi`, or bare `kimi`). Do not point headless jobs at kimicc.

K2.7 requires **Thinking ON** in the Claude Code TUI (`Tab`) or the endpoint
rejects requests. Official guide: [Use Kimi in Claude Code](https://platform.kimi.ai/docs/guide/claude-code-kimi).

`start-codex.sh` launches Codex with:

- interactive Codex in dangerous bypass mode
- live web search and Codex 0.145 multi-agent V2 enabled
- at most three spawned children (four active agents including the root), with
  Terra/medium as the default child route and visible spawn metadata
- a footer showing model/reasoning, run state, context usage and window, 5-hour
  and weekly limits, branch, and current plan progress
- `CODEX_SESSION=1` so repo scripts can detect an interactive Codex session
- the canonical `main` checkout as its working root; the launcher does not create or refresh a detached interactive worktree
- generated Codex config and rollover state bootstrapped before launch
- an explicit native-Codex context profile, validated against `--model`/`-m`
  immediately and against the CLI-reported model at `SessionStart`
- repo subprocess defaults unchanged unless you explicitly override env vars

The V2 concurrency value under `[agents]` counts spawned children; Codex adds
the root slot internally. V2 ignores the legacy `agents.max_depth`, so LU keeps
nested fan-out bounded through its agent instructions and the three-child cap.
Native Codex children remain OpenAI-family and do not satisfy the repository's
independent cross-family review gate.

Bind a Codex session to one epic at launch so SessionStart loads only that
lane's handoff and rollover namespace:

```bash
./start-codex.sh --epic hramatka
./start-codex.sh --epic atlas
./start-codex.sh --epic harness
```

`--epic` is launcher-only and is not forwarded to the Codex CLI. It exports the
binding `SESSION_EPIC` and a provider-specific handoff identity such as
`codex-hramatka`. SessionStart selects that epic's `CODEX-DRIVER-HANDOFF.md`
when present and otherwise uses (or initializes) its shared
`CLAUDE-DRIVER-HANDOFF.md`. Without `--epic`, the existing cold-start rule still
requires the first user message or lane-assignment fallback to identify the
session before it touches a queue.

Override before launch if needed:

```bash
CODEX_DISPATCH_MODE=workspace-write CODEX_BRIDGE_MODE=safe ./start-codex.sh
```

For a repository created with `--separate-git-dir`, Git cannot recover the
primary checkout path from a linked worktree. In that uncommon layout, set
`CODEX_CANONICAL_REPO_ROOT=/absolute/path/to/main`; the launcher verifies that
the path is this repository's root on the `main` branch before using it.

Implementation work still follows `AGENTS.md`: create a scoped dispatch
worktree instead of editing or committing from the primary checkout. The
launcher also sets `GIT_OPTIONAL_LOCKS=0` so read-oriented Git commands do not
refresh the primary index unnecessarily.

---

## Claude Code Hooks

Session hooks live in `claude_extensions/hooks/` and deploy to `.claude/hooks/`.

### `session-setup.sh`

Runs on every session start, new or resumed.

| # | Check | Severity | Details |
| --- | --- | --- | --- |
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

### Gemini bridge auth modes

Gemini bridge commands now support explicit auth selection per invocation:

- `--auth subscription` strips `GEMINI_API_KEY` and `GOOGLE_API_KEY` for that subprocess so Gemini uses the logged-in subscription/OAuth path
- `--auth api-key` keeps key-based auth active for that subprocess
- `--auth auto` preserves ambient shell behavior

Use `subscription` as the default for normal bridge work. Use `api-key` only for explicit one-off calls that are meant to bypass the subscription path.

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

## Deterministic Track Audit

Run a reusable, non-LLM audit across a built track. The audit checks inventory,
activity and vocabulary sidecars, resources, generated MDX, learner-facing
English leakage, internal workflow leakage, and optional route metadata. It
explicitly excludes old LLM-QG state while issue #2156 is replacing that path.

```bash
.venv/bin/python scripts/audit/track_deterministic_audit.py --track b2 --format summary
```

Useful rollout examples:

```bash
.venv/bin/python scripts/audit/track_deterministic_audit.py --track b2 --format json --output /tmp/b2-deterministic-audit.json --fail-on never
.venv/bin/python scripts/audit/track_deterministic_audit.py --track b1 --format summary --fail-on never
.venv/bin/python scripts/audit/track_deterministic_audit.py --track a2 --format summary --fail-on never
.venv/bin/python scripts/audit/track_deterministic_audit.py --track a1 --format summary --fail-on never
```

Use `--range N-M` for a smoke pass before running a full track. Advisory
findings such as missing optional resources appear in the output, but
`--fail-on never` keeps baseline rollout runs from failing on them. Keep JSON
outputs under `/tmp` unless a durable audit report is explicitly in scope.

---

## UA Evaluation Harness Schema

The source-language-agnostic evidence contract for #2156 / #4307 lives in:

- `docs/projects/ua-eval-harness/schema.md`
- `scripts/audit/qg_schema.py`

`qg_schema.py` is a library module, not a CLI. Downstream scorer adapters should
import its builders and validators instead of inventing local finding shapes.

Useful examples:

```python
from scripts.audit.qg_schema import (
    build_dimension,
    build_deterministic_curriculum_finding,
    build_evidence_record,
    build_semantic_false_friend_finding,
    build_ua_gec_finding,
    validate_record,
)

finding = build_ua_gec_finding(
    error="являється",
    correction="є",
    tag="F/Calque",
    file="module.md",
    line=18,
    span={"start": 210, "end": 218},
    doc_id="0301",
)
record = build_evidence_record(
    profile="ua_gec_eval",
    evidence_kind="fixture",
    fixture_id="ua-gec-0301",
    dimensions={
        "contact_calque": build_dimension(score=9.0, verdict="WARN", findings=[finding]),
    },
    verdict="WARN",
    terminal_verdict="PASS",
)
validate_record(record)
```

The canonical schema version is `ua_contact_quality_evidence.v1`. Existing
`curriculum_ua_qg_evidence.v1` and `llm_qg_evidence.v1` records remain valid
projection profiles; do not regenerate module evidence just to adopt the new
schema.

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
# First-time build (no existing DB) — allowed unconditionally
.venv/bin/python scripts/wiki/build_sources_db.py

# Rebuild an existing populated DB — REQUIRES --force
.venv/bin/python scripts/wiki/build_sources_db.py --force

# Preview without touching disk
.venv/bin/python scripts/wiki/build_sources_db.py --dry-run

# Rebuild + wipe the wikipedia API cache too (rare)
.venv/bin/python scripts/wiki/build_sources_db.py --force --no-preserve-wiki
```

Rebuilds the unified SQLite database from textbook, literary, external,
Wikipedia, and dictionary inputs.

**Safety guards (#1563):**

- The script refuses to destroy a populated DB without `--force`.
- A populated DB is detected primarily by **file size** (>1 MB),
  not just by `COUNT(*)` on main tables. This guards against the
  2026-04-25 wipe pattern, where a transient SQLite error during
  the count made the script falsely conclude the DB was empty,
  proceed past the safety check, and `unlink()` a 1.46 GB file.
- `--dry-run` never mutates filesystem or DB state. Safe even on
  a populated DB.
- `--force` rebuilds everything except the `wikipedia` and
  `wikipedia_negative_cache` tables (snapshot + restore across the
  rebuild, since refetching costs Wikipedia API budget). Pass
  `--no-preserve-wiki` to wipe those too.

### Recovery: when `data/sources.db` is empty or corrupt

If `data/sources.db` is found at 0 bytes or with broken schema (the
2026-04-25 wipe pattern), restore from the Google Drive backup —
**do NOT run `build_sources_db.py --force`**, that rebuilds from
JSONL inputs which lack the post-#1427 `ukrainian_wiki` table and
the post-#1555 chunker policy.

```bash
# 1) Snapshot whatever is currently on disk (in case the "wipe" was
#    actually something subtler and we want forensic evidence).
cp data/sources.db "data/sources.db.bak-$(date +%Y%m%d-%H%M%S)"
ls -lah data/sources.db data/sources.db.bak-*

# 2) Check the GDrive backup age. Anything <30 days is fine; older
#    than that means more re-ingest work after restore.
#    Path resolution: $LU_GDRIVE_DATA env var if set, else glob the
#    per-user GoogleDrive mount. (Email is not hardcoded in committed
#    code — see #1577 Phase 1 Q4.)
GDRIVE="${LU_GDRIVE_DATA:-$(ls -d "$HOME/Library/CloudStorage/"GoogleDrive-*/"My Drive/Projects/learn-ukrainian-data" 2>/dev/null | head -1)}"
ls -lah "$GDRIVE/sources.db"

# 3) Restore from backup.
cp "$GDRIVE/sources.db" data/sources.db

# 4) Verify the restore worked: row counts should be non-trivial.
sqlite3 data/sources.db "
  SELECT 'textbooks',         COUNT(*) FROM textbooks UNION ALL
  SELECT 'literary_texts',    COUNT(*) FROM literary_texts UNION ALL
  SELECT 'external_articles', COUNT(*) FROM external_articles UNION ALL
  SELECT 'wikipedia',         COUNT(*) FROM wikipedia UNION ALL
  SELECT 'ukrainian_wiki',    COUNT(*) FROM ukrainian_wiki;
"

# 5) Re-ingest any tables that were added AFTER the backup date.
#    For backups older than 2026-04-23, ukrainian_wiki is missing.
#    Use the per-subdir loop (NOT `wiki/ --encode` — that command is
#    broken until #1570 ships, see scripts/wiki/ingest_ukrainian_wiki.py).
SUBDIRS="wiki/academic/c1 wiki/figures wiki/folk/genres wiki/folk/lyric \
         wiki/folk/prose wiki/folk/ritual wiki/folk/short-forms wiki/folk/tradition \
         wiki/grammar/a2 wiki/grammar/b1 wiki/grammar/b2 wiki/historiography \
         wiki/linguistics/oes wiki/linguistics/ruthenian wiki/literature/works \
         wiki/pedagogy/a1 wiki/periods"
for d in $SUBDIRS; do
  .venv/bin/python scripts/wiki/ingest_ukrainian_wiki.py "$d"
done

# 6) Re-encode any corpora whose dense embeddings drifted with the
#    schema. After a fresh backup, this should be a no-op for
#    textbook_sections / external / wikipedia. After ukrainian_wiki
#    re-ingest in step 5, it must run for that corpus.
.venv/bin/python scripts/wiki/cold_encode.py \
    --corpora textbook_sections,external,wikipedia,ukrainian_wiki --dry-run

# Run without --dry-run for any corpus where new_units > 0.
.venv/bin/python scripts/wiki/cold_encode.py \
    --corpora ukrainian_wiki --resume

# 7) Refresh the GDrive backup so the next session starts from a
#    clean point.
./scripts/backup-data.sh
```

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

### Services (`./services.sh`)

Canonical process manager for the three long-running local services. It owns
PID/lock/port bookkeeping — **always use it instead of ad-hoc `npm run dev`,
`astro preview`, or `nohup`**, which create port drift (4322/4323…) and orphan
servers.

| Service | Port | What it is |
| --- | --- | --- |
| `sources` | 8766 | MCP Sources Server (SQLite FTS5 — textbooks, dicts, literary, Wikipedia). Legacy alias: `rag`. |
| `api` | 8765 | API / Monitor dashboard (FastAPI) — the `/api/orient` etc. cold-start endpoints. |
| `astro` | **4321** | **Astro Course UI dev server** — the local site. Alias: `starlight`. |

```bash
./services.sh status            # read-only, safe — what's running + PID + port
./services.sh start             # start all three
./services.sh start astro       # start ONLY the Course UI → http://localhost:4321/
./services.sh stop astro        # stop one service
./services.sh restart astro     # restart one service (use after dependency/config changes)
```

**Local site = `./services.sh start astro` → http://localhost:4321/** (live-reload
dev server; reflects source edits to `starlight/src/**` immediately). For a
build-accurate local copy of what would deploy, use the production build instead
of a second server:

```bash
./services.sh build astro       # astro production build → starlight/dist/ (no server)
./services.sh clean astro       # remove build/cache outputs
./services.sh rebuild astro     # clean then build
```

> Public deploy is separate and **manual**: the `deploy-pages.yml` GitHub Actions
> workflow (`workflow_dispatch`) — auto-deploy on push to `main` is disabled.
> Running services locally never touches the live site.

### Key Files

| File | Purpose |
| --- | --- |
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
| --- | --- |
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
- `mcp__sources__vet_vocabulary` - batched VESUM/CEFR/Russian-shadow vocabulary vetting (optional SUM-11 gloss)
- `mcp__rag__search_text` - textbook content search
- `mcp__rag__search_definitions` - SUM-11 explanatory dictionary
- `mcp__rag__search_style_guide` - Antonenko-Davydovych style guidance

### Deterministic audit checks

At `scripts/audit/checks/`:

- `cross_file_integrity.py` - vocabulary used in activities exists in vocabulary YAML
- `outline_compliance.py` - markdown section structure matches `meta.yaml` outline
- `activity_quality.py` - deterministic activity quality checks

Additional audit guardrails:

- `scripts/audit/lint_dispatch_brief.py` - dispatch brief `.venv/bin/python` worktree guardrail
- `scripts/audit/atlas_source_census.py` - aggregate-only Word Atlas source intake census; public reports must not include raw source text, private paths, or candidate lemma lists
- `scripts/audit/atlas_entry_model_census.py` - aggregate-only Word Atlas entry-model census; separates reviewed article entries by `entry_type` from alias/form records
- `scripts/audit/atlas_source_entry_count.py` - aggregate-only Word Atlas source-corpus entry-demand census by finalized entry-model bucket; public reports must not include source text, private paths, filenames, or candidate lists
- `scripts/atlas/atlas_db.py` - rebuild `data/atlas.db` from the hydrated Atlas manifest, materialize the Astro article payload projection, and validate alias targets
- `scripts/atlas/fill_local.py` - Phase-1 offline local enrichment writer for `data/atlas.db`; reads local dictionary/cache data only and reports per-section before/after coverage
- `site/scripts/benchmark-atlas-db.mjs` - benchmark Atlas DB build, preload, and getStaticPaths mapping at current and synthetic sizes
- `scripts/audit/curriculum_qg_harness.py` - deterministic Ukrainian curriculum QG fixture harness; use it to calibrate B1-27, A1/A2 scaffolding, B1+ leakage, and seminar-register checks before changing QG behavior

### Build pipeline entry point

`.venv/bin/python scripts/build/v7_build.py {level} {slug} --worktree` is the single end-to-end build entry point. It drives the write -> enrich -> review -> audit -> publish chain.

### Agent runtime

`scripts/agent_runtime/` is the universal adapter layer for the dispatchable agent
lanes. See [`docs/agent-runtime-guide.md`](agent-runtime-guide.md). Gemini-family
work uses AGY; the legacy Gemini CLI route is unsupported.

### Delegate to background workers

```bash
.venv/bin/python scripts/delegate.py dispatch \
  --agent {codex|claude|agy|grok|grok-build|grok-hermes|kimi|deepseek|cursor} \
  --task-id <id> \
  --prompt-file <file> \
  --worktree \
  --mode danger
```

Fire-and-forget **execution** with status polling and completion artifacts. This is the right tool when you need another agent to write code, run commands, and commit — not to hold a conversation. For discussion, reviews, or Q&A see [Inter-Agent Communication](#inter-agent-communication) below (`ai_agent_bridge` channel bridge, `ask-*`).

For write-capable delegation, prefer `--worktree`. `delegate.py` creates the worktree if missing and records its path in the task state. `--mode danger` now requires `--worktree` so background agents cannot switch branches in the main checkout by accident.

#### Project Research Registry — orchestrator dispatch duty

Before every dispatch, the orchestrator classifies the task by functional role,
task family, track, and owned paths. Pass every known dimension explicitly; the
dispatcher never infers research context from the prompt, provider, agent, branch,
or task ID:

```bash
.venv/bin/python scripts/delegate.py dispatch \
  --agent codex \
  --task-id quality-4952 \
  --prompt-file docs/dispatch-briefs/quality-4952.md \
  --worktree \
  --mode danger \
  --research-role quality \
  --research-task-family difficulty-gate \
  --research-track core \
  --research-owned-path scripts/audit/text_difficulty.py
```

`--research-role`, `--research-task-family`, and `--research-track` are
single-valued; repeat `--research-owned-path` when the task owns multiple paths.
Matching is conjunctive, so omitting a dimension required by a registry record
safely produces no pointer. Never invent a value to force a match. If the task is
genuinely generic or unknown, omit all `--research-*` flags and record that
classification in the brief or orchestration note.

The worker receives bounded pointers, not record bodies. When it relies on one,
it fetches `GET /api/knowledge/record/{id}?task=<task-id>` while the delegated
task is active. This creates attributed consumption evidence in the task state;
`GET /api/knowledge/monitor?window_days=30` exposes only privacy-safe aggregate
surface/consumption health. A surfaced pointer is not proof of consumption, and
workers must not fetch irrelevant records merely to inflate adoption metrics.
Registry delivery is fail-open when disabled or degraded; task classification
remains an orchestrator responsibility.

Gemini-family work routes through `--agent agy`; the legacy `gemini` dispatcher
choice remains compatibility-only and should not be used for new work.

---

## Build & Validation Workflow

Use two entry points depending on the job:

| Need | Entry point |
| --- | --- |
| Full module build | `.venv/bin/python scripts/build/v7_build.py {level} {slug} --worktree` |
| Validate existing content | `npm run audit`, `npm run pipeline`, `npm run generate:json` |

### `scripts/build/v7_build.py`

Single end-to-end build entry point.

```bash
# Single module
.venv/bin/python scripts/build/v7_build.py a1 m01-alphabet --worktree

# Resume from prior state
.venv/bin/python scripts/build/v7_build.py hist m12-kyivan-rus --worktree --resume

# Run a specific step only
.venv/bin/python scripts/build/v7_build.py b1 m09-travel --worktree --step review
```

Useful flags:

- `--writer` and `--reviewer` choose agent family
- `--step` runs a targeted phase
- `--resume` reuses saved progress
- `--no-skeleton` and `--no-chunk` alter generation behavior

#### Build monitoring with Claude Code `Monitor` tool

v7_build.py emits JSONL events on stdout (`module_start`, `phase_done`, `review_score`, `module_done`, `module_failed`, `batch_done`). Use the Claude Code `Monitor` tool to stream these as notifications:

```
Monitor(
    command=".venv/bin/python -u scripts/build/v7_build.py a1 m01-alphabet --worktree --resume 2>&1 | grep --line-buffered '^{\"event\"'",
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

`pipeline.py` is the technical validation pipeline. It is not the same thing as the end-to-end build orchestrator in `scripts/build/v7_build.py`.

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
| --- | --- | --- |
| `scripts/build/v7_build.py` | End-to-end module build | `.venv/bin/python scripts/build/v7_build.py a1 m01-alphabet --worktree` |
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
| `scripts/audit/atlas_source_census.py` | Build aggregate-safe Word Atlas source planning counts | `.venv/bin/python scripts/audit/atlas_source_census.py --markdown-out docs/runbooks/word-atlas-source-census-planning.md` |
| `scripts/audit/atlas_entry_model_census.py` | Count reviewed Atlas entries by finalized `entry_type` bucket | `.venv/bin/python scripts/audit/atlas_entry_model_census.py --format markdown` |
| `scripts/audit/atlas_source_entry_count.py` | Estimate aggregate source-corpus Atlas entry backlog by finalized bucket | `.venv/bin/python scripts/audit/atlas_source_entry_count.py --include-ohoiko-private --markdown-out docs/runbooks/word-atlas-source-entry-count.md` |
| `scripts/atlas/atlas_db.py` | Rebuild `data/atlas.db`, materialize article payloads, and validate public alias targets | `.venv/bin/python -m scripts.atlas.atlas_db --db data/atlas.db` |
| `scripts/atlas/fill_local.py` | Fill `data/atlas.db` with Phase-1 local Atlas enrichment rows | `.venv/bin/python -m scripts.atlas.fill_local --db data/atlas.db --report-json /tmp/atlas-fill-local-report.json` |
| `site/scripts/benchmark-atlas-db.mjs` | Benchmark Atlas DB build, preloaded payload read, and getStaticPaths mapping | `npm --prefix site run atlas:perf` |
| `scripts/audit/curriculum_qg_harness.py` | Run calibrated Ukrainian QG fixtures or scan one module into compact evidence | `.venv/bin/python scripts/audit/curriculum_qg_harness.py --fixtures tests/fixtures/curriculum_qg/fixtures.yaml` |
| `scripts/audit/ingest_ua_gec_gold.py` | Curate the small attributed UA-GEC gold fixture for the #2156 eval harness | `.venv/bin/python scripts/audit/ingest_ua_gec_gold.py --dry-run` |
| `scripts/audit/module_quality_audit.py` | Report surface and LLM-QG/compact evidence coverage by level | `.venv/bin/python scripts/audit/module_quality_audit.py --level b1 --format summary` |
| `scripts/audit/lint_session_state.py` | Check handoff docs for missing env-file references | `.venv/bin/python scripts/audit/lint_session_state.py --all` |
| `scripts/audit/lint_anti_menu.py` | Detect anti-menu sign-off prompts in markdown | `.venv/bin/python scripts/audit/lint_anti_menu.py --text docs/session-state/current.md` |
| `scripts/audit/decision_lineage.py` | Scan decision git backlinks | `.venv/bin/python scripts/audit/decision_lineage.py --decision-id ADR-008` |

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

### `scripts/audit/curriculum_qg_harness.py`

Deterministic Ukrainian curriculum QG calibration harness for issue #2156.
Use it before changing QG prompts, evidence persistence, or deterministic
surface checks. It does not bulk-score the curriculum and does not write raw
LLM logs.

```bash
# Run the labeled PR1 fixture suite
.venv/bin/python scripts/audit/curriculum_qg_harness.py \
  --fixtures tests/fixtures/curriculum_qg/fixtures.yaml

# Scan one module and print compact evidence
.venv/bin/python scripts/audit/curriculum_qg_harness.py \
  --module-dir curriculum/l2-uk-en/b1/aspect-in-imperatives \
  --level b1 \
  --slug aspect-in-imperatives \
  --format json
```

The fixture suite covers current and restored-bad B1-27 behavior, allowed
A1/A2 English scaffolding, B1+ English leakage, local English glosses, and
seminar-register pathos. Single-module scans emit compact evidence shaped like
`qg_evidence.json`: module id, level policy, checker version/config/hash,
content hash, dimensional scores/findings, compact spans/excerpts, LLM metadata
placeholders, and provenance.

### `scripts/audit/qg_workflow.py`

Cost-aware tiered curriculum QG workflow for #2156 / #4310. It composes
deterministic structural checks, optional UA-GEC gold lookup, and the gated LLM
reviewer into one canonical `qg_schema` evidence record. Live LLM dispatch is
not wired by default; Tier 2 uses a composite cache hit or an explicitly
provided reviewer response until #4370 calibration lands.

```bash
# Dry-run before broad reviewer spend; writes nothing
.venv/bin/python scripts/audit/qg_workflow.py \
  --target b1:aspect-in-imperatives:curriculum/l2-uk-en/b1/aspect-in-imperatives \
  --dry-run \
  --format json

# Single-module deterministic workflow evidence
.venv/bin/python scripts/audit/qg_workflow.py \
  --module-dir curriculum/l2-uk-en/b1/aspect-in-imperatives \
  --level b1 \
  --slug aspect-in-imperatives \
  --format json
```

Tier 0 always runs `DeterministicRuleAdapter` and
`llm_reviewer.run_structural_checks()`. A hard Tier-0 `FAIL` skips Tier 2 by
default for cost, overriding the harness's `llm_review.required` flag; use
`--llm-on-fail` only when richer diagnostics are worth reviewer spend. Tier 2
is eligible by `policy_for_level(level).family` (`b1_plus` and `seminar`) or by
explicit `--force-llm` / calibration sample. Broad Tier-2 runs require a
passing `llm_qg_canaries.py` result and budget ceilings such as
`--max-llm-calls` or `--max-cost-usd`.

The LLM cache reuses `scripts/audit/llm_qg_store.py` with the composite key
`content_sha + gate_version + prompt_hash + checker_version +
level_policy.family + reviewer_model_id`. The content basis is
`llm_qg_store.CONTENT_FILES` (`module.md`, `activities.yaml`,
`vocabulary.yaml`, `resources.yaml`), not the promotion sidecar's plan-inclusive
hash.

### `scripts/audit/ingest_ua_gec_gold.py`

Curates the small tracked UA-GEC fixture for the #2156 eval harness. It reads
the local ignored `data/sources.db` table `ua_gec_errors`, recovers sentence
context/spans from the local `data/ua-gec` clone, maps tags through
`scripts/audit/qg_schema.py`, and writes `data/ua-gec-gold/ua-gec-gold.json`
with top-level CC-BY-4.0 attribution and per-row `build_ua_gec_finding` output.

Run the dry-run first; it prints candidate totals, per-tag/source-language
counts, kept/rejected totals, and rejection reasons without writing files.

```bash
.venv/bin/python scripts/audit/ingest_ua_gec_gold.py --dry-run
```

Dispatch worktrees may not contain the ignored local source clone/database. In
that case, pass the main-checkout source paths explicitly:

```bash
.venv/bin/python scripts/audit/ingest_ua_gec_gold.py --dry-run \
  --db-path /path/to/learn-ukrainian/data/sources.db \
  --ua-gec-root /path/to/learn-ukrainian/data/ua-gec

.venv/bin/python scripts/audit/ingest_ua_gec_gold.py \
  --db-path /path/to/learn-ukrainian/data/sources.db \
  --ua-gec-root /path/to/learn-ukrainian/data/ua-gec \
  --retrieval-date YYYY-MM-DD
```

The curation policy is intentionally not a raw extract: it prioritizes
`F/Calque` rows with Russian source language, includes `G/Case` and
`G/Gender`, rejects rows without recoverable context, duplicate pairs, empty
edits, known context-stripped junk such as `рожі -> мармизи` and
`вдів -> одягнув`, short opaque word-form pairs, and excessive
same-document/tag repeats. Tune the documented CLI constants only when the
fixture policy itself is changing.

### `scripts/audit/module_quality_audit.py`

Coverage report for planned modules, built modules, deterministic surface
failures, persisted LLM-QG records, and compact file-only `qg_evidence.json`
records.

```bash
.venv/bin/python scripts/audit/module_quality_audit.py --level b1 --format summary
.venv/bin/python scripts/audit/module_quality_audit.py --level b1 --format json
```

Use this before spending reviewer tokens. A current compact `qg_evidence.json`
counts as current file-only QG evidence, but modules still remain in the DB
persistence count until their LLM-QG result is stored in the telemetry DB.

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
| --- | --- |
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

### `lint_session_state.py`

Scans `docs/session-state/*.md` for references to env/config files that do not exist locally.

```bash
.venv/bin/python scripts/audit/lint_session_state.py --all
.venv/bin/python scripts/audit/lint_session_state.py --file docs/session-state/current.md
```

Known user-scoped paths that are expected but not committed live in
`scripts/audit/known_user_paths.yaml`. This check is also wired into pre-commit
for `docs/session-state/*.md`.

**Capabilities and Limitations:**
- ✅ Catches: missing-file references for tilde-rooted dotfiles (`~/.bash_secrets`, etc.) + `.env*` variants.
- ❌ Does NOT catch: typos that resolve to a different *existing* file, or verify content-correctness *inside* referenced files.

### `scripts/audit/lint_anti_menu.py`

Scans markdown for MEMORY #0I anti-menu sign-off prompts while ignoring
acceptance criteria, code fences, tables, and status/plan lines.

```bash
.venv/bin/python scripts/audit/lint_anti_menu.py --text docs/session-state/current.md
cat handoff.md | .venv/bin/python scripts/audit/lint_anti_menu.py --stdin
```

### `scripts/audit/decision_lineage.py`

Scans `docs/decisions/**/*.md` plus git history for commits and PR references
that touch or cite decision files by file path, filename slug, title, ADR ID,
or declared decision ID.

```bash
.venv/bin/python scripts/audit/decision_lineage.py
.venv/bin/python scripts/audit/decision_lineage.py --decision-id ADR-008
```

The Monitor API exposes the same read-only JSON at `/api/decisions/lineage`.

---

## Dashboards

| Entry | Purpose |
| --- | --- |
| `scripts/generate_dashboard_data.py` | Aggregate audit cache into dashboard data |
| `scripts/build_dashboards.py` | Build HTML dashboards with embedded data |
| `npm run dashboards:data` | Regenerate `dashboards/data/status.json` |
| `npm run dashboards:build` | Rebuild dashboard HTML |

---

## Inter-Agent Communication

Claude, Gemini, and Codex coordinate through three distinct primitives. Pick the right one for the job.

> **Authoritative sources:**
> - [`docs/best-practices/agent-bridge.md`](best-practices/agent-bridge.md) — channel bridge mechanics, pinned context, include chains, bridge `discuss`
> - [`docs/best-practices/agent-cooperation.md`](best-practices/agent-cooperation.md) — agent roles, Green Team protocol, review discipline
>
> This section is a quick-reference index. For anything more than the examples below, read the authoritative docs.

### When to use which tool

| Need | Tool | Write access? |
| --- | --- | --- |
| Sustained topic-scoped discussion, multi-turn, pinned context | **`ai_agent_bridge post` / `ai_agent_bridge discuss`** (channel bridge) | No (Q&A only) |
| One-off drive-by question to another agent | **`ask-claude` / `ask-agy` / `ask-codex`** | No by default; opt-in via `--allow-write` |
| Fire-and-forget execution — run code, commit, push | **`scripts/delegate.py dispatch`** | Yes |
| Watch a long-running process (builds, reviews) emit events — **Claude only** | **`Monitor` tool** (Claude Code built-in) | N/A |
| Watch a long-running process — **Gemini / Codex** | Shell-poll the Monitor API | N/A |
| Read project state (track health, failing modules, build status) | **Monitor API** — `http://localhost:8765` | N/A |

**Rules of thumb:**
- Channel-first for anything >1 turn. The pinned `context.md` eliminates re-pasting project setup on every round.
- `ask-*` is not deprecated for genuine one-shots. `ask-gemini` is retired; use `ask-agy` for Gemini-family one-shots.
- `ai_agent_bridge` is for **communication**. `delegate.py dispatch` is for **execution**. Don't confuse them.
- Never run a polling loop to check a background task — use `Monitor` or the bash `run_in_background` completion notification.

### Channel bridge — preferred for multi-turn

Channels are topic-scoped threads with auto-prepended pinned context and a Monitor API state snapshot on every post. Full docs in [`agent-bridge.md`](best-practices/agent-bridge.md).

Seeded channels: `shared`, `pipeline`, `content`, `architecture`, `reviews`. `shared` is included by all others.

Use the explicit bridge path. Do not rely on `ab`; on some machines it resolves to ApacheBench.

```bash
# Inspect
.venv/bin/python scripts/ai_agent_bridge/__main__.py channel list
.venv/bin/python scripts/ai_agent_bridge/__main__.py channel info pipeline
.venv/bin/python scripts/ai_agent_bridge/__main__.py channel tail reviews -n 20
.venv/bin/python scripts/ai_agent_bridge/__main__.py channel tail reviews --thread THREAD_ID

# Create a new topic-scoped channel
.venv/bin/python scripts/ai_agent_bridge/__main__.py channel new mytopic --include shared --agents claude,agy,codex

# Post — short form (one recipient)
.venv/bin/python scripts/ai_agent_bridge/__main__.py p reviews agy "Review the heal-loop changes in scripts/build/linear_pipeline.py"

# Post — long form (multi-recipient, threading)
.venv/bin/python scripts/ai_agent_bridge/__main__.py post reviews "Adversarial review of #1299 docs patch" --to agy,codex --parent MSG_ID

# Multi-agent bounded discussion (parallel rounds, short-circuits on [AGREE])
.venv/bin/python scripts/ai_agent_bridge/__main__.py discuss architecture "Should we extract the V6 god object?" \
    --with claude,agy,codex --max-rounds 2

# Drain incoming channel deliveries (REQUIRED for headless AGY/Codex;
# Claude Code drains automatically via OS-level watchers)
.venv/bin/python scripts/ai_agent_bridge/__main__.py sync agy
.venv/bin/python scripts/ai_agent_bridge/__main__.py sync --all
```

**Reading messages — critical distinction:**

- `sync <agent>` drains the **channel deliveries queue** — this is how AGY and Codex actually receive channel posts when running headless.
- `inbox` (in the Legacy broker section below) reads the **old 1:1 message queue ONLY**. It does NOT show channel messages. If you expected channel posts and `inbox` is empty, run `sync` instead.

Web dashboard at `http://localhost:8765/channels.html` (localhost-only, read + post).

### One-off `ask-*`

Fire a single query at one agent. Each recipient has its own model flag and defaults — do not assume they are interchangeable.

| Recipient | Flag | Recommended value |
| --- | --- | --- |
| AGY | `--to-model` | `gemini-3.1-pro-high` or display label from `agy models`, e.g. `Gemini 3.1 Pro (High)` |
| Codex | `--model` | omit unless overriding (defaults to `gpt-5.5` via runtime config) |
| Claude | `--to-model` | omit (auto-selects per active session); override only when routing to a specific Opus/Sonnet tier |

```bash
# AGY — Gemini-family adversarial review
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-agy "Adversarial review for #NNN. Read {path}." \
  --task-id issue-NNN \
  --to-model gemini-3.1-pro-high

# Codex — quick question
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-codex "Review posted on #1177. Please read and respond." \
  --task-id issue-1177

# Claude — routed from AGY/Codex or a script
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-claude "Please verify the stress marks in curriculum/l2-uk-en/a1/hello.md" \
  --task-id stress-verify-hello --from agy

# AGY with skill activation + write access
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-agy "Activate skill final-review. ..." \
  --task-id fr-{slug} --allow-write \
  --delimiters FINAL_REVIEW,FRICTION \
  --to-model gemini-3.1-pro-high
```

AGY examples:

```bash
# Default: AGY bridge call
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-agy "Review #NNN." \
  --task-id issue-NNN \
  --to-model gemini-3.1-pro-high

# Fast AGY one-off
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-agy "Quick one-off check." \
  --task-id adhoc-agy-check \
  --to-model gemini-3.5-flash-high

# Drain AGY channel inbox explicitly
.venv/bin/python scripts/ai_agent_bridge/__main__.py inbox run agy
.venv/bin/python scripts/ai_agent_bridge/__main__.py sync agy
```

> **Note.** You rarely call `ask-claude` from inside a Claude session — you already *are* Claude. It's the return path for AGY/Codex or for scripts routing work to Claude.

### Execution via `delegate.py dispatch`

For write-access work (implement, commit, push). See [Delegate to background workers](#delegate-to-background-workers) above for the full command. **Not** a comms tool — use `ai_agent_bridge` or `ask-*` to discuss, `delegate.py` to have the work done.

When the delegated task may edit files or run git commands:

```bash
.venv/bin/python scripts/delegate.py dispatch \
  --agent codex \
  --task-id issue-1383-smoke \
  --prompt-file /tmp/prompt.md \
  --worktree \
  --mode danger
```

`delegate.py status <task-id>` will include the `worktree_path` so operators can inspect or clean it up later.
Use `delegate.py status-or-fail <task-id>` before reporting async task state from memory; it exits 0 only when the Monitor API confirms the task is currently running, exits 1 when the task is done/missing/stale, and exits 2 when the Monitor API is unreachable.

### Monitoring

Two event surfaces, split by agent:

- **Claude Code** has a built-in `Monitor` tool that streams stdout events as notifications with ~zero context cost. Use it to watch `v7_build.py` JSONL events, `.venv/bin/python scripts/ai_agent_bridge/__main__.py channel watch --event-stream`, or any long-running command. Invoke the tool directly — do **not** wrap it in a shell poll loop.
- **Gemini / Codex** (headless) do not have `Monitor`. Poll the Monitor API via `curl` when they need to check state.

State queries (all agents):

```bash
curl -s http://localhost:8765/api/state/track-health/a1
curl -s http://localhost:8765/api/state/failing?track=a2
curl -s http://localhost:8765/api/state/build-status/a1
curl -s http://localhost:8765/api/delegate/active
```

Full Monitor API reference: [`docs/MONITOR-API.md`](MONITOR-API.md).

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

### Usage telemetry

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py codex-usage --window 5h
.venv/bin/python scripts/ai_agent_bridge/__main__.py codex-usage --window 24h --entrypoint bridge --json
```

Reads recent `batch_state/api_usage/usage_codex-*.jsonl` records, groups by outcome and entrypoint, lists recent rate-limit events, and reports whether `gpt-5.5` currently has bridge headroom.

### Legacy message broker

The original 1:1 broker (separate from channels) is still available for low-level inspection and legacy flows. Prefer channels for new work.

> **Do not confuse with channel draining.** `inbox` reads **only** the legacy 1:1 queue. Channel deliveries require `sync <agent>` (see Channel bridge above). An empty `inbox` does NOT mean you have no channel messages.

```bash
.venv/bin/python scripts/ai_agent_bridge/__main__.py inbox
.venv/bin/python scripts/ai_agent_bridge/__main__.py inbox --for codex
.venv/bin/python scripts/ai_agent_bridge/__main__.py read <message_id>
.venv/bin/python scripts/ai_agent_bridge/__main__.py conversation <task_id>
.venv/bin/python scripts/ai_agent_bridge/__main__.py send "Your message" --type query --task-id my-task
.venv/bin/python scripts/ai_agent_bridge/__main__.py interactive
```

| Message type | Purpose |
| --- | --- |
| `query` | Ask another agent a question |
| `response` | Return an answer |
| `request` | Request work |
| `handoff` | Transfer a task with context |
| `context` | Share state or findings |
| `feedback` | Review or comment |

### Helper tools

```bash
.venv/bin/python scripts/tools/signal_claude.py "Your message here"
.venv/bin/python scripts/tools/message_viewer.py   # archive viewer on http://localhost:5055
```

---

## Common Workflows

| Workflow | Command |
| --- | --- |
| Build one module | `/module {level} {num}` |
| Full seminar rebuild | `/full-rebuild {track} {slug}` |
| Full core rebuild | `/full-rebuild-core {level} {num}` |
| Full v7 build via script | `.venv/bin/python scripts/build/v7_build.py {level} {slug} --worktree` |
| Audit a module or range | `npm run audit -- {level} {num\|range}` |
| Run technical validation | `npm run pipeline l2-uk-en {level} {num}` |
| Generate app JSON | `npm run generate:json l2-uk-en {level} {num}` |
| Sync landing pages | `npm run sync:landing` |
| Compile one wiki article | `.venv/bin/python scripts/wiki/compile.py --track {track} --slug {slug}` |
| Compile a wiki track with review | `.venv/bin/python scripts/wiki/compile.py --track {track} --all --review` |
