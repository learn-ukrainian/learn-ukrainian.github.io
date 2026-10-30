# Scripts & Workflow Reference

Current operational reference for repo-local scripts and agent workflows.

- Main build entry point: `.venv/bin/python scripts/build/v7_build.py {level} {slug} --worktree`
- Validation pipeline after content exists: `npm run audit`, `npm run pipeline`, `npm run generate:json`
- Typed sub-issue removal: `.venv/bin/python -m scripts.publish issue-unlink --repo owner/repo --parent-id PARENT_NODE_ID --child-id CHILD_NODE_ID` (#9647)
- This document intentionally omits retired pipelines and legacy script paths
- **Seat onboarding (ownership matrix, ACPX boundary, Kimi routes retired, Buzz deferral):**
  [`docs/runbooks/agent-seat-onboarding.md`](runbooks/agent-seat-onboarding.md)

Before guessing CLI flags, run the tool's `--help`. The repo standard lives in
`agents_extensions/shared/rules/cli-help-standard.md`, and touched CLIs are expected to
meet it so agents can use them without source-diving.

## GRAC frequency snapshot

`.venv/bin/python -m scripts.ingest.grac_frequency_ingest --db data/grac_frequency.db`
ingests `lemma` and `word` down to the inclusive `--min-freq` (default 5).
Use a separate local destination for probes; `--max-pages` bounds committed
frequency bands per attribute, including any requests needed to finish a tie.

The ingest requests page 1 of each descending frequency window. It fetches the
last frequency group with equal `wlminfreq`/`wlmaxfreq`, enlarging `wlmaxitems`
to that group's `total` when needed, and verifies the entire distinct group
before advancing `wlmaxfreq` below it. Higher frequencies are wholly in page 1;
no tie is split between committed windows. A truncated or changing tie halts
without advancing the checkpoint. Items are deduplicated by `(attr, str)`;
a wholesale earlier band violates the upper bound and halts. Completion also
requires the stored distinct count to equal the original server `total` for the
floor; a mismatch reports the gap and stays incomplete.

Existing offset checkpoints, including page 12 with 12,000 lemma rows, replay
once from the top automatically. No database replacement or row deletion is
needed. Existing items retain their original provenance; new request receipts
append after the old checkpoint. `frequency_cursor` stores the next upper
frequency and original total; `request_bounds` records the actual request
floor, ceiling and size. Provenance/checkpoint page numbers are receipt IDs;
remote `wlpage` is always 1. Rows, receipts and cursor commit together.
The three-second default delay, bounded retry/backoff and immediate 403/429
stop policy apply to tie requests too. A reconciliation failure needs operator
investigation; rerunning does not turn an incomplete snapshot into complete.

A six-request bounded probe verified the frequency-window parameters on
2026-10-08 (#10087):

```text
wlminfreq=9369 wlmaxfreq=9369 wlmaxitems=1000: rows=2 total=2 lastpage=1 frequencies=[9369]
wlminfreq=5 wlmaxfreq=9368 wlmaxitems=1000: rows=1000 total=1135917 lastpage=0 min_returned=8316 max_returned=9366
wlminfreq=5 wlmaxfreq=5 wlmaxitems=2: rows=2 total=147011 lastpage=0
wlminfreq=5 wlmaxfreq=5 wlmaxitems=147011: rows=147011 distinct=147011 total=147011 lastpage=1
```

The first two requests tested `wlsort=w`: the first lacked `Items`, and the
second returned `No format specified for custom frequency`. The ingest uses
`wlsort=frq`.
The successful exact-floor probe recovered a tie larger than the normal page
size in one response. API/manatee versions were `open-5.71.15` and
`2.36.7-open-2.225.8`. See #9969 for the original snapshot/read design.

## Usage advice ingest (Glavcom & mova.ua)

`.venv/bin/python -m scripts.ingest.usage_advice_ingest [--source movne_pytannya|movaua|all]`
ingests Ukrainian usage advice and word-pair distinctions from:
1. Glavcom «Мовне питання» (archive by Olha Vasylieva) into `data/movne_pytannya.db`.
2. Мова – ДНК нації (mova.ua / ukr-mova.in.ua) into `data/movaua.db`.

Key behaviors:
- Honest identifying User-Agent by default (`learn-ukrainian-usage-ingest/1.0 ...`) with `--user-agent` override.
- Strict circuit-breaker stop on HTTP 403 (marks `error_status = 'http_403'` in SQLite to skip in subsequent incremental runs; zero retries).
- Exponential backoff on HTTP 429 and 5xx, respecting standard `Retry-After` headers.
- Incremental mode (`--incremental`, default true) querying existing SQLite tables.
- Full fidelity: untruncated raw HTML, article text, content SHA-256 digest, and metadata.
- Re-extraction CLI mode: `--re-extract` / `--reextract` re-runs word-pair extraction from stored raw HTML in SQLite without network traffic.
- Optional JSON export: `--export-json-movne <path>` and `--export-json-movaua <path>`.

```bash
.venv/bin/python -m scripts.ingest.usage_advice_ingest --source all
.venv/bin/python -m scripts.ingest.usage_advice_ingest --re-extract --source all
```

## Reviewer bench health

`.venv/bin/python -m scripts.review.bench_health [--profile code|infra] [--risk low|medium|high|critical]`
counts only reviewers eligible for automatic routing. It exits 0 when every author
family meets its required minimum and 1 for any shortfall, with JSON exclusion
reasons on stderr. The default minimum is two seats. The documented
`ACCEPTED_SINGLE_SEAT_BENCHES` constant accepts one seat for Anthropic and OpenAI
authors at high/critical risk (#9423 AC-02). High is limited to Sol/Opus by #9538;
critical by the catalog's `critical_review` role (#9583). OpenAI authors have
Opus alone because Cursor-routed Claude stays unpinned (#9488). Such rows
display `[EXPECTED single seat]`; zero seats always fails. The summaries are
`BENCH HEALTH PASS: All author families meet their required reviewer minimum.` or
`BENCH HEALTH FAIL: At least one author family is below its required reviewer minimum.`
This diagnostic exception changes neither eligibility nor routing policy.

For the Composer and pool exclusion evidence (AC-01), see [#9423](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/9423).

## Routing facts (capacity and admission)

`scripts.fleet.credit_lane.routing_facts(lane, record, *, model, snapshot_metadata=None, policy=None, now=None, usage_dir=None)`
is the one reading of a routing-budget lane record (#9740). `capacity_pick`,
`idle_settle` and the curriculum wave gate use its
facts before adding their own restrictions (role, risk, egress, transport, wave
config). The reviewer scheduler uses the same plan-window reader.
Pass `model=None` for lane inventory. It returns the tightest plan window and its
source, snapshot/probe freshness, `health` (`healthy`, `unhealthy` or `unknown`,
with `health_basis`), the pace deficit, credit evidence and a `capacity` class:
`verified`, `unknown`, `unknown_stale` or `avoid`. Missing data stays `unknown`, never
fresh or healthy.

- **`UNKNOWN — stale/advisory`:** a pace deficit or weekly-pace hot label read
  from a stale snapshot or probe is `unknown_stale`. It is history, not a current
  refusal. `capacity_pick` ranks these rows after every row with verified capacity
  and before AVOID rows. They never appear in `cooler_lanes` and never satisfy
  `--strict`. Near cap, runtime-blocked hot, unhealthy, `NEED_LOGIN` and ineligible
  lanes stay AVOID.
- **Lane health scan:** `scripts.api.lane_health.scan_lane_health` returns a typed
  `LaneHealthScan`. Each lane's `health_for(lane)` record carries a `basis`:
  `recent_tasks` (computed from tasks in the window), `scan_observed_idle` (scan ran,
  no tasks, so healthy) or `scan_unavailable` (scan failed; `healthy` and failure
  counts are null).
- **Unobservable load:** if the task directory cannot be read, the routing budget
  publishes `in_flight: null` (`—` in the picker). It never publishes `0`. Unknown
  load is not idle: `idle_settle` needs `in_flight == 0` and explicit quota
  permission (`quota_ok: true` or a `verified` class) before it counts a lane as
  available.
- **Wave receipts:** the coordinator ledger `healthLane` records `healthy` as
  `true`/`false` when known, or `null` with a required `health_basis` when unknown,
  such as a scan error or a missing lane record. It also records the owner's
  `freshness` (`fresh`, `stale` or `unknown`). The wave is `fresh` only when
  `diagnostics.stale` is explicitly `false` and no relevant lane probe is stale;
  missing staleness metadata is unknown, never fresh.
- **Dispatch routing:** the budget substitution guard is retired. Select an
  explicit provider/model using current capacity evidence.

- **Reviewer resolver and wave gate:** a near-cap candidate keeps credit relief
  only when `credit_lane.published_credit_relief` re-decides it with
  `lane_credit_state` over the complete published lane record: snapshot
  staleness, probe freshness, age and stale flag, the raw balance and its fetch
  time, and runtime rate-limit evidence. A published `credit_balance_present`
  leaf alone is not enough.
- **Routing recommendation:** a past-cap lane is a credit candidate only when
  the owner's `routing_facts` for the record grant credit relief as verified
  capacity; the published `credit` leaf is not read.

## GitHub REST budget: who spends it

The shared GitHub client (`scripts/common/github_client.py`) counts every request it sends to
the REST core pool in a `usage` table of its own cache (`batch_state/github-client/cache.sqlite3`,
owner-only, rows kept six hours). A request's row is written in a short transaction of its own,
after the call's budget observation and cache writes committed; opening it and taking the write
lock together wait at most a quarter second, and counting never changes where the client keeps its
budget. Each row names the caller (the dispatched task id with its command, else
the calling command's module or script, never its arguments; for the `gh` shim, the command that
ran `gh`) and an endpoint template such as
`GET repos/:repo/actions/runs/:n`. The template is the route the path matches in a table of
GitHub's REST routes (`_ROUTES` in `scripts/common/github_usage.py`), so a repository, number, SHA, account,
team, branch, tag or label (a ref with slashes included) is replaced by the position it holds,
however it is spelled; a path no route matches keeps only its root (`repos/:repo/:other`). A native `gh` command with no readable request is named by its
known command words alone (`gh pr view`), never by an argument. Print the top consumers
of the last hour:

```bash
.venv/bin/python -m scripts.common.github_usage top            # --hours 3, --limit 50, --json
```

`charged` excludes `304` responses, which GitHub does not charge. A landing call (a PR merge,
review, update-branch or rerun) is never counted, so counting never adds a wait to the landing
path. A native `gh` command counts once, as charged, however many requests gh makes for it. A
write SQLite refuses drops its row rather than fail the call; the row follows the budget
observation, so it cannot cost it. The `usage` table is created by the count itself, never by the
client's ordinary cache access, so a cache from before this change is read and written exactly as it was.
A cache file SQLite reports as damaged, whether at open or mid-use, is set aside as `cache.sqlite3.corrupt`
and rebuilt, because without it every read is charged in full and budget observations stop reaching
other callers; the call itself continues in memory. Only the damaged file is moved, under a directory
lock a client never waits for: a fresh file another process already put in its place is left alone.

## Git hooks

Run `scripts/install_git_hooks.sh` once after cloning to install delegators in
`$GIT_COMMON_DIR/hooks` that delegate to the tracked `.githooks/` of the current
worktree. `core.hooksPath` stays unset so hook-installing tools cannot write into
tracked files. The delegators ensure the complete tracked hook chain is
shared across all linked worktrees without a per-worktree install. It runs the
configured pre-commit, commit-message, and pre-push gates; preserves the
pytest-stamp and Git LFS hooks; and restores the primary-checkout guards after
checkout or merge. The installer also materializes `.githooks` in existing sparse
worktrees without broadening their checkout. The Entire CLI integration was removed
(C-2928): the installer replaces any Entire wrapper still in the hooks directory with
the delegator, removes the Entire-only wrappers and the delegators it once placed at
`<name>.pre-entire`. It refuses, without changing anything, when a hook path is a
symlink. `scripts/install_git_hooks.sh --check` (read-only) fails when a hook stage
declared in `.pre-commit-config.yaml` has no reachable delegator, an Entire wrapper
remains (`RETIRED`), or a hook path is a symlink.

---

## Startup Wrappers

Project-local wrappers for interactive agent sessions:

```bash
./start-claude.sh      # native Anthropic Claude Code (original config)
./start-codex.sh       # native Codex
./start-grok.sh        # native Grok Build TUI
./start-gemini.sh      # native Gemini / Antigravity AGY Build TUI
./start-kimi.sh        # retired catalog ids; the wrapper refuses (OO-58)
./start-kimicc.sh      # retired catalog ids; the wrapper refuses (OO-58)
./start-glm.sh         # Claude Code routed to Z.AI GLM
./start-glmcc.sh       # same GLM route under the historical name
./start-claude-driver.sh --epic devops
./start-codex-driver.sh --epic devops
./start-grok-driver.sh --epic devops
```

Kimi models are retired (OO-58, #11327). Do not dispatch `--agent kimi` or start a Kimi model.
The bridge refuses every Kimi recipient, ask, inbox and discussion. Launcher names remain
so a short name resolves and is refused.

### Rules core loading

Every launcher starts its seat with the rules core
(`agents_extensions/shared/rules/core.md`; curriculum driver lanes add
`core-curriculum.md`), read offline by `scripts/lib/rules_core.py` through
`scripts/lib/rules_core.sh`. The core always comes from the checkout the code
runs from; no environment variable moves it. Claude Code routes get `--append-system-prompt`,
native Codex `-c developer_instructions=…`, Grok `--rules`; AGY, Cursor, OpenCode and Hermes
receive the core at the head of the initial prompt. A Kimi launcher exits 2 on the catalog
retirement before rules attachment, so it never starts a coding task. ACP calls
and legacy bridge prompts prepend the same block unless the prompt already
starts with it. Dispatch v2 checks core availability but does not prepend the
core or support rules-seat selection; the one exception is read-only Claude, which
gets the core as an appended system prompt (see the dispatch v2 section below). An absent, unreadable or empty core (or, for a content seat, addendum) refuses: a launcher exits 1 before
any adapter check or deploy, `dispatch.py dispatch` exits 2 before any check or task record, an ACP call raises
`InterAgentTransportError`, a discussion raises `AcpxDiscussionError` before admission, an `ask-*` prompt exits, and
the loader CLI exits 3; each message names the path. `LAUNCHER_DRY_RUN=1` prints the seat
and size; `LAUNCHER_DRY_RUN_ARGV_FILE=<path>` also writes the exact argv.

```bash
.venv/bin/python scripts/lib/rules_core.py --format json          # seat, bytes, first/last pillar anchors
.venv/bin/python scripts/lib/rules_core.py --lane core --format seat   # content
```

### Parallel routes and original Claude config

`start-codex.sh --harness claude-code` and
`start-glmcc.sh` / `start-glm.sh` route through process-scoped
configuration. They **never rewrite** the live `~/.claude/settings.json`. That means:

- `./start-claude.sh` always keeps the original Anthropic / Claude Code setup
- You can run native Claude and a routed provider in **parallel terminals**
- Tools like [cc-switch](https://github.com/farion1231/cc-switch) that pin
  `ANTHROPIC_*` into `settings.json env` will **block** these launchers until
  those keys are removed (or you use `--isolate-config` / `CLAUDE_CONFIG_DIR`)

### Codex through Claude Code

`start-codex.sh --harness claude-code` keeps Claude Code's interface while
routing Codex through the approved local CLIProxyAPI endpoint. The default
Codex harness remains native; use the Claude-Code harness only when its
interface is required.

```bash
./start-codex.sh --harness claude-code --model gpt-6.1-sol
./start-codex-driver.sh --governor AUTO
```

On macOS, install and connect CLIProxyAPI once before launching:

```bash
brew install cliproxyapi
brew services start cliproxyapi
cliproxyapi --codex-login
```

See the [CLIProxyAPI quick start](https://help.router-for.me/introduction/quick-start)
for upstream installation details.

The adapter uses `http://127.0.0.1:8317` and CLIProxyAPI's documented dummy
client token by default. `CODEX_CC_BASE_URL` is restricted to that local
endpoint; `CODEX_CC_AUTH_TOKEN` is process-scoped and never written to the
repository.

### Kimi through Claude Code

Retired (OO-58, #11327). `start-kimi.sh` and `start-kimicc.sh` remain so a short
name resolves, then the catalog refusal exits 2. There is no default Kimi model,
no KimiCC opt-in, and no headless `--agent kimi` route. Do not log in or point a
job at these wrappers. Historically the Claude Code UI reached Kimi models through
an isolated config and an explicit Kimi credential, never an ambient
`ANTHROPIC_AUTH_TOKEN`. Every Kimi catalog id now has empty transports.
See [`agent-seat-onboarding.md`](runbooks/agent-seat-onboarding.md).

### GLM through Claude Code (Z.AI)

`start-glmcc.sh` / `start-glm.sh` routes Claude Code to the Z.AI Anthropic-compatible
endpoint (`https://api.z.ai/api/anthropic`) per
[Z.AI Claude Code docs](https://docs.z.ai/scenario-example/develop-tools/claude).

```bash
./start-glmcc.sh                     # coding endpoint + isolated ~/.claude-glmcc
./start-glmcc.sh --endpoint platform
./start-glm.sh --model glm-5.3
```

**Credentials (first match wins):** `GLMCC_AUTH_TOKEN`, `ZAI_API_KEY`,
`ZHIPU_API_KEY`, `GLM_API_KEY`, then owner-only `~/.secret/zai.key`
(mode `0600` or `0400`). Override the file path with `GLMCC_SECRET_FILE`.
File-backed keys are loaded into process-scoped `ANTHROPIC_AUTH_TOKEN` only —
they are never re-exported as `ZAI_*`, never written to
`~/.claude/settings.json`, and never printed by dry-run. Ambient
`ANTHROPIC_AUTH_TOKEN` is deliberately rejected as a GLM credential.

Create the secret file once (avoid putting the key on the shell command line
or in shell history):

```bash
mkdir -p ~/.secret
touch ~/.secret/zai.key && chmod 600 ~/.secret/zai.key
${EDITOR:-nano} ~/.secret/zai.key   # paste the key alone, save, quit
```

The trusted `agents_extensions/codex/config.toml` overlay leaves the root model
and reasoning effort user-selectable while giving Codex App and CLI the same
Terra/medium V2 child defaults. Personal root defaults belong in
`~/.codex/config.toml`; task-specific choices come from the model picker or CLI
flags. `start-codex.sh` launches the CLI with:

- interactive Codex in dangerous bypass mode
- live web search; project config supplies Codex 0.145 multi-agent V2
- at most three project-configured spawned children (four active agents
  including the root), with Terra/medium as the default child route
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

Start a lease-bound Codex driver so the core claims the one lane lease before
the adapter's canary step and the injected `drive-epic` binding:

```bash
./start-codex-driver.sh --epic hramatka
./start-codex-driver.sh --epic atlas
./start-codex-driver.sh --epic harness
```

Interactive launchers reject `--epic`, so they cannot accidentally claim a
driver lease. The driver core validates the selector, exports the provider
handoff identity, claims the stream, runs a provider canary only where the
adapter has a semantic canary (otherwise reports `not run`), and only then
injects the `drive-epic` binding.

Override before launch if needed:

```bash
CODEX_DISPATCH_MODE=workspace-write CODEX_BRIDGE_MODE=safe ./start-codex.sh
```

For a repository created with `--separate-git-dir`, Git cannot recover the
primary checkout path from a linked worktree. In that uncommon layout, set
`CODEX_CANONICAL_REPO_ROOT=/absolute/path/to/main`; the launcher verifies that
the path is this repository's primary checkout (not a linked worktree) on the
`main` branch, then runs every launcher helper from it. Only Codex launches read
this override; it is the one accepted way to name a primary that Git cannot
prove from the worktree (#9121). When the repository records `core.worktree`,
the override must be that directory. Otherwise Git keeps no back-pointer to a
separate-git-dir primary, so another directory holding a copy of its `.git`
gitfile also passes: an operator who sets `CODEX_CANONICAL_REPO_ROOT` vouches
for that directory.

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

Rejects bare `python` and `python3` shell calls and prints one shell-quoted,
copyable command using the canonical checkout's `.venv/bin/python`.

### `check-agent-inbox.sh`

Checks the SQLite message broker for unread cross-agent messages for the current seat (`LEARN_UK_HOOK_RECIPIENT`, default `claude`) and surfaces them as additional context. A read-only, 1 s-bounded unread count short-circuits silently when the inbox is empty; any probe error falls back to the live bridge CLI. It skips during pipeline runs.

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

- `docs/projects/qg-quality-gate/schema.md`
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
  rebuild, since refetching costs Wikipedia API budget), the official
  DictUA cache, and every table whose name starts with `sum20_` (the
  official СУМ-20 articles, which cannot be re-imported). Pass
  `--no-preserve-wiki` to wipe the Wikipedia tables too; the DictUA cache
  and the `sum20_` tables are always kept.

### Recovery: when `data/sources.db` is empty or corrupt

If `data/sources.db` is found at 0 bytes or with broken schema (the
2026-04-25 wipe pattern), restore a versioned snapshot into an empty staging
directory. **Do not restore over live `data/` and do not run
`build_sources_db.py --force`**: that rebuilds from JSONL inputs which lack the
post-#1427 `ukrainian_wiki` table and the post-#1555 chunker policy.

```bash
# 1) List snapshots and preview a staging-only restore.
./scripts/backup-data.sh snapshots
./scripts/backup-data.sh restore latest \
  --to /absolute/path/to/empty-recovery-directory

# 2) Execute after checking the selected snapshot and target.
./scripts/backup-data.sh restore latest \
  --to /absolute/path/to/empty-recovery-directory \
  --execute

# 2b) Restore needs free space: the script measures the restore size first
#     and refuses (writing nothing) if the target filesystem has less than
#     size + LU_BACKUP_RESTORE_MARGIN_PERCENT (default 10). To restore just one
#     file or directory of the run (e.g. one database), add --path:
./scripts/backup-data.sh restore latest \
  --to /absolute/path/to/empty-recovery-directory \
  --path data/sources.db --execute

# 3) Verify the staged database. Row counts should be non-trivial.
sqlite3 /absolute/path/to/empty-recovery-directory/data/sources.db "
  PRAGMA quick_check;
  SELECT 'textbooks',         COUNT(*) FROM textbooks UNION ALL
  SELECT 'literary_texts',    COUNT(*) FROM literary_texts UNION ALL
  SELECT 'external_articles', COUNT(*) FROM external_articles UNION ALL
  SELECT 'wikipedia',         COUNT(*) FROM wikipedia UNION ALL
  SELECT 'ukrainian_wiki',    COUNT(*) FROM ukrainian_wiki;
"

# 4) Stop writers, preserve the damaged live database outside the project,
#    and copy back only the verified staged database. The backup script
#    deliberately does not overwrite live data.

# 5) Re-ingest any tables that were added AFTER the snapshot date.
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

# 7) Preview and create a fresh versioned snapshot.
./scripts/backup-data.sh backup
./scripts/backup-data.sh backup --execute
```

See `docs/runbooks/data-backup.md` for setup, integrity checks, exclusions,
and the complete restore drill.

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

On Linux, `services.sh` controls the loaded systemd user units for `sources`,
`api`, `work`, and `astro`, clears project-owned stray listeners, and reads logs
from the journal. If the user bus is unavailable, it refuses to launch an
unsupervised copy even when no unit file is found. The existing `monitor-pull`
timer restarts the api unit every five minutes after a pull. Never restart
`learn-ukrainian-loopback.target`:
its dependencies start all four services. On systems without these units,
`services.sh` retains its direct or launchd process management. Always use it
instead of ad-hoc `npm run dev`, `astro preview`, or `nohup`, which create port
drift and orphan servers.

| Service | Port | What it is |
| --- | --- | --- |
| `sources` | 8766 | MCP Sources Server (SQLite FTS5 — textbooks, dicts, literary, Wikipedia). Legacy alias: `rag`. |
| `api` | 8765 | **Ops API** (FastAPI) — `/docs`, `/api/contracts/routes`, `/api/orient`, state, fleet, work. Narrative: `docs/MONITOR-API.md`. |
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

> Public deploy is separate: the `deploy-pages.yml` GitHub Actions workflow retains
> manual `workflow_dispatch` for certified content, and automatically deploys a
> `main` push only when the diff since the last successful Pages deployment contains
> approved site code and no content drift. Running services locally never touches the
> live site.

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
| `agents_extensions/shared/rules/workflow.md` (`GET /api/rules`) | Core workflow rules for agent sessions |
| `agents_extensions/shared/rules/pipeline.md` | Build and validation workflow guidance |
| `agents_extensions/shared/rules/mcp-sources-and-dictionaries.md` | MCP sources and dictionary lookup rules |
| `agents_extensions/shared/rules/ukrainian-linguistics.md` | Ukrainian language quality rules |
| `agents_extensions/shared/phases/gemini/README.md` | Gemini phase map |
| `agents_extensions/shared/phases/gemini/v6-write.md` | Current write phase reference |
| `agents_extensions/shared/phases/gemini/v6-review.md` | Current review phase reference |
| `agents_extensions/shared/quick-ref/ACTIVITY-SCHEMAS.md` | Activity schema quick reference |
| `docs/agent-runtime-guide.md` | Agent runtime architecture |
| `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` | Module richness requirements |
| `agents_extensions/shared/consultation-queue/README.md` | Consultation queue format |

## Tool Inventory (Quick Reference)

### MCP sources tools

Full list: [`agents_extensions/shared/rules/mcp-sources-and-dictionaries.md`](../agents_extensions/shared/rules/mcp-sources-and-dictionaries.md). Core tools used daily:

- `mcp__sources__verify_word` - VESUM morphological check
- `mcp__sources__vet_vocabulary` - batched VESUM/CEFR/Russian-shadow vocabulary vetting (optional SUM-11 gloss)
- `mcp__sources__search_text` - textbook content search
- `mcp__sources__search_definitions` - SUM-11 explanatory dictionary
- `mcp__sources__search_style_guide` - Antonenko-Davydovych style guidance

### Deterministic audit checks

At `scripts/audit/checks/`:

- `cross_file_integrity.py` - vocabulary used in activities exists in vocabulary YAML
- `outline_compliance.py` - markdown section structure matches `meta.yaml` outline
- `activity_quality.py` - deterministic activity quality checks

Additional audit guardrails:

- `scripts/audit/lint_dispatch_brief.py` - dispatch brief `.venv/bin/python` worktree guardrail
- `scripts/audit/typesafe_citation_verifier.py` - fail-closed TypeSafe citation and source-grounding check (#8192): deterministic quote match, then one System One Choice; only `supports` at confidence ≥ 0.80 is an accept. CLI: `.venv/bin/python -m scripts.audit.typesafe_citation_verifier --input cases.jsonl --out receipt.json`
- `scripts/typesafe/client.py` - shared TypeSafe key load and `system_one` HTTP helper (`load_typesafe_api_key`, `system_one`); not a CLI
- `scripts/audit/atlas_source_census.py` - aggregate-only Word Atlas source intake census; public reports must not include raw source text, private paths, or candidate lemma lists
- `scripts/audit/atlas_entry_model_census.py` - aggregate-only Word Atlas entry-model census; separates reviewed article entries by `entry_type` from alias/form records
- `scripts/audit/atlas_source_entry_count.py` - aggregate-only Word Atlas source-corpus entry-demand census by finalized entry-model bucket; public reports must not include source text, private paths, filenames, or candidate lists
- `scripts/audit/lint_word_atlas.py` - read-only, advisory sense-first Word Atlas entry lint (#6437): LINT-001 `TRUNCATED_TEXT_CUTOFF` + LINT-002 `AMBIGUOUS_BARE_EN` + LINT-004 `UNVETTED_EN_SOURCE` + LINT-101 `MULTI_SENSE_UK_SINGLE_EN` + LINT-102 `POS_TRANSFORM_MISMATCH` against `senses[]`, plus LINT-003 `DRILL_SENSE_ID_MISSING` on practice bindings / optional `--practice-deck` shards; skips sense rules when entries lack sense data; exit 0 unless `--strict` (then exit 1 on findings); no CI gate wired yet
- `scripts/lexicon/teacher_deck.py refresh --docx <master.docx>` - one-command rebuild of the teacher-table practice deck (lesson ingest, table sync, shard + cloze, independent check, published-set swap); see [`docs/practice/teacher-deck-artifacts.md`](practice/teacher-deck-artifacts.md) (#8843); `record-review` folds a language-review result into the sentence ledger `site/src/data/lexicon-teacher-deck-withheld.json`
- `scripts/audit/check_teacher_deck.py` - independent structural checker for the teacher-table deck (Atlas sense/identity, same-slot distractors, fragment rules, withheld ledger); prints the eligibility matrix and residual lists
- `scripts/lexicon/admit_teacher_table.py` - local-only teacher-table Atlas admission and English-card enrichment; writes a separate staged manifest, private deltas, and a named VESUM residual ledger but never publishes
- `scripts/atlas/atlas_db.py` - rebuild `data/atlas.db` from the hydrated Atlas manifest, materialize the Astro article payload projection, and validate alias targets
- `scripts/atlas/fill_local.py` - Phase-1 offline local enrichment writer for `data/atlas.db`; reads local dictionary/cache data only and reports per-section before/after coverage
- `scripts/atlas/word_card_assembly.py` - pilot word-card `build`/`verify`/`rehearse` (#8981): assembles the frozen pilot units into host-only cards from cited ULIF/VESUM/PULS rows (derived ULIF forms authenticated against the held raw pages; build id over every consumed row and query), re-reads every locator, rehearses withdrawal and rollback; output is refused in the primary checkout and every sibling worktree; pass `--sources-db/--vesum-db/--atlas-db` as absolute paths; see `docs/atlas/word-cards/pilot-findings.md`
- `scripts/atlas/allocate_pilot_identities.py` - pilot identity allocation audit (#9402); `--append-holding` appends the `unsplit` holding senses the assembler needs (append-only, idempotent, #8981); `--apply` refuses to regenerate an existing allocation
- `scripts/lexicon/thin_page_report.py` - read-only thin-page report over `data/atlas.db` (#8313): per-entry thinness tier (`bare`/`thin`/`rich`), missing enrichment sections of all 18, and per-section × per-source fillable counts from `data/lexicon/slovnyk_cache/` and `data/sources.db` (`ulif_dictua_sections`); never parks or mutates entries. CLI: `.venv/bin/python -m scripts.lexicon.thin_page_report --json /tmp/thin.json`
- `scripts/lexicon/lesson_atlas_link_census.py` - read-only census of committed lesson `/lexicon/<slug>/` targets against the published search index and alias file (#8734). Classifies each slug as entry, unique alias, ambiguous, or dead. Does not generate links. CLI: `.venv/bin/python scripts/lexicon/lesson_atlas_link_census.py`
- `site/scripts/benchmark-atlas-db.mjs` - benchmark Atlas DB build, preload, and getStaticPaths mapping at current and synthetic sizes
- `scripts/audit/curriculum_qg_harness.py` - deterministic Ukrainian curriculum QG fixture harness; use it to calibrate B1-27, A1/A2 scaffolding, B1+ leakage, and seminar-register checks before changing QG behavior
- `scripts/lexicon/promote_teacher_lesson_intake.py` - promote reviewed private teacher-lesson intake into the Word Atlas (`--apply --write --report`); also has two standalone, `--vesum-db`-free modes: `--emit-membership` (fold every approved lemma with an existing Atlas route into curated-practice membership) and `--record-source-shape` (append a weekly source-shape checksum to the intake journal's audit trail). See [Teacher-lesson intake: weekly delta recipe](#teacher-lesson-intake-weekly-delta-recipe) below.

### Teacher-lesson intake: weekly delta recipe

The private teacher-lesson vocabulary source is a living document — the teacher keeps
appending rows. A "delta" batch is the set of headwords new since the last reviewed pass.
Two mistakes to avoid, both seen in practice (#7623):

1. **Diff the full document, not just the rows after the last known boundary.** A
   post-boundary-only diff (`--post-boundary-row`) misses edits or insertions made
   *above* the boundary between passes. Always compute triage buckets over the whole
   current document, then union all three buckets — `high_frequency_missing`,
   `post_boundary_table_missing`, **and** `needs_review_bulk` — into the delta. A prior
   pass took only the first two buckets and silently dropped `needs_review_bulk`; the
   operator flagged it. The practice tab only ever grows upward (older rows never move),
   so a full-document diff against the cumulative committed decision ledgers is always
   correct and never re-approves an already-reviewed row.
2. **Never commit the raw source.** Only derived, privacy-safe headword metadata
   (lemma + neutral locator, e.g. `private source unit N paragraph 1`) is committed —
   see `OMITTED_PUBLIC_FIELDS` in `scripts/audit/private_teacher_lesson_intake.py`.

```bash
SOURCE=/path/to/local/teacher-lesson-vocabulary.docx   # never committed; local-only

# 1) Checksum the current full document shape (safe to print/commit; no raw text).
.venv/bin/python -m scripts.audit.private_teacher_lesson_intake "$SOURCE" \
  --print-source-shape --source-shape-id private-teacher-lesson-vocabulary-YYYY-MM-DD-delta

# 2) Full-document bulk triage — all three buckets, not just post-boundary.
.venv/bin/python -m scripts.audit.private_teacher_lesson_intake "$SOURCE" \
  --bulk-triage --triage-out "$TMPDIR/atlas-private-teacher-lesson-bulk-triage.json" \
  --triage-report-out "$TMPDIR/atlas-private-teacher-lesson-bulk-triage.md"

# 3) Set-diff the triage lemmas against every lemma already approved in
#    registry/lexicon/source-inventory-review-decisions/*teacher-lesson*.yaml (cumulative,
#    not just the last batch) to get the new delta only, then hand-review and write:
#      - registry/lexicon/source-inventory/oneshot/private-teacher-lesson-vocabulary-<date>-delta.yaml
#      - registry/lexicon/source-inventory-review-decisions/<date>-teacher-lesson-delta-approve.yaml
#    Both commit the source-shape SHA-256 from step 1 in their notes for traceability.

# 4) Record the checksum in the intake journal's audit trail (append-only; never
#    touches promotion phase/tx_id).
.venv/bin/python -m scripts.lexicon.promote_teacher_lesson_intake \
  --record-source-shape <sha256 from step 1> \
  --source-shape-batch-id private-teacher-lesson-delta-<date> --report

# 5) Promote for real (needs a VESUM shadow db; see scripts/rag/build_vesum_shadow.py):
.venv/bin/python -m scripts.lexicon.promote_teacher_lesson_intake \
  --curated-inventory registry/lexicon/source-inventory/oneshot/private-teacher-lesson-vocabulary-<date>-delta.yaml \
  --vesum-db "$TMPDIR/vesum-shadow.db" --apply --write --report

# 6) Fold every approved lemma that already has an Atlas route (not just the newly
#    promoted heads) into curated-practice membership, recognition-only:
.venv/bin/python -m scripts.lexicon.promote_teacher_lesson_intake \
  --emit-membership site/src/data/lexicon-teacher-curated-membership.json \
  --decisions-in "$TMPDIR/atlas-private-teacher-lesson-decisions.yaml" \
  --manifest site/src/data/lexicon-manifest.json \
  --membership-in site/src/data/lexicon-teacher-curated-membership.json --report
```

Keep producer, review, promotion and membership consumption within one caller-owned
`TMPDIR`/`task_scratch` lifecycle; separate scratch invocations do not share implicit
artifacts. `TMPDIR` must be an existing absolute directory. Intake CLI omitted
output flags write nothing; API omitted outputs and promotion CLI defaults use
the current `TMPDIR`. Explicit paths override defaults, including `--plan-out`.
Review intake candidates into approved ledgers before promotion. The intake
review and promoter auto-merge JSON share a basename but have different schemas;
retain an intake copy with its explicit output override if needed. Promotion
consumes reviewed ledgers before replacing the candidate artifact. Candidate,
decision and plan files remain for consumers after return or failed gates;
the caller owns cleanup.

Step 6 matters even when step 5 promotes zero new heads: most approved lemmas already
have an Atlas route from an earlier batch or an unrelated source, and `--emit-membership`
is the only step that admits those into curated-practice recognition. It never gates on
gloss-fallback availability (unlike promotion), so it is stable across runs regardless of
local dictionary-cache state.

### Task-owned scratch for large ad-hoc runs (#8738)

```bash
# run a big producer inside a disposable, task-owned scratch directory
.venv/bin/python scripts/tools/task_scratch.py run --task-id atlas-8307-410k -- COMMAND [ARGS...]
# inventory / reclaim interrupted runs (the scheduled hygiene runner applies this)
.venv/bin/python scripts/tools/task_scratch.py recover [--apply]
# ad-hoc /tmp leak sweep (exact Atlas/QA legacy names drain; other atlas-*/qa-* are inventory only)
.venv/bin/python -m scripts.orchestration.tmp_leak_sweep [--apply]
```

`$LU_TASK_SCRATCH_DIR` (also `TMPDIR`) is the payload directory; it is removed on
exit, failure and interrupt. From a dispatch worktree, run the Atlas 410k example with
the primary checkout's interpreter, source DB and deck dir via an exported
`PRIMARY_REPO` (`run --help` prints the copyable form). Full contract and the Atlas
410k invocation: `docs/runbooks/worktree-cleanup.md` § Task-owned scratch.

### Host test slots (#10662)

```bash
# run a multi-process test command inside host test slots (caps -n at the slots held)
.venv/bin/python -m scripts.common.test_slots run -- .venv/bin/python -m pytest -n 4 -q tests/x.py
# who holds slots and who waits, by task (same data: GET /api/ops/v1/test-slots)
.venv/bin/python -m scripts.common.test_slots status [--json]
```

Use the test-slot wrapper for dispatch-worker pytest runs: v2 does not inject
the nested-pytest plugin. The pre-push gate runs no tests and holds none. A
waiting run prints `TEST SLOTS: waiting ... queue position N/M`. Settings, refusals and the
long-queue procedure: `docs/runbooks/test-slots.md`.

### Build pipeline entry point

`.venv/bin/python scripts/build/v7_build.py {level} {slug} --worktree` is the single end-to-end build entry point. It drives the write -> enrich -> review -> audit -> publish chain.

### Agent runtime

`scripts/agent_runtime/` is the universal adapter layer for the dispatchable agent
lanes. See [`docs/agent-runtime-guide.md`](agent-runtime-guide.md). Gemini-family
work uses AGY; the legacy Gemini CLI route is unsupported.

### Delegate to background workers

Use dispatch v2 for detached execution. Give every task an explicit provider and
model, a complete brief, and a dispatch worktree:

```bash
.venv/bin/python scripts/dispatch.py dispatch \
  --agent codex --model gpt-6.1-sol --effort high \
  --task-id example-task --prompt-file brief.md \
  --worktree --mode workspace-write --owned-path scripts/example.py
.venv/bin/python scripts/dispatch.py status example-task --run-nonce <nonce>
.venv/bin/python scripts/dispatch.py wait example-task --run-nonce <nonce> --timeout 60
.venv/bin/python scripts/dispatch.py list --status running
```

Use `read-only` for inspection and review. `--dry-run` prints the invocation
without starting a worker. `status-or-fail TASK` verifies a running task and its
supervisor identity; its exit codes are 0 for running, 1 for not running and 2 for
unavailable state. `cancel TASK --run-nonce NONCE` requests cancellation of that
specific run. Read the returned task ID and nonce before arming a wait.

A write task must produce a pushed branch or a verified merged PR to satisfy delivery.
Dispatch v2 terminal statuses are `done`, `failed`, `timeout`, `rate_limited`, `cancelled`, `crashed`, and
`no_deliverable`. Only `done` is success; other terminal statuses require driver
disposition. The briefed worker runs its chain to the end and nobody arms auto-merge. Landing and merge closeout follow
`agents_extensions/shared/rules/workflow.md`.

The dispatcher requires the local rules core to exist. It does not inject rules
or research pointers into the worker prompt, with one exception: a read-only
Claude run (`scripts/dispatcher/providers/claude.py` `build`) passes the rules
core to `claude` as an appended system prompt (`--append-system-prompt-file`),
because `--restricted` skips `CLAUDE.md`. Put the required instructions and
source locators in the brief. Research flags record metadata; they do not fetch
or deliver registry records. `--owned-path` records scope without a path-claim
queue. Check disjoint ownership before launch.

Resolve capacity with `scripts.fleet.capacity_pick` and `scripts.fleet.usage`.
Dispatch v2 has no budget substitution guard, pricing/cost telemetry, preflight
triage, lifecycle-file propagation, keep/force-worktree switches, repository
backfill, Cursor self-dispatch/DoR/dirty-primary gates, open-PR freeze, or Kimi
boundary hooks. Native Grok dispatch and the RB2 trail are retired. Use a supported
provider and model from the current catalog; dispatch Grok as
`--agent cursor --model grok-4.7-high` (`grok` is not an agent).

`--mode read-only` (the default) cannot edit the worktree on any provider. Each
provider's own CLI holds the lock: Codex `-s read-only`, Cursor `--mode ask`,
Muse `--disable-write --disable-shell`, Claude `dontAsk` with no blanket Bash
grant (only Claude Code's built-in read-only commands and `gh` reads run, and
redirects are checked against the Edit deny) under `--restricted`, so no user,
project or local settings file can add an allow rule, and OpenCode's
`OPENCODE_PERMISSION` rules (edits denied; bash limited to `git diff`, `git log`,
`git show` and `git status` with no redirect or `--output`). Hermes gives a
dispatched run no enforceable write lock, so read-only on it exits 2 with
`read_only_unenforceable` before anything launches. AGY has none of its own
either, so read-only AGY runs inside the dispatcher's bubblewrap boundary
(`scripts/dispatcher/agy_sandbox.py`): a read-only root, a private scratch home,
and a dispatcher-owned Sources relay that forwards only the read-only tools. It
exits 2 with the same refusal only on a host that cannot start that boundary
(not Linux, or no `bwrap`). Read-only runs on Claude and OpenCode cannot run
tests; use Codex when a read-only reviewer must execute them.

`--restricted` skips CLAUDE.md, so read-only Claude gets the rules core
(`agents_extensions/shared/rules/core.md`) through `--append-system-prompt-file`;
Claude-only notes that exist only in CLAUDE.md do not reach it. `--restricted`
still loads managed settings, which could widen the lock, so read-only Claude
also exits 2 with `read_only_unenforceable` when any managed source exists or
cannot be checked: the `/etc/claude-code` policy directory, a non-empty
`remote-settings.json` cache, a `claude doctor` report other than "not fetched"
for remote managed settings, or a host other than plain Linux.

**Accepted residual risk (F5, CTO decision C-2982, 2026-10-28).** `claude doctor`
reads user, project and local settings files that the `--restricted` launch
ignores, so an auth override in one of them could make doctor report "not
fetched" while the launch uses a stored Team or Enterprise login whose
server-managed policy widens the lock. This is accepted because neither host
Claude login can carry such a policy: both are individual Max accounts
(`oauthAccount.organizationType = claude_max`), and `/etc/claude-code` is
absent. Revisit before any Team or Enterprise login is added to this host.

Sparse worktrees use `SPARSE_EXCLUDE_DEFAULT` in `scripts/dispatcher/git.py`.
Re-include a tree explicitly with `--sparse-include DIR`, or use
`--full-checkout`. There are no sparse anchors or owned-path re-inclusions.
The environment contract is `scripts/dispatcher/environment.py`; do not assume
the retired launcher's extra exports or nested-pytest plugin injection.

For review, pass the exact branch/head, author model, profile and risk selected
by the reviewer resolver. Protected bound-review execution remains unavailable;
`--review-id`, `--attempt-id` and `--review-attempt` are dry-run-only. A plain
read-only dispatch does not supply protected isolation or Sources receipts.

Shared fixture and caller tests cover the surviving dispatch interface. PR CI
and merge-group CI provide the broader test proof.

#### Project Research Registry — orchestrator dispatch duty

Classify every task by functional role, task family, track and owned paths.
Pass known dimensions as `--research-role`, `--research-task-family`,
`--research-track` and repeatable `--research-owned-path` metadata. Omit unknown
values. Put relevant record locators in the brief and verify attributed
consumption separately. A metadata label is not evidence of delivery or use.

Task-record maintenance remains available through
`scripts.orchestration.stale_task_records`; it is separate from dispatch.

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

For state queries without builds, use the **Ops API** (`docs/MONITOR-API.md`;
live explorer `http://127.0.0.1:8765/docs`, contracts
`http://127.0.0.1:8765/api/contracts/routes`):
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
| `scripts/ci/check_issue_task_quality.py` | Advisory DoR/DoD field check for issue bodies (#7854) | `.venv/bin/python scripts/ci/check_issue_task_quality.py --issue N` |
| `scripts/audit/atlas_source_census.py` | Build aggregate-safe Word Atlas source planning counts | `.venv/bin/python scripts/audit/atlas_source_census.py --markdown-out docs/runbooks/word-atlas-source-census-planning.md` |
| `scripts/audit/atlas_entry_model_census.py` | Count reviewed Atlas entries by finalized `entry_type` bucket | `.venv/bin/python scripts/audit/atlas_entry_model_census.py --format markdown` |
| `scripts/audit/atlas_source_entry_count.py` | Estimate aggregate source-corpus Atlas entry backlog by finalized bucket | `.venv/bin/python scripts/audit/atlas_source_entry_count.py --include-ohoiko-private --markdown-out docs/runbooks/word-atlas-source-entry-count.md` |
| `scripts/audit/lint_word_atlas.py` | Advisory sense-first Atlas entry lint (LINT-001–004, LINT-101, LINT-102, #6437; exit 0 unless `--strict`) | `.venv/bin/python scripts/audit/lint_word_atlas.py --manifest path/to/manifest.json` |
| `scripts/audit/typesafe_citation_verifier.py` | Fail-closed citation grounding: quote must occur in the source, then one TypeSafe Choice (#8192) | `.venv/bin/python -m scripts.audit.typesafe_citation_verifier --input cases.jsonl --out receipt.json` |
| `scripts/typesafe/client.py` | Shared TypeSafe API-key load and System One POST (library, not a CLI) | import `load_typesafe_api_key` / `system_one` from `scripts.typesafe.client` |
| `scripts/lexicon/admit_teacher_table.py` | Locally admit a current teacher table and fill missing English cards; leaves VESUM failures in a private residual ledger | `.venv/bin/python -m scripts.lexicon.admit_teacher_table --extract path/to/current-table.json --manifest-in path/to/manifest.json --manifest-out batch_state/atlas/teacher-table/lexicon-manifest.staged.json --write` |
| `scripts/atlas/atlas_db.py` | Rebuild `data/atlas.db`, materialize article payloads, and validate public alias targets | `.venv/bin/python -m scripts.atlas.atlas_db --db data/atlas.db` |
| `scripts/atlas/fill_local.py` | Fill `data/atlas.db` with Phase-1 local Atlas enrichment rows | `.venv/bin/python -m scripts.atlas.fill_local --db data/atlas.db --report-json /tmp/atlas-fill-local-report.json` |
| `site/scripts/benchmark-atlas-db.mjs` | Benchmark Atlas DB build, preloaded payload read, and getStaticPaths mapping | `npm --prefix site run atlas:perf` |
| `scripts/audit/curriculum_qg_harness.py` | Run calibrated Ukrainian QG fixtures or scan one module into compact evidence | `.venv/bin/python scripts/audit/curriculum_qg_harness.py --fixtures tests/fixtures/curriculum_qg/fixtures.yaml` |
| `scripts/audit/ingest_ua_gec_gold.py` | Curate the small attributed UA-GEC gold fixture for the #2156 eval harness | `.venv/bin/python scripts/audit/ingest_ua_gec_gold.py --dry-run` |
| `scripts/audit/module_quality_audit.py` | Report surface and LLM-QG/compact evidence coverage by level | `.venv/bin/python scripts/audit/module_quality_audit.py --level b1 --format summary` |
| `scripts/audit/lint_session_state.py` | Check handoff docs for missing env-file references | `.venv/bin/python scripts/audit/lint_session_state.py docs/session-state/current.md` |
| `scripts/audit/lint_anti_menu.py` | Detect anti-menu sign-off prompts in markdown | `.venv/bin/python scripts/audit/lint_anti_menu.py --text docs/session-state/current.md` |
| `scripts/audit/decision_lineage.py` | Scan decision git backlinks | `.venv/bin/python scripts/audit/decision_lineage.py --decision-id ADR-008` |
| `scripts/audit/curriculum_manifest_canary.py` | SHA-256 integrity and drift canary for published curriculum; regenerates or verifies canonical file hashes | `.venv/bin/python scripts/audit/curriculum_manifest_canary.py {--check\|--write}` |
| `scripts/ci/ci_timings.py` | Measure per-event and per-job CI durations and merge-queue timings (#7174). BEFORE snapshot for the 2026-09-02 sweet-spot drive: [`docs/plans/2026-09-02-ci-sweet-spot.md`](plans/2026-09-02-ci-sweet-spot.md) | `.venv/bin/python scripts/ci/ci_timings.py --event merge_group --since 2026-08-22` |
| `scripts/ci/coverage_diff.py` | Compare lost executed lines and arcs in paired branch coverage reports from `coverage-ref.yml` (#11226, PR #11343). With `--baseline-data` it names the baseline tests covering each lost line/arc lists every deleted test covering a loss in non-dead production files (`candidate_tests`), picks a small `restore_set` from them with greedy set cover (within ln(n) + 1 of the minimum), and reports losses no deleted test covered as `unrestorable_identities` | `.venv/bin/python scripts/ci/coverage_diff.py baseline/coverage.json candidate/coverage.json --baseline-data baseline/.coverage --git-range <base>..<head>` |
| `scripts/ci/coverage_ref.py` | Record selected, completed, failed and crashed test IDs; combine valid branch data even after failures. `manifest.json` separates measurement `complete` from `tests_passed` and lists non-Python measured paths as non-reportable. Set `COVERAGE_REF_CONTEXTS=true` to retain pytest-cov per-test contexts | `.venv/bin/python scripts/ci/coverage_ref.py combine --input ci-artifacts/shards --output ci-artifacts/combined --sha <40-hex> --matrix-result success` |
| `scripts/ci/coverage_ref_environment.py` | Install coverage storage isolation in the disposable coverage-ref runner venv only. Source write guards remain active; never install in a shared interpreter | `.venv/bin/python scripts/ci/coverage_ref_environment.py` |
| `scripts.publish workflow-run` | Dispatch `coverage-ref.yml` with a required 40-hex `sha` and optional typed boolean `contexts`; other admitted workflows accept no inputs | `.venv/bin/python -m scripts.publish workflow-run --workflow coverage-ref.yml --ref main --inputs '{"sha":"<40 hex>","contexts":true}'` |
| `scripts/ci/split_tests.py` | Static duration-balanced split of test files across the CI pytest shards; pins `scripts/ci/history-tests.txt` (tests that need git history or fetch) to shard 1, the only full-history shard; `durations` refreshes `scripts/ci/pytest-file-durations.json` from a full run's JUnit | `git ls-files -- tests \| grep -E '/test_[^/]+\.py$' \| .venv/bin/python -m scripts.ci.split_tests split --shard 1 --of 16` |
| `scripts/ci/pytest_report.py` | CI whole-run check over every shard: file partition, executed tests, needs_artifact collected and skip sets; writes the tested-tree record | `.venv/bin/python -m scripts.ci.pytest_report --results ci-artifacts/shards --record ci-artifacts/tested-tree.json` |
| `scripts/ci/gate.py` | Validate event-specific CI results: PR admission includes full pytest collection; merge-group, nightly and manual events require the full suite. Green PR-run reuse is retired; the queue tests its real candidate | `.venv/bin/python -m scripts.ci.gate` |
| `scripts/ci/metadata_commit.py` | Merge queue: an empty-diff commit carrying the queue commit's metadata, so TruffleHog scans message, author and committer alone | run by ci.yml's `queue-metadata-scan` job |
| `scripts/audit/secret_scan_local.py` | Offline local TruffleHog scan (`tree` or full-history `history` mirror); console shows only totals and per-detector counts (no path, commit, line or value); raw JSON report 0600 in a new 0700 temp directory outside the repo; triage only through its `show-keys` and `count` subcommands. Runbook: `docs/runbooks/secret-scanning.md` (#9416) | `.venv/bin/python scripts/audit/secret_scan_local.py tree` |
| `scripts/ci/checks.sh` | Every lint/content-contract gate of ci.yml's Checks job; runs all, fails if any failed | `bash scripts/ci/checks.sh` |
| `scripts/projects/open_model_data/v4_mine_stem_controls.py` | Phase 3.3 STEM `PRESERVE` miner + polysemy typing (#8007). Receipts are hash-only; shards stay local. | `python -m scripts.projects.open_model_data.v4_mine_stem_controls --sources-db "$SOURCES_DB" --vesum-db "$VESUM_DB" --output-dir "$STEM_CONTROLS_OUT"` |
| `scripts/projects/open_model_data/quarantine.py` | Build or verify the sealed inventory of old-plan open-model artifacts (path, bytes, SHA-256, reason; #9607). Loaders refuse those paths through `paths.refuse_quarantined`. | `.venv/bin/python scripts/projects/open_model_data/quarantine.py verify [--data-root <checkout-with-data>]` |

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
`scripts/audit/qg_schema.py`, and writes `registry/ua-gec-gold/ua-gec-gold.json`
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

### `scripts/projects/open_model_data/v4_differential_soviet_miner.py`

Differential Soviet candidate miner and modern whitelist filter (ULDR Phase 3.4, #8008, Epic #6321). Ingests 7,152 entries with `sovietization_risk > 0` from `sum11` in `data/sources.db`, enforces an explicit 20th-century technical neologism whitelist (*програмування*, *комп'ютер*, *авіація*, *транзистор*), disambiguates network errors (`SOURCE_UNAVAILABLE`) from absent terms (`NOT_FOUND_WITHIN_VERIFIED_COVERAGE`), tags Soviet ideological realia, and rejects Skrypnykivka-only archaisms.

```bash
# Mine and adjudicate candidates
.venv/bin/python scripts/projects/open_model_data/v4_differential_soviet_miner.py

# Verify generated receipt and checksums
.venv/bin/python scripts/projects/open_model_data/v4_differential_soviet_miner.py --verify-only
```

### `scripts/projects/open_model_data/v4_verify_trajectory_claims.py`

Automated Chain-of-Thought (CoT) factual claim-verifier for Ukrainian linguistic reasoning trajectories (ULDR Phase 3.5, #8009, Epic #6321). Ingests trajectory JSONL records, parses reasoning steps, and grounds linguistic claims against local databases (`vesum.db` for lemma attestation, inflected forms count, tags, and living standard validity; `sources.db` for СУМ-11 headwords, volume citations, and definitions; `r2u_differential_cache.json` for 1920s Academy dictionary attestation; and `sources.db` `ulif_dictua_*` for orthographic register). Trajectories with ungrounded, fabricated, or miscounted claims are hard-rejected. Emits cryptographic verification receipts validated against `v1_cot_claim_verification_receipt.schema.json`.

```bash
# Run claim verification across input trajectories
.venv/bin/python scripts/projects/open_model_data/v4_verify_trajectory_claims.py

# Fast receipt and checksum integrity check
.venv/bin/python scripts/projects/open_model_data/v4_verify_trajectory_claims.py --verify-only
```

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
| `agents_extensions/shared/consultation-queue/*.yaml` | Pending proposals |
| `agents_extensions/shared/consultation-queue/applied/` | Approved proposals |
| `agents_extensions/shared/consultation-queue/rejected/` | Rejected proposals |

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
.venv/bin/python scripts/audit/lint_session_state.py docs/session-state/current.md
.venv/bin/python scripts/audit/lint_session_state.py --all   # explicit whole-directory audit
```

Known user-scoped paths that are expected but not committed live in
`scripts/audit/known_user_paths.yaml`. This check is also wired into pre-commit
for `docs/session-state/*.md`; the hook lints only the session-state files in the
commit, so a stale reference in an untouched file (written on another host) never
blocks an unrelated commit (#8354). `--all` remains for explicit/CI audits.

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

Claude, Gemini, and Codex coordinate through distinct primitives. Pick the right one for the job.

> **Authoritative sources:**
> - [`docs/runbooks/agent-seat-onboarding.md`](runbooks/agent-seat-onboarding.md) — **canonical ownership matrix** (`discuss` / `delegate` / fleet-comms / ACPX / Buzz deferred), formal CF separation, Kimi routes
> - [`docs/best-practices/agent-bridge.md`](best-practices/agent-bridge.md) — channel bridge mechanics, pinned context, include chains, bridge `discuss`
> - [`docs/best-practices/agent-cooperation.md`](best-practices/agent-cooperation.md) — agent roles, Green Team protocol, review discipline
>
> This section is a quick-reference index. For anything more than the examples below, read the authoritative docs.

### When to use which tool

| Need | Tool | Write access? |
| --- | --- | --- |
| Sustained topic-scoped discussion, multi-turn, pinned context | **`ai_agent_bridge post` / `ai_agent_bridge discuss`** (channel bridge) | No (Q&A only; **not** formal CF) |
| One-off drive-by question to another agent | **Legacy `ask-*` compatibility command** pending single-seat ACP cutover | No by default; opt-in via `--allow-write` only on legacy paths |
| Fire-and-forget execution — run code, commit, push | **`scripts/dispatch.py dispatch`** | Yes |
| Durable fleet coordination / topology | **`scripts.fleet_comms`** (`plane-status`, …) + **file dual-write handoffs** (authoritative in every plane mode) | Hand-off files only as existing lane diaries; never invent a third bus |
| Formal cross-family PR review | **Direct `ask-* --type review` + PR comment** (sealed `review-pr` / `publish-review-verdict` removed in #8520) | No (review evidence) |
| Structured 2-to-4-seat agent conversation | **ACPX adapters** for Codex, Grok (`acpx-grok-shadow`), Claude, Cursor, Pool, AGY/Gemini, GLM, and DeepSeek (never Kimi/K3; retired, OO-58; feature-flagged, default-off; not a coordination plane) | **No** (read-only/stateless; see onboarding runbook) |
| Buzz relay coordination | **Deferred** — not in this rollout | N/A |
| Watch a long-running process (builds, reviews) emit events — **Claude only** | **`Monitor` tool** (Claude Code built-in) | N/A |
| Watch a long-running process — **Gemini / Codex** | Shell-poll the Monitor API | N/A |
| Read project state (track health, failing modules, build status) | **Monitor API** — `http://localhost:8765` | N/A |

**Rules of thumb:**
- Channel-first for anything >1 turn. The pinned `context.md` eliminates re-pasting project setup on every round.
- Supported 2-to-4-seat `discuss` calls delegate to ACP; the command name is a
  compatibility surface, not a second provider-launch engine.
- `ask-*` remains a temporary compatibility path only until single-seat ACP
  and initiator/quota telemetry land. Do not add new provider launch logic
  there. `ask-gemini` is retired; AGY is the Gemini-family route.
- `ai_agent_bridge` is for **communication**. `dispatch.py dispatch` is for **execution**. Don't confuse them.
- **`discuss` is not formal review.** Use direct `ask-* --type review` + PR comment for CF (sealed `review-pr` / `publish-review-verdict` removed in #8520).
- Query `.venv/bin/python -m scripts.fleet_comms plane-status` — never hard-code a live plane mode.
- ACPX is the structured transport for supported bounded 2-to-4-seat panels;
  rollback is feature-flag off + native runtime. It is
  not a new coordination plane, and fleet-comms/file handoffs remain durable
  authority.
- Never run a polling loop to check a background task — use `Monitor` or the bash `run_in_background` completion notification.
- A local service that must intentionally outlive its launching task needs the
  [detached-session contract](runbooks/background-session-tasks.md); do not
  weaken process-group cleanup or keep its state in task `$TMPDIR`.

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
# AGY bridge — Ukrainian content review; bridge code reviews are refused.
# Native AGY admits low/medium risk code review through dispatch.py;
# high/critical, infra and security reviews exclude Gemini.
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-agy "Перевір наголос і відмінювання в curriculum/l2-uk-en/a1/hello.md." \
  --task-id issue-NNN \
  --review \
  --review-profile ukrainian \
  --to-model gemini-3.1-pro-high

# Codex — code / adversarial review
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-codex "Adversarial review for #NNN. Read {path}." \
  --task-id issue-NNN

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
# Default: AGY bridge call (not a code review)
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-agy "Quick check of the greeting in curriculum/l2-uk-en/a1/hello.md." \
  --task-id issue-NNN \
  --to-model gemini-3.1-pro-high

# Fast AGY one-off
.venv/bin/python scripts/ai_agent_bridge/__main__.py ask-agy "Quick one-off check." \
  --task-id adhoc-agy-check \
  --to-model gemini-3.8-flash-high

# Drain AGY channel inbox explicitly
.venv/bin/python scripts/ai_agent_bridge/__main__.py inbox run agy
.venv/bin/python scripts/ai_agent_bridge/__main__.py sync agy
```

> **Note.** You rarely call `ask-claude` from inside a Claude session — you already *are* Claude. It's the return path for AGY/Codex or for scripts routing work to Claude.

### Execution via `dispatch.py dispatch`

For write-access work (implement, commit, push). See [Delegate to background workers](#delegate-to-background-workers) above for the full command. **Not** a comms tool — use `ai_agent_bridge` or `ask-*` to discuss, `dispatch.py` to have the work done.

When the delegated task may edit files or run git commands:

```bash
.venv/bin/python scripts/dispatch.py dispatch --model <catalog-model> \
  --agent codex \
  --task-id issue-1383-smoke \
  --prompt-file /tmp/prompt.md \
  --worktree \
  --mode workspace-write
```

`dispatch.py status <task-id>` will include the `worktree_path` so operators can inspect or clean it up later.
Use `dispatch.py status-or-fail <task-id>` before reporting async task state from memory; it exits 0 only when the Monitor API confirms the task is currently running, exits 1 when the task is done/missing/stale, and exits 2 when the Monitor API is unreachable.

**Site dependencies.** A new dispatch worktree gets its own real `site/node_modules` made of hard links to a
content-addressed store in the primary checkout's `.git/dispatch-dep-store` (about 530 MB once, near zero per
worktree), so no `npm ci` is needed there. The store key covers the lockfile, `package.json`, project `.npmrc`,
local inputs, Node/npm versions, platform and the whole npm configuration; a miss installs once with `npm ci`
in a staging directory and a controlled environment (fixed locale and `PATH`, no ambient variables). Store files are read-only and hash-checked before every
reuse, because hard links share one inode: do not edit package files in place (`chmod` and an edit changes them
for every worktree holding that file). Before editing, patching or changing the permissions of package files,
run `site_deps detach [--path <dir-or-file under site/node_modules>]` to turn them into private copies.
`npm ci` or `rm -r` in a worktree is safe. A failure never blocks the task, and
`LEARN_UKRAINIAN_SITE_DEPS=off` skips the step. `.venv/bin/python -m scripts.dispatcher.site_deps
{ensure|status|prune|detach}` runs it by hand.

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

### Dispatch settle (Luna handoff)

`.venv/bin/python -m scripts.orchestration.dispatch_settle task --task-id <id> --push --open-pr` — heal zombie task state, release inactive write claims, optionally push/open PR. Formal CF stays orchestrator-owned. After closeout it evaluates the #6976 settle reminder when `--idle-snapshot-json` is supplied (`--dispatched` or `--disposition <code>`). Standalone: `.venv/bin/python -m scripts.fleet.idle_settle evaluate|report|admission`. `idle_settle report --since-hours 24` includes events recorded in the last 24 hours and events without a valid timestamp; without the flag it includes all events. `driver_breadth_report --enforce` uses its `--since-hours` window for tasks and idle events, failing on in-window MISSING/DISHONEST dispositions (never raw idle seconds).

## Private open-model-data review build (RB-1)

`.venv/bin/python -m scripts.projects.open_model_data.review_build {build|verify} --config "$TMPDIR/request.json" --out "$TMPDIR/rb1"`

Builds or re-verifies cited `review_only` records from host-local candidates and reviewed
component specifications. The `omd-review-request.v1` JSON descriptor supplies candidate
JSONL, catalog/register YAML paths, database store paths, per-component independent unit
queries and frozen counts, declarative bindings, and citation compatibility/role mappings.
See [the RB-1 design](projects/open-model-data/REVIEW_BUILD.md) and the `build.execute`,
`bindings` and `roles` module contracts for the extension interface. Real extraction and
attribution adapters ship with their components; the framework's synthetic adapter refuses
unmarked sources. `--help` includes required flags, outputs and exit codes.

All records, candidate accounting, attribution notices, metrics, manifest, README and error
tracebacks stay under `--out` (directories `0700`, files `0600`); repository paths, symlinks,
unsupported filesystems, unsafe ownership/modes and POSIX ACLs are refused. Console failures
contain only reason codes, record ids, component ids and hashed row keys. `verify` re-runs
all gates against pinned inputs and compares every artifact byte; it does not certify D2/D3,
training readiness or RB-1 delivery. No network calls or database writes are performed.

### Issue readiness and daily counts

- `scripts/ci/check_issue_task_quality.py`: `--issue NUMBER --repo OWNER/REPO
  --strict --json` checks DoR, canonical stable-ID DoD structure and live
  repository-qualified ancestry. `--body` and `--body-file` leave membership
  unchecked. Unchecked ACs pass structure validation; closeout proof is separate.
- `scripts/ci/comment_issue_task_quality.py`: issue-event entry point. Refetches
  current data, reconciles the existing bot marker, and records observation time.
- `scripts/orchestration/issue_quality_report.py`: prepares a daily counts-only
  fleet report. `--publish --sender devops` publishes persisted bytes to the
  epics channel. `--date YYYY-MM-DD` retries that day's immutable payload under
  ignored `batch_state/reports/`. Unknown or truncated sources stay incomplete;
  private issue data never enters the report. `scripts.publish read issue-count
  --repo OWNER/REPO` is the fixed independent open-count reader.
- `scripts/orchestration/install_issue_quality_report_timer.py`: `--check`
  compares daily user units; `--apply` installs safely and reloads systemd;
  `--apply --enable` also starts the timer. Run installation from the primary
  checkout after approval, not from a dispatch worktree.

See `docs/best-practices/task-quality.md` and issue #10565 for admission semantics.
