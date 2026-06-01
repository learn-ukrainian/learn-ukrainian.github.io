# Current - Codex Thread Handoff (2026-06-01T08:33+02:00)

Latest-Brief: docs/session-state/current.codex.md

## Active Work

- Repo: `/Users/krisztiankoos/projects/learn-ukrainian`
- Active worktree:
  `/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-m1-m7-golden-journey-2026-05-30`
- Branch: `codex/a1-m1-m7-golden-journey-2026-05-30`
- Latest implementation commit:
  `48e6598fd9 feat(a1): add M9 what is it like module`

## Current Direction

- Codex owns A1 learner journey, tooling, infra, and tech debt.
- BIO remains Claude/BIO-owned; do not touch BIO files, PRs, or worktrees.
- Do not use Gemini for review confidence.
- Keep using `services.sh` for local services.
- Continue M10 next (`colors`). M1-M9 are now built as English-led student
  textbook/workbook pages and pass deterministic QG in this worktree.

## Latest M9 Update

Commit `48e6598fd9 feat(a1): add M9 what is it like module` added:

- `curriculum/l2-uk-en/a1/what-is-it-like/module.md`
- `curriculum/l2-uk-en/a1/what-is-it-like/activities.yaml`
- `curriculum/l2-uk-en/a1/what-is-it-like/vocabulary.yaml`
- `curriculum/l2-uk-en/a1/what-is-it-like/resources.yaml`
- `starlight/src/content/docs/a1/what-is-it-like.mdx`

M9 is an English-led A1.2 grammar-first-contact module for descriptive
adjective agreement: `який / яка / яке / які`, hard nominative endings,
soft-pattern preview chunks, plural `-і`, room and book-fair descriptions,
`і`/`а`/`але`, and required adjective trap repair. Student-facing resources
include Ukrainian Lessons adjective resources, the Anna Ohoiko adjective video
page, a learner adjective chart, and Dobra Forma adjective practice. Internal
wiki references are not published.

Validation after M9:

- `scripts.yaml_activities`: parsed 10 activities.
- Direct `run_python_qg()` for M9: passed.
  - `resources_search_attempted`: passed with two real `search_external`
    telemetry calls captured in the local ignored `writer_tool_calls.json`.
  - `archetype_fit`, `vesum_verified`, `scaffolding_leak`,
    `russianisms_strict`, `activity_types`, `inject_activity_ids`,
    `engagement_floor`, and resource gates passed.
- Direct seeded hard wiki coverage: passed, 17/17 obligations covered.
- CLI `scripts/validate_mdx.py l2-uk-en a1 9`: passed.
- `npm run build:starlight`: passed; 99 pages built.
- Local Starlight restarted with `./services.sh restart starlight`.
- In-app Browser inspection for `/a1/what-is-it-like/`:
  - Lesson page showed H1 `Який він?` and inline workbook activities.
  - Vocabulary tab rendered adjective chunks.
  - Resources tab showed ULP, Anna Ohoiko, chart, and Dobra Forma resources.
  - Hidden anchor `#finish-the-adjective` switched back to the Lesson tab.
  - No internal `wiki/pedagogy` links, no visible `Крок 1:` scaffolding, and
    no broken bad-form comment markers.
- `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/pre-commit run
  --files ...`: passed for the 5 committed M9 files.
- `scripts/audit/lint_agent_trailer.py`: all branch commits pass.

Next target: M10 `colors`. Start by inspecting
`curriculum/l2-uk-en/plans/a1/colors.yaml`, the relevant wiki/pedagogy brief,
resource obligations, and `build_wiki_manifest_data`. Then build the same full
artifact set and validate with the same gates.

## Prior M8 Update

Commit `a675a2b1c5 feat(a1): add M8 things have gender module` added:

- `curriculum/l2-uk-en/a1/things-have-gender/module.md`
- `curriculum/l2-uk-en/a1/things-have-gender/activities.yaml`
- `curriculum/l2-uk-en/a1/things-have-gender/vocabulary.yaml`
- `curriculum/l2-uk-en/a1/things-have-gender/resources.yaml`
- `starlight/src/content/docs/a1/things-have-gender.mdx`

M8 is an English-led A1.2 grammar-first-contact module for noun gender:
`він / вона / воно`, clear ending signals, room and bag nouns,
`У мене є...`, `мій / моя / моє`, feminine profession forms, and common gender
trap repair. Student-facing resources include ULP Episode 6, ULP noun-gender
article/video resources, the Vakulenko noun-gender video, and Dobra Forma
references. Internal wiki references are not published.

Validation after M8:

- `scripts.yaml_activities`: parsed 9 activities.
- Direct `run_python_qg()` for M8: passed.
  - `word_count`: 1217 words, above the 1104 tolerated floor for target 1200.
  - `resources_search_attempted`: passed with two real `search_external`
    telemetry calls captured in the local ignored `writer_tool_calls.json`.
  - `archetype_fit`: passed for `a1-grammar-first-contact`.
  - `vesum_verified`, `scaffolding_leak`, `long_uk_ceiling`,
    `russianisms_strict`, `activity_types`, `inject_activity_ids`, and
    `engagement_floor`: passed.
  - `resource_coverage`: skipped as expected for non-M1-M7 archetype.
- Direct seeded hard wiki coverage: passed, 15/15 obligations covered.
- CLI `scripts/validate_mdx.py l2-uk-en a1 8`: passed.
- `npm run build:starlight`: passed; 98 pages built.
- Local Starlight restarted with `./services.sh restart starlight`.
- Served HTML check for `/a1/things-have-gender/`: HTTP 200, H1
  `Речі мають рід`, expected activity/resource text, no internal
  `wiki/pedagogy` links, and no visible `Крок 1:` scaffolding.
- In-app Browser inspection:
  - Lesson page showed H1 `Речі мають рід` and activity content.
  - Activities tab showed `Fix gender traps` and `Gender-flip diagnostic`.
  - Resources tab showed `Noun Genders in Ukrainian`, the ULP noun-gender
    video page, and Dobra Forma resources.
  - No internal wiki link or visible step scaffolding.
- `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/pre-commit run
  --files ...`: passed for the 5 committed M8 files.
- `scripts/audit/lint_agent_trailer.py`: all branch commits pass.
- Commit was pushed to origin.

## Prior M7 Update

Commit `ef9fbee094 feat(a1): add M7 first contact checkpoint` added the full
M7 artifact set under `curriculum/l2-uk-en/a1/checkpoint-first-contact/` plus
`starlight/src/content/docs/a1/checkpoint-first-contact.mdx`.

M7 validation passed before this handoff: YAML activities parsed, direct
`run_python_qg()` passed, seeded hard wiki coverage passed 17/17, direct and
CLI MDX validation passed, `npm run build:starlight` passed with 97 pages,
served/browser checks passed, pre-commit passed, trailer lint passed, and the
commit was pushed to origin.

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
