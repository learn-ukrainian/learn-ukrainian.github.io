===REVIEW_START===
# Рецензія: The Dative II — Nouns

**Level:** A2 | **Module:** 02
**Overall Score:** 7.5/10
**Status:** FAIL
**Reviewed:** February 9, 2026

## Plan Verification

```
Plan-Content Alignment: [FAIL]
- Sections: [PASS] All outline sections present.
- Vocabulary: [FAIL] Required words 'личить', 'підходити', 'бракувати', 'вистачати' are MISSING from the content text but 'личить' appears in the Quiz.
- Grammar scope: [FAIL] 'ім'я' -> 'імені' (irregular) is tested in Activities but the text explicitly says Neuter nouns take -у/-ю without exception. Passive participle 'доставлена' in Cloze is out of scope.
- Objectives: [PASS] Main objectives covered, though specific verbs are missing.
```

## Scores

| # | Dimension | Score | Auto-fail | Evidence |
|---|-----------|-------|-----------|----------|
| 1 | Experience Quality | 7/10 | <7 | Good explanations, but frustration when quizzed on untaught words (`личить`). |
| 2 | Coherence | 7/10 | <7 | Contradiction: Text says "Neuter takes -у/-ю", Activity marks "імені" as correct without explanation in text. |
| 3 | Relevance | 9/10 | <7 | Content is highly relevant. |
| 4 | Educational | 6/10 | <7 | **FAIL**: Testing untaught concepts (`личить`, `імені`) violates scaffolding rules. |
| 5 | Language | 9/10 | <8 | Ukrainian examples are natural and correct. |
| 6 | Pedagogy | 6/10 | <7 | **FAIL**: Missed required vocabulary from Plan (`личить`, `підходити`) which are core Dative functions. |
| 7 | Immersion | 8/10 | <6 | Good mix, clear distinctions. |
| 8 | Activities | 6/10 | <7 | **FAIL**: Cloze contains `доставлена` (passive participle) and `сподобається` (perfective future) - too advanced for A2.02. |
| 9 | Richness | 8/10 | <6 | Good cultural notes. |
| 10 | Beginner Safety | 6/10 | <7 | **FAIL**: User will feel tricked by the Quiz items on `ім'я` and `личить`. |
| 11 | LLM Fingerprint | 9/10 | <7 | Voice is reasonably human. |
| 12 | Linguistic Accuracy | 9/10 | <9 | No grammar errors in the *text* itself. |

**Weighted Overall:** (10.5 + 7 + 9 + 7.2 + 9.9 + 7.2 + 8 + 7.8 + 7.2 + 7.8 + 9 + 13.5) / 14.0 = **7.44/10**

## Auto-Fail Checklist Results

- Russianisms: [CLEAN]
- Calques: [CLEAN]
- Grammar scope: **FAIL** (`доставлена` - passive participle in Cloze; `імені` - irregular declension not taught; `сподобається` - perfective future).
- Activity errors: **FAIL** (Quiz Q12 and True/False Q12 test concepts not in the text).
- Beginner safety: 3/5 (Frustration triggers found in quiz).

## Critical Issues Found

### Issue 1: Missing Required Vocabulary
- **Location**: Section "Verbs Taking Dative Objects"
- **Original**: Only lists `допомагати`, `телефонувати`, `дарувати`, `пояснювати`.
- **Problem**: Plan explicitly requires `личить` (to suit) and `підходити`. These are tested in the activities (`Quiz Q12`) but never taught.
- **Fix**: Add a row to the verb table or a small subsection "Expressing 'It suits you'" explaining `личить` + Dative.

### Issue 2: Untaught Irregular Grammar (Trap)
- **Location**: Section "Neuter and Plural Dative" vs Activity `True-False Q12` & `Quiz Q12`
- **Original Text**: "Neuter nouns follow the masculine casual pattern: they take -у or -ю."
- **Activity Item**: "Neuter nouns ending in -я like «ім'я» have regular dative forms. -> False: These nouns are irregular: ім'я → імені."
- **Problem**: The student was explicitly told Neuter nouns take -у/-ю. They have no way of knowing `ім'я` is an exception unless the text says so.
- **Fix**: Add a `> [!note] Exception` in the Neuter section mentions that `ім'я` becomes `імені` in the Dative.

### Issue 3: Vocabulary Duplication
- **Location**: `vocabulary/02-the-dative-ii-nouns.yaml`
- **Original**: `lemma: Петро` AND `lemma: петро`
- **Problem**: Duplicate entry.
- **Fix**: Remove the lowercase `petro`.

### Issue 4: Advanced Grammar in Cloze
- **Location**: `activities/02-the-dative-ii-nouns.yaml` (Cloze "Complete the Dialogue")
- **Original**: "Посилка буде {готова|там|доставлена} за тиждень."
- **Problem**: `доставлена` is a passive participle (B1/B2 grammar).
- **Fix**: Replace `доставлена` with `готова` (adjective, A1/A2).

## Beginner Safety Audit

"Would I Continue?" Test: 3/5
- Overwhelmed? No.
- Instructions clear? Yes.
- Quick wins? Yes, until the quiz.
- Ukrainian scary? No.
- Come back tomorrow? Maybe, but I'd be annoyed that I failed the quiz because the lesson didn't teach the words.

## Fix Plan to Reach 9/10

### Pedagogy & Educational: 6/10 → 9/10

**What to fix:**
1.  **Section "Verbs Taking Dative Objects"**: Add `личить` to the table.
    *   Row: `личить | to suit (look good) | Цей колір тобі личить`
2.  **Section "Neuter and Plural Dative"**: Add a note about the irregular noun `ім'я`.
    *   Add: `> [!note] **Exception: Name**\nThe noun **ім'я** (name) is irregular. In the Dative case, it becomes **імені**. \nExample: *Це пасує твоєму імені.* (This suits your name.)`
3.  **Activities File**: Fix the Cloze items.
    *   Change `{сподобається|подобається|личить}` to `{сподобається|подобається|личить}` -> ensure `сподобається` is replaced with `сподобається` only if Future Perfective is known? Actually, `Книга сподобається` is fine as a lexical chunk, but maybe `Книга точно сподобається` makes it clearer? Or just use `підійде`. Let's stick to `сподобається` but ensure the student knows it.
    *   **BETTER FIX**: Just change `доставлена` to `там` as the correct answer or `готова`.

### Vocabulary: Clean up
1.  **File `vocabulary/02-the-dative-ii-nouns.yaml`**: Delete the duplicate `petro` entry.

### Projected Overall After Fixes
With these fixes, Plan Alignment passes, Educational becomes 9/10, Beginner Safety 9/10.
**Projected Score: ~9.2/10**

## Verdict

**FAIL**

The module fails mainly because it tests vocabulary (`личить`) and grammar exceptions (`імені`) that are not taught in the text, and misses required vocabulary from the Plan. Simple additions to the text will resolve this.

===REVIEW_END===
