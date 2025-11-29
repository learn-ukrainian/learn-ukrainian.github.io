# Module Template

This template defines how to write module content in Markdown.
The generator will parse this into Vibe-compatible JSON and HTML preview.

---

## Structure

```markdown
---
# YAML Frontmatter (required metadata)
module: 1
title: "Module Title"
subtitle: "Optional subtitle"
level: A1
phase: A1.1
duration: 45
transliteration: full|vocab-only|first-occurrence|none
tags: [tag1, tag2]
---

# Lesson Content

## warm-up
Theory/notes content here...

## presentation
### Section Title
Content with bullet points:
• Point one
• Point two

More content...

## practice
Practice instructions...

## production
Production tasks...

---

# Activities

## match-up: Activity Title
> Instructions for the activity

| Left | Right |
|------|-------|
| Item A | Match A |
| Item B | Match B |

## quiz: Activity Title
> Instructions for the activity

1. Question text here?
   - [ ] Wrong option
   - [x] Correct option
   - [ ] Wrong option
   - [ ] Wrong option
   > Explanation shown after answering

2. Another question?
   - [x] Correct
   - [ ] Wrong
   > Explanation

## group-sort: Activity Title
> Instructions for the activity

### Group Name 1
- Item A
- Item B

### Group Name 2
- Item C
- Item D

## gap-fill: Activity Title
> Instructions

1. Sentence with ___ blank here.
   > answer: correct word

---

# Vocabulary

| uk | translit | ipa | en | pos | gender | note |
|----|----------|-----|-----|-----|--------|------|
| слово | slovo | /ˈslɔwɔ/ | word | noun | n | Learning note |
| інше | inshe | /ˈinʃe/ | other | adj | | Another note |

---

# Letter Groups (optional, for alphabet modules)

## True Friends
А Е І О К М Т

## False Friends
В Н Р С У Х

## New Letters
Б Д З Л П Ф
```

## Parsing Rules

1. **Frontmatter**: YAML between `---` markers at the top
2. **Lesson Phases**: H2 headers matching `warm-up`, `presentation`, `practice`, `production`
3. **Activities**: H2 with format `type: title` after `# Activities` section
4. **Vocabulary**: Table after `# Vocabulary` header
5. **Letter Groups**: Optional section for alphabet modules

## Activity Types

- `match-up`: Table with Left/Right columns
- `quiz`: Numbered questions with checkbox options, `[x]` = correct
- `group-sort`: H3 group names with item lists
- `gap-fill`: Numbered sentences with `___` blanks
- `flash-cards`: Auto-generated from vocabulary

## Notes

- Use `>` for instructions/explanations
- Use `•` or `-` for bullet points
- Tables must have header row with `|---|` separator
- Keep content concise for mobile display
