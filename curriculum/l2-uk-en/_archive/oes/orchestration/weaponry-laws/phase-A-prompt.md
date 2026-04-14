# Phase A: Research + Meta (Seminar Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module_v3).**
> **This is a combined Phase 0 + Phase 1. Your ONLY task: Research the topic AND produce the meta outline in one pass.**

---

## Your Input

Read the plan file (SOURCE OF TRUTH):

```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/oes/weaponry-laws.yaml
```

Read the current meta file (for reference — you will replace the content_outline):

```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/oes/meta/weaponry-laws.yaml
```

---

## PART 1: Deep Research

Research **Weaponry Laws** for the **oes** track. Produce structured research notes that will drive content writing in Phase B.

### Research Requirements

1. **Sources**: Find 3+ Ukrainian-language academic sources (esu.com.ua, history.org.ua, uk.wikipedia.org, litopys.org.ua). Russian-language sources are PROHIBITED.
2. **Timeline**: Build a chronological timeline with 5+ dated events/milestones.
3. **Primary Quotes**: Find 2+ quotable primary source excerpts (original Ukrainian text preferred).
4. **Engagement Hooks**: Identify 6+ engagement hooks mapped to specific content sections:
   - `[!myth-buster]` — Decolonization: correct imperial/Soviet myths
   - `[!history-bite]` — Surprising or lesser-known facts
   - `[!context]` — Broader historical/cultural context
   - `[!quote]` — Primary source citations
   - `[!decolonization]` — Ukraine-centric reframing
   - `[!culture]` — Cultural significance
5. **Decolonization Angle**: Identify how this topic has been distorted by imperial/Soviet historiography and what the Ukrainian-centric framing should be.
6. **Section-Mapped Content**: Structure notes with headings that match the `content_outline` sections from the plan. This makes Phase B content writing mechanical.

If this topic involves contested narratives (Ukrainian vs. Russian/Soviet/Polish historiography), include a Contested Terms Table:

```markdown
## Contested Terms

| Concept | Imperial framing | Ukrainian (decolonized) framing |
|---------|-----------------|-------------------------------|
| ...     | ...             | ...                           |
```

---

## PART 2: Meta Outline

After completing research, rebuild the `content_outline` using:
- The plan's section structure as skeleton
- Your research notes to inform depth and word allocation

### Rules for Meta Outline

- **Do NOT copy the old meta's outline** — rebuild from the plan's section structure
- Allocations must sum to approximately **5000** words (±10% acceptable)
- Minimum section allocation: 200 words (merge smaller sections)
- For modules with target ≥ 4000w, aim for **8-12 sections minimum** — this prevents any one section from consuming a disproportionate share of the module.
- **No single section may consume more than 25% of the total word target.** A 5000w module → max 1250w per section. If a plan section would exceed this, you MUST split it.
- Each section must have `section`, `words`, and `points` fields
- Section names must be in Ukrainian (these become H2 headings in the lesson)
- **Section names must match plan exactly** — if the plan has a `content_outline` with section names, use those EXACT names (or very close Ukrainian equivalents). When splitting a large plan section, add a subtitle (e.g. "Читання: I — Походження").
- Points reflect research findings — cite specific facts, dates, quotes where relevant
- Check the subject's vital status: living person → "Значення" / "Вплив"; deceased → "Спадщина" / "Наслідки"

### How to split a plan section (CRITICAL)

**The plan's bullet points are section topics, not sub-bullets.** A plan section with 10 bullet points should become 3-5 meta sections, not one giant section.

**Process:**
1. Count the bullet points in each plan section
2. If a section has 5+ bullets: group them into thematic clusters of 2-4 bullets
3. Each cluster becomes its own meta section with the parent name as prefix:
   - `"Читання: I — Розселення та племінна мозаїка"` (bullets 1-4)
   - `"Читання: II — Суспільний устрій і права"` (bullets 5-7)
   - `"Читання: III — Духовний світ та побут"` (bullets 8-11)
   - etc.
4. Allocate words based on research depth for each cluster

**Example:** A plan section `Читання` with 14 bullet points should NOT become one 3200w meta section. It should become 4-5 sub-sections of 600-800w each. The bullets tell you what the sub-sections should cover.

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

```
===RESEARCH_START===

# Дослідження: Weaponry Laws

## Використані джерела
1. [Source name](URL) — brief description
2. ...
3. ...

## Хронологія
- {date}: {event}
- ...

## Ключові факти та цитати
- ...

## Engagement Hooks (mapped to sections)
- Section "{section_name}": [!hook_type] — description
- ...

## Деколонізаційний контекст
- Imperial/Soviet myth: ...
- Ukrainian reality: ...

## Contested Terms (if applicable)
| Concept | Imperial framing | Ukrainian framing |
|---------|-----------------|-------------------|
| ...     | ...             | ...               |

## Section-Mapped Research Notes

### {Section 1 from content_outline}
Key facts, dates, sources for this section...

### {Section 2 from content_outline}
...

===RESEARCH_END===
```

### Output Block 2: Meta Outline

```
===META_OUTLINE_START===
content_outline:
  - section: "{Section 1 name in Ukrainian}"
    words: {allocation}
    points:
      - "{key point 1 — informed by research}"
      - "{key point 2}"
  - section: "{Section 2 name}"
    words: {allocation}
    points:
      - "..."
  # ... all sections
  # Total: ~5000 words
===META_OUTLINE_END===
```

### Validation checklist (complete before outputting meta):

- [ ] All section names are Ukrainian
- [ ] Section names match plan structure
- [ ] Each section has `words` and `points`
- [ ] Sum of all `words` ≈ 5000
- [ ] No section has fewer than 200 words
- [ ] Points reflect research findings

---

## Friction Report (MANDATORY)

After both output blocks, include:

```
===FRICTION_START===
**Phase**: Phase A: Research + Meta (Seminar)
**Step**: {what you were doing when friction occurred, or "Full Phase A"}
**Friction Type**: NONE | TOKEN_LIMIT_TRUNCATION | TOOL_REDUNDANCY | SOURCE_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT write lesson content — only research notes and meta outline
- Do NOT generate activities or vocabulary
- Do NOT skip any section from the plan's content_outline
- Do NOT use Russian-language sources
- Do NOT fabricate quotes or dates — if unsure, mark as "[needs verification]"
- Do NOT reference persona names or voice instructions — persona is assigned at content generation time
- Do NOT request skills, delegate to Claude, or skip this phase
