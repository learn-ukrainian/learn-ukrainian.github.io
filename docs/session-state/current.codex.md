# Current - Codex Thread Handoff (2026-06-01T18:50+02:00)

Latest-Brief: docs/session-state/current.codex.md

## Active Work

- Repo: `/Users/krisztiankoos/projects/learn-ukrainian`
- Active worktree:
  `/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-m1-m7-golden-journey-2026-05-30`
- Branch: `codex/a1-m1-m7-golden-journey-2026-05-30`
- Latest implementation commit:
  `6b57fe4d70 feat(a1): add M14 checkpoint my world module`

## Current Direction

- Codex owns A1 learner journey, tooling, infra, and tech debt.
- BIO remains Claude/BIO-owned; do not touch BIO files, PRs, worktrees, or
  delegates.
- Do not use Gemini for review confidence.
- M1-M14 are now English-led student textbook/workbook pages and pass
  deterministic QG in this worktree.
- Next module if continuing: M15 `what-i-like`.

## Latest M14 Update

Commit `6b57fe4d70 feat(a1): add M14 checkpoint my world module` added:

- `curriculum/l2-uk-en/a1/checkpoint-my-world/module.md`
- `curriculum/l2-uk-en/a1/checkpoint-my-world/activities.yaml`
- `curriculum/l2-uk-en/a1/checkpoint-my-world/vocabulary.yaml`
- `curriculum/l2-uk-en/a1/checkpoint-my-world/resources.yaml`
- `starlight/src/content/docs/a1/checkpoint-my-world.mdx`

M14 is the A1.2 "my world" checkpoint. It reviews self-presentation chunks,
gender, possessives, adjective/color agreement, demonstratives, prices,
simple plurals, and a street-market dialogue using Ukrainian cultural items.

Validation after M14:

- `scripts.yaml_activities`: parsed 8 activities.
- Direct `run_python_qg()` for M14: passed; word count 1327.
- Direct seeded hard wiki coverage: passed, 17/17 obligations covered.
- CLI `scripts/validate_mdx.py l2-uk-en a1 14`: passed.
- `npm run build:starlight`: passed; 104 pages built.
- Local Starlight serves `/a1/checkpoint-my-world/` with `200 OK`.
- Browser inspection:
  - Lesson tab showed expected checkpoint content and inline practice.
  - Resources tab showed only external UkrainianLessons resources.
  - Resource title rendering was repaired by using
    `Noun Genders in Ukrainian - Infographic`.
  - `#repair-traps` selected Lesson and landed on the repair table after tab
    content settled.
  - No internal wiki links, teacher labels, visible scaffolding, or injection
    markers were found in checked surfaces.
- Targeted pre-commit passed.
- Agent-trailer lint passed after the M14 commit; all 54 non-skipped commits in
  `origin/main..HEAD` carry `X-Agent` trailers.

Local ignored telemetry exists for direct QG resource-search gates:

- `curriculum/l2-uk-en/a1/many-things/writer_tool_calls.json`
- `curriculum/l2-uk-en/a1/checkpoint-my-world/writer_tool_calls.json`

## Guardrails

- Use `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python`.
- Use `./services.sh` for services.
- Do not touch `.python-version`, `.yamllint`, `.markdownlint.json`,
  generated `status/*.json`, `audit/*-review.md`, or `review/*-review.md`.
- Do not use `sys.executable`.
