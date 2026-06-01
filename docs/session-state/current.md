# Current Session Handoff

Generated-At: 2026-06-01T07:33Z

## Active Branch

- Worktree: `/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-m1-m7-golden-journey-2026-05-30`
- Branch: `codex/a1-m1-m7-golden-journey-2026-05-30`
- Latest implementation commit:
  `2bc13f6e8c feat(a1): add M10 colors module`
- Previous handoff commit:
  `36b7e734ca docs(orchestration): refresh M9 handoff`
- Remote: branch is ahead locally and needs push after this handoff commit.

Recent commits:

- `2bc13f6e8c feat(a1): add M10 colors module`
- `36b7e734ca docs(orchestration): refresh M9 handoff`
- `48e6598fd9 feat(a1): add M9 what is it like module`
- `9e7c278760 docs(orchestration): refresh M8 handoff`
- `a675a2b1c5 feat(a1): add M8 things have gender module`

## Current Goal State

- M1-M10 are built as English-led A1 student textbook/workbook modules.
- M10 `colors` is complete locally. Next module: M11 `how-many`.
- BIO remains Claude/BIO-owned; do not touch BIO files, worktrees, delegates,
  or PRs.

## Latest M10 Update

Commit `2bc13f6e8c feat(a1): add M10 colors module` added:

- `curriculum/l2-uk-en/a1/colors/module.md`
- `curriculum/l2-uk-en/a1/colors/activities.yaml`
- `curriculum/l2-uk-en/a1/colors/vocabulary.yaml`
- `curriculum/l2-uk-en/a1/colors/resources.yaml`
- `starlight/src/content/docs/a1/colors.mdx`

It also fixed the tab/hash deep-link path for newly assembled modules:

- `scripts/generate_mdx/core.py` now emits `<HashTabSync />` as a
  server-rendered helper, not `client:load`.
- `starlight/src/components/HashTabSync.tsx` now emits an inline script with
  long hash-scroll retries for hydrated activity layout shifts.
- `docs/lesson-schema.yaml` was regenerated for the component hash change.

M10 content is an English-led A1.2 grammar-first-contact module for color
agreement: `Якого кольору...?`, core color adjectives, hard/soft adjective
endings, `синій` vs `блакитний`, `синьо-жовтий прапор`, appearance chunks
(`карі очі`, `русяве/сиве/руде волосся`), and required color-trap repair.
Student-facing resources are learner-safe external links only.

Validation passed:

- `scripts.yaml_activities`: parsed 10 activities.
- Direct `run_python_qg()` for M10: passed, 0 failed gates.
- Direct seeded hard wiki coverage: passed, 13/13 obligations covered.
- `scripts/validate_mdx.py l2-uk-en a1 10`: passed.
- `npm run build:starlight`: passed; 100 pages built.
- In-app Browser content inspection for `/a1/colors/`: H1 `Кольори`,
  Ukrainian activity surfaces visible, resources visible, no internal
  `wiki/pedagogy` links, no teacher labels, no `Крок 1:` scaffolding, no
  broken injection markers.
- Local Chrome/Puppeteer deep-link check for
  `/a1/colors/#repair-color-traps`: Lesson tab visible, target heading at
  16px from viewport top after hydration retries.
- Targeted pre-commit passed for the staged M10 files plus generator/schema
  hash-tab fix.
- `scripts/audit/lint_agent_trailer.py`: all branch commits pass.

## Services

Verified 2026-06-01T07:33Z:

- `sources` running on port 8766.
- `api` running on port 8765.
- `starlight` running on port 4321 after `./services.sh restart starlight`.

## Restart Commands

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-m1-m7-golden-journey-2026-05-30
git status --short --branch
git log --oneline --decorate -10 --no-merges
./services.sh status
curl -sS http://127.0.0.1:8765/api/delegate/active
```

If continuing the A1 golden journey, start M11 `how-many` from the locked plan,
wiki/pedagogy brief, resource obligations, and `build_wiki_manifest_data`.
Preserve the same artifact flow: four authoring artifacts, assembled MDX,
direct QG, seeded hard wiki coverage, MDX validation, Starlight build,
served/browser check, pre-commit, trailer lint, commit, push, handoff.

## Guardrails

- Use `./services.sh` for services.
- Use `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python` for
  Python.
- Do not touch `.python-version`, `.yamllint`, `.markdownlint.json`,
  generated `status/*.json`, `audit/*-review.md`, or `review/*-review.md`.
- Do not use `sys.executable`.
- Do not use Gemini for review confidence.
- Commit every safe slice with trailer:
  `X-Agent: codex/a1-m1-m14-golden-journey`.
