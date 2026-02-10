# Рецензія: Describing Things - Adjectives

**Level:** A1 | **Module:** 26
**Overall Score:** 7.5/10
**Status:** FAIL
**Reviewed:** 2026-02-09

## Plan Verification

```
Plan-Content Alignment: [FAIL]
- Sections: [Mismatch: "Questions Який/Яка" are in Presentation, Plan asked for Warm-up]
- Vocabulary: [PASS: Required words present]
- Grammar scope: [PASS]
- Objectives: [PASS]
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 8/10 | <7 | Content flow is good, but activities will frustrate users. |
| 2 | Coherence | 9/10 | <7 | Explanations are clear and logical. |
| 3 | Relevance | 9/10 | <7 | High-frequency adjectives used in text. |
| 4 | Educational | 6/10 | <7 | **FAIL**: Activities test vocabulary NOT taught in the lesson. |
| 5 | Language | 9/10 | <8 | Ukrainian is natural and grammatically correct. |
| 6 | Pedagogy | 6/10 | <7 | **FAIL**: Testing untaught material (Ghost Vocabulary). |
| 7 | Immersion | 8/10 | <6 | Good examples and dialogues. |
| 8 | Activities | 5/10 | <7 | **FAIL**: ~50% of items use unknown vocabulary. |
| 9 | Richness | 8/10 | <6 | Good examples, culture bite, and myth buster. |
| 10 | Beginner Safety | 6/10 | <7 | **FAIL**: User will fail activities due to unknown words. |
| 11 | LLM Fingerprint | 9/10 | <7 | Doesn't feel overly robotic. |
| 12 | Linguistic Accuracy | 9/10 | <9 | No major errors found. |

**Weighted Overall:** 7.5/10

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: [CLEAN]
- Activity errors: **[FAIL]** (Massive vocabulary scope violation)
- Beginner safety: 2/5 (Activities are unfair)

## Critical Issues Found

### Issue 1: Ghost Vocabulary in Activities
- **Location**: `activities/26-describing-things-adjectives.yaml` (Multiple types: match-up, fill-in, quiz)
- **Problem**: The activities require knowledge of at least 16 adjectives **never mentioned** in the module content or vocabulary list.
- **Words Found Only in Activities**:
    - `повільний` (slow)
    - `легкий` (easy/light)
    - `важкий` (hard/heavy)
    - `довгий` (long)
    - `короткий` (short)
    - `широкий` (wide)
    - `вузький` (narrow)
    - `високий` (tall/high)
    - `низький` (low)
    - `слабкий` (weak)
    - `нудний` (boring)
    - `важливий` (important)
    - `простий` (simple)
    - `перший` (first)
    - `хороший` (good)
    - `чорний` (black)
- **Impact**: A beginner will fail these activities and feel stupid. This violates "Beginner Safety".
- **Fix**: Remove these items or replace them with known vocabulary (`великий`, `малий`, `новий`, `старий`, `гарний`, `поганий`, `добрий`, `злий`, `цікавий`, `синій`, `білий`, `коричневий` from the text).

### Issue 2: Plan Misalignment (Section)
- **Location**: `plans/a1/26-describing-things-adjectives.yaml` vs `26-describing-things-adjectives.md`
- **Original**: Plan asks for "Питання Який? Яка? Яке?" in **Warm-up**.
- **Current**: It is in **Presentation** subsection "Asking 'Which one?'".
- **Fix**: Acceptable deviation for flow, but worth noting. The activities issue is the blocker.

### Issue 3: Potential Confusion (Dog Gender)
- **Location**: Presentation > Describing People
- **Original**: "У неї є великий собака. Собака дуже швидкий..."
- **Problem**: `Собака` ending in `-а` looks feminine to a beginner who just learned `-а` = feminine. While correct (masculine), it might confuse.
- **Fix**: Consider swapping to `пес` (masc) or adding a tiny note that `собака` is masculine despite the ending. Or just leave it as an "exposure" moment.

## Beginner Safety Audit

"Would I Continue?" Test: 2/5
- Overwhelmed? **Yes** (during activities)
- Instructions clear? Yes
- Quick wins? Yes (reading text) -> No (failing quiz)
- Ukrainian scary? Yes (unexpected words)
- Come back tomorrow? No

## Fix Plan to Reach 9/10

### Educational & Pedagogy: 6/10 → 9/10
**What to fix:**
1.  **Activity Refactor**: Rewrite `activities/26-describing-things-adjectives.yaml` to strictly use ONLY vocabulary introduced in the module or previous modules.
    - **Antonym Pairs**: Remove `легкий/важкий`, `довгий/короткий`, `широкий/вузький`, `високий/низький`. Keep only `великий/малий`, `новий/старий`, `добрий/поганий`, `дорогий/дешевий`. Add `білий/чорний` ONLY if colors are known (Module 27 is next, so maybe not). Stick to the 5 pairs taught.
    - **Adjective Categories**: Remove `високий`, `низький`, `швидкий`, `повільний`, `легкий`, `важкий`. Use `великий`, `малий`, `новий`, `старий`, `цікавий`, `гарний`.
    - **Fill-in**: Replace sentences requiring `високий`, `повільний`, `чорний`, `короткий`, `смачне`, `перша`, `хороша` with sentences using `гарний`, `великий`, `синій`, `білий`, `старий`.
    - **Quiz**: Ensure all options and questions use known words. Remove `нудна`, `важливе`, `просте`, `вузька`, `широка`.

### Activities: 5/10 → 9/10
**What to fix:**
1.  See above. The activities must be 100% solvable based on the text provided.

### Projected Overall After Fixes
(8+9+9+9+9+9+8+9+8+9+9+9)/12 ≈ **8.75/10** (rounding up to 9 if executed perfectly)

## Verdict

**FAIL**

The module content is solid, but the **activities are broken** because they test a massive amount of vocabulary that was never taught. This is a critical pedagogical failure that will discourage learners. The activities must be rewritten to match the content scope.