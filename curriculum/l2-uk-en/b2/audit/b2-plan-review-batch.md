# B2 Plan Review — Batch Summary

**Track:** B2 | **Total modules:** 86 | **Date:** 2026-03-05
**Reviewer:** Claude Opus 4.6 (plan-review skill)
**Reference:** Issue #729

---

## Executive Summary

**Overall verdict: NEEDS FIXES**

All 86 plans share `word_target: 4000` (correct) and section budgets sum to exactly 4000 (correct). Version fields are all properly quoted as strings (`'2.0'`). Grammar content aligns well with State Standard B2 (lines 2452-3479). The core linguistic content is strong and pedagogically sound.

However, there are **two systemic issues** affecting ~60% of plans that must be fixed before builds:

1. **Two incompatible plan formats** — 16 early plans (sequences 1-10, plus a few others) use an older schema missing `grammar:`, `register:`, `subtitle:`, and `pedagogy:` fields. 44 plans (mostly seq 36+) are missing `register:`.
2. **Template activity hints** — 52 of 86 plans use a minimal boilerplate pattern (reading + essay-response + true-false, ~3 types total) instead of level-appropriate diverse activity hints.

---

## Rule Compliance (All 86 Plans)

| Check | Status | Details |
|-------|--------|---------|
| word_target | **PASS** (86/86) | All plans: 4000, matches config.py |
| section_budgets | **PASS** (86/86) | All plans sum to exactly 4000 (+0%) |
| version_string | **PASS** (86/86) | All use `version: '2.0'` (quoted) |
| required_fields | **FAIL** (44/86) | See "Missing Fields" below |

### Missing Fields by Pattern

**Pattern A: Old-format plans (16 plans)** — missing `grammar:`, `register:`, `subtitle:`, `pedagogy:`

These 16 plans use the older schema with `module_type:`, `immersion: 100% Ukrainian`, and inline `sources:` blocks but lack the newer required fields:

1. passive-voice-system (seq 1)
2. past-passive-participles (seq 2)
3. b2-impersonal-passive (seq 3)
4. reflexive-passive (seq 4)
5. third-person-plural-passive (seq 5)
6. passive-in-context (seq 6)
7. active-participles-present (seq 7)
8. active-participles-past (seq 8)
9. participles-vs-relative-clauses (seq 9)
10. checkpoint-passive-voice (seq 10)
11. multi-clause-sentences (seq 18)
12. emphasis-and-inversion (seq 19)
13. stylistic-connectors (seq 20)
14. parenthetical-expressions (seq 16)
15. register-introduction (seq 25)
16. register-formal-informal (seq 26)
17. register-business-ukrainian (seq 27)
18. register-official-legal (seq 29)

**Pattern B: Missing `register:` only (28 additional plans)** — these have `grammar:`, `subtitle:`, `pedagogy:` but no `register:` field:

academic-writing, aspect-nuances-imperative-infinitive, aspect-nuances-secondary-imperfectivization, b2-one-member-sentences, b2-pidsumkovyy-ohlyad, capstone-prezentatsiya, capstone-research, checkpoint-register, law-justice-vocabulary, modern-diaspora, mystetstvo-i-literatura, nauka-i-doslidzhennia, news-analysis-basics, politics-government-vocabulary, professional-email-advanced, professional-reports-advanced, professional-reports-basics, register-colloquial-style, register-literary-ukrainian, register-media-journalistic, register-practice-cross-register-rewriting, register-religious-ukrainian, religion-in-ukraine, tekhnolohii-ta-shi, text-analysis

**Pattern C: Missing `subtitle:` only (2 plans)**:
idioms-animals, idioms-nature

---

## State Standard Alignment

Grammar topics across all 86 B2 plans were cross-referenced against State Standard 2024 B2 section (lines 2452-3479). Alignment is **strong**:

| State Standard Area | Plan Coverage | Status |
|---|---|---|
| §4.1.1 Morphology (noun/adj/numeral/pronoun) | Covered by seq 42-53 (morphology block + word formation) | PASS |
| §4.1.2 Cases (advanced meanings) | Implicitly covered across grammar modules; no dedicated case modules | MEDIUM — see note |
| §4.1.3 Verb forms (pluperfect, conditional, aspect) | pluperfect-tense, conditional-mood-particles, aspect-nuances-* | PASS |
| §4.2 Word formation | 5 dedicated modules (seq 46-50) | PASS |
| §4.3 Syntax (all areas) | 12 modules (seq 11-24) | PASS |
| §4.3.5 Direct/indirect speech | direct-indirect-speech (seq 21) | PASS |
| §4.4 Stylistics (phonetic, lexical, syntactic) | 12 register modules + synonymy + idioms | PASS |

### Note on Cases

The State Standard B2 §4.1.2 specifies advanced case usage (partitive genitive, ethical dative, abstract accusative, etc.) but there are no dedicated B2 modules for case-level review. Case usage is addressed within grammar modules (e.g., passive voice modules handle instrumental, etc.) but not systematically. This is acceptable at B2 since these were covered at B1, but could benefit from explicit cross-referencing in plan `grammar:` fields.

---

## Grammar Verification (Textbook RAG — Sampled)

| Concept | Textbook Source | Correct? | Notes |
|---------|----------------|----------|-------|
| Pluperfect = past + був/була/було/були | Grade 10, Karaman (chunk s0325) | YES | Textbook confirms formation via past tense paradigm |
| -но/-то constructions with accusative object | Grade 7, Avramenko (chunk s0130); Grade 11, Avramenko (chunk s0109) | YES | Textbook confirms passive constructions pattern |
| Active participles (-учий/-ючий) as limited/bookish | Grade 11, Avramenko §25 | YES | Textbook confirms preference for relative clauses |
| Reflexive passive (-ся) for imperfective | Consistent with standard grammar | YES | Process vs result distinction correctly framed |

---

## Vocabulary Verification (Sampled)

| Word | VESUM | Issues |
|------|-------|--------|
| чимчикувати | OK (verb:imperf:inf) | None |
| шкутильгати | OK (verb:imperf:inf) | None |

### CRITICAL: Generic Boilerplate Vocabulary

**28 plans** contain identical boilerplate "required" vocabulary that is not module-specific:
- `термін (term)`, `поняття (concept)`, `процес (process)`, `метод (method)`

These four words appear in `vocabulary_hints.required` across plans as diverse as word-formation, idioms, conjunctions, and professional email. This is a content generation artifact — the vocabulary was not customized for each module's actual topic.

**Affected plans:** academic-writing, advanced-conjunctions-i, aspect-nuances-imperative-infinitive, aspect-nuances-secondary-imperfectivization, b2-final-exam, b2-one-member-sentences, checkpoint-domain, checkpoint-lexicology, checkpoint-morphology, complex-syntax-ellipsis-parcelling, correlative-constructions, discussion-debate, economics-business-vocabulary, modern-diaspora, nauka-i-doslidzhennia, numeral-declension-compound-numbers, numeral-declension-time-dates, presentation-skills-advanced, professional-email-basics, professional-reports-basics, proverbs-nature-time-caution, register-literary-ukrainian, register-practice-cross-register-rewriting, set-expressions-combined, word-formation-abstract-nouns, word-formation-adverbs-integration, word-formation-person-suffixes, word-formation-place-object-names

---

## Activity Hints Quality

### CRITICAL: Template Activity Hints (52/86 plans)

**52 plans** use an identical minimal activity pattern:
```yaml
- type: reading
  focus: Аналіз тексту
  items: 4
- type: essay-response
  focus: Практичне застосування
- type: true-false
  focus: Перевірка розуміння
  items: 8
```

This is a boilerplate template, not module-specific activity design. Issues:
- Only 3 activity types (reading, essay-response, true-false) — fails variety requirements
- No items count on essay-response
- Generic focus labels (not tailored to module content)
- Missing: quiz, fill-in, match-up, group-sort, error-correction
- B2 requires >=6 activities with diverse types (Tier 2 standard: >=60% variety)

**Well-designed activity hints (34 plans)** have 6-7 activity types with specific focus descriptions (e.g., passive-voice-system has quiz, match-up, group-sort, fill-in x2, quiz, essay-response with 12-16 items each).

### Plans with Good Activity Hints (for reference):
passive-voice-system, past-passive-participles, b2-impersonal-passive, reflexive-passive, third-person-plural-passive, passive-in-context, active-participles-present, active-participles-past, participles-vs-relative-clauses, checkpoint-passive-voice, phrases-word-combinations, predicate-types, secondary-sentence-members, b2-one-member-sentences (has 6 types despite template vocab), homogeneous-members, parenthetical-expressions, detached-members, multi-clause-sentences, emphasis-and-inversion, stylistic-connectors, direct-indirect-speech, checkpoint-syntax, register-introduction, register-formal-informal, register-business-ukrainian, register-academic-technical, register-official-legal, checkpoint-register (partial), synonymy-types-and-rows, synonymy-in-registers, synonymy-practice-precision, pluperfect-tense, conditional-mood-particles

---

## Immersion Field Inconsistency

Two formats observed:
- **Old format:** `immersion: 100% Ukrainian` (string) — 18 plans
- **New format (some):** `immersion: 100` (bare number) — 16 plans
- **Most new-format plans:** No `immersion:` field at all — 52 plans

This is a LOW issue since the build pipeline may not consume this field from plans, but it should be standardized.

---

## Issues Found

### CRITICAL (must fix before build)

1. **Template activity hints in 52/86 plans** — Only 3 generic types (reading, essay-response, true-false). Fails B2 variety requirements. Each plan needs module-specific activity hints with 6+ types, specific focus descriptions, and item counts.

2. **Generic boilerplate vocabulary in 28/86 plans** — Required vocab contains `термін`, `поняття`, `процес`, `метод` instead of module-specific words. These are not wrong words, but having them in *every* module's required vocabulary is evidence the vocab hints were not customized.

### HIGH (should fix before build)

3. **Missing `grammar:` field in 18/86 plans** — Plans without explicit grammar field cannot be properly validated against State Standard. The grammar topics ARE present in the content_outline, but not declared as a top-level field for machine-readable validation.

4. **Missing `register:` field in 44/86 plans** — Register is a required field per plan schema. Even if the module doesn't focus on register, it should declare the target register of its content.

5. **Missing `subtitle:` in 18/86 plans** — Subtitle provides the English translation for navigation. Older plans lack this.

6. **Missing `pedagogy:` in 18/86 plans** — Pedagogy approach (TTT, CBI, CLIL, etc.) should be declared for build guidance.

### MEDIUM (fix if possible)

7. **No dedicated B2 case-review modules** — State Standard B2 §4.1.2 specifies advanced case meanings (ethical dative, partitive genitive, etc.) but these are only implicitly covered through other modules (passive voice = instrumental, etc.). Consider whether explicit case modules are needed or if cross-referencing in grammar fields is sufficient.

8. **Inconsistent `connects_to` format** — Old plans use `b2-NN (Description)` format, new plans use bare slug names. Should be standardized.

9. **Inconsistent `prerequisites` format** — Old plans use `b2-NN (Description)`, new plans use bare slugs. Mix can cause build pipeline confusion.

### LOW (informational)

10. **Immersion field inconsistency** — Three formats: string "100% Ukrainian", bare number 100, or absent. Standardize to one format.

11. **`focus:` field values vary** — grammar, style, vocabulary, phraseology, skills, checkpoint. This is appropriate variation, not a bug.

---

## Pattern Analysis: Two Plan Generations

The 86 B2 plans clearly fall into two generations:

| Feature | Generation 1 (seq 1-10, 16, 18-20, 25-29) | Generation 2 (seq 11-15, 17, 21-24, 30+) |
|---|---|---|
| Has `grammar:` | No | Yes |
| Has `register:` | No | Mostly no (but some yes) |
| Has `subtitle:` | No | Yes |
| Has `pedagogy:` | No | Yes |
| Has `sources:` | Yes (detailed) | No |
| Has `module_type:` | Yes | No |
| Activity hints | Custom (6-7 types, specific) | Template (3 types, generic) |
| Vocabulary hints | Custom (module-specific) | Often generic boilerplate |

**Root cause:** Plans were generated in at least two batches with different templates. Generation 1 had better activity/vocab customization but missed newer schema fields. Generation 2 added schema fields but used template activity/vocab patterns.

---

## Suggested Fixes

### Fix 1: Add missing schema fields to Generation 1 plans (18 plans)

For each old-format plan, add:
```yaml
subtitle: [English translation of title]
pedagogy: TTT  # or appropriate
grammar:
- [list grammar topics from content_outline]
register: [appropriate register]
```

### Fix 2: Replace template activity hints (52 plans)

Replace the boilerplate `reading + essay-response + true-false` pattern with module-specific hints. Minimum 6 types, including:
- quiz (recognition)
- fill-in (production)
- match-up or group-sort (classification)
- error-correction (analysis)
- essay-response (extended production)
- At least 1 more type appropriate to content

### Fix 3: Replace generic vocabulary (28 plans)

Replace `термін`, `поняття`, `процес`, `метод` with words actually specific to each module's topic. For example:
- `word-formation-person-suffixes` should have suffix-related vocab as required, not generic academic terms
- `idioms-somatic` should not list `процес` as required vocabulary

### Fix 4: Add `register:` to 44 plans

Even if the field value is just `varies` or `науковий`, it should be present.

### Fix 5: Standardize `connects_to` and `prerequisites` format

Choose one format: either `b2-NN (Description)` or bare slug. Recommend bare slug for machine readability.

---

## PASS/FAIL Counts

| Verdict | Count | Notes |
|---------|-------|-------|
| PASS | 34 | Fully-specified plans with custom activities and vocab |
| NEEDS FIXES | 52 | Template activities and/or generic vocab and/or missing fields |
| FAIL | 0 | No plans have wrong word targets or incorrect grammar |

**No individual plan is rejected** — the content outlines and grammar coverage are strong across the board. The issues are schema completeness and activity/vocab templating, not content quality.

---

## Recommendation

The 34 well-specified plans (mostly passive voice seq 1-10 and syntax seq 11-24) can proceed to build immediately. The 52 template-pattern plans need activity and vocabulary hint enrichment before building. This can be done as a batch template fix operation.

**Priority order:**
1. Fix template activity hints (CRITICAL — blocks build quality)
2. Fix generic vocabulary (CRITICAL — affects activity generation)
3. Add missing schema fields (HIGH — affects validation)
4. Standardize format inconsistencies (MEDIUM)
