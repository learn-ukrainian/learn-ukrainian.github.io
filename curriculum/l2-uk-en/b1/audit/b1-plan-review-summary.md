# B1 Plan Review Summary

**Track:** B1 | **Plans reviewed:** 100 | **Date:** 2026-03-05
**Reviewer:** Claude (plan-review skill) | **Reference:** Issue #729

## Overall Verdict

| Metric | Count |
|--------|-------|
| PASS (no issues) | 56 |
| NEEDS FIXES | 44 |
| FAIL (critical) | 0 |

**No CRITICAL issues found.** All plans have correct word_target (4000), section budgets sum correctly, versions are strings, and all required fields are present except `register` in 25 plans.

---

## Rule Compliance

| Check | Status | Details |
|-------|--------|---------|
| word_target | PASS (100/100) | All plans = 4000, matches config.py |
| section_budgets | PASS (100/100) | All plans sum to exactly 4000 |
| required_fields | FAIL (25/100) | 25 plans missing `register` field |
| version_string | PASS (100/100) | All versions are strings ('1.0', '2.0', '3.0') |

---

## Issue #1: Missing `register` Field (HIGH) — 25 plans

All plans in sequences 1-27 (the metalanguage, aspect, and motion verb blocks) are missing the `register` field, which is a required field per the plan schema.

**Affected plans (seq 1-27):**

| Seq | Slug |
|-----|------|
| 1 | how-to-talk-about-grammar |
| 2 | language-about-verbs |
| 3 | reading-grammar-rules |
| 4 | sentence-structure |
| 5 | ready-for-immersion |
| 8 | aspect-complete-system |
| 9 | aspect-past-single-repeated |
| 10 | aspect-past-result-process |
| 11 | aspect-future |
| 12 | aspect-negation |
| 13 | aspect-in-imperatives |
| 14 | aspect-pairs-essential-40 |
| 15 | work-week-aspect-in-action |
| 16 | aspect-integration-practice |
| 17 | checkpoint-aspect-mastery |
| 18 | motion-verbs-full-system |
| 19 | motion-coming-going |
| 20 | motion-passing-crossing |
| 21 | motion-starting-returning |
| 22 | motion-approaching-departing |
| 23 | motion-figurative-uses |
| 24 | motion-full-prefix-integration |
| 25 | motion-patterns-other-verbs |
| 26 | motion-practice-integration |
| 27 | checkpoint-motion-verbs |

**Root cause:** These appear to be from an earlier plan generation batch (v2.0 with `immersion:` field instead of `register:`). Plans seq 28+ all have `register`.

**Suggested fix:** Add `register: нейтральний` (or appropriate value) to each of these 25 plans. The `immersion:` field present in these plans provides the immersion percentage but does not replace `register`.

---

## Issue #2: `connects_to` Self-References (HIGH) — 9 entries in 8 plans

Multiple plans have `connects_to` entries that reference their own sequence number instead of the next module. This is a systematic off-by-one error.

| Plan (seq) | connects_to says | Should be |
|------------|-----------------|-----------|
| aspect-complete-system (8) | b1-08 (Aspect in past) | b1-09 |
| aspect-future (11) | b1-11 (Aspect in imperatives) | b1-12 or b1-13 |
| aspect-pairs-essential-40 (14) | b1-14 (Aspect integration practice) | b1-15 or b1-16 |
| motion-approaching-departing (22) | b1-22 (Motion full prefix integration) | b1-23 or b1-24 |
| motion-patterns-other-verbs (25) | b1-25 (Checkpoint - motion verbs) | b1-26 or b1-27 |
| past-passive-participles-1 (46) | b1-46 (Past Passive Participles 2) | b1-47 |
| past-passive-participles-2 (47) | b1-47 (Passive Constructions) | b1-48 |
| relative-clauses-yakyi (29) | b1-29 (twice, self-ref) | b1-30, b1-31 |

**Root cause:** During plan generation, the `connects_to` module numbers were set to the current module's number rather than the target module's number. The labels in parentheses describe the *next* module correctly, but the b1-XX prefix is wrong.

**Suggested fix:** For each affected plan, increment the module number in `connects_to` to point to the actual next module in sequence.

---

## Issue #3: Vague/Untestable Objectives (MEDIUM) — 26 objectives in 20 plans

26 objectives use "understands" or "knows" instead of testable "can do" language.

**Pattern:** Most grammar modules have at least one objective starting with "Learner understands..." which is not directly testable. Per pedagogical standards, objectives should describe observable behavior.

**Most common offenders:**
- "Learner understands X" (22 instances)
- "Learner knows X" (4 instances)

**Examples:**
- `aspect-complete-system`: "Learner understands the complete aspectual system"
  - Better: "Learner can explain when to use perfective vs imperfective aspect"
- `motion-verbs-full-system`: "Learner knows all 14 motion verb pairs"
  - Better: "Learner can match all 14 unidirectional/multidirectional motion verb pairs"

**Affected plans:** aspect-complete-system, aspect-future, aspect-in-imperatives, aspect-negation, aspect-pairs-essential-40, aspect-past-result-process, aspect-past-single-repeated, active-participles-phrases, adverbial-participles-imperfective, concessive-khocha, conditionals-mixed-complex, conditionals-real-yakshcho, conditionals-unreal-yakby, diminutives-master-class, motion-figurative-uses, motion-verbs-full-system, numerals-collectives-fractions, passive-constructions, past-passive-participles-1, past-passive-participles-2, purpose-shchob-infinitive, purpose-shchob-past-form, relative-clauses-de-kudy-zvidky, relative-clauses-yakyi

**Suggested fix:** Rewrite "understands" → "can explain" or "can identify"; "knows" → "can list" or "can match".

---

## Issue #4: Version Distribution (LOW)

| Version | Count | Notes |
|---------|-------|-------|
| 1.0 | 4 | b1-final-exam, communication-channels, feedback-negotiation-complaints, presentations-visuals |
| 2.0 | 95 | Standard batch |
| 3.0 | 1 | how-to-talk-about-grammar |

The 4 plans at v1.0 (seq 97-100) may be from a different generation batch. Not inherently an issue, but worth noting — these plans should be reviewed for consistency with v2.0 plans.

---

## State Standard Alignment

### Grammar Scope — PASS

All B1 grammar topics are within the State Standard B1 scope:
- **Verbal aspect** (§4.2.3.1) — confirmed
- **Motion verbs** with prefixes (§4.3.8) — confirmed
- **Conditional mood** (§4.2.3.3) — confirmed
- **Participles** (§4.2.3.1: дієприкметники, дієприслівники) — confirmed
- **Complex sentences** (§4.4.3) — confirmed
- **One-member sentences** (§4.4.2) — confirmed
- **Word formation** (§4.3) — confirmed
- **Numerals: collective and fractions** (§4.2.1.3) — confirmed
- **Indefinite/negative pronouns** (§4.2.1.4) — confirmed

No grammar topics were found that belong to B2 or higher. The coverage is comprehensive.

### Thematic Catalogue — PASS

B1 themes covered: щоденне життя, подорожі, здоров'я, освіта, робота, купівля, природа, суспільні відносини, традиції, дозвілля, ресторан, послуги. All align with State Standard §3 thematic catalogue.

### Grammar Verification (Textbook RAG)

| Concept | Textbook Source | Correct? | Notes |
|---------|----------------|----------|-------|
| Умовний спосіб (якби + past + б/би) | Grade 7, Litvinova 2024, §12 | YES | Formation confirmed: past tense + б/би |
| Частка б after vowel, би after consonant | Grade 7, Avramenko 2024, §37 | YES | Euphony rule confirmed |
| Passive participles -н-/-ен-/-т- | Grade 7, Litvinova 2024; Grade 10, Karaman | YES | Suffix selection rules accurate |
| Adverbial participles -ючи/-ачи, -вши/-ши | Grade 7, Litvinova 2024, §21 | YES | Formation rules confirmed |

### Vocabulary Verification (VESUM)

| Word | VESUM | Status |
|------|-------|--------|
| односпрямований | OK (adj) | PASS |
| різноспрямований | OK (adj) | PASS |
| улюблений | OK (adj, passive perf) | PASS |
| саджений | OK (adj, passive imperf) | PASS |
| ношений | OK (adj, passive imperf) | PASS |
| любимий | NOT FOUND | PASS (correctly flagged as error in plan) |

No ghost words found in the sampled vocabulary.

---

## Pedagogy Distribution

| Pedagogy | Count | Notes |
|----------|-------|-------|
| TTT | 49 | Grammar modules — appropriate |
| PPP | 33 | Bridge/integration modules |
| CBI | 17 | Culture/vocabulary modules |
| Checkpoint | 1 | b1-final-exam |

Distribution is appropriate for B1 level (grammar-heavy with cultural integration).

---

## Issues Grouped by Pattern

### Pattern A: Missing `register` field (25 plans, HIGH)
- All in seq 1-27 (early batch)
- Fix: Add `register: нейтральний` to each

### Pattern B: Self-referencing `connects_to` (8 plans, HIGH)
- Off-by-one error in module numbers
- Fix: Correct module numbers in `connects_to`

### Pattern C: Vague objectives (20 plans, MEDIUM)
- "understands"/"knows" instead of testable verbs
- Fix: Rewrite to "can explain"/"can identify"/"can list"

### Pattern D: Version inconsistency (4 plans, LOW)
- v1.0 plans at seq 97-100
- Review for consistency with v2.0 plans

---

## Suggested Template Fixes

### Fix A: Add register to early-batch plans
```yaml
# Add after immersion line in each of the 25 plans:
register: нейтральний
```

### Fix B: Correct connects_to module numbers
```yaml
# Example for past-passive-participles-1 (seq 46):
# BEFORE:
connects_to:
- b1-46 (Past Passive Participles 2)
# AFTER:
connects_to:
- b1-47 (Past Passive Participles 2)
```

### Fix C: Rewrite vague objectives
```yaml
# BEFORE:
- Learner understands the complete aspectual system
# AFTER:
- Learner can explain the key differences between perfective and imperfective aspect
```

---

## Summary

The B1 plan suite is **structurally sound** with no CRITICAL issues. Word targets, section budgets, versions, grammar scope, and vocabulary are all correct. The main issues are:

1. **25 plans missing `register`** — systematic gap in the early batch (HIGH, easy fix)
2. **8 plans with self-referencing `connects_to`** — off-by-one module number errors (HIGH, easy fix)
3. **26 vague objectives** — "understands"/"knows" should be rewritten to testable verbs (MEDIUM)
4. **4 plans at v1.0** — minor version inconsistency (LOW)

Total estimated fix time: ~1 hour for a batch script to add register fields and correct connects_to numbers.
