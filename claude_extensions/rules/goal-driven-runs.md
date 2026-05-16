# Goal-Driven Runs

<critical>

How to use `/goal` (bounded autonomous batch) vs `ScheduleWakeup`+`/loop` (cadence/polling). Encodes the kubedojo Option B convergence (2026-05-07 consult) + Claude Code 2.1.139 native `/goal` deltas (released 2026-05-11). Pinned by #1884.

## When to use which

| Need | Tool | Why |
|---|---|---|
| Bounded batch with a measurable predicate ("build 5 modules", "iterate until VESUM gate passes", "fix every red test in `tests/runtime/`") | `/goal` | One predicate, one termination condition, one transcript. Halt-on-success is explicit; halt-on-blocked is explicit. |
| Cadence / polling ("check build every 5 min", "watch PR until CI green", "monitor channel for replies") | `ScheduleWakeup` + `/loop` | No predicate — just "do this on a schedule." Sleeping is the work. |
| Long-running event stream (build logs, `ab channel watch --follow`) | `Monitor` tool | Stdout line → notification, ~zero context cost. NEVER `/loop` poll for this. |
| Hard-bug investigation, multi-file architectural refactor, anything requiring sustained reasoning over a single artifact | Neither — direct work, inline or via dispatch | `/goal` is for predicate-bounded batch, not for one big problem. |

## Status-line convention (MANDATORY)

Every `/goal` turn MUST end with a machine-parseable status line. Prose state descriptions ("I think we're almost done", "blocked for a few rounds now") are forbidden — they force the evaluator to infer state from narrative, which is fragile and gameable.

### Per-turn status

```
GOAL_STATUS turn=N/M blocked=N/M no_progress=N/M queue_head=<token>
```

- `turn=N/M` — current turn / max turns. Both integers. Pull `N` from a real counter, not a guess.
- `blocked=N/M` — consecutive blocked-rounds counter / abort threshold. A "blocked round" is one where the predicate did not advance AND no new work was unlocked. Reset to 0 when progress resumes.
- `no_progress=N/M` — consecutive no-progress counter / abort threshold. Distinct from `blocked` — "blocked" means hit a wall; "no_progress" means working but not measurably advancing.
- `queue_head=<token>` — short identifier for the next work item. Free-form but deterministic. If the queue is empty, use `queue_head=<empty>`.

### Terminal status

```
GOAL_DONE reason="<one-line>"
```

The reason MUST be the deterministic predicate result, not a vibe. Examples:
- `GOAL_DONE reason="all 5 modules audit-green per audit/INDEX.md"`
- `GOAL_DONE reason="VESUM gate passed: 0 errors in audit/vesum_check.txt"`

### Abort status

```
GOAL_ABORT reason="<why>" last_cmd="<command>" last_cwd="<dir>" last_output="<grep'd line>" next_action="<concrete>" queue_head=<token>
```

All six fields are required. `last_cmd` MUST be the literal command executed, not a paraphrase, and `last_cwd` is the directory it ran from — together they form the reproducer the human will run after reading the transcript. Examples:
- `GOAL_ABORT reason="blocked_rounds=3" last_cmd=".venv/bin/pytest tests/test_x.py" last_cwd="/Users/k/projects/learn-ukrainian" last_output="FAILED: assertion mismatch line 47" next_action="rebase against origin/main, re-run, file issue if still red" queue_head=fix-test-x`
- `GOAL_ABORT reason="no_progress=3" last_cmd="git log -1 --oneline origin/main" last_cwd="/Users/k/projects/learn-ukrainian/.worktrees/foo" last_output="0e97806d7 docs(handoff)..." next_action="confirm correct base branch, then resume" queue_head=verify-base`

### Wait status — for async-dispatch work

```
GOAL_WAIT signal=<watcher_id> reason="<why>" [eta_s=<int>]
```

Terminal-but-not-final. Use when the predicate cannot advance until an out-of-band event fires (a `delegate.py dispatch` lands, a PR's CI turns green, a long-running Monitor stream emits a specific event). The status-line evaluator and the project Stop hook (`claude_extensions/hooks/goal-driver-stop.sh`) treat this as legitimate suspension — NOT as a `no_progress` round.

- `signal=<watcher_id>` — short kebab-case ID matching either (a) a Bash `run_in_background` task name, (b) a `Monitor` tool subscription, or (c) a `/api/delegate/active` task ID. The next turn re-enters when this signal fires.
- `reason="..."` — quoted human reason ("Codex dispatch ETA 30 min", "PR #1930 CI awaiting merge").
- `eta_s=<int>` — optional integer ETA in seconds. Useful for the hook to size its watchdog timeout.

Example:

```
GOAL_WAIT signal=watcher-b6v1j-codex-dispatch-done reason="in-flight Codex dispatch — V7 MDX assembler ETA 30 min" eta_s=1800
```

This is the highest-leverage harness improvement (filed as #1933 wishlist item 1). For the V7 MDX shipping run on 2026-05-14 it would have saved ~30K context tokens by replacing ~40 empty `GOAL_STATUS no_progress=N/M` cycles with one `GOAL_WAIT` suspend + one resume turn.

**The goal prompt MUST reference these tokens explicitly** so any downstream evaluator (Haiku judge, log-grepper, regression-detector) reads from a fixed grammar, not from English-paraphrase guess. Example goal prompt fragment:

> *Halt the run when you can emit `GOAL_DONE reason="..."` with the predicate satisfied. Halt early with `GOAL_ABORT reason="..."` if `blocked` or `no_progress` reaches their thresholds. Every turn must end with a `GOAL_STATUS` line — no exceptions.*

## One-goal-per-session (MANDATORY)

Each `/goal` invocation = a separate `claude -p` (or `codex` interactive) process. Composing multiple goals in one session is forbidden:

- ❌ `/goal A` → success → `/goal clear` → `/goal B` — ambiguous transcript; resume-persistence breaks; the evaluator can't tell phase boundaries apart.
- ✅ `claude -p "/goal A ..."` → exit → new shell → `claude -p "/goal B ..."` — each transcript stands alone.

`--resume <SESSION_ID>` is allowed ONLY for warm-cache reuse of the SAME goal (e.g. continuing after a network blip). Resuming for a different goal is a bug.

## Dispatch ownership (anti-fabrication)

Code changes inside a `/goal` body are FORBIDDEN. The `/goal` driver writes orchestration text — it does not write code. Code changes ship via:

- `scripts/delegate.py dispatch ...` for execution (committing work, with worktree isolation enforced).
- `scripts/ai_agent_bridge/__main__.py discuss` for read-only consultation (no code change, just review).

Inside a `/goal` body, "I did X" without a quoted tool-output line is treated as hallucination, even if the claim happens to be true. Required evidence for common claims:

| Claim | Required evidence in the turn body (command + cwd + output) |
|---|---|
| "Tests pass" | command + cwd + `pytest` final summary line raw (`N passed in M.MMs`) |
| "Lint clean" | command + cwd + `ruff check` final line raw (`All checks passed!` or zero-error count) |
| "Commit landed" | command + cwd + `git log -1 --oneline` raw |
| "PR opened" | command + cwd + `gh pr view --json url` raw URL line |
| "Dispatch fired" | command + cwd + `delegate.py dispatch` final `task_id` line raw |
| "API healthy" | command + cwd + `curl /api/orient` `health.api: true` raw |
| **"Nothing to do / queue is empty"** | command + cwd + raw output proving the empty state. Examples: `git status --short` → empty (proves clean tree); `git diff --name-only origin/main..HEAD` → empty (proves no diff); `cat /tmp/work-queue.txt` → empty (proves queue exhausted); `ls failing/` → empty. **This is the anti-fabrication gap** — a model can claim "we're done" with no evidence and the evaluator has nothing to disprove. Forbid that pattern. |
| **"No-op turn / made no changes"** | command + cwd + `git diff` → empty AND `git status --short` → empty. Both, not one. |

The evidence requirement is `<command + cwd + raw-output>` as a triple, not a bare output snippet. A raw-looking line without the command that produced it can be ungrounded — fabricated outputs are usually well-formatted because the model learned the format, not the truth. Mirrors MEMORY.md #M-4 (Deterministic Over Hallucination).

The status-line tokens themselves count as "tool-backed" only when the counters they reference (turn number, blocked count, queue head) come from real state — usually a small shell loop maintaining a counter file (`echo "$((n+1))" > /tmp/turn.txt`), not from the model's running tally.

## On `GOAL_ABORT` — diagnostic dump

The final turn of an aborted goal MUST include:

1. The `GOAL_ABORT` line (per the schema above).
2. The last command run, verbatim — including the directory it ran from.
3. The last command's last 10 lines of output, in a code block.
4. The queue head at abort time (already in the `GOAL_ABORT` line, repeat in prose if useful).
5. The recommended manual next action — concrete enough that a human can execute it without re-reading the transcript.

The point is to make goal-abort recovery cheap. A bare `GOAL_ABORT reason="failed"` is worse than no abort line at all because it lies about being informative.

## Sizing the M cap

The `M` in `turn=N/M` is the abort threshold. Picking it by gut on the 2026-05-14 V7 MDX run went `30 → 40 → 50 → 60` mid-flight — under-sized, then over-sized after recovery. Use the auto-sizing formula instead:

```
M = clamp(15, queue_depth * 2 + 5 + async_waits, 200)
```

- **2 turns per queue item** — one to advance, one to verify. Tighter loses the verification turn (re-learns #M-4 "deterministic over hallucination").
- **+5 buffer** — per-run setup + the final `GOAL_DONE` turn + 1-2 retry slots when a verification fails on first attempt.
- **+1 per expected async wait** — out-of-band signal (CI green, dispatch land, PR merge). Defaults to 0; name a number when you know the goal will suspend that many times.
- **floor 15** — under 15 the counter stops being informative. Predicate work that small should ship without `/goal`.
- **ceiling 200** — anything bigger is a planning failure that should split into multiple goals.

For long-running async-heavy goals the operator can set the cap to dynamic — the predicate becomes the sole termination condition and turn count is unbounded. Pair with `GOAL_WAIT` for the suspends.

CLI:

```bash
.venv/bin/python -m scripts.goal_driver.size_cap --queue-depth 8 --async-waits 2
# → 23

.venv/bin/python -m scripts.goal_driver.size_cap --dynamic
# → infinity
```

## Terminal-status state cleanup

`GOAL_DONE` and `GOAL_ABORT` are **both** terminal and **both** clear hook state. Specifically, the project Stop hook (`claude_extensions/hooks/goal-driver-stop.sh`) maintains a per-session file at `.claude/goal-state/<session_id>.json` recording any pending `GOAL_WAIT` watcher. On detecting either terminal status the hook deletes that file so the next `/goal` invocation in the same session starts with a clean slate.

This closes the issue #1933 item 3 gap where an emitted `GOAL_ABORT` did not actually scrub the hook fingerprint — the next `/goal` could resume the dead watcher. **If you are emitting `GOAL_ABORT`, trust that the cleanup runs**: do not also try to delete the file manually inside the goal body.

## Claude vs Codex `/goal` — pick the right one

| Driver | Mode | Use for |
|---|---|---|
| `claude -p "/goal ..."` | Headless / non-interactive | **Autonomous orchestration** (the canonical case). Has Remote Control, has the overlay panel showing elapsed/turns/tokens, supports `--resume <UUID>` for warm-cache. v2.1.139+. |
| `/goal` (Codex TUI slash command) | Codex interactive REPL only | **Manual bakeoffs, interactive iteration** where the operator sits at the terminal. Typed INSIDE the Codex REPL — NOT a shell-level command. Verified against `codex-cli 0.130.0`: `codex help goal` fails; `codex /goal --help` only hits top-level help; the headless surface is `codex exec [PROMPT]` with no documented `/goal` flag. There is no `-p` handle for `/goal` on Codex today (`-p` on the `codex` CLI means `--profile`, unrelated). |

When the bakeoff or autonomous orchestration plan calls for `/goal` UNATTENDED, the answer is **Claude `-p "/goal ..."`** every time. The Codex TUI `/goal` is the wrong tool for that job today, regardless of whether Codex is otherwise the right model for the underlying work. When the Codex CLI ships a headless `/goal` surface, revisit this rule.

## Anti-pattern catalog

- ❌ **Prose state in lieu of status line.** "I've been blocked for a few rounds" without `blocked=N/M`. The evaluator can't grep prose reliably.
- ❌ **Counter inflation / deflation.** Reporting `turn=5/30` while really on turn 12 because the model lost track. Maintain a counter file (`/tmp/<task>-turn.txt`) and `cat` it into the status line.
- ❌ **`/goal clear` mid-session.** Phase boundaries get lost. Use separate `claude -p` calls.
- ❌ **Inline code edits inside a `/goal` body.** Dispatch to `delegate.py`. The goal driver coordinates; it does not write code.
- ❌ **`GOAL_DONE` with a vibe reason.** `GOAL_DONE reason="looks good"` is forbidden. The reason must be a predicate result deterministic enough to re-verify.
- ❌ **Missing `next_action` on `GOAL_ABORT`.** Without it, the human reading the transcript has to re-derive the recovery path. The whole point of abort is to make recovery cheap.
- ❌ **`ScheduleWakeup` loops watching for build output.** Use the `Monitor` tool — one stdout line, one notification.

## Sequencing notes

- Status-line convention is mandatory; wrapper script that auto-emits the line is optional and can ship later.
- v2.1.139 ships the `/goal` overlay panel — that's an operator UX layer, not a substitute for the status line. Both serve different consumers (overlay = human; status line = evaluator).
- This rule is checked-in / shared vocabulary. It supersedes any ad-hoc `/goal` conventions in earlier session-state files.

</critical>

---

*Codified 2026-05-12 per #1884. Origin: 2026-05-07 kubedojo Codex consult (Option B convergence) + 2026-05-11 v2.1.139 native `/goal` release. Companion rules: `claude_extensions/rules/workflow.md` (cold-start + handoff), `memory/MEMORY.md` #M-4 (deterministic-over-hallucination), `memory/MEMORY.md` #M-6 (orchestrator drive).*
