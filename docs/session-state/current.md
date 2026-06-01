# Current Session Handoff

Generated-At: 2026-06-01T16:28Z

## Active Branch

- Worktree:
  `/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-m1-m7-golden-journey-2026-05-30`
- Branch: `codex/a1-m1-m7-golden-journey-2026-05-30`
- Latest implementation commit:
  `f6cd35a701 feat(a1): add M13 many things module`
- Previous handoff commit:
  `51a958a49b docs(orchestration): refresh M13 handoff`

Recent commits:

- `f6cd35a701 feat(a1): add M13 many things module`
- `51a958a49b docs(orchestration): refresh M13 handoff`
- `f305dc8347 feat(a1): add M12 this and that module`
- `e3bc2bce16 docs(orchestration): refresh M12 handoff`
- `13cb273fda docs(orchestration): refresh M11 handoff`

## Current Goal State

- M1-M13 are built as English-led A1 student textbook/workbook modules.
- M13 `many-things` is complete and pushed in commit `f6cd35a701`.
- Next module: M14 `checkpoint-my-world`.
- BIO remains Claude/BIO-owned; do not touch BIO files, worktrees, delegates,
  or PRs.

## M13 Summary

Commit `f6cd35a701 feat(a1): add M13 many things module` added:

- `curriculum/l2-uk-en/a1/many-things/module.md`
- `curriculum/l2-uk-en/a1/many-things/activities.yaml`
- `curriculum/l2-uk-en/a1/many-things/vocabulary.yaml`
- `curriculum/l2-uk-en/a1/many-things/resources.yaml`
- `starlight/src/content/docs/a1/many-things.mdx`

M13 teaches common nominative plural noun chunks, plural adjective agreement
with **-і**, plural helpers **ці/ті/мої/які**, small plural-person pronoun
chunks, recognition for plural-only and collective singular words, and a
learner-safe number recap for **два/три/чотири** versus later **5+** chunks.

Local ignored telemetry exists for the resource-search gate:
`curriculum/l2-uk-en/a1/many-things/writer_tool_calls.json`.

## M13 Validation

- `scripts.yaml_activities`: parsed 8 activities.
- Direct `run_python_qg()` for M13: passed.
  - `word_count`: 1273 words, above the 1104 tolerated floor for target 1200.
  - `l2_exposure_floor`: passed with 15 Ukrainian dialogue lines.
  - `resources_search_attempted`: passed with two local `search_external`
    telemetry calls.
  - `vesum_verified`, `scaffolding_leak`, `russianisms_strict`,
    `activity_types`, `inject_activity_ids`, `engagement_floor`,
    `component_props`, and resource/citation gates passed.
- Direct seeded hard wiki coverage: passed, 18/18 obligations covered.
- CLI `scripts/validate_mdx.py l2-uk-en a1 13`: passed.
- `npm run build:starlight`: passed; 103 pages built.
- Local Starlight restarted with `./services.sh restart starlight`.
  - The service status command reported `starlight` as degraded after restart,
    but the dev server log showed Astro ready on `http://127.0.0.1:4321/` and
    Browser successfully loaded the page.
- In-app Browser checks for `/a1/many-things/`:
  - Lesson tab showed expected plural noun/adjective content and activities.
  - Resources tab showed external learner resources only.
  - No internal `wiki/pedagogy` links, visible scaffolding, injection markers,
    or teacher/writer labels.
  - Hidden anchor `#repair-traps` preserved the requested hash, selected the
    Lesson tab, and landed on the target heading.
- Targeted pre-commit passed for the 5 staged files.
- `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python scripts/audit/lint_agent_trailer.py`
  passed before the M13 commit.

## Verified Runtime State

Checked at the start of this slice:

- `git status --short --branch`: clean and aligned with origin at
  `51a958a49b`.
- `git log --oneline --decorate -10 --no-merges`: latest pushed handoff was
  `51a958a49b docs(orchestration): refresh M13 handoff`.
- `./services.sh status`: `sources` running on 8766, `api` running on 8765,
  `starlight` running on 4321.
- `curl -sS http://127.0.0.1:8765/api/delegate/active`:
  `{"total":0,"tasks":[]}`.

## Open Issues / In-Flight Notes

- This handoff refresh should be committed and pushed after M13.
- Session setup still reports postmortem hygiene issues in
  `docs/bug-autopsies/codex-tool-capture.md` (`Symptom`, `Root cause`, and
  `Links` missing). This is out of scope for the A1 slice.
- `MEMORY.md` is near its line budget; do not add memory unless necessary.
- ADR warnings and unrelated open issues remain out of scope.

## Next Steps

Continue M14 `checkpoint-my-world`:

1. Inspect `curriculum/l2-uk-en/plans/a1/checkpoint-my-world.yaml`, the locked
   wiki brief, resource obligations, and `build_wiki_manifest_data`.
2. Build the full M14 artifact set:
   `curriculum/l2-uk-en/a1/checkpoint-my-world/{module.md,activities.yaml,
   vocabulary.yaml,resources.yaml}` plus
   `starlight/src/content/docs/a1/checkpoint-my-world.mdx`.
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
