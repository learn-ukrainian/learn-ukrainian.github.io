===REVIEW_START===
# Рецензія: At the Post Office and Bank

**Level:** A2 | **Module:** 10
**Overall Score:** 7.1/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [PASS]
- Sections: [all present]
- Vocabulary: [15/15 from plan used, 5 extra words found]
- Grammar scope: [clean]
- Objectives: [all covered]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Generally good flow, but interrupted by confusion. |
| 2 | Coherence | 6/10 | <7 | **FAIL**: Module contradicts itself on `лист` vs `листа`. |
| 3 | Relevance | 9/10 | <7 | Highly relevant service vocabulary. |
| 4 | Educational | 7/10 | <7 | Good content, marred by grammatical misinformation. |
| 5 | Language | 6/10 | <8 | **FAIL**: Linguistically false explanation for `лист` (called "animate"). |
| 6 | Pedagogy | 6/10 | <7 | **FAIL**: Inconsistent rules for A2 learners (Nom vs Gen object). |
| 7 | Immersion | 8/10 | <6 | Good use of Ukrainian headers and context. |
| 8 | Activities | 6/10 | <7 | **FAIL**: Broken instructions and contradictions. |
| 9 | Richness | 9/10 | <6 | Good variety of phrases. |
| 10 | Beginner Safety | 6/10 | <7 | **FAIL**: Frustration risk high due to conflicting answers. |
| 11 | LLM Fingerprint | 8/10 | <7 | Generally natural, one awkward unjumble sentence. |
| 12 | Linguistic Accuracy | 7/10 | <9 | **FAIL**: Incorrect grammatical labeling. |

**Weighted Overall:** 7.1/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: **FAIL** (Contradictory answers for `лист`, missing instruction criteria)
- Beginner safety: 3/5

## Critical Issues Found

### Issue 1: Linguistic Falsehood & Contradiction
- **Location**: `activities.yaml` / `error-correction` (Item 1) vs `cloze` (Item 1)
- **Original**: `explanation: Animate accusative for лист = листа.` vs `answer: лист` (in cloze)
- **Problem**: `Лист` (letter) is **inanimate**. Calling it "Animate Accusative" is grammatically incorrect and confusing. While `написати листа` (Genitive object) is a common variant, teaching it as a rule for "sending a letter" at A2 level — while simultaneously marking `лист` (the standard Inanimate Accusative form) as correct in another activity — creates chaos.
- **Fix**: Standardize on **`лист`** (Accusative = Nominative) for A2 simplicity. Remove the "Animate" explanation entirely.

### Issue 2: Broken Activity Instructions
- **Location**: `activities.yaml` / `mark-the-words` (Item "Find Case Forms")
- **Original**: `instruction: Клацніть на слова, що відповідають критерію.`
- **Problem**: The instruction refers to a "criterion" that is not defined. The title "Find Case Forms" is too vague (is Nominative a case form?). Users won't know what to click.
- **Fix**: Change instruction to: "Клацніть на слова, що стоять у непрямих відмінках (не в називному)." or "Find nouns in Accusative, Genitive, or Instrumental cases."

### Issue 3: Unnatural Phrasing
- **Location**: `activities.yaml` / `unjumble` (Item 7)
- **Original**: `answer: Я хочу обміняти долари на гривні сьогодні зараз`
- **Problem**: "Сьогодні зараз" (Today now) is redundant and unnatural.
- **Fix**: Remove "зараз" or "сьогодні".

### Issue 4: Vocabulary Bloat
- **Location**: `vocabulary.yaml`
- **Original**: `бюрократія`, `розвінчання`, `надаватися`
- **Problem**: These words appear in the vocabulary list but are not in the text, nor are they A2 level.
- **Fix**: Remove them.

## Fix Plan to Reach 9/10

### Language & Pedagogy: 6/10 → 9/10

**What to fix:**
1.  **File**: `10-at-the-post-office-and-bank.md`
    - Section "Practice / 1. Case Recognition": Change `Я хочу відправити листа.` -> `Я хочу відправити лист.` (Standard A2 Grammar).
2.  **File**: `activities.yaml`
    - Activity `error-correction`, Item 1:
        - Change `error: лист` -> `error: листі` (or another wrong case).
        - Change `answer: листа` -> `answer: лист`.
        - Change `explanation: Animate accusative...` -> `explanation: Direct object (inanimate) -> Accusative (same as Nominative).`
    - Activity `quiz`, Item 1:
        - Change Option 1 `Я хочу відправити листа.` -> `Я хочу відправити лист.`
        - Change Option 2 `Я хочу відправити лист.` -> `Я хочу відправити листа.` (and mark false if strictly enforcing, or better: use a clearly wrong case like `листом` as the distractor to avoid valid-variant confusion).
    - Activity `translate`, Item 1:
        - Change `Я хочу відправити листа.` -> `Я хочу відправити лист.`

**Expected score after fix:** 9/10

### Activities: 6/10 → 9/10

**What to fix:**
1.  **File**: `activities.yaml`
    - Activity `mark-the-words`: Update `instruction` to: `Знайдіть іменники у знахідному, родовому або орудному відмінках.` (Find nouns in Accusative, Genitive, or Instrumental). Ensure the answer list matches this logic exactly.
    - Activity `unjumble`, Item 7: Remove `зараз` from words list and answer.
    - Activity `cloze`, Item 1: Ensure options and answer align with the `лист` decision above.

**Expected score after fix:** 9/10

### Vocabulary: Clean-up

**What to fix:**
1.  **File**: `vocabulary.yaml`
    - Remove entries: `бюрократія`, `розвінчання`, `надаватися`, `вважати`, `довідка`.

## Verdict

**FAIL**

The module fails due to a critical pedagogical contradiction regarding the word `лист` (teaching it as animate/genitive in one place and inanimate/nominative in another) and a linguistically false explanation. Activity instructions are also incomplete. Immediate fixes required.

===REVIEW_END===
