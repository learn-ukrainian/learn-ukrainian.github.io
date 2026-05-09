# Codex CLI — PR #1835 N1 nit fix: replace line-number cites with function-name anchors

## TL;DR

PR #1835's ADR cites `scripts/ai_agent_bridge/_channels_cli.py:1413` (line 79 of the ADR). At PR base this was correct; on current `origin/main` the broker has drifted ~49 lines and 1413 now lands on a comment, not the convergence check. Replace literal line numbers with **function-name anchors** so the cite doesn't decay on broker edits.

This is a **one-line** edit on the existing PR branch — no new PR.

Full N1 detail in `audit/claude-review-1835-adr-round4-2026-05-09/REVIEW.md` §3.N1 (now on main).

---

## Mandatory orientation (#M-4)

1. **Read the round-4 review** — `audit/claude-review-1835-adr-round4-2026-05-09/REVIEW.md` — to internalize the N1 framing and why function-name anchors win.
2. **Read the current ADR** at PR #1835 head (commit `1116e3054c`):
   ```bash
   git show 1116e3054c:docs/decisions/pending/2026-05-09-decision-graph-view.md | sed -n '78,82p'
   git show 1116e3054c:docs/decisions/pending/2026-05-09-decision-graph-view.md | sed -n '105,108p'
   ```
3. **Verify the function name to anchor to.** The convergence check sits inside `_handle_discuss` (def at `_channels_cli.py:1057` on current main). Confirm:
   ```bash
   awk '/^(def |async def )/{f=$0; n=NR} /endswith.*\[AGREE\]/{print n":"f"  // L"NR": "$0}' scripts/ai_agent_bridge/_channels_cli.py
   ```
4. **Check whether the second cite has drifted too:** ADR line 106 cites `docs/best-practices/agent-cooperation.md:210-222` for "Mechanism A." Verify it still points there:
   ```bash
   sed -n '208,225p' docs/best-practices/agent-cooperation.md | grep -nE "Mechanism A|high-risk"
   ```
   If drifted, replace with a heading anchor. If still correct, leave as-is (Claude's review only flagged N1, not this cite).

## Verifiable claims this work will produce + the tool

| Claim | Tool | Evidence format |
|---|---|---|
| "ADR no longer cites brittle line `1413`" | `grep -n '1413' docs/decisions/pending/2026-05-09-decision-graph-view.md` | Quoted output (must be empty) |
| "ADR uses function-name anchor `_handle_discuss`" | `grep -nE '_handle_discuss\|_channels_cli\\.py' docs/decisions/pending/2026-05-09-decision-graph-view.md` | Quoted output |
| "The function `_handle_discuss` exists and contains the convergence check" | `grep -nE 'def _handle_discuss' scripts/ai_agent_bridge/_channels_cli.py` + the awk command above | Quoted output |
| "Pre-commit clean" | `.venv/bin/pre-commit run --files docs/decisions/pending/2026-05-09-decision-graph-view.md` | Quoted output |

---

## Worktree instructions

You will be invoked via `delegate.py dispatch --agent codex --mode danger --worktree --base codex/1791-adr-round3-revise`. The worktree branches FROM the existing PR head, so a single commit on top updates PR #1835.

**Push back to `codex/1791-adr-round3-revise`** (the PR branch), NOT a new branch. From the worktree:
```bash
git push origin HEAD:codex/1791-adr-round3-revise
```

**Do NOT open a new PR.** This patch lands on the existing #1835.

---

## The edit

ADR line 79 currently:
```markdown
*   **Canonical Markers:** `[AGREE]` and `[DISAGREE]`. The broker prompt requires agents to end round replies with one of these markers, and convergence uses strict `[AGREE]` tail matching in `scripts/ai_agent_bridge/_channels_cli.py:1413`.
```

Change to (function-name anchor):
```markdown
*   **Canonical Markers:** `[AGREE]` and `[DISAGREE]`. The broker prompt requires agents to end round replies with one of these markers, and convergence uses strict `[AGREE]` tail matching in `scripts/ai_agent_bridge/_channels_cli.py::_handle_discuss` (the convergence check is `text.strip().endswith("[AGREE]")` — grep that literal to find current line).
```

If line 106's `agent-cooperation.md:210-222` cite has ALSO drifted, fix it the same way (replace numeric range with a stable section heading anchor). If it hasn't drifted, leave as-is.

---

## Workflow (numbered)

1. Worktree branched from `origin/codex/1791-adr-round3-revise`.
2. Read the ADR + the round-4 review's §3.N1.
3. Verify `_handle_discuss` exists and contains the convergence check.
4. Check whether `agent-cooperation.md:210-222` has drifted.
5. Apply the edit(s).
6. `.venv/bin/pre-commit run --files docs/decisions/pending/2026-05-09-decision-graph-view.md`.
7. Commit (note this is on top of `1116e3054c`):
   ```
   docs(adr): replace brittle line cites with function-name anchors (#1835 N1)

   Resolves the round-4 N1 nit at audit/claude-review-1835-adr-round4-2026-05-09/REVIEW.md §3.N1.

   - L79: `_channels_cli.py:1413` → `_channels_cli.py::_handle_discuss`
     with the convergence-check literal as a grep anchor (function-name
     anchors don't drift on broker edits like this PR's base→main shifted
     the line by ~49 lines).
   - [if applicable] L106: agent-cooperation.md numeric range → section
     anchor.

   Refs #1835 #1791.

   Co-Authored-By: Codex (gpt-5.5) <noreply@anthropic.com>
   ```
8. Push: `git push origin HEAD:codex/1791-adr-round3-revise`.
9. **Do NOT open a new PR.** PR #1835 picks up the new commit automatically.
10. **NO auto-merge.** Stop. Orchestrator will re-verify CI then merge.

## Done criteria

- ADR no longer contains literal `1413`.
- Function-name anchor present and verified to exist.
- Pre-commit clean.
- New commit pushed to `codex/1791-adr-round3-revise` (PR #1835).
- No new PR opened.

## Escalation

If the function `_handle_discuss` doesn't exist or doesn't contain the convergence check (very unlikely given today's verification), STOP, comment on PR #1835 with the actual location, exit cleanly.
