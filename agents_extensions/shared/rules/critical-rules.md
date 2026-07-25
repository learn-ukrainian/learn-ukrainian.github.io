# Critical Rules

<critical>

### 1. Work in `agents_extensions/` First
**NEVER** edit `.claude/`, `.codex/`, `.agent/`, `.gemini/` directly. Edit in `agents_extensions/`, run `npm run agents:deploy` to sync.

### 2. Use Python venv
**ALWAYS** `.venv/bin/python`, **NEVER** `python3` or `python` directly.
- pyenv Python 3.12.8 with `--enable-loadable-sqlite-extensions`
- Recreate: `rm -rf .venv && ~/.pyenv/versions/3.12.8/bin/python -m venv .venv`

### 3. Language Settings
**English**: all technical work. **Ukrainian**: curriculum content only.

### 4. External LLM Access
Use `gemini-cli` (Google AI Pro subscription). No direct API keys.

### 5. Word Targets Are Minimums
**NEVER** reduce content or change `word_target` to match short content. Expand the content instead.

### 6. GitHub Issues as Persistent Memory
Every change tracked via GH issues. Before work: find/create issue. After: update/close. Reference in commits. Full protocol: [`issue-tracking.md`](docs/best-practices/issue-tracking.md)

### 7. Intellectual Independence
**The user explicitly wants pushback. Do not rubber-stamp ideas.**
- Challenge bad ideas directly — don't silently comply then fix later
- Think independently — consider second-order effects and alternatives before agreeing
- Propose the better approach when you disagree, not just a veto

### 8. Git, PR, and Merge Discipline

**Binding on EVERY agent — dispatched workers and drivers alike, every provider, every lane.**
This is the canonical statement; other files point here instead of restating it.

**8.1 — NEVER push to `main`.** Not a commit, not a fast-forward, not "just a regenerated file",
not with `--no-verify`, not to unblock something urgent. **PRs only, always.** A direct push skips
PR CI, review, and the pre-commit hooks in a single action.
> Why this is a rule and not advice: on 2026-07-25 two commits (`5f425a5fe1`, `9debd99699`) were
> pushed straight to `main`, changing `site/src/components/**` without regenerating the tracked
> `docs/lesson-schema.yaml`. The **required** `Lesson Schema Drift` gate went red on `main`, every
> branch inherited it, and **all open PRs became unmergeable**. The paths filter, its coverage test,
> and a matching pre-commit hook were all correct — they were simply walked around. Autopsy:
> `docs/bug-autopsies/ci-hang-unbounded-jobs.md`.

**8.2 — ALWAYS work in a git worktree**, never the primary checkout, and never switch branches in it:
`git worktree add .worktrees/dispatch/<agent>/<task> -b <agent>/<task> origin/main`.
Full contract: [`delegate-must-use-worktree.md`](delegate-must-use-worktree.md). Pass git an explicit
**literal** `-C <absolute worktree path>`: the primary-checkout guard cannot resolve shell variables
and will refuse the write, which is a guard working correctly, not a bug to route around.

**8.3 — "Done" means PUSHED.** Definition of done is **a pushed branch and an open PR**. A task that
ends without one has **FAILED**, whatever its status field says; analysis delivered only as a chat
reply is worth nothing. **Commit early and often** — uncommitted work in a worktree is lost work.
> On 2026-07-25 four dispatches reported `done` having pushed nothing: two left finished work
> uncommitted in their worktrees, one produced nothing after inventorying its targets, and one replied
> with a clarifying question instead of building. Three real failures read as three successes.
> **Workers:** if something is ambiguous, state your assumption and proceed — never stop to ask.
> **Orchestrators:** verify a pushed PR, never a status field. Prior art:
> `docs/bug-autopsies/codex-dispatch-stall.md` (#2985).

**8.4 — Cross-family review is MANDATORY before any merge.** It must be **independent** (never review
your own work), from **outside the author's model family**, and an actual review — *discussion does not
satisfy the gate*. Resolve the seat with
`.venv/bin/python -m scripts.review.closeout_cli … resolve-reviewer` rather than hand-picking one.
**If the review returns findings: FIX them, then RE-REVIEW, and only then merge.** A `FAIL` that is
blocked purely by missing evidence (no network, sandboxed filesystem) is **not** a pass — get the
missing evidence from a lane that can obtain it, then finalise.

**8.5 — Auto-merge protocol.**
- **Workers never merge and never arm auto-merge.** Only the driver owning that PR's lane arms it.
- Arm **only** when all three hold: review **PASS** (findings fixed and re-reviewed) · PR is **not a
  draft** · **no failing checks**. Standard form:
  `gh pr merge <N> --auto --squash --delete-branch -R <owner/repo>`.
- **Our review gate is agent-enforced, not GitHub-enforced.** Branch protection may require only a
  single status check and **zero approving reviews**, so nothing external will stop a premature merge.
  That is precisely why the review gate must gate *arming*.
- **Never merge ahead of the verdict, even under pressure.** On 2026-07-25 PR #5741 was armed while
  green and merged before its review returned; that review then found a factual omission and an
  overstatement in the merged document, needing a follow-up PR to correct.
- **ARMED ≠ MERGED.** A PR leaves the books only at state `MERGED`. Keep one babysitter running while
  any lane PR is open, and arm green PRs as they become green rather than when someone notices.
- **Never `--admin`-bypass blocking CI** (pytest, ruff, frontend, schema-drift, gitleaks, radon,
  prompt-lint).
- A **`cancelled`** required check is a gate failure, not a pass — re-run it. But after fixing the
  **base branch**, use `gh pr update-branch`, **not** `gh run rerun`: rerun re-tests the original
  pinned merge SHA and reproduces the old result.
- After any merge: delete the remote branch and remove the worktree (worktree first).

</critical>
