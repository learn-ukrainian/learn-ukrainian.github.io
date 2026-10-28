# Delegated Work MUST Use Git Worktree

<critical>

When you dispatch work to Codex, Gemini, or any other agent via
`scripts/dispatch.py dispatch` (or any equivalent), the agent MUST work
in a git worktree — **not** a feature branch in the main checkout.

## Why this matters

`critical-rules.md` says: *"All work on `main`. Use `git worktree` for
isolation."* If delegated work creates a feature branch inside the main
checkout directory (`git checkout -b ...`), it:

- Switches HEAD of the main checkout off `main`, silently
- Mixes delegated work with any uncommitted work the user has
- Breaks scripts that expect `main` to be current
- Violates the "all on main" convention

This happened on 2026-04-21. I wrote a Codex brief saying *"Commit as a
feature branch + single PR if possible"* without specifying WHERE.
Codex ran `git checkout -b feature/gemini-fallback-ladder` inside the
main checkout. Cleanup was awkward (user had running scripts, couldn't
switch HEAD). The rule exists so this never happens again.

## Layout: dispatch subtree

Dispatch v2 creates `.worktrees/dispatch/<agent>/<task>/` by default. An explicit
`--worktree PATH` or `--cwd PATH` must stay inside that agent's dispatch subtree
and pass the planner's repository and symlink checks. New dispatches do not use
the deprecated flat layout.

Sparse exclusions are defined by `SPARSE_EXCLUDE_DEFAULT` in
`scripts/dispatcher/git.py`. Use `--sparse-include DIR` or `--full-checkout` for
required inputs. Owned paths do not re-include sparse files, and there are no
automatic sparse anchors.

## MANDATORY in every dispatch brief

Every Codex / Gemini / Claude-headless dispatch prompt MUST include
wording equivalent to:

```
## Worktree instructions (mandatory)

Work in a git worktree under `.worktrees/dispatch/<agent>/<task>/`
(auto-created by the runtime when you pass bare `--worktree`). Do NOT
create a feature branch in the main checkout. Concrete dispatch:

    .venv/bin/python scripts/dispatch.py dispatch \
        --agent codex --model gpt-6.1-sol \
        --task-id <task-id> \
        --mode workspace-write \
        --worktree \
        --base origin/main \
        --prompt-file brief.md

    # For dispatches that warrant peak Opus 5.5 reasoning:
    .venv/bin/python scripts/dispatch.py dispatch \
        --agent claude --model claude-opus-5-5 --effort xhigh \
        --task-id <task-id> --mode workspace-write --worktree \
        --base origin/main --prompt-file brief.md
    # Accepted --effort levels: low | medium | high | xhigh | max
    # (Omit --effort to use the agent's own CLI/config default.)

The main checkout (wherever the user is working) stays untouched on
`main`. After the PR merges, the accountable driver follows the sole landing
and cleanup recipe in `agents_extensions/shared/rules/workflow.md` § Merge policy.
Cleanup uses the common reaper; it is not a manual user step.

If the work truly cannot be done in a worktree (extremely rare —
usually only repo-wide mass migrations), STOP and ask for approval
before creating any branch.
```

Use descriptive task-ids: `<agent>-<issue-number>-<short-topic>`
(e.g. `codex-1877-verify-quote`). The runtime derives the branch name
and worktree path from the task-id + agent.

## Post-merge cleanup

Post-merge cleanup is mandatory. Follow [`workflow.md`](workflow.md) § Merge
policy / Post-merge cleanup, including common-reaper receipts, worker exit,
branch removal and the fail-closed non-zero/SKIPPED disposition. Never force
remove a worktree or invent a second removal path.

Use the common reaper for terminal worktree cleanup after checking custody and
delivery evidence. Dispatch v2 has no keep-worktree switch.

## When YOU (not a delegated agent) need isolation

Same rule — use a worktree. Don't branch in the main checkout. You may start at the repository root and run `git status --short --branch` as a read-only preflight/orientation step, but do not implement there. Any implementation edit, branch work, commit, or PR must happen from a worktree unless the user explicitly authorizes an exception. This prose rule is a reminder/backstop; mechanical enforcement is in `scripts/dispatch.py` and the common worktree reaper.

Use the subtree layout:

    git worktree add -b claude/<issue>-<topic> .worktrees/dispatch/claude/<issue>-<topic>
    cd .worktrees/dispatch/claude/<issue>-<topic>

## Required commit trailer: `X-Agent`

Every commit produced inside a dispatch worktree (or by the orchestrator
inline) MUST carry an `X-Agent: <agent>/<task-id>` trailer. This is the
only deterministic signal of which agent authored a commit — the git
`committer` field is the user's local config and is identical across
all locally-dispatched agents.

In the dispatch brief, instruct the agent explicitly:

```
Add the X-Agent trailer to every commit you make:

    git commit -m "feat(...): ..." --trailer "X-Agent: <agent>/<task-id>"

Where <agent> ∈ {claude, codex, gemini} and <task-id> is the dispatch
task identifier you were given (e.g. codex/1879-fix-ci-and-wikipedia).

Before pushing, verify with:

    .venv/bin/python scripts/audit/lint_agent_trailer.py
```

For orchestrator-inline commits I make myself: use `claude-inline/orchestrator`
(or a more specific topic like `claude-inline/agent-trailer-fix`).

Forward-only enforcement — do NOT rewrite history of already-merged
commits. The lint runs over `origin/main..HEAD` so each PR is checked
in isolation.

## Enforcement

The rule lives in both `agents_extensions/shared/rules/` (this file) and will
fire on every session start. If you dispatch without the worktree
instruction, you're violating a critical rule — reread it and rewrite
the brief.

</critical>
