# Dispatch brief — #1737 second-pass (broader code review + dead-feature removal + structural fixes)

**Status:** FIRED 2026-05-06 (~14:35 CET) — first-pass landed in PR #1739, branch `codex/1737-api-stability`.

**Context for the dispatched agent:** The first pass on #1737 (`1737-api-stability`, PR #1739, branch `codex/1737-api-stability`) produced an audit doc + fixed the top-5 stressing endpoints. Read these FIRST:
- `docs/api-stability-audit-2026-05-06.md` — endpoint × dashboard matrix, ranked stressors, server findings
- `docs/best-practices/local-api-server.md` — hardening guide
- `tests/test_playground_api_stability.py` — existing smoke test (extend it)
- The 8 modified files in PR #1739 — DON'T redo their fixes

User's explicit ask (verbatim, 2026-05-06 ~14:20 CET):

> "the api is crashing like a boss, need you to take care of 1737, there might be features we don't need anymore, the whole code needs to be reviewed and fixed"

This is a **broader, structural** follow-up — go beyond patching the worst 3 endpoints.

---

## Worktree instructions (mandatory)

```bash
git fetch origin
git worktree add -b codex/1737-api-review .worktrees/dispatch/codex/1737-api-review origin/codex/1737-api-stability
cd .worktrees/dispatch/codex/1737-api-review
# work, commit, push
gh pr create --title "..." --body "..." --base codex/1737-api-stability
```

Do NOT branch in the main checkout. Worktree path: `.worktrees/dispatch/codex/1737-api-review`. Branch: `codex/1737-api-review`. Base: `origin/codex/1737-api-stability` (PR #1739 first-pass tip — gives you the audit doc as input). The PR opens against `codex/1737-api-stability` so it stacks; once #1739 merges, retarget the second-pass PR to `main`.

**MANDATORY commit/push/PR steps (the first pass forgot these):**
1. `git add` your work
2. `git commit -m "..."` (commit hooks will run ruff + targeted pytest)
3. `git push -u origin codex/1737-api-review`
4. `gh pr create --title "..." --body "..." --base codex/1737-api-stability`
5. Reply with the PR URL in your final response

If you finish writing code but skip step 2-4, the work is lost — Claude has to salvage your worktree. Don't make that mistake again.

---

## Scope

The local API server (`scripts/api/`) currently has **26 routers** and the UI has **18 playground HTML files**. The first pass tightened SQL on the worst endpoints. This second pass asks two questions for every piece of that surface:

1. **Is this code still doing real work?** If a router has no consumer, or a playground isn't linked from anywhere, it's a candidate for deletion.
2. **Why does the server keep dying?** The first-pass fix was tactical. The second pass identifies the *systemic* cause: single-worker uvicorn? unbounded queries? blocking sync handlers? memory leaks? FD leaks? — and fixes the architecture, not just the symptom.

---

## Acceptance criteria

### AC1 — Endpoint × consumer matrix (`docs/api-endpoint-consumer-map-2026-05-06.md`)

For every route exported by `scripts/api/*_router.py` (and `scripts/api/main.py`), produce a table:

| Route | HTTP method | Router file | Consumer(s) | Last touched | Verdict |
|---|---|---|---|---|---|
| `/api/comms/inbox` | GET | `comms_router.py` | `playgrounds/comms.html`, `MEMORY.md` rule #0C bootstrap, `scripts/ai_agent_bridge/__main__.py` | 2026-05-06 | KEEP |
| `/api/...` | … | … | … | … | KEEP / DEPRECATE / DELETE |

How to find consumers:
- `grep -r "fetch.*'/api/<route>'" playgrounds/`
- `grep -r "/api/<route>" scripts/`
- `git log --diff-filter=A -- scripts/api/<file>.py` for "last touched" / "added when"

`KEEP` = at least one active consumer.
`DEPRECATE` = used by exactly one consumer that itself is dead/stale.
`DELETE` = zero consumers.

### AC2 — Playground × usefulness matrix (same doc, second table)

For every `playgrounds/*.html`:

| File | Linked from index.html? | Last visited (mtime / git log) | Functional today? | Endpoints used | Verdict |
|---|---|---|---|---|---|
| `index.html` | n/a (root) | … | yes | … | KEEP |
| `comms.html` | yes | … | yes (channels.html supersedes for chat?) | … | KEEP / REDUNDANT / DELETE |

`Functional today?` = open it in a browser via `curl localhost:8765/playgrounds/<file>` (or `mcp__claude-in-chrome__navigate`) and check if it loads + the endpoints it calls return 2xx.

### AC3 — Dead-code candidates list (audit doc, third section)

From AC1 + AC2, produce a `## Candidates for deletion` section listing every router file + every HTML file marked `DELETE` or `DEPRECATE`. Include:

- File path
- LOC
- Why it's dead (no consumer / superseded by X / experiment never adopted)
- Risk level if deleted (low / medium — anything potentially-medium needs user signoff)

**DO NOT delete in this PR.** Listing only. User reviews the list, approves specific files, then a *third* dispatch executes the deletions. (Reason: silent feature deletion via an audit PR is hostile.)

Exception: if a file is *obviously* dead (no consumer, no test, no doc reference, last touched >60 days ago, AND no CHANGELOG / decision-card mention) — you may delete it in this PR, but call it out clearly in the PR description so the user can revert if surprised.

### AC4 — Structural-cause diagnosis (audit doc, fourth section)

Find the architectural reason the server keeps dying. Not "endpoint X had a slow query" — that's a symptom. Look for:

- **Single-worker uvicorn** — one slow handler stalls everything. Check `scripts/api/main.py` startup config + how `npm run api` / equivalent launches it.
- **Sync DB calls in async handlers** — blocks the event loop. Grep for `sqlite3.connect` / `cursor.execute` in `*_router.py`.
- **Unbounded SELECTs** — anything without `LIMIT` / pagination. The first pass fixed top 3; find any others.
- **N+1 queries** — handler that loops over a parent and queries per child.
- **Memory leaks** — global caches that never evict. Grep for module-level dict / list assignments that grow without bound.
- **FD leaks** — `open()` without context manager, DB connections not closed.
- **CPU-bound work in handlers** — anything like JSON-parsing 10MB blobs, regex over large strings, etc., that should be in a thread/process pool.

For each cause found, a one-paragraph diagnosis + concrete fix recommendation (file + line + proposed change).

### AC5 — Resilience layer (code, in this PR)

Implement at least three of these (Codex's choice based on what AC4 surfaces):

1. **Per-request timeout middleware** — every handler wrapped with `asyncio.wait_for(handler, timeout=N)`. Returns 504 on timeout instead of hanging the worker.
2. **Concurrency limiter middleware** — bound concurrent in-flight requests per worker. 503 with `Retry-After` when saturated.
3. **DB connection pool with bounded size** — replace ad-hoc `sqlite3.connect()` calls with a pool. Configurable max connections.
4. **Slow-query log** — warn-log any DB call >500ms with the query + caller. Surface in `/api/state/health`.
5. **Watchdog** — separate thread/process that tails server health every N seconds; if 3 consecutive failures, restart the server. Optional — implement only if user signs off (touches process model).

Each one comes with: implementation, unit test, smoke test that proves it triggers under simulated load.

### AC6 — Tests + docs

- All existing tests pass (`.venv/bin/pytest scripts/api/`).
- New tests for each resilience-layer item (AC5).
- New tests for any router-level fix (AC4).
- `docs/best-practices/local-api-server.md` updated:
  - Recommended uvicorn config (worker count, timeouts, limits)
  - Architecture overview (which routers exist + their purpose)
  - "How to add a new endpoint without making the server fragile"
  - "How to deprecate / remove an endpoint cleanly"

### AC7 — Smoke test suite (extending AC4 from first pass)

The first pass adds one smoke test. Extend it: every dashboard's primary load (open + first 3 user actions) is exercised, the server's `/api/state/health` stays green, and the test fails loudly if any single endpoint exceeds a 500ms p99 budget.

---

## Coordination notes

- **First-pass PR is your base.** Rebase on whatever ships there; don't redo its work.
- **Don't fight #1736 (`codex/1736-comms-fix`)** — same broker DB, but you're operating one level up. If conflicts arise on broker-table indexes, use `CREATE INDEX IF NOT EXISTS` and let the merge be additive.
- **Cap discipline:** Codex cap is 2. Wait for at least one of (`1736-comms-fix`, `1737-api-stability`) to free before this fires.

---

## Effort + tooling

```bash
.venv/bin/python scripts/delegate.py dispatch --agent codex \
  --mode danger --worktree --base origin/main \
  --task-id 1737-api-review --effort high \
  --prompt-file docs/dispatch-queue/2026-05-06-1737-followup-brief.md
```

(`--effort high` because this is a deep review pass, not a one-line fix. NOT `xhigh`/`max` — those are reserved for adversarial Claude reviews per `claude_extensions/rules/model-assignment.md`.)

---

## Out of scope

- Fixing other open bugs (#1708, #1710, #1707, #1701, #1702 — those have their own dispatches in the afternoon queue)
- New features
- UI redesigns
- Adding routers / dashboards
- Migrating from sqlite to anything else
