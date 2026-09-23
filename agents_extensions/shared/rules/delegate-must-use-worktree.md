# Delegated Work MUST Use Git Worktree

<critical>

When you dispatch work to Codex, Gemini, or any other agent via
`scripts/delegate.py dispatch` (or any equivalent), the agent MUST work
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

## Layout: prefer the `dispatch/` subtree (new default)

`scripts/delegate.py` supports two worktree layouts:

| Layout | Path | How invoked |
|---|---|---|
| **Subtree (preferred)** | `.worktrees/dispatch/{agent}/{task}/` | bare `--worktree` (no path) — runtime auto-derives |
| **Flat (deprecated, back-compat)** | `.worktrees/<task-name>` | `--worktree <explicit-path>` |

Use the **subtree** layout for all new dispatches. The runtime prints a
`⚠️ DEPRECATED flat worktree layout` warning on the flat form. The
subtree layout has cleaner cleanup (`rm -rf .worktrees/dispatch/codex/`
nukes all Codex leftovers at once) and aligns the branch name
(`codex/1657p2-verify-quote`) with the path
(`.worktrees/dispatch/codex/1657p2-verify-quote/`).

Default sparse checkout: dispatch worktrees exclude `curriculum/`, `wiki/`,
`data/projects/`, `data/lexicon/` by default (~275 MB per worktree);
re-include with `--sparse-include <dir>` (repeatable) or matching
`--research-owned-path`; `--full-checkout` disables sparse; inside a worktree
`git sparse-checkout add <dir>` adds a tree later.

## MANDATORY in every dispatch brief

Every Codex / Gemini / Claude-headless dispatch prompt MUST include
wording equivalent to:

```
## Worktree instructions (mandatory)

Work in a git worktree under `.worktrees/dispatch/<agent>/<task>/`
(auto-created by the runtime when you pass bare `--worktree`). Do NOT
create a feature branch in the main checkout. Concrete dispatch:

    .venv/bin/python scripts/delegate.py dispatch \
        --agent codex \
        --task-id <task-id> \
        --mode danger \
        --worktree \
        --base origin/main \
        --prompt-file brief.md

    # For dispatches that warrant peak Opus 4.7 reasoning:
    .venv/bin/python scripts/delegate.py dispatch \
        --agent claude --model claude-opus-4-8 --effort xhigh \
        --task-id <task-id> --mode danger --worktree \
        --base origin/main --prompt-file brief.md
    # Accepted --effort levels: low | medium | high | xhigh | max
    # (Omit --effort to use the agent's own CLI/config default.)

The main checkout (wherever the user is working) stays untouched on
`main`. After the PR merges, `merge_closeout` (the P0 reaper) removes
the dispatch worktree and its local and remote branch. That cleanup is
not a manual user step:

    .venv/bin/python -m scripts.orchestration.merge_closeout <PR_NUMBER> --apply

If the work truly cannot be done in a worktree (extremely rare —
usually only repo-wide mass migrations), STOP and ask for approval
before creating any branch.
```

Use descriptive task-ids: `<agent>-<issue-number>-<short-topic>`
(e.g. `codex-1877-verify-quote`). The runtime derives the branch name
and worktree path from the task-id + agent.

## Post-merge cleanup

When a worktree's PR merges to main, the worktree and its branch MUST be
deleted. This is NOT optional — stale worktrees accumulate and pollute
`git worktree list`. The accountable command is `merge_closeout`, which
proves the PR is merged and reaps every worktree tied to that head through
the P0 reaper (do not delete worktrees or branches by hand, and never run `git worktree remove --force` yourself):

    .venv/bin/python -m scripts.orchestration.merge_closeout <PR_NUMBER> --apply

That removes the subtree worktree (`.worktrees/dispatch/<agent>/<task>`)
and the branch. Older flat worktrees (`.worktrees/<name>`) are reaped the
same way when they are registered against the merged head.

Clean read-only / workspace-write dispatch worktrees are removed automatically when the task settles (#8548); dirty trees are kept.

## When YOU (not a delegated agent) need isolation

Same rule — use a worktree. Don't branch in the main checkout. You may start at the repository root and run `git status --short --branch` as a read-only preflight/orientation step, but do not implement there. Any implementation edit, branch work, commit, or PR must happen from a worktree unless the user explicitly authorizes an exception. This prose rule is a reminder/backstop; mechanical enforcement is tracked in #4444-#4450.

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
