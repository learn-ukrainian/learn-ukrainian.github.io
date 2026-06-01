# Current Session Handoff

Generated-At: 2026-06-01T06:33Z

## Active Branch

- Worktree: `/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-m1-m7-golden-journey-2026-05-30`
- Branch: `codex/a1-m1-m7-golden-journey-2026-05-30`
- Latest implementation commit:
  `48e6598fd9 feat(a1): add M9 what is it like module`
- Remote: implementation commit is local at this handoff point and should be
  pushed with the handoff commit.

Recent commits:

- `48e6598fd9 feat(a1): add M9 what is it like module`
- `9e7c278760 docs(orchestration): refresh M8 handoff`
- `a675a2b1c5 feat(a1): add M8 things have gender module`
- `50ba907bd0 docs(orchestration): refresh M7 handoff`
- `ef9fbee094 feat(a1): add M7 first contact checkpoint`

## Current Goal State

- M1-M9 are built as English-led A1 student textbook/workbook modules.
- M9 `what-is-it-like` is complete locally. Validation passed: YAML activities
  parsed, direct `run_python_qg()` passed, seeded hard wiki coverage passed
  17/17, CLI MDX validation passed, `npm run build:starlight` passed with 99
  pages, local in-app browser checks passed for `/a1/what-is-it-like/`,
  targeted pre-commit passed, and X-Agent trailer lint passed.
- Next module: M10 `colors`.

## In-Flight Work

- No content work remains in flight for M9.
- M9 added:
  - `curriculum/l2-uk-en/a1/what-is-it-like/module.md`
  - `curriculum/l2-uk-en/a1/what-is-it-like/activities.yaml`
  - `curriculum/l2-uk-en/a1/what-is-it-like/vocabulary.yaml`
  - `curriculum/l2-uk-en/a1/what-is-it-like/resources.yaml`
  - `starlight/src/content/docs/a1/what-is-it-like.mdx`
- Local ignored telemetry file exists for the M9 direct QG resource-search
  gate:
  `curriculum/l2-uk-en/a1/what-is-it-like/writer_tool_calls.json`.
  It is intentionally not committed because the repo ignores writer telemetry.
- Active delegate API last known before M9 work: `{"total":0,"tasks":[]}`.

## Services

Verified 2026-06-01T06:33Z:

- `sources` running on port 8766.
- `api` running on port 8765.
- `starlight` running on port 4321 after
  `./services.sh restart starlight`.

## Open Issues

- Relevant known issue: `#2480` A1 M1-M7 safe onboarding / first-contact slice.
- Other open issues were not refreshed in this handoff turn; use
  `gh issue list --state open --limit 10` or Monitor API from a fresh session.

## Guardrails

- BIO is Claude/BIO-owned; do not touch BIO files/worktrees/PRs/delegates.
- Do not use Gemini for review confidence.
- Use `./services.sh` for services.
- Use `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python` for
  Python.
- Do not touch `.python-version`, `.yamllint`, `.markdownlint.json`,
  generated `status/*.json`, `audit/*-review.md`, or `review/*-review.md`.
- Do not use `sys.executable`.
- Commit every safe slice with trailer:
  `X-Agent: codex/a1-m1-m14-golden-journey`.

## Restart Commands

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-m1-m7-golden-journey-2026-05-30
git status --short --branch
git log --oneline --decorate -10 --no-merges
./services.sh status
curl -sS http://127.0.0.1:8765/api/delegate/active
```

If continuing the A1 golden journey, start M10 `colors` from the locked plan
and relevant wiki/pedagogy brief. Preserve the same artifact flow: four
authoring artifacts, assembled MDX, direct QG, seeded hard wiki coverage, MDX
validation, Starlight build, served/browser check, pre-commit, trailer lint,
commit, push, handoff.
