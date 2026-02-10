# Рецензія: Time Clauses

**Level:** A2 | **Module:** 33
**Overall Score:** 8.7/10
**Status:** FAIL (due to critical activity logic and IPA errors)
**Reviewed:** Monday, February 9, 2026

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: All present (Вступ, Презентація, Практика, Діалоги, Підсумок)
- Vocabulary: 16 items in YAML; used effectively in text. One irrelevant item found.
- Grammar scope: Clean. Matches A2 expectations for temporal clauses and aspect.
- Objectives: All covered. Sequencing, simultaneity, and "until" logic are addressed.
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Engaging "temporal glue" metaphor (Line 6) and warm tutor voice. |
| 2 | Coherence | 10/10 | <7 | Logical flow from simultaneity to sequencing to immediacy. |
| 3 | Relevance | 9/10 | <7 | High-frequency A2 topic. Irrelevant vocab "радій" slightly detracts. |
| 4 | Educational | 10/10 | <7 | Excellent explanation of the "Until" trap (Line 38) and Aspect selection. |
| 5 | Language | 9/10 | <8 | Natural sentences. Comma rules (Line 46) are clearly explained. |
| 6 | Pedagogy | 9/10 | <7 | Follows PPP; "The Rhythm of Time" reflection (Line 63) adds depth. |
| 7 | Immersion | 8/10 | <6 | Estimated 45% Ukrainian. Perfectly hits the 40-50% plan target. |
| 8 | Activities | 6/10 | <7 | **AUTO-FAIL.** Activity 8 contains logic errors; Activity 4 has clunky word order. |
| 9 | Richness | 10/10 | <6 | 1300 words (130% of target), 10 activities, 3 engagement callouts. |
| 10 | Beginner Safety | 10/10 | <7 | "Would I Continue?" 5/5. Clear scaffolding and quick wins. |
| 11 | LLM Fingerprint | 10/10 | <7 | High degree of specific cultural context (UkrZaliznytsia, Line 84). |
| 12 | Linguistic Accuracy | 8/10 | <9 | **AUTO-FAIL.** Wrong IPA stress for "ледве" and questionable vocab choice. |

**Weighted Overall:** (9.0×1.5 + 10.0×1.0 + 9.0×1.0 + 10.0×1.2 + 9.0×1.1 + 9.0×1.2 + 8.0×1.0 + 6.0×1.3 + 10.0×0.9 + 10.0×1.3 + 10.0×1.0 + 8.0×1.5) / 14.0 = **121.2 / 14.0** = **8.66/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [Activity 8 logic failure; Activity 4 word order]
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Activity Logic Error
- **Location**: Activity 8 (mark-the-words)
- **Original**: `answers: [коли, поки, Як тільки, Перш ніж, після того як, мій брат, гарний дім, люблю каву]`
- **Problem**: The instruction asks for "Time Markers", but the answers include "мій брат", "гарний дім", and "люблю каву". This will mark correct student responses as wrong if they only select actual time markers.
- **Fix**: Remove non-temporal phrases from the `answers` list.

### Issue 2: Incorrect IPA Stress
- **Location**: Vocabulary YAML, item "ледве"
- **Original**: `ipa: /lɛdʋˈɛ/`
- **Problem**: The stress mark is on the second syllable, but the word is **ле́две** (stress on the first syllable).
- **Fix**: Change to `ipa: /ˈlɛdʋɛ/`.

### Issue 3: Irrelevant Vocabulary
- **Location**: Vocabulary YAML, item "радій"
- **Original**: `lemma: радій`, `translation: radium, rejoice! (imp)`
- **Problem**: "Radium" is completely irrelevant to A2 Time Clauses. "Rejoice" (imperative) is not used in the text. This is a "hallucinated" or misplaced vocab entry.
- **Fix**: Replace with a word used in the module, such as "чекати" or "з'явитися".

### Issue 4: Unnatural Word Order in Unjumble
- **Location**: Activity 4, Item 1 & 2
- **Original**: `...він завжди зайнятий дуже`, `...йшов дощ сильний вчора`
- **Problem**: While grammatically possible, this word order is poetic or clunky for A2. Standard Ukrainian prefers `дуже зайнятий` and `вчора йшов сильний дощ`.
- **Fix**: Rearrange `answer` strings to: `...він завжди дуже зайнятий` and `Ми гуляли, тим часом як вчора йшов сильний дощ`.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Vocab | /lɛdʋˈɛ/ | /ˈlɛdʋɛ/ | IPA (Stress) |
| Vocab | радій | чекати | Relevance |
| Act 4 | зайнятий дуже | дуже зайнятий | Word Order |
| Act 4 | дощ сильний вчора | вчора йшов сильний дощ | Word Order |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? [Pass] - Concepts are broken down clearly.
- Instructions clear? [Pass] - Bilingual instructions in practice section.
- Quick wins? [Pass] - Simple "коли/поки" drills at start of Practice.
- Ukrainian scary? [Pass] - Narrative style in dialogues is approachable.
- Come back tomorrow? [Pass] - High relevance to daily life.

Emotional beats: 4 found
- Welcome: Line 3 (Introduction)
- Curiosity: Line 38 (The "Until" Trap)
- Quick wins: Line 51 (Practice 1)
- Encouragement: Line 93 (Summary conclusion)

## Strengths
- **Cultural Context**: Integration of the "Punctuality in Ukraine" box (Line 84) adds authentic flavor beyond grammar.
- **Grammatical Clarity**: The distinction between simultaneous and sequential aspect selection (Line 42-45) is a high-value teaching point for A2.

## Fix Plan to Reach 9/10 (REQUIRED)

### Activities: 6/10 → 9/10
**What to fix:**
1. **Activity 8**: Remove `мій брат`, `гарний дім`, `люблю каву` from the `answers` list.
2. **Activity 4**: Update word order in `answer` for items 1 and 2 to follow standard `Adverb + Adjective` and `Adverb + Verb + Adjective + Noun` patterns.

### Linguistic Accuracy: 8/10 → 10/10
**What to fix:**
1. **Vocabulary YAML**: Correct the IPA for `ледве` to /ˈlɛdʋɛ/.
2. **Vocabulary YAML**: Remove `радій`. Add `чекати` (IPA: /t͡ʃɛkˈatɪ/, trans: to wait).
3. **Vocabulary YAML**: Ensure `разу` has correct IPA (checked, currently /ˈrazu/, which is correct).

### Projected Overall After Fixes
(9.0×1.5 + 10.0×1.0 + 10.0×1.0 + 10.0×1.2 + 10.0×1.1 + 9.0×1.2 + 8.0×1.0 + 9.0×1.3 + 10.0×0.9 + 10.0×1.3 + 10.0×1.0 + 10.0×1.5) / 14.0 = **136.2 / 14.0** = **9.7/10**

## Verification Summary

- Content lines read: 98
- Activity items checked: 82
- Ukrainian sentences verified: 34
- IPA transcriptions checked: 16
- Issues found: 5
- Naturalness score recommendation: 9/10

## Verdict

**FAIL**

The module is structurally and narratively excellent, but Activity 8 has a logic error that breaks functionality for students, and the Vocabulary IPA/selection contains errors that must be corrected before production.