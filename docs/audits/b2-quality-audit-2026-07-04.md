# B2 Final Quality Audit

Report version: 0.1
Date: 2026-07-04
Auditor: Codex
Worktree: `/Users/krisztiankoos/.codex/worktrees/1b15/learn-ukrainian`
Branch: `codex/b2-quality-audit-final-sweep`
Scope: B2 M01-M93, including checkpoints and final exam
Read-only curriculum audit: true
Durable report path: `docs/audits/b2-quality-audit-2026-07-04.md`

## Executive Summary

Status: not ready to declare B2 final-quality complete.

The built-module inventory is complete: `curriculum/l2-uk-en/curriculum.yaml`
lists 93 B2 modules, and every listed slug has the expected plan, module,
activities, vocabulary, wiki, and site mirror files. There are no planned but
unbuilt B2 modules in this checkout.

The quality gate state is not complete. The deterministic level audit reports
all 93 B2 modules with missing current LLM-QG records: current DB 0, current
file 0, stale 0, missing 93. Because the assignment is a final post-build
quality sweep, missing LLM-QG coverage is a blocker for final certification,
even where the lesson content looks usable by subjective inspection.

The deterministic no-fix module audit was run for all 93 modules. It passed 8
modules and failed 85 modules. The failures are mostly systemic: outline
section matching, richness and engagement gates, word target gaps, checkpoint
format gates, and style/pedagogy checks. Several failures may reflect a V6
module-schema/audit-gate mismatch, but they still block a final quality claim
until the validator/content contract is resolved and rerun.

Blocker issue classes: 2
Total issue classes recorded: 14
Modules with no deterministic audit failure: M11, M12, M13, M83, M84, M85,
M86, M93

No curriculum, wiki, site, telemetry, or generated audit/status artifacts are
included in this PR.

## Source Assumptions Verified

- B2 scope comes from `curriculum/l2-uk-en/curriculum.yaml`.
- B2 live immersion policy in `scripts/config.py` is 100% Ukrainian for B2.
- Audit-side B2 grammar constraints in `scripts/audit/config.py` allow full
  case system, full aspect, participles, adverbial participles, complex
  subordination, up to 35 words per sentence, and up to 6 clauses.
- Audit-side B2 module thresholds in `scripts/audit/config.py` set the core
  word target from `LEVEL_THRESHOLDS['B2']`, with 25 vocabulary items, 6
  engagement items, 90-100% immersion, and no transliteration.
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md` still states B2 should be
  full Ukrainian immersion, advanced metalanguage, rich syntax, register
  control, and language-practice activities rather than topic trivia.

## Commands And Coverage

Deterministic level quality summary:

```bash
.venv/bin/python scripts/audit/module_quality_audit.py --level b2 --format json --include-findings --output /tmp/b2-quality-audit-2026-07-04.json
```

Outcome: success. Output was kept under `/tmp` and summarized here; no JSON
artifact is committed.

Deterministic module audit coverage:

```bash
.venv/bin/python scripts/audit_module.py --skip-review curriculum/l2-uk-en/b2/<slug>/module.md
```

Outcome: run for every B2 slug M01-M93 without `--fix`. After each run, the
known generated `.cache/lemma-frequency-b2-<num>.json`, curriculum `audit/`,
and curriculum `status/` outputs were removed. The audit-created
`curriculum/l2-uk-en/vocabulary.db` mutation was restored before report
delivery.

No builds were run.

## LLM-QG Coverage

Current DB LLM-QG modules: 0
Current file-only LLM-QG modules: 0
Stale LLM-QG modules: 0
Missing LLM-QG modules: 93
Modules needing LLM review: 93

Affected slugs: `passive-voice-system`, `past-passive-participles`,
`b2-impersonal-passive`, `dim-zhytlo`, `reflexive-passive`,
`third-person-plural-passive`, `passive-in-context`, `pobut-shchodenne`,
`active-participles-present`, `checkpoint-passive-voice`,
`active-participles-past`, `participles-vs-relative-clauses`,
`zdorovya-i-medytsyna`, `phrases-word-combinations`, `predicate-types`,
`secondary-sentence-members`, `sport-i-dozvillia`,
`b2-one-member-sentences`, `homogeneous-members`, `detached-members`,
`checkpoint-syntax-i`, `parenthetical-expressions`, `multi-clause-sentences`,
`kharchuvannia-i-kukhnia`, `correlative-constructions`,
`emphasis-and-inversion`, `stylistic-connectors`, `kupivlia-i-servisy`,
`complex-syntax-ellipsis-parcelling`, `direct-indirect-speech`,
`checkpoint-syntax-ii`, `phonetic-stylistic-devices`,
`lexical-stylistic-devices`, `syntactic-stylistic-devices`,
`mistsia-i-oriientyry`, `register-formal-informal`,
`register-business-ukrainian`, `register-formal-written`,
`tradytsii-i-zvychai`, `register-literary-ukrainian`,
`register-public-discourse`, `checkpoint-register-domain`,
`register-practice-cross-register-rewriting`, `politics-government-vocabulary`,
`law-justice-vocabulary`, `economics-business-vocabulary`,
`genitive-advanced`, `dative-advanced`, `instrumental-advanced`,
`questions-deliberative-rhetorical`, `advanced-case-semantics`,
`pronoun-system-advanced`, `checkpoint-cases-morphology`,
`aspect-nuances-secondary-imperfectivization`,
`aspect-nuances-imperative-infinitive`, `pluperfect-tense`,
`conditional-mood-particles`, `numeral-declension-time-dates`,
`numeral-declension-compound-numbers`, `word-formation-person-suffixes`,
`word-formation-abstract-nouns`, `word-formation-place-object-names`,
`word-formation-adjective-adverbs`, `advanced-conjunctions-i`,
`advanced-conjunctions-ii`, `checkpoint-morphology`,
`synonymy-types-and-rows`, `synonymy-in-registers`,
`synonymy-practice-precision`, `proverbs-work-wisdom-character`,
`proverbs-nature-time-caution`, `set-expressions-combined`,
`checkpoint-lexicology-i`, `idioms-somatic`, `idioms-animals`,
`idioms-nature`, `neologisms-borrowings`, `checkpoint-lexicology-ii`,
`professional-email-basics`, `professional-email-advanced`,
`professional-reports`, `academic-writing`, `text-analysis`,
`news-analysis`, `presentation-skills`, `discussion-debate`,
`checkpoint-communication`, `tekhnolohii-ta-shi`, `nauka-i-doslidzhennia`,
`mystetstvo-i-literatura`, `modern-diaspora`, `religion-in-ukraine`,
`b2-final-exam`.

Severity rationale: this is blocker-level for the final sweep because the
current checkout cannot prove that any B2 module has a current persisted LLM
quality-gate result. It is not proof that all modules are pedagogically bad;
it is proof that the final gate is not complete.

## Complete Issue Inventory

### B2-QA-001 Missing Current LLM-QG For Every Built B2 Module

Severity: blocker
Modules: M01-M93
Files:
- `data/telemetry/llm_qg.db` expected by audit tooling, not committed
- `curriculum/l2-uk-en/b2/*/llm_qg.json` absent for B2 modules
Evidence:
- `module_quality_audit.py` summary: current DB 0, current file-only 0, stale
  0, missing 93.
Why it matters:
- Final post-build quality cannot be claimed without persisted current LLM-QG
  coverage or an explicit accepted replacement gate.
Expected fix:
- Run or restore current LLM-QG records for all 93 B2 modules and persist them
  through the approved store. Do not commit telemetry DB files.
Batch recommendation: Batch R1.

### B2-QA-002 Deterministic Module Audit Fails 85 Of 93 B2 Modules

Severity: blocker
Modules: all failing rows in the matrix below
Files:
- `curriculum/l2-uk-en/b2/*/module.md`
- `curriculum/l2-uk-en/b2/*/activities.yaml`
- `curriculum/l2-uk-en/b2/*/vocabulary.yaml`
- `curriculum/l2-uk-en/plans/b2/*.yaml`
Evidence:
- All 93 modules were audited with `scripts/audit_module.py --skip-review`.
  Results: 8 PASS, 85 FAIL.
Why it matters:
- Even if some failures are audit-contract drift, a final sweep cannot mark B2
  complete while the official deterministic audit fails most modules.
Expected fix:
- First triage the V6 outline/summary/checkpoint contract versus the audit
  gates, then remediate actual content gaps and rerun all 93.
Batch recommendation: Batches R2-R6.

### B2-QA-003 Learner-Facing English-Led Lines In B2 Modules

Severity: high
Modules: M01 `passive-voice-system`, M23 `multi-clause-sentences`, M31
`checkpoint-syntax-ii`, M80 `professional-email-advanced`, M81
`professional-reports`
Files:
- `curriculum/l2-uk-en/b2/passive-voice-system/module.md`
- `curriculum/l2-uk-en/b2/multi-clause-sentences/module.md`
- `curriculum/l2-uk-en/b2/checkpoint-syntax-ii/module.md`
- `curriculum/l2-uk-en/b2/professional-email-advanced/module.md`
- `curriculum/l2-uk-en/b2/professional-reports/module.md`
Evidence:
- The level quality audit reports 5 surface-fail modules and 8 critical
  English-led learner-facing lines.
Why it matters:
- B2 policy is Ukrainian-led/full-immersion, with English limited to narrow
  support contexts such as vocabulary translations.
Expected fix:
- Rewrite the flagged lines in Ukrainian or move them into allowed translation
  contexts.
Batch recommendation: Batch R3 for M01/M23/M31, Batch R4 for M80/M81.

### B2-QA-004 Plan Outline Matching Fails Broadly

Severity: high
Modules: 79 modules
Evidence:
- The all-module audit detected outline/section mismatches in 79 failing
  modules.
Why it matters:
- If the plan outline and module headings do not align, automated plan-fidelity
  checks cannot prove that objectives and section budgets were met.
Expected fix:
- Decide whether the V6 module heading style or the audit matcher is the
  source of truth, then align the content or validator.
Batch recommendation: Batch R2 before content edits.

### B2-QA-005 Richness And Engagement Gates Fail Broadly

Severity: high
Modules: 77 modules
Evidence:
- The deterministic audit reports richness failures in 77 modules and
  engagement failures in the same systemic cluster.
Why it matters:
- B2 modules should support abstraction, register control, and production with
  examples, tasks, and usable scaffolding, not just taxonomy.
Expected fix:
- After validator triage, expand true content-thin modules with authentic
  scenarios, extended transformations, argumentation, and production tasks.
Batch recommendation: Batches R3-R5.

### B2-QA-006 Word Target Misses Are Widespread

Severity: high
Modules: 57 modules
Evidence:
- `audit_module.py` reports `Words` failures in 57 modules against the 4000
  B2 target.
Why it matters:
- Word targets are minimums in this repo. Under-target modules may still be
  usable, but the final audit cannot waive the floor without an explicit
  policy decision.
Expected fix:
- Expand under-target modules or record an accepted profile-specific exception.
Batch recommendation: Batches R3-R5.

### B2-QA-007 Checkpoint Format Failures

Severity: high
Modules: M10, M21, M53, M66, M73, M78, M87
Evidence:
- The deterministic audit reports checkpoint format errors in seven checkpoint
  modules.
Why it matters:
- Checkpoints are the learner's synthesis gates; malformed checkpoint structure
  undermines readiness signals across B2 phases.
Expected fix:
- Normalize checkpoint sections and task structure after resolving V6 audit
  expectations.
Batch recommendation: Batch R5.

### B2-QA-008 Activity Type And Advanced-Activity Gaps

Severity: medium
Modules: M01, M02, M03, M04, M06, M09, M72
Evidence:
- The deterministic audit reports unique activity-type failures in 7 modules
  and missing advanced activity expectations in 6 modules.
Why it matters:
- B2 practice should include production, argumentation, editing, and register
  control; narrow activity variety reduces skill transfer.
Expected fix:
- Add or rebalance activity types after confirming whether the current YAML
  V2/V6 shape is being read correctly by the audit.
Batch recommendation: Batches R3 and R5.

### B2-QA-009 Expected Summary Heading Missing

Severity: medium
Modules: M14, M15, M16, M19, M22, M23, M50, M51, M52, M53, M66, M67, M88,
M90, M91
Evidence:
- The deterministic audit reports missing `## Summary` structure checks for
  15 modules.
Why it matters:
- This may be a heading-contract mismatch, but until resolved it prevents
  deterministic validation of the expected closing synthesis.
Expected fix:
- Align summary headings with the current audit contract or update the contract
  if bilingual/V6 headings are intended.
Batch recommendation: Batch R2.

### B2-QA-010 M43 Resource Pack Has Missing Corpus Chunks

Severity: medium
Module: M43 `register-practice-cross-register-rewriting`
Files:
- `curriculum/l2-uk-en/b2/register-practice-cross-register-rewriting/resources.yaml`
- `curriculum/l2-uk-en/b2/register-practice-cross-register-rewriting/module.md`
Evidence:
- Read-only helper inspection found every cited textbook reference in
  `resources.yaml` marked with missing corpus data and no chunk ID in prompt.
Why it matters:
- A register-rewriting module should be source-auditable if it presents itself
  as grounded in controlled source material.
Expected fix:
- Add real corpus chunks and chunk IDs, or narrow the module/resource wording
  to explicitly synthetic scenario practice.
Batch recommendation: Batch R4.

### B2-QA-011 M04 Thematic Module Is Thin For B2

Severity: medium
Module: M04 `dim-zhytlo`
Evidence:
- Helper inspection measured the module below the 4000-word plan target and
  found limited depth for renting, repairs, neighborhood issues, and service
  negotiation.
Why it matters:
- Thematic B2 modules should support extended speaking/writing and register
  shifts, not only vocabulary coverage.
Expected fix:
- Add authentic housing-service scenarios, complaint/request production, and
  comparison of ad copy versus spoken negotiation.
Batch recommendation: Batch R3.

### B2-QA-012 M05-M06 Passive Variants Are Too Thin As Standalone Units

Severity: high
Modules: M05 `reflexive-passive`, M06 `third-person-plural-passive`
Evidence:
- Helper inspection found both far under the 4000-word target and only six
  section blocks each.
Why it matters:
- These are B2 passive-variant modules; they need enough register-sensitive
  variation, editing practice, and production to justify standalone placement.
Expected fix:
- Expand with procedural examples, contrastive rewrites, and production tasks,
  or merge/rebalance the material into the passive cluster.
Batch recommendation: Batch R3.

### B2-QA-013 M25-M27 Syntax/Style Modules Are Compressed

Severity: medium
Modules: M25 `correlative-constructions`, M26 `emphasis-and-inversion`, M27
`stylistic-connectors`
Evidence:
- Helper inspection found the modules below target and weighted toward taxonomy
  rather than enough worked transformations and extended practice.
Why it matters:
- These are core B2 syntax/style modules; learners need context showing
  rhetorical effect and register, not only definitions.
Expected fix:
- Add longer excerpts, rewrite drills, and short argumentation tasks.
Batch recommendation: Batch R3.

### B2-QA-014 M28-M30 Need One More Production-Heavy Scenario Each

Severity: low
Modules: M28 `kupivlia-i-servisy`, M29 `complex-syntax-ellipsis-parcelling`,
M30 `direct-indirect-speech`
Evidence:
- Helper inspection found each slightly under the plan target.
Why it matters:
- These modules are close to acceptable, but late-B2 consumer dispute,
  ellipsis/parcelling, and quotation-control work benefits from one additional
  substantial scenario.
Expected fix:
- Add one production-heavy scenario per module.
Batch recommendation: Batch R3.

## Module Matrix

| Module | Slug | Built/source mirror | LLM-QG | Deterministic audit | Primary categories |
| --- | --- | --- | --- | --- | --- |
| M01 | `passive-voice-system` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, activity-types, engagement, pedagogy, ua-gec, missing-advanced-activity |
| M02 | `past-passive-participles` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, activity-types, engagement, pedagogy, ua-gec, missing-advanced-activity |
| M03 | `b2-impersonal-passive` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, activity-types, engagement, pedagogy, ua-gec, missing-advanced-activity |
| M04 | `dim-zhytlo` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, activity-types, engagement, pedagogy, ua-gec, missing-advanced-activity |
| M05 | `reflexive-passive` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline |
| M06 | `third-person-plural-passive` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, activity-types, engagement, pedagogy, ua-gec, missing-advanced-activity |
| M07 | `passive-in-context` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, activity-types, engagement, pedagogy, ua-gec |
| M08 | `pobut-shchodenne` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M09 | `active-participles-present` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, activity-types, engagement, pedagogy, ua-gec |
| M10 | `checkpoint-passive-voice` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, checkpoint-format, richness, word-count, engagement, pedagogy, ua-gec |
| M11 | `active-participles-past` | plan,module,activities,vocab,wiki,site present | missing | PASS | none |
| M12 | `participles-vs-relative-clauses` | plan,module,activities,vocab,wiki,site present | missing | PASS | none |
| M13 | `zdorovya-i-medytsyna` | plan,module,activities,vocab,wiki,site present | missing | PASS | none |
| M14 | `phrases-word-combinations` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, missing-summary, richness, word-count, engagement, pedagogy, ua-gec |
| M15 | `predicate-types` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, missing-summary, richness, word-count, engagement, pedagogy, ua-gec |
| M16 | `secondary-sentence-members` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, missing-summary, richness, word-count, engagement, pedagogy, ua-gec |
| M17 | `sport-i-dozvillia` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M18 | `b2-one-member-sentences` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M19 | `homogeneous-members` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, missing-summary |
| M20 | `detached-members` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M21 | `checkpoint-syntax-i` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, checkpoint-format, richness, word-count, engagement, pedagogy, ua-gec |
| M22 | `parenthetical-expressions` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, missing-summary, richness, word-count, engagement, pedagogy, ua-gec |
| M23 | `multi-clause-sentences` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, missing-summary, richness, word-count, engagement, pedagogy, ua-gec |
| M24 | `kharchuvannia-i-kukhnia` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M25 | `correlative-constructions` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M26 | `emphasis-and-inversion` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M27 | `stylistic-connectors` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M28 | `kupivlia-i-servisy` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M29 | `complex-syntax-ellipsis-parcelling` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M30 | `direct-indirect-speech` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M31 | `checkpoint-syntax-ii` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M32 | `phonetic-stylistic-devices` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M33 | `lexical-stylistic-devices` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, engagement, pedagogy, ua-gec |
| M34 | `syntactic-stylistic-devices` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, engagement, pedagogy, ua-gec |
| M35 | `mistsia-i-oriientyry` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, engagement, pedagogy, ua-gec |
| M36 | `register-formal-informal` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M37 | `register-business-ukrainian` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, engagement, pedagogy, ua-gec |
| M38 | `register-formal-written` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M39 | `tradytsii-i-zvychai` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M40 | `register-literary-ukrainian` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M41 | `register-public-discourse` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M42 | `checkpoint-register-domain` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M43 | `register-practice-cross-register-rewriting` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M44 | `politics-government-vocabulary` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M45 | `law-justice-vocabulary` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M46 | `economics-business-vocabulary` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M47 | `genitive-advanced` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, engagement, pedagogy, ua-gec |
| M48 | `dative-advanced` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, engagement, pedagogy, ua-gec |
| M49 | `instrumental-advanced` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M50 | `questions-deliberative-rhetorical` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, missing-summary, richness, word-count, engagement, pedagogy, ua-gec |
| M51 | `advanced-case-semantics` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, missing-summary, richness, word-count, engagement, pedagogy, ua-gec |
| M52 | `pronoun-system-advanced` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, missing-summary, richness, word-count, engagement, pedagogy |
| M53 | `checkpoint-cases-morphology` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, missing-summary, checkpoint-format, richness, word-count, engagement, pedagogy, ua-gec |
| M54 | `aspect-nuances-secondary-imperfectivization` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M55 | `aspect-nuances-imperative-infinitive` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M56 | `pluperfect-tense` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M57 | `conditional-mood-particles` | plan,module,activities,vocab,wiki,site present | missing | FAIL | pedagogy, ua-gec |
| M58 | `numeral-declension-time-dates` | plan,module,activities,vocab,wiki,site present | missing | FAIL | pedagogy, ua-gec |
| M59 | `numeral-declension-compound-numbers` | plan,module,activities,vocab,wiki,site present | missing | FAIL | pedagogy, ua-gec |
| M60 | `word-formation-person-suffixes` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, engagement, pedagogy, ua-gec |
| M61 | `word-formation-abstract-nouns` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, engagement, pedagogy, ua-gec |
| M62 | `word-formation-place-object-names` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, engagement, pedagogy, ua-gec |
| M63 | `word-formation-adjective-adverbs` | plan,module,activities,vocab,wiki,site present | missing | FAIL | pedagogy |
| M64 | `advanced-conjunctions-i` | plan,module,activities,vocab,wiki,site present | missing | FAIL | pedagogy |
| M65 | `advanced-conjunctions-ii` | plan,module,activities,vocab,wiki,site present | missing | FAIL | pedagogy |
| M66 | `checkpoint-morphology` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, missing-summary, checkpoint-format, richness, word-count, engagement, pedagogy, ua-gec |
| M67 | `synonymy-types-and-rows` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, missing-summary, richness, word-count, engagement, pedagogy, ua-gec |
| M68 | `synonymy-in-registers` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M69 | `synonymy-practice-precision` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M70 | `proverbs-work-wisdom-character` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M71 | `proverbs-nature-time-caution` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M72 | `set-expressions-combined` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec, missing-advanced-activity |
| M73 | `checkpoint-lexicology-i` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, checkpoint-format, richness, engagement, pedagogy, ua-gec |
| M74 | `idioms-somatic` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M75 | `idioms-animals` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M76 | `idioms-nature` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M77 | `neologisms-borrowings` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, word-count, engagement, pedagogy, ua-gec |
| M78 | `checkpoint-lexicology-ii` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, checkpoint-format, richness, engagement, pedagogy, ua-gec |
| M79 | `professional-email-basics` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, engagement, pedagogy, ua-gec |
| M80 | `professional-email-advanced` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, engagement, pedagogy, ua-gec |
| M81 | `professional-reports` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, engagement, pedagogy, ua-gec |
| M82 | `academic-writing` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, engagement, pedagogy, ua-gec |
| M83 | `text-analysis` | plan,module,activities,vocab,wiki,site present | missing | PASS | none |
| M84 | `news-analysis` | plan,module,activities,vocab,wiki,site present | missing | PASS | none |
| M85 | `presentation-skills` | plan,module,activities,vocab,wiki,site present | missing | PASS | none |
| M86 | `discussion-debate` | plan,module,activities,vocab,wiki,site present | missing | PASS | none |
| M87 | `checkpoint-communication` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, checkpoint-format, richness, word-count, engagement, pedagogy, ua-gec |
| M88 | `tekhnolohii-ta-shi` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, missing-summary, richness, engagement, pedagogy, ua-gec |
| M89 | `nauka-i-doslidzhennia` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, engagement, pedagogy, ua-gec |
| M90 | `mystetstvo-i-literatura` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, missing-summary, richness, engagement, pedagogy, ua-gec |
| M91 | `modern-diaspora` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, missing-summary, richness, engagement, pedagogy, ua-gec |
| M92 | `religion-in-ukraine` | plan,module,activities,vocab,wiki,site present | missing | FAIL | outline, richness, engagement, pedagogy, ua-gec |
| M93 | `b2-final-exam` | plan,module,activities,vocab,wiki,site present | missing | PASS | none |

## Remediation Batches

R1: LLM-QG persistence sweep for M01-M93. Recreate or restore current LLM-QG
records, confirm current DB/file status, and keep telemetry DB out of the diff.

R2: Audit-contract triage. Resolve V6 heading, summary, outline, checkpoint,
richness, and activity-parser expectations before broad content edits. This
batch should decide what is a validator mismatch versus a real module defect.

R3: Passive and syntax remediation, M01-M31. Fix surface English in M01, M23,
and M31; expand M04-M06 and M25-M30 as noted; then rerun deterministic audits
for M01-M31.

R4: Register/domain/professional remediation, M32-M62 and M79-M82. Resolve M43
resource grounding, fix surface English in M80-M81, and address true
richness/engagement gaps after R2.

R5: Lexicology/checkpoint/final-phase remediation, M66-M78 and M87-M92. Normalize
checkpoint format, address lexicology richness gaps, and rerun no-fix audits.

R6: Final all-B2 verification. Rerun level quality summary, all 93 no-fix module
audits, LLM-QG status checks, and diff gates. Do not include generated status,
audit, review, or telemetry artifacts.

## Helper Usage

swarm_used: true
swarm_label: helper-swarm
swarm_note: three read-only explorer helpers inspected M01-M31, M32-M62, and
M63-M93 for subjective plan/source/wiki/site consistency and B2 quality. Helpers
did not edit files, use GitHub, or make final severity decisions.

## Independent Review

Reviewer identity: pending draft PR review
Review model: pending
Review scope: blocker-only review of the docs-only report PR/diff, audited
scope, validation summary, artifact-clean statement, and helper usage
Final disposition: pending
Unresolved review findings: pending
