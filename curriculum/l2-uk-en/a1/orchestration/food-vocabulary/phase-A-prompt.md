# Beginner Research + Meta Outline

> **You are Gemini, executing the research phase for a beginner-level module.**
> **Your task: Generate lightweight research notes AND a content_outline (meta YAML) in one pass.**

---

## Your Input

Read the plan file (SOURCE OF TRUTH):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/food-vocabulary.yaml
```

Read the meta file (you will replace the content_outline):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/meta/food-vocabulary.yaml
```

Read the level quick-ref for constraints:
```
/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md
```

---

## Module Sequence Constraints

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



---

## PART 1: Research

Research **Food and Drink** for the **A1** track.

Beginner research is focused and practical — no literary analysis, no decolonization framing.

### What to research:

1. **State Standard**: Briefly check `docs/l2-uk-en/state-standard-2024-mapping.yaml` for the relevant A1 entry. Quote the §reference if one exists. If no mapping applies (e.g., letter-introduction modules), write "No specific § — foundational literacy prerequisite."
2. **Vocabulary**: For key vocabulary items in the plan's `vocabulary_hints`, list them in a table with brief notes (frequency, collocations, or cognate status). Minimum 3 rows.
3. **Common errors**: 2-3 mistakes English speakers make with this topic (numbered list)
4. **Cultural hook**: 1-2 verified cultural facts or fun connections (numbered list, keep it simple)
5. **Cross-references**: Which modules this builds on and prepares for (check plan's `connects_to`)
6. **Notes**: Any observations useful for the content writer

### What NOT to research:

- Decolonization framing (irrelevant for alphabet and basic vocabulary)
- Literary or historical sources
- Deep frequency analysis (a brief table is enough)

---

## PART 2: Meta Outline

Generate a `content_outline` for this module. The outline defines H2/H3 structure with word budgets.

**Target**: 1200 total words across all sections.

### Outline rules:

1. Section word budgets must sum to approximately 1200 (±10%)
2. Each section needs a clear teaching purpose (introduce, practice, reinforce)
3. Structure should build progressively: introduce concept → show examples → practice → summarize
4. Include a summary section with 3-4 self-check questions

---

## Output Format

```
===RESEARCH_START===

# Дослідження: Food and Drink

## State Standard Reference
§{section_number}: "{quoted requirement}" (or "No specific § — foundational literacy prerequisite" for alphabet modules)
Alignment: {how this module addresses the standard}

## Vocabulary Frequency
| Word | Notes | Key collocations |
|------|-------|------------------|
| ...  | ...   | ...              |

## Cultural Hooks
1. {Verified fact — keep simple and age-appropriate}

## Common Learner Errors
1. {Error pattern} → {Correct form} — {Why it happens}
2. ...

## Cross-References
- Builds on: {module slugs or "first module"}
- Prepares for: {module slugs}

## Notes for Content Writing
- {Any observations for the content writer}

===RESEARCH_END===
```

**Research word cap**: 400-800 words. Keep it dense: facts, tables, examples — not prose.

```
===META_OUTLINE_START===
content_outline:
  - title: "Section Title"
    slug: section-slug
    words: 300
    points:
      - "Teaching point 1"
      - "Teaching point 2"
  - title: "Another Section"
    slug: another-section
    words: 250
    points:
      - "Teaching point"
===META_OUTLINE_END===
```

## Boundaries

- Do NOT write lesson content — only research notes and meta outline
- Do NOT invent vocabulary outside the plan's vocabulary_hints
- Do NOT fabricate cultural facts — if unsure, omit
- Keep research focused — beginner modules need structured research, not lengthy prose
