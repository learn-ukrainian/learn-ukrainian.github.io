# Рецензія: Practical Intro

**Level:** A2 | **Module:** 57
**Overall Score:** 8.4/10
**Status:** FAIL
**Reviewed:** 2026-02-10

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: all present
- Vocabulary: 4/8 from plan used (Missing: правило, контекст, правильно, неправильно), 6 extra words found in YAML
- Grammar scope: clean
- Objectives: all covered
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Clear progression from theory to practice. |
| 2 | Coherence | 8/10 | <7 | Inconsistency in Accusative case usage (Лист vs Листа). |
| 3 | Relevance | 10/10 | <7 | Highly relevant review of core A2 grammar. |
| 4 | Educational | 9/10 | <7 | Good error correction and strategy sections. |
| 5 | Language | 8/10 | <8 | Pedagogical confusion in "Aspect Pairs" example. |
| 6 | Pedagogy | 9/10 | <7 | Strong PPP structure. |
| 7 | Immersion | 8/10 | <6 | Good use of Ukrainian, but explanations are English-heavy (appropriate for review). |
| 8 | Activities | 8/10 | <7 | One activity has vague instructions. |
| 9 | Richness | 9/10 | <6 | Content is dense and valuable. |
| 10 | Beginner Safety | 8/10 | <7 | Heavy metalanguage, but mitigated by clear explanations. |
| 11 | LLM Fingerprint | 9/10 | <7 | No obvious AI hallucinations or patterns. |
| 12 | Linguistic Accuracy | 9/10 | <9 | Grammar is correct, just inconsistent for learners. |

**Weighted Overall:** (13.5 + 8 + 10 + 10.8 + 8.8 + 10.8 + 8 + 10.4 + 8.1 + 10.4 + 9 + 13.5) / 14.0 = **8.66/10** (Adjusted to **8.4** for multiple minor issues)

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: Activity 14 (Mark the Words) has vague instructions.
- Beginner safety: 4/5

## Critical Issues Found

### Issue 1: Inconsistent Accusative Rule (Inanimate Masculine)
- **Location**: Section "Skill 2: Verb Aspect", Model: Aspect Pairs
- **Original**: "Я писав **листа** вчора..." / "Я написав **листа**..."
- **Problem**: Earlier in Skill 1, the module teaches "Я йду в **парк**" (Accusative = Nominative for inanimate). Suddenly using "**листа**" (Accusative = Genitive form) without explanation confuses the learner about the rule for inanimate masculine nouns. While "листа" is correct usage, it contradicts the simplified A2 rule just demonstrated.
- **Fix**: Change to "Я писав **лист**..." and "Я написав **лист**..." to maintain pedagogical consistency.

### Issue 2: Missing Required Vocabulary
- **Location**: Throughout text
- **Original**: (Missing words)
- **Problem**: Plan requires `vocabulary_hints`: "правило", "контекст". These words do not appear in the text.
- **Fix**: Add sentences containing these words to the "Огляд" or "Skill 4" sections.

### Issue 3: Vague Activity Instructions
- **Location**: `activities/practical-intro.yaml`, Item 14 (type: mark-the-words)
- **Original**: `instruction: Клацніть на слова, що відповідають критерію.`
- **Problem**: The "criterion" is not stated in the instruction. The user doesn't know what to click (Verbs? Nouns? Past tense?).
- **Fix**: Change instruction to: `instruction: Знайдіть усі дієслова минулого часу (Find all past tense verbs).`

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Skill 2 | Я писав листа | Я писав лист | Pedagogical Inconsistency |
| Skill 2 | Я написав листа | Я написав лист | Pedagogical Inconsistency |

## Beginner Safety Audit

"Would I Continue?" Test: 4/5
- Overwhelmed? No, structure is clear.
- Instructions clear? Mostly, except for one activity.
- Quick wins? Yes, "Strategy" boxes are helpful.
- Ukrainian scary? A bit heavy on cases, but expected for review.
- Come back tomorrow? Yes.

Emotional beats: 4 found
- Welcome: "Вітаємо!"
- Curiosity: "Чи можете ви...?" headers.
- Quick wins: "Стратегія вибору відмінка".
- Encouragement: "Не бійтеся помилок."

## Strengths
- Excellent "Myth Buster" regarding the word "що".
- clear, structured review of 7 cases with examples.
- Good integration of "Naturalness" advice (politeness).

## Fix Plan to Reach 9/10 (REQUIRED)

### Language: 8/10 → 9/10

**What to fix:**
1.  **Section "Skill 2: Verb Aspect"**: Change "Я писав листа" -> "Я писав лист".
2.  **Section "Skill 2: Verb Aspect"**: Change "Я написав листа" -> "Я написав лист".
    *   *Why*: Removes confusion about Inanimate Accusative rule (A2 level).
3.  **Section "Огляд"**: Add sentence: "У цьому модулі ми розглянемо основні **правила** та використаємо їх у **контексті**."
    *   *Why*: Satisfies missing plan vocabulary requirements.

### Activities: 8/10 → 9/10

**What to fix:**
1.  **Activity 14 (mark-the-words)**: Change `instruction` from "Клацніть на слова, що відповідають критерію." to "Знайдіть усі дієслова минулого часу."
    *   *Why*: User cannot guess the task otherwise.
2.  **Activity 10 (Select - Case Detector)**: Change Item "«Пишу листа»" to "«Пишу лист»" (or "«Бачу брата»" if an unambiguous Accusative is needed).
    *   *Why*: Aligns with the content fix and avoids ambiguity for students who know "Inanimate = Nominative".

### Projected Overall After Fixes

(All dimensions move to 9 or 10) => **9.3/10**

## Verification Summary

- Content lines read: 140
- Activity items checked: 60+
- Ukrainian sentences verified: ~30
- IPA transcriptions checked: 6
- Issues found: 3
- Naturalness score recommendation: 9/10

## Verdict

**FAIL**

The module is strong but fails on pedagogical consistency regarding the Accusative case ("лист" vs "листа") and contains a vague activity instruction that makes the task unsolvable without guessing. Fixing these specific issues will easily push the score above 9.0.