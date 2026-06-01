# Current - Codex Thread Handoff (2026-06-01T18:05+02:00)

Latest-Brief: docs/session-state/current.codex.md

## Active Work

- Repo: `/Users/krisztiankoos/projects/learn-ukrainian`
- Active worktree:
  `/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-m1-m7-golden-journey-2026-05-30`
- Branch: `codex/a1-m1-m7-golden-journey-2026-05-30`
- Latest implementation commit:
  `f305dc8347 feat(a1): add M12 this and that module`

## Current Direction

- Codex owns A1 learner journey, tooling, infra, and tech debt.
- BIO remains Claude/BIO-owned; do not touch BIO files, PRs, worktrees, or
  delegates.
- Do not use Gemini for review confidence.
- Continue with M13 `many-things`. M1-M12 are now English-led student
  textbook/workbook pages and pass deterministic QG in this worktree.

## Latest M12 Update

Commit `f305dc8347 feat(a1): add M12 this and that module` added:

- `curriculum/l2-uk-en/a1/this-and-that/module.md`
- `curriculum/l2-uk-en/a1/this-and-that/activities.yaml`
- `curriculum/l2-uk-en/a1/this-and-that/vocabulary.yaml`
- `curriculum/l2-uk-en/a1/this-and-that/resources.yaml`
- `starlight/src/content/docs/a1/this-and-that.mdx`

It also updated `starlight/src/components/HashTabSync.tsx` and the generated
`docs/lesson-schema.yaml` component hash so learner-facing anchors in tabbed
pages survive Starlight's internal tab-panel hash replacement.

M12 is English-led A1.2 grammar-first-contact content for demonstratives:
`це`, `цей/ця/це/ці`, `той/та/те/ті`, `чи`, noun-gender agreement, near/far
choice questions, `та` as demonstrative vs connector, `цю книгу` as a fixed
object chunk, passive recognition for emphatic/poetic forms, and repair of the
locked L2 traps.

Validation after M12:

- `scripts.yaml_activities`: parsed 8 activities.
- Direct `run_python_qg()` for M12: passed.
- Direct seeded hard wiki coverage: passed, 18/18 obligations covered.
- CLI `scripts/validate_mdx.py l2-uk-en a1 12`: passed.
- `npm run build:starlight`: passed; 102 pages built.
- Local Starlight restarted with `./services.sh restart starlight`.
- Browser inspection for `/a1/this-and-that/`:
  - Lesson tab showed expected demonstrative content.
  - Resources tab showed only external learner-facing resources.
  - No internal wiki links, teacher labels, visible scaffolding, or injection
    markers.
  - `#repair-traps` selected the Lesson tab, preserved the requested hash, and
    landed on the target heading.
- Targeted pre-commit passed after staging the schema hash refresh.

## Next Target

Start M13 `many-things`:

1. Inspect `curriculum/l2-uk-en/plans/a1/many-things.yaml`.
2. Inspect the relevant locked wiki/pedagogy brief and source/resource sidecar.
3. Inspect `build_wiki_manifest_data` obligations.
4. Build `module.md`, `activities.yaml`, `vocabulary.yaml`, `resources.yaml`,
   and assembled `starlight/src/content/docs/a1/many-things.mdx`.
5. Run the same validation gates and commit with
   `X-Agent: codex/a1-m1-m14-golden-journey`.

## Guardrails

- Use `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python`.
- Use `./services.sh` for services.
- Do not touch `.python-version`, `.yamllint`, `.markdownlint.json`,
  generated `status/*.json`, `audit/*-review.md`, or `review/*-review.md`.
- Do not use `sys.executable`.
