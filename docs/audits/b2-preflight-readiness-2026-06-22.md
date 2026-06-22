# B2 Preflight Readiness Audit

Report version: 0.1
Date: 2026-06-22
Auditor: Codex
Worktree: /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/b2-preflight-readiness
Scope: B2 core production readiness, all 93 planned B2 modules
Read-only: true
Durable report path: docs/audits/b2-preflight-readiness-2026-06-22.md

## Executive Summary

Readiness status: do not build

B2 has complete top-level source coverage: the curriculum manifest lists 93 modules, and the checkout has 93 plan YAML files, 93 discovery YAML files, 93 wiki articles, and 93 wiki source registries. `scripts/validate_plans.py b2` passes with zero errors and zero warnings.

Production is still blocked. The plan source of truth contains at least one direct grammatical contradiction with its locked wiki article, all plans contain English summary text that can be copied into B2 modules despite the live B2 full-immersion policy, and discovery files are source-empty auto-generated stubs even though the B2 production prompt tells builders to read them. These are pre-build source problems, not module-build problems.

Blockers: 3
High issues: 3
Medium issues: 2
Production allowed now: no

## Source Files Inspected

- AGENTS.md
- CLAUDE.md
- GEMINI.md
- docs/prompts/orchestrators/b2/preflight-readiness-audit-orchestrator.md
- docs/prompts/orchestrators/shared/repo-rules.md
- docs/prompts/orchestrators/shared/validation-checklist.md
- docs/prompts/orchestrators/shared/review-output-schema.md
- curriculum/l2-uk-en/curriculum.yaml
- docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md
- docs/l2-uk-en/state-standard-2024-mapping.yaml
- scripts/config.py
- scripts/audit/config.py
- scripts/common/thresholds.py
- all files under curriculum/l2-uk-en/plans/b2/
- all files under curriculum/l2-uk-en/b2/discovery/
- all files under wiki/grammar/b2/

Repo assumptions verified:

- B2 is a core track with 93 modules in `curriculum/l2-uk-en/curriculum.yaml`.
- B2 production is not yet built: there are zero source module directories under `curriculum/l2-uk-en/b2/` other than `discovery/`, and only `site/src/content/docs/b2/index.mdx` exists.
- Live shared config sets `TRACK_CONFIG["b2"]["immersion_range"]` to `[1.0, 1.0]`.
- Live audit thresholds set B2 `target_words` to 4000.
- The local State Standard 2024 mapping places B2 case usage under `§4.1.2`, syntax under `§4.3`, and stylistics under `§4.4`.

## Coverage Matrix

| Check | Result | Notes |
| --- | --- | --- |
| Manifest module count | pass | 93 B2 slugs, first `passive-voice-system`, last `b2-final-exam` |
| Plan coverage | pass | 93 live `*.yaml` plans, no missing or extra live plan slug |
| Sequence alignment | pass | Plan `sequence` and `module` IDs match manifest order |
| Discovery coverage | pass for presence, fail for substance | 93 discovery files, all have empty `rag_chunks` and `rag_literary` |
| Wiki article coverage | pass | 93 `wiki/grammar/b2/<slug>.md` files |
| Wiki source registry coverage | pass | 93 `<slug>.sources.yaml` files; each has at least 3 sources |
| Wiki unresolved markers | pass | No `VERIFY` markers found in B2 wiki articles |
| Plan validation script | pass | 93 plans checked, 0 errors, 0 warnings |
| Stale backup files | fail | Tracked `curriculum/l2-uk-en/plans/b2/advanced-case-semantics.yaml.bak` exists |

## B2 Group Matrix

| Group | Manifest span | Count |
| --- | ---: | ---: |
| B2.0 Passive Voice System | M01-M10 | 10 |
| B2.1 Participles & Sentence Structure | M11-M21 | 11 |
| B2.2 Advanced Syntax & Stylistics | M22-M31 | 10 |
| B2.3 Stylistic Devices & Register | M32-M42 | 11 |
| B2.4 Domain Vocabulary & Advanced Cases | M43-M53 | 11 |
| B2.5 Verb Nuances & Word Formation | M54-M63 | 10 |
| B2.6 Connectors, Synonymy & Phraseology | M64-M73 | 10 |
| B2.7 Idioms, Neologisms & Professional Communication | M74-M84 | 11 |
| B2.8 Communication Skills & Capstone | M85-M93 | 9 |

## Issues

### B2-PREFLIGHT-BLOCKER-001 `reflexive-passive` teaches the opposite of its locked wiki source

Severity: blocker
Track or level: B2
Module: M05 `reflexive-passive`
Files:

- curriculum/l2-uk-en/plans/b2/reflexive-passive.yaml
- wiki/grammar/b2/reflexive-passive.md

Evidence:

- The plan objective says to use the instrumental case for the agent with reflexive verbs.
- The plan outline calls `Книга читається (ким?) учнем` a grammatical norm.
- The plan summary says passive `-ся` places the agent in the instrumental case.
- The plan grammar metadata lists `Instrumental case for the agent`.
- The locked wiki says this exact pattern is a norm violation: passive `-ся` with a personal agent in instrumental must be rewritten as an active construction.

Why it matters:

The plan is the source of truth for production. If a writer follows it, B2 module 5 will teach a Russian-influenced passive pattern that the locked wiki explicitly rejects. This is a linguistic correctness blocker and a decolonization blocker.

Expected fix:

Patch the plan before any build. Replace the objective, outline section, summary, examples, and grammar metadata so the module teaches passive `-ся` only for natural/autonomous or abstract process uses, and treats instrumental personal agents as errors to rewrite actively.

Batch recommendation: single-module preflight remediation.

### B2-PREFLIGHT-BLOCKER-002 All plans contain English summary copy despite B2 full-immersion policy

Severity: blocker
Track or level: B2
Module: all 93 B2 modules
Files:

- curriculum/l2-uk-en/plans/b2/*.yaml
- scripts/config.py
- docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md

Evidence:

- All 93 plans contain a `Підсумок — Summary` section with English `Self-check` prompts.
- Example: `passive-voice-system` includes English summary points under the content outline.
- Example: `pronoun-system-advanced` has English objectives and English content-outline points beyond the summary.
- Live config requires B2 full Ukrainian immersion; English is allowed only in vocabulary translation contexts.

Why it matters:

B2 production prompts consume plans. English summary blocks and English objectives create a direct copy path into generated modules, violating the 100% B2 immersion policy and requiring cleanup after every build.

Expected fix:

Before production, either localize the English summary/objective content in all B2 plans or modify the production prompt and writer checks to explicitly ignore English plan-summary scaffolding and require Ukrainian-only output. The safer fix is plan remediation because the plans are source of truth.

Batch recommendation: mechanical B2 plan remediation batch, followed by a targeted diff review.

### B2-PREFLIGHT-BLOCKER-003 Discovery files are present but source-empty stubs

Severity: blocker
Track or level: B2
Module: all 93 B2 modules
Files:

- curriculum/l2-uk-en/b2/discovery/*.yaml

Evidence:

- Every B2 discovery file has `rag_chunks: []` and `rag_literary: []`.
- Files contain `warning: Auto-generated from plan`.
- Example: `curriculum/l2-uk-en/b2/discovery/passive-voice-system.yaml` contains query keywords but no source chunks.

Why it matters:

The production prompt says builders should build from plans, discovery files, and wiki/source coverage. If discovery remains in that authority chain, it contributes no independent source evidence and can give a false sense of readiness.

Expected fix:

Choose one policy before production: populate discovery with current source packets, or revise the production prompt so discovery files are treated as keyword indexes only and wiki/source registries are the actual source authority.

Batch recommendation: prompt-policy remediation or discovery regeneration batch.

### B2-PREFLIGHT-HIGH-001 Several State Standard citations are stale or mislabeled

Severity: high
Track or level: B2
Module: 11 affected plans
Files:

- curriculum/l2-uk-en/plans/b2/advanced-case-semantics.yaml
- curriculum/l2-uk-en/plans/b2/synonymy-types-and-rows.yaml
- curriculum/l2-uk-en/plans/b2/synonymy-in-registers.yaml
- curriculum/l2-uk-en/plans/b2/synonymy-practice-precision.yaml
- curriculum/l2-uk-en/plans/b2/proverbs-work-wisdom-character.yaml
- curriculum/l2-uk-en/plans/b2/proverbs-nature-time-caution.yaml
- curriculum/l2-uk-en/plans/b2/set-expressions-combined.yaml
- curriculum/l2-uk-en/plans/b2/idioms-somatic.yaml
- curriculum/l2-uk-en/plans/b2/idioms-animals.yaml
- curriculum/l2-uk-en/plans/b2/idioms-nature.yaml
- curriculum/l2-uk-en/plans/b2/neologisms-borrowings.yaml

Evidence:

- `advanced-case-semantics` cites `B2 SS 4.4 — Lexicology and case semantics`.
- The local mapping puts advanced B2 case semantics under `§4.1.2`, while `§4.4` is stylistics.
- Ten lexicology/phraseology plans cite `SS 4.4 — Lexicology...`, but the local mapping describes B2 `§4.4` as stylistic phonetic, lexical, and syntactic devices.

Why it matters:

The preflight prompt requires source-supported State Standard 2024 alignment. Stale section labels make it unclear whether the affected plan is aligned to the State Standard, the wiki source registry, or an older planning taxonomy.

Expected fix:

Replace stale `SS 4.4 — Lexicology...` references with exact local mapping anchors or record them as thematic/wiki-source-backed modules rather than false State Standard section claims.

Batch recommendation: B2 source-reference cleanup batch.

### B2-PREFLIGHT-HIGH-002 Plan metadata is incomplete for production prompting

Severity: high
Track or level: B2
Module: broad B2 pattern
Files:

- curriculum/l2-uk-en/plans/b2/*.yaml

Evidence:

- 93 of 93 plans omit `persona`.
- 76 of 93 plans omit top-level `grammar`.
- 76 of 93 plans omit top-level `register`.
- 21 of 93 plans omit `phase`.
- `validate_plans.py b2` still passes, so the current validator does not enforce the metadata expected by the preflight prompt.

Why it matters:

The production prompt asks writers to preserve plan grammar/register intent. When those fields are absent, writers must infer from title, outline, or wiki, which increases inconsistency and makes plan fidelity harder to audit.

Expected fix:

Either backfill top-level `grammar`, `register`, and `phase` where missing, or update B2 production guidance to derive these fields from wiki/source files and record that derivation in each module-tailored mini-prompt.

Batch recommendation: metadata backfill batch after fixing blockers 001 and 002.

### B2-PREFLIGHT-HIGH-003 A tracked `.bak` plan file exists in the B2 plan directory

Severity: high
Track or level: B2
Module: M51 `advanced-case-semantics`
Files:

- curriculum/l2-uk-en/plans/b2/advanced-case-semantics.yaml.bak

Evidence:

- `git ls-files` shows the `.bak` file is tracked.
- The live plan is also present as `advanced-case-semantics.yaml`.

Why it matters:

Stale plan backups in source directories invite accidental reads by broad globs, manual searches, or future scripts. The preflight prompt explicitly requires stale `.bak` identification.

Expected fix:

Remove or archive the backup file in a scoped remediation PR if project owners confirm it is not intentionally consumed.

Batch recommendation: include in the source-reference cleanup batch.

### B2-PREFLIGHT-MEDIUM-001 Some objectives are not testable can-do objectives

Severity: medium
Track or level: B2
Module: 23 affected plans
Files:

- curriculum/l2-uk-en/plans/b2/*.yaml

Evidence:

- 23 plans contain objective verbs such as `Розуміти`, `Зрозуміти`, or `Ознайомитися`.
- Examples include `passive-voice-system`, `multi-clause-sentences`, `correlative-constructions`, `word-formation-*`, and `religion-in-ukraine`.

Why it matters:

Preflight plan-review criteria prefer testable learner actions. Understanding-oriented objectives are harder to verify in activities and post-build audits.

Expected fix:

Rewrite weak objectives as observable actions such as identify, transform, explain, compare, edit, write, defend, or apply.

Batch recommendation: can-do objective cleanup batch.

### B2-PREFLIGHT-MEDIUM-002 Plan vocabulary schemas are inconsistent

Severity: medium
Track or level: B2
Module: broad B2 pattern
Files:

- curriculum/l2-uk-en/plans/b2/*.yaml

Evidence:

- 68 plans use `vocabulary` and omit `vocabulary_hints`.
- 25 plans use `vocabulary_hints` and omit `vocabulary`.
- Counts are adequate after normalizing both schemas: every plan has at least 11 vocabulary items.

Why it matters:

The content is not missing, but mixed schemas make builder prompts and review scripts more fragile.

Expected fix:

Normalize the plan vocabulary field or document both schemas as first-class accepted B2 plan shapes.

Batch recommendation: schema normalization or validator documentation batch.

## Modules With No Coverage Findings

No module is missing a live plan, discovery file, wiki article, or source registry.

## State Standard Alignment Summary

The local State Standard mapping supports the broad B2 architecture:

- Passive voice, participles, pluperfect, and conditional mood are under B2 verb forms.
- Advanced case meanings are under B2 `§4.1.2`.
- One-member sentences, complex sentences, and direct/indirect speech are under B2 syntax.
- Stylistic phonetic, lexical, and syntactic devices are under B2 `§4.4`.
- Thematic modules map broadly to B2 thematic areas such as home, daily life, health, sport, shopping, services, places, science/technology, media, traditions, culture, and society.

Alignment is not ready for production because plan citations still need cleanup in the lexicology/phraseology and advanced-case areas, and eight early grammar plans lack a direct State Standard reference in the plan itself: `past-passive-participles`, `b2-impersonal-passive`, `reflexive-passive`, `third-person-plural-passive`, `active-participles-present`, `active-participles-past`, `participles-vs-relative-clauses`, and `pronoun-system-advanced`.

## Recommended Remediation Batches

1. Fix M05 `reflexive-passive` before any B2 production.
2. Remove or neutralize English plan-summary copy across all B2 plans before production.
3. Decide the discovery-file policy: populate source chunks or mark discovery as non-authoritative keyword scaffolding in production prompts.
4. Clean stale State Standard references and the tracked `.bak` file.
5. Backfill or formally derive missing `grammar`, `register`, and `phase` metadata.
6. Normalize weak objectives and vocabulary field shape.

## Validation Run Before Report

Commands run:

```bash
.venv/bin/python scripts/validate_plans.py b2
```

Outcome:

```text
93 plans checked
Errors: 0
Warnings: 0
[OK] All plans valid.
```

Additional read-only checks:

- Manifest/plan/discovery/wiki/source matrix generated with local YAML parsing.
- B2 built-source directory check found zero built module directories.
- B2 site check found only `site/src/content/docs/b2/index.mdx`.
- `git ls-files curriculum/l2-uk-en/plans/b2/advanced-case-semantics.yaml.bak` confirms the stale backup is tracked.

## Final Auditor Response Schema

Report written: docs/audits/b2-preflight-readiness-2026-06-22.md
Scope inspected: all 93 B2 planned modules
Readiness status: do not build
Blockers: 3
Issues recorded: 8
Recommended next batch: fix `reflexive-passive`, then remove/neutralize English plan-summary copy
Files changed: docs/audits/b2-preflight-readiness-2026-06-22.md only
Curriculum files modified: no
swarm_used: false
swarm_label: solo
swarm_note: solo run; no swarm used
