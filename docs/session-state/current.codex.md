# Current - Codex Thread Handoff (2026-06-01T10:03+02:00)

Latest-Brief: docs/session-state/current.codex.md

## Active Work

- Repo: `/Users/krisztiankoos/projects/learn-ukrainian`
- Active worktree:
  `/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-m1-m7-golden-journey-2026-05-30`
- Branch: `codex/a1-m1-m7-golden-journey-2026-05-30`
- Latest implementation commit:
  `ed01b995e4 feat(a1): add M11 how many module`

## Current Direction

- Codex owns A1 learner journey, tooling, infra, and tech debt.
- BIO remains Claude/BIO-owned; do not touch BIO files, PRs, worktrees, or
  delegates.
- Do not use Gemini for review confidence.
- Continue with M12 `this-and-that`. M1-M11 are now English-led student
  textbook/workbook pages and pass deterministic QG in this worktree.

## Latest M11 Update

Commit `ed01b995e4 feat(a1): add M11 how many module` added:

- `curriculum/l2-uk-en/a1/how-many/module.md`
- `curriculum/l2-uk-en/a1/how-many/activities.yaml`
- `curriculum/l2-uk-en/a1/how-many/vocabulary.yaml`
- `curriculum/l2-uk-en/a1/how-many/resources.yaml`
- `starlight/src/content/docs/a1/how-many.mdx`

M11 is English-led A1.2 grammar-first-contact content for counting, prices,
age, and phone numbers. It covers `нуль` through `сто`, hundreds/prices through
`тисяча гривень`, `гривня/гривні/гривень`, `рік/роки/років`,
`Скільки коштує...?`, `Скільки тобі років?`, `Мені ... років`, and
phone-number groups. It explicitly repairs the locked number traps:
`п'ять столів`, `Котра година?`, `Мені 20 років`,
`перше січня / сьоме травня`, `п'ятдесят / шістдесят`, and
`тисяча / мільйон`, plus common numeral spellings such as `шість`, `сім`,
`сімнадцять`, and `дев'яносто`.

Validation after M11:

- `scripts.yaml_activities`: parsed 10 activities.
- Direct `run_python_qg()` for M11: passed.
- Direct seeded hard wiki coverage: passed, 14/14 obligations covered.
- CLI `scripts/validate_mdx.py l2-uk-en a1 11`: passed.
- `npm run build:starlight`: passed; 101 pages built.
- Local Starlight restarted with `./services.sh restart starlight`.
- Browser inspection for `/a1/how-many/`:
  - Lesson tab showed price dialogue, age chunks, phone-number chunks, and
    number-trap repair.
  - Resources tab showed only external learner-facing resources.
  - No internal wiki links, visible step scaffolding, injection markers, or
    teacher/writer labels.
  - Hidden anchor `#repair-number-traps` switched back to Lesson and landed on
    the target heading.
- Targeted pre-commit passed for the 5 committed M11 files.
- `scripts/audit/lint_agent_trailer.py`: all branch commits pass.

## Next Target

Start M12 `this-and-that`:

1. Inspect `curriculum/l2-uk-en/plans/a1/this-and-that.yaml`.
2. Inspect the relevant locked wiki/pedagogy brief and source/resource sidecar.
3. Inspect `build_wiki_manifest_data` obligations.
4. Build `module.md`, `activities.yaml`, `vocabulary.yaml`, `resources.yaml`,
   and assembled `starlight/src/content/docs/a1/this-and-that.mdx`.
5. Run the same validation gates and commit with
   `X-Agent: codex/a1-m1-m14-golden-journey`.

## Guardrails

- Use `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python`.
- Use `./services.sh` for services.
- Do not touch `.python-version`, `.yamllint`, `.markdownlint.json`,
  generated `status/*.json`, `audit/*-review.md`, or `review/*-review.md`.
- Do not use `sys.executable`.
