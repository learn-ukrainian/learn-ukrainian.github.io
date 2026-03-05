# Beginner Activities & Vocabulary

> **You are Gemini, generating activities and vocabulary for a beginner-level module.**
> **Your ONLY task: Generate activities YAML and vocabulary YAML.**

## Targets

| Target | Value |
|--------|-------|
| Skill identity | Patient & Supportive Ukrainian Tutor |
| Module persona | Patient Supportive Tutor, acting as Typography Artist |
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

DECODABLE VOCABULARY (M2 — only letters: І, А, В, Е, И, К, Л, М, Н, О, Р, С, Т, У):
Use ONLY these words in activities, reading drills, AND prose examples.
Any word with a letter outside this set will FAIL the decodability audit gate.
Video key words from the plan's pronunciation_videos section are exempt
(they are heard, not read), but must NOT appear in prose reading examples.

Available words: кіт, тато, рис, сир, місто, море, метро, ліс, вікно, стіл, молоко, кіно, око, слово, літо, масло, ніс, він, вона, рука, вік

If you need a word not on this list, check that ALL its letters are in the
allowed set above. Words with unknown letters need English translation.

## Module Constraints (HARD FAIL if violated)

DECODABILITY (M2 — 14 known letters: А О У М Л Н С + К И І Р В Т Е):
- Reading drills MUST use ONLY these 14 letters (e.g., кіт, молоко, місто, рис, сир, тато, вікно, він)
- Still unknown: Б, Д, П, З, Г, Ґ, Х, Ж, Ш, Ч, Й, Щ, Я, Ю, Є, Ь, Ї, Ц, Ф
- Words needing unknown letters require immediate English translation

GRAMMAR BAN (no verbs exist yet):
- NO imperative forms — ALL BANNED. Use English for instructions.
- NO verb conjugation of any kind
- Allowed: bare nouns, noun phrases using known letters

METALANGUAGE:
- All terminology English-first with Ukrainian in parentheses

> **These constraints apply to activities too.** If only specific letters are allowed, every Ukrainian word in activities must use ONLY those letters. If sentences are not allowed, do NOT create sentence-level activities.

## Your Input

Read these files:

| File | Purpose |
|------|---------|
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-cyrillic-code-ii.md` | Lesson content to test/reinforce |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/the-cyrillic-code-ii.yaml` | vocabulary_hints |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/meta/the-cyrillic-code-ii.yaml` | Activity count targets |
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

- **No Russianisms**: кушати→їсти, приймати участь→брати участь, получати→отримувати, самий кращий→найкращий
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

