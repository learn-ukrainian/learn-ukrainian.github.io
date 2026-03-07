# Beginner Activities & Vocabulary

> **You are Gemini, generating activities and vocabulary for a beginner-level module.**
> **Your ONLY task: Generate activities YAML and vocabulary YAML.**

## Targets

| Target | Value |
|--------|-------|
| Skill identity | Patient & Supportive Ukrainian Tutor |
| Module persona | Patient Supportive Tutor, acting as Logistics Expert |
| Activities required | 8–15 |
| Required types |  |
| Vocabulary items | 20 |

### Item Minimums Per Activity Type

| Type | Minimum |
|------|--------|
| quiz | ≥8 items |
| true-false | ≥8 items |
| fill-in | ≥8 items |
| match-up | ≥8 pairs |
| anagram | ≥8 items |
| unjumble | ≥6 items |
| group-sort | ≥8 items |
| watch-and-repeat | ≥1 items |
| classify | ≥1 items |
| image-to-letter | ≥5 items |

**CRITICAL — HARD FAIL if violated:** Each activity MUST meet the minimum item count for its type. Activities with fewer items than the minimum will cause an automatic validation failure. Check the minimums table above BEFORE submitting.



## Module Constraints (HARD FAIL if violated)

SEQUENCE CONSTRAINTS (M15+ — Verbs & Beyond):
Present tense verbs start at M15. Past tense at M36. Future at M37.

KEY RESTRICTION: Imperative forms (Слухайте!, Читайте!, Пишіть!) are NOT taught until M47 (imperative-and-requests). Before M47, use indirect requests or English for instructions.

BANNED IMPERATIVE FORMS (non-exhaustive): Запам'ятайте, Уявіть, Порівняйте, Зверніть увагу, Спробуйте, Подивіться, Послухайте, Прочитайте, Повторіть, Напишіть, Скажіть, Виберіть, Подивімось, Поговорімо, Повторімо, Давайте розглянемо, Розглянемо.

INSTEAD OF → USE:
- Запам'ятайте → "Remember that..." (English)
- Порівняйте → "Compare..." (English)
- Зверніть увагу → "Notice that..." (English)
- Подивіться → "Look at..." (English)
- Спробуйте → "Try to..." (English)
- Прочитайте → "Read..." (English)
- Повторіть → "Repeat..." (English)

The standard A1 LEVEL_CONSTRAINTS (no dative, no instrumental, imperfective only) apply in addition to this constraint.

> **These constraints apply to activities too.** If only specific letters are allowed, every Ukrainian word in activities must use ONLY those letters. If sentences are not allowed, do NOT create sentence-level activities.

## Your Input

Read these files:

| File | Purpose |
|------|---------|
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-accusative-i-things.md` | Lesson content to test/reinforce |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/the-accusative-i-things.yaml` | vocabulary_hints |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/meta/the-accusative-i-things.yaml` | Activity count targets |
| `schemas/activities-a1.schema.json` | Allowed fields per activity type |
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

### unjumble (sentence word reordering — ONLY when sentences allowed)

```yaml
- type: unjumble
  title: "Put the Words in Order"
  instruction: "Arrange the words to form a correct Ukrainian sentence."
  items:  # minItems: 8
    - words: ["книга", "Це", "нова"]
      answer: "Це нова книга"
    - words: ["великий", "дім", "Це"]
      answer: "Це великий дім"
```

**CRITICAL**: Use `words` (array of strings) + `answer` (string). Do NOT use `sentence`, `jumbled`, or `scrambled` fields — those are WRONG and will fail schema validation.

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
4. **Schema compliance** — only fields from `schemas/activities-a1.schema.json`, no extras

## Allowed Activity Types

**ALLOWED (use ONLY these):** quiz, true-false, fill-in, match-up, anagram, unjumble, group-sort, watch-and-repeat, classify, image-to-letter

**FORBIDDEN (audit will auto-FAIL):** cloze, error-correction, mark-the-words, select, translate, essay-response, critical-analysis, comparative-study, authorial-intent

## YAML Formatting Rules (HARD FAIL if violated)

**Do NOT use Ukrainian angular quotes `«»` in YAML values.** They break YAML parsing when combined with colons.

```yaml
❌ WRONG (guillemets + colon = YAML parse error):
  title: «Знайдіть пару: термін та його значення»
  explanation: Термін «доконати» означає: завершити дію.

✅ RIGHT (plain strings, quote with single quotes if value contains colon):
  title: 'Знайдіть пару: термін та його значення'
  explanation: Термін доконати означає завершити дію.
```

**Rules:**
1. **Never use `«»` in YAML** — use plain text or single/double quotes
2. **Quote any value containing `:`** with single quotes: `'text: with colon'`
3. **Double-check** every `title`, `question`, `sentence`, `explanation`, and `text` field

## Language Quality (applies to ALL Ukrainian text in activities)

- **No Russianisms**: кушати→їсти, приймати участь→брати участь, получати→отримувати, самий кращий→найкращий, красивий→гарний, красива→гарна, прекрасний→чудовий, відноситися→стосуватися, слідуючий→наступний
- **No Russian characters**: ы, э, ё, ъ must NEVER appear
- **No IPA**: NEVER include IPA symbols or `ipa` fields
- **No Latin transliteration**: Reference Ukrainian words in Cyrillic, not Latin (ZhYty → Жити)

## Vocabulary YAML Rules

1. **Object with `items:` wrapper** — NOT a bare list
2. **Follow plan's vocabulary_hints** — include all required items
3. **Each entry needs**: `lemma` (NOT `term`), `translation`, `pos`
4. **Optional fields**: `gender` (for nouns: m/f/n), `aspect` (for verbs), `notes`, `usage`, `example`
5. **NO `ipa` field**
6. **Count target**: 20 items

## Output Delimiters

> **Content outside delimiters is automatically discarded by the extraction pipeline.**

Activities block (BARE LIST — no wrapper):
```
===ACTIVITIES_START===
- type: quiz
  title: "..."
  items:
    ...
===ACTIVITIES_END===
```

Vocabulary block (OBJECT with `items:` wrapper):
```
===VOCABULARY_START===
items:
  - lemma: "слово"
    translation: "word"
    pos: "noun"
===VOCABULARY_END===
```

## Friction Report (MANDATORY)

```
===FRICTION_START===
**Phase**: Phase 3: Activities + Vocabulary
**Step**: {what you were doing when friction occurred, or "Full YAML generation"}
**Friction Type**: NONE | YAML_SCHEMA_VIOLATION | TOKEN_LIMIT_TRUNCATION | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

## Boundaries

- Do NOT modify lesson content — only generate activities and vocabulary
- Do NOT add fields not in the schema (check schema carefully!)
- Do NOT wrap in `activities:` or `vocabulary:` dictionary keys
- Do NOT request skills or delegate to Claude

