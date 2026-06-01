# Current Session Handoff

Generated-At: 2026-06-01T16:50Z

## Active Branch

- Worktree:
  `/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-m1-m7-golden-journey-2026-05-30`
- Branch: `codex/a1-m1-m7-golden-journey-2026-05-30`
- Latest implementation commit:
  `6b57fe4d70 feat(a1): add M14 checkpoint my world module`
- Latest handoff commit before this refresh:
  `df4252ac84 docs(orchestration): refresh M14 handoff`

Recent commits:

- `6b57fe4d70 feat(a1): add M14 checkpoint my world module`
- `df4252ac84 docs(orchestration): refresh M14 handoff`
- `f6cd35a701 feat(a1): add M13 many things module`
- `51a958a49b docs(orchestration): refresh M13 handoff`
- `f305dc8347 feat(a1): add M12 this and that module`

## Current Goal State

- M1-M14 are built as English-led A1 student textbook/workbook modules.
- M13 `many-things` and M14 `checkpoint-my-world` are complete and pushed.
- Next A1 module if continuing: M15 `what-i-like`.
- BIO remains Claude/BIO-owned; do not touch BIO files, worktrees, delegates,
  or PRs.

## M14 Summary

Commit `6b57fe4d70 feat(a1): add M14 checkpoint my world module` added:

- `curriculum/l2-uk-en/a1/checkpoint-my-world/module.md`
- `curriculum/l2-uk-en/a1/checkpoint-my-world/activities.yaml`
- `curriculum/l2-uk-en/a1/checkpoint-my-world/vocabulary.yaml`
- `curriculum/l2-uk-en/a1/checkpoint-my-world/resources.yaml`
- `starlight/src/content/docs/a1/checkpoint-my-world.mdx`

M14 is the A1.2 checkpoint for "my world." It reviews personal-pronoun chunks,
noun gender, `мій/моя/моє/мої`, adjective/color agreement, numbers/prices,
`цей/ця/це/ці` and `той/та/те/ті`, basic plural forms, and a learner-safe
street-market dialogue with `вишиванка`, `глечик`, `намисто`, and `писанки`.

Local ignored telemetry exists for the resource-search gate:
`curriculum/l2-uk-en/a1/checkpoint-my-world/writer_tool_calls.json`.

## M14 Validation

- `scripts.yaml_activities`: parsed 8 activities.
- Direct `run_python_qg()` for M14: passed.
  - `word_count`: 1327 words, above the 1104 tolerated floor for target 1200.
  - Resource-search gate passed with local `search_external` telemetry.
  - Russianism, VESUM, activity type, activity injection, scaffolding leak,
    resource, component prop, engagement, and contract gates passed.
- Direct seeded hard wiki coverage: passed, 17/17 obligations covered.
- CLI `scripts/validate_mdx.py l2-uk-en a1 14`: passed.
- `npm run build:starlight`: passed; 104 pages built.
- Local Starlight route `http://127.0.0.1:4321/a1/checkpoint-my-world/`
  returned `200 OK` after restarting Starlight once to refresh Astro's content
  cache.
- In-app Browser checks for `/a1/checkpoint-my-world/`:
  - Lesson tab showed the expected checkpoint content and inline practice.
  - Resources tab showed only external UkrainianLessons resources.
  - Fixed a rendered resource-title punctuation defect by changing the visible
    title to `Noun Genders in Ukrainian - Infographic`.
  - No internal `wiki/pedagogy` links, visible scaffolding, injection markers,
    or teacher/writer labels in the checked tab surfaces.
  - Hidden anchor `#repair-traps` selected the Lesson tab, preserved the hash,
    and landed on the repair table after the tab content settled.
- Targeted pre-commit passed for the 5 committed files.
- `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python scripts/audit/lint_agent_trailer.py`
  passed after the M14 commit; all 54 non-skipped commits in
  `origin/main..HEAD` carry `X-Agent` trailers.

## Verified Runtime State

After M14:

- `git status --short --branch`: clean and aligned with origin after pushing
  `6b57fe4d70`.
- `./services.sh status`: `sources` running on 8766, `api` running on 8765,
  `starlight` running on 4321.
- `curl -sS -I http://127.0.0.1:4321/a1/checkpoint-my-world/`: `200 OK`.

Initial delegation checks at the start of this goal also showed:

- `curl -sS http://127.0.0.1:8765/api/delegate/active`:
  `{"total":0,"tasks":[]}`.

## Open Issues / In-Flight Notes

- This handoff refresh should be committed and pushed after M14.
- Session setup still reports postmortem hygiene issues in
  `docs/bug-autopsies/codex-tool-capture.md` (`Symptom`, `Root cause`, and
  `Links` missing). This is out of scope for the A1 slice.
- `MEMORY.md` is near its line budget; do not add memory unless necessary.
- ADR warnings and unrelated open issues remain out of scope.

## Next Steps

If continuing the golden learner journey, start M15 `what-i-like`:

1. Inspect `curriculum/l2-uk-en/plans/a1/what-i-like.yaml`, the locked wiki
   brief, resource obligations, and `build_wiki_manifest_data`.
2. Build the full artifact set:
   `curriculum/l2-uk-en/a1/what-i-like/{module.md,activities.yaml,
   vocabulary.yaml,resources.yaml}` plus
   `starlight/src/content/docs/a1/what-i-like.mdx`.
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
