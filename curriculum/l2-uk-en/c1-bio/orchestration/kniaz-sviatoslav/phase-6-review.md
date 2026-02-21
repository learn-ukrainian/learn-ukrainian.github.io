# Рецензія: Князь Святослав: Воїн-завойовник

**Level:** C1_BIO | **Module:** 2
**Overall Score:** 7.9/10
**Status:** FAIL
**Reviewed:** 2026-02-18

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: All plan sections present and well-structured.
- Vocabulary: 10/10 from plan (but total 10 is low for C1).
- Grammar scope: PASS
- Objectives: Met.
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Strong narrative voice, excellent "History Bite" usage, compelling hook. |
| 2 | Coherence | 9/10 | <7 | Logical chronological flow interspersed with thematic analysis. |
| 3 | Relevance | 10/10 | <7 | Perfectly matches the "Warrior Archetype" focus of the plan. |
| 4 | Educational | 9/10 | <7 | Deep historical analysis, deconstructs myths effectively. |
| 5 | Language | 8/10 | <8 | High literary quality, but occasional jarring anachronisms ("суперкорпорація"). |
| 6 | Pedagogy | 7/10 | <7 | Content-Based Instruction is good, but lacks practice depth due to few activities. |
| 7 | Immersion | 10/10 | <6 | 100% Ukrainian, excellent academic register. |
| 8 | Activities | 4/10 | <7 | **CRITICAL FAIL**: Only 4 activities found. Minimum 8 required for density. |
| 9 | Richness | 9/10 | <6 | Primary sources (Leo Deacon), decolonization notes, cultural context. |
| 10 | Beginner Safety | 10/10 | <7 | N/A for C1, but text is readable and well-paced. |
| 11 | LLM Fingerprint | 8/10 | <7 | Generally authentic voice, though some metaphor repetition ("тектонічні"). |
| 12 | Linguistic Accuracy | 9/10 | <9 | No grammar errors found; historical terminology accurate. |

**Weighted Overall:** (9×1.5 + 9×1.0 + 10×1.0 + 9×1.2 + 8×1.1 + 7×1.2 + 10×0.8 + 4×1.3 + 9×0.9 + 10×0.8 + 8×1.1 + 9×1.5 + 10×1.5 + 9×1.2) / 16.1 = 127.6 / 16.1 = **7.92/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: **FAIL** (Only 4 activities, min 8)
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Insufficient Activity Density
- **Location**: `activities/kniaz-sviatoslav.yaml`
- **Original**: 4 activities (`reading`, `essay-response`, `comparative-study`, `true-false`)
- **Problem**: C1 modules require high engagement density (8+ activities) to ensure retention of complex material. 4 is half the requirement.
- **Fix**: Add 4 more activities: 
  1. **Lexical Match**: Match archaic terms (пардус, моноксил) with definitions.
  2. **Chronology**: Order the events of Sviatoslav's campaigns.
  3. **Text Analysis**: "Fill in the gaps" (Cloze) using the Leo Deacon quote.
  4. **Open Question**: Reflection on "Мертві сорому не мають".

### Issue 2: Anachronistic Terminology
- **Location**: Section "Східний похід та крах Хазарії", paragraph 1
- **Original**: «Хозарський каганат на той час був більше, ніж державою — це була торговельна **суперкорпорація**...»
- **Problem**: The term "суперкорпорація" is a modern business neologism that breaks the historical immersion of a C1 biography.
- **Fix**: Change to «торговельна імперія» or «торговельний гігант».

### Issue 3: Anachronistic Terminology
- **Location**: Section "Балканська мрія", paragraph 1
- **Original**: «Святослав прийняв золото не як найманець, а як **інвестор** власного геополітичного проекту.»
- **Problem**: "Інвестор" and "проект" are too modern/corporate for the narrative voice established (Senior Biographer).
- **Fix**: «Святослав прийняв золото не як найманець, а як будівничий власної держави...»

### Issue 4: Repetitive Metaphors (LLM Fingerprint)
- **Location**: Section "Вступ" and Section "Підсумок"
- **Original**: «...маркує фундаментальний, **тектонічний зсув**...» (Intro) / «...зрушив **тектонічні плити** історії...» (Outro)
- **Problem**: Repetitive use of "tectonic" metaphor marks AI writing style.
- **Fix**: In Outro, change to «...змінив хід історії...» or «...перекроїв карту Європи...».

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| ~140 | «суперкорпорація» | «імперія / потуга» | Stylistic (Anachronism) |
| ~220 | «інвестор» | «будівничий / творець» | Stylistic (Anachronism) |
| ~460 | «тектонічні плити» | «хід / плин» | Stylistic (Repetition) |

## Strengths
- **Decolonization**: Excellent deconstruction of the "Sviatoslav as Russian prince" myth via the Leo Deacon visual description (oseleselets).
- **Narrative Arc**: The "Warrior on the Throne" vs "Architect (Olga)" contrast is a brilliant pedagogical anchor.
- **Immersion**: The text feels passionate and "Ukrainian", avoiding the dry "textbook voice" common in AI outputs.

## Fix Plan to Reach 9/10

### Activities: 4/10 → 9/10
**What to fix:**
1. **Add Activity 5**: `match-up` (Vocabulary). Terms: пардус, моноксил, каганат, капище.
2. **Add Activity 6**: `order-events` (Chronology). Khazaria -> Viatychi -> Bulgaria -> Dorostol -> Death.
3. **Add Activity 7**: `cloze` (Text). Use the "Mertvi soromu ne maiut" speech.
4. **Add Activity 8**: `multiple-choice` (Analysis). Why did Sviatoslav refuse baptism? (Fear of druzhina's mockery).

### Language: 8/10 → 9/10
**What to fix:**
1. Replace "суперкорпорація" with "торговельна потуга".
2. Replace "інвестор" with "архітектор/творець".
3. Vary the "tectonic" metaphor in the conclusion.

**Expected score after fix:** 9.0/10

## Verification Summary

- Content lines read: ~500
- Activity items checked: 13 (1 reading + 1 essay + 1 comparison + 10 TF items)
- Ukrainian sentences verified: ~200
- IPA transcriptions checked: 10
- Issues found: 4 (1 Critical Structural, 2 Stylistic, 1 Repetitive)

## Verdict

**FAIL**

The content is excellent (Lecture Quality), but the module **fails technically** due to insufficient activity density (4 instead of 8+) and low vocabulary count (10 items). The stylistic anachronisms ("supercorporation") also need polishing to meet C1 academic standards.
