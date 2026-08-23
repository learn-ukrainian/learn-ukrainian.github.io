# Git Discipline — checkout violations in the primary project directory

Standing repo rule (user, repeated many times): **agents work in git worktrees; the
primary checkout NEVER leaves `main`.** Violations put every concurrent reader of the
primary tree (Monitor API, sources MCP, other orchestrators, running services) on
silently wrong code and risk code loss.

## 2026-07-10 — read-only review delegate ran `gh pr checkout` at repo root (#4857)

**What broke.** The primary checkout was found on branch `pr-4849` instead of `main`.
Reflog: `checkout: moving from main to pr-4849` @ 00:35:04+02:00.

**Root cause.** Task `review-4849` (deepseek-v4-pro) was dispatched with
`delegate.py --mode read-only`, which is allowed to run with `cwd = repo root`. The
reviewer, asked to verify claims about PR-branch files, reached for `gh pr checkout
4849` — in the primary checkout — then stalled and was killed
(`batch_state/tasks/review-4849.json`: 22:32:42Z→22:35:43Z, `response_chars: 0`,
checkout timestamp inside the window). Nothing in the sandbox, env, or delegate
finalize path prevents or detects a child moving the primary HEAD: the
`guard-branch-switch-in-main` hook covers interactive agent shells, not delegate
subprocesses.

**Not a one-off.** Stale local branches `pr-4397`, `pr-4556`, `pr-4557` carry the same
`gh pr checkout` naming — fossil record of prior undetected occurrences of this class.

**Recovery.** Tree was clean; `git checkout main` + `git pull --ff-only` restored state
at 00:42. No commits lost (reflog verified nothing dangling). Blast radius this time:
~7 minutes of every repo-root reader seeing PR-branch code.

**Prevention.** Layered — tracked in #4857, infra-harness #4707:
1. Review/read-only dispatches default into throwaway worktrees; repo-root requires an
   explicit opt-in flag.
2. `delegate.py` finalize assertion: record primary branch+HEAD at spawn → on exit,
   auto-restore when clean / hard-stop + surface when dirty; mark the task
   `failed(checkout-violation)`.
3. Wrapper/hook shim blocking `git checkout|switch` and `gh pr checkout` for delegate
   children whose `cwd` is the primary checkout.
4. Prompt-level hard line in every review brief ("read via `gh pr diff` /
   `git show origin/<branch>:<path>`; NEVER `gh pr checkout`") — mitigation only,
   never the fix; adopted immediately 2026-07-10.

**Category lesson.** Any subprocess that can execute `git`/`gh` in the primary checkout
can violate repo topology invariants. Invariants (branch == main) must be ENFORCED by
the dispatch runtime (fail-closed, verify-on-exit), not assumed from agent obedience.

## 2026-08-23 — worker published a connector-built commit that silently reverted merged `main` hunks (#7181)

**What broke.** PR #7180 (codex, #7171) opened with head `7a7844a1ec`, green PR-tier CI, a full
acceptance-evidence body — and a `.github/workflows/ci.yml` that **removed the three hunks PR #7169
had merged to `main` an hour earlier** (secret-scan scope step, `OPSEC_RANGE`, TruffleHog
`base`/`head`). Merging it would have reverted a landed patch while every signal said "done".

**Why.** The worker did the right thing in git: commit → push → `git rebase origin/main` (carried
#7169's hunks) → amend (`f5292cfc44`, correct). Then its push auth broke mid-task (`git fetch failed
after 3 attempts`, the #7166 class). Instead of stopping, it published through the GitHub connector
MCP inside `codex exec`: `github.create_commit` built a commit **server-side from file contents the
model supplied** — and for `ci.yml` it supplied its pre-rebase copy — then `github.update_ref
force:true` overwrote the branch, then `github.create_pr`. The commit never existed in any local
reflog on any host; the worktree still showed the correct `f5292cfc44`, clean, and the task record
said `done / commits_ahead: 1`. The only thing that caught it: `delegate.py dispatch --branch`
refused to attach a reviewer to a worktree whose head ≠ origin, which made the driver diff the
two heads (`git diff 7a7844a1ec f5292cfc44` = exactly the #7169 hunks, +24/−1).

**Prevention.**
1. Write-capable GitHub connector actions (`create_commit`, `update_ref`, `create_pr`, `merge_*`)
   have no place in a dispatched worker — publishing goes through git in the worktree, or the
   driver relay when worker auth is broken (#7166). Operator decision on #7181.
2. Driver gate before any review/merge: `origin/<branch>` must equal the dispatch worktree HEAD
   and the PR head must exist in that worktree's reflog. A mismatch is a stop, not a curiosity —
   promote the existing `--branch` refusal into a named check with an actionable reason.
3. A model "restoring" a file after a rebase from memory is a normal LLM failure; the fix is at
   the transport layer (no out-of-band commits), not at the prompt layer.
4. Recovery pattern that worked: sync the worktree to the bad remote head, let the **authoring
   lane** add a forward-fix commit with plain git (`git checkout <good-sha> -- <file>`, verify
   `git diff <good-sha>` empty), driver relays with a fast-forward push — no force-push needed.
