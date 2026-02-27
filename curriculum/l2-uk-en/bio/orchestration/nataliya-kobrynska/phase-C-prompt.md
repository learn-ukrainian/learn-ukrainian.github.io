# Phase 3: Activities & Vocabulary Generation

> **You are Gemini, executing Phase 3 of an orchestrated rebuild.**
> **Your ONLY task: Generate activities YAML and vocabulary YAML.**

## Pre-flight Checklist

Before writing ANY YAML, confirm these targets:

| Target | Value |
|--------|-------|
| Skill identity | Professor of Ukrainian Arts (biography) |
| Module persona | Senior Biographer, acting as Feminist Pioneer |
| Activities required | 3–9 |
| Items per activity | ≥1 |
| Required types | reading, essay-response, critical-analysis |
| Priority types | reading, essay-response, critical-analysis, comparative-study, authorial-intent, quiz |
| Vocabulary items | 30 |

Keep this table visible as you write. Every activity and vocab item must serve these targets.

## Your Input

Read these files from disk:

**Lesson content** (generate activities that test/reinforce this content):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/bio/nataliya-kobrynska.md
```

**Plan file** (vocabulary_hints — vocabulary list to follow):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/bio/nataliya-kobrynska.yaml
```

**Meta file** (activity count targets, pedagogy):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/bio/meta/nataliya-kobrynska.yaml
```

**Activity schema** (CRITICAL — defines allowed fields per activity type):
```
schemas/activities-bio.schema.json
```

**Activity reference guide**:
```
docs/ACTIVITY-YAML-REFERENCE.md
```

## Downstream Audit Gates (your activities will be checked for)

These are the top failure causes from previous rebuilds — write with them in mind:
- **Schema violations**: `additionalProperties: false` means ANY unlisted field = instant fail. Read `schemas/activities-bio.schema.json` before writing.
- **Item counts**: `true-false` often requires 12 items, `quiz` requires 8+. Check `minItems` in schema.
- **Forbidden fields**: `id` only on `reading` type (seminar tracks). Reading activities REQUIRE `text` (inline source) + `tasks` (comprehension questions). `instruction` is optional.
- **Russian characters**: ы, э, ё, ъ in any activity text = hard fail
- **Ukrainian quotes**: do NOT use «» in YAML values — they break parsing with colons
- **No IPA**: NEVER include IPA symbols or `ipa` fields

---

## Your Task

Generate two YAML blocks: activities and vocabulary.

### Activities YAML Rules

1. **BARE LIST at root** — no `activities:` wrapper, no `module:` or `level:` headers
2. **Schema compliance** — only use fields defined in the schema. `additionalProperties: false` means unlisted fields cause audit failure.
3. **Seminar style** (bio): Reading Input → Analytical Output. Focus on comprehension, analysis, and critical thinking — NOT drill exercises.
4. **Activity count**: 5 activities (4-9 for seminar tracks)
5. **Type variety**: Use at least 3 different activity types
6. **Only `reading` type has `id` field** in seminar tracks — do NOT add `id` to other types
7. **`essay-response` rubric fields**: `criteria` / `description` / `points` (NOT `criterion` / `weight`)
8. **`mark-the-words` format**: Use `text` (no asterisks) + `answers` array

### CRITICAL: Activity Type Constraints for bio

**ALLOWED types (use ONLY these):** reading, essay-response, critical-analysis, comparative-study, authorial-intent, quiz, true-false

**FORBIDDEN types (audit will auto-FAIL if you use these):** match-up, fill-in, cloze, group-sort, unjumble, anagram, mark-the-words

Using a forbidden type wastes the entire activity generation phase. Check the allowed list BEFORE writing each activity.

### Correct Quiz Schema (REFERENCE — read this FIRST)

**This is the EXACT correct quiz structure. Anchor to this pattern before reading mistakes below.**

```yaml
- type: quiz
  title: "Перевірте знання"
  items:  # minItems: 8, question ≥5 words
    - question: "Яка частина мови позначає дію або стан предмета?"  # ≥5 words!
      explanation: "Дієслово позначає дію або стан."  # HERE at question level
      options:  # exactly 4
        - text: "дієслово"
          correct: true
        - text: "іменник"
          correct: false
        - text: "прикметник"
          correct: false
        - text: "прислівник"
          correct: false
```

**Key rules**: `explanation` at QUESTION level (not inside options), `question` ≥5 words, exactly 4 options, exactly 1 `correct: true`.

### Correct Reading Schema (REFERENCE)

**Reading schema varies by track — always check `schemas/activities-bio.schema.json` for your track's required fields.**

**Seminar tracks (ISTORIOHRAFIIA, BIO, LIT, HIST):** Reading = passive input linked to analytical activities.
```yaml
- type: reading
  id: reading-hrushevsky          # REQUIRED for seminar tracks (for source_reading links)
  title: "Первинне джерело: Звичайна схема історії"
  source: "Михайло Грушевський (1904)"
  text: |                          # REQUIRED — the actual passage
    Головним і єдиним рушієм усієї світової історії є не амбітні
    королі чи владні гетьмани, а саме широкі народні маси...
```

**Core tracks (A1, A2, B1, B2, C1):** Reading = standalone with comprehension questions.
```yaml
- type: reading
  title: "Первинне джерело"
  text: |                          # REQUIRED
    Actual passage text here...
  tasks:                           # REQUIRED for core tracks
    - "Comprehension question 1?"
    - "Comprehension question 2?"
```

**WRONG — missing `text` (the #1 reading failure):**
```yaml
# ❌ FAILS AUDIT — no text field
- type: reading
  title: "Первинне джерело"
  source: "Грушевський"
  instruction: "Прочитайте уривок."
```

### Common Schema Mistakes (FIX BEFORE OUTPUT)

**These mistakes caused audit failures in previous rebuilds. Check EVERY activity against these rules:**

1. **Quiz `explanation` placement** — `explanation` goes at the QUESTION level, NOT inside an option. WRONG:
```yaml
options:
  - text: "відповідь"
    correct: true
    explanation: "Пояснення"  # WRONG — explanation is not a valid option field
```
CORRECT:
```yaml
explanation: "Пояснення чому ця відповідь правильна"
options:
  - text: "відповідь"
    correct: true
```

2. **Quiz question text length** — Every `question` field must be ≥5 words. WRONG: "Слово «хто» — це..." (3 words). RIGHT: "До якої частини мови належить слово «хто»?" (8 words). Short questions fail the pedagogy gate.

3. **No extra fields** — The schema uses `additionalProperties: false`. ANY field not in the schema causes instant failure. Common mistakes: adding `id` to non-reading activities, adding `hint` where not allowed, adding `explanation` inside option objects.

4. **Vocabulary YAML structure** — Use object with `items:` array wrapper. Each entry uses `lemma` (NOT `term`), `translation`, `pos`. Optional: `gender` (m/f/n for nouns), `aspect` (for verbs), `notes`, `usage`, `example`. Do NOT use bare list for vocabulary. Do NOT include `ipa` fields.

### Activity Quality Standards (MANDATORY)

**These rules prevent low-quality activities that waste learner time:**

1. **Activities test LANGUAGE, not content** — The Golden Rule: Can the learner answer this question WITHOUT reading the Ukrainian text? If YES → it tests content recall, not language. **REWRITE IT.** FORBIDDEN patterns: "У якому році..." (dates), "Хто був..." (names), "Скільки..." (numbers), "Що символізує..." (interpretation without text reference). REQUIRED patterns: "Згідно з текстом, як автор...", "У тексті модуля автор характеризує...", "Яку функцію автор підкреслює...", "Який аргумент автор наводить...". Applies to ALL quiz/reading/essay activities in HIST, BIO, ISTORIOHRAFIIA, LIT, and content-heavy modules. If a quiz question is answerable from general knowledge alone, you have FAILED the activity.

2. **Production over recognition** — At least 2 activities must require the learner to PRODUCE language, not just recognize it. Production types: `translate` (with free text, not multiple choice), `fill-in`, `unjumble`, `error-correction`, `cloze`. Recognition types: `quiz`, `true-false`, `select`, `match-up`, `group-sort`. A module with only recognition activities fails review.

2. **Plausible example sentences** — Every sentence in every activity must be something a real Ukrainian speaker might actually say, write, or encounter. FORBIDDEN: philosophical/motivational statements ("Граматика — це музика мови"), meta-sentences about learning ("Ми спостерігаємо за тривалістю лінгвістичного експерименту"), or artificially constructed sentences that exist only to contain target vocabulary. GOOD: everyday speech, textbook excerpts, teacher instructions, realistic dialogues.

3. **Unjumble quality** — Unjumble sentences must test grammar knowledge (word order rules, case agreement, verb placement). FORBIDDEN: reassembling motivational quotes or poetic metaphors. Each unjumble sentence should have exactly one correct grammatical order.

4. **mark-the-words minimum** — `mark-the-words` activities must have at least 3 separate text passages (sentences or short paragraphs). One sentence with 6 targets is too thin for meaningful practice.

5. **Error-correction precision** — Each item must have exactly one clear error with one correct fix. The error must be a plausible learner mistake (wrong case, wrong aspect, Russianism), not an obviously absurd mistake nobody would make.

6. **Group-sort accuracy** — Every item must belong unambiguously to exactly one group. Do NOT include category labels (like "непрямий" meaning "indirect cases") as items — only include concrete instances.

7. **Item count consistency** — Activities of the same type should have similar item counts (±2). Don't have one quiz with 4 items and another with 12.

### YAML Formatting Rules (HARD FAIL if violated)

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
3. **In example sentences**, use plain quotes or omit decorative quotes entirely
4. **Double-check** every `title`, `question`, `sentence`, `explanation`, and `text` field

### Language Quality (applies to ALL Ukrainian text in activities)

- **Typography in CONTENT files**: use Ukrainian angular quotes «...» — but **NOT in YAML** (see above)
- **No Russianisms**: кушати→їсти, приймати участь→брати участь, получати→отримувати, самий кращий→найкращий
- **No Russian characters**: ы, э, ё, ъ must NEVER appear

### Pronunciation in Activity Explanations (HARD FAIL)

**In YAML explanations, use the Ukrainian word directly — NEVER Latin transliteration.**

YAML explanations should reference Ukrainian words in Cyrillic.

```yaml
❌ WRONG (Latin transliteration):
  explanation: 'ZhYty uses the hard И sound.'
  explanation: 'Dity uses the soft І sound.'
  explanation: 'The first vowel in Kyiv is hard И (Ky-yiv).'

❌ WRONG (non-Cyrillic in YAML):
  explanation: 'Жити [ˈʒɪ.tɪ] uses the hard И sound.'

✅ RIGHT (Ukrainian word directly):
  explanation: 'Жити uses the hard И sound.'
  explanation: 'Діти uses the soft І sound.'
  explanation: 'The first vowel in Київ is the hard И.'
```

**Rules:**
1. Reference words in Cyrillic, not Latin transliteration (ZhYty → Жити)
2. Keep explanations simple and readable — use Cyrillic only
3. English descriptions of sounds are fine ("hard И", "soft І", "the ch sound")

### Vocabulary YAML Rules

1. **Object with `items:` wrapper** — NOT a bare list. Required structure: `items:` array
2. **Follow plan's vocabulary_hints** — include all required items, optionally include recommended
3. **Each entry needs**: `lemma` (NOT `term`), `translation`, `pos` (part of speech)
4. **Optional fields**: `gender` (for nouns: m/f/n), `aspect` (for verbs), `notes`, `usage`, `example`
5. **NO `ipa` field** — Do NOT include an `ipa` field in vocabulary YAML.
6. **Count target**: 30 items

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

Return TWO YAML blocks with clear delimiters:

### Correct YAML Examples (COPY THESE STRUCTURES EXACTLY)

**These are the EXACT field structures from the schema. Using wrong fields = instant audit failure.**

#### unjumble (CRITICAL — #1 schema failure in previous rebuilds)

```yaml
- type: unjumble
  title: "Складіть речення"
  items:  # minItems: 6
    - words: ["мова", "українська", "красива"]  # Array of strings, NOT a single string
      answer: "Українська мова красива"          # The correct sentence as one string
    - words: ["граматику", "ми", "вивчаємо"]
      answer: "Ми вивчаємо граматику"
```

❌ WRONG: `jumbled: "мова українська красива"` (string field does NOT exist in schema)
❌ WRONG: `sentence: "..."` (field does NOT exist)
✅ ONLY: `words` (array of strings) + `answer` (string)

#### anagram (CRITICAL — scrambled MUST be space-separated)

```yaml
- type: anagram
  title: "Розшифруйте слова"
  instruction: "Rearrange the letters to form the correct Ukrainian word."
  items:  # minItems: 8
    - scrambled: "О М Т Е Р"    # SPACE-SEPARATED letters — NOT concatenated!
      answer: "МЕТРО"
    - scrambled: "а й ч"         # Lowercase is fine too
      answer: "чай"
    - scrambled: "к у б л о я"
      answer: "яблуко"
```

❌ WRONG: `scrambled: "ОМТЕР"` (concatenated — React component splits on spaces, this produces 1 "letter")
❌ WRONG: `scrambled: "ОМТЕР"` with 5 letters but answer "МЕТР" with 4 (letter count mismatch)
✅ MUST: Every letter in `scrambled` separated by a space
✅ MUST: Scrambled letters are EXACTLY the same letters as the answer (same count, same characters)
✅ NOTE: A1 M01-M10 use anagram (letter scramble), A1 M11+ use unjumble (sentence reorder)

#### group-sort

```yaml
- type: group-sort
  title: "Розподіліть за групами"
  groups:  # minItems: 2, practical max: 4-5
    - name: "Іменники"
      items: ["книга", "стіл", "місто"]
    - name: "Дієслова"
      items: ["читати", "писати", "бігти"]
```

❌ WRONG: `items:` at root level — use `groups:` array with `name` + `items`
❌ WRONG: 6+ groups — keep to 2-4 for usability

#### mark-the-words (requires `instruction` — REQUIRED field)

```yaml
- type: mark-the-words
  title: "Знайдіть іменники"
  instruction: "Знайдіть і позначте всі іменники в тексті."  # REQUIRED
  text: "Гарний день приніс радість у серце. Маленька дитина грала в парку. Сонячне світло освітлювало дорогу."
  answers: ["день", "радість", "серце", "дитина", "парку", "світло", "дорогу"]
```

❌ WRONG: `items:` array — mark-the-words uses `text` (single string) + `answers`
❌ WRONG: Missing `instruction` — it is REQUIRED for this type

#### cloze (minItems: 14 blanks)

```yaml
- type: cloze
  title: "Заповніть пропуски"
  passage: "Це {{1}} з пропусками. Кожен {{2}} має номер."  # Use {{N}} markers
  blanks:  # minItems: 14 — you need at least 14 blanks!
    - id: 1
      answer: "текст"
      options: ["текст", "слово", "речення", "абзац"]  # exactly 4
    - id: 2
      answer: "пропуск"
      options: ["пропуск", "елемент", "частина", "блок"]
```

❌ WRONG: `items:` — cloze uses `passage` + `blanks`
❌ WRONG: Fewer than 14 blanks — schema requires minItems: 14

#### error-correction (ALL 5 fields REQUIRED per item)

```yaml
- type: error-correction
  title: "Виправте помилку"
  items:  # minItems: 6
    - sentence: "Я кушаю яблуко кожен день."
      error: "кушаю"                            # REQUIRED
      answer: "їм"                              # REQUIRED
      options: ["їм", "їду", "їжу", "кусаю"]   # REQUIRED, exactly 4
      explanation: "«Кушати» — русизм, правильно «їсти»."  # REQUIRED
```

❌ WRONG: Missing any of `sentence/error/answer/options/explanation` — ALL five are required
✅ Optional: `error_type: "word"` (or "phrase", "register", "construction")

#### select (multi-correct, min 4 options)

```yaml
- type: select
  title: "Оберіть правильні відповіді"
  items:  # minItems: 6
    - question: "Які з цих слів є іменниками? Оберіть усі правильні."
      options:  # minItems: 4, maxItems: 6
        - text: "книга"
          correct: true
        - text: "читати"
          correct: false
        - text: "стіл"
          correct: true
        - text: "швидко"
          correct: false
```

#### quiz

See **"Correct Quiz Schema"** section above for the full reference pattern.

❌ WRONG: `explanation` inside an option object — it goes at the question level

### Mandatory Self-Check Before Output

After writing all activities, run these checks mentally. Any failure = fix before submitting.

**1. SELECT min_correct match** — every `select` question's `min_correct` must equal exact count of `correct: true` options. Count them.

**2. QUIZ single correct** — every `quiz` item must have exactly 1 `correct: true` option.

**3. FILL-IN answer in options** — every `fill-in` item's `answer` must appear verbatim in its `options` list.

**4. TRANSLATE single correct** — every `translate` item must have exactly 1 `correct: true` option.

**5. MARK-THE-WORDS answers in text** — every string in `answers` must appear verbatim in the `text` field.

**6. UNJUMBLE no run-ons** — every `answer` string must be a single sentence. If a capital letter appears mid-answer without preceding punctuation (`.!?:`), you have merged two sentences. Split into two separate items instead.

**7. UNJUMBLE vocabulary scope** — every word in every `words` array must come from `vocabulary_hints` in the plan file OR be a basic function word (preposition, conjunction, particle). Do NOT introduce grammar forms not yet taught in this module. Specifically: if this module teaches dative PRONOUNS only, do not use possessive adjective dative forms (моїй, твоїй, нашій…) — those belong to a dative NOUNS module.

### Activity Count Check (MANDATORY)

**Count your activities before outputting.** You MUST generate 5 activities. Previous rebuilds consistently underproduced (8 activities when 12-16 were needed). If under target, ADD MORE activities before submitting. Types to add when short: quiz (8+ items), fill-in (8+ items), match-up (8+ pairs).

### Output Delimiters

Activities block (BARE LIST — no wrapper):

```
===ACTIVITIES_START===

- type: quiz
  title: "..."
  items:
    ...

- type: unjumble
  title: "..."
  items:
    ...

===ACTIVITIES_END===
```

Vocabulary block (OBJECT with `items:` wrapper):

```
===VOCABULARY_START===

items:
  - lemma: "іменник"
    translation: "noun"
    pos: "noun"
  - lemma: "дієслово"
    translation: "verb"
    pos: "noun"
    notes: "describes the concept of a verb as a part of speech"

===VOCABULARY_END===
```

## Friction Report (MANDATORY)

After your YAML blocks, include:

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
- Do NOT add `id` field to non-reading activities (seminar tracks)
- Do NOT request skills or delegate to Claude
- If you're unsure about a schema field, add:
  `NEEDS_HELP: Cannot determine correct schema for {activity_type} field "{field_name}"`
  `HELP_TYPE: yaml_schema`
