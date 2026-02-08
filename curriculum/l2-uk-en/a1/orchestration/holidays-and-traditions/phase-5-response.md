# Рецензія: Holidays & Traditions

**Level:** A1 | **Module:** 33
**Overall Score:** 8.3/10
**Status:** FAIL
**Reviewed:** 2026-02-08

## Plan Verification

Plan-Content Alignment: [PASS]
- Sections: [PASS - slight structural variation but covers all points]
- Vocabulary: [PASS - all required words present]
- Grammar scope: [FAIL - issues in activities with Past Tense and Genitive Plural]
- Objectives: [PASS]

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Excellent cultural notes and warm tone. |
| 2 | Coherence | 9/10 | <7 | Logical flow from greetings to wishes to specific dates. |
| 3 | Relevance | 10/10 | <7 | Highly relevant content for daily life. |
| 4 | Educational | 8/10 | <7 | Good explanations, but activities test untaught grammar. |
| 5 | Language | 9/10 | <8 | Natural Ukrainian, good cultural phrasing. |
| 6 | Pedagogy | 7/10 | <7 | Scope creep in activities (Past Tense, Genitive Plural). |
| 7 | Immersion | 8/10 | <6 | Good use of Ukrainian in "Pro Tips" and headers. |
| 8 | Activities | 6/10 | <7 | Multiple items require A2 grammar (Genitive Plural, Past Tense). |
| 9 | Richness | 9/10 | <6 | Cultural context (Calendar switch, odd numbers for flowers) is excellent. |
| 10 | Beginner Safety | 9/10 | <7 | Encouraging and accessible. |
| 11 | LLM Fingerprint | 9/10 | <7 | Feels handcrafted and culturally specific. |
| 12 | Linguistic Accuracy | 7/10 | <9 | Critical IPA error in core greeting; vocab file error. |

**Weighted Overall:** (9*1.5 + 9*1.0 + 10*1.0 + 8*1.2 + 9*1.1 + 7*1.2 + 8*1.0 + 6*1.3 + 9*0.9 + 9*1.3 + 9*1.0 + 7*1.5) / 14.0 = **116.1 / 14.0 = 8.29**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [FAIL] - Activities use Past Tense and Genitive Plural.
- Activity errors: [FAIL] - IPA error in text, Wrong lemma in vocab file.
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: IPA Error (Content)
- **Location**: Section "Common Holiday Greetings", Row "День народження"
- **Original**: `/z dɛnʲ nɑrɔˈdʒɛnnʲɑ/`
- **Problem**: The IPA shows the Nominative case `день` (/dɛnʲ/), but the phrase uses the Instrumental case `днем` (/dnɛm/).
- **Fix**: `/z dnɛm nɑrɔˈdʒɛnnʲɑ/`

### Issue 2: Vocabulary Lemma Error (YAML)
- **Location**: `vocabulary/33-holidays-and-traditions.yaml`
- **Original**: `lemma: зіркий ... translation: visonary, hawk-eyed ... pos: adj`
- **Problem**: The text mentions "перша зірка" (first star). The vocabulary file incorrectly extracted the adjective `зіркий` (sharp-sighted) instead of the noun `зірка` (star).
- **Fix**: Change lemma to `зірка`, translation to `star`, pos to `noun`, gender `f`.

### Issue 3: Grammar Scope Creep - Genitive Plural (Activities)
- **Location**: `activities/33...yaml`, Type: `fill-in`, Title: `Святкування`, Item: `На торті п'ять ___.` (Answer: `свічок`)
- **Original**: `свічок`
- **Problem**: Genitive Plural is A2 grammar. A1 students only know singular cases.
- **Fix**: Change sentence to `Ми запалюємо ___ .` (We light candles - Accusative Plural inanimate = Nominative Plural `свічки`) or `Там є ___ .` (There are candles - `свічки`).

### Issue 4: Grammar Scope Creep - Past Tense (Activities)
- **Location**: `activities/33...yaml`, Type: `fill-in`, Title: `Святкування`
- **Original**: `Я ___ квіти на день народження.` -> `отримав` (received)
- **Problem**: Past tense is typically A2. A1 focuses on Present.
- **Fix**: Change to Present Tense: `Я ___ квіти на день народження.` -> `отримую` (I receive) or `Ми купуємо` (We buy).

### Issue 5: Grammar Scope Creep - Declension III (Activities)
- **Location**: `activities/33...yaml`, Type: `fill-in`, Title: `Святкування`
- **Original**: `Скільки ___ у вас на день народження!` -> `радості`
- **Problem**: Genitive singular of III declension (`радість` -> `радості`) is complex for A1.
- **Fix**: Change to `Це велика ___ !` -> `радість` (Nominative).

## Strengths
- **Cultural Depth**: The inclusion of the calendar switch (Dec 25) and the "odd numbers for flowers" rule makes this module highly practical and culturally accurate.
- **Clear Explanations**: The explanation of "З + Instrumental" as a fixed phrase is pedogogically sound for A1.

## Fix Plan to Reach 9/10

### Linguistic Accuracy: 7/10 → 9/10

**What to fix:**
1. **Content**: Update table row "День народження" IPA from `/z dɛnʲ nɑrɔˈdʒɛnnʲɑ/` to `/z dnɛm nɑrɔˈdʒɛnnʲɑ/`.
2. **Vocabulary**: Replace entry `зіркий` with `зірка` (star).

### Activities: 6/10 → 9/10

**What to fix:**
1. **Activity "Святкування" (fill-in)**:
   - Change `Я ___ квіти на день народження.` (answer: `отримав`) to `Я ___ квіти на день народження.` (answer: `отримую` - present tense).
   - Change `На торті п'ять ___.` (answer: `свічок`) to `На торті гарні ___.` (answer: `свічки` - nominative plural).
   - Change `Скільки ___ у вас на день народження!` (answer: `радості`) to `Це велика ___!` (answer: `радість` - nominative).
2. **Activity "Holiday Sentences" (unjumble)**:
   - Change `отримав / він / квіти` to `купує / він / квіти` (He buys flowers).

### Pedagogy: 7/10 → 9/10
- The fixes in Activities section above will resolve the pedagogy scope creep issues.

## Verification Summary

- Content lines read: All
- Activity items checked: 9 activities (approx 45 items)
- Ukrainian sentences verified: ~20
- IPA transcriptions checked: 6
- Issues found: 5 (1 IPA, 1 Vocab, 3 Scope Creep)
- Naturalness score recommendation: 10/10

## Verdict

**FAIL**

The module is culturally rich and well-written, but it fails on **Grammar Scope** in the activities (testing Past Tense and Genitive Plural at A1) and has a critical **IPA error** in the core phrase "Happy Birthday". These must be fixed before release.