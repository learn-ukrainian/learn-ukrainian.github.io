# Phase A: Research + Meta (Professional Track)

> **You are Gemini, executing Phase A of an optimised rebuild (build_module_v3).**
> **This is a combined Phase 0 + Phase 1. Your ONLY task: Research the professional topic AND produce the meta outline in one pass.**

---

## Your Input

Read the plan file (SOURCE OF TRUTH):

```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/c1-pro/industry-integration.yaml
```

Read the current meta file (for reference — you will replace the content_outline):

```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-pro/meta/industry-integration.yaml
```

---

## PART 1: Professional Research

Research **Інтеграція: Галузева практика** for the **c1-pro** professional track. Produce structured research notes that will drive authentic, professionally accurate content in Phase B.

### Research Requirements

1. **Sources**: Find 3+ Ukrainian-language professional/official sources. Priority order:
   - `zakon.rada.gov.ua` — Ukrainian legislation and legal norms
   - `dstu.ua`, `kharkiv.dstu.ua` — ДСТУ standards for professional language
   - `business.diia.gov.ua`, `msp.gov.ua` — official business guidance
   - Ukrainian professional publications, industry associations, university resources
   - Russian-language sources are PROHIBITED.

2. **Terminology Inventory**: Build a table of 8+ key professional terms for this topic:
   - Ukrainian standard form (as per ДСТУ/official norms)
   - Common Russified/non-standard variant used in practice (if exists)
   - English equivalent
   - Usage context (formal written / spoken / legal / technical)

3. **Language Norms**: Identify relevant ДСТУ standards or official language guidelines that apply to this professional domain. Note specific rules (e.g. ДСТУ 4163:2020 for business documents).

4. **Authentic Examples**: Collect 3+ short authentic Ukrainian professional text fragments:
   - Email phrases, document clauses, meeting formulas, report templates, etc.
   - Must be sourced from real Ukrainian professional practice (not invented)
   - Ukrainian only — no Russian examples

5. **Common Errors**: Identify 5+ language mistakes Ukrainian speakers make in this professional context:
   - Russianisms carried over from Soviet-era professional language
   - Calques from Russian professional terminology
   - Register mismatches (using colloquial forms in formal contexts)
   - With correct Ukrainian alternative for each error

6. **Engagement Hooks**: Identify 4+ hooks mapped to specific content sections:
   - `[!pro-tip]` — Professional insider tips
   - `[!language-note]` — Ukrainian vs Russified form, with explanation
   - `[!example]` — Authentic workplace example
   - `[!common-error]` — Frequent mistake with correction
   - `[!context]` — Professional/cultural context

7. **Section-Mapped Notes**: Structure your notes with headings that match the `content_outline` sections from the plan. This makes Phase B content writing mechanical.

---

## PART 2: Meta Outline

After completing research, rebuild the `content_outline` using:
- The plan's section structure as skeleton
- Your research notes to inform depth, authentic examples, and word allocation

### Rules for Meta Outline

- **Do NOT copy the old meta's outline** — rebuild from the plan's section structure
- Allocations must sum to approximately **4000** words (±10% acceptable)
- Minimum section allocation: 200 words (merge smaller sections)
- **No single section may consume more than 25% of the total word target**
- Each section must have `section`, `words`, and `points` fields
- Section names must be in Ukrainian (these become H2 headings in the lesson)
- **Section names must match plan exactly** — use EXACT names from plan (or close Ukrainian equivalents). When splitting a large plan section, add a subtitle.
- Points must reference specific professional terms, authentic examples, or language norms from your research

### How to split a plan section

**The plan's bullet points are section topics, not sub-bullets.** A plan section with 8+ bullet points should become 3-4 meta sections.

**Process:**
1. Count the bullet points in each plan section
2. If a section has 5+ bullets: group them into thematic clusters of 2-4 bullets
3. Each cluster becomes its own meta section with the parent name as prefix

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block 1: Research Notes

```
===RESEARCH_START===

# Дослідження: Інтеграція: Галузева практика

## Використані джерела
1. [Source name](URL) — brief description
2. ...
3. ...

## Термінологічна база

| Українська (норма) | Русизм/ненорма | English | Контекст вживання |
|--------------------|---------------|---------|-------------------|
| ...                | ...           | ...     | ...               |

## Мовні норми та стандарти
- ДСТУ / official norm reference: ...
- Key rule 1: ...
- Key rule 2: ...

## Аутентичні приклади
1. [Context]: «Ukrainian professional text fragment»
2. ...
3. ...

## Типові помилки
1. ❌ [wrong form] → ✅ [correct form] — explanation
2. ...
3. ...
4. ...
5. ...

## Engagement Hooks (mapped to sections)
- Section "{section_name}": [!hook_type] — description
- ...

## Section-Mapped Research Notes

### {Section 1 from content_outline}
Key terminology, authentic examples, norms for this section...

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
      - "{key point 1 — grounded in research}"
      - "{key point 2}"
  - section: "{Section 2 name}"
    words: {allocation}
    points:
      - "..."
  # ... all sections
  # Total: ~4000 words
===META_OUTLINE_END===
```

### Validation checklist (complete before outputting meta):

- [ ] All section names are Ukrainian
- [ ] Section names match plan structure
- [ ] Each section has `words` and `points`
- [ ] Sum of all `words` ≈ 4000
- [ ] No section has fewer than 200 words
- [ ] Points reference specific terminology/examples from research

---

## Friction Report (MANDATORY)

After both output blocks, include:

```
===FRICTION_START===
**Phase**: Phase A: Research + Meta (Professional)
**Step**: {what you were doing when friction occurred, or "Full Phase A"}
**Friction Type**: NONE | TOKEN_LIMIT_TRUNCATION | SOURCE_NOT_FOUND | ...
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
- Do NOT invent professional examples — source them from real Ukrainian practice
- Do NOT use invented ДСТУ numbers — only cite standards you can verify
- Do NOT request skills, delegate to Claude, or skip this phase
