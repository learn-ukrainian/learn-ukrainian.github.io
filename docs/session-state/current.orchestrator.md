# Current - Codex Orchestrator Handoff (2026-06-01T16:28Z)

Latest-Brief: docs/session-state/current.orchestrator.md

> Handoff-only update. Treat `origin/main` and this file as authoritative for
> orchestration state; treat the active A1 branch as authoritative for the
> M1-M13 implementation slice.

## Role / Direction

- Codex owns main orchestration, GitHub issue memory, A1 golden learner
  journey, tooling, infra, and tech debt.
- BIO is fully owned by the BIO track orchestrator (Claude). Do not touch BIO
  worktrees, PRs, files, content, or delegates unless Claude routes work back.
- Stop using Gemini for review confidence.
- Use `./services.sh` and the repo venv Python.

## Git State

- Active A1 worktree:
  `/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-m1-m7-golden-journey-2026-05-30`
- Branch: `codex/a1-m1-m7-golden-journey-2026-05-30`
- Latest implementation commit:
  `f6cd35a701 feat(a1): add M13 many things module`

## A1 Built Sequence

1. `sounds-letters-and-hello`
2. `reading-ukrainian`
3. `special-signs`
4. `stress-and-melody`
5. `who-am-i`
6. `my-family`
7. `checkpoint-first-contact`
8. `things-have-gender`
9. `what-is-it-like`
10. `colors`
11. `how-many`
12. `this-and-that`
13. `many-things`

Next target: M14 `checkpoint-my-world`.

## A1 M13 Update

- Commit `f6cd35a701 feat(a1): add M13 many things module` added the full
  M13 artifact set under `curriculum/l2-uk-en/a1/many-things/` plus
  `starlight/src/content/docs/a1/many-things.mdx`.
- Local ignored telemetry file exists for the direct QG resource-search gate:
  `curriculum/l2-uk-en/a1/many-things/writer_tool_calls.json`.

Validation passed:

- Activity parser: 8 activities.
- Direct M13 `run_python_qg()`: passed.
- Seeded hard wiki coverage: 18/18 obligations covered.
- MDX validation for A1 M13: passed.
- `npm run build:starlight`: passed; 103 pages.
- Browser/content checks: expected Lesson/Resources content, no internal wiki
  links, teacher labels, visible scaffolding, or injection markers.
  Local Browser verified `#repair-traps` lands on the target and selects the
  Lesson tab.
- Targeted pre-commit: passed.
- Agent-trailer lint: passed before the M13 commit.

## Restart Commands

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-m1-m7-golden-journey-2026-05-30
git status --short --branch
git log --oneline --decorate -10 --no-merges
./services.sh status
curl -sS http://127.0.0.1:8765/api/delegate/active
```

## Guardrails

- Do not edit generated `status/*.json`, `audit/*-review.md`, or
  `review/*-review.md`.
- Do not touch `.python-version`, `.yamllint`, or `.markdownlint.json`.
- Do not use `sys.executable`.
- Keep changed files scoped and under 20 unless explicitly justified.
- Every commit must carry `X-Agent: codex/a1-m1-m14-golden-journey`.
