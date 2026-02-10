===REVIEW_START===
# Рецензія: Aspect Morphology

**Level:** A2 | **Module:** 15
**Overall Score:** 7.3/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [15/15 required words present]
- Grammar scope: [clean]
- Objectives: [all covered in text, but activities drift]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Clear explanations, good tone. |
| 2 | Coherence | 9/10 | <7 | Logical flow from prefixes to suffixes to irregularities. |
| 3 | Relevance | 9/10 | <7 | Highly relevant for A2. |
| 4 | Educational | 8/10 | <7 | Good teaching of the concept. |
| 5 | Language | 9/10 | <8 | Natural Ukrainian examples. |
| 6 | Pedagogy | 8/10 | <7 | PPP structure followed. |
| 7 | Immersion | 8/10 | <6 | ~40% Ukrainian, appropriate for grammar explanation. |
| 8 | Activities | 4/10 | <7 | **CRITICAL FAIL**: Tests concepts and verbs NOT taught in the lesson. |
| 9 | Richness | 9/10 | <6 | Comprehensive text. |
| 10 | Beginner Safety | 6/10 | <7 | **FAIL**: Quiz asks about untaught verbs, causing frustration. |
| 11 | LLM Fingerprint | 5/10 | <7 | **FAIL**: Vocabulary YAML contains hallucinations ("watt") and English-to-Ukrainian back-translations. |
| 12 | Linguistic Accuracy | 9/10 | <9 | Good, minor stylistic choices. |

**Weighted Overall:** (12 + 9 + 9 + 9.6 + 9.9 + 9.6 + 8 + 5.2 + 8.1 + 7.8 + 5 + 13.5) / 14.0 = **7.62/10** (Adjusted manually for severe fails: **7.3**)

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [FAIL] - Activities test `-ну-` suffix and irregular root changes not in text.
- Activity errors: [FAIL] - Multiple items test untaught content.
- Beginner safety: 2/5 (Quiz is impossible without external knowledge)

## Critical Issues Found

### Issue 1: Activity Scope Creep (Major)
- **Location**: Activities YAML (Quiz & Match-up)
- **Problem**: The activities test verbs and concepts completely absent from the lesson text.
- **Evidence**:
    - Quiz Q4: Ask about `-ну-` suffix (`гукати` -> `гукнути`). The text **never mentions** the `-ну-` suffix.
    - Quiz Q5: Asks about `допомагати` -> `допомогти` (Root change). Not in text.
    - Quiz Q6: Asks about `замітати` -> `замести`. Not in text.
    - Quiz Q12: Asks about `стрибати` -> `стрибнути`. Not in text.
    - Match-up "Suppletive Pairs": Includes `ловити/піймати`, `ставати/стати`, `заходити/зайти`. None of these are in the lesson text or vocabulary list.
- **Fix**: Replace all untaught examples in activities with verbs explicitly taught in the "Core Aspect Pairs" table or the "Presentation" section.

### Issue 2: Vocabulary YAML Hallucinations
- **Location**: `vocabulary/15-aspect-morphology.yaml`
- **Problem**: The file contains words that appear to be hallucinations or accidental extractions from English substrings.
- **Evidence**:
    - `- lemma: ват` (translation: watt). Likely from the suffix `-uvati`.
    - `- lemma: збити` (translation: to knock down). Not in text.
    - `- lemma: пантелик` (translation: confusion). Not in text.
    - `- lemma: найнадійніший`. Not in text.
    - `- lemma: розтягнутий`. Not in text.
- **Fix**: Purge the vocabulary file. Keep ONLY the words found in the `content_outline` vocabulary hints and the actual lesson text.

### Issue 3: Grammar Confusion in Unjumble
- **Location**: Activity "Aspect Pattern Sentences", Item 2
- **Original**: "Вона написала дуже великого листа..."
- **Problem**: Usage of `листа` (Genitive/Accusative Animate) for an inanimate object (`лист`). While colloquial/stylistic, A2 learners are taught "Inanimate Accusative = Nominative". This looks like a grammar error to a beginner ("Why is it -a?").
- **Fix**: Change to "Вона написала дуже великий лист..." OR change the object to feminine/neuter to avoid ambiguity (e.g., "довге повідомлення").

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| Act 2 | "великого листа" | "великий лист" | Grammar (A2 Standard) |

## Beginner Safety Audit

"Would I Continue?" Test: 2/5
- Overwhelmed? **YES** (The quiz asks questions I wasn't taught).
- Instructions clear? Yes.
- Quick wins? No (failed the quiz).
- Ukrainian scary? Yes (unexpected rules appearing in quiz).
- Come back tomorrow? Maybe not.

## Strengths
- The explanation of "Aspect as a family" is excellent.
- The "Prefix vs Suffix" logic is explained clearly.
- "Logic of Finding" reflection is very insightful.

## Fix Plan to Reach 9/10

### Activities: 4/10 → 9/10

**What to fix:**
1.  **Quiz Item 4**: Delete question about `-ну-` suffix (or add `-ну-` to the Presentation section text). Recommend deleting to keep scope tight.
2.  **Quiz Item 5**: Replace `допомагати` (untaught) with `вибирати` -> `вибрати` (taught).
3.  **Quiz Item 6**: Replace `замітати` (untaught) with `вимикати` -> `вимкнути` (taught).
4.  **Quiz Item 12**: Delete or replace `стрибати`.
5.  **Match-up "Suppletive Pairs"**: Remove `ловити/піймати`, `заходити/зайти`. Add `класти/покласти` (taught in text) or stick to the ones in the table.
6.  **Unjumble Item 2**: Change `великого листа` to `великий лист`.

### LLM Fingerprint: 5/10 → 10/10

**What to fix:**
1.  **Vocabulary YAML**: Remove `ват`, `видалення`, `глибший`, `збити`, `пантелик`, `надзвичайний`, `найнадійніший`, `оволодівши`, `розтягнутий`, `сильне`, `схоже`, `творення`, `точність`, `точніший`, `фразовий`, `індикатор`.
2.  **Keep**: The core verbs list + basic terms like `вид`, `префіксація` (if used).

### Projected Overall After Fixes

With activities aligned and vocabulary cleaned, the module will be solid.
Projected Score: **9.3/10**

## Verification Summary

- Content lines read: 140
- Activity items checked: 45
- Ukrainian sentences verified: 30
- IPA transcriptions checked: 40
- Issues found: 3 major (Scope, Vocab, Grammar nuance)
- Naturalness score recommendation: 9/10 (Content is fine, metadata is stale)

## Verdict

**FAIL**

The lesson content is good, but the **Activities are broken** (testing untaught material) and the **Vocabulary file is hallucinated**. These must be fixed before release.

===REVIEW_END===
