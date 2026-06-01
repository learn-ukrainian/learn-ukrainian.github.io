# Current Session Handoff

Generated-At: 2026-06-01T07:40Z

## Active Branch

- Worktree:
  `/Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-m1-m7-golden-journey-2026-05-30`
- Branch: `codex/a1-m1-m7-golden-journey-2026-05-30`
- Verified HEAD before this handoff edit:
  `42869f2bc4 docs(orchestration): refresh M10 handoff`
- Remote: clean and synced with
  `origin/codex/a1-m1-m7-golden-journey-2026-05-30` before this handoff edit.

Recent commits:

- `42869f2bc4 docs(orchestration): refresh M10 handoff`
- `2bc13f6e8c feat(a1): add M10 colors module`
- `36b7e734ca docs(orchestration): refresh M9 handoff`
- `48e6598fd9 feat(a1): add M9 what is it like module`
- `9e7c278760 docs(orchestration): refresh M8 handoff`
- `a675a2b1c5 feat(a1): add M8 things have gender module`

## Current Goal State

- M1-M10 are built as English-led A1 student textbook/workbook modules.
- M11 `how-many` is the next unfinished module.
- No M11 authoring files were changed in this session; this handoff only records
  the completed orientation and inspection before a context reset.
- BIO remains Claude/BIO-owned; do not touch BIO files, worktrees, delegates,
  or PRs.

## Verified Runtime State

Checked 2026-06-01T07:34Z:

- `git status --short --branch`: clean at
  `codex/a1-m1-m7-golden-journey-2026-05-30...origin/codex/a1-m1-m7-golden-journey-2026-05-30`.
- `./services.sh status`: `sources` running on 8766, `api` running on 8765,
  `starlight` running on 4321.
- `curl -sS http://127.0.0.1:8765/api/delegate/active`:
  `{"total":0,"tasks":[]}`.

## M11 Inspection Completed

Read these inputs for M11 `how-many`:

- Locked plan: `curriculum/l2-uk-en/plans/a1/how-many.yaml`
- Wiki review: `wiki/.reviews/pedagogy/a1/how-many-review-LOCKED.md`
- Wiki brief: `wiki/pedagogy/a1/how-many.md`
- Source sidecar: `wiki/pedagogy/a1/how-many.sources.yaml`
- Related OES article checked for context only:
  `wiki/linguistics/oes/numbers-currency.md`
- Discovery sidecar:
  `curriculum/l2-uk-en/a1/discovery/how-many.yaml`
- Existing module patterns inspected:
  `curriculum/l2-uk-en/a1/colors/{module.md,activities.yaml,vocabulary.yaml,resources.yaml}`
  and `curriculum/l2-uk-en/a1/what-is-it-like/activities.yaml`.

Hard M11 obligations from the plan/wiki:

- Teach numbers 0-100 productively, with hundreds/prices up to 1000 as useful
  chunks.
- Include three practical contexts: prices, age, and phone-number reading.
- Keep `Мені/тобі/їй + number + рік/роки/років` as a chunk, not a dative-case
  lesson.
- Keep `гривня/гривні/гривень` as a 1 / 2-4 / 5+ chunk, not a genitive-plural
  lesson.
- Explicitly repair the locked numerals L2-error table: `шість` not `шесть`,
  `п'ять` not `пять`, `сім` not `сєм/семь`, `сімнадцять`,
  `п'ятдесят`, `дев'яносто`, `Мені двадцять років` not English/Russian-style
  age calques, and `пів на шосту` not `пол-шостого`.
- Treat collective numerals (`двоє`, `троє`, `четверо`) as passive recognition
  only.
- Student-facing resources must be external learner resources only, with no
  internal wiki links.

## Open Issues / Hygiene Notes

- Session setup reported postmortem hygiene issues in
  `docs/bug-autopsies/codex-tool-capture.md` (`Symptom`, `Root cause`, and
  `Links` missing). This is out of scope for A1 M11.
- `MEMORY.md` is near its line budget; do not add memory unless necessary.
- ADR hygiene warnings and unrelated open issues remain out of scope.

## Next Steps

Continue in a fresh Codex thread from this exact worktree:

1. Re-run the restart commands below.
2. Generate direct `build_wiki_manifest_data` obligations for
   `a1/how-many` before writing.
3. Create the full M11 artifact set:
   `curriculum/l2-uk-en/a1/how-many/module.md`,
   `activities.yaml`, `vocabulary.yaml`, `resources.yaml`, and
   `starlight/src/content/docs/a1/how-many.mdx`.
4. Validate M11 with activity parsing, direct `run_python_qg()`, seeded hard
   wiki coverage, MDX assembly/validation, `npm run build:starlight`, browser
   inspection, targeted pre-commit, and
   `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python scripts/audit/lint_agent_trailer.py`.
5. Commit and push each safe slice with:
   `X-Agent: codex/a1-m1-m14-golden-journey`.

## Restart Commands

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/a1-m1-m7-golden-journey-2026-05-30
git status --short --branch
git log --oneline --decorate -10 --no-merges
./services.sh status
curl -sS http://127.0.0.1:8765/api/delegate/active
```

## Guardrails

- Use `./services.sh` for services.
- Use `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python` for
  Python.
- Do not touch `.python-version`, `.yamllint`, `.markdownlint.json`,
  generated `status/*.json`, `audit/*-review.md`, or `review/*-review.md`.
- Do not use `sys.executable`.
- Do not use Gemini for review confidence.
