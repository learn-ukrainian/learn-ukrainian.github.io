# Universal Markdown Format Specification

## Purpose

This document defines the standard markdown format for all curriculum modules. The format is designed to be:
- **Unambiguous**: Every pattern has exactly one meaning
- **Complete**: Covers all content types needed for language learning
- **Simple**: Easy to parse and render

> [!IMPORTANT]
> **Strict Header Hierarchy**
> The generator strictly adheres to the following header levels. Deviating will cause sections to be ignored.
> *   **H1 (`#`)**: Main Sections (Title, Summary, Activities, Vocabulary).
> *   **H2 (`##`)**: Content Subsections (Warm-up, Presentation, Activity Items).
> *   **H3 (`###`)**: Deep nested content (rarely used).

---

## Module Structure

All modules must follow this top-level structure:

```markdown
---
frontmatter: ...
---

# [Module Title]

## [Section: Warm-up]
## [Section: Main Content]

# Summary
(H1 Required)

# Activities
(H1 Required)
## [Activity Type]: [Title] (H2 Required)

# Vocabulary
(H1 Required)
```

---

## Content Types

### 1. Regular Content (Always Visible)

Regular markdown text, headers, lists, tables, etc.

```markdown
# Section Title

Regular paragraph text.

- List item
- Another item

| Column 1 | Column 2 |
|----------|----------|
| data     | data     |
```

### 2. Linguistic Transformations (Always Visible)

Use `→` arrow for showing how words/forms change. This is ALWAYS visible content.

```markdown
- їсти → їв (infinitive to past)
- я → мені (nominative to dative)

| Base | Changed | Rule |
|------|---------|------|
| к    | ч       | before е |
| г    | ж       | before у |
```

### 3. Answers (Hidden by Default)

Use `> [!answer]` callout for exercise answers that should be hidden.

```markdown
1. Він ___ (читати) книгу.
   > [!answer] читає

2. Translate: "I am reading"
   > [!answer] Я читаю
```

### 4. Explanations (Hidden with Answer)

Use `> [!explanation]` for explanations shown with the answer.

```markdown
1. Why is this правда or міф?
   > [!answer] Правда
   > [!explanation] Because Ukrainian has 7 cases, not 6.
```

### 5. Alternative Answers

Use `> [!alt]` for acceptable alternative answers.

```markdown
1. How do you say "hello"?
   > [!answer] Привіт
   > [!alt] Вітаю
   > [!alt] Добрий день
```

### 6. Notes and Tips (Always Visible)

Use `> [!note]` or `> [!tip]` for highlighted information.

```markdown
> [!note] Remember: soft sign ь doesn't have its own sound.

> [!tip] Practice this pattern daily for best results.
```

### 7. Model Answers (for Writing Tasks)

Use `> [!model-answer]` callout for longer blocks of model text, such as sample essays, paragraphs, or creative writing prompts where a full exemplar answer is provided. This callout is essential for supporting self-learners in production tasks at B2, C1, and C2 levels.

```markdown
## Вправа: Write a short essay

> [!model-answer]
> [Here would be a full, multi-paragraph model essay.]
>
> Перш за все, варто зазначити, що питання глобального потепління є одним з
> найнагальніших викликів сучасності. Наукові дослідження беззаперечно
> свідчать про зростання середньої температури на планеті, що призводить до
> незворотних змін у кліматичній системі.
>
> По-друге, наслідки цього явища вже відчуваються по всьому світу. Ми
> спостерігаємо екстремальні погодні умови...
```

---

## Migration Rules

### OLD → NEW Conversions

| Old Pattern | New Pattern | Context |
|-------------|-------------|---------|
| `   → **answer**` | `> [!answer] **answer**` | Indented arrow = answer |
| `   - → **answer**` | `> [!answer] **answer**` | List arrow = answer |
| `question → answer` in exercise | `question` + `> [!answer] answer` | Split inline answers |
| `→ answer (explanation)` | `> [!answer] answer` + `> [!explanation] explanation` | Parenthetical = explanation |
| `→ ✅ **Правда.** text` | `> [!answer] Правда` + `> [!explanation] text` | True/false answers |
| `→ ❌ **Міф.** text` | `> [!answer] Міф` + `> [!explanation] text` | True/false answers |
| `word → word` in text/table | Keep as-is | Transformations stay visible |

### Preserved Patterns (No Change)

- `→` in tables (transformation examples)
- `→` in regular text explaining grammar
- `→` in section headers
- Already converted `> [!answer]` blocks

---

## Exercise Structures

### Fill-in-the-blank

```markdown
## Вправа: Fill in the blanks

1. Я ___ (читати) книгу.
   > [!answer] читаю

2. Вони ___ (писати) листи.
   > [!answer] пишуть
   > [!explanation] писати → пиш- stem change
```

### Multiple Choice

```markdown
## Вправа: Choose the correct answer

1. Which case is used for direct objects?
   - [ ] Nominative
   - [x] Accusative
   - [ ] Dative
```

### Translation

```markdown
## Вправа: Translate

1. I love Ukraine.
   > [!answer] Я люблю Україну.

2. She reads a book.
   > [!answer] Вона читає книгу.
   > [!alt] Вона читає книжку.
```

### True/False

```markdown
## Правда чи міф?

1. Ukrainian has 7 grammatical cases.
   > [!answer] Правда
   > [!explanation] Ukrainian has 7 cases: nominative, genitive, dative, accusative, instrumental, locative, and vocative.

2. All Ukrainian nouns have gender.
   > [!answer] Правда
```

---

## Activity Section Format

All activities appear under `# Activities` using pure markdown syntax (NOT YAML).

### Quiz Format

```markdown
## quiz: Title

> Instructions for this activity.

1. Question text here?
   - [ ] Wrong answer
   - [x] Correct answer
   - [ ] Wrong answer
   - [ ] Wrong answer
   > Explanation shown after answering.

2. Another question?
   - [x] Correct answer
   - [ ] Wrong answer
   - [ ] Wrong answer
   - [ ] Wrong answer
   > Explanation text.
```

**Key points:**
- Use `- [x]` for correct answer, `- [ ]` for wrong answers
- Use `>` for explanation (optional)
- See MODULE-RICHNESS-GUIDELINES-v2.md for item counts

### Match-up Format

```markdown
## match-up: Title

> Match the Ukrainian words with their English meanings.

| Left | Right |
|------|-------|
| привіт | hello |
| дякую | thank you |
| так | yes |
| ні | no |
```

**Key points:**
- Use markdown table with `| Left | Right |` headers exactly
- See MODULE-RICHNESS-GUIDELINES-v2.md for item counts

### Fill-in Format

```markdown
## fill-in: Title

> Complete each sentence with the correct word.

1. Я ___ книгу. (читати)
   > [!answer] читаю
   > [!options] читаю | читаєш | читає | читають

2. Вона ___ українською. (говорити)
   > [!answer] говорить
   > [!options] говорить | говорю | говоримо | говорять
```

**Key points:**
- Use `___` for blank
- Use `> [!answer]` for correct answer
- Use `> [!options]` with pipe-separated options
- See MODULE-RICHNESS-GUIDELINES-v2.md for item counts

### True-False Format

```markdown
## true-false: Title

> Decide if each statement is true (Правда) or false (Міф).

- [x] Ukrainian has 7 grammatical cases.
  > Correct! Nominative, Genitive, Dative, Accusative, Instrumental, Locative, Vocative.

- [ ] All Ukrainian nouns are masculine.
  > Incorrect! Ukrainian has three genders: masculine, feminine, and neuter.

- [x] Verb endings show who is doing the action.
  > Correct! That's why pronouns are often optional.
```

**Key points:**
- Use `- [x]` for true statements, `- [ ]` for false statements
- Use `>` for explanation
- See MODULE-RICHNESS-GUIDELINES-v2.md for item counts

### Error Correction Format

```markdown
## error-correction: Title

> Find the mistake in each sentence and correct it.

1. Я **бачу** студент.
   > [!error] студент
   > [!answer] студента
   > [!options] студент | студента | студенту

2. Це моя книга.
   > [!error] none
   > [!answer] ✓
```

**Key points:**
- The sentence usually contains the error (bolding optional but discouraged if it reveals the answer too easily).
- Use `> [!error]` to identify the incorrect word (or `none`).
- Use `> [!answer]` for the correct form.
- Use `> [!options]` for multiple choice correction (optional but recommended).


### Group-sort Format

```markdown
## group-sort: Title

> Sort these items into the correct categories.

### Category 1
- item1
- item2
- item3

### Category 2
- item4
- item5
- item6

### Category 3
- item7
- item8
- item9
```

**Key points:**
- Use `### Category Name` for each group
- Use bullet list for items in that group
- Minimum 2 categories, 3+ items each

### Anagram Format (A1 Only - Phased Out)

**LEVEL RESTRICTIONS:**
- A1 Modules 01-10: ✅ Allowed (Cyrillic scaffolding)
- A1 Modules 11-20: ⚠️ Reduce usage
- A1 Modules 21-30: ❌ Avoid (use unjumble instead)
- A2+: ❌ NOT ALLOWED

```markdown
## anagram: Title

> Arrange the letters to form the correct word.

1. ч и т а т и
   > [!answer] читати
   > (to read)

2. п и с а т и
   > [!answer] писати
   > (to write)
```

**Key points:**
- Spaced letters for scrambled word
- `> [!answer]` for correct word
- `> (translation)` for meaning
- See MODULE-RICHNESS-GUIDELINES-v2.md for item counts
- **Use `unjumble` instead for A1.3+ and all higher levels**

### Unjumble Format

```markdown
## unjumble: Title

> Put the words in the correct order.

1. книгу читаю Я
   > [!answer] Я читаю книгу.
   > (I read a book.) [3 words]

2. українською Вона говорить
   > [!answer] Вона говорить українською.
   > (She speaks Ukrainian.) [3 words]
```

**Key points:**
- Jumbled words on first line
- `> [!answer]` for correct sentence
- `> (translation) [X words]` for meaning and word count
- See MODULE-RICHNESS-GUIDELINES-v2.md for item counts

### Error-Correction Format (A2+)

**LEVEL RESTRICTIONS:**
- A1: ❌ NOT ALLOWED
- A2+: ✅ Required (see MODULE-RICHNESS-GUIDELINES-v2.md for counts)

```markdown
## error-correction: Find and Fix

> Each sentence has ONE error. Find the incorrect word, then choose the correct form.

1. Я бачу студент у бібліотеці.
   > [!error] студент
   > [!answer] студента
   > [!options] студент | студента | студенту | студентом
   > [!explanation] Animate masculine accusative = genitive form

2. Вона читав книгу вчора.
   > [!error] читав
   > [!answer] читала
   > [!options] читав | читала | читало | читали
   > [!explanation] Past tense agrees with subject gender (feminine = -ла)

3. Це моя книга, а це твоя.
   > [!error] none
   > [!answer] ✓
   > [!explanation] No error - keeps learners alert (use sparingly: 1-2 per activity)
```

**Key points:**
- Sentence with error on first line
- `> [!error]` for the incorrect word (or `none` for trick questions)
- `> [!answer]` for the correct form (or `✓` for no-error items)
- `> [!options]` with pipe-separated options (must include both wrong and correct)
- `> [!explanation]` **REQUIRED** - explains why it's wrong and the rule
- See MODULE-RICHNESS-GUIDELINES-v2.md for item counts
- Use `none` errors sparingly (1-2 per activity max)

**UI Flow:**
1. User clicks word they think is wrong
2. If correct word selected → show options to choose fix
3. If wrong word selected → feedback "Try again"
4. After fix selected → show explanation

**Scoring:** 2 points per item (1 for identifying error, 1 for correct fix)

---

## IMPORTANT: DO NOT USE YAML FORMAT

**WRONG** (will not parse):
```yaml
## match-up: Title
pairs:
  - left: "привіт"
    right: "hello"

## quiz: Title
questions:
  - prompt: "Question?"
    options: ["a", "b", "c"]
    answer: 0
```

**CORRECT** (use markdown):
```markdown
## match-up: Title

| Left | Right |
|------|-------|
| привіт | hello |

## quiz: Title

1. Question?
   - [x] Correct
   - [ ] Wrong
```

---

## Section Structure

The example below shows the **PPP (Presentation-Practice-Production)** structure.
Note that **TTT (Test-Teach-Test)** and **CLIL/Narrative** structures are also valid and supported.
Refer to `claude_extensions/skills/module-architect/SKILL.md` for specific pedagogical section headers.

Standard module sections (PPP Example):

```markdown
---
title: Title
subtitle: Subtitle
phase: A1.1
duration: 45
transliteration: full
tags: [grammar]
objectives:
  - Objective 1
grammar:
  - Grammar point 1
---

# Lesson Content

## warm-up
Introduction content...

## presentation
Teaching content with → for transformations...

## practice
Exercises with > [!answer] for answers...

## production
Open-ended practice...

---

# Activities

## quiz: Title
[Using markdown format - see Activity Section Format above]

## match-up: Title
[Using markdown table format]

## fill-in: Title
[Using markdown format with > [!answer] and > [!options]]

---

# Vocabulary

| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| слово | /ˈslɔvɔ/ | word | noun | n | |

---

# Summary

> Summary content...
```

---

## Vocabulary Section Formats

The vocabulary section format varies by level to support immersion progression. The parser (`scripts/lib/parsers/vocabulary.ts`) supports all formats dynamically.

### Tier 1: A1 (Modules 1-30) — Maximum Scaffolding

```markdown
# Vocabulary

| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| слово | /ˈslɔvɔ/ | word | noun | n | Usage context |
| говорити | /ɦɔvɔˈrɪtɪ/ | to speak | verb | - | говорю, говориш |
| великий | /vɛˈlɪkɪj/ | big, large | adj | m | agrees with noun |
```

**Requirements:**
- English header `# Vocabulary`
- 6 columns: Word, IPA, English, POS, Gender, Note
- Full IPA pronunciation for every word
- Explicit POS: noun, verb, adj, adv, prep, conj, pron, phrase, interj
- Gender for nouns: m, f, n, pl (use `-` for non-nouns)
- Notes for conjugation hints, usage, cognates

### Tier 2: A2-A2+ (Modules 31-80) — Intermediate Support

Same 6-column format as Tier 1:

```markdown
# Vocabulary

| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| подорож | /ˈpɔdɔrɔʒ/ | journey, trip | noun | f | feminine! |
| затримка | /zɑˈtrɪmkɑ/ | delay | noun | f | |
```

**Requirements:**
- Same structure as Tier 1
- English header maintained
- Continue IPA for new vocabulary
- Shorter notes (learners more independent)

### Tier 3: B1 (Modules 81-160) — Transitional

```markdown
# Словник

| Слово | Вимова | Переклад | ЧМ | Примітка |
|-------|--------|----------|-----|----------|
| заперечення | /zɑpɛˈrɛt͡ʃɛnʲːɑ/ | negation | ім | grammar term |
| відмова | /wʲidˈmovɑ/ | refusal | ім | f |
```

**Requirements:**
- Ukrainian header `# Словник`
- Ukrainian column names
- 5 columns: Слово, Вимова (IPA), Переклад, ЧМ (частина мови), Примітка
- POS abbreviations: ім (noun), дієсл (verb), прикм (adj), присл (adv), прийм (prep)
- No separate gender column (include in Примітка if needed)

### Tier 4: B2+ (Modules 161+) — Immersive

```markdown
# Словник

| Слово | Переклад | Примітки |
|-------|----------|----------|
| публіцистика | journalism | стиль ЗМІ |
| коаліція | coalition | політика |
```

**Requirements:**
- Ukrainian header `# Словник`
- Minimal 3-column format
- Only essential info for maximum immersion
- Extended notes for context, collocations, register
- **CBI Note:** For vocabulary modules following a Narrative Arc, words may also be introduced and contextualized directly within the narrative text, with the table serving as a summary or quick reference.

### Review Vocabulary Section (B1+ only)

For modules 81+, include cross-references to recurring words:

```markdown
# Review Vocabulary

| Word | First Module |
|------|-------------|
| ніколи | 7 |
| заборонено | 59 |
```

**Purpose:** Track words from earlier modules that appear in current module's activities.

### POS Values Reference

| Level | Language | Accepted Values |
|-------|----------|-----------------|
| A1-A2+ | English | noun, verb, adj, adv, prep, conj, pron, phrase, interj |
| B1 | Ukrainian abbrev | ім, дієсл, прикм, присл, прийм, сполучн, займ, фраза |
| B2+ | (optional) | іменник, дієслово, прикметник, or omit |

### Word Count Targets

**CRITICAL:** For official word count targets (Total Content Words and New Vocabulary Words per module), refer to the authoritative source:
`docs/l2-uk-en/MODULE-RICHNESS-GUIDELINES-v2.md`

Do not use the deprecated targets previously listed here.

---

## Validation Rules

1. `→` in answers = ERROR (should use `> [!answer]`)
2. `> [!answer]` without preceding question = WARNING
3. Unclosed callout blocks = ERROR
4. Mixed old/new formats = ERROR
