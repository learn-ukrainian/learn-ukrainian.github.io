# Current Session Handoff

Generated-At: 2026-06-01T15:28Z

## Active Branch

- Worktree:
  `/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-m1-m7-golden-journey-2026-05-30`
- Branch: `codex/a1-m1-m7-golden-journey-2026-05-30`
- Latest handoff commit:
  `13cb273fda docs(orchestration): refresh M11 handoff`
- Latest implementation commit:
  `ed01b995e4 feat(a1): add M11 how many module`

Recent commits:

- `13cb273fda docs(orchestration): refresh M11 handoff`
- `ed01b995e4 feat(a1): add M11 how many module`
- `5031a7d99b docs(orchestration): refresh M11 handoff`
- `42869f2bc4 docs(orchestration): refresh M10 handoff`
- `2bc13f6e8c feat(a1): add M10 colors module`
- `36b7e734ca docs(orchestration): refresh M9 handoff`

## Current Goal State

- M1-M11 are built as English-led A1 student textbook/workbook modules.
- M11 `how-many` is complete and pushed.
- Next module: M12 `this-and-that`.
- BIO remains Claude/BIO-owned; do not touch BIO files, worktrees, delegates,
  or PRs.

## M11 Summary

Commit `ed01b995e4 feat(a1): add M11 how many module` added:

- `curriculum/l2-uk-en/a1/how-many/module.md`
- `curriculum/l2-uk-en/a1/how-many/activities.yaml`
- `curriculum/l2-uk-en/a1/how-many/vocabulary.yaml`
- `curriculum/l2-uk-en/a1/how-many/resources.yaml`
- `starlight/src/content/docs/a1/how-many.mdx`

M11 teaches numbers `нуль` through `сто`, useful prices through
`тисяча гривень`, `Скільки коштує...?`, age chunks
`Мені/тобі/їй + number + рік/роки/років`, Ukrainian phone-number grouping,
and number-trap repair. It keeps currency and age agreement as chunks, not a
case lesson. Collective numerals `двоє`, `троє`, `четверо` are passive
recognition only.

Local ignored telemetry exists for the resource-search gate:
`curriculum/l2-uk-en/a1/how-many/writer_tool_calls.json`.

## M11 Validation

- `scripts.yaml_activities`: parsed 10 activities.
- Direct `run_python_qg()` for M11: passed.
  - `word_count`: 1343 words, above the 1104 tolerated floor for target 1200.
  - `resources_search_attempted`: passed with two local
    `search_external` telemetry calls.
  - `vesum_verified`, `scaffolding_leak`, `russianisms_strict`,
    `activity_types`, `inject_activity_ids`, `engagement_floor`,
    `archetype_fit`, and resource/citation gates passed.
- Seeded hard wiki coverage: passed, 14/14 obligations covered.
- CLI `scripts/validate_mdx.py l2-uk-en a1 11`: passed.
- `npm run build:starlight`: passed; 101 pages built.
- Local Starlight restarted with `./services.sh restart starlight`.
- In-app browser checks for `/a1/how-many/`:
  - Lesson tab showed expected price, age, phone, and number-trap content.
  - Resources tab showed external learner resources only.
  - No internal `wiki/pedagogy` links, visible `Крок 1:` scaffolding,
    injection markers, or teacher/writer labels.
  - Hidden anchor `#repair-number-traps` returned to the Lesson tab and
    landed on the target.
- Targeted pre-commit passed for the 5 committed M11 files.
- `scripts/audit/lint_agent_trailer.py`: all branch commits pass.

## Verified Runtime State

Checked 2026-06-01T15:28Z:

- `git status --short --branch`: clean and synced at
  `codex/a1-m1-m7-golden-journey-2026-05-30...origin/codex/a1-m1-m7-golden-journey-2026-05-30`.
- `./services.sh status`: `sources` running on 8766, `api` running on 8765,
  `starlight` running on 4321.
- `curl -sS http://127.0.0.1:8765/api/delegate/active`:
  `{"total":0,"tasks":[]}`.

## Open Issues / In-Flight Notes

- This handoff refresh is the only in-flight edit in the current thread.
- Start a fresh Codex thread before authoring M12; current thread context is
  at the auto-compact threshold.
- Session setup still reports postmortem hygiene issues in
  `docs/bug-autopsies/codex-tool-capture.md` (`Symptom`, `Root cause`, and
  `Links` missing). This is out of scope for the A1 M12 slice.
- `MEMORY.md` is near its line budget; do not add memory unless necessary.
- ADR warnings and unrelated open issues remain out of scope.

## Next Steps

Continue M12 `this-and-that`:

1. Inspect `curriculum/l2-uk-en/plans/a1/this-and-that.yaml`, the locked wiki
   brief, resource obligations, and `build_wiki_manifest_data`.
2. Build the full M12 artifact set:
   `curriculum/l2-uk-en/a1/this-and-that/{module.md,activities.yaml,
   vocabulary.yaml,resources.yaml}` plus
   `starlight/src/content/docs/a1/this-and-that.mdx`.
3. Validate with activity parsing, direct `run_python_qg()`, seeded hard wiki
   coverage, MDX validation, `npm run build:starlight`, browser inspection,
   targeted pre-commit, and
   `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python scripts/audit/lint_agent_trailer.py`.
4. Commit and push with:
   `X-Agent: codex/a1-m1-m14-golden-journey`.

## Guardrails

- Use `./services.sh` for services.
- Use `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python`.
- Do not touch `.python-version`, `.yamllint`, `.markdownlint.json`,
  generated `status/*.json`, `audit/*-review.md`, or `review/*-review.md`.
- Do not use `sys.executable`.
- Do not use Gemini for review confidence.
