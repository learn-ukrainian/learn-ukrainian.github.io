# Current - Codex Orchestrator Handoff (2026-06-01T07:33Z)

Latest-Brief: docs/session-state/current.orchestrator.md

> Handoff-only update. Treat `origin/main` and this file as authoritative for
> orchestration state; treat the active A1 branch as authoritative for the
> M1-M10 implementation slice.

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
  `2bc13f6e8c feat(a1): add M10 colors module`
- Branch is local-ahead and should be pushed after the handoff commit.

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

Next target: M11 `how-many`.

## A1 M10 Update

- Commit `2bc13f6e8c feat(a1): add M10 colors module` added the full M10
  artifact set under `curriculum/l2-uk-en/a1/colors/` plus
  `starlight/src/content/docs/a1/colors.mdx`.
- M10 is English-led A1.2 grammar-first-contact content for color questions,
  color adjective endings, `синій` vs `блакитний`, `синьо-жовтий прапор`,
  appearance chunks, and color-trap repair.
- Student-facing resources are external only; no internal wiki links.
- Hash/tab rendering fix shipped for new assemblies:
  `scripts/generate_mdx/core.py` emits `<HashTabSync />`, and
  `starlight/src/components/HashTabSync.tsx` server-renders an inline hash
  scroll helper with hydration-aware retries.

Validation passed:

- Activity parser: 10 activities.
- Direct M10 `run_python_qg()`: passed.
- Seeded hard wiki coverage: 13/13 obligations covered.
- MDX validation for A1 M10: passed.
- `npm run build:starlight`: passed; 100 pages.
- Browser/content checks: expected lesson/resources/activity surfaces, no
  internal wiki links, teacher labels, visible scaffolding, or injection
  markers. Local Chrome verified `#repair-color-traps` lands on the target
  after hydration.
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
