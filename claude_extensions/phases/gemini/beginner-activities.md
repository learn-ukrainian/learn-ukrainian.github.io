# Beginner Activities & Vocabulary

> **You are Gemini, generating activities and vocabulary for a beginner-level module.**
> **Your ONLY task: Generate activities YAML and vocabulary YAML.**

## Targets

| Target | Value |
|--------|-------|
| Skill identity | {SKILL_IDENTITY} |
| Module persona | {PERSONA_VOICE}, acting as {PERSONA_ROLE} |
| Activities required | {ACTIVITY_MIN}–{ACTIVITY_MAX} |
| Required types | {REQUIRED_TYPES} |
| Vocabulary items | {VOCAB_COUNT_TARGET} |

### Item Minimums Per Activity Type

{ITEM_MINIMUMS_TABLE}

{DECODABLE_VOCABULARY}

## Module Constraints (HARD FAIL if violated)

{PEDAGOGICAL_CONSTRAINTS}

> **These constraints apply to activities too.** If only specific letters are allowed, every Ukrainian word in activities must use ONLY those letters. If sentences are not allowed, do NOT create sentence-level activities.

## Your Input

Read these files:

| File | Purpose |
|------|---------|
| `{CONTENT_PATH}` | Lesson content to test/reinforce |
| `{PLAN_PATH}` | vocabulary_hints |
| `{META_PATH}` | Activity count targets |
| `{SCHEMA_PATH}` | Allowed fields per activity type |
| `docs/ACTIVITY-YAML-REFERENCE.md` | Activity reference guide |

---

## Beginner Activity Rules

### Language in Activities

- **Questions, explanations, instructions** → English (scaffolding language)
- **Target content being practiced** → Ukrainian (letters, words, phrases)
- **Option text** → Ukrainian when selecting Ukrainian words/letters, English when selecting concepts

### Activity Types by Constraint Level

**If constraints say "letters/syllables only" (no sentences):**
Use: `quiz`, `match-up`, `group-sort`, `anagram`, `true-false`
Do NOT use: `fill-in`, `unjumble`, `cloze`, `error-correction`, `translate`

**If constraints allow words and simple phrases:**
Add: `fill-in`, `match-up` with phrases
Still avoid: `cloze` (needs 14+ blanks), `error-correction`, `unjumble`

**If constraints allow basic sentences:**
Add: `unjumble`, `fill-in` with sentences, `translate`
Still avoid: `cloze` (needs 14+ blanks)

### Do NOT Use Grammar Terminology

A1/A2 learners do NOT know terms like іменник (noun), дієслово (verb), голосний (vowel), відмінок (case). Write questions in plain English.

❌ "Яка частина мови позначає дію?" (meaningless to A1)
✅ "Which letter looks like English H but sounds like N?" (clear)

---

## Schema Reference

### quiz (English questions, Ukrainian options)

```yaml
- type: quiz
  title: "Check Your Knowledge"
  instruction: Choose the correct answer.
  items:  # minItems: 6
    - question: "Which letter looks like English H but represents the /n/ sound?"
      explanation: "Н is a visual trap — it looks like H but sounds like N."
      options:
        - text: "Н"
          correct: true
        - text: "М"
          correct: false
        - text: "С"
          correct: false
        - text: "Л"
          correct: false
    - question: "What does the word сума mean?"
      explanation: "Сума means sum/amount in Ukrainian."
      options:
        - text: "sum/amount"
          correct: true
        - text: "bag"
          correct: false
        - text: "moon"
          correct: false
        - text: "mom"
          correct: false
```

Key: `explanation` at QUESTION level (not inside options), exactly 4 options, exactly 1 `correct: true`.

### anagram (letter scramble — M1-M10)

```yaml
- type: anagram
  title: "Unscramble the Word"
  instruction: "Rearrange the letters to form the correct Ukrainian word."
  items:  # minItems: 8
    - scrambled: "А М А М"    # SPACE-SEPARATED letters
      answer: "МАМА"
    - scrambled: "а н у л"
      answer: "луна"
```

**CRITICAL**: Letters MUST be space-separated. `scrambled` and `answer` must have exactly the same letters.

### match-up

```yaml
- type: match-up
  title: "Match Letter to Sound"
  pairs:  # minItems: 6 — MUST use "pairs:" not "items:"
    - left: "Н"
      right: "/n/ sound"
    - left: "М"
      right: "/m/ sound"
```

### fill-in (MUST include `options` array)

```yaml
- type: fill-in
  title: "Complete the Sentence"
  items:  # minItems: 6
    - sentence: "Мама купує ___."
      answer: "молоко"
      options: ["молоко", "молока", "молоку", "молоком"]  # REQUIRED: exactly 4 options, answer MUST be in the list
    - sentence: "Я бачу ___."
      answer: "кота"
      options: ["кіт", "кота", "коту", "котом"]
```

❌ WRONG: fill-in without `options` — every item MUST have `options` (exactly 4 strings)
❌ WRONG: `answer` not in `options` — the answer MUST appear verbatim in the options array

### group-sort

```yaml
- type: group-sort
  title: "Sort the Letters"
  groups:  # 2-4 groups
    - name: "True Friends (same look, same sound)"
      items: ["А", "М"]
    - name: "Visual Traps (different sound)"
      items: ["Н", "С"]
```

### true-false

```yaml
- type: true-false
  title: "True or False?"
  items:  # minItems: 8
    - statement: "The Ukrainian letter Н makes the same sound as English H."
      correct: false
      explanation: "Н looks like H but sounds like N — it's a visual trap."
```

---

## Activity Quality Rules

1. **Every Ukrainian word must be from the decodable vocabulary.** Do NOT use words with letters the student hasn't learned.
2. **Plausible, clear items.** Every question must have one unambiguous correct answer.
3. **No sentence-level activities** if constraints say letters/syllables only.
4. **Prefer fewer, high-quality activities** over padding. 6 good activities > 8 activities where the last 2 are filler.

## Mandatory Self-Check

1. **QUIZ single correct** — every quiz item has exactly 1 `correct: true`
2. **ANAGRAM letter match** — scrambled letters = same letters as answer (same count, same chars)
3. **MATCH-UP unique pairs** — no duplicate left or right values
4. **Schema compliance** — only fields from `{SCHEMA_PATH}`, no extras

## Allowed Activity Types

**ALLOWED (use ONLY these):** {ALLOWED_ACTIVITY_TYPES}

**FORBIDDEN (audit will auto-FAIL):** {FORBIDDEN_ACTIVITY_TYPES}

{SHARED_ACTIVITY_RULES}
