# Codex CLI — `ab discuss` read-only enforcement (#1821)

## TL;DR

`ab discuss` is supposed to be deliberation-only. On 2026-05-09 morning, **round 2 of thread `33d8893f` modified the working tree** — agents wrote `scripts/api/docs_router.py`, `scripts/docs/migrate_to_html.py`, and 9 HTML files. Policy invariant broken. Live channel post captured the violation: *"🚨 DISCUSSION READ-ONLY VIOLATION."*

Make `ab discuss` runtime-enforce read-only across all three agents (Codex / Claude / Gemini), plus a post-round git-diff guard for the agent that doesn't have a native flag.

Full spec: **GH issue #1821** — read it first, every AC must be ticked.

---

## Mandatory orientation (#M-4 — deterministic over hallucination)

Before any code, read these (use the `/artifacts` route on `localhost:8765` for the HTML versions):

1. **`docs/best-practices/deterministic-over-hallucination.md`** — TOP-PRIORITY rule landed in commit `653ffe39e9`. Every verifiable claim you make in the PR description, commit messages, or test assertions MUST be backed by a tool call. No prose claims like "this should work" — only "I ran X, output was Y, attached as evidence."
2. **GH issue #1821** — `gh issue view 1821` — full ACs.
3. **`docs/best-practices/agent-bridge.md`** — current `ab discuss` semantics.
4. **`scripts/ai_agent_bridge/__main__.py`** — bridge implementation. Trace `discuss` end-to-end before touching anything.
5. **`MEMORY.md` `#M-0.5`** (no admin-bypass) and **`#0`** (orchestrator-only execution path) — same family of rules.

## Verifiable claims this work will produce + the tool for each

| Claim | Tool to verify | Evidence format |
|---|---|---|
| "Codex CLI accepts `--mode read-only`" | `codex --help` (you are the colleague — confirm) | Quoted CLI help output in commit body |
| "Claude headless write tools were disabled" | Check the dispatch invocation flags + run a test agent that tries `Write` and observes refusal | Quoted test output |
| "Gemini lacks native read-only mode" | `gemini --help`, ask via `ab ask-gemini` if unclear (per `#M-3` — don't assume colleague capabilities) | Quoted CLI help + bridge round-trip |
| "Post-round git-diff catches violation" | Run a test discussion where one agent attempts a write; assert `git diff --quiet` fails and the discussion summary marks `READ_ONLY_VIOLATION` | Pytest output |
| "Test passes" | `.venv/bin/pytest tests/<new test file>` | Quoted pytest output |
| "Ruff clean" | `.venv/bin/ruff check scripts/ai_agent_bridge/ tests/` | Quoted output |

If you find the bridge has a different control surface than the issue assumes, document it and propose the closest faithful enforcement. Do NOT silently re-scope.

---

## Worktree instructions (mandatory — `delegate-must-use-worktree.md`)

You will be invoked via `delegate.py dispatch --agent codex --mode danger --worktree`. The worktree is created at `.worktrees/dispatch/codex/codex-1821-ab-discuss-read-only/`. **All work happens there.** Do NOT branch in the main checkout.

Branch name: `codex/1821-ab-discuss-read-only` (auto-derived). Base: `origin/main`.

After your push lands the PR, the orchestrator (Claude) cleans up:
```
git worktree remove .worktrees/dispatch/codex/codex-1821-ab-discuss-read-only
git branch -d codex/1821-ab-discuss-read-only
```

---

## Workflow (numbered — execute in order)

1. **Worktree setup** — confirmed by the dispatcher; verify `pwd` is the worktree, branch is `codex/1821-ab-discuss-read-only`, base is `origin/main`.
2. **Read the issue** — `gh issue view 1821`. Note every AC checkbox.
3. **Trace `ab discuss` end-to-end** — `scripts/ai_agent_bridge/__main__.py`, find the function that runs `discuss`, identify the per-agent invocation point.
4. **Confirm per-agent flags exist** — query `codex --help`, `claude --help`, `gemini --help`. Document in your PR body what each agent supports natively.
5. **Implement the read-only enforcement:**
   - Per-agent: pass the native read-only flag where supported (Codex `--mode read-only`, Claude headless without write permissions).
   - Gemini: post-round audit — capture `git diff --stat HEAD` before each round, after each round; if changed, mark `READ_ONLY_VIOLATION: gemini` in the discussion summary.
   - Don't break legitimate channel-post (the agent's reply text) — only filesystem writes.
6. **Tests** — at minimum:
   - One test where an agent attempts a write → blocked or violation surfaced.
   - One test where the agent posts a normal reply → still works.
   - Place tests under `tests/test_ab_discuss_read_only.py`. Use existing test infra; don't invent a parallel runner.
7. **Documentation:**
   - `MEMORY.md` rule update: append to `#M-0.5` family — *"`ab discuss` is analysis-only. Filesystem writes during discussion = HARD STOP, dispatch the work as a separate brief."*
   - `docs/best-practices/agent-bridge.md` (and the HTML companion if it already exists — check `docs/best-practices/agent-bridge.html`; if absent, do NOT create one — that's not in scope).
   - Bridge `--help` for `discuss`: append the read-only line.
8. **Lint** — `.venv/bin/ruff check scripts/ai_agent_bridge/ tests/test_ab_discuss_read_only.py` — must be clean before commit.
9. **Commit** — conventional message:
   ```
   feat(bridge): enforce read-only mode in ab discuss (#1821)

   - Codex sub-agents launched with --mode read-only.
   - Claude headless without write permissions.
   - Gemini: post-round git-diff audit; violations surfaced in summary.
   - Tests + docs.

   Closes #1821.

   Co-Authored-By: Codex (gpt-5.5) <noreply@anthropic.com>
   ```
10. **Push** — `git push -u origin codex/1821-ab-discuss-read-only`.
11. **PR** — `gh pr create` with body referencing #1821, listing every AC ticked, and quoting evidence (test output, ruff clean) per #M-4. Title: `feat(bridge): enforce read-only mode in ab discuss (#1821)`.
12. **Do NOT auto-merge.** Stop here. The orchestrator will pick up the PR for cross-agent review (Claude headless + Gemini) and merge.

---

## What "done" looks like

- Every AC in #1821 ticked in the PR body with a quoted-evidence link (test name, file/line, or CLI output).
- Pre-commit hooks pass (ruff, prompt-lint, etc. — don't bypass).
- PR opened, **NOT merged**.
- Worktree clean (`git status` empty in the worktree).

## Escalation

If `ab discuss` runtime is more tangled than the issue assumes (e.g. agents share a single subprocess, or the per-agent flags don't compose), STOP, post a comment on #1821 with the diagnosis + proposed alternative, and exit cleanly. Do NOT half-implement.

If a test would require a real model call (slow / expensive), use a stub agent that simulates the write attempt — do NOT burn API budget for tests.
