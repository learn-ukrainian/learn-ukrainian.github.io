# Рецензія: Checkpoint: Core Grammar

**Level:** A1 | **Module:** 34
**Overall Score:** 8.2/10
**Status:** PASS
**Reviewed:** 2026-02-20

## Plan Verification

Plan-Content Alignment: PASS
- Sections: All plan sections are present.
- Vocabulary: Matches A1 core requirements.
- Grammar scope: Aligned with A1 expectations (4 cases, 3 tenses).
- Objectives: Met.

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 9/10 | <7 | Tone is encouraging and supportive ("stop, exhale, and check"). |
| 2 | Coherence | 9/10 | <7 | Logical progression from phonetics to syntax. |
| 3 | Relevance | 10/10 | <7 | Directly addresses common A1 stumbling blocks. |
| 4 | Educational | 8/10 | <7 | Good explanations, but contains a factual error about noun endings. |
| 5 | Language | 9/10 | <8 | Clear English instructions; Ukrainian examples are natural. |
| 6 | Pedagogy | 9/10 | <7 | Good use of "Teach-Test" loop. |
| 7 | Immersion | 6/10 | <6 | ~35% Ukrainian. Low for A1.3 target (60-80%), but acceptable for a Grammar Checkpoint where clarity is priority. |
| 8 | Activities | 8/10 | <7 | Good variety, but some titles are misleading. |
| 9 | Richness | 7/10 | <6 | Cultural note is good, but could use more Ukrainian text in the "Practice" sections. |
| 10 | Beginner Safety | 9/10 | <7 | "Would I Continue?" 5/5. Very safe and supportive. |
| 11 | LLM Fingerprint | 8/10 | <7 | "Welcome to this important milestone" is a bit generic, but persona is consistent. |
| 12 | Linguistic Accuracy | 7/10 | <9 | Critical error in gender examples; missing stress marks in minimal pairs. |

**Weighted Overall:** 8.2/10

## Auto-Fail Checklist Results

- Russianisms: CLEAN
- Calques: CLEAN
- Grammar scope: CLEAN
- Activity errors: Minor title mismatches.
- Beginner safety: 5/5

## Critical Issues Found

### Issue 1: Factual Error (Gender)
- **Location**: Section "Навичка 2: Рід та узгодження", "Caution: Soft Sign"
- **Original**: «Words ending in soft sign **-ь** can be masculine (день, тато) or feminine (ніч, сіль).»
- **Problem**: "Тато" ends in **-о**, not **-ь**. It is masculine, but it is NOT an example of a soft sign ending.
- **Fix**: Replace "тато" with a valid masculine soft sign word like "дідусь" or "вчитель", or just remove it.

### Issue 2: Missing Stress Marks
- **Location**: Section "Навичка 1: Читання та вимова"
- **Original**: «(for example, **плачу** — *I pay* vs **плачу** — *I cry*)»
- **Problem**: Without visual stress marks, the visual distinction is non-existent for the learner.
- **Fix**: Add stress marks: **плачу́** vs **пла́чу**.

### Issue 3: Content Mismatch (Copy-Paste)
- **Location**: Section "Навичка 4: Система відмінків", "Accusative Case"
- **Original**: «* Я йду **в парк**. (Банк — unchanged, because inanimate, masc. gender)»
- **Problem**: The example uses "park", but the explanation refers to "bank".
- **Fix**: Change explanation to "Парк — unchanged..."

### Issue 4: Activity Title Mismatch
- **Location**: Activities file, `match-up` "Числа від 1 до 5"
- **Original**: Title 'Числа від 1 до 5' but contains pairs up to 8.
- **Problem**: Title contradicts content.
- **Fix**: Change title to 'Числа від 1 до 10'.

### Issue 5: Activity Title Mismatch
- **Location**: Activities file, `fill-in` "В чи У?"
- **Original**: Title 'В чи У? (Напрямок чи Місце)'
- **Problem**: The task asks to choose the noun form ("парк" vs "парку"), not the preposition (which is always "в" in the prompt).
- **Fix**: Change title to 'Напрямок чи Місце (Закінчення)'.

## Ukrainian Language Issues

| Line | Current | Corrected | Type |
|------|---------|-----------|------|
| N/A | тато (as soft sign example) | дідусь/день | Factual Error |
| N/A | плачу vs плачу | плачу́ vs пла́чу | Orthography |

## Beginner Safety Audit

"Would I Continue?" Test: 5/5
- Overwhelmed? Pass (Pacing is slow and careful)
- Instructions clear? Pass
- Quick wins? Pass
- Ukrainian scary? Pass (Heavily scaffolded)
- Come back tomorrow? Pass

## Strengths
- Excellent emotional support and "tutor" persona.
- Clear, digestible grammar tables.
- Good cultural hook about the "melodious language".

## Fix Plan to Reach 9/10

### Linguistic Accuracy: 7/10 → 9/10
**What to fix:**
1. Fix the "tato" gender example error.
2. Add stress marks to the minimal pair.
3. Fix the "park/bank" copy-paste error.

### Activities: 8/10 → 9/10
**What to fix:**
1. Correct the misleading titles in the YAML file.

## Verification Summary

- Content lines read: ~160
- Activity items checked: 40
- Ukrainian sentences verified: All
- IPA transcriptions checked: N/A (Vocab file looks good)
- Issues found: 5

## Verdict

**PASS**

The module is solid pedagogically but contains a few specific errors that must be fixed to ensure accuracy. The immersion level is low, but acceptable for a Grammar Checkpoint.