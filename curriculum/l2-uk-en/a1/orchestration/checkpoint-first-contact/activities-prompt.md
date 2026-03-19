# Beginner Checkpoint Activities & Vocabulary

> **You are Gemini, generating activities and vocabulary for a CHECKPOINT module.**
> **Your ONLY task: Generate activities YAML and vocabulary YAML.**

## CHECKPOINT IDENTITY

**This is a CHECKPOINT module — activities must test INTEGRATION, not isolated skills.**

Activities in a checkpoint module are fundamentally different from teaching module activities:

| Teaching Module Activities | Checkpoint Activities |
|---------------------------|----------------------|
| Test one skill at a time | Combine 2+ skills per activity |
| Practice newly introduced patterns | Review patterns from multiple prior modules |
| Drill specific grammar points | Test integrated language use |
| Focus on accuracy of new forms | Focus on fluency with known forms |

**Golden rule: Every activity should require the learner to combine skills from different prior modules.**

## Targets

| Target | Value |
|--------|-------|
| Skill identity | Patient & Supportive Ukrainian Tutor |
| Module persona | Patient Supportive Tutor, acting as Friendly Hostel Host |
| Activities required | 0–15 |
| Required types | quiz |
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

**CRITICAL — HARD FAIL if violated:** Each activity MUST meet the minimum item count for its type.

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

> **Every Ukrainian word in your activities MUST come from PRIOR modules that this checkpoint reviews.** Read the content file first. Do not introduce new Ukrainian vocabulary — only practice words from the reviewed block.

## Module Constraints (HARD FAIL if violated)

GRAMMAR CONSTRAINTS (A1.1 — Grammar, M07-M14):
Keep grammar simple — first exposure to Ukrainian grammar.

ALLOWED:
- Це + noun: «Це кіт», «Це мама»
- Simple present tense (я читаю, я бачу)
- Basic imperatives (читай, слухай, дивись)
- Question words: «Хто це?», «Що це?», «Де?»
- Так/Ні answers
- Adj + noun: «великий дім», «нова книга»

BANNED: Past/future tense, conditionals, participles, passive, gerunds,
compound sentences (no і/а/але joining clauses)

METALANGUAGE: English first, Ukrainian in parentheses. Bilingual headings.

> **These constraints apply to activities too.** If only specific letters are allowed, every Ukrainian word in activities must use ONLY those letters.

## Your Input

Read these files:

| File | Purpose |
|------|---------|
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/checkpoint-first-contact.md` | Checkpoint content to reinforce |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/checkpoint-first-contact.yaml` | vocabulary_hints (all REVIEW words) |
| `schemas/activities-a1.schema.json` | Allowed fields per activity type |
| `docs/ACTIVITY-YAML-REFERENCE.md` | Activity reference guide |

---

## Checkpoint Activity Design Principles

### 1. Integration Over Isolation

Each activity should combine skills. Examples:

- **Quiz**: Questions that require understanding BOTH gender AND adjective agreement (not just one)
- **Fill-in**: Sentences requiring correct case ending AND correct vocabulary choice
- **Unjumble**: Sentences combining vocabulary from 2+ prior modules
- **Group-sort**: Sorting by multiple criteria (gender + number, or case + meaning)

### 2. New Contexts, Familiar Words

Use all review vocabulary in situations the learner hasn't seen before:
- If they learned food words and adjectives separately, combine them: «велика піца», «свіжий хліб»
- If they learned greetings and questions separately, create dialogues that use both

### 3. Realistic Scenarios

Frame activities around realistic situations:
- Ordering at a cafe (combines food vocabulary + polite forms + questions)
- Describing a room (combines objects + adjectives + prepositions)
- Meeting someone new (combines greetings + introductions + questions)

### 4. Progressive Difficulty Within Activities

Start with simpler integration (2 skills) and build to more complex (3+ skills) within the same activity.

---

## Beginner Activity Rules

### Language in Activities

- **Questions, explanations, instructions** → English (scaffolding language)
- **Target content being practiced** → Ukrainian (words, phrases from prior modules)
- **Option text** → Ukrainian when selecting Ukrainian words/letters, English when selecting concepts

### Activity Types by Constraint Level

**If constraints say "letters/syllables only" (no sentences):**
Use: `quiz`, `match-up`, `group-sort`, `anagram`, `true-false`

**If constraints allow words and simple phrases:**
Add: `fill-in`, `match-up` with phrases

**If constraints allow basic sentences:**
Add: `unjumble`, `fill-in` with sentences, `translate`

### Do NOT Use Grammar Terminology

A1/A2 learners do NOT know terms like іменник, дієслово, голосний, відмінок. Write questions in plain English.

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
```

**CRITICAL**: Letters MUST be space-separated.

### match-up

```yaml
- type: match-up
  title: "Match Letter to Sound"
  pairs:  # minItems: 6 — MUST use "pairs:" not "items:"
    - left: "Н"
      right: "/n/ sound"
```

### fill-in (MUST include `options` array)

```yaml
- type: fill-in
  title: "Complete the Sentence"
  items:  # minItems: 6
    - sentence: "Мама купує ___."
      answer: "молоко"
      options: ["молоко", "молока", "молоку", "молоком"]
```

### group-sort

```yaml
- type: group-sort
  title: "Sort the Words"
  groups:  # 2-4 groups
    - name: "Masculine"
      items: ["стіл", "дім"]
    - name: "Feminine"
      items: ["книга", "мама"]
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

### unjumble (sentence word reordering — ONLY when sentences allowed)

```yaml
- type: unjumble
  title: "Put the Words in Order"
  instruction: "Arrange the words to form a correct Ukrainian sentence."
  items:  # minItems: 8
    - words: ["книга", "Це", "нова"]
      answer: "Це нова книга"
```

**CRITICAL**: Use `words` (array of strings) + `answer` (string).

---

## Activity Quality Rules

1. **Every Ukrainian word must appear in the lesson content or prior modules.** Do NOT introduce new vocabulary.
2. **Integration focus.** Each activity should combine skills from different prior modules.
3. **Plausible, clear items.** Every question must have one unambiguous correct answer.
4. **No sentence-level activities** if constraints say letters/syllables only.
5. **Prefer fewer, high-quality integrative activities** over many single-skill drills.

## Mandatory Self-Check

1. **QUIZ single correct** — every quiz item has exactly 1 `correct: true`
2. **ANAGRAM letter match** — scrambled letters = same letters as answer
3. **MATCH-UP unique pairs** — no duplicate left or right values
4. **Schema compliance** — only fields from `schemas/activities-a1.schema.json`, no extras
5. **Integration check** — does each activity combine 2+ skills?

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

