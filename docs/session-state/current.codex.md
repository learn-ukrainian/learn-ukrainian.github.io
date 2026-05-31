# Current - Codex Thread Handoff (2026-06-01T00:20+02:00)

Latest-Brief: docs/session-state/current.codex.md

## Active Work

- Repo: `/Users/krisztiankoos/projects/learn-ukrainian`
- Active worktree:
  `/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-m1-m7-golden-journey-2026-05-30`
- Branch: `codex/a1-m1-m7-golden-journey-2026-05-30`
- Latest implementation commit:
  `f07757ea58 feat(a1): add M2 reading Ukrainian module`

## Current Direction

- Codex owns A1 learner journey, tooling, infra, and tech debt.
- BIO remains Claude/BIO-owned; do not touch BIO files, PRs, or worktrees.
- Do not use Gemini for review confidence.
- Keep using `services.sh` for local services.
- Continue M3 next. M1 and M2 are now built as English-led student
  textbook/workbook pages and pass deterministic QG.

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

## Next Steps

1. Commit/push this handoff refresh.
2. Start M3 (`special-signs`) using the same M1/M2 artifact pattern.
3. Keep wiki/resource coverage hard. For M3, first check the plan references
   and wiki manifest, then build the full artifact set and run direct
   `run_python_qg()` before MDX assembly.
