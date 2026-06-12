# Codex dispatch stall at the finalize step

## What broke
On 2026-06-12, **three** codex `delegate.py dispatch` runs in one session
(`atlas-finalize-all`, `atlas-heritage-fix`, `kaikki-ipa-etym-wiring`) each:
1. did the real work correctly (edits applied, manifest regenerated), AND
2. passed their own gates (pytest + ruff green, site built), THEN
3. **hung at the pre-submit / commit step** — the codex CLI sat in a `write_stdin` empty-poll loop
   (`{"chars":"", "yield_time_ms":30000}` repeated) waiting on an interactive shell session that never
   returned what it expected — and exited WITHOUT `git commit` / `git push` / `gh pr create`.

The `delegate.py` tracker kept the task at `status: running` with a **dead pid** (zombie). The
batch_state `*.stdout.log` was empty the whole time (codex streams to its own session JSONL, not to the
delegate wrapper stdout), so a Monitor on the batch_state logs would NEVER fire — matching MEMORY #M-8.

## Why
Two compounding causes:
1. **Codex's poll-loop:** when codex launches a long command in a backgrounded interactive shell and then
   polls it with empty `write_stdin`, it can wait indefinitely if the command's output doesn't terminate the
   way codex expects. The pre-submit checklist phase (running `rg sys.executable`, `git diff --name-only`,
   etc.) is where it stalled all three times.
2. **`--silence-timeout=0` removed the backstop.** The first run (`atlas-finalize-all`) was dispatched with
   `--silence-timeout 0` (the brief said "long + silent by nature"), so the runtime never killed the silent
   poll-loop — it ran ~75 min until the hard timeout. The later two runs used a non-zero
   `--silence-timeout 2700`, which **caught the stall cleanly** (`status: timeout` after 45 min idle) because
   codex's wrapper-stdout IS silent during the hang.

A secondary failure mode: while working the pre-submit checklist, codex **over-reaches** — `kaikki-ipa-etym-wiring`
"helpfully" rewrote `sys.executable → .venv/bin/python` in **5 unrelated test files** to satisfy the
"no `sys.executable`" checklist item, violating "every changed file is directly related to the task."

## Prevention
- **Always set a non-zero `--silence-timeout`** on long codex dispatches (e.g. 2700s). Codex's wrapper-stdout
  is silent during the poll-loop hang, so the silence timeout is the reliable catch. Never `--silence-timeout 0`.
- **Brief instruction:** tell codex to run regenerations as FOREGROUND blocking commands with an explicit
  `timeout`, NOT in a backgrounded interactive shell it polls.
- **Finalize-the-zombie** (orchestrator playbook when a codex dispatch reads `running` but pid is dead /
  session is parked at pre-submit):
  1. Confirm the work is in the worktree, uncommitted.
  2. Re-run the gates YOURSELF (#M-11 — don't trust the session's "gates green" claim).
  3. `git diff <base> HEAD --name-only` and **strip out-of-scope files** (codex's pre-submit cleanup creep).
  4. Commit (`X-Agent: codex`) + push + `gh pr create` yourself.
- Detecting the zombie: `delegate.py` says `running` but `ps -p <pid>` is dead; the codex session JSONL
  (`~/.codex/sessions/.../rollout-*.jsonl`) last records are `write_stdin` empty-polls + "still waiting…".

## Links
- Issue: #2985 (Word Atlas EPIC — the work these three dispatches were finalizing).
- Fix: `c060124a26` (PR #3042 — autopsy + INDEX entry landed with the session handoff).
- MEMORY #M-8 (orchestrator-active through dispatch lifecycle; agent-private JSONL, not batch_state logs).
- Session handoff: `docs/session-state/2026-06-12-claude-atlas-goatcounter-policy-kaikki.md`.
