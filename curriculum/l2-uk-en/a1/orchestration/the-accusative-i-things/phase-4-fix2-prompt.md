# Phase 4: Audit Fixes (Attempt 2)

> **You are Gemini (Yellow Team), fixing a module that failed audit.**
> **Your Goal:** Fix grammar violations and boost immersion.

## Audit Failures

### 1. A1 Grammar Violations (Critical)
The audit found complex grammar not allowed in A1.
**Task:** Edit `curriculum/l2-uk-en/a1/the-accusative-i-things.md` to SIMPLIFY these sentences.
- **Instrumental Case**: `з продавцем` -> Forbidden. Use Nominative or simple "and" (і).
  - *Example Fix*: "Я розмовляю з продавцем" -> "Я і продавець говоримо."
- **Subordinate Clauses**: `що`, `якщо` -> Forbidden. Split into two simple sentences.
  - *Example Fix*: "Я бачу, що це стіл" -> "Це стіл. Я бачу це." or "Я бачу стіл."
  - *Example Fix*: "Якщо я хочу..." -> "Я хочу... Тоді..."
- **Dative/Locative**: Check for words ending in `-і` used as indirect objects. Simplify.

### 2. Immersion Too Low (17.2% < 25%)
**Task:** Rewrite MORE English text into **Simple Ukrainian**.
- Target: 35% Ukrainian words.
- Translate:
  - "Now let's practice" -> "Тепер практика."
  - "Look at the table" -> "Дивіться на таблицю."
  - "This is important" -> "Це важливо."
- **Constraint**: Keep sentences Short (max 10 words). SVO structure only.

### 3. Metalanguage
**Task:** Add these terms to `curriculum/l2-uk-en/a1/vocabulary/the-accusative-i-things.yaml`:
- чоловічий рід (masculine gender)
- жіночий рід (feminine gender)
- середній рід (neuter gender)
- відмінок (case)
- іменник (noun)

## Execution
You have WRITE ACCESS.
1. Read the files `curriculum/l2-uk-en/a1/the-accusative-i-things.md` and `curriculum/l2-uk-en/a1/vocabulary/the-accusative-i-things.yaml`.
2. Apply the fixes.
3. Verify your changes.
