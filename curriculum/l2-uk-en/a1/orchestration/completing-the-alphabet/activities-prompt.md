# Beginner Activities & Vocabulary

> **You are Gemini, generating activities and vocabulary for a beginner-level module.**
> **Your ONLY task: Generate activities YAML and vocabulary YAML.**

## Targets

| Target | Value |
|--------|-------|
| Skill identity | Patient & Supportive Ukrainian Tutor |
| Module persona | Patient Supportive Tutor, acting as Typography Artist |
| Activities required | 0–15 |
| Required types | watch-and-repeat, classify, image-to-letter, quiz, classify |
| Vocabulary items | 20 |

### Item Minimums Per Activity Type

| Type | Minimum |
|------|--------|
| quiz | ≥6 items |
| true-false | ≥6 items |
| fill-in | ≥6 items |
| match-up | ≥6 pairs |
| anagram | ≥6 items |
| unjumble | ≥6 items |
| group-sort | ≥8 items |
| watch-and-repeat | ≥1 items |
| classify | ≥1 items |
| image-to-letter | ≥5 items |

**CRITICAL — HARD FAIL if violated:** Each activity MUST meet the minimum item count for its type. Activities with fewer items than the minimum will cause an automatic validation failure. Check the minimums table above BEFORE submitting.

### Real Textbook Exercises (вправи) — Pedagogical Inspiration

These are real exercises from Ukrainian school textbooks (grade 1/2). Study their **pedagogical patterns** — how they build progressively, use familiar vocabulary, and test specific skills. Since your students are English-speaking adults, **translate exercise instructions to English** while keeping Ukrainian content words. Adapt the pedagogical approach (progressive difficulty, real-world context) but not the language of instruction.

**Grade 1, zaharijchuk** — Сторінка 73:
```
71
	
Відшукай предмети, у назвах яких є буква ї, 
звуки [йа], звук [дз].
Вийди, вийди, ... ,
На дідове ... ,
На бабине ... ,
На наше ... ,
На весняні ... ,
На маленькі ... .
полечко
зіллячко
 квіточки
сонечко
подвір’ячко
 діточки
	
Знайди «загублений» склад у словах — на-
звах намальованих предметів. 
	
Прочитай слова в рамках. Розмісти їх у по-
трібних місцях у закличці. Прочитай її. 
__ -мін-го	
фук-,	
фла-,	
фут-
__ -ре-ло	
дзе-,	
джи-,	
дже-
лі- __ -на	
-ши-,	
-щи-,	
-чи-
Pidruchnyk.com.ua
```

**Grade 1, zaharijchuk** — Сторінка 11:
```
9
Склад слова.  
Наголошені та ненаголошені склади
	 Що «зайве»? Поділи слова на склади. Визнач 
наголошений склад.
        
        
        
	 Який у тебе сьогодні настрій? Вибери.
```

**Grade 1, zaharijchuk** — Сторінка 30:
```
28
Вшниі, шаркептик, шмкруаа, 
шшпииан, аачкш.
	
«Збери» слова — назви намальованих пред-
метів. Поділи на склади слово, у якому дві 
букви ш (усно).
Бачу Ш, ш (ша). Чую [ш].
ш и н ш и
ш и ш к
к о м и ш
и
а
л
а
о
у
и
і
Ш
ша
шо
шу
ши
ші
а
о
у
и
і
аш
ош
уш
иш
іш
Ш
ша-                  
шо-                       шпа-                   
ши
шка
на
шу
м
міти
ше
лест
рех
 [  –  •–  |  –•|  –•] 
 [  –  •|  –  •– ] 
Ш ш
Pidruchnyk.com.ua
```

**Grade 1, zaharijchuk** — Сторінка 24:
```
22
	 Утвори слова — нáзви предметів.
Х
	
Що тобі відомо про персонажів казки «Ко-
тигорошко»?  Роз­кажи.
	
Прочитай склади. Знайди слова із цими 
складами.
	
Розділи речення на слова, прочитай при­
слів’я. У при­слі­в’ї є 4, 5 чи 6 слів? Вибери 
правильну відповідь.
	
Зимабезснігу — літобезхліба.
	
Які букви нагадують ці предмети?
хвилина
мухомор
горіхи
горох
хви-
-хо-
-рох
-хи
Pidruchnyk.com.ua
```



## Vocabulary Scope

> **Activity answers must use words from the lesson content you are reinforcing.** Read the content file first. Distractors (wrong options) may use other level-appropriate words, but correct answers should practice vocabulary from the lesson. If you need a concept not covered in the content, use English instead.

## Module Constraints (HARD FAIL if violated)

GRAMMAR CONSTRAINTS (A1.1 — First Contact):
Keep grammar simple — this is the learner's first exposure to Ukrainian.

ALLOWED:
- Це + noun: «Це кіт», «Це мама»
- Simple present tense (я читаю, я бачу)
- Basic imperatives (читай, слухай, дивись)
- Question words: «Хто це?», «Що це?», «Де?»
- Так/Ні answers
- Adj + noun: «великий дім», «нова книга»

BANNED (too complex for first contact):
- Past tense, future tense, conditionals
- Participles, passive voice, gerunds
- Compound/complex sentences — max 1 clause per sentence (no і/а/але joining clauses)
- Do not explicitly teach cases — use nouns in natural contexts

METALANGUAGE:
- ALL terminology in English first, Ukrainian in parentheses: 'vowels (голосні)'
- Section headings MUST be bilingual (e.g., '## Голосні — Vowels')
- Explanatory prose in English, Ukrainian for examples and dialogues

> **These constraints apply to activities too.** If only specific letters are allowed, every Ukrainian word in activities must use ONLY those letters. If sentences are not allowed, do NOT create sentence-level activities.

## Your Input

Read these files:

| File | Purpose |
|------|---------|
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/completing-the-alphabet.md` | Lesson content to test/reinforce |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/completing-the-alphabet.yaml` | vocabulary_hints |
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

1. **Activity answers must use words from the lesson content.** Distractors MUST be verified against VESUM — call `verify_words` on every distractor before including it. Never use unverified or made-up words.
2. **Plausible, clear items.** Every question must have one unambiguous correct answer.
3. **No sentence-level activities** if constraints say letters/syllables only.
4. **Prefer fewer, high-quality activities** over padding. 6 good activities > 8 activities where the last 2 are filler.
5. **No duplicate options.** Every distractor within an item must be unique. Copy-pasting the same option multiple times is an instant fail.

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

- **No Russianisms**: кушати→їсти, приймати участь→брати участь, получати→отримувати, самий кращий→найкращий, відноситися→стосуватися, слідуючий→наступний
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

## Builder Notes (MANDATORY)

```
===BUILDER_NOTES_START===
phase: ACTIVITIES
status: SUCCESS | PARTIAL | BLOCKED
activity_count: {number of activities generated}
deviations:
  - "{any deviations from plan activity_hints and why}"
frictions:
  - type: SCHEMA_MISMATCH | PLAN_GAP | CONTENT_VOCABULARY_GAP
    description: "{what went wrong}"
    proposed_fix: "{how to fix}"
unverified_terms:
  - "{Ukrainian words in activities you couldn't verify}"
review_focus:
  - "{activities or items that need reviewer attention}"
===BUILDER_NOTES_END===
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

## Item Counting

Use the post-generation verification block below to confirm you hit the required item counts. If any type is short, add more items before outputting.

## Activity Focus Override

If the plan's `activity_hints` includes a `focus` description, it is a HARD OVERRIDE of the default pattern for that activity type. Read the focus carefully and implement it literally.

Example: If focus says "Match Ukrainian letter to its sound (for false friends: Н≠H, С≠C)" → your match-up pairs MUST be letter→sound, NOT word→translation.

## Post-Generation Verification (MANDATORY)

After generating all activities, output this verification block:

```
===ACTIVITY_VERIFY_START===
Activity counts vs plan:
  - {type}: {actual} items (plan: {required}) ✅|❌
  - ...
Focus compliance:
  - {type}: {focus description} → implemented as: {what you actually built} ✅|❌
===ACTIVITY_VERIFY_END===
```

If any line shows ❌, output a corrected `===ACTIVITIES_START===` to `===ACTIVITIES_END===` block with the fixes applied, THEN output the friction report.

## Boundaries

- Do NOT modify lesson content — only generate activities and vocabulary
- Do NOT add fields not in the schema (check schema carefully!)
- Do NOT wrap in `activities:` or `vocabulary:` dictionary keys
- Do NOT request skills or delegate to Claude

