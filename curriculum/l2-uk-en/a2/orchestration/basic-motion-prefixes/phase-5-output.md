===REVIEW_START===
# Рецензія: Basic Motion Prefixes

**Level:** A2 | **Module:** 36
**Overall Score:** 8.4/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [PASS] All sections present (Introduction, Presentation, Practice, Dialogues).
- Vocabulary: [FAIL] Massive mismatch. 10+ words in YAML not found in content (e.g., брама, вбудовуватися, вмитися, змокнути).
- Grammar scope: [PASS] Mostly clean, though `з-` prefix introduced as a necessity for "surface" exit.
- Objectives: [PASS] Covered.
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Good flow, engaging intro ("Grammatical GPS"). |
| 2 | Coherence | 7/10 | <7 | Vocabulary list is completely disconnected from the text. |
| 3 | Relevance | 9/10 | <7 | Highly relevant for A2 (Metro, commmute). |
| 4 | Educational | 9/10 | <7 | Clear explanations of "The Cube" vs "The Plane". |
| 5 | Language | 8/10 | <8 | Minor style issues (`включити`) and dialogue naturalness (`в'їжджаю на станцію`). |
| 6 | Pedagogy | 9/10 | <7 | Strong scaffolding (Prefix -> Preposition -> Aspect). |
| 7 | Immersion | 9/10 | <6 | Good usage of Ukrainian cultural context (Kyiv Metro). |
| 8 | Activities | 8/10 | <7 | Some errors in translation keys and questionable distractors. |
| 9 | Richness | 8/10 | <6 | Good examples, but vocabulary list is "ghost data". |
| 10 | Beginner Safety | 9/10 | <7 | Clear instructions, not overwhelming. 5/5 on Safety Test. |
| 11 | LLM Fingerprint | 8/10 | <7 | Vocabulary list feels hallucinated/generic. |
| 12 | Linguistic Accuracy | 8/10 | <9 | "Spilled" translation error; `Включити` vs `Увімкнути`. |

**Weighted Overall:** 8.39/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN] (Note: `включити` is borderline but acceptable colloquially; preferred `увімкнути`).
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: [FAIL] See Critical Issues (Translate item 10, Cloze item 5).
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Ghost Vocabulary
- **Location**: `vocabulary/36-basic-motion-prefixes.yaml`
- **Original**: Includes `брама`, `вбудовуватися`, `вмитися`, `відтінковий`, `змокнути`, `королівський`, `передбачувано`, `проникнення`, `сільський`.
- **Problem**: None of these words appear in the module content or activities. This confuses the learner (why learn words not used?) and breaks the "Content-Driven" philosophy.
- **Fix**: Delete all unused items from the YAML. Ensure `бариста` is actually used (it is not in the text either).

### Issue 2: Translation Error (Semantic)
- **Location**: Activity `translate`, Item 10
- **Original**: "He spilled the milk..." -> Option `Він вилив молоко` marked `correct: true`.
- **Problem**: "Spilled" implies accidental action (`розлив`). "Вилив" implies intentional pouring out (`poured out`). Marking `вилив` as correct for "spilled" is misleading.
- **Fix**: Mark `Він вилив молоко` as `correct: false`. Ensure `Він розлив молоко` is the only correct option for "spilled".

### Issue 3: Stylistic Standard (Surzhyk avoidance)
- **Location**: Activity `match-up`, Pair 9
- **Original**: `left: Включити світло`, `right: Виключити світло`
- **Problem**: While common, `включити/виключити` is often considered non-standard/Russianism for appliances. Standard is `увімкнути/вимкнути`.
- **Fix**: Change to `left: Увімкнути світло`, `right: Вимкнути світло`. Or replace with `Впустити/Випустити` (Let in/Let out) to keep "Motion" theme better.

### Issue 4: Dialogue Naturalness
- **Location**: Section "Dialogues", Elena's last line
- **Original**: "В'їжджаю на нашу станцію!"
- **Problem**: A passenger inside a metro train does not say "I am driving onto the station".
- **Fix**: Change to "Ми під'їжджаємо до станції!" (We are approaching the station) or "Поїзд в'їжджає на станцію!" (The train is entering...).

### Issue 5: Cloze Logic (Preposition/Prefix mismatch)
- **Location**: Activity `cloze`, Gap 5
- **Original**: "автобус [{ви|в|за|під}:5]їхав зі зупинки"
- **Problem**: A bus leaving a stop is `від'їхав від зупинки`. `Виїхав зі зупинки` implies the stop is an enclosure.
- **Fix**: Change context to a bus depot/station (`автостанції`), or accept `від` as an option/answer if the focus is strictly exiting a space. Given the options, `ви` is the "least wrong" but unnatural. Better: "автобус ... з парковки" (matches `виїхав`).

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Act `match-up` | Включити світло | Увімкнути світло | Stylistic |
| Dial 6 | В'їжджаю на нашу станцію | Під'їжджаю до нашої станції | Naturalness |
| Act `translate` | Він вилив молоко (for "spilled") | Він розлив молоко | Accuracy |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? No
- Instructions clear? Yes
- Quick wins? Yes (Simple logic of In/Out)
- Ukrainian scary? No, logical.
- Come back tomorrow? Yes.

## Fix Plan to Reach 9/10

### Coherence: 7/10 → 10/10
**What to fix:**
1. **Vocabulary YAML**: Delete `бариста`, `брама`, `вбудовуватися`, `вмитися`, `відтінковий`, `змокнути`, `королівський`, `передбачувано`, `проникнення`, `сільський`.
2. **Vocabulary YAML**: Add words that ARE in the text but missing from vocab: `навігатор`, `траєкторія`, `парковка`, `гараж`.

### Activities: 8/10 → 9/10
**What to fix:**
1. **Match-up**: Replace `Включити/Виключити` with `Увімкнути/Вимкнути` OR `Впустити/Випустити`.
2. **Translate**: Item 10, set `Він вилив молоко` to `correct: false`.
3. **Cloze**: Gap 5, change `зі зупинки` to `з парковки` (to make `виїхав` natural) OR change gap answer to `від` (if `від-` prefix is allowed). Recommendation: Change text to `з парковки`.

### Linguistic Accuracy: 8/10 → 9/10
**What to fix:**
1. **Dialogue**: Change "В'їжджаю на нашу станцію" to "Ми під'їжджаємо до станції".

### Projected Overall After Fixes
(9 + 10 + 9 + 9 + 9 + 9 + 9 + 9 + 9 + 9 + 9 + 9) / 14 ≈ **9.1/10**

## Verdict

**FAIL**

The content is generally high quality and engaging, but the **vocabulary list is hallucinated** (contains 10+ unused words) and there are **specific accuracy errors** in the activities (spilled vs poured out) and dialogue naturalness. These must be fixed to pass the high-quality bar.

===REVIEW_END===
