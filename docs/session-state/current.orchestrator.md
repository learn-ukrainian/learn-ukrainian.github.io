# Current - Codex Orchestrator Handoff (2026-06-01T08:03Z)

Latest-Brief: docs/session-state/current.orchestrator.md

> Handoff-only update. Treat `origin/main` and this file as authoritative for
> orchestration state; treat the active A1 branch as authoritative for the
> M1-M11 implementation slice.

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
  `ed01b995e4 feat(a1): add M11 how many module`
- M11 implementation is committed locally and should be pushed with this
  handoff commit.

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

Next target: M12 `this-and-that`.

## A1 M11 Update

- Commit `ed01b995e4 feat(a1): add M11 how many module` added the full M11
  artifact set under `curriculum/l2-uk-en/a1/how-many/` plus
  `starlight/src/content/docs/a1/how-many.mdx`.
- M11 is English-led A1.2 content for numbers and practical use: counting,
  prices, age, phone-number grouping, `гривня/гривні/гривень`,
  `рік/роки/років`, and number-trap repair.
- Student-facing resources are external only; no internal wiki links.
- Local ignored telemetry file exists for the direct QG resource-search gate:
  `curriculum/l2-uk-en/a1/how-many/writer_tool_calls.json`.

Validation passed:

- Activity parser: 10 activities.
- Direct M11 `run_python_qg()`: passed.
- Seeded hard wiki coverage: 14/14 obligations covered.
- MDX validation for A1 M11: passed.
- `npm run build:starlight`: passed; 101 pages.
- Browser/content checks: expected Lesson/Resources content, no internal wiki
  links, teacher labels, visible scaffolding, or injection markers.
  Local Browser verified `#repair-number-traps` lands on the target after
  hydration.
- Targeted pre-commit: passed.
- X-Agent trailer lint: passed.

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
