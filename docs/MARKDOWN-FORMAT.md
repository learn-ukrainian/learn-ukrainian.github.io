# Universal Markdown Format Specification

## Purpose

This document defines the standard markdown format for all curriculum modules. The format is designed to be:
- **Unambiguous**: Every pattern has exactly one meaning
- **Complete**: Covers all content types needed for language learning
- **Simple**: Easy to parse and render

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

### Matching (in Activities section)

```yaml
# Вправи

## match-up: Match words
pairs:
  - left: "привіт"
    right: "hello"
  - left: "дякую"
    right: "thank you"
```

---

## Section Structure

Standard module sections:

```markdown
---
module: 1
title: Title
level: A1
---

# Вступ
Introduction content...

# Main Content Section
Teaching content with → for transformations...

# Практика
Exercises with > [!answer] for answers...

# Вправи
## match-up: Title
pairs:
  - left: "x"
    right: "y"

## quiz: Title
questions:
  - prompt: "Question?"
    options: ["a", "b", "c"]
    answer: 0

# Словник
| Ukrainian | English |
|-----------|---------|
| слово     | word    |

# Підсумок
Summary content...
```

---

## Validation Rules

1. `→` in answers = ERROR (should use `> [!answer]`)
2. `> [!answer]` without preceding question = WARNING
3. Unclosed callout blocks = ERROR
4. Mixed old/new formats = ERROR
