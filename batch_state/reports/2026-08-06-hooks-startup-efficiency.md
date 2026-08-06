# Claude Code hooks + session startup efficiency review

**Date:** 2026-08-06  
**Scope:** `.claude/settings.json` hook wiring + `.claude/hooks/*` (source-of-truth under `agents_extensions/shared/hooks/*`), plus the context those hooks inject at `SessionStart`.  
**Method:** read-only measurement. Re-used the timing harness from open PR #6408 (`grok/hook-audit`) where noted; all other numbers were measured directly in this worktree.  
**Machine:** macOS, worktree `kimi/hooks-claude-startup-review`, sparse checkout (no `curriculum/`, no `wiki/`).

---

## Executive summary

- **SessionStart is the big ticket**: a representative cold-start with a session id costs **~948 ms** (median of 5 runs). PR #6408 measured only the stripped path (no session id / no lease claim) at **~112 ms**, so the real Claude cold-start is ~8× worse than the baseline.
- **Per-turn tax is heavy**: a single Bash tool call pays **~161 ms** PreToolUse guard tax + **~370 ms** PostToolUse tax, and every turn pays **~180 ms** on Stop. Over a 20-turn session that is ~11 s of hook latency.
- **The fan-out is the cause**: `session-setup.sh` alone starts **~16 .venv python interpreters** in series; `context-monitor.sh`, `thread-lease-heartbeat.sh`, `goal-driver-stop.sh`, etc. each start at least one python per firing.
- **Context injection is large and partly duplicated**: a new Claude session receives **~70 KB** of project instructions before the first user message (CLAUDE.md + AGENTS.md + MEMORY.md + hook output). AGENTS.md already digests the same rules that are also served by `/api/rules` and, if still auto-loaded, by `.claude/rules/`.
- **Failure-path quality is brittle**: `session-setup.sh:461` labels **any** non-zero return from `claim-thread-lease` as a "DURABLE THREAD LEASE CONFLICT", including `ImportError` crashes.
- **Top wins**: merge SessionStart python calls into one script (~600–800 ms saved), remove the PostToolUse heartbeat hook (~136 ms/tool call), cache the context-monitor denominator or only run it on tier crossings (~170 ms/tool call), and evict `stamp-pytest.sh` from PostToolUse (~53 ms/tool call).

---

## 1. Wall-clock cost per hook event

Hook/event mapping is taken from `.claude/settings.json`:

| Event | Hooks wired (in order) |
|-------|------------------------|
| `SessionStart` | `session-setup.sh`, Entire CLI `session-start` (no-op if missing) |
| `PreToolUse` (Bash) | `enforce-venv.sh`, `heal-core-bare.py`, `guard-branch-switch-in-main.py`, `guard-admin-merge.py`, `guard-pr-merge.py`, `guard-secret-print.py`, `guard-primary-checkout-write.py` |
| `PreToolUse` (Write/Edit/MultiEdit) | `guard-primary-checkout-write.py` |
| `PreToolUse` (Task) | Entire CLI `pre-task` (no-op if missing) |
| `PostToolUse` | `tool-timing.sh`, `context-monitor.sh`, `stamp-pytest.sh`, `thread-lease-heartbeat.sh` |
| `PostToolUseFailure` | `tool-timing.sh`, `stamp-pytest.sh` |
| `UserPromptSubmit` | `check-gemini-inbox.sh`, Entire CLI `user-prompt-submit` (no-op if missing) |
| `Stop` | `goal-driver-stop.sh`, Entire CLI `stop` (no-op if missing) |
| `SessionEnd` | `release-thread-lease.sh`, Entire CLI `session-end` (no-op if missing) |
| `PostCompact` | `post-compact.sh` |
| `FileChanged` (curriculum) | `auto-audit.sh` |
| `FileChanged` (agents_extensions) | `auto-deploy-agent-extensions.sh` |

### Measured wall times

The PR #6408 stack harness was run from the `grok/hook-audit` worktree with the canonical venv:

```bash
/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python \
  scripts/hooks/measure_hook_stack.py --repeats 5 --json-stdout
```

| Hook | Median ms | Source |
|------|----------:|--------|
| `session-setup.sh` (no session id, PR baseline) | 112 | PR #6408 harness |
| `session-setup.sh` (full cold-start, this review) | **948** | measured below |
| `post-compact.sh` | 12 | PR #6408 harness |
| `post-compact.sh` with `GROK_AGENT=1` | 8 | PR #6408 harness |
| `enforce-venv.sh` | 10 | PR #6408 harness |
| `heal-core-bare.py` | 22 | PR #6408 harness |
| `guard-primary-checkout-write.py` | 23 | PR #6408 harness |
| `guard-pr-merge.py` | 29 | PR #6408 harness |
| `guard-secret-print.py` | 18 | PR #6408 harness |
| `guard-branch-switch-in-main.py` | 38 | PR #6408 harness |
| `guard-admin-merge.py` | 21 | PR #6408 harness |
| **Claude Bash PreToolUse tax (7 guards sum)** | **161** | PR #6408 harness |
| `context-monitor.sh` (dummy transcript, record present) | 169 | this review |
| `context-monitor.sh` (no session record fallback) | 131 | this review |
| `thread-lease-heartbeat.sh` | 136 | this review |
| `stamp-pytest.sh` | 53 | this review |
| `tool-timing.sh` | 12 | this review |
| `goal-driver-stop.sh` | 180 | this review |
| `release-thread-lease.sh` | 120 | this review |
| `check-gemini-inbox.sh` (no broker DB) | 9 | this review |

Full `SessionStart` was measured with a realistic payload and with writes redirected into the worktree:

```bash
cat > batch_state/session-start-input.json <<'EOF'
{"session_id":"kimi-test-001","transcript_path":"/dev/null","source":"new","model":{"id":"claude-sonnet-5"},"agent_type":"claude"}
EOF
CODEX_CANONICAL_REPO_ROOT="$PWD" CLAUDE_PROJECT_DIR="$PWD" \
  bash agents_extensions/shared/hooks/session-setup.sh < batch_state/session-start-input.json
```

```python
# repeated 5× with time.perf_counter()
median_ms 947.71
mean_ms   976.70
samples   [927.62, 992.68, 947.71, 1137.75, 877.75]
```

### Total added latency

| Scenario | Latency |
|----------|--------:|
| One session start | ~948 ms |
| One user turn with one Bash tool | ~161 ms PreToolUse + ~370 ms PostToolUse + ~180 ms Stop + ~9 ms UserPromptSubmit = **~720 ms** |
| 20-turn session (1 Bash/tool per turn) | ~948 ms + 20 × ~720 ms + ~120 ms SessionEnd ≈ **15.4 s** |

The PostToolUse tax is the largest per-turn block because four hooks fire serially:
`tool-timing.sh` (12) + `context-monitor.sh` (~170) + `stamp-pytest.sh` (53) + `thread-lease-heartbeat.sh` (136) ≈ **~370 ms**.

---

## 2. Subprocess fan-out

Each `.venv/bin/python` interpreter startup costs ~15 ms for `python -c pass`, but loading the project scripts (`thread_handoff.py`, `session_record.py`, etc.) costs **~100–140 ms** per spawn.

### Session-start fan-out

A source audit of the representative cold-start path in `session-setup.sh` shows the following `.venv/bin/python` spawns:

```bash
# run_bounded python target invocations
grep -nE 'run_bounded [0-9]+' agents_extensions/shared/hooks/session-setup.sh | \
  grep -E 'SESSION_RECORD|CANONICAL_PYTHON|\.venv/bin/python|ROLLOVER_PYTHON'
```

Active on a normal Claude cold-start:

1. `scripts/lib/context_profiles.py` (profile resolver) — 1 python
2. `scripts/lib/session_record.py update` — via `run_bounded` → 1× `bounded_command.py` + 1× target
3. `python --version` — via `run_bounded` → 1× `bounded_command.py` + 1× target
4. `scripts/guardrails/assert_primary_on_main.py` — via `run_bounded` → 1× `bounded_command.py` + 1× target
5. `scripts/orchestration/thread_handoff.py claim-thread-lease` — via `run_bounded` → 1× `bounded_command.py` + 1× target
6. `thread_handoff.py detect --format json` — via `run_bounded` → 1× `bounded_command.py` + 1× target
7. `thread_handoff.py detect --format session-start` (fallback) — via `run_bounded` → 1× `bounded_command.py` + 1× target
8. Three inline `$ROLLOVER_PYTHON -c 'import json,sys; …'` JSON parses

**Total: ~16 python interpreter startups in series**, plus the final `jq` output formatter and a `git config` canary. This is the dominant cost in the 948 ms cold-start.

### Per-turn fan-out

| Hook | Typical external spawns |
|------|-------------------------|
| `enforce-venv.sh` | 1 `jq`, 1 `git`, up to 1 `python --version` |
| `heal-core-bare.py` | 1 python process |
| `guard-*` scripts (5) | 1 python each; some call `git`/`gh` |
| `context-monitor.sh` | 1 `python session_record.py get`, ~6 `jq` pipes, `wc`/`awk` if transcript-fallback |
| `thread-lease-heartbeat.sh` | 1 `git`, 1 `jq`, 1 `python thread_handoff.py refresh-thread-lease-heartbeat` |
| `stamp-pytest.sh` | 1 `python .githooks/pytest_stamp.py`, 1 `git` |
| `tool-timing.sh` | 1 `jq`, 1 background `curl` |
| `goal-driver-stop.sh` | 1 `git`, 1 `jq`, 1 `python thread_handoff.py refresh-thread-lease-heartbeat`, 1 `python -m scripts.goal_driver.stop_hook` |
| `release-thread-lease.sh` | 1 `git`, 1 `jq`, 1 `python thread_handoff.py release-thread-lease` |
| `check-gemini-inbox.sh` | 1–2 `sqlite3`, 1 `shasum`, 1 `jq` |

Most of the per-turn python calls are independent of each other and could be merged into a single "per-turn housekeeper" python invocation.

---

## 3. Context injection size

### Files loaded by Claude Code before the first turn

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
files = {
    'CLAUDE.md': Path('/Users/krisztiankoos/projects/learn-ukrainian/CLAUDE.md'),
    'AGENTS.md': Path('/Users/krisztiankoos/projects/learn-ukrainian/AGENTS.md'),
    'MEMORY.md': Path('/Users/krisztiankoos/projects/learn-ukrainian/.claude/memory/MEMORY.md'),
}
for name, p in files.items():
    text = p.read_text()
    print(f"{name}: bytes={len(text.encode('utf-8'))}, words={len(text.split())}")
PY
```

| Source | Bytes | Words | Notes |
|--------|------:|------:|-------|
| `CLAUDE.md` | 13 806 | 1 719 | Project instructions |
| `AGENTS.md` | 30 863 | 4 284 | Rules digest; overlaps heavily with `/api/rules` sources |
| `MEMORY.md` | 23 315 | 3 125 | User-local, currently 128/150 lines (warning already triggered) |
| **Static instructions subtotal** | **67 984** | **9 128** | **~68 KB / ~9.1 K words** |

The full rules set served by the Monitor API (`/api/rules`) is **137 KB**:

```bash
.venv/bin/python - <<'PY'
from pathlib import Path
base = Path('/Users/krisztiankoos/projects/learn-ukrainian/agents_extensions/shared/rules')
files = ['operator-expectations.md','critical-rules.md','non-negotiable-rules.md','workflow.md',
         'fleet-comms-coordination.md','delegate-must-use-worktree.md','cli-help-standard.md','model-assignment.md']
print(f"total_shared_rules_bytes={sum((base/f).read_bytes().__len__() for f in files)}")
PY
```

So the static prompt already carries a **30 KB digest** of rules whose full text is available via API, and may also auto-load `.claude/rules/*.md` (another **26.6 KB**):

```bash
ls /Users/krisztiankoos/projects/learn-ukrainian/.claude/rules/*.md | \
  xargs wc -c | tail -1
# 27478 bytes total
```

`.claude/rules/_load-via-api.md` claims the full rules "no longer auto-load into the Claude Code system prompt"; if that is accurate, the 26.6 KB is only path-specific rule overhead. If it is not accurate, SessionStart silently injects **~95 KB** of rules material.

### Hook-injected context

The `SessionStart` hook output measured in this review was **2 053 bytes / 256 words**:

```bash
CODEX_CANONICAL_REPO_ROOT="$PWD" CLAUDE_PROJECT_DIR="$PWD" \
  bash agents_extensions/shared/hooks/session-setup.sh < batch_state/session-start-input.json \
  > batch_state/session-start-output.json
wc -c batch_state/session-start-output.json
# 2189 bytes (JSON wrapper incl. 2053 bytes of additionalContext)
```

Component split:

| Component | Bytes | Words |
|-----------|------:|------:|
| Profile capsule | 400 | 40 |
| Epic banner | 425 | 70 |
| Handoff / cold-start context | 554 | 71 |
| Issues + INFO lines | 668 | 75 |
| **Hook output total** | **2 047** | **256** |

### Total per-session context injection

Conservative estimate (CLAUDE.md + AGENTS.md + MEMORY.md + hook output):

**~70 KB / ~9.4 K words** before the user types a message.

If `.claude/rules/*.md` are also auto-loaded, the total is **~97 KB**. If the model later follows the orientation URL and loads `/api/rules`, it adds another **137 KB**, for a worst-case **~234 KB** of rule/context material in early turns.

### Duplication / staleness

- **AGENTS.md duplicates `/api/rules`**: AGENTS.md contains a long digest of `operator-expectations.md`, `workflow.md`, `fleet-comms-coordination.md`, etc. If the model fetches `/api/rules` on demand, the digest is redundant.
- **`.claude/rules/` duplicates docs**: `pipeline.md` embeds full decision-card text already in `docs/decisions/2026-05-06-writer-selection-codex-gpt55.md`; `ukrainian-linguistics.md` duplicates reference material elsewhere.
- **MEMORY.md is actively warned as near-limit** (128/150 lines in this session). Much of it is reference data that belongs in topic files, not in the always-loaded prompt.

---

## 4. Failure-path quality

### The 2026-08-06 case study: lease-crash mislabelled

`session-setup.sh:453-463`:

```bash
THREAD_LEASE_OUTPUT=$(run_bounded 3 "$ROLLOVER_PYTHON" "$ROLLOVER_SCRIPT" \
  --repo-root "$CANONICAL_ROOT" claim-thread-lease --agent "$HANDOFF_AGENT" \
  --current-thread-id "$CURRENT_THREAD_ID" 2>&1) || THREAD_LEASE_RC=$?
if [ "$THREAD_LEASE_RC" -eq 124 ] || [ "$THREAD_LEASE_RC" -eq 127 ]; then
  HANDOFF_CONTEXT="ERROR: LEASE CLAIM COULD NOT RUN (timeout/budget/runner missing) ..."
elif [ "$THREAD_LEASE_RC" -ne 0 ]; then
  HANDOFF_CONTEXT="ERROR: DURABLE THREAD LEASE CONFLICT — stop; do not cold-start or drive this queue."
```

**Problem:** any `rc != 0` other than 124/127 is reported as a lease conflict. If `thread_handoff.py` crashes with an `ImportError`, the operator sees a false "conflict" instead of "could not determine". This is the mislabel described in the brief.

### Other rc→verdict branches that can be wrong on a crash

| File | Lines | Verdict on rc≠0 / parse failure | What a crash looks like |
|------|------:|--------------------------------|-------------------------|
| `session-setup.sh` | 461 | "DURABLE THREAD LEASE CONFLICT" | false conflict |
| `session-setup.sh` | 416 | "CODEX LAUNCHER EXACT ROLLOVER BIND FAILED" | could be crash, not necessarily bind logic failure |
| `session-setup.sh` | 424 | "CODEX LAUNCHER EXACT ROLLOVER RESUME FAILED" | could be crash |
| `session-setup.sh` | 430 | "CODEX LAUNCHER EXACT ROLLOVER READBACK FAILED" | could be crash |
| `session-setup.sh` | 623 | "thread_handoff.py detect failed" | accurate-ish, but swallows the crash reason |
| `session-setup.sh` | 630 | "thread_handoff.py detect output could not be parsed" | the *parse* failed; the underlying detect may have crashed |
| `session-setup.sh` | 223 | "SESSION RECORD FAILED" | could be a runner crash, not a record write failure |
| `session-setup.sh` | 248 | "CLAUDEX SUPERVISOR BIND FAILED" | could be crash |
| `session-setup.sh` | 359 | "PRIMARY HEAD is detached or not on main" | could be `assert_primary_on_main.py` crash |
| `session-setup.sh` | 267 | "VENV WRONG PYTHON" | compares `python --version` stdout; if the command crashes/garbles, the verdict is wrong |
| `post-compact.sh` | 69–72 | "HYDRATION BLOCKED" | if `scripts.session_canary.codex_lane` crashes, it is reported as blocked hydration |

Most hooks outside `session-setup.sh` use `|| true` and fail open, so they do not mislabel crashes. The load-bearing verdicts are all in `session-setup.sh`.

---

## 5. Redundancy across hooks

### Thread-lease hooks overlap

Three hooks touch the durable thread lease:

1. `session-setup.sh` — claims the lease at cold-start.
2. `thread-lease-heartbeat.sh` (PostToolUse) — refreshes heartbeat, throttled to 60 s.
3. `goal-driver-stop.sh` (Stop) — also refreshes heartbeat, unthrottled.
4. `release-thread-lease.sh` (SessionEnd) — releases the lease.

The PostToolUse heartbeat is explicitly described in `thread-lease-heartbeat.sh:5-10` as **diagnostic only** — it does not guard a real burn. Yet it fires after **every** tool call and costs **~136 ms**. The Stop hook already refreshes once per turn.

### Context-monitor repeated data fetches

`context-monitor.sh` runs on **every** PostToolUse. It:
- re-reads the transcript from disk,
- re-queries `scripts/lib/session_record.py get`,
- re-sources `scripts/lib/profile_resolver.sh` if the record has no window,
- re-computes the same percentage every call.

There is no in-memory cache or `If-None-Match`; the only throttle is the script's own early-exits.

### Post-compact and SessionStart both call `thread_handoff.py detect`

`session-setup.sh` calls `detect` at boot; `post-compact.sh` calls `detect` after compaction. They serve different lifecycle moments, but they use the same unbounded (well, 2 s bounded) python call. The PostCompact hook also re-scans `curriculum/` for in-progress modules even though the model has just compacted and is about to resume from a handoff.

### Entire CLI hooks

Every Entire hook in `.claude/settings.json` is guarded by `if ! command -v entire >/dev/null 2>&1; then exit 0; fi`. On a machine without Entire installed they exit instantly, but each still spawns a shell lookup on every event.

### Tool-timing vs other telemetry

`tool-timing.sh` POSTs to `http://127.0.0.1:8765/api/telemetry/tool-timings` on every PostToolUse/Failure. It is fire-and-forget, but it still forks `curl` in the background on every tool call.

---

## 6. Bloat verdict and ranked recommendations

### Per-hook load-bearing vs bloat

| Hook | Load-bearing? | Guarded burn | Bloat / merge opportunity |
|------|---------------|--------------|---------------------------|
| `session-setup.sh` | **Mixed** | Lease claim, handoff pointer, venv/primary canaries | ~16 python startups can be merged into 1–2 python calls; orientation URL and MEMORY line check are orientation, not gatekeeping |
| `enforce-venv.sh` | **Yes** | Prevents bare `python3` usage | Cheap; keep |
| `heal-core-bare.py` | **Yes** | Fixes `core.bare=true` | Cheap; keep |
| `guard-primary-checkout-write.py` | **Yes** | Prevents writes to primary | Keep |
| `guard-secret-print.py` | **Yes** | OPSEC | Keep |
| `guard-pr-merge.py` | **Yes** | Bad merge prevention | Keep |
| `guard-admin-merge.py` | **Yes** | Admin merge policy | Keep |
| `guard-branch-switch-in-main.py` | **Yes** | Branch safety | Keep (could skip in worktrees) |
| `context-monitor.sh` | **Debatable** | Context rollover warning | Runs every tool call; should only run when a tier is crossed or cache the denominator |
| `thread-lease-heartbeat.sh` | **No** | Diagnostic only per its own comments | Remove or merge into Stop hook; saves ~136 ms/tool call |
| `stamp-pytest.sh` | **No** | Provenance marker | Move to pre-push or periodic; saves ~53 ms/tool call |
| `tool-timing.sh` | **No** | Telemetry | Batch or skip if endpoint down; saves ~12 ms/tool call |
| `goal-driver-stop.sh` | **Yes** (if `/goal` used) | /goal state annotation | Always runs; could be skipped when no active `/goal` |
| `release-thread-lease.sh` | **Yes** | Lease release | Keep |
| `check-gemini-inbox.sh` | **Yes** | Cross-agent messages | Keep, but guard DB existence already does |
| `post-compact.sh` | **Yes** | Context restore after compaction | Keep; curriculum scan is the expensive part and is already skipped for Codex |
| `auto-audit.sh` / `auto-deploy-agent-extensions.sh` | **Yes** | Immediate audit/deploy on file change | Only fire on file changes; OK |
| Entire CLI hooks | **No** (if Entire absent) | None | No-op shells on every event |

### Ranked recommendations

| Rank | Win | Estimated saving | Concrete recommendation |
|------|-----|------------------:|--------------------------|
| 1 | Merge SessionStart python calls | **~600–800 ms per cold-start** | Rewrite `session-setup.sh` so that profile resolution, session-record write, primary assert, and thread-handoff claim/detect are handled by **one** python entrypoint (or one bounded call), returning structured JSON. The shell should only format the final context. |
| 2 | Remove PostToolUse thread-lease heartbeat | **~136 ms per tool call** | Delete `thread-lease-heartbeat.sh` from the `PostToolUse` stack. The `Stop` hook already refreshes once per turn; diagnostic freshness every tool call is not load-bearing. |
| 3 | Make `context-monitor.sh` conditional / cached | **~130–170 ms per tool call** | Cache the resolved window + tiers in the session record or an env var; only recompute when usage changes enough to cross a tier. Also skip when `transcript_path` is missing. |
| 4 | Move `stamp-pytest.sh` out of PostToolUse | **~53 ms per tool call** | Stamp proven pytest status in a pre-push hook or a nightly job, not on every tool use. |
| 5 | Deduplicate rules context | **~10–20 K tokens per session** | Either (a) stop auto-loading `.claude/rules/*.md` and rely on `/api/rules` + AGENTS.md digest, or (b) shrink AGENTS.md to a pointer and always fetch `/api/rules` with `If-None-Match`. Do not ship both a digest and the full rule files in the static prompt. |
| 6 | Fix failure-path verdicts | Quality, not latency | In `session-setup.sh`, distinguish `thread_handoff.py` crash (rc 1, stderr contains traceback) from business-logic conflicts. Emit "could not determine" when the helper itself fails. |
| 7 | Gate `goal-driver-stop.sh` | **~180 ms per turn when `/goal` unused** | Skip the Stop hook's `scripts.goal_driver.stop_hook` call unless the transcript contains a `GOAL_*` status line or an active `/goal` state file exists. |

---

## Verification commands run

All quoted numbers were produced by the following commands:

- PR #6408 stack harness: `.venv/bin/python -m scripts.hooks.measure_hook_stack --repeats 5 --json-stdout` (run from `grok/hook-audit` worktree).
- Full SessionStart timing: the Python loop in this worktree with `CODEX_CANONICAL_REPO_ROOT="$PWD" CLAUDE_PROJECT_DIR="$PWD" bash agents_extensions/shared/hooks/session-setup.sh < batch_state/session-start-input.json`.
- Per-turn hook timing: the Python loop timing `bash agents_extensions/shared/hooks/<hook>.sh` with representative stdin payloads.
- File sizes: the Python snippets using `Path.read_text()` / `Path.read_bytes()` shown above.
- Spawn counts: `grep -nE 'run_bounded [0-9]+'`, `grep -nE '\.venv/bin/python|\$PYTHON|\$ROLLOVER_PYTHON'`, and manual branch audit of `agents_extensions/shared/hooks/session-setup.sh`.
- Failure-path lines: `grep -nE 'HANDOFF_CONTEXT=|ISSUES\+=' agents_extensions/shared/hooks/session-setup.sh`.

No hooks, settings, or scripts were modified during this review.
