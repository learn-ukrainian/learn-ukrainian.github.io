# A2 Plan Review Summary

**Date:** 2026-03-05
**Reviewer:** Claude (plan-review skill)
**Reference:** Issue #729
**Plans reviewed:** 76
**State Standard:** docs/l2-uk-en/state-standard-2024-mapping.yaml (A2 section, lines 749-1432)

## Verdicts

| Verdict | Count |
|---------|-------|
| PASS | 69 |
| NEEDS FIXES | 6 |
| FAIL | 1 |
| **Total** | **76** |

## Issue Summary

| Severity | Count | Pattern |
|----------|-------|---------|
| CRITICAL | 1 | word_target mismatch (a2-final-exam) |
| HIGH | 8 | B1 grammar taught at A2 level |
| MEDIUM | 0 | -- |
| LOW | 49 | Missing recommended fields (register, activity_hints) |

## CRITICAL Issues

### 1. word_target mismatch: a2-final-exam (seq=76)

**Plan:** `plans/a2/a2-final-exam.yaml`
**Problem:** `word_target: 2000` but focus is `checkpoint`, which requires `1500` per config.py.
**Fix:**
```yaml
# OLD
word_target: 2000

# NEW
word_target: 1500
```
Section budgets would also need proportional reduction (current sum = 2000).

## HIGH Issues — B1 Grammar at A2 Level

The State Standard 2024 places the following grammar concepts at B1, NOT A2. Six plans teach them at A2:

### Pattern 1: Conditional Mood (B1 §4.2.3.3)

| Plan | Seq | Issue |
|------|-----|-------|
| if-i-were | 27 | Teaches conditional mood (якби + past tense, б/би particle) |
| checkpoint-aspect-comparison | 30 | Reviews conditional mood content from seq=27 |

**State Standard:** Conditional mood (умовний спосіб) first appears at B1 (§4.2.3.3, line 2297).
**A2 does NOT include conditional mood.**

**Recommendation:** Either (a) move these to late A2 as "preview/scaffolding" with explicit labeling that this is B1-bound content, or (b) relocate to B1 proper. The approach in seq=27 (teaching both якщо and якби) is pedagogically sound but exceeds A2 scope.

### Pattern 2: Participles and Gerunds (B1 §4.2.3.1)

| Plan | Seq | Issue |
|------|-----|-------|
| participles-passive | 73 | Teaches passive participles (-ний/-тий) |
| impersonal-passive | 74 | Teaches -но/-то impersonal passive |
| gerunds-intro | 75 | Teaches present (-ючи/-ачи) and past (-вши/-ши) gerunds |

**State Standard:** Participles (дієприкметники) and gerunds (дієприслівники) first appear at B1 (§4.2.3.1, lines 2269-2291).

**Recommendation:** These three plans (seq 73-75) appear to be intentional "bridge to B1" modules at the end of A2. The plans themselves acknowledge this ("Scaffolding B1 morphological concepts"). Consider:
- Keeping them but adding explicit `bridge_to: B1` metadata
- OR moving them to early B1

### Pattern 3: Indefinite/Negative Pronouns (B1 §4.2.1.4)

| Plan | Seq | Issue |
|------|-----|-------|
| indefinite-negative-pronouns | 21 | Teaches хтось, будь-хто, ніхто, ніщо |

**State Standard:** Indefinite pronouns (хтось, щось, дехто) and negative pronouns (ніхто, ніщо) first appear at B1 (§4.2.1.4, lines 2095-2113). A2 pronouns are limited to "possessive, demonstrative, interrogative" (§4.2.1.4, lines 1244-1254).

**Recommendation:** хтось/щось are extremely common in daily speech and learners encounter them early. Consider:
- Keeping the plan but marking it as "early exposure" with simplified scope
- OR noting in the plan that this exceeds strict A2 scope

## LOW Issues — Missing Recommended Fields

### Missing `register` field: 49 plans

Almost two-thirds of A2 plans lack the `register` field. This is a template-level gap, not a per-plan issue. All A2 content should specify register (розмовний, нейтральний, офіційний).

### Missing `activity_hints` field: 22 plans

Plans in the A2.2-A2.4 phases (seq 22-49) commonly lack activity_hints. These were likely generated in a batch that didn't include this field.

**Affected plans:** the-best-the-worst (seq=23), preferences-and-choices (seq=24), if-i-were (seq=27), complete-imperative (seq=28), smart-shopping (seq=29) ... and 17 more.

### Missing `grammar` field on grammar-focused plans: 6

6 plans with `focus: grammar` lack the `grammar` field:
- preferences-and-choices (seq=24)
- numerals-and-nouns (seq=25)
- complete-imperative (seq=28)
- because-and-although (seq=32)
- adjective-suffixes-qualities (seq=44)
- adjective-suffixes-types (seq=45)

## Suggested Template Fixes

1. **Add `register` to all A2 plans** — Default to `розмовний` for practical modules, `нейтральний` for grammar modules
2. **Add `activity_hints` to all plans missing it** — Even basic hints improve build quality
3. **Add `grammar` to grammar-focused plans** — Required for State Standard alignment checking
4. **Add `bridge_to: B1` metadata** for seq 73-75 (participles, passive, gerunds)
5. **Fix a2-final-exam word_target** — Change from 2000 to 1500

## Plans with Clean PASS (69 total)

All other plans passed structural checks, word_target validation, and State Standard alignment. Vocabulary hints are present in all 76 plans. Version strings are correctly formatted as strings in all plans.

## RAG Verification Notes

Vocabulary spot-checks via VESUM confirmed:
- айтішник: exists (noun, animated masculine)
- бракувати: exists (verb, imperfective)
- вболівати: exists (verb, imperfective)

RAG textbook search was unavailable during this review session (service timeout). Grammar verification against textbooks should be done in a follow-up review.
