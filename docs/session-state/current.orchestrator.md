# Current - Codex Orchestrator Handoff (2026-06-01T06:33Z)

Latest-Brief: docs/session-state/current.orchestrator.md

> Handoff-only update. Treat `origin/main` and this file as authoritative for
> orchestration state; treat the active A1 branch as authoritative for the
> M1-M9 implementation slice.

## Role / Direction

- Codex owns main orchestration, GitHub issue memory, A1 golden learner
  journey, tooling, infra, and tech debt.
- BIO is fully owned by the BIO track orchestrator (Claude). Do not touch BIO
  worktrees, PRs, files, content, or delegates unless Claude routes work back.
- Stop using Gemini for review confidence.
- Use `./services.sh` for local services.
- Use `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python` for
  Python.
- Product direction remains: A1 from the beginning as English-led student
  textbook/workbook modules; Ukrainian appears in controlled chunks.

## Git State

- Repo: `/Users/krisztiankoos/projects/learn-ukrainian`
- Active A1 worktree:
  `/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-m1-m7-golden-journey-2026-05-30`
- Branch: `codex/a1-m1-m7-golden-journey-2026-05-30`
- Latest implementation commit:
  `48e6598fd9 feat(a1): add M9 what is it like module`
- M9 implementation is committed locally at this handoff point; push it with
  the handoff commit.
- Active delegate API last known before M9 work: `{"total":0,"tasks":[]}`.

## A1 Direction

Codex focus remains A1, tooling, infra, tech debt, and GitHub issues.

A1 built sequence on the active branch:

1. `sounds-letters-and-hello`
2. `reading-ukrainian`
3. `special-signs`
4. `stress-and-melody`
5. `who-am-i`
6. `my-family`
7. `checkpoint-first-contact`
8. `things-have-gender`
9. `what-is-it-like`

Next target: M10 `colors`.

## A1 M9 Update (2026-06-01)

- Commit `48e6598fd9 feat(a1): add M9 what is it like module` is local on
  `codex/a1-m1-m7-golden-journey-2026-05-30`.
- Added the full M9 artifact set:
  `curriculum/l2-uk-en/a1/what-is-it-like/{module.md,activities.yaml,
  vocabulary.yaml,resources.yaml}` plus
  `starlight/src/content/docs/a1/what-is-it-like.mdx`.
- M9 is English-led A1.2 grammar-first-contact content: descriptive adjective
  agreement, `який / яка / яке / які`, hard nominative endings, soft-pattern
  preview chunks, plural `-і`, room/book-fair descriptions, `і`/`а`/`але`, and
  adjective-trap repair. Student-facing resources are ULP, Anna Ohoiko, chart,
  and Dobra Forma resources; internal wiki references are skipped.
- Validation passed:
  - `scripts.yaml_activities`: 10 activities parsed.
  - Direct M9 `run_python_qg()`: passed, including
    `resources_search_attempted`, `archetype_fit`, `vesum_verified`,
    `scaffolding_leak`, `russianisms_strict`, `activity_types`,
    `inject_activity_ids`, and `engagement_floor`.
  - Direct seeded hard wiki coverage: 17/17 obligations covered.
  - CLI `scripts/validate_mdx.py l2-uk-en a1 9`: passed.
  - `npm run build:starlight`: passed; 99 pages built.
  - Local browser checks for `/a1/what-is-it-like/`: H1 `Який він?`, expected
    Lesson/Vocabulary/Resources content, inline workbook activities, ULP and
    Dobra Forma resources visible, no internal wiki links, no visible
    `Крок 1:` scaffolding, and hidden anchor `#finish-the-adjective` returned
    to the Lesson tab.
  - `.venv/bin/pre-commit run --files ...`: passed for the 5 committed M9
    files.
  - `scripts/audit/lint_agent_trailer.py`: all branch commits pass.

## A1 M8 Update (2026-06-01)

- Commit `a675a2b1c5 feat(a1): add M8 things have gender module` is pushed on
  `codex/a1-m1-m7-golden-journey-2026-05-30`.
- Added the full M8 artifact set:
  `curriculum/l2-uk-en/a1/things-have-gender/{module.md,activities.yaml,
  vocabulary.yaml,resources.yaml}` plus
  `starlight/src/content/docs/a1/things-have-gender.mdx`.
- M8 is English-led A1.2 grammar-first-contact content: noun gender,
  `він / вона / воно`, ending signals, everyday room/bag nouns,
  `У мене є...`, `мій / моя / моє`, feminitive profession forms, and required
  gender-trap repair. Student-facing resources are ULP/Dobra Forma/video
  resources; internal wiki references are skipped.
- Validation passed:
  - `scripts.yaml_activities`: 9 activities parsed.
  - Direct M8 `run_python_qg()`: passed, including `resources_search_attempted`,
    `archetype_fit`, `vesum_verified`, `scaffolding_leak`,
    `russianisms_strict`, `activity_types`, `inject_activity_ids`, and
    `engagement_floor`.
  - Direct seeded hard wiki coverage: 15/15 obligations covered.
  - CLI `scripts/validate_mdx.py l2-uk-en a1 8`: passed.
  - `npm run build:starlight`: passed; 98 pages built.
  - Local HTML/browser checks for `/a1/things-have-gender/`: H1
    `Речі мають рід`, expected Lesson/Activities/Resources content, ULP and
    Dobra Forma resources visible, no internal wiki links, and no visible
    `Крок 1:` scaffolding.
  - `.venv/bin/pre-commit run --files ...`: passed for the 5 committed M8
    files.
  - `scripts/audit/lint_agent_trailer.py`: all branch commits pass.

## Restart Commands

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-m1-m7-golden-journey-2026-05-30
git status --short --branch
git log --oneline --decorate -10 --no-merges
./services.sh status
curl -sS http://127.0.0.1:8765/api/delegate/active
```

If continuing the A1 golden journey, inspect
`curriculum/l2-uk-en/plans/a1/colors.yaml`, the relevant wiki brief, resource
obligations, and `build_wiki_manifest_data`, then build M10 with the same
artifact and validation flow.

## Guardrails

- Do not edit generated `status/*.json`, `audit/*-review.md`, or
  `review/*-review.md`.
- Do not touch `.python-version`, `.yamllint`, or `.markdownlint.json`.
- Do not use `sys.executable`.
- Keep changed files scoped and under 20 unless explicitly justified.
- Every commit must carry `X-Agent: codex/a1-m1-m14-golden-journey`.
