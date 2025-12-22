# Stage 1: Skeleton

Create the module skeleton with frontmatter, section headers, and vocabulary table.

## Input Required

- **Level**: A1, A2, B1, B2, C1, C2
- **Module number**: 01-XX (depends on level)
- **Curriculum plan section**: Extracted from `{LEVEL}-CURRICULUM-PLAN.md`

## Output

A markdown file with:
1. Complete YAML frontmatter
2. All section headers (based on pedagogy)
3. Vocabulary table (copied EXACTLY from plan)
4. Empty content placeholders

## Frontmatter Template

```yaml
---
module: {level}-{number}
title: "{title from plan}"
subtitle: "{subtitle if applicable}"
version: "1.0"
phase: "{phase}"
pedagogy: "{PPP|TTT|CLIL}"
objectives:
  - "Learner can..."
  - "Learner can..."
vocabulary_count: {count}
---
```

## Section Structure by Pedagogy

### PPP (A1-A2)
```markdown
# {title}

## Warm-up
[placeholder]

## Presentation
[placeholder]

## Practice
[placeholder]

## Production
[placeholder]

## Cultural Insight
[placeholder]

---

## Summary
[placeholder]

---

## Vocabulary
{copy table from plan}
```

### TTT (B1+ grammar)
```markdown
# {title}

## Diagnostic
[placeholder]

## Analysis
[placeholder]

## Deep Dive
[placeholder]

## Practice
[placeholder]

---

## Summary
[placeholder]

---

## Словник
{copy table from plan}
```

### CLIL/Narrative (B1+ vocabulary/culture)
```markdown
# {title}

## Introduction
[placeholder]

## Immersive Narrative
[placeholder]

## Analysis
[placeholder]

## Grammar in Context
[placeholder]

---

## Summary
[placeholder]

---

## Словник
{copy table from plan}
```

## Vocabulary Table Formats

### A1-A2 (English headers)
```markdown
| Word | IPA | English | POS | Gender | Note |
|------|-----|---------|-----|--------|------|
| слово | /ˈsɫɔwɔ/ | word | noun | n | - |
```

### B1+ (Ukrainian headers)
```markdown
| Слово | Вимова | Переклад | ЧМ | Примітка |
|-------|--------|----------|-----|----------|
| слово | /ˈsɫɔwɔ/ | word | ім. | - |
```

### B2-C2 (Simplified)
```markdown
| Слово | Переклад | Примітки |
|-------|----------|----------|
| слово | word | - |
```

## Validation

Before completing:
- [ ] Frontmatter has all required fields
- [ ] Pedagogy matches level (PPP for A1-A2, TTT/CLIL for B1+)
- [ ] All section headers present
- [ ] Vocabulary table copied exactly from plan (no additions/removals)
- [ ] Module number in correct format (01-XX with leading zero)

## File Naming

`curriculum/l2-uk-en/{level}/{number}-{slugified-title}.md`

Example: `curriculum/l2-uk-en/a1/01-the-cyrillic-code-i.md`
