# Рецензія: Checkpoint: First Contact

**Level:** A1 | **Module:** 10
**Overall Score:** 5.7/10
**Status:** FAIL
**Reviewed:** 2026-02-18

## Plan Verification

```
Plan-Content Alignment: PASS
- Sections: PASS (All 5 skills + Integration present)
- Vocabulary: PASS (All required words present)
- Grammar scope: PASS (Strictly reviews A1.1 material)
- Objectives: PASS (Matches plan)
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 4/10 | <7 | Module is completely inaccessible to A1.1 students due to language barrier. |
| 2 | Coherence | 8/10 | <7 | Logical flow is excellent, even if readable only by intermediates. |
| 3 | Relevance | 5/10 | <7 | Fails the primary goal of a "Check-up" if instructions can't be understood. |
| 4 | Educational | 5/10 | <7 | Explanations are linguistically accurate but pedagogically misplaced (in Ukrainian). |
| 5 | Language | 10/10 | <8 | The Ukrainian text itself is natural and error-free. |
| 6 | Pedagogy | 3/10 | <7 | Explaining A1 grammar rules *in Ukrainian* is a critical pedagogical failure. |
| 7 | Immersion | 1/10 | <6 | 86% Immersion vs 20-40% target. Complete violation of Tier 1 constraints. |
| 8 | Activities | 9/10 | <7 | Activities use English prompts and are well-designed. One typo found. |
| 9 | Richness | 8/10 | <6 | Excellent cultural hooks (Kulchytsky, Lviv coffee). |
| 10 | Beginner Safety | 2/10 | <7 | "Would I Continue?" Score: 1/5. Student will feel completely overwhelmed. |
| 11 | LLM Fingerprint | 8/10 | <7 | Generally natural tone, though some "AI Tutor" persona genericness. |
| 12 | Linguistic Accuracy | 9/10 | <9 | High accuracy, minor pragmatic issue with "Навзаєм". |

**Weighted Overall:** 5.7/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [TYPO FOUND]
- Beginner safety: 1/5

## Critical Issues Found

### Issue 1: Immersion Violation (BLOCKER)
- **Location**: Entire Content File
- **Original**: «Ми не будемо вчити нові граматичні правила. Ми повторимо все вивчене.» (and all other explanatory text)
- **Problem**: The instructional text is written entirely in Ukrainian (86% immersion). An A1.1 student at Module 10 *cannot* read complex sentences about grammar ("візуальне впізнавання", "біологія перемагає граматику"). This violates the Tier 1 requirement for "Clear, simple explanations in English".
- **Fix**: Rewrite all explanatory text (Overview, Skill Introductions, Models, Tips) into English. Keep only the examples and specific target phrases in Ukrainian.

### Issue 2: Activity Typo
- **Location**: `activities/checkpoint-first-contact.yaml`, `fill-in` ("Second Conjugation (-ити)"), Item 7 option
- **Original**: `['роблю', 'робиш', 'роббить', 'робимо']`
- **Problem**: Typo in the distractor «роббить» (double 'б').
- **Fix**: Change to `робить`.

### Issue 3: Pragmatic Competence
- **Location**: Skill 5: Замовлення їжі
- **Original**: «Офіціант скаже: «Смачного!»... Ваша відповідь: «Дякую!». Або «Навзаєм!» (Likewise!).»
- **Problem**: Replying "Likewise" (`Навзаєм`) to a waiter wishing you "Bon appétit" is socially awkward/incorrect (unless the waiter is also eating).
- **Fix**: Remove «Або «Навзаєм!»». Just leave «Дякую!».

### Issue 4: Pedagogical Gap (Mnemonic)
- **Location**: Skill 3: Дієвідміна
- **Original**: «У першій групі форма "вони" має -ють. Або -уть. ... Асоціація: Юля читає.»
- **Problem**: The mnemonic "Юля" only covers the `-ють` ending (Ю). It does not help with verbs like `писати` -> `пишуть` (-уть), leaving half the conjugation group unsupported by the memory aid.
- **Fix**: Add a second association or clarify that "Юля" helps identify the *soft* variant, while the hard variant matches too. Or simply remove the "Association" if it's incomplete, to avoid confusion.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| N/A | «Навзаєм» (to waiter) | (remove) | Pragmatic |

## Beginner Safety Audit

"Would I Continue?" Test: 1/5
- Overwhelmed? **Fail** (Cannot read instructions)
- Instructions clear? **Fail** (In unknown language)
- Quick wins? **Pass** (Activities are doable)
- Ukrainian scary? **Fail** (Wall of text)
- Come back tomorrow? **Fail** (Discouraging barrier)

## Strengths
- **Cultural Context**: The connection of Lviv coffee culture to Yuriy Kulchytsky is brilliant and memorable.
- **Activity Design**: The activities in the YAML are well-structured, varied, and correctly use English for prompts, making them the only accessible part of the module.
- **Tone**: The underlying persona ("Friendly Hostel Host") is great, once translated.

## Fix Plan to Reach 9/10

### Immersion: 1/10 → 10/10
**What to fix:**
1. **Global Rewrite**: Translate all H2 descriptions, "Model" sections, "Practice" instructions, and "Tip/Warning" contents into English.
   - Example: Change «Деякі літери підступні. Вони схожі на англійські...» → "Some letters are tricky. They look like English letters but sound different..."
2. **Retain Ukrainian**: Keep headers (e.g., "Skill 1: Читання кирилиці"), example lists, and the "Integration Task" dialog.

### Activities: 9/10 → 10/10
**What to fix:**
1. `activities/checkpoint-first-contact.yaml`: Correct `роббить` to `робить`.

### Linguistic Accuracy: 9/10 → 10/10
**What to fix:**
1. Remove the suggestion to say "Навзаєм" to a waiter.

### Projected Overall After Fixes
```
Overall = (9×1.5 + 10×1.0 + 10×1.0 + 10×1.2 + 10×1.1 + 10×1.2 + 10×1.0 + 10×1.3 + 9×0.9 + 10×1.3 + 9×1.0 + 10×1.5) / 16.1 = 9.8/10
```

## Verification Summary

- Content lines read: 215
- Activity items checked: 55
- Ukrainian sentences verified: ~40 (examples)
- IPA transcriptions checked: 28
- Issues found: 4

## Verdict

**FAIL**

The module fails primarily on **Immersion** and **Beginner Safety**. Providing A1.1 instructions and grammar explanations entirely in Ukrainian (86% immersion) creates an insurmountable barrier for beginners. The content must be translated to English to be usable. Minor issues in activities (typo) and pragmatics (waiter response) also need fixing.
