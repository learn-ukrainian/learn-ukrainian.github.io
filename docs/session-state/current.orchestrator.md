# Current - Codex Orchestrator Handoff (2026-06-01T16:05Z)

Latest-Brief: docs/session-state/current.orchestrator.md

> Handoff-only update. Treat `origin/main` and this file as authoritative for
> orchestration state; treat the active A1 branch as authoritative for the
> M1-M12 implementation slice.

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
  `f305dc8347 feat(a1): add M12 this and that module`

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

Next target: M13 `many-things`.

## A1 M12 Update

- Commit `f305dc8347 feat(a1): add M12 this and that module` added the full
  M12 artifact set under `curriculum/l2-uk-en/a1/this-and-that/` plus
  `starlight/src/content/docs/a1/this-and-that.mdx`.
- Shared rendered-page defect fixed in `starlight/src/components/HashTabSync.tsx`:
  requested hashes such as `#repair-traps` are restored when Starlight's tabs
  temporarily replace them with internal `#tab-panel-*` hashes. The schema hash
  refresh in `docs/lesson-schema.yaml` is part of that component change.
- Local ignored telemetry file exists for the direct QG resource-search gate:
  `curriculum/l2-uk-en/a1/this-and-that/writer_tool_calls.json`.

Validation passed:

- Activity parser: 8 activities.
- Direct M12 `run_python_qg()`: passed.
- Seeded hard wiki coverage: 18/18 obligations covered.
- MDX validation for A1 M12: passed.
- `npm run build:starlight`: passed; 102 pages.
- Browser/content checks: expected Lesson/Resources content, no internal wiki
  links, teacher labels, visible scaffolding, or injection markers.
  Local Browser verified `#repair-traps` lands on the target after the
  `HashTabSync` fix.
- Targeted pre-commit: passed.

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
