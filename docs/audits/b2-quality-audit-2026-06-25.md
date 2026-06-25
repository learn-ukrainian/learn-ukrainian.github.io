# B2 M04/M08/M09 Quality Audit Report

Date: 2026-06-25
Auditor: codex/gpt-5
Branch: `codex/b2-m04-m08-m09-audit-scores`
Scope: B2 M04 `dim-zhytlo`, B2 M08 `pobut-shchodenne`, B2 M09 `active-participles-present`
Read-only audit phase: true
Durable report path: `docs/audits/b2-quality-audit-2026-06-25.md`

## Correction Note

The production PRs for M04, M08, and M09 were merged after deterministic module audits, GitHub CI, telemetry persistence, and Claude Opus 4.8 read-only blocker review. The separate B2 quality-audit prompt was not run before merge. This report runs that audit phase after merge and records the LLM quality scores for the newly built modules.

## Source Files Inspected

- `docs/prompts/orchestrators/b2/quality-audit-orchestrator.md`
- `docs/prompts/orchestrators/shared/repo-rules.md`
- `docs/prompts/orchestrators/shared/validation-checklist.md`
- `docs/prompts/orchestrators/shared/review-output-schema.md`
- `docs/prompts/orchestrators/shared/telemetry-and-pr.md`
- `docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`
- `scripts/config.py`
- `scripts/audit/config.py`
- `curriculum/l2-uk-en/curriculum.yaml`
- `curriculum/l2-uk-en/plans/b2/dim-zhytlo.yaml`
- `curriculum/l2-uk-en/plans/b2/pobut-shchodenne.yaml`
- `curriculum/l2-uk-en/plans/b2/active-participles-present.yaml`
- `curriculum/l2-uk-en/b2/dim-zhytlo/module.md`
- `curriculum/l2-uk-en/b2/dim-zhytlo/activities.yaml`
- `curriculum/l2-uk-en/b2/dim-zhytlo/vocabulary.yaml`
- `curriculum/l2-uk-en/b2/pobut-shchodenne/module.md`
- `curriculum/l2-uk-en/b2/pobut-shchodenne/activities.yaml`
- `curriculum/l2-uk-en/b2/pobut-shchodenne/vocabulary.yaml`
- `curriculum/l2-uk-en/b2/active-participles-present/module.md`
- `curriculum/l2-uk-en/b2/active-participles-present/activities.yaml`
- `curriculum/l2-uk-en/b2/active-participles-present/vocabulary.yaml`

## Executive Summary

| Module | LLM Score | Verdict | Human Review Readiness | Blockers | Notes |
| --- | ---: | --- | --- | ---: | --- |
| B2 M04 `dim-zhytlo` | 9/10 | B+ | Ready | 0 | Strong housing/repair/rental module. Minor polish remains around section balance and one deterministic UA-GEC false-positive family (`тим`). |
| B2 M08 `pobut-shchodenne` | 10/10 | A | Ready | 0 | Excellent everyday-life module with strong activity coverage, real-world Ukrainian domestic context, and no meaningful content blockers. |
| B2 M09 `active-participles-present` | 9/10 | B+ | Ready | 0 | Strong grammar/editorial module. Score held at 9 because section balance remains uneven and deterministic audit still emits false-positive naturalness warnings despite clean source review. |

All three modules are suitable for B2 preview-phase human review. No release-blocking issue was found in this audit pass.

## Deterministic Audit Evidence

| Module | Audit Result | Words | Activities | Vocabulary | Immersion | Richness | Residual Audit Notes |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| B2 M04 `dim-zhytlo` | PASS | 4882/4000 | 10 workbook / 0 inline | 94/25 | 100.0% | 96% | One minor UA-GEC `тим` suggestion; manual review treats it as non-blocking. |
| B2 M08 `pobut-shchodenne` | PASS | 4263/4000 | 12 workbook / 0 inline | 55/25 | 99.9% | 99% | No deterministic pedagogical blocker. |
| B2 M09 `active-participles-present` | PASS | 4808/4000 | 10 workbook / 0 inline | 40/25 | 100.0% | 99% | Deterministic Russicism/UA-GEC warnings are false positives in context: `оточуюч*` appears only as explicitly flagged calque examples that the module corrects, never as endorsed usage. |

## LLM Quality Scoring Method

B2 modules use the Tier 2 Core rubric and the content-review "Did I Learn?" test:

| Pass Count | Score |
| ---: | ---: |
| 5/5 with no meaningful content polish | 10/10 |
| 5/5 with non-blocking polish or unevenness | 9/10 |
| 4/5 | 8/10 |
| 3/5 | 7/10 |
| 0-2/5 | 6/10 or lower |

The five checks are:

1. Did I learn something new?
2. Is the explanation clear without re-reading?
3. Could I apply it in conversation or writing?
4. Am I appropriately challenged?
5. Did the teacher voice guide me?

## B2 M04: `dim-zhytlo`

**Lesson Quality Score:** 9/10
**Verdict:** B+
**Human-review readiness:** ready

### Tier 2 "Did I Learn?" Test

| Question | Result | Evidence |
| --- | --- | --- |
| Did I learn something new? | PASS | Learner gets a B2-level housing/rental/repair communication model, including contracts, utility issues, neighbor communication, and result-focused `-но/-то` forms. |
| Is the explanation clear without re-reading? | PASS | Tables, examples, dialogues, and checklists make the housing scenarios operational rather than abstract. |
| Could I apply it in conversation or writing? | PASS | Learner can write rental messages, utility reports, house-chat notices, and negotiation language. |
| Am I appropriately challenged? | PASS | Module asks for register control, evidence-based requests, and repair/rental negotiation rather than only vocabulary recall. |
| Did the teacher voice guide me? | PASS | Dialogues, warnings, notes, and a final checklist provide a visible tutor path. |

### Issues

| Severity | Issue | Score Impact |
| --- | --- | --- |
| LOW | Section balance remains uneven: total word count passes but some sections are over-expanded while summary/utility sections are shorter than plan targets. | Holds score at 9/10. |
| LOW | Deterministic audit emits one `тим` UA-GEC suggestion; manual review did not confirm it as a real linguistic issue. | No blocker. |

## B2 M08: `pobut-shchodenne`

**Lesson Quality Score:** 10/10
**Verdict:** A
**Human-review readiness:** ready

### Tier 2 "Did I Learn?" Test

| Question | Result | Evidence |
| --- | --- | --- |
| Did I learn something new? | PASS | Learner gets B2-level everyday-life language for chores, routines, domestic negotiations, outages, shared responsibility, and cultural expectations. |
| Is the explanation clear without re-reading? | PASS | The module repeatedly connects sentence focus, imperative forms, `-но/-то` results, and pragmatic household negotiation. |
| Could I apply it in conversation or writing? | PASS | Practice supports housemate messages, chore distribution, problem reporting, and reflective writing. |
| Am I appropriately challenged? | PASS | Learners must manage politeness, responsibility, gender-stereotype framing, and Ukrainian-first naturalness. |
| Did the teacher voice guide me? | PASS | Realistic dialogues, warnings, and examples maintain a guided learning arc. |

### Issues

No current critical, high, medium, or low content issue was found. M08 earns 10/10 because it passes all five Tier 2 checks and deterministic audit metrics are strong.

## B2 M09: `active-participles-present`

**Lesson Quality Score:** 9/10
**Verdict:** B+
**Human-review readiness:** ready

### Tier 2 "Did I Learn?" Test

| Question | Result | Evidence |
| --- | --- | --- |
| Did I learn something new? | PASS | Learner gets the core B2 insight: active present participles are mainly recognition/editorial replacement targets, not productive forms. |
| Is the explanation clear without re-reading? | PASS | The module distinguishes lexicalized adjectives from calqued temporary-action forms and gives five replacement strategies. |
| Could I apply it in conversation or writing? | PASS | Activities require choosing `охочі`, `чинний`, `зворушливий`, `зволожувальний`, subordinate clauses, and role nouns in context. |
| Am I appropriately challenged? | PASS | Learners must decide between suffix recognition, lexicalized exceptions, register, and replacement strategy. |
| Did the teacher voice guide me? | PASS | Dialogues, editorial algorithm, example banks, and self-checks make the topic practical. |

### Issues

| Severity | Issue | Score Impact |
| --- | --- | --- |
| LOW | Section balance remains uneven: the analytical-practice section is very large relative to the plan, while the summary is shorter than the nominal plan target. | Holds score at 9/10. |
| LOW | Deterministic audit still emits Russicism/UA-GEC warnings because `оточуюч*` appears in explicitly flagged calque examples corrected by the module. These examples are pedagogically intentional, not endorsed usage. | No blocker. |

## Validation Results

| Command | Result |
| --- | --- |
| `.venv/bin/python scripts/validate_activities.py l2-uk-en b2 4` | PASS |
| `.venv/bin/python scripts/validate_activities.py l2-uk-en b2 8` | PASS |
| `.venv/bin/python scripts/validate_activities.py l2-uk-en b2 9` | PASS |
| `.venv/bin/python scripts/validate_vocab_yaml.py curriculum/l2-uk-en/b2/dim-zhytlo/vocabulary.yaml` | PASS, 94 items |
| `.venv/bin/python scripts/validate_vocab_yaml.py curriculum/l2-uk-en/b2/pobut-shchodenne/vocabulary.yaml` | PASS, 55 items |
| `.venv/bin/python scripts/validate_vocab_yaml.py curriculum/l2-uk-en/b2/active-participles-present/vocabulary.yaml` | PASS, 40 items |
| `.venv/bin/python scripts/audit_module.py --skip-review curriculum/l2-uk-en/b2/dim-zhytlo/module.md` | PASS |
| `.venv/bin/python scripts/audit_module.py --skip-review curriculum/l2-uk-en/b2/pobut-shchodenne/module.md` | PASS |
| `.venv/bin/python scripts/audit_module.py --skip-review curriculum/l2-uk-en/b2/active-participles-present/module.md` | PASS |

Generated local audit/status/cache outputs were removed after audit commands. No curriculum, wiki, or site source files were modified by this audit PR.

## Recommended Remediation Batches

| Batch | Scope | Recommendation |
| --- | --- | --- |
| `b2-m04-optional-polish` | M04 section balance and minor phrasing | Defer until human review unless reviewers ask for polish. |
| `b2-m09-optional-polish` | M09 section balance and audit false-positive cleanup | Defer until human review unless reviewers ask for polish. |
| `b2-next-wave-builds` | M03, M05, M06, M07, M10 | Start next production wave. Recommended parallelism: M03/M05/M06 first, then M07/M10 once landing conflicts are resolved. |

## Independent Review Evidence

| Module | Reviewer | Model | Scope | Disposition |
| --- | --- | --- | --- | --- |
| M04 `dim-zhytlo` | Claude via agent bridge | `claude-opus-4-8` | PR #3803 read-only blocker review | Mergeable, 0 blockers. One wording nit addressed before merge. |
| M08 `pobut-shchodenne` | Claude via agent bridge | `claude-opus-4-8` | PR #3801 read-only blocker review | Mergeable, 0 blockers. |
| M09 `active-participles-present` | Claude via agent bridge | `claude-opus-4-8` | PR #3805 read-only blocker review | Mergeable, 0 blockers. One morphology-table nit addressed before merge. |

## Final Auditor Response Schema

Report written: `docs/audits/b2-quality-audit-2026-06-25.md`
Scope inspected: B2 M04 `dim-zhytlo`, B2 M08 `pobut-shchodenne`, B2 M09 `active-participles-present`
Blockers: 0
Issues recorded: 4 low/non-blocking issues
Recommended remediation batches: optional M04 polish, optional M09 polish, next-wave builds M03/M05/M06/M07/M10
Validation run: activities, vocabulary, deterministic audit for all scoped modules passed
Curriculum files modified: no
Forbidden artifacts included: no
swarm_used: false
swarm_label: none
swarm_note: solo audit/score persistence; no helper swarm used for this audit PR
