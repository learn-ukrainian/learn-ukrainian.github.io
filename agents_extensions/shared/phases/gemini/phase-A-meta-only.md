# Phase A: Meta Outline Only (Research Already Exists)

> **You are Gemini, executing Phase A (meta-only mode) of an optimised rebuild (build_module).**
> **Research is already complete. Your ONLY task: Rebuild the meta outline from the existing research.**

---

## Your Input

Read the **existing research notes** (already complete — do NOT re-research):

```
{RESEARCH_PATH}
```

Read the plan file (SOURCE OF TRUTH for structure):

```
{PLAN_PATH}
```

---

## Your Task

**Rebuild** the `content_outline` from scratch using:
- The **plan's section structure** as the skeleton (match section names exactly)
- The **research notes** to inform depth and specific bullet points

The existing meta `content_outline` is likely outdated (stale teaching points). Do NOT copy it. Start fresh from the plan + research.

### Rules

- **Do NOT copy the old meta's outline** — rebuild from the plan's section structure
- Organize sections around the teaching points and their connections.
- Each section must have `section`, `words`, and `points` fields. The numeric `words` field is deprecated compatibility metadata and has no teaching authority.
- Section names must be in Ukrainian (these become H2 headings in the lesson)
- **Section names must match plan exactly** — if the plan has a `content_outline` with section names,
  use those EXACT names (or very close Ukrainian equivalents). When splitting a large plan section,
  add a subtitle (e.g. "Читання: I — Походження").
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
4. Explain the evidence and teaching purpose for each cluster

**Example:** Organize the plan section `Читання` and its bullet points into subsections when that helps learners follow the material.

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block: Meta Outline

```
===META_OUTLINE_START===
content_outline:
  - section: "{Section 1 name in Ukrainian}"
    words: {allocation}  # Deprecated compatibility metadata; no teaching authority
    points:
      - "{key point 1 — informed by research}"
      - "{key point 2}"
  - section: "{Section 2 name}"
    words: {allocation}  # Deprecated compatibility metadata; no teaching authority
    points:
      - "..."
  # ... all sections
===META_OUTLINE_END===
```

### Validation checklist (complete before outputting):

- [ ] All section names are Ukrainian
- [ ] Section names match plan structure
- [ ] Each section has `words` and `points`
- [ ] Points reflect research findings
- [ ] Every plan point has an appropriate place in the outline

---

## Friction Report (MANDATORY)

After the meta outline output, include:

```
===FRICTION_START===
**Phase**: Phase A: Meta Outline Only (research-exists mode)
**Step**: {what you were doing when friction occurred, or "Full meta outline"}
**Friction Type**: NONE | TOKEN_LIMIT_TRUNCATION | TOOL_REDUNDANCY | SOURCE_NOT_FOUND | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

---

## Boundaries

- Do NOT re-research — use only the provided research file
- Do NOT write lesson content — only the meta outline
- Do NOT generate activities or vocabulary
- Do NOT skip any section from the plan's content_outline
- Do NOT reference persona names or voice instructions
- Do NOT request skills, delegate to Claude, or skip this phase
