# B1 Sequential Batch Build Template

Use this prompt when building a small B1 batch in a new agent thread.

The key pattern is: one PR may contain a batch, but writing stays sequential.
Each module gets its own build card, build, generation, certification, and fix
loop before the next module starts.

## Maintenance Notes

- Keep this template B1-specific.
- Do not add module-specific lessons permanently unless they are part of the
  current instantiation block.
- When review finds a recurring production failure, add it to the template.
- For another track, copy this structure into a new track-specific template and
  adjust level rules, source paths, activity rules, and validation expectations.

## BEGIN PROMPT

You are building production B1 curriculum modules for learn-ukrainian.

Goal: build a small batch, but preserve one-module-at-a-time quality through
module-tailored build cards.

Build exactly this batch:

- B1 M85 `text-register-formal` - Офіційний стиль
- B1 M86 `text-register-informal` - Розмовний стиль
- B1 M87 `text-compression` - Абревіатури та скорочення
- B1 M88 `reading-literature` - Читання художніх текстів
- B1 M89 `introductory-words` - Вставні слова та Однорідні члени речення
- B1 M90 `checkpoint-text-register` - Контрольна робота 8

Do not build, unlock, or modify M91+.

Use a clean worktree:

```bash
.worktrees/dispatch/codex/b1-m85-m90-text-register
```

Use branch:

```bash
codex/b1-m85-m90-text-register
```

Important: this is not one giant generation pass. Build sequentially:

1. Make a module-tailored build card for M85.
2. Build M85.
3. Generate MDX.
4. Certify M85.
5. Fix until clean.
6. Only then move to M86.

Repeat through M90. M90 must be built last because it is a checkpoint over
M85-M89.

For each module, before writing content, create a module-specific build card in
working notes. The card must include:

- module number, slug, title, focus, word target
- exact plan objectives
- required and recommended vocabulary
- discovery file findings
- wiki/research facts that must appear
- wiki/research facts to omit because they exceed B1 scope
- prior modules to reference
- expected lesson arc
- required tables
- required engagement boxes/callouts
- activity plan: inline vs workbook, types, target errors
- vocabulary plan
- known traps for this module
- final transition to next module

Use these required sources per module:

- `curriculum/l2-uk-en/plans/b1/{slug}.yaml`
- `curriculum/l2-uk-en/b1/discovery/{slug}.yaml`
- `wiki/grammar/b1/{slug}.md`
- `wiki/grammar/b1/{slug}.sources.yaml`
- relevant prior built modules when the plan or checkpoint depends on them

Production quality rules:

- B1 has no stress marks. Scan for U+0301.
- No wall-of-text sections.
- Every normal B1 module needs at least 6 useful engagement boxes/callouts;
  target 7+.
- Checkpoint M90 must be an assessment/review, not a new-topic lecture.
- Use examples before rules where practical.
- Use tables for register/style contrasts, punctuation, abbreviation patterns,
  and review matrices.
- Activities must be varied and realistic.
- No invalid activity schema fields.
- For cloze blanks, do not add per-blank `explanation` unless the schema allows
  it.
- Direct speech punctuation must be correct:
  - `«Текст», — сказала Олена.`
  - `«Текст?» — запитала Олена.`
- No copied scaffolding: `Крок N`, `Учень`, `manifest`, `checklist`,
  `phase 8`, stale module refs.
- No generic AI prose: "In this module...", "It is important to note...",
  filler transitions.

Files to create per module:

- `curriculum/l2-uk-en/b1/{slug}/module.md`
- `curriculum/l2-uk-en/b1/{slug}/activities.yaml`
- `curriculum/l2-uk-en/b1/{slug}/vocabulary.yaml`
- `curriculum/l2-uk-en/b1/{slug}/resources.yaml`
- generated MDX in `site/src/content/docs/b1/{slug}.mdx`

Update `site/src/content/docs/b1/index.mdx`:

- M85-M90 must become active.
- M91+ must remain locked.

Validation after each module:

```bash
.venv/bin/python scripts/generate_mdx.py l2-uk-en b1 {num} --validate
.venv/bin/python scripts/audit/certify_module.py b1 {slug} --skip-site-build --clean-qg-artifacts
```

After the full batch:

```bash
.venv/bin/python scripts/audit/lint_agent_trailer.py
git diff --check
```

Run targeted scans:

- no U+0301 stress marks in M85-M90 source or MDX
- no scaffold strings
- no bad direct-speech patterns
- M85-M90 active
- M91+ locked
- no `status/*.json`
- no `audit/*-review.md`
- no `review/*-review.md`
- no QG artifacts
- no telemetry DB/runtime state
- no unrelated files
- total changed files should be reasonable for 6 modules; explain if high

Independent quality gate:

- Use an independent-family LLM review/QG after deterministic validation.
- Minimum acceptable: every dimension >= 8.
- Target: 9+.
- If any dimension is below 8, fix and rerun.

Telemetry:

Persist module-build telemetry via:

```text
POST /api/telemetry/module-builds
```

Telemetry must include:

- modules: M85-M90
- writer model
- `swarm_used`: true/false
- `swarm_note`
- validation summary
- independent QG score
- note that this was sequential batch orchestration with module-tailored build
  cards

Commit trailer:

```text
X-Agent: codex/b1-m85-m90-text-register
```

Open a draft PR only. Do not merge or deploy.

PR body must include:

- modules built
- per-module validation results
- independent QG score
- telemetry id
- `swarm_used` and `swarm_note`
- confirmation that M91+ remain locked
- confirmation no forbidden artifacts are included
- summary of any wiki/research facts intentionally omitted for B1 scope

Final response must include:

- PR URL
- commit SHA
- validation commands and results
- QG score
- telemetry id
- residual concerns, if any

## END PROMPT
