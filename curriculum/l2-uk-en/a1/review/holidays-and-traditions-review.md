# Рецензія: Holidays & Traditions

**Level:** A1 | **Module:** 33
**Overall Score:** 8.5/10
**Status:** FAIL
**Reviewed:** 2026-02-08

## Plan Verification

Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [covered, plus relevant extras like 'олів'є', 'кутя']
- Grammar scope: [clean, adheres to 'fixed phrases' approach]
- Objectives: [all covered]

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Content flow is good, but activities jolt the learner with unknown terms. |
| 2 | Coherence | 9/10 | <7 | Logical progression from greetings to wishes to specific scenarios. |
| 3 | Relevance | 10/10 | <7 | Highly relevant cultural content (Christmas date change, odd number flowers). |
| 4 | Educational | 8/10 | <7 | Strong instruction, but assessment validity is compromised by ghost vocabulary. |
| 5 | Language | 10/10 | <8 | Natural Ukrainian, correct phonetics/IPA. |
| 6 | Pedagogy | 7/10 | <7 | "Ghost Vocabulary" in activities (testing words not taught). |
| 7 | Immersion | 9/10 | <6 | Good balance of cultural context and language. |
| 8 | Activities | 6/10 | <7 | **FAIL**: Significant vocabulary scope creep in Group Sort and Fill-in tasks. |
| 9 | Richness | 9/10 | <6 | Excellent cultural tips (Myth vs Fact, Pro Tip). |
| 10 | Beginner Safety | 8/10 | <7 | Safe handling of cases ("memorize as fixed phrases"). |
| 11 | LLM Fingerprint | 9/10 | <7 | Feels curated and specific. |
| 12 | Linguistic Accuracy | 10/10 | <9 | No grammatical errors found. |

**Weighted Overall:** (12+9+10+9.6+11+8.4+9+7.8+8.1+10.4+9+15) / 14 = **8.52/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [FAIL - Scope Creep]
- Beginner safety: 4/5

## Critical Issues Found

### Issue 1: Ghost Vocabulary in Activities
- **Location**: Activities YAML, `group-sort` "Holidays by Season"
- **Original**: Items include "Трійця", "День Незалежності", "День Конституції", "Івана Купала", "Святий Миколай".
- **Problem**: None of these holidays are introduced in the text or vocabulary list. A1 learners cannot sort what they don't know.
- **Fix**: Replace with taught holidays or remove. Add "8 березня", "День народження" to relevant groups if logical, or stick to the core set.

### Issue 2: Ghost Vocabulary in Activities (Part 2)
- **Location**: Activities YAML, `group-sort` "Holiday Activities"
- **Original**: Items include "цукерки", "шоколад".
- **Problem**: Not in vocab list.
- **Fix**: Replace with "кутя" (taught in text), "листівка" (taught in text).

### Issue 3: Ghost Vocabulary in Fill-in
- **Location**: Activities YAML, `fill-in` "Привітання"
- **Original**: "Наречений і наречена. ___!"
- **Problem**: "Наречений і наречена" (Bride and Groom) is unknown vocabulary.
- **Fix**: Change cue to "Це гарне весілля. ___!" or "Гірко! ___!" (if 'Гірко' was taught, otherwise stick to simple context). Suggestion: "Твоя сестра виходить заміж. ___!" (Your sister is getting married - if vocabulary allows) OR simply "Весілля! ___!".

### Issue 4: Ghost Vocabulary in Fill-in (Part 3)
- **Location**: Activities YAML, `fill-in` "Святкування"
- **Original**: "Це ___ на мій день народження." (Answer: запрошення)
- **Original**: "У мене ___ настрій!" (Answer: святковий)
- **Problem**: "Запрошення" (invitation) and "святковий" (festive) are not taught.
- **Fix**: Remove these items or replace with sentences using known words. E.g., "Це мій ___ (подарунок)."

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Act | "Наречений і наречена" | (Remove/Change) | Scope |
| Act | "Трійця", "Івана Купала" | (Remove/Change) | Scope |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? [Pass] Content is safe, but activities might panic a student ("I don't know these words!").
- Instructions clear? [Pass]
- Quick wins? [Pass]
- Ukrainian scary? [Pass]
- Come back tomorrow? [Pass]

Emotional beats: 5 found
- Welcome: "Щасливих свят!" (Warm-up)
- Curiosity: "Greetings start with З" (Aha Moment)
- Quick wins: "Learn these greetings as fixed phrases"
- Encouragement: "You're almost at the end of A1—celebrate your progress!"
- Progress: "Now you know many sincere greetings."

## Strengths
- **Cultural nuance**: Explicitly addressing the calendar shift (Dec 25) and the odd-number flower rule is high-value content.
- **Phonetics**: IPA is accurate and helpful.
- **Pragmatics**: Teaching *patterns* (З + Instr) without drowning the student in grammar tables is the right approach for A1.

## Fix Plan to Reach 9/10

### Activities: 6/10 → 9/10

**What to fix:**
1. **Activity 3 (Holidays by Season)**:
    - Remove: "Трійця", "День Незалежності", "День Конституції", "Івана Купала", "Святий Миколай".
    - Add: "8 березня" (Spring), "Весілля" (Personal).
    - Ensure all items in the sort are in the module content.
2. **Activity 4 (Holiday Activities)**:
    - Remove: "цукерки", "шоколад".
    - Add: "кутя", "писанки" (taught in text).
3. **Activity 5 (Greetings)**:
    - Item 5: Change "Наречений і наречена." to "Це гарне весілля."
4. **Activity 6 (Celebrating)**:
    - Remove Item 8 (запрошення) and Item 10 (святковий) entirely, as they introduce new nouns/adjectives not critical to the core objective.
    - Replace with:
        - Sentence: "На столі смачна ___." Answer: "кутя" (options: кутя, музика, листівка).
        - Sentence: "Ми пишемо ___." Answer: "листівку" (options: листівку, торт, свято).

**Expected score after fix:** 9/10

### Pedagogy: 7/10 → 9/10

**What to fix:**
- The fix above (aligning activities with content) automatically resolves the pedagogical issue of testing untaught material.

### Projected Overall After Fixes

(12 + 9 + 10 + 9.6 + 11 + 10.8 + 9 + 11.7 + 8.1 + 10.4 + 9 + 15) / 14 = 9.0/10

## Verification Summary

- Content lines read: 145
- Activity items checked: 45
- Ukrainian sentences verified: ~30
- IPA transcriptions checked: 12
- Issues found: 4 (All related to Activity Scope)
- Naturalness score recommendation: 10/10

## Verdict

**FAIL**

The module content is excellent, linguistically accurate, and culturally rich. However, the activities significantly violate the scope boundaries by testing vocabulary and cultural facts (specific holidays) that were not introduced in the lesson. This creates a frustrating experience for beginners ("How was I supposed to know that?"). Fixing the activities to match the taught content will easily bring this module to a 9+/10.