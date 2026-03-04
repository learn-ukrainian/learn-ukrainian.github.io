# Beginner Research + Meta Outline

> **You are Gemini, executing the research phase for a beginner-level module.**
> **Your task: Generate lightweight research notes AND a content_outline (meta YAML) in one pass.**

---

## Your Input

Read the plan file (SOURCE OF TRUTH):
```
{PLAN_PATH}
```

Read the meta file (you will replace the content_outline):
```
{META_PATH}
```

Read the level quick-ref for constraints:
```
{QUICK_REF_PATH}
```

---

## Module Sequence Constraints

{PEDAGOGICAL_CONSTRAINTS}

{DECODABLE_VOCABULARY}

---

## PART 1: Research

Research **{TOPIC_TITLE}** for the **{LEVEL}** track.

Beginner research is focused and practical — no literary analysis, no decolonization framing, no frequency studies.

### What to research:

1. **Textbook approach**: How do Ukrainian textbooks for beginners introduce this topic? What order, what examples?
2. **Common errors**: 2-3 mistakes English speakers make with this topic
3. **Cultural hook**: 1 verified cultural fact or fun connection (keep it simple and age-appropriate)
4. **Cross-references**: Which modules this builds on and prepares for (check plan's `connects_to`)

### What NOT to research:

- State Standard mapping (not useful for letter/syllable modules)
- Vocabulary frequency analysis (word list is provided in constraints)
- Decolonization framing (irrelevant for alphabet and basic vocabulary)
- Literary or historical sources

---

## PART 2: Meta Outline

Generate a `content_outline` for this module. The outline defines H2/H3 structure with word budgets.

**Target**: {WORD_TARGET} total words across all sections.

### Outline rules:

1. Section word budgets must sum to approximately {WORD_TARGET} (±10%)
2. Each section needs a clear teaching purpose (introduce, practice, reinforce)
3. Structure should build progressively: introduce concept → show examples → practice → summarize
4. Include a summary section with 3-4 self-check questions

---

## Output Format

```
===RESEARCH_START===
## Research Notes

[Your research findings — 200-400 words max]
===RESEARCH_END===
```

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
- Keep research concise — beginner modules need less research, not more
