# Рецензія: Як говорити про граматику

**Level:** B1 | **Module:** 1
**Overall Score:** 7.9/10
**Status:** FAIL
**Reviewed:** 2026-02-18

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: PASS (All sections present)
- Vocabulary: PASS (All required terms covered)
- Grammar scope: PASS (Covers POS, cases, syntax as requested)
- Objectives: PASS
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Good flow, but the density of metaphors ("king", "engine", "artist", "cement") becomes distracting. |
| 2 | Coherence | 9/10 | <7 | Strong logical progression from words to sentences to text. |
| 3 | Relevance | 10/10 | <7 | Critical meta-skills for B1+ success. |
| 4 | Educational | 7/10 | <7 | Damaged by a broken mnemonic for cases (see Critical Issues). |
| 5 | Language | 9/10 | <8 | High quality Ukrainian generally. |
| 6 | Pedagogy | 8/10 | <7 | Good explanations, but the mnemonic error is a pedagogical trap. |
| 7 | Immersion | 9/10 | <6 | Meets the B1 Bridge target (70-85%). |
| 8 | Activities | 9/10 | <7 | Relevant and well-structured activities. |
| 9 | Richness | 8/10 | <6 | Good cultural callouts, but over-reliance on metaphors. |
| 10 | Beginner Safety | 8/10 | <7 | Clear, though the volume of text (5500+ words) is intimidating. |
| 11 | LLM Fingerprint | 5/10 | <7 | Failed metaphor density test (>8 "X is Y" metaphors). |
| 12 | Linguistic Accuracy | 5/10 | <9 | Critical error in the case mnemonic (associating "Горішки" with "Орудний"). |

**Weighted Overall:** 7.9/10

## Auto-Fail Checklist Results

- Russianisms: CLEAN
- Calques: CLEAN
- Grammar scope: CLEAN
- Activity errors: CLEAN
- Beginner safety: 4/5 (Very long text)

## Critical Issues Found

### Issue 1: Broken Case Mnemonic
- **Location**: Line 411 / Section "Відмінки: сім ключів"
- **Original**: «**О** — Орудний (слово «горішки» тут для асоціації з літерою О)»
- **Problem**: This is hallucinated logic. The word «горішки» starts with «Г», not «О». It does not help recall «Орудний». The standard mnemonic uses «Окуляри» (Glasses) or «Оленка» (name).
- **Fix**: Change «Горішки» to «Окуляри».
  Original mnemonic line: «На Різдво Дід Загубив **Окуляри** Між Ковбасками.»

### Issue 2: English text intrusion
- **Location**: Line 131 / Section "Іменник"
- **Original**: «(у значенні one item, we say *одні* as plural form)»
- **Problem**: Raw English instructional text inserted in the middle of a Ukrainian sentence/paragraph without proper formatting or brackets, breaking immersion.
- **Fix**: «(у значенні «один предмет» ми вживаємо форму множини *одні*)» or simply remove the English if redundant.

### Issue 3: Metaphor Overload (LLM Fingerprint)
- **Location**: Throughout
- **Original**: "Іменник — це абсолютний король...", "Дієслово — це двигун...", "Прикметник — це найвірніший друг...", "Числівник — це математик..."
- **Problem**: Every part of speech is defined via a "Personification/Metaphor" structure. This is a distinct AI pattern ("X is the Y of Z"). It feels artificial and repetitive.
- **Fix**: Rewrite 50% of these definitions to be direct and functional. E.g., "Дієслово позначає дію або стан" instead of "Дієслово — це двигун".

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| 131 | we say *одні* as plural form | ми вживаємо *одні* як форму множини | Immersion |
| 411 | Горішки | Окуляри | Linguistic Accuracy |

## Beginner Safety Audit

"Would I Continue?" Test: 3/5
- Overwhelmed? **Fail** (5500 words is very long for a single sitting)
- Instructions clear? **Pass**
- Quick wins? **Pass**
- Ukrainian scary? **Pass**
- Come back tomorrow? **Pass**

## Strengths
- Excellent logical structure moving from word parts to sentence roles.
- The "Textbook Analysis" section is a brilliant practical application of the theory.
- Cultural callouts (Smotrytsky, Shevchenko) are well-integrated and relevant.

## Fix Plan to Reach 9/10

### Linguistic Accuracy: 5/10 → 10/10
**What to fix:**
1. Line 411: Change «Горішки» → «Окуляри» — Fixes the broken mnemonic.
2. Line 414: Update the explanation: «**О** — Орудний (слово «Окуляри»)».

### LLM Fingerprint: 5/10 → 8/10
**What to fix:**
1. Section "Частини мови": Remove "King", "Engine", "Artist", "Mathematician" metaphors. Replace with functional definitions for at least 3 of them.
2. Line 13: Remove "Це скелет, на якому тримається живе тіло мовлення" (Purple prose).

### Immersion/Polish: 9/10 → 10/10
**What to fix:**
1. Line 131: Translate "we say *одні* as plural form" into Ukrainian.

### Projected Overall After Fixes
```
(8*1.5 + 9*1.0 + 10*1.0 + 9*1.2 + 9*1.1 + 9*1.2 + 10*1.0 + 9*1.3 + 9*0.9 + 8*1.3 + 8*1.0 + 10*1.5) / 14.0 = 9.0/10
```

## Verification Summary

- Content lines read: 720
- Activity items checked: 4 activities (approx 30 items)
- Ukrainian sentences verified: ~200
- IPA transcriptions checked: 18
- Issues found: 3

## Verdict

**FAIL**

The module fails primarily due to a **critical linguistic error** in the case mnemonic ("Горішки" ≠ "Орудний"), which would confuse learners. Additionally, the **excessive word count** (139% of target) and **high metaphor density** (LLM fingerprint) require editing. The English intrusion in line 131 must also be fixed.
