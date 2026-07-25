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

> **These are agent SOPs, not the primary safeguard.** An independent best-practice audit
> (2026-07-25) put it bluntly: *"you are over-engineering review ritual and under-engineering merge
> physics."* Every incident these rules respond to is fixable at the **forge** — rulesets, a merge
> queue, and identities that can approve each other — and prose is a poor substitute for
> configuration. Read §8.6 first: it names the controls that must exist. The rules below are what an
> agent does *while* those controls are being put in place, and remain useful afterwards as
> operating discipline.

**8.1 — NEVER push to `main`.** Not a commit, not a fast-forward, not "just a regenerated file",
not with `--no-verify`, not to unblock something urgent. **PRs only, always.** A direct push skips
PR CI, review, and the pre-commit hooks in a single action.
>
> **This belongs in a repository ruleset, not only here** — industry treats it as a technical supply-chain
> control (SLSA Source L3, OpenSSF Scorecard *Branch-Protection*), not etiquette: `main` write-protected,
> **require pull request · no force-push · no deletions · no admin bypass for agent identities.**
> Until the ruleset exists, this rule is all that stands there, and it already failed once as prose.
> Why this is a rule and not advice: on 2026-07-25 two commits (`5f425a5fe1`, `9debd99699`) were
> pushed straight to `main`, changing `site/src/components/**` without regenerating the tracked
> `docs/lesson-schema.yaml`. The **required** `Lesson Schema Drift` gate went red on `main`, every
> branch inherited it, and **all open PRs became unmergeable**. The paths filter, its coverage test,
> and a matching pre-commit hook were all correct — they were simply walked around. Autopsy:
> `docs/bug-autopsies/ci-hang-unbounded-jobs.md`.

**8.2 — ALWAYS work in a git worktree**, never the primary checkout, and never switch branches in it:
`git worktree add .worktrees/dispatch/<agent>/<task> -b <agent>/<task> origin/main`. The primary
checkout is reserved for humans and services on `main`.
Full contract: [`delegate-must-use-worktree.md`](delegate-must-use-worktree.md). Pass git an explicit
**literal** `-C <absolute worktree path>`: the primary-checkout guard cannot resolve shell variables
and will refuse the write, which is a guard working correctly, not a bug to route around.
> **Scope honesty: this is hygiene, not a supply-chain control.** It prevents agent and human
> footguns and dirty primary trees. It does **not** prevent a direct push to `main`, does not
> implement "never merge an untested combination", and does not fix a cancelled required check. Do
> not present worktree discipline as the answer to any of those.

**8.3 — "Done" means PUSHED.** Definition of done is **a pushed branch, an open PR, and CI triggered
on it** (or an entry in the merge queue). A task that ends without that has **FAILED**, whatever its
status field says; analysis delivered only as a chat reply is worth nothing. **Commit early and
often** — uncommitted work in a worktree is lost work.
**A clarifying question with no PR is not success — it is `BLOCKED` / `NEEDS-INPUT`,** and must be
reported as such rather than settling as `done`.
> On 2026-07-25 four dispatches reported `done` having pushed nothing: two left finished work
> uncommitted in their worktrees, one produced nothing after inventorying its targets, and one replied
> with a clarifying question instead of building. Three real failures read as three successes.
> **Workers:** if something is ambiguous, state your assumption and proceed — never stop to ask.
> **Orchestrators:** verify a pushed PR, never a status field. Prior art:
> `docs/bug-autopsies/codex-dispatch-stall.md` (#2985).

**8.4 — Before merge, both must hold: (A) required CI green on the merge candidate, and (B) a review
artifact from a model family different from the author's.** It must be **independent** (never review
your own work) and an actual review — *discussion does not satisfy it*. Resolve the seat with
`.venv/bin/python -m scripts.review.closeout_cli … resolve-reviewer` rather than hand-picking one.
A `FAIL` that is blocked purely by missing evidence (no network, sandboxed filesystem) is **not** a
pass — get the missing evidence from a lane that can obtain it, then finalise.

> **What this is, and what it is NOT.** It is a **quality control** — a second model, unlike the
> author, hunting defects. It found real ones this week: an omitted root cause in a merged autopsy, and
> a wrong "nothing imports torch" claim. Keep it for that.
> It is **NOT** the review *requirement* itself, and must never be presented as equivalent to a human
> approving review. Precisely: **OpenSSF gives bot/AI review ZERO credit toward a review requirement.**
> Two independent audits agreed on that fact and split on the tone — one called presenting it as a
> Scorecard-grade gate "security theatre", the other noted the same sentence *validates the intent*
> while proving it is **not sufficient**. Both readings land in the same place: keep it as defect-finding,
> never claim it satisfies a review requirement, and optimise for control continuity rather than badge
> maths.

**Severity tiers — do not restart the world for a nit.** Blanket "fix every finding, then re-review
everything" cannot survive this repo's merge rate and is corporate dual-control cosplay:
- **P0 / P1 (correctness, security, scope violation, coverage silently dropped):** fix, then
  **RE-REVIEW**, then merge.
- **P2 / nits (naming, comments, style, non-behavioural cleanups):** fix and merge, or file a
  follow-up. No re-review required.
- Where a finding sits is the **reviewer's** call, recorded in the verdict — not the author's.

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
  > **The babysitter is a symptom, not a virtue.** Needing an agent to watch PRs to `MERGED` means the
  > forge is not doing it: either there is no merge queue, or cancellation makes green unobtainable
  > (§8.6). That is **under-automation**, not diligence. Once the queue is enabled, enqueueing replaces
  > babysitting — do not build elaborate watcher machinery instead of fixing the merge physics.
- **Never `--admin`-bypass blocking CI** (pytest, ruff, frontend, schema-drift, gitleaks, radon,
  prompt-lint).
- A **`cancelled`** required check is a gate failure, not a pass — re-run it. But after fixing the
  **base branch**, use `gh pr update-branch`, **not** `gh run rerun`: rerun re-tests the original
  pinned merge SHA and reproduces the old result.
- After any merge: delete the remote branch and remove the worktree (worktree first).

**8.6 — The controls that must exist at the forge (these SOPs are standing in for them).**
From an independent best-practice audit, ranked by value-per-effort. Anything above the line is worth
more than any wording in §8.1–8.5:

1. **Ruleset on `main`:** require pull request · required status check · no force-push · no deletions ·
   **no bypass for agent identities.** Stops the direct-push class outright.
2. **Fix the cancellation lie.** A required check that reports `cancelled` fails the gate (correctly),
   while `cancel-in-progress` *manufactures* cancellations on every push. Together they deadlock the
   queue: no PR can hold a green gate under load. Fix by keying concurrency to the PR number or SHA and
   cancelling **only** for `pull_request`.
3. **Merge queue** (`merge_group` wired, max group size 1 so failures attribute to one PR). This is the
   real implementation of *never merge an untested combination* — the problem that two individually
   green PRs can combine into a state neither validated.
   > **Verify availability before promising it.** GitHub's GA announcement scopes the feature to "a
   > managed organization with public repositories and GitHub Enterprise Cloud users", which is genuinely
   > ambiguous about free org plans. Checked 2026-07-25: this repo is **Organization-owned and public**,
   > so the wording plausibly covers us — but confirm the setting actually appears before designing
   > around it. Wiring `merge_group` into the workflow is harmless either way; assuming the queue exists
   > is not.
4. **Split the agent identities:** an author identity distinct from the approver/enqueue identity.
   With one shared identity GitHub **cannot** enforce required reviews at all, because that identity
   cannot approve its own PR. This is what makes §8.4 and §8.5 enforceable rather than voluntary.
5. **Stop gating on a whole-directory content hash.** A tracked generated file that hashes a whole
   directory serialises every PR touching it and invites semantic merge conflicts. Compute it in CI,
   or regenerate at merge time with a single writer.

**Explicitly NOT worth it at this scale** (named so nobody rebuilds them): Kubernetes OWNERS/Prow or
Chromium CQ ceremony · chasing Scorecard/SLSA badge levels that require multiple humans · paid merge
products before trying the free native queue · classifying an entire 12k-test suite **before** the
cancellation and merge-queue fixes land — that last one is process theatre while `main` is red.

</critical>
