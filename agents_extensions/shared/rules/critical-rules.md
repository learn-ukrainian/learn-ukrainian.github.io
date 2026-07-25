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
> physics."* **Most** of the incidents these rules respond to are fixable at the **forge** — the direct
> push, the untested combination, the unenforceable review — and for those, prose is a poor substitute
> for configuration. Read §8.6 first: it names those controls.
> **But not all of them.** The false-completion incident (§8.3) was a **harness defect**, not a forge
> gap: a dispatch settled as `done` having pushed nothing because the dirty-worktree check was gated on
> the wrong mode. No ruleset or merge queue would have caught it; it was fixed in code. Treat "configure
> the forge" as the first question, never the only one.

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

**8.3 — For a task whose deliverable is a CHANGE, "done" means PUSHED:** a pushed branch, an open PR,
and CI triggered on it (or an entry in the merge queue). Such a task ending without that has **FAILED**,
whatever its status field says; the change delivered only as a chat reply is worth nothing. **Commit
early and often** — uncommitted work in a worktree is lost work.

**Scope, stated precisely because the first draft of this rule over-reached:** this applies to tasks
dispatched to produce a change — code, docs, config. It does **not** apply to read-only work, which is
legitimately complete with no PR: reviews, audits, research, diagnosis, and any dispatch run with
`--mode read-only`. For those, the deliverable *is* the report. The mechanical test is the dispatch's
own mode plus whether its worktree is dirty — not a judgement about intent.

**Three distinct terminal outcomes; do not collapse them into `done`:**
- **`done`** — the deliverable exists (a pushed PR for change tasks, a report for read-only tasks).
- **`needs_finalize`** — work was produced but not committed or pushed. This is a **failure to finish**,
  and it is now detected mechanically for every write-capable mode (`delegate.py`); a dirty worktree with
  no commits can no longer report `done`.
- **`BLOCKED` / `NEEDS-INPUT`** — genuinely cannot proceed. Reporting this is correct behaviour, not a
  failure of nerve.

Prefer **assume-and-proceed** over asking: where a brief is ambiguous but a reasonable assumption exists,
take it, state it in the PR body, and continue. Reserve `BLOCKED` for the case where no reasonable
assumption exists — a missing credential, a contradictory instruction, an inaccessible resource. What is
forbidden is the middle path that caused the incident: replying with a question and settling as `done`.
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
everything" cannot survive this repo's merge rate and is corporate dual-control cosplay. The boundary is
**one question about impact**, so that two reviewers reach the same tier independently:

> **Can this finding change what the merged artifact DOES, or what a reader/consumer would conclude
> from it?**

- **Yes → BLOCKING.** Fix, then **RE-REVIEW**, then merge. Includes: wrong behaviour or output; a
  security or secret-handling defect; a change outside the PR's declared scope; coverage or a gate
  weakened or skipped; a factual claim in shipped prose that is wrong or unsupported (a wrong statement
  in an autopsy or a rule changes what readers conclude, so it blocks).
- **No → NON-BLOCKING.** Fix and merge, or file a follow-up; **no re-review**. Includes: naming, comment
  wording, formatting, and refactors that provably cannot change behaviour.
- **Unsure → treat as BLOCKING.** The tie-break is fail-closed, so an ambiguous finding never merges on
  an optimistic reading.
- The tier is the **reviewer's** call, recorded explicitly in the verdict, not the author's. An author
  who disagrees escalates to a second reviewer rather than re-tiering their own finding.

**8.5 — Auto-merge protocol.**
- **Workers never merge and never arm auto-merge.** Only the driver owning that PR's lane arms it.
- Arm **only** when all three hold: the review gate is satisfied — **no BLOCKING finding outstanding**
  per §8.4, so a non-blocking nit does **not** hold arming · PR is **not a draft** · **no failing
  checks**. Standard form:
  `gh pr merge <N> --auto --squash --delete-branch -R <owner/repo>`.
- **Arm as early as those conditions allow, then leave it alone.** The binding policy in
  [`workflow.md`](workflow.md) (§ auto-merge) is explicit: arm `--auto` and *"GitHub merges it when CI
  settles, nobody babysits."* `--auto` waits for green and never bypasses blocking checks, so early
  arming is safe and is the intended path.
- **Our review gate is agent-enforced, not GitHub-enforced.** Branch protection may require only a
  single status check and **zero approving reviews**, so nothing external will stop a premature merge.
  That is precisely why the review gate must gate *arming*.
- **Never merge ahead of the verdict, even under pressure.** On 2026-07-25 PR #5741 was armed while
  green and merged before its review returned; that review then found a factual omission and an
  overstatement in the merged document, needing a follow-up PR to correct.
- **ARMED ≠ MERGED.** A PR leaves the books only at state `MERGED`. Once armed, GitHub is responsible for
  merging it — **do not babysit for arming.** A watcher's only legitimate jobs are to notice
  *exceptions*: an outage-failed check that needs re-running, a base-branch fix that needs
  `gh pr update-branch`, a conflict, or a PR that has sat armed-and-green without merging. If a watcher
  is doing anything else, it has become a substitute for configuration.
  > **Known gap that makes a watcher necessary today, stated so it is fixed rather than institutionalised:**
  > `guard-pr-merge` refuses to arm while checks are red — correctly, since red is red — but that means a
  > PR whose checks are still running or transiently red **cannot be armed early**, which is exactly what
  > [`workflow.md`](workflow.md) intends. Until arming is permitted before green (or a merge queue removes
  > the question), something must notice when a PR becomes armable. That gap is **under-automation**, not
  > diligence, and it is infra debt — not a pattern to build on.
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
   > **Availability:** current GitHub documentation states merge queues are available for **any public
   > repository** (and for private repos on Enterprise Cloud). The 2023 GA announcement's phrasing —
   > "a managed organization with public repositories and GitHub Enterprise Cloud users" — reads as
   > ambiguous but has been superseded; an earlier draft of this rule over-stated that uncertainty and
   > was corrected in review. Verified 2026-07-25: this repo is **Organization-owned and public**, so it
   > qualifies. Wire `merge_group` into every required workflow, drop wildcard branch rules, and set
   > **maximum group size 1** if you want per-PR failure attribution.
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
