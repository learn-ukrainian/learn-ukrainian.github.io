# Рецензія: At the Café

**Level:** A1 | **Module:** 19
**Overall Score:** 9.5/10
**Status:** PASS
**Reviewed:** 2026-02-08

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [7/8 from plan used; 4 extra words found in Activities (виделка, ніж, ложка, серветка) not in Plan/Text]
- Grammar scope: [clean / minor issue: 'Я буду' in activity not taught]
- Objectives: [all covered]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 10/10 | <7 | Coherent, engaging flow, excellent cultural context. |
| 2 | Coherence | 10/10 | <7 | Logical progression from phrases to dialogues. |
| 3 | Relevance | 10/10 | <7 | High utility content for immediate use. |
| 4 | Educational | 9/10 | <7 | Minor deduction for testing untaught vocabulary in Activity 1. |
| 5 | Language | 9/10 | <8 | Generally excellent, but IPA stress on 'візьму' is non-standard and IPA strings are inconsistently truncated. |
| 6 | Pedagogy | 10/10 | <7 | Strong PPP structure. |
| 7 | Immersion | 10/10 | <6 | ~25% immersion, good use of L2 in examples. |
| 8 | Activities | 8/10 | <7 | Deducted for "ghost vocabulary" in Match-up and untaught grammar in Group-sort. |
| 9 | Richness | 9/10 | <6 | Good cultural insights (Lviv coffee, tipping). |
| 10 | Beginner Safety | 10/10 | <7 | Safe, encouraging, clear instructions. |
| 11 | LLM Fingerprint | 10/10 | <7 | Natural, distinct voice. |
| 12 | Linguistic Accuracy | 9/10 | <9 | IPA stress error on 'візьму'. |

**Weighted Overall:** (15 + 10 + 10 + 10.8 + 9.9 + 12 + 10 + 10.4 + 8.1 + 13 + 10 + 13.5) / 14.0 = **9.48/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [Minor issue in Activity 5]
- Activity errors: [Ghost vocabulary in Activity 1]
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Ghost Vocabulary in Activity
- **Location**: `activities/19-at-the-cafe.yaml` / Activity 1 (Match-up)
- **Original**: `виделка`, `ніж`, `ложка`, `серветка`
- **Problem**: These words are not taught in the content `19-at-the-cafe.md`, nor listed in `vocabulary/19-at-the-cafe.yaml`, nor in the Plan. Students cannot match them except by guessing.
- **Fix**: Replace with taught vocabulary (e.g., `борщ`, `цукор`, `молоко`, `вода`) or add these words to a "Table Setting" vocabulary list in the main content.

### Issue 2: IPA Stress Error
- **Location**: `19-at-the-cafe.md` / Line 23
- **Original**: `/jɑ ˈʋizʲmu ˈkɑʋu/`
- **Problem**: The stress on `візьму` is placed on the first syllable. Standard Ukrainian stress is on the second syllable (`візьму́`).
- **Fix**: `/jɑ ʋizʲˈmu ˈkɑʋu/`

### Issue 3: Inconsistent IPA Truncation
- **Location**: `19-at-the-cafe.md` / Lines 24, 25, 28, 31
- **Original**: `Принесіть, будь ласка, борщ. /prɪnɛˈsʲitʲ/`
- **Problem**: The IPA transcription is provided only for the first word (`Принесіть`), ignoring the rest of the sentence. This occurs in multiple lines (`Рахунок`, `Дякую`), while others have full sentence IPA. This inconsistency is confusing.
- **Fix**: Provide full IPA for the sentences or strictly limit IPA to the key keyword if that is the intention (but the format implies full sentence). Recommended: Provide full IPA for consistency with lines 13-17.

### Issue 4: Untaught Grammar in Activity
- **Location**: `activities/19-at-the-cafe.yaml` / Activity 5 (Group-sort)
- **Original**: `Я буду каву.`
- **Problem**: The construction `Я буду` (Future of 'to be') + Accusative is colloquial and, more importantly, `буду` has not been taught. The lesson explicitly teaches `Я візьму`.
- **Fix**: Replace with `Я візьму каву` or `Можна каву?`.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 23 | `/jɑ ˈʋizʲmu ˈkɑʋu/` | `/jɑ ʋizʲˈmu ˈkɑʋu/` | Linguistics (Stress) |
| Act 5 | `Я буду каву` | `Я візьму каву` | Scope / Consistency |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? [Pass]
- Instructions clear? [Pass]
- Quick wins? [Pass] (Ordering coffee is a high-value win)
- Ukrainian scary? [Pass]
- Come back tomorrow? [Pass]

Emotional beats: 5 found
- Welcome: Warm-up section setting the scene.
- Curiosity: "Did You Know?" about café lingering.
- Quick wins: Mini-dialogues are short and achievable.
- Encouragement: "You're not learning new grammar—you're combining..."
- Progress: Checklist at the end.

## Strengths
- **Cultural Context**: The distinction between "ordering" and "demanding" (`візьму` vs `хочу`) is explained perfectly and is crucial for polite interaction.
- **Real-World Value**: Explaining "Separate checks" (`окремо`) is a very practical, high-value tip for Ukraine.
- **Activity Volume**: 8 activities is a very healthy density.

## Verdict

**PASS**

The module is excellent—practical, culturally rich, and pedagogical sound. The score is high (9.5), but the identified issues (IPA errors and untaught vocabulary in activities) are concrete and should be fixed to maintain the "Theory-First" high standard. The "ghost vocabulary" in the first activity is the most significant pedagogical slip.