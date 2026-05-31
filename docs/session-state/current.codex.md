# Current - Codex Thread Handoff (2026-05-31T21:24Z)

Latest-Brief: docs/session-state/current.codex.md

## Active Work

- Repo: `/Users/krisztiankoos/projects/learn-ukrainian`
- Active worktree:
  `/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-m1-m7-golden-journey-2026-05-30`
- Branch: `codex/a1-m1-m7-golden-journey-2026-05-30`
- Latest implementation commit before this handoff:
  `e8633c3145 feat(pipeline): gate A1 M1 resource coverage`

## Current Direction

- Codex owns A1 learner journey, tooling, infra, and tech debt.
- BIO remains Claude/BIO-owned; do not touch BIO files, PRs, or worktrees.
- Do not use Gemini for review confidence.
- Keep using `services.sh` for local services.
- Do not build M2/M3 yet. Finish the M1 template/gates first.

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

## Known Remaining M1 Gates

Full `run_python_qg()` still fails on pre-existing M1 content/template issues
outside the resource-coverage slice:

- `quiz_translate_explanations`: activity `act-9` translation items lack
  explanations.
- `plan_sections`: hand-authored English headings do not match the locked
  Ukrainian plan section names.
- `vesum_verified`: sung vowel strings `ааа`, `ооо`, `ііі`.
- `resources_search_attempted`: no writer tool-call telemetry for this
  hand-authored module.
- `long_uk_ceiling`: raw alphabet row is treated as a long unsupported
  Ukrainian run.
- `inject_activity_ids`: workbook-only activities are counted as unused by the
  old inject gate.
- `engagement_floor`: no callout and one `in this lesson` meta-narration hit.

These are the next infra/content-alignment targets. Do not interpret them as a
failure of the new `resource_coverage` gate.

## Next Steps

1. Push the branch if not already pushed after this handoff.
2. Decide whether to fix the remaining M1 gates by adapting gates to the new
   English-led archetype or by small content edits where the gate is still
   pedagogically correct.
3. Keep `current.orchestrator.md` in sync after the final push, then create or
   switch to a fresh Codex thread before context gets high.
