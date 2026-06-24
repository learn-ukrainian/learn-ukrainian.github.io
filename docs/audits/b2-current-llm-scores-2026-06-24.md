# B2 Current LLM Scores

Date: 2026-06-24
Auditor: codex/gpt-5
Branch: `codex/b2-current-llm-scores`
Scope: B2 M01 `passive-voice-system`, B2 M02 `past-passive-participles`
Review basis: content-review skill, Tier 2 Core rubric, current built module source, current activities/vocabulary, current plan YAML, and deterministic audit rerun with review validation skipped.

This is a durable score note under `docs/audits/`. It intentionally does not persist generated files under `curriculum/l2-uk-en/**/status/`, `curriculum/l2-uk-en/**/audit/`, or `curriculum/l2-uk-en/**/review/`.

## Summary

| Module | Current LLM Score | Verdict | Ready for Human Review? | Notes |
| --- | ---: | --- | --- | --- |
| B2 M01 `passive-voice-system` | 10/10 | A | Yes | Excellent B2 teaching arc, strong register control, no content blockers. Optional section-balance polish only. |
| B2 M02 `past-passive-participles` | 9/10 | B | Yes | Strong teaching arc and practice coverage. Minor non-blocking polish remains around exact activity affordance/notation consistency. |

## Deterministic Audit Evidence

| Module | Audit Result | Words | Activities | Vocabulary | Immersion | Richness |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| B2 M01 `passive-voice-system` | PASS | 4599/4000 | 11 workbook / 0 inline | 37/25 | 99.8% | 99% |
| B2 M02 `past-passive-participles` | PASS | 4623/4000 | 11 workbook / 0 inline | 40/25 | 99.9% | 99% |

Validation commands rerun on the current checkout:

```bash
/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python scripts/audit_module.py --skip-review curriculum/l2-uk-en/b2/passive-voice-system/module.md
/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python scripts/audit_module.py --skip-review curriculum/l2-uk-en/b2/past-passive-participles/module.md
```

Both commands completed successfully. The local generated audit/status/cache outputs were removed before staging.

## Scoring Method

B2 uses the Tier 2 Core rubric. The LLM score here is the content-review `Lesson Quality Score`, grounded in the Tier 2 "Did I Learn?" test:

| Pass Count | Score |
| ---: | ---: |
| 5/5 | 10/10 |
| 4/5 | 9/10 |
| 3/5 | 8/10 |
| 2/5 | 7/10 |
| 0-1/5 | 6/10 or lower |

The grade follows the content-review grading scale:

| Grade | Meaning |
| --- | --- |
| A | Excellent, ready for deployment/review with no required fixes. |
| B | Good, ready for review with optional polish. |
| C | Adequate, requires fixes before deployment. |
| F | Fails, has critical issues or score <= 5. |

## B2 M01: `passive-voice-system`

**Lesson Quality Score:** 10/10
**Verdict:** A
**Human-review readiness:** ready

### Tier 2 "Did I Learn?" Test

| Question | Result | Evidence |
| --- | --- | --- |
| Did I learn something new? | PASS | The module gives a usable B2 decision model: active when the actor matters, `-но/-то` for result, participle for object state, cautious `-ся` for process. |
| Is the explanation clear without re-reading? | PASS | The recurring "three questions of the editor" frame makes the grammar operational rather than abstract. |
| Could I apply it in conversation or writing? | PASS | Examples cover official letters, reports, news, research prose, public responsibility, and document editing. |
| Am I appropriately challenged? | PASS | The module asks learners to edit register and responsibility, not merely identify passive morphology. |
| Did the teacher voice guide me? | PASS | Mini-dialogues, editor tests, warnings, and register notes guide the learner through real choices. |

### Issues

| Severity | Issue | Score Impact |
| --- | --- | --- |
| LOW | Section word balance remains uneven: the synthesis section is over target while two early sections and the summary are under local outline targets. Total words pass. | No score reduction. Optional polish only. |

M01 has no current critical, high, or medium content-review blocker for preview/human review.

## B2 M02: `past-passive-participles`

**Lesson Quality Score:** 9/10
**Verdict:** B
**Human-review readiness:** ready, with non-blocking polish recommended

### Tier 2 "Did I Learn?" Test

| Question | Result | Evidence |
| --- | --- | --- |
| Did I learn something new? | PASS | The module teaches suffix groups, transitivity, aspect/result meaning, agreement, and register-sensitive use. |
| Is the explanation clear without re-reading? | PARTIAL | The teaching arc is clear overall, but a few formation notes still read as notation polish rather than clean learner-facing pairs. |
| Could I apply it in conversation or writing? | PASS | Practice covers official, journalistic, scientific, literary, and editing contexts. |
| Am I appropriately challenged? | PASS | Learners must distinguish participles from `-но/-то`, reject non-standard forms, and edit dense sentences. |
| Did the teacher voice guide me? | PASS | The lesson uses diagnostics, mini-dialogues, warnings, checklists, and real register choices. |

### Issues

| Severity | Issue | Score Impact |
| --- | --- | --- |
| MEDIUM | Planned `highlight-morphemes` intent is covered by suffix-identification `fill-in`, but there is no literal `highlight-morphemes` activity. | Reduces verdict from A to B, but does not block preview review. |
| LOW | Formation notation can be normalized further in a future polish pass. | Included in 9/10 score. |
| LOW | Deterministic UA-GEC emitted generic low-severity calque suggestions while the module still passed; manual review did not promote them to blockers. | No additional reduction. |

M02 has no current critical or high content-review blocker for preview/human review.

## Independent Review Gate

Reviewer: Claude via agent bridge
Review model: `claude-opus-4-8`
Review scope: read-only blocker review of PR #3794 scoring note and artifact hygiene
Swarm used before independent review: false
Initial findings: 1 blocker
Disposition: fixed before merge by correcting the M01 deterministic word count from `4727/4000` to `4599/4000`
Unresolved findings: 0

## Current Decision

Both modules are ready for human review in the B2 preview phase.

M01 is scored as A / 10 because it passes all five Tier 2 teaching checks and has only optional balance polish. M02 is scored as B / 9 because its teaching arc is strong, but one rubric check is partial due to non-blocking activity-affordance and notation polish.
