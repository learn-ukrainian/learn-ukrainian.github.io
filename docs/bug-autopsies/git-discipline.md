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
