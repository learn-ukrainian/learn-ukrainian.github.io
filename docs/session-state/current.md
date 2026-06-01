# Current Session Handoff

Generated-At: 2026-06-01T16:05Z

## Active Branch

- Worktree:
  `/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-m1-m7-golden-journey-2026-05-30`
- Branch: `codex/a1-m1-m7-golden-journey-2026-05-30`
- Latest implementation commit:
  `f305dc8347 feat(a1): add M12 this and that module`
- Previous handoff commit:
  `e3bc2bce16 docs(orchestration): refresh M12 handoff`

Recent commits:

- `f305dc8347 feat(a1): add M12 this and that module`
- `e3bc2bce16 docs(orchestration): refresh M12 handoff`
- `13cb273fda docs(orchestration): refresh M11 handoff`
- `ed01b995e4 feat(a1): add M11 how many module`
- `5031a7d99b docs(orchestration): refresh M11 handoff`

## Current Goal State

- M1-M12 are built as English-led A1 student textbook/workbook modules.
- M12 `this-and-that` is complete locally in commit `f305dc8347`.
- Next module: M13 `many-things`, then M14 `checkpoint-my-world`.
- BIO remains Claude/BIO-owned; do not touch BIO files, worktrees, delegates,
  or PRs.

## M12 Summary

Commit `f305dc8347 feat(a1): add M12 this and that module` added:

- `curriculum/l2-uk-en/a1/this-and-that/module.md`
- `curriculum/l2-uk-en/a1/this-and-that/activities.yaml`
- `curriculum/l2-uk-en/a1/this-and-that/vocabulary.yaml`
- `curriculum/l2-uk-en/a1/this-and-that/resources.yaml`
- `starlight/src/content/docs/a1/this-and-that.mdx`

It also fixed the shared `HashTabSync` helper so page hashes such as
`#repair-traps` are not overwritten by Starlight internal `#tab-panel-*`
hashes before scrolling. The required `docs/lesson-schema.yaml` component hash
was refreshed by the pre-commit schema drift hook.

M12 teaches `це` as the universal "this is" sentence starter, near forms
`цей/ця/це/ці`, far forms `той/та/те/ті`, `чи` choice questions, the two jobs
of `та`, fixed object chunks such as `цю книгу`, passive recognition for
`оцей/отой` and poetic forms, and repair drills for the locked L2 traps.

Local ignored telemetry exists for the resource-search gate:
`curriculum/l2-uk-en/a1/this-and-that/writer_tool_calls.json`.

## M12 Validation

- `scripts.yaml_activities`: parsed 8 activities.
- Direct `run_python_qg()` for M12: passed.
  - `word_count`: 1153 words, above the 1104 tolerated floor for target 1200.
  - `resources_search_attempted`: passed with two local `search_external`
    telemetry calls.
  - `vesum_verified`, `scaffolding_leak`, `russianisms_strict`,
    `activity_types`, `inject_activity_ids`, `engagement_floor`,
    `component_props`, and resource/citation gates passed.
- Seeded hard wiki coverage: passed, 18/18 obligations covered.
- CLI `scripts/validate_mdx.py l2-uk-en a1 12`: passed.
- `npm run build:starlight`: passed; 102 pages built.
- Local Starlight restarted with `./services.sh restart starlight`.
- In-app browser checks for `/a1/this-and-that/`:
  - Lesson tab showed expected demonstrative content and activities.
  - Resources tab showed external learner resources only.
  - No internal `wiki/pedagogy` links, visible `Крок 1:` scaffolding,
    injection markers, or teacher/writer labels.
  - Hidden anchor `#repair-traps` preserved the requested hash, selected the
    Lesson tab, and landed on the target heading after the shared
    `HashTabSync` fix.
- Targeted pre-commit passed for the 7 staged files.

## Verified Runtime State

Checked 2026-06-01T16:05Z:

- `./services.sh status`: `sources` running on 8766, `api` running on 8765,
  `starlight` running on 4321.
- `curl -sS http://127.0.0.1:8765/api/delegate/active`:
  `{"total":0,"tasks":[]}` before authoring M12.
- Branch is one implementation commit ahead of origin before this handoff
  refresh/push.

## Open Issues / In-Flight Notes

- This handoff refresh should be committed and pushed after M12.
- Session setup still reports postmortem hygiene issues in
  `docs/bug-autopsies/codex-tool-capture.md` (`Symptom`, `Root cause`, and
  `Links` missing). This is out of scope for the A1 slice.
- `MEMORY.md` is near its line budget; do not add memory unless necessary.
- ADR warnings and unrelated open issues remain out of scope.

## Next Steps

Continue M13 `many-things`:

1. Inspect `curriculum/l2-uk-en/plans/a1/many-things.yaml`, the locked wiki
   brief, resource obligations, and `build_wiki_manifest_data`.
2. Build the full M13 artifact set:
   `curriculum/l2-uk-en/a1/many-things/{module.md,activities.yaml,
   vocabulary.yaml,resources.yaml}` plus
   `starlight/src/content/docs/a1/many-things.mdx`.
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
