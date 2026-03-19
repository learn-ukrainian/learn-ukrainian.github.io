<!-- content-hash: 30f692abbf46 -->
# Рецензія: Syllables and Word Division

**Level:** A1 | **Module:** M05
**Overall Score:** 7.5/10
**Status:** FAIL
**Reviewed:** 2026-03-19
**Reviewed-By:** claude-sonnet-4-6

## Plan Verification

```
Plan-Content Alignment: PARTIAL FAIL
- Sections: All 5 sections present as H2 ✅
- Vocabulary: 12/12 required+recommended terms defined in YAML. 5 vocab items (книга, звук, буква, слово, тут) NOT used in prose ⚠️
- Grammar scope: CLEAN — no grammar beyond syllable/division scope
- Objectives: 4/4 addressed ✅
- Activity hints: 4/4 plan-required types present (quiz, fill-in, group-sort, match-up) + 2 bonus (true-false, anagram) ✅
```

**Plan Point Checklist (content_outline.points):**

Section "Що таке склад? — What Is a Syllable?":
- Vowel as syllable core: COVERED — Line 7: 「This metalinguistic term for vowel is **голосний**. Every **голосний** creates a new beat.」
- Counting syllables (молоко, кіт, Україна): COVERED — Lines 11-19, all three examples present
- Contrast with English syllable intuition: COVERED — Line 21: 「This might feel a little different from your English syllable intuition.」

Section "Типи складів — Syllable Types":
- Open syllables: COVERED — Lines 27-33
- Closed syllables with sonorant rule: COVERED — Line 38: 「Closed syllables also happen in the middle of a word when a sonorant consonant (like **й**, **в**, **р**, **л**, **м**, **н**) comes before another consonant, as in the word **чай-ка**.」
- Consonant clusters / maximal onset: COVERED — Lines 40-45
- Practice with high-frequency words (вулиця, автобус, дерево): COVERED — Lines 29-38

Section "Правила переносу — Word Division Rules":
- Why division matters: COVERED — Line 49
- Cannot split single letter / дж-дз: COVERED — Lines 53-55
- Cannot separate ь / apostrophe: COVERED — Lines 57-59
- Can split between consonants / V-C: COVERED — Line 61
- Common learner errors + drill words: COVERED — Lines 63-69

Section "Практика — Practice":
- Syllable counting drills: COVERED — Lines 76-81
- Word division exercises: COVERED — Lines 83-87
- Reading multi-syllable words aloud: COVERED — Lines 89-94

Section "Підсумок — Summary":
- Recap: COVERED — Line 100
- Self-check: COVERED — Lines 103-105
- Next module preview: COVERED — Line 107

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Warm opening, good pacing, but lacks callout boxes and visual variety. Practice section repeats examples from earlier sections without adding new value. |
| 2 | Language | 8/10 | <8 | English is clear B1-level. Ukrainian examples are all correct. One untranslated word (острів). No Russianisms. |
| 3 | Pedagogy | 8/10 | <7 | PPP structure well-executed. Discovery approach (count vowels → rule). But no callout boxes for key rules, and the ї vowel point (research recommended callout) is buried in prose. |
| 4 | Activities | 8/10 | <7 | 6 activity types, good variety. Quiz has 10 items, fill-in 8, group-sort 13, match-up 10, true-false 8, anagram 6 = 55 total items. But true-false instruction is in Ukrainian (A1 violation). Activities are all syllable-counting — no word division activities despite being half the module. |
| 5 | Beginner Safety | 8/10 | <7 | "Would I Continue?" 4/5 — safe pacing, clear instructions, quick wins. But острів on line 43 is untranslated and could confuse. |
| 6 | LLM Fingerprint | 8/10 | <7 | Section openings are varied. No generic AI clichés. Practice section is somewhat repetitive (same words re-drilled). No callout monotony (no callouts at all). |
| 7 | Linguistic Accuracy | 9/10 | <9 | All syllable divisions verified against textbook sources. Phonetic/orthographic distinction handled correctly. One edge case: острів used without context. |

**Weighted Overall:** (8×1.5 + 8×1.1 + 8×1.2 + 8×1.3 + 8×1.3 + 8×1.0 + 9×1.5) / 8.9 = (12 + 8.8 + 9.6 + 10.4 + 10.4 + 8 + 13.5) / 8.9 = 72.7 / 8.9 = **8.2/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN] — no Russianisms found
- Calques: [CLEAN]
- Colonial framing: [CLEAN] — no Russian references; English contrast on line 21 is legitimate pedagogy
- Grammar scope: [CLEAN] — no verbs in Ukrainian sentences, all «Це + noun» pattern
- Activity errors: true-false instruction in Ukrainian at line 263 (A1 violation)
- Beginner safety: 4/5
- Factual accuracy: [CLEAN] — all syllable rules verified against Grade 5 textbooks (Avramenko, Zabolotnyi, Golub)

**D.0 Pre-Screen Disposition:**

1. **[MORPHOLOGICAL_VIOLATION] стрів** — DISMISSED (false positive). Line 43 shows 「Another example is **о-стрів**.」 This is the noun "острів" (island) displayed in syllable-divided form, not the verb "стріти". The scanner incorrectly extracted the fragment "стрів" from "о-стрів".

2. **[RUSSICISM_OR_NONSTANDARD] перенос** — DISMISSED. VESUM confirms "перенос" is a valid Ukrainian noun (noun:inanim:m:v_naz). Textbooks use both "перенос" (Avramenko Grade 5 p.85: "Основні правила переносу") and "перенесення" (Litvinova p.170). The plan vocabulary_hints explicitly lists "перенос". Both forms are standard.

3. **[AGREEMENT_ERROR] 'се' + 'перенос'** — DISMISSED (false positive). Line 45 reads: 「While written orthographic hyphenation (**перенос**) is a bit more flexible」. There is no Ukrainian word "се" adjacent to "перенос" — the scanner likely misidentified an English fragment.

4. **[AGREEMENT_ERROR] 'сільський' + 'сіль'** — DISMISSED (false positive). Line 61: 「in a word like **сільський**」. "Сільський" derives from "село" (village), meaning "rural/village". It has no morphological relationship to "сіль" (salt). The scanner made a naive root-match error.

5. **[LOW_ENGAGEMENT] 0 engagement boxes** — CONFIRMED. The module has zero callout boxes (`[!tip]`, `[!example]`, `[!cultural-note]`, etc.). This is a real richness gap causing audit FAIL.

**Pre-Computed Word Verification Disposition:**
All 10 words flagged ❌ (блі, Бі, вер, ву, дж, дз, ка, ло, ль, стр) are syllable fragments used as examples in the prose and activities (e.g., "**бі-блі-о-те-ка**", "**дж** and **дз**"). They are pedagogical demonstrations, not intended as standalone words. All dismissed.

## Critical Issues Found

### Issue 1: Zero Engagement Boxes (Audit-Blocking)
- **Location**: Entire module — all sections
- **Problem**: The module contains 0 callout boxes. Minimum for A1 is 1, and the richness audit expects engagement: 2. This is the primary cause of the audit FAIL (richness 53% < 60% threshold). The research notes specifically recommended a callout for ї as a vowel and suggested using the скоромовка «На дворі трава, на траві дрова» as a cultural hook. Neither was implemented.
- **Fix**: Add at minimum:
  - A `[!tip]` box in section "Що таке склад? — What Is a Syllable?" about ї always being its own syllable (line 19 area)
  - A `[!cultural-note]` box in section "Практика — Practice" with the скоромовка clapping exercise
  - A `[!tip]` box in section "Правила переносу — Word Division Rules" summarizing the "never split" rules as a quick reference

### Issue 2: True-False Instruction in Ukrainian (A1 Violation)
- **Location**: Activities file, line 263
- **Original**: 「Визначте, чи твердження правильне.」
- **Problem**: This instruction is entirely in Ukrainian. At A1 M05, activity instructions must be in English. The learner cannot yet parse a Ukrainian imperative sentence. All other activity instructions in this file are in English.
- **Fix**: Replace with English: "Decide whether each statement is true or false."

### Issue 3: Untranslated "острів" in Content
- **Location**: Line 43 in section "Типи складів — Syllable Types"
- **Original**: 「Another example is **о-стрів**.」
- **Problem**: The word "острів" (island) appears as a syllable division example but is never translated. Every other Ukrainian example word in the module includes its English meaning ("the word for milk: **молоко**", "the word for sister: **сестра**", etc.). An A1 learner encountering an untranslated word will be confused. The word is also not in the vocabulary YAML.
- **Fix**: Change to "Another example is the word for island: **о-стрів**."

### Issue 4: Five Vocabulary Items Not Used in Prose
- **Location**: Vocabulary YAML — items "книга", "звук", "буква", "слово", "тут"
- **Problem**: These 5 vocabulary items are defined in the vocabulary YAML but never appear in the content markdown. Vocabulary should be introduced in context within the prose. Of these, "буква" (letter) and "звук" (sound) are highly relevant metalinguistic terms that should be woven into section "Що таке склад? — What Is a Syllable?" or "Типи складів — Syllable Types".
- **Fix**: Either (a) integrate these words into the prose with translations, or (b) remove from vocabulary YAML if they're not pedagogically essential. Recommendation: add "буква" and "звук" as metalinguistic terms in the prose (they are fundamental to discussing syllables). "Книга" could appear as a syllable example (кни-га, 2 syllables). "Тут" and "слово" can remain in vocab as passive recognition items with their `example` sentences serving as introduction.

### Issue 5: Practice Section Repeats Without Adding Value
- **Location**: Section "Практика — Practice" (lines 73-96)
- **Problem**: This section re-uses the exact same words (молоко, автобус, сестра, бібліотека, університет) that were already fully worked through in sections "Що таке склад? — What Is a Syllable?" and "Типи складів — Syllable Types". No new words are introduced. A practice section should test with fresh examples to verify transfer of learning, not re-drill familiar words.
- **Fix**: Replace at least 2-3 examples with fresh words from the vocabulary (e.g., книга → кни-га, мама → ма-ма) to test whether the learner can apply the rules independently.

### Issue 6: Missing Examples Count (Richness Gap)
- **Location**: Whole module
- **Problem**: Richness audit shows examples: 4/8. The module needs more formatted example blocks. While Ukrainian examples exist inline, they aren't structured as dedicated example blocks that the richness scanner can detect.
- **Fix**: Add `[!example]` callout boxes around key demonstration sets (e.g., the open vs closed syllable examples in section "Типи складів — Syllable Types", the word division rules in section "Правила переносу — Word Division Rules").

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 43 | 「Another example is **о-стрів**.」 | Another example is the word for island: **о-стрів**. | Missing translation |
| 263 (activities) | 「Визначте, чи твердження правильне.」 | Decide whether each statement is true or false. | A1 language violation |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? **Pass** — Pacing is comfortable, 3-5 new words per section, concepts introduced one at a time
- Instructions clear? **Pass** — Always clear what the learner should do; "count the vowels" rule is simple
- Quick wins? **Pass** — 「«Це кіт.»」 on line 15 is an early quick win; the clapping metaphor is engaging
- Ukrainian scary? **Pass** — Ukrainian introduced gently with translations; 「You can think of a syllable, or **склад**, as a single beat of rhythm in a word.」
- Come back tomorrow? **Borderline** — the module is solid but visually monotone (no callout boxes, no visual aids, no tables). A nervous beginner might find the wall-of-text format less inviting than a module with visual variety.

## Strengths

- **Accurate linguistics**: All syllable divisions verified against Grade 5 textbooks (Avramenko, Zabolotnyi, Golub). The phonetic vs orthographic distinction (line 45) correctly presents both perspectives.
- **Pre-verbal compliance**: All Ukrainian sentences follow the «Це + noun» pattern — no verbs used in Ukrainian, compliant with M05 pre-verbal constraint.
- **Warm tutor voice**: 「Welcome back! You have mastered the Ukrainian alphabet, and you are doing an incredible job.」 and 「This step-by-step approach will make even the longest Ukrainian words feel easy and manageable. You are doing great!」 — consistent encouragement throughout.
- **Strong activity suite**: 6 activity types with 55 total items provide thorough practice. The quiz covers all key words, the fill-in exercises test syllable division, and the group-sort activity tests the open/closed distinction.
- **Cultural anchor**: Using Україна as the model 4-syllable word is excellent pedagogy, aligning with how Ukrainian schools teach (research notes confirm this).

## Fix Plan to Reach 9/10 (REQUIRED since score < 9.0)

### Experience Quality: 8/10 → 9/10
**What to fix:**
1. Add 3 callout boxes (see Issue 1) — `[!tip]` for ї vowel rule, `[!cultural-note]` for скоромовка, `[!tip]` for word division summary
2. Add an `[!example]` box in section "Типи складів — Syllable Types" for open vs closed comparison

**Expected score after fix:** 9/10

### Language: 8/10 → 9/10
**What to fix:**
1. Line 43: Add translation for острів (see Issue 3)

**Expected score after fix:** 9/10

### Pedagogy: 8/10 → 9/10
**What to fix:**
1. Integrate missing vocab words (буква, звук, книга) into prose (see Issue 4)
2. Add fresh examples to section "Практика — Practice" (see Issue 5)

**Expected score after fix:** 9/10

### Activities: 8/10 → 9/10
**What to fix:**
1. Line 263: Change true-false instruction to English (see Issue 2)
2. Consider adding a word-division focused activity (the fill-in tests syllable division, but a dedicated exercise on the "cannot split" rules would strengthen coverage)

**Expected score after fix:** 9/10

### Projected Overall After Fixes
```
(9×1.5 + 9×1.1 + 9×1.2 + 9×1.3 + 9×1.3 + 8×1.0 + 9×1.5) / 8.9
= (13.5 + 9.9 + 10.8 + 11.7 + 11.7 + 8 + 13.5) / 8.9
= 79.1 / 8.9 = 8.9/10
```

## Factual Verification

- Research notes consulted: YES
- Key Facts Ledger present: NO (not a seminar track — N/A)
- Grammar rules verified: All syllable rules checked against Grade 5 textbooks (Avramenko §36-37, Zabolotnyi p.88, Golub p.87). Rules are accurate.
- Textbook alignment: Content correctly mirrors textbook presentation order (single-letter rule → digraph rule → ь rule → apostrophe rule)
- Claims without research grounding: None

## Verification Summary

- Content lines read: 107
- Activity items checked: 55 (10 quiz + 8 fill-in + 13 group-sort + 10 match-up + 8 true-false + 6 anagram)
- Ukrainian sentences verified: 18
- Citations in bank: 19
- Issues found: 6

## Verdict

**FAIL**

Blocking issues: (1) Zero engagement boxes causing richness audit failure (53% < 60% threshold). (2) True-false activity instruction in Ukrainian at A1. (3) Untranslated острів. After adding 3 callout boxes and fixing the activity instruction, the module should pass audit and reach ~9/10.

---

## Post-Fix Re-Score (automated)

**Scored by:** claude-opus-4-6 (on fixed content)
**Overall Score:** 5.6/10
**Verdict:** FAIL

| Dimension | Score |
|-----------|-------|
| experience | 7/10 |
| language | 7/10 |
| pedagogy | 6/10 |
| activities | 3/10 |
| beginner_safety | 5/10 |
| llm_fingerprint | 5/10 |
| linguistic_accuracy | 8/10 |
