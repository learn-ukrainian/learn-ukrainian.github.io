# B2 M02 Quality Audit Report version: 0.1

Date: 2026-06-23
Auditor: codex/gpt-5
Worktree: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/b2-m02-quality-audit
Scope: B2 M02 `past-passive-participles`
Read-only audit phase: true
Durable report path: docs/audits/b2-quality-audit-2026-06-23.md

## Source Files Inspected

- `AGENTS.md`
- `docs/prompts/orchestrators/b2/quality-audit-orchestrator.md`
- `docs/prompts/orchestrators/shared/repo-rules.md`
- `docs/prompts/orchestrators/shared/validation-checklist.md`
- `docs/prompts/orchestrators/shared/review-output-schema.md`
- `docs/prompts/orchestrators/shared/telemetry-and-pr.md`
- `docs/audits/b2-preflight-readiness-remediation-2026-06-22.md`
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
- `scripts/config.py`
- `scripts/audit/config.py`
- `curriculum/l2-uk-en/curriculum.yaml`
- `curriculum/l2-uk-en/plans/b2/past-passive-participles.yaml`
- `wiki/grammar/b2/past-passive-participles.md`
- `wiki/grammar/b2/past-passive-participles.sources.yaml`
- `curriculum/l2-uk-en/b2/past-passive-participles/module.md`
- `curriculum/l2-uk-en/b2/past-passive-participles/activities.yaml`
- `curriculum/l2-uk-en/b2/past-passive-participles/vocabulary.yaml`
- `site/src/content/docs/b2/past-passive-participles.mdx`

## Repo Assumptions Verified

- B2 M02 is present on merged `origin/main` at commit `ce7dcb3d21`.
- B2 manifest sequence lists `passive-voice-system` then `past-passive-participles`.
- The module source directory contains `module.md`, `activities.yaml`, and `vocabulary.yaml`; no `resources.yaml` is present.
- Wiki article and source registry are present for the slug.
- The audit phase did not modify curriculum, wiki, or site files.

## Executive Summary

Verdict: PASS with non-blocking remediation recommended.

Blockers: 0
High issues: 0
Medium issues: 1
Low issues: 2

B2 M02 covers the locked plan objectives: suffix formation, agreement, attributive and predicative use, and avoidance of mechanical non-standard participle forms. The lesson arc is appropriate for B2: diagnostic contrast, formation models, agreement/syntax, register decisions, common errors, and an editing practice close. The workbook gives substantial practice volume and variety, and deterministic validators pass.

The main remediation need is a small source patch, not a rebuild: one central correction-table row is itself ungrammatical, and several morphology examples need cleaner notation. A planned `highlight-morphemes` activity type is represented by suffix-identification practice rather than the exact component type, so this should be treated as optional plan-fidelity polish unless the production prompt intends exact activity-type enforcement.

## Issues

### B2-M02-001 Correction table has an ungrammatical normative row

Severity: medium
Track level: B2
Module: M02 `past-passive-participles`

Files:

- `curriculum/l2-uk-en/b2/past-passive-participles/module.md`
- `site/src/content/docs/b2/past-passive-participles.mdx`

Evidence:

- In the `Помилка 4. Плутанина між дієприкметником і формою на -но, -то` table, the row has the incorrect side `Підписано заява лежить столі.` and the correction `Підписана лежить столі.`

Why matters:

- This row sits inside the central distinction between participial agreement and forms on `-но/-то`.
- The correction omits the noun and the preposition before `столі`, so the "correct" side is not a usable Ukrainian model.

Expected fix:

- Replace the row with a complete contrast such as `Підписано заява лежить на столі.` -> `Підписана заява лежить на столі.`

Batch recommendation:

- `b2-m02-source-polish`: targeted module source patch plus regenerated MDX.

### B2-M02-002 Formation notation is inconsistent in the morphology section

Severity: low
Track level: B2
Module: M02 `past-passive-participles`

Files:

- `curriculum/l2-uk-en/b2/past-passive-participles/module.md`
- `site/src/content/docs/b2/past-passive-participles.mdx`

Evidence:

- The support-pair sentence includes examples without arrows, such as `відкрити відкрита виставка`, `відновити відновлений парк`, `стерти стертий напис`, and `озброїти озброєний`.
- The `-н-` table has otherwise clear model rows, but a few stem-plus-suffix cells omit the visible `+` marker.

Why matters:

- This module teaches a morphological algorithm; inconsistent notation slightly weakens learner parsing of stem, suffix, and output.
- The issue does not change the normative forms, but it makes the pattern less visually disciplined.

Expected fix:

- Normalize the support pairs to `інфінітив -> форма` and use consistent stem `+ suffix` notation in the model table.

Batch recommendation:

- `b2-m02-source-polish`: targeted module source patch plus regenerated MDX.

### B2-M02-003 Planned `highlight-morphemes` activity type is substituted rather than exact

Severity: low
Track level: B2
Module: M02 `past-passive-participles`

Files:

- `curriculum/l2-uk-en/plans/b2/past-passive-participles.yaml`
- `curriculum/l2-uk-en/b2/past-passive-participles/activities.yaml`

Evidence:

- The plan lists required activity types: `fill-in`, `match-up`, `select`, and `highlight-morphemes`.
- The built activities include `fill-in`, `match-up`, `select`, `error-correction`, `mark-the-words`, `group-sort`, `reading`, and `essay-response`, but no literal `highlight-morphemes` activity.
- The workbook does include `Позначте суфікси`, a 14-item suffix-identification `fill-in`, which covers much of the planned morpheme-recognition intent.

Why matters:

- If the plan type is meant literally, the generated module misses a requested interaction affordance.
- If suffix-identification fill-ins are accepted as an equivalent, the plan or validator should make that substitution rule explicit.

Expected fix:

- Either add a real `highlight-morphemes` activity in a source patch, or document that suffix-identification `fill-in` activities satisfy this plan requirement for B2 morphology modules.

Batch recommendation:

- `b2-m02-source-polish` if exact component fidelity is required; otherwise defer as prompt/validator contract clarification.

## Coverage Matrices

### Plan Objective Coverage

| Objective | Coverage |
| --- | --- |
| Form past passive participles with `-н-`, `-ен-`, `-т-` | Covered in the morphology algorithm, model tables, suffix fill-ins, match-up, group-sort, and suffix-identification activities. |
| Agree participles with nouns by gender, number, and case | Covered in the agreement section, declension table, controlled examples, and grammar-check activities. |
| Use participles as attributes and as part of predicates | Covered through diagnostic contrasts, syntax section, official-style contrasts, and workbook selection tasks. |
| Avoid forms like `роблений` for `зроблений` with aspect/form awareness | Covered in explanation, common-error tables, error-correction tasks, and VESUM spot checks of selected normative/non-standard forms. |

### Wiki And Source Coverage

| Source expectation | Audit result |
| --- | --- |
| Wiki article present | Present: `wiki/grammar/b2/past-passive-participles.md`. |
| Source registry present | Present: `wiki/grammar/b2/past-passive-participles.sources.yaml`, seven textbook entries. |
| Module follows wiki norms | Yes: transitivity, suffix groups, alternations, active-preference guidance, `-но/-то` distinction, and active-suffix warnings are represented. |
| Missing contradictory sources | None found. |

### Activity Coverage

| Requirement | Result |
| --- | --- |
| Required `fill-in` | Present. |
| Required `match-up` | Present. |
| Required `select` | Present. |
| Required `highlight-morphemes` | No literal component; suffix-identification `fill-in` covers intent partially. |
| Workbook activity count | 11. |
| Inline activity count | 0. Acceptable for validation, but less aligned with in-lesson morphology discovery. |
| Total practice volume | Strong: 80+ counted items/tasks across workbook activities. |

### Vocabulary Coverage

| Metric | Result |
| --- | --- |
| Vocabulary item count | 40 entries, above B2 floor of 25. |
| Core grammar metalanguage | Present: `пасивний дієприкметник`, `дієприкметник минулого часу`, `перехідне дієслово`, `неперехідне дієслово`, `суфікс`, `чергування`, `форма на -но, -то`, `дієприкметниковий зворот`. |
| Register/editing vocabulary | Present: `офіційно-діловий стиль`, `лаконічність`, `перебудувати`, `відредагувати`, `відповідальний діяч`, `калька`. |
| Normative form examples | Present: `зроблений`, `спечений`, `кошений`, `зім'ятий`, `підписаний`, `погоджений`, `затверджений`. |

### Immersion And B2 Quality

| Check | Result |
| --- | --- |
| B2 Ukrainian immersion | Deterministic audit reports 99.9%, within target. |
| English leakage | Limited to translation/gloss metadata and technical file imports, not lesson prose. |
| Teaching arc | Strong: diagnostic contrast, discovery, explanation, syntax, style, common errors, editing practice, checklist. |
| Register control | Strong: official, scientific, journalistic, literary, and editing contexts are contrasted. |
| Engagement beats | Present: dialogues, cultural moment, warning/caution/tip boxes, real-world editing practice. |
| LLM fingerprint | No generic English AI openings or repetitive filler pattern found. |

### Validation Results

| Command | Result |
| --- | --- |
| `.venv/bin/python scripts/validate_activities.py l2-uk-en b2 2` | PASS. |
| `.venv/bin/python scripts/validate_vocab_yaml.py curriculum/l2-uk-en/b2/past-passive-participles/vocabulary.yaml` | PASS in build phase. |
| `.venv/bin/python scripts/generate_mdx.py l2-uk-en b2 2 --validate` | PASS. |
| `.venv/bin/python scripts/audit_module.py --skip-review curriculum/l2-uk-en/b2/past-passive-participles/module.md` | PASS; local generated audit/status/cache outputs removed before staging. |
| `.venv/bin/python scripts/validate_vocab_yaml.py curriculum/l2-uk-en/b2/past-passive-participles/vocabulary.yaml` | PASS in audit phase; 40 items. |
| `git diff --check` | PASS. |
| Protected/forbidden artifact diff gate | PASS before commit; only durable report changed. |

Deterministic audit note: the audit emitted generic UA-GEC calque suggestions with low aggregate severity while still passing. Manual context review did not promote those suggestions to issue findings because the surfaced terms occur in grammatical or ordinary Ukrainian contexts.

## Remediation Batching Plan

| Batch | Scope | Recommendation |
| --- | --- | --- |
| `b2-m02-source-polish` | Fix the correction-table row, normalize morphology notation, optionally add literal `highlight-morphemes`, regenerate MDX. | Recommended but non-blocking. |
| `b2-activity-contract-clarification` | Decide whether suffix-identification `fill-in` can satisfy planned `highlight-morphemes` requirements. | Defer to prompt/validator contract work if this recurs. |

## Independent Review Gate

Pending for audit-report PR. Required before merge: read-only independent-family blocker review of the audit report PR, preferably Claude Opus 4.8. Unresolved findings are blockers.

## Final Auditor Response Schema

Report written: `docs/audits/b2-quality-audit-2026-06-23.md`
Scope inspected: B2 M02 `past-passive-participles`
Blockers: 0
Issues recorded: 3
Recommended next batch: `b2-m02-source-polish`
Validation run: deterministic module audit, activity validation, vocabulary validation, MDX generation validation, and diff hygiene passed
Files changed: only durable audit report expected
swarm_used: false
swarm_label: none
swarm_note: solo audit; no helper swarm used
