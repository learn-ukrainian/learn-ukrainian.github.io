# Current - Codex Thread Handoff (2026-06-01T18:28+02:00)

Latest-Brief: docs/session-state/current.codex.md

## Active Work

- Repo: `/Users/krisztiankoos/projects/learn-ukrainian`
- Active worktree:
  `/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-m1-m7-golden-journey-2026-05-30`
- Branch: `codex/a1-m1-m7-golden-journey-2026-05-30`
- Latest implementation commit:
  `f6cd35a701 feat(a1): add M13 many things module`

## Current Direction

- Codex owns A1 learner journey, tooling, infra, and tech debt.
- BIO remains Claude/BIO-owned; do not touch BIO files, PRs, worktrees, or
  delegates.
- Do not use Gemini for review confidence.
- Continue with M14 `checkpoint-my-world`. M1-M13 are now English-led student
  textbook/workbook pages and pass deterministic QG in this worktree.

## Latest M13 Update

Commit `f6cd35a701 feat(a1): add M13 many things module` added:

- `curriculum/l2-uk-en/a1/many-things/module.md`
- `curriculum/l2-uk-en/a1/many-things/activities.yaml`
- `curriculum/l2-uk-en/a1/many-things/vocabulary.yaml`
- `curriculum/l2-uk-en/a1/many-things/resources.yaml`
- `starlight/src/content/docs/a1/many-things.mdx`

M13 is English-led A1.2 grammar-first-contact content for plural things:
nominative plural noun chunks, plural adjective **-і**, plural helpers
`ці/ті/мої/які`, small pronoun chunks for `ми/ви/нас/вас/нам/вам/нами/вами`,
plural-only and collective-singular recognition, and a controlled recap of
`два/три/чотири` versus later `5+` chunks.

Validation after M13:

- `scripts.yaml_activities`: parsed 8 activities.
- Direct `run_python_qg()` for M13: passed.
- Direct seeded hard wiki coverage: passed, 18/18 obligations covered.
- CLI `scripts/validate_mdx.py l2-uk-en a1 13`: passed.
- `npm run build:starlight`: passed; 103 pages built.
- Local Starlight restarted with `./services.sh restart starlight`.
- Browser inspection for `/a1/many-things/`:
  - Lesson tab showed expected plural content.
  - Resources tab showed only external learner-facing resources.
  - No internal wiki links, teacher labels, visible scaffolding, or injection
    markers.
  - `#repair-traps` selected the Lesson tab, preserved the requested hash, and
    landed on the target heading.
- Targeted pre-commit passed.
- Agent-trailer lint passed before the M13 commit.

Local ignored telemetry exists for the direct QG resource-search gate:
`curriculum/l2-uk-en/a1/many-things/writer_tool_calls.json`.

## Next Target

Start M14 `checkpoint-my-world`:

1. Inspect `curriculum/l2-uk-en/plans/a1/checkpoint-my-world.yaml`.
2. Inspect the relevant locked wiki/pedagogy brief and source/resource sidecar.
3. Inspect `build_wiki_manifest_data` obligations.
4. Build `module.md`, `activities.yaml`, `vocabulary.yaml`, `resources.yaml`,
   and assembled `starlight/src/content/docs/a1/checkpoint-my-world.mdx`.
5. Run the same validation gates and commit with
   `X-Agent: codex/a1-m1-m14-golden-journey`.

## Guardrails

- Use `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python`.
- Use `./services.sh` for services.
- Do not touch `.python-version`, `.yamllint`, `.markdownlint.json`,
  generated `status/*.json`, `audit/*-review.md`, or `review/*-review.md`.
- Do not use `sys.executable`.
