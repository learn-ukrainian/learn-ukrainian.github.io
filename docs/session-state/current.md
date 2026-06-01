# Current Session Handoff

Generated-At: 2026-06-01T05:37Z

## Active Branch

- Worktree: `/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-m1-m7-golden-journey-2026-05-30`
- Branch: `codex/a1-m1-m7-golden-journey-2026-05-30`
- Latest implementation commit:
  `a675a2b1c5 feat(a1): add M8 things have gender module`
- Remote: implementation commit pushed to
  `origin/codex/a1-m1-m7-golden-journey-2026-05-30`

Recent commits:

- `a675a2b1c5 feat(a1): add M8 things have gender module`
- `50ba907bd0 docs(orchestration): refresh M7 handoff`
- `ef9fbee094 feat(a1): add M7 first contact checkpoint`
- `9846684d28 docs(orchestration): refresh compact handoff`
- `1ab2f271d5 docs(orchestration): refresh M6 handoff`

## Current Goal State

- M1-M8 are built and pushed as English-led A1 student textbook/workbook
  modules.
- M8 `things-have-gender` is complete and pushed. Validation passed:
  YAML activities parsed, direct `run_python_qg()` passed, seeded hard wiki
  coverage passed 15/15, CLI MDX validation passed,
  `npm run build:starlight` passed with 98 pages, local HTML/browser checks
  passed for `/a1/things-have-gender/`, pre-commit passed, and X-Agent trailer
  lint passed.
- Next module: M9 `what-is-it-like`.

## In-Flight Work

- No content work remains in flight for M8.
- M8 added:
  - `curriculum/l2-uk-en/a1/things-have-gender/module.md`
  - `curriculum/l2-uk-en/a1/things-have-gender/activities.yaml`
  - `curriculum/l2-uk-en/a1/things-have-gender/vocabulary.yaml`
  - `curriculum/l2-uk-en/a1/things-have-gender/resources.yaml`
  - `starlight/src/content/docs/a1/things-have-gender.mdx`
- Local ignored telemetry file exists for the M8 direct QG resource-search
  gate:
  `curriculum/l2-uk-en/a1/things-have-gender/writer_tool_calls.json`.
  It is intentionally not committed because the repo ignores writer telemetry.
- Active delegate API last known: `{"total":0,"tasks":[]}`.

## Services

Verified 2026-06-01T05:37Z:

- `sources` running on port 8766.
- `api` running on port 8765.
- `starlight` running on port 4321.

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

If continuing the A1 golden journey, start M9 `what-is-it-like` from the
locked plan and relevant wiki/pedagogy brief. Preserve the same artifact flow:
four authoring artifacts, assembled MDX, direct QG, seeded hard wiki coverage,
MDX validation, Starlight build, served/browser check, pre-commit, trailer lint,
commit, push, handoff.
