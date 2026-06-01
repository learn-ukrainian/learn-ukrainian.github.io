# Current - Codex Thread Handoff (2026-06-01T02:25+02:00)

Latest-Brief: docs/session-state/current.codex.md

## Active Work

- Repo: `/Users/krisztiankoos/projects/learn-ukrainian`
- Active worktree:
  `/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-m1-m7-golden-journey-2026-05-30`
- Branch: `codex/a1-m1-m7-golden-journey-2026-05-30`
- Latest implementation commit:
  `5dec6241f6 feat(a1): add M6 my family module`

## Current Direction

- Codex owns A1 learner journey, tooling, infra, and tech debt.
- BIO remains Claude/BIO-owned; do not touch BIO files, PRs, or worktrees.
- Do not use Gemini for review confidence.
- Keep using `services.sh` for local services.
- Continue M7 next (`checkpoint-first-contact`). M1-M6 are now built as
  English-led student textbook/workbook pages and pass deterministic QG. The
  M5 rendered learner defect at `/a1/who-am-i/#fix-common-l2-traps` is fixed.
  M6 `/a1/my-family/` is live locally and browser-inspected.

## Latest M6 Update

Commit `5dec6241f6 feat(a1): add M6 my family module` added:

- `curriculum/l2-uk-en/a1/my-family/module.md`
- `curriculum/l2-uk-en/a1/my-family/activities.yaml`
- `curriculum/l2-uk-en/a1/my-family/vocabulary.yaml`
- `curriculum/l2-uk-en/a1/my-family/resources.yaml`
- `starlight/src/content/docs/a1/my-family.mdx`

M6 is an English-led first-contact family/photo module covering `сім'я`,
`родина`, close family words, `У мене є`, `мій/моя/моє/мої`,
`твій/твоя/твоє/твої`, fixed `його/її`, recognition-only patronymics, and
learner-safe native family-word choices. Student-facing resources include only
the three locked ULP references; the internal wiki reference is skipped.

Validation after M6:

- `scripts.yaml_activities`: parsed 8 activities.
- Direct `run_python_qg()` for M6: passed.
  - `word_count`: 1373 words, above the 1104 tolerated floor for target 1200.
  - `resource_coverage`: passed; internal wiki reference skipped.
  - `archetype_fit`: passed for `a1-first-contact-survival`.
  - `vesum_verified`, `russianisms_strict`, and `inject_activity_ids`: passed.
- Direct seeded hard wiki coverage: passed, 16/16 obligations covered.
- Direct `validate_module()` for directory-layout source and generated MDX:
  passed with no errors or warnings.
- `npm run build:starlight`: passed; 96 pages built.
- Local Starlight restarted with `./services.sh restart starlight`.
- HTML check for `/a1/my-family/`: H1 `Моя сім'я`, Lesson/Vocabulary/
  Activities/Resources tabs, expected dialogue/activity/resource text, no
  `Russian-influenced` placeholders, and no internal `wiki/pedagogy` links.
- In-app Browser inspection:
  - Lesson tab selected cleanly and showed the family dialogue, inline
    `Family photo questions`, Ukrainian sentence surfaces, no internal wiki,
    and no placeholder distractors.
  - Activities tab selected cleanly through DOM control and showed workbook
    activity content including `Native family words`.
- `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/pre-commit run
  --files ...`: passed for the 5 M6 files.
- `scripts/audit/lint_agent_trailer.py`: all branch commits pass.
- Commit was pushed to origin.

Next target: M7 `checkpoint-first-contact`. Start by inspecting
`curriculum/l2-uk-en/plans/a1/checkpoint-first-contact.yaml`, the relevant
wiki/pedagogy brief, resource obligations, and `build_wiki_manifest_data`.
Then build the same full artifact set and validate with the same gates.

## Completed In This Slice

- Added deterministic `resource_coverage` gate in
  `scripts/build/linear_pipeline.py`.
- Gate is scoped through `resolve_module_archetype()` and currently fires only
  for `a1-zero-script-onboarding` (A1 M1), so unrelated modules are not blocked.
- Coverage now checks:
  - non-internal plan references are present in `resources.yaml`;
  - internal AI-facing wiki references are skipped, not published;
  - all non-null `plan.pronunciation_videos` URLs are present in resources;
  - wiki manifest `external_resources` URLs are present when declared.
- Backfilled A1 M1 `resources.yaml` and regenerated Starlight MDX so the
  Resources tab lists the Anna Ohoiko alphabet overview, playlist, all plan
  per-letter videos, and the stored O-video activity reference.
- Adapted `inject_activity_ids` for the M1-M7 English-led textbook/workbook
  archetypes. The gate still rejects injected ids that do not exist, but
  workbook-only activities are allowed for A1 zero/script/first-contact modules.
  A1 M1 now reports `act-4`, `act-7`, `act-8`, and `act-9` as workbook-only
  instead of unused.
- Replaced the passive A1 M1 `act-4` letter-grid workbook entry with an active
  five-question recognition quiz for high-value letters/signs (`Ґ`, `Ї`, `Ь`,
  `О`, `И/І`) and regenerated the Starlight MDX.
- Fixed YAML `letter-grid` MDX rendering so it does not display the same title
  twice, and passed Quiz item explanations through to the React component.

## Validation

- `tests/test_plan_reference_match_gate.py tests/test_audit_learner_state.py tests/test_module_archetypes.py`:
  35 passed.
- Pre-commit on `e8633c3145`: passed, including affected pytest, ruff,
  gitleaks, YAML, MDX parity, and repository hooks.
- Direct A1 M1 `resource_coverage` report: passed, with the locked internal
  wiki reference skipped.
- `scripts/validate_mdx.py`: passed.
- `npm run build:starlight`: passed; 91 pages in about 5s; etymology dynamic
  routes skipped unless `BUILD_ETYMOLOGY_ROUTES=1`.
- Browser plugin could not attach to the in-app browser in this session
  (`agent.browsers.list()` returned empty), so rendered Resources were verified
  by inspecting generated MDX and built HTML instead.
- `tests/test_inject_activity_gate.py tests/test_immersion_gates.py tests/test_module_archetypes.py`:
  22 passed.
- `ruff check scripts/build/linear_pipeline.py tests/test_inject_activity_gate.py`:
  passed.
- `tests/test_yaml_activities_v7_types.py tests/test_quiz_translate_explanations_gate.py tests/test_inject_activity_gate.py`:
  13 passed.
- `npm test -- tests/unit/Quiz.test.tsx` in `starlight/`: 23 passed.
- `npm run build:starlight`: passed; 91 pages built.
- Direct A1 M1 `run_python_qg()` report no longer fails `inject_activity_ids`.

## Latest M1 Wiki / Gate Closure

Commit `6ccce0946a` closed the remaining M1 full `run_python_qg()` failures:

- Added real M1 wiki-obligation coverage in `module.md` and `activities.yaml`.
  Seeded full wiki coverage is now 12/12 (`coverage_pct: 1.0`, minimum 0.8).
- Added explanations to `act-9` translate items and fixed the YAML-to-MDX
  translate renderer so explanations reach the React `Translate` component.
- Added an active `act-10` pronunciation-trap error-correction workbook block
  for the L2 contrast pairs required by the wiki manifest.
- Scoped `plan_sections` heading aliases to the `a1-zero-script-onboarding`
  archetype so English-led M1 headings can satisfy locked Ukrainian plan
  sections without weakening other modules.
- Scoped `resources_search_attempted` manual pass-through to A1 zero-script
  modules only when deterministic `resource_coverage` has already passed. This
  preserves hard wiki/resource coverage while avoiding a telemetry-only failure
  for the hand-authored M1 template.
- Taught VESUM to ignore sung vowel practice strings and taught the long-UK
  immersion gate to ignore Ukrainian alphabet rows.

Current direct checks:

- Seeded M1 full wiki coverage: passed, 12/12.
- Direct A1 M1 `run_python_qg()`: passed.
- Focused Python tests: 33 passed.
- Pre-commit on `6ccce0946a`: 200 passed, 1 skipped plus repo hooks.
- `npm test -- tests/unit/Quiz.test.tsx tests/unit/Translate.test.tsx
  tests/unit/ErrorCorrection.test.tsx`: 79 passed.
- `npm run build:starlight`: passed; 91 pages built.

## Next Steps

## Latest Archetype-Fit Gate

Commit `79c8d84fe9` added a deterministic `archetype_fit` gate:

- `scripts/audit/checks/contract_compliance.py` now exposes
  `check_archetype_fit()`.
- `scripts/build/linear_pipeline.py` records it in `run_python_qg()`.
- It does not replace wiki/resource, VESUM, Russianism, or decolonization
  gates. It only checks deterministic artifact shape for the resolved module
  archetype.
- For A1 M1-M7 it checks: no internal wiki links, English-led surface,
  workbook activity floor, A1-compatible activity families, and a real
  textbook/workbook split.
- Direct A1 M1 `run_python_qg()` passes with `archetype_fit.passed == true`.

Validation for `79c8d84fe9`:

- `tests/test_contract_compliance.py`: 36 passed.
- Focused suite:
  `tests/test_contract_compliance.py tests/test_inject_activity_gate.py
  tests/test_resources_search_gate.py tests/test_plan_reference_match_gate.py
  tests/test_quiz_translate_explanations_gate.py`: 55 passed.
- Direct A1 M1 `run_python_qg()`: passed.
- `ruff check scripts/audit/checks/contract_compliance.py
  scripts/build/linear_pipeline.py tests/test_contract_compliance.py`: passed.
- `git diff --check`: passed.
- `npm run build:starlight`: passed; 91 pages built.
- Pre-commit on `79c8d84fe9`: passed.

## Next Steps

## Latest M2 / M1-M7 Gate Update

Commits after `79c8d84fe9`:

- `42195a1d59 fix(pipeline): gate A1 M1-M7 resource coverage`
  - `resource_coverage` now applies to A1 M1-M7 archetypes, not only M1.
  - A1 M2 correctly hard-failed with missing plan references until
    `resources.yaml` covered the locked plan references.
  - Manual resource-search telemetry pass-through is still allowed only when
    deterministic resource coverage has already passed, and only for A1 M1-M7.
- `48b3b15978 fix(pipeline): allow A1 M2-M7 English section headings`
  - `plan_sections` still requires every locked plan section.
  - A1 M1-M7 can satisfy Ukrainian plan section names with approved English
    student-facing headings, preserving the English-led product direction.
- `f07757ea58 feat(a1): add M2 reading Ukrainian module`
  - Added `curriculum/l2-uk-en/a1/reading-ukrainian/{module.md,activities.yaml,
    vocabulary.yaml,resources.yaml}`.
  - Added rendered `starlight/src/content/docs/a1/reading-ukrainian.mdx`.
  - M2 is English-led script-building: syllables, vowel letters, reading words,
    reading traps, and textbook/workbook check.

Validation after M2:

- M2 `scripts.yaml_activities`: passed.
- M2 direct `run_python_qg()`: passed.
  - `resource_coverage`: passed; locked internal wiki references skipped.
  - `archetype_fit`: passed for `a1-script-building`.
  - `word_count`: 1160 words, above the 1104 tolerated floor for target 1200.
- Focused gate suite after infra changes:
  `tests/test_correction_loop_surgical.py tests/test_contract_compliance.py
  tests/test_inject_activity_gate.py tests/test_resources_search_gate.py
  tests/test_plan_reference_match_gate.py
  tests/test_quiz_translate_explanations_gate.py`: 73 passed.
- `ruff check` on touched infra/test files: passed.
- `git diff --check`: passed.
- `scripts/validate_mdx.py l2-uk-en a1 2`: passed.
- `npm run build:starlight`: passed; 92 pages built.
- Local Starlight dev server restarted via `./services.sh restart starlight`
  from the active worktree and serves
  `http://127.0.0.1:4321/a1/reading-ukrainian/`.
- HTML inspection confirmed the page has H1 `Читаємо українською`, English
  section headings, and rendered activity text. Playwright browser inspection
  could not run because the local Playwright browser binary is missing.
- `scripts/audit/lint_agent_trailer.py`: all branch commits pass.

## Latest M3 Update

Commit `440cd017a6 feat(a1): add M3 special signs module` added:

- `curriculum/l2-uk-en/a1/special-signs/module.md`
- `curriculum/l2-uk-en/a1/special-signs/activities.yaml`
- `curriculum/l2-uk-en/a1/special-signs/vocabulary.yaml`
- `curriculum/l2-uk-en/a1/special-signs/resources.yaml`
- `starlight/src/content/docs/a1/special-signs.mdx`

M3 is English-led script-building for `ь`, apostrophe, and the contrasts
`день`, `сім'я`, `буряк`, `бур'ян`, `свято`, `цвях`.

Validation after M3:

- M3 `scripts.yaml_activities`: passed.
- M3 direct `run_python_qg()`: passed.
  - `resource_coverage`: passed; locked internal wiki reference skipped.
  - `archetype_fit`: passed for `a1-script-building`.
  - `word_count`: 1157 words, above the 1104 tolerated floor for target 1200.
- `scripts/validate_mdx.py l2-uk-en a1 3`: passed.
- `npm run build:starlight`: passed; 93 pages built.
- Local Starlight initially returned HTTP 500 for `/a1/special-signs/` after
  hot reload; `./services.sh restart starlight` cleared Astro/Vite caches and
  the route then served correctly.
- Served HTML inspection confirmed H1 `Особливі знаки`, English section
  headings, and rendered activity text.
- `scripts/audit/lint_agent_trailer.py`: all branch commits pass.

## Latest M4 Update

Commit `a5c8d98253 feat(a1): add M4 stress and melody module` added:

- `curriculum/l2-uk-en/a1/stress-and-melody/module.md`
- `curriculum/l2-uk-en/a1/stress-and-melody/activities.yaml`
- `curriculum/l2-uk-en/a1/stress-and-melody/vocabulary.yaml`
- `curriculum/l2-uk-en/a1/stress-and-melody/resources.yaml`
- `starlight/src/content/docs/a1/stress-and-melody.mdx`

M4 is English-led script-building for word stress, clear unstressed vowels,
meaning-changing stress, yes/no rising melody, question-word falling melody,
and short read-aloud routines.

Validation after M4:

- M4 `scripts.yaml_activities`: passed.
- M4 direct `run_python_qg()`: passed.
  - `resource_coverage`: passed; locked internal wiki reference skipped.
  - `archetype_fit`: passed for `a1-script-building`.
  - `word_count`: 1251 words, above the 1104 tolerated floor for target 1200.
  - `vesum_verified`: passed with no missing words.
- Direct `validate_module()` for directory-layout source and generated MDX:
  passed with no errors or warnings.
- `npm run build:starlight`: passed; 94 pages built.
- Local Starlight was restarted from the active worktree. Served HTML for
  `/a1/stress-and-melody/` returned HTTP 200, had exactly one H1
  `Наголос і мелодика`, and contained Lesson/Vocabulary/Activities/Resources
  tab content.
- In-app Browser inspection confirmed one H1, no duplicate English H1, visible
  Lesson/Vocabulary/Activities/Resources tabs, stress/melody activities, and
  the ULP resource text.
- Pre-commit on `a5c8d98253`: passed.

## Latest M5 Infra Unblock

Commit `1bfcc7a7f9 fix(pipeline): allow zero-word summary sections` unblocked
M5 plan loading without editing the locked plan:

- `validate_plan()` still rejects missing, non-integer, and negative section
  word budgets.
- It now accepts `words: 0`, which the locked M5 `Підсумок` section uses as a
  heading/self-check-only contract.
- Added regression coverage in `tests/test_linear_pipeline_wiki_coverage.py`
  against `plan_path_for("a1", "who-am-i")`.

Validation:

- `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python -m pytest
  tests/test_linear_pipeline_wiki_coverage.py -q`: 7 passed.
- `git diff --check`: passed.
- Pre-commit on `1bfcc7a7f9`: passed.

## Latest M5 Content Update

Commit `08fe80bf95 feat(a1): add M5 who am i module` added:

- `curriculum/l2-uk-en/a1/who-am-i/module.md`
- `curriculum/l2-uk-en/a1/who-am-i/activities.yaml`
- `curriculum/l2-uk-en/a1/who-am-i/vocabulary.yaml`
- `curriculum/l2-uk-en/a1/who-am-i/resources.yaml`
- `starlight/src/content/docs/a1/who-am-i.mdx`

M5 is an English-led first-contact module for name, profession/status, origin,
residence, age, and polite identity exchange. It keeps the locked internal wiki
reference out of student-facing resources while covering all M5 wiki
obligations.

Scoped fixes included in the same implementation commit:

- `wiki_manifest` strips HTML `<!-- VERIFY ... -->` comments from wiki L2
  error cells before manifest extraction.
- `wiki_coverage_gate` ignores the teacher-facing parenthetical loanword
  `чанк` so the learner page can use English "chunk" without forcing a
  non-VESUM Ukrainian loanword into student prose.
- `DialogueBox` now supports generated legacy `uk`/`en` props used by existing
  MDX output and renders those lines with visible English glosses.
- `docs/lesson-schema.yaml` was regenerated by the schema drift hook for the
  `DialogueBox` prop contract.

Validation after M5:

- M5 `scripts.yaml_activities`: passed.
- M5 direct `run_python_qg()`: passed.
  - `word_count`: 1549 words for target 1200.
  - `resource_coverage`: passed; locked internal wiki reference skipped.
  - `archetype_fit`: passed for `a1-first-contact-survival`.
  - `vesum_verified` and `russianisms_clean`: passed.
- Hard wiki coverage check: passed, 15/15 obligations covered.
- `tests/test_wiki_manifest.py tests/audit/test_wiki_coverage_gate.py`:
  40 passed.
- `npm test -- tests/unit/LessonComponents.test.tsx`: 23 passed.
- `ruff check` on touched Python/test files: passed.
- `scripts/validate_mdx.py l2-uk-en a1 5`: passed.
- Direct `validate_module()` for directory-layout M5 source and MDX: passed.
- `npm run build:starlight`: passed; 95 pages built.
- Local Starlight was restarted via `./services.sh restart starlight`.
  In-app Browser inspection of `/a1/who-am-i/` confirmed one H1
  `Хто я?`, visible Lesson/Vocabulary/Activities/Resources tabs, rendered
  Marko dialogue with English glosses, M5 workbook activities, and ULP
  resources only.
- Pre-commit on `08fe80bf95`: passed, including affected pytest and repository
  hooks.

## Latest M5 Rendered Page Repair

Commit `17b5f9fe8e fix(a1): repair M5 activity hash target` fixed the
learner-facing defect reported at `/a1/who-am-i/#fix-common-l2-traps`:

- Replaced the English teacher-facing `act-7` error-correction prompts with
  visible Ukrainian sentence surfaces.
- Renamed the activity to `Choose the Ukrainian sentence`.
- Preserved the legacy `#fix-common-l2-traps` URL through an explicit
  `anchor_id` in `activities.yaml`.
- Moved the repaired activity to the first workbook position in the Activities
  tab so the exact legacy URL opens on the right tab with the corrected activity
  immediately visible in the constrained in-app browser viewport.
- Added `HashTabSync` to generated tabbed MDX so hash targets inside hidden
  Starlight tabs activate the containing tab before attempting to scroll.
- Extended `scripts/yaml_activities.py` so error-correction activities preserve
  optional `instruction` and `anchor_id` fields in generated MDX.
- Regenerated M5 MDX and `docs/lesson-schema.yaml`; the schema update is the
  hook-generated contract entry for the new `HashTabSync` component.

Validation after the repair:

- M5 `scripts.yaml_activities`: passed.
- Focused Python tests:
  `tests/test_yaml_activities.py tests/test_generate_mdx.py`: 107 passed.
- Direct M5 `run_python_qg()`: passed, including `resource_coverage`,
  `archetype_fit`, `vesum_verified`, `russianisms_clean`, and
  `inject_activity_ids`.
- Direct hard wiki coverage: passed, 15/15 obligations covered.
- Direct `validate_module()` for directory-layout M5 source and MDX: passed
  with no errors or warnings.
- `npm test -- tests/unit/HashTabSync.test.tsx tests/unit/ErrorCorrection.test.tsx`:
  35 passed.
- `npm run build:starlight`: passed; 95 pages built.
- In-app Browser inspection of
  `http://127.0.0.1:4321/a1/who-am-i/#fix-common-l2-traps` confirmed:
  selected tab `Activities`, first visible activity heading
  `Choose the Ukrainian sentence`, legacy hash target present, no old English
  teacher prompt phrases, and all six Ukrainian sentence surfaces visible.
- Pre-commit on `17b5f9fe8e`: passed, including affected pytest and repository
  hooks.

Next target: M6 `my-family`.

## Next Steps

1. Commit/push this handoff refresh.
2. Start M6 content (`my-family`) using the same M1-M5 artifact pattern.
3. Keep wiki/resource coverage hard. For M6, first inspect the plan references
   and wiki manifest, then build the full artifact set and run direct
   `run_python_qg()` before MDX assembly.
