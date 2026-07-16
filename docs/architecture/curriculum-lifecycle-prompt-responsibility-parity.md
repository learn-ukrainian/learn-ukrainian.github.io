# Curriculum lifecycle prompt responsibility parity

**Status**: Proposed migration inventory
**Date**: 2026-07-14
**Related**: ADR-012, [#5152](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5152), [#5153](https://github.com/learn-ukrainian/learn-ukrainian.github.io/issues/5153)

## Purpose

This inventory prevents policy loss while replacing large operator prompts with
the code-driven curriculum lifecycle defined by ADR-012. It covers every file
under `docs/prompts/orchestrators`: **39 files and 5,173 lines** at the inventory
commit.

No file is deprecated merely because its execution mechanics are duplicated.
Deprecation requires repository-backed parity for every responsibility below.
`RETAIN-EVAL` means freeze the current prompt as a comparison oracle until the
replacement's fixtures pass; it does not make the prompt completion authority.

## Classification rules

| Class | Target owner |
| --- | --- |
| `CODE` | Deterministic coordinator, module engine, adapter, validator, or integration implementation |
| `CONFIG` | Strict schema-validated profile, command, threshold, cohort, or evidence requirement |
| `PROMPT` | Versioned semantic instructions consumed by a model through the deterministic resolver |
| `POLICY` | Binding human-reviewed curriculum, source, safety, rights, or repository rule |
| `REFERENCE` | Non-executable generated/history/operator documentation |
| `RETAIN-EVAL` | Frozen comparison oracle until golden/canary responsibility parity passes |
| `DEPRECATE` | Remove as an operator entry point only after its target owners and tests are live |

## Shared responsibility map

The repeated mechanics are assigned once:

| Responsibility found in legacy prompts | Canonical owner |
| --- | --- |
| Manifest scope, order, cohorts, prerequisites, ranges, waves | `CODE` coordinator plus bounded `CONFIG` |
| Issue, worktree, branch, commit, PR, CI, merge, cleanup | `CODE` integration adapter plus binding repository `POLICY` |
| Allowed/forbidden writes and generated-artifact hygiene | Binding `POLICY` plus track bundle `CONFIG` |
| Source/dossier/wiki/readings/rights readiness | PREPARE adapter `CODE`, profile `CONFIG`, source/rights `POLICY` |
| Plan review and approval-bound repair | PLAN adapter `CODE`, family prompt, plan-version `POLICY` |
| Build, patch-vs-rebuild, MDX generation | BUILD/repair adapter `CODE`, profile `CONFIG`, semantic `PROMPT` |
| Deterministic validation command menus | Adapter `CODE` and typed validation `CONFIG` |
| Track language, pedagogy, framing, source, and register | Track/family `POLICY` plus phase `PROMPT` |
| Activity, vocabulary, reading, and rendered-tab contracts | Schema/validator `CODE`, bundle `CONFIG`, learner `POLICY` |
| Semantic and deterministic review output | Versioned JSON schema, finding model, and evidence ledger |
| Durable report paths and remediation batches | Runtime ledger/status `CODE`; compact `REFERENCE` output |
| Model/helper routing, ownership, and output budgets | Fleet `CONFIG` and coordinator `CODE` |
| Telemetry and final response | Integration/telemetry adapter `CODE` and schema `CONFIG` |
| Schema-bound, evidence-backed in-result diagnostic scores and reporting-only minimum | `ACCEPT`: v4 evidence fields; categorical semantic and deterministic gates remain authoritative |
| Numeric score authority, numeric readiness thresholds, score sidecars, score-based disposition, warning demotion, parser salvage, merged retries, DB/mtime readiness, same-route median independence | `REJECT`: no lifecycle authority or retry-selection role |

## File-by-file parity

Paths below are relative to `docs/prompts/orchestrators/`.

### CORE

| File | Durable responsibility | Target / disposition |
| --- | --- | --- |
| `a1/quality-audit-orchestrator.md` | Emotional safety; sound-to-word-to-chunk scaffolding; Cyrillic decodability; pronunciation/stress; intentional A1 English support | `PROMPT`/`POLICY`; `RETAIN-EVAL` until A1 audit canaries pass, then `DEPRECATE` wrapper |
| `a1/remediation-build-orchestrator.md` | Preserve warm beginner language, decodability, controlled grammar, current stress policy, and patch-vs-rebuild distinction | Repair `CODE` plus A1 `CONFIG`/`PROMPT`; `DEPRECATE` wrapper |
| `a2/quality-audit-orchestrator.md` | Phase-sensitive immersion ramp, all-case/aspect progression, B1 readiness, and avoidance of A1 regression or premature B1 prose | `PROMPT`/`POLICY`; `RETAIN-EVAL`, then `DEPRECATE` wrapper |
| `a2/remediation-build-orchestrator.md` | Preserve early/late A2 transition and controlled Ukrainian metalanguage | Repair `CODE` plus A2 `CONFIG`/`PROMPT`; `DEPRECATE` wrapper |
| `b1/finale-build-orchestrator.md` | Lock M1-M92, synthesize existing skills in M93-M94, introduce no new grammar, and enforce prerequisite/cohort boundary | Cohort `CONFIG` plus finale `PROMPT`; `DEPRECATE` wrapper |
| `b1/quality-audit-orchestrator.md` | M1-M82 normalization against M83-M94 bar, inventory unbuilt finale modules, and inspect the M82 discontinuity | Audit `PROMPT`/`CONFIG`; `RETAIN-EVAL`, then `DEPRECATE` wrapper |
| `b1/remediation-build-orchestrator.md` | Keep normalization separate from finale, preserve Ukrainian-only body, and classify targeted patch versus rebuild | Repair `CODE` plus B1 `CONFIG`; `DEPRECATE` wrapper |
| `b2/preflight-readiness-audit-orchestrator.md` | Manifest/plan/discovery/wiki/source coverage, stale/orphan detection, prerequisite sequence, and pass/conditional/do-not-build result | PREPARE `CODE`/`CONFIG`; `RETAIN-EVAL`, then `DEPRECATE` wrapper |
| `b2/production-build-orchestrator.md` | Production freeze/archive boundary, golden pilot, examples-first lessons, V2 activities, inline practice and concept-span floors | Build `POLICY`/`PROMPT` plus numeric `CONFIG`; `DEPRECATE` wrapper |
| `b2/quality-audit-orchestrator.md` | Abstraction, natural complex syntax, register, argumentation, and professional/academic readiness | `PROMPT`/`POLICY`; `RETAIN-EVAL`, then `DEPRECATE` wrapper |
| `c1/suite-orchestrator.md` | Study-in-Ukrainian shift, academic argument/source handling/register, C1 immersion, and avoidance of accidental FOLK duplication | C1 `PROMPT`/`CONFIG`; split lifecycle mechanics into `CODE`, then `DEPRECATE` suite |
| `c2/suite-orchestrator.md` | Native-level creation, transformation, teaching, translation, capstone work, expert terminology, and authentic-source fidelity | C2 `PROMPT`/`CONFIG`; split lifecycle mechanics into `CODE`, then `DEPRECATE` suite |

### Seminar

| File | Durable responsibility | Target / disposition |
| --- | --- | --- |
| `bio/suite-orchestrator.md` | Readiness ladder; dossier/plan/wiki dependencies; source tiers; portrait rights; naming; watchlists/holds; HIST alignment; human biography narrative; politically sensitive framing | Split to PREPARE/coordinator `CODE`, BIO `CONFIG`/`POLICY`/`PROMPT`; `RETAIN-EVAL`; do not port legacy QG closure authority |
| `folk/preflight-readiness-audit-orchestrator.md` | FOLK framing, school-canon test, corpus-bound primary-text target, rights, hosted-reading, and quote provenance | PREPARE `CONFIG`/`POLICY`; `RETAIN-EVAL`, then `DEPRECATE` wrapper |
| `folk/production-build-orchestrator.md` | Christian-heritage-first framing, primary readings, myth/high-culture components, hosted/link/excerpt decisions, seminar assembly | FOLK build `PROMPT`/`POLICY`/`CONFIG`; `DEPRECATE` wrapper |
| `folk/quality-audit-orchestrator.md` | Rendered learner-page review; framing, reading, quotation, link, Lesson, and Workbook blockers | PBR FOLK `PROMPT`/`POLICY`; `RETAIN-EVAL`, then `DEPRECATE` wrapper |
| `folk/remediation-build-orchestrator.md` | Repair order from framing through readings/rights to activities/style; preserve verified archaic/dialectal quotations | Repair `CODE` plus FOLK repair `PROMPT`; `DEPRECATE` wrapper |
| `hist/suite-orchestrator.md` | Primary historical documents; evidence versus synthesis/historiography/memory; sourced regional perspectives; non-neutral imperial violence | HIST `PROMPT`/`POLICY`; lifecycle mechanics to `CODE`, then `DEPRECATE` suite |
| `istorio/suite-orchestrator.md` | Competing interpretations and source bases; primary evidence versus historiography/memory artifacts; reject neutral imperial/Soviet authority | ISTORIO `PROMPT`/`POLICY`; `DEPRECATE` suite |
| `lit/suite-orchestrator.md` | Primary literary text at center; Ukrainian periodization; BIO cross-reference checks; close reading versus history/reception/memory | LIT `PROMPT`/`POLICY`; `DEPRECATE` suite |
| `lit-drama/suite-orchestrator.md` | Dialogue, staging, conflict, theatre history, performance-source verification, and play/recording/image rights | LIT-drama `PROMPT`/`POLICY`; `DEPRECATE` suite |
| `lit-essay/suite-orchestrator.md` | Argument, register, voice, evidence, public context, author stance versus reception, and non-generic essay pedagogy | LIT-essay `PROMPT`; `DEPRECATE` suite |
| `lit-fantastika/suite-orchestrator.md` | Genre devices, worldbuilding, allegory, colonial framing, Ukrainian genre history, and rejection of neutral Russian/Soviet taxonomy | LIT-fantastika `PROMPT`/`POLICY`; `DEPRECATE` suite |
| `lit-hist-fic/suite-orchestrator.md` | Separate fiction, historical evidence, memory politics, and authorial interpretation; decolonized periodization | LIT-hist-fic `PROMPT`/`POLICY`; `DEPRECATE` suite |
| `lit-humor/suite-orchestrator.md` | Comic mechanism, register shift, irony, parody target, cultural context, and sensitivity | LIT-humor `PROMPT`/`POLICY`; `DEPRECATE` suite |
| `lit-war/suite-orchestrator.md` | Ukrainian agency/testimony/mourning, trauma-aware pedagogy, rejection of both-sides framing and Russian source laundering, current-event sensitivity | LIT-war `PROMPT`/`POLICY`; `DEPRECATE` suite |
| `lit-youth/suite-orchestrator.md` | Audience and age-coded register without patronizing adults, ethical conflict, classroom safety, and non-simplistic youth literature | LIT-youth `PROMPT`/`POLICY`; `DEPRECATE` suite |
| `oes/suite-orchestrator.md` | Historical phonology, orthography, paleography, register layers, no Old-Russian flattening, and no silent source modernization | OES `PROMPT`/`POLICY`; `DEPRECATE` suite |
| `ruth/suite-orchestrator.md` | Ruthenian/Prosta Mova/Church Slavonic/Polish/Latin layers, diglossia, chancery formulae, and explicit source/transliteration/modernization labels | RUTH `PROMPT`/`POLICY`; `DEPRECATE` suite |

### Shared

| File | Durable responsibility | Target / disposition |
| --- | --- | --- |
| `README.md` | Historical suite index, creation order, lint expectations, and migration navigation | `REFERENCE`, preferably generated from prompt/profile manifests |
| `shared/deterministic-track-audit-orchestrator.md` | Stable structural finding schema, skipped-check accounting, read-only default, and explicit old-LLM-QG exclusion | Existing audit `CODE`/typed `CONFIG`; `DEPRECATE` prose invocation |
| `shared/reading-catalog-template.md` | Candidate schema, hosting decisions, text/quote identity, rights, and verification states | JSON/YAML schema `CONFIG` plus generated `REFERENCE` |
| `shared/reading-section-rules.md` | Corpus survey, primary text versus scholarship, hosted/link/excerpt rules, FOLK floor, and `PrimaryReading` wiring | Reading/rights `POLICY` plus PREPARE/integration `CONFIG` |
| `shared/repo-rules.md` | Repeated protected-file, interpreter, worktree, artifact, scope, commit, and PR rules | Binding repository `POLICY`; `DEPRECATE` duplicate prompt copy |
| `shared/review-output-schema.md` | Complete non-truncated issue schema, coverage matrices, repair categories, and final auditor result | Versioned JSON schema and ledger `CONFIG`; `DEPRECATE` Markdown as authority |
| `shared/seminar-source-rules.md` | Active taxonomy, source universe, quotation integrity, learner register, decolonization, historical-language terminology | Family/track `POLICY` plus semantic `PROMPT`; manifest supplies active tracks |
| `shared/seminar-track-checklists.md` | Per-track source-family and high-risk matrix for HIST/BIO/LIT/ISTORIO/OES/RUTH | Strict track `CONFIG` with versioned policy references |
| `shared/telemetry-and-pr.md` | Telemetry payload, participant token provenance, commit trailer, PR body, and independent review | Integration/telemetry `CODE` plus schema and binding `POLICY`; `DEPRECATE` duplicate prompt copy |
| `shared/validation-checklist.md` | Protected-file/artifact guard, module/track validation profiles, prompt structural checks, and commit validation | Validator/adapters `CODE` plus typed validation `CONFIG`; generated operator `REFERENCE` only |

All 39 source files appear exactly once in the tables above.

## Required states outside the phase labels

`PREPARE -> PLAN -> BUILD -> CERTIFY` is the semantic center, not the complete
operational state model. Parity requires the following surrounding capabilities:

1. **COORDINATE**: manifest queue/DAG, cohorts, waves, quota/headroom, leases,
   independent-review capacity, serial merge order, and cross-module prerequisites.
2. **HOLD / APPROVE**: production freezes, pilot acceptance, canonicity/watchlist
   holds, rights uncertainty, and plan/editorial decisions requiring authority.
3. **INTEGRATE**: generated learner surfaces, rendered routes/tabs, telemetry,
   focused PR, CI, review gate, merge, and cleanup. Integration is not certification.
4. **EVALUATE**: read-only whole-track audits, coverage matrices, durable findings,
   and repair batching independent of one module release.
5. **COHORT**: B1 finale locks, normalization boundaries, checkpoint prerequisites,
   and track readiness constraints above isolated module state.
6. **MATERIALIZE_READINGS**: rights classification belongs to PREPARE, while
   hosted-reading creation is an explicit build/integration side effect.
7. **CERTIFY_RENDERED_PRODUCT**: review learner-visible MDX and Lesson/Workbook
   behavior, not only source bundles.
8. **AUDIT_TOOLING_REQUIRED / REVIEWER_INSTABILITY**: stop content mutation when
   a tool or unchanged-source reviewer result is defective or unstable.
9. **CERTIFICATION_CURRENCY**: track provisional PBR, optional production QG,
   complete dependency hashes, gate/prompt versions, and invalidation separately.

## Migration gate

The central parity conclusion is that most of the 5,173 lines are duplicated
execution mechanics. The durable semantic residue is a bounded set of track
policies, strict configuration, schemas, and phase-specific semantic prompts.

Before any legacy operator entry point is deprecated, its issue must prove:

- every row above has a live canonical owner;
- the owner is versioned, hashed, and tested;
- CORE and seminar golden fixtures preserve required catches and false-positive
  protections;
- the short lifecycle invocation reproduces the intended state and evidence;
- the old file either becomes generated/reference-only, remains a frozen eval
  oracle, or is removed with an explicit replacement pointer.

P1-P6 implementation ownership is tracked in issues `#5155`, `#5154`, `#5158`,
`#5156`, `#5157`, and `#5159` respectively. No runtime implementation begins
before the P0 ADR and this inventory merge.
