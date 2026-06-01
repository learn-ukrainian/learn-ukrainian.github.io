# Current - Codex Thread Handoff (2026-06-01T09:33+02:00)

Latest-Brief: docs/session-state/current.codex.md

## Active Work

- Repo: `/Users/krisztiankoos/projects/learn-ukrainian`
- Active worktree:
  `/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-m1-m7-golden-journey-2026-05-30`
- Branch: `codex/a1-m1-m7-golden-journey-2026-05-30`
- Latest implementation commit:
  `2bc13f6e8c feat(a1): add M10 colors module`

## Current Direction

- Codex owns A1 learner journey, tooling, infra, and tech debt.
- BIO remains Claude/BIO-owned; do not touch BIO files, PRs, worktrees, or
  delegates.
- Do not use Gemini for review confidence.
- Continue with M11 `how-many`. M1-M10 are now English-led student
  textbook/workbook pages and pass deterministic QG in this worktree.

## Latest M10 Update

Commit `2bc13f6e8c feat(a1): add M10 colors module` added:

- `curriculum/l2-uk-en/a1/colors/{module.md,activities.yaml,vocabulary.yaml,resources.yaml}`
- `starlight/src/content/docs/a1/colors.mdx`

M10 teaches `Якого кольору...?`, color adjective agreement, the soft `синій`
pattern, `синій` vs `блакитний`, `синьо-жовтий прапор`, safe appearance
chunks, and color-trap repair. Resources are external and learner-facing only.

Related rendering fix:

- `HashTabSync` is now server-rendered for newly assembled modules, and the
  assembler emits `<HashTabSync />`.
- The script retries hash scrolling long enough for client-only activity
  hydration to settle; local Chrome verified `#repair-color-traps` lands on
  the target heading.

Validation:

- Activities parsed: 10.
- Direct `run_python_qg()`: passed.
- Seeded hard wiki coverage: passed, 13/13.
- `scripts/validate_mdx.py l2-uk-en a1 10`: passed.
- `npm run build:starlight`: passed, 100 pages.
- Browser/content checks: no internal wiki links, teacher labels, visible
  scaffolding, or broken injection markers.
- Targeted pre-commit: passed.
- `scripts/audit/lint_agent_trailer.py`: passed for all branch commits.

## Next Target

Start M11 `how-many`:

1. Inspect `curriculum/l2-uk-en/plans/a1/how-many.yaml`.
2. Inspect the relevant locked wiki/pedagogy brief and source/resource sidecar.
3. Inspect `build_wiki_manifest_data` obligations.
4. Build `module.md`, `activities.yaml`, `vocabulary.yaml`, `resources.yaml`,
   and assembled `starlight/src/content/docs/a1/how-many.mdx`.
5. Run the same validation gates and commit with
   `X-Agent: codex/a1-m1-m14-golden-journey`.

## Guardrails

- Use `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python`.
- Use `./services.sh` for services.
- Do not touch `.python-version`, `.yamllint`, `.markdownlint.json`,
  generated `status/*.json`, `audit/*-review.md`, or `review/*-review.md`.
- Do not use `sys.executable`.
