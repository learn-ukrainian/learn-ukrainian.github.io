# Shared Repo Rules For Orchestrator Prompts

Prompt suite component version: 0.2
Last reviewed: 2026-06-21

Paste these rules into future orchestration prompts and then verify them against the current local `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md`.

## Non-Negotiable Files

- Do not edit `.python-version`; it must remain `3.12.8`.
- Do not edit `.yamllint`.
- Do not edit `.markdownlint.json`.
- Do not weaken tests, skip tests with empty bodies, or change assertions to weaker checks.
- Do not delete existing scripts or utilities unless the user explicitly asks.

## Interpreter And Paths

- Never use `sys.executable` in project code or subprocess examples.
- Use `.venv/bin/python` explicitly in shell commands and subprocess calls.
- Do not use container-root absolute paths.
- Use real local paths or repo-relative paths from the worktree root.

## Worktree Layout

- Work in a dispatch worktree, not the main checkout.
- Run worktree setup from the main checkout, or set `REPO_ROOT` to the intended source checkout before pasting a setup block. This avoids nesting dispatch worktrees inside another worktree.
- Use `.worktrees/dispatch/codex/<task>/` for Codex work.
- Align the branch name with the path, for example `codex/<task>`.
- Verify the worktree before editing:

```bash
pwd
git status --short --branch
git rev-parse --show-toplevel
```

## Generated Artifacts

- Do not commit `curriculum/l2-uk-en/**/status/*.json`.
- Do not commit `curriculum/l2-uk-en/**/audit/*-review.md`.
- Do not commit `curriculum/l2-uk-en/**/review/*-review.md`.
- Do not commit `docs/*-STATUS.md`.
- Do not commit telemetry SQLite files under `data/telemetry/`.
- Durable human audit reports for these orchestrators belong under `docs/audits/`, not curriculum `audit/`, `review/`, or `status/` directories.

## Scope

- One PR equals one concern.
- Changed files should stay under 20 where practical. If a PR exceeds that, recheck for generated artifacts or scope creep.
- Every changed file must be directly related to the task.
- Inspect local repo files before acting. Do not rely on stale prompt text.
- Do not invent undocumented workflows, files, commands, standards, or policies.

## Commits And PRs

- Every commit must include an `X-Agent` trailer.
- Format: `X-Agent: codex/<task-id>` or the correct agent/task for the thread.
- Run `.venv/bin/python scripts/audit/lint_agent_trailer.py` before pushing.
- Module-build PRs must include token telemetry with `swarm_used`, `swarm_label`, and `swarm_note`.
- Do not commit, push, or open a PR unless the user explicitly asks or the orchestrator prompt says that is part of the task.
