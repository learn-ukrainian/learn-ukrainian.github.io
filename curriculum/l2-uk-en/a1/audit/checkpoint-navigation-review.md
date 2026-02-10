# Рецензія: Checkpoint: Navigation

**Level:** A1 | **Module:** 20
**Overall Score:** 8.8/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [8/8 from plan used, but 'наліво' missing from vocabulary.yaml]
- Grammar scope: [clean]
- Objectives: [all covered]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Clear layout, strong "Gamer's Corner" cultural hook. |
| 2 | Coherence | 10/10 | <7 | Excellent flow from individual skills to integration. |
| 3 | Relevance | 10/10 | <7 | Navigation is high-utility content. |
| 4 | Educational | 9/10 | <7 | Strong reinforcement of previous skills. |
| 5 | Language | 8/10 | <8 | Minor euphony issues in activity options; "Дякую дуже" word order. |
| 6 | Pedagogy | 9/10 | <7 | Effective TTT approach. |
| 7 | Immersion | 10/10 | <6 | Uses Ukr headers and solutions correctly. |
| 8 | Activities | 7/10 | <7 | **CRITICAL**: Ambiguous distractors in Locative quiz (both 'у' and 'в' offered). |
| 9 | Richness | 9/10 | <6 | Good cultural tips (Stalker, Tipping). |
| 10 | Beginner Safety | 9/10 | <7 | 5/5 on Safety Test. |
| 11 | LLM Fingerprint | 9/10 | <7 | Feels handcrafted. |
| 12 | Linguistic Accuracy | 9/10 | <9 | Accurate grammar explanations. |

**Weighted Overall:** 8.8/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [Ambiguous options in Locative fill-ins]
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Ambiguous Activity Options
- **Location**: `activities/20-checkpoint-navigation.yaml` / Type: `fill-in` (Locative)
- **Original**: Items 7, 12 (and others) offer both `у` and `в` as options, but only one is the "correct" answer.
    - Item 7: `Ми ___ ресторані.` Answer: `у`. Options: `[у, на, в, біля]`.
    - Item 12: `Кава ___ чашці.` Answer: `у`. Options: `[у, на, в, біля]`.
- **Problem**: In both cases, `в` is actually the euphonically preferred option (after vowel `а` in `Кава`, after vowel `и` in `Ми`). Having `в` as a distractor when it's valid (or even better) forces the student to guess the "system's" preference rather than correct Ukrainian.
- **Fix**: Remove the valid/competing preposition from the distractors. Replace `в` with `до` or `біля` in the options list for these items.

### Issue 2: Unnatural Word Order
- **Location**: `activities/20-checkpoint-navigation.yaml` / Type: `quiz` (Real Dialogues Order)
- **Original**: `Дякую дуже за допомогу!`
- **Problem**: While not strictly impossible, `Дуже дякую за допомогу!` is the standard neutral word order. `Дякую дуже` sounds emphatic or poetic.
- **Fix**: Change to `Дуже дякую за допомогу!`

### Issue 3: Missing Vocabulary
- **Location**: `vocabulary/20-checkpoint-navigation.yaml`
- **Original**: Only `красивий`, `праворуч`, `направо`.
- **Problem**: Plan lists `наліво` as required vocabulary. It is used in the text but missing from the vocabulary file.
- **Fix**: Add `наліво` to the vocabulary file.

### Issue 4: Unexplained Morphology (Fleeting Vowel)
- **Location**: Content / Skill 3 Practice
- **Original**: `без + цукор → Без _` (Answer: `цукру`)
- **Problem**: The explicit pattern box for Skill 3 says `Masculine → -а/-у`. It does not explain that `цукор` drops the `о`. This is a "gotcha" for A1 students following the rules strictly (`цукору`?).
- **Fix**: Add a small note to the Pattern box or key triggers: `(Note: цукор → цукру)`.

## Fix Plan to Reach 9/10

### Activities: 7/10 → 9/10

**What to fix:**
1.  **File**: `activities/20-checkpoint-navigation.yaml`
2.  **Section**: `type: fill-in` (title: `Case Mastery - Locative`)
    *   **Item 7** (`Ми ___ ресторані`): Change options `[у, на, в, біля]` → `[у, на, до, біля]` (Remove `в`).
    *   **Item 9** (`Турист ___ центрі`): Change options `[у, на, в, біля]` → `[у, на, до, біля]` (Remove `в`).
    *   **Item 12** (`Кава ___ чашці`): Change options `[у, на, в, біля]` → `[у, на, до, біля]` (Remove `в`).
    *   *Note*: Ensure `у` remains the correct answer key, or switch to `в` if you prefer euphony, but removing the ambiguity is critical.
3.  **Section**: `type: quiz` (title: `Real Dialogues Order`)
    *   **Item 11**: Change text `Дякую дуже за допомогу!` → `Дуже дякую за допомогу!`

### Language: 8/10 → 9/10

**What to fix:**
1.  **File**: `20-checkpoint-navigation.md`
2.  **Section**: `Skill 3: Genitive Case`
    *   **Action**: In the "Key Triggers" or "The Pattern" box, add a line: `Note: Some words drop vowels (цукор → цукру).`
3.  **File**: `vocabulary/20-checkpoint-navigation.yaml`
    *   **Action**: Add item:
        ```yaml
        - lemma: наліво
          ipa: /nɑˈlʲiʋo/
          translation: to the left
          pos: adv
        ```

### Projected Overall After Fixes

```
(9x1.5 + 10x1.0 + 10x1.0 + 9x1.2 + 9x1.1 + 9x1.2 + 10x1.0 + 9x1.3 + 9x0.9 + 9x1.3 + 9x1.0 + 9x1.5) / 14.0 = 9.2/10
```

## Verification Summary

- Content lines read: 250+
- Activity items checked: 45
- Ukrainian sentences verified: 60+
- IPA transcriptions checked: 3
- Issues found: 4
- Naturalness score recommendation: 9/10

## Verdict

**FAIL**

The module is excellent in content and coherence, but the **ambiguous activity options** in the Locative section are a functional error that will confuse learners. Fixing the activity YAML and the minor word order/vocab issues will easily push this to a PASS (9.2/10).