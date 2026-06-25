# B2 Current LLM Scores

Date: 2026-06-25
Auditor: codex/gpt-5
Branch: `codex/b2-m04-m08-m09-audit-scores`
Scope: currently active B2 preview modules on `origin/main`: M01, M02, M04, M08, M09.

This durable score note supersedes `docs/audits/b2-current-llm-scores-2026-06-24.md` for current B2 active-module status. It intentionally does not persist generated files under `curriculum/l2-uk-en/**/status/`, `curriculum/l2-uk-en/**/audit/`, or `curriculum/l2-uk-en/**/review/`.

## Summary

| Module | Current LLM Score | Verdict | Ready for Human Review? | Notes |
| --- | ---: | --- | --- | --- |
| B2 M01 `passive-voice-system` | 10/10 | A | Yes | Excellent B2 teaching arc, strong register control, no content blockers. Score carried forward from 2026-06-24 durable score note. |
| B2 M02 `past-passive-participles` | 9/10 | B | Yes | Strong teaching arc and practice coverage. Score carried forward from 2026-06-24 durable score note; optional activity-affordance/notation polish remains. |
| B2 M04 `dim-zhytlo` | 9/10 | B+ | Yes | Strong housing/rental/repair communication module. Minor optional polish around section balance and residual deterministic false-positive naturalness warning. |
| B2 M08 `pobut-shchodenne` | 10/10 | A | Yes | Excellent everyday-life module with strong activity coverage, natural Ukrainian household negotiation, and no meaningful content issue found. |
| B2 M09 `active-participles-present` | 9/10 | B+ | Yes | Strong editorial grammar module. Score held at 9 due section imbalance and residual deterministic false-positive warnings despite clean source inspection. |

## Deterministic Audit Evidence

| Module | Audit Result | Words | Activities | Vocabulary | Immersion | Richness |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| B2 M01 `passive-voice-system` | PASS | 4599/4000 | 11 workbook / 0 inline | 37/25 | 99.8% | 99% |
| B2 M02 `past-passive-participles` | PASS | 4623/4000 | 11 workbook / 0 inline | 40/25 | 99.9% | 99% |
| B2 M04 `dim-zhytlo` | PASS | 4882/4000 | 10 workbook / 0 inline | 94/25 | 100.0% | 96% |
| B2 M08 `pobut-shchodenne` | PASS | 4263/4000 | 12 workbook / 0 inline | 55/25 | 99.9% | 99% |
| B2 M09 `active-participles-present` | PASS | 4808/4000 | 10 workbook / 0 inline | 40/25 | 100.0% | 99% |

## Scoring Method

B2 uses the Tier 2 Core rubric. LLM score here is the content-review `Lesson Quality Score`, grounded in the Tier 2 "Did I Learn?" test:

| Pass Count | Score |
| ---: | ---: |
| 5/5 with no meaningful content polish | 10/10 |
| 5/5 with non-blocking polish or unevenness | 9/10 |
| 4/5 | 8/10 |
| 3/5 | 7/10 |
| 0-2/5 | 6/10 or lower |

## Score Notes For New Modules

### B2 M04: `dim-zhytlo`

**Lesson Quality Score:** 9/10
**Verdict:** B+
**Human-review readiness:** ready

All five Tier 2 checks pass. The score is 9 rather than 10 because the module still has uneven section balance and one residual deterministic UA-GEC false-positive family. No blocker or required fix was found.

### B2 M08: `pobut-shchodenne`

**Lesson Quality Score:** 10/10
**Verdict:** A
**Human-review readiness:** ready

All five Tier 2 checks pass with strong deterministic audit metrics and no meaningful content issue. The module is ready for human review without required polish.

### B2 M09: `active-participles-present`

**Lesson Quality Score:** 9/10
**Verdict:** B+
**Human-review readiness:** ready

All five Tier 2 checks pass. The module is strong and correctly teaches active present participles as recognition/editorial replacement rather than productive morphology. The score is 9 rather than 10 because section balance remains uneven and deterministic audit still emits false-positive warnings after source inspection.

## Validation Commands Run For 2026-06-25 Additions

```bash
.venv/bin/python scripts/validate_activities.py l2-uk-en b2 4
.venv/bin/python scripts/validate_activities.py l2-uk-en b2 8
.venv/bin/python scripts/validate_activities.py l2-uk-en b2 9
.venv/bin/python scripts/validate_vocab_yaml.py curriculum/l2-uk-en/b2/dim-zhytlo/vocabulary.yaml
.venv/bin/python scripts/validate_vocab_yaml.py curriculum/l2-uk-en/b2/pobut-shchodenne/vocabulary.yaml
.venv/bin/python scripts/validate_vocab_yaml.py curriculum/l2-uk-en/b2/active-participles-present/vocabulary.yaml
.venv/bin/python scripts/audit_module.py --skip-review curriculum/l2-uk-en/b2/dim-zhytlo/module.md
.venv/bin/python scripts/audit_module.py --skip-review curriculum/l2-uk-en/b2/pobut-shchodenne/module.md
.venv/bin/python scripts/audit_module.py --skip-review curriculum/l2-uk-en/b2/active-participles-present/module.md
```

All commands completed successfully. Local generated audit/status/cache outputs were removed before staging.

## Review Evidence

| Module | Independent Review | Disposition |
| --- | --- | --- |
| M04 `dim-zhytlo` | Claude Opus 4.8 PR #3803 blocker review | Mergeable, 0 blockers; one wording nit addressed before merge. |
| M08 `pobut-shchodenne` | Claude Opus 4.8 PR #3801 blocker review | Mergeable, 0 blockers. |
| M09 `active-participles-present` | Claude Opus 4.8 PR #3805 blocker review | Mergeable, 0 blockers; one morphology-table nit addressed before merge. |
