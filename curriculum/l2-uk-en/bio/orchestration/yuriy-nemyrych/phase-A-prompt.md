# Phase A: Meta Outline Only (Research Already Exists)

> **You are Gemini, executing Phase A (meta-only mode) of an optimised rebuild (build_module_v3).**
> **Research is already complete. Your ONLY task: Rebuild the meta outline from the existing research.**

---

## Your Input

Read the **existing research notes** (already complete — do NOT re-research):

```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/bio/research/yuriy-nemyrych-research.md
```

Read the plan file (SOURCE OF TRUTH for structure):

```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/bio/yuriy-nemyrych.yaml
```

Read the current meta file (for reference — you will replace the content_outline):

```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/bio/meta/yuriy-nemyrych.yaml
```

---

## Your Task

**Rebuild** the `content_outline` from scratch using:
- The **plan's section structure** as the skeleton (match section names exactly)
- The **research notes** to inform depth, word allocation, and specific bullet points

The existing meta `content_outline` is likely outdated (wrong section sizes, stale points). Do NOT copy it. Start fresh from the plan + research.

### Rules

- **Do NOT copy the old meta's outline** — rebuild from the plan's section structure
- Allocations must sum to approximately **5000** words (±10% acceptable)
- Minimum section allocation: 200 words (merge smaller sections)
- For modules with target ≥ 4000w, aim for **8-12 sections minimum** — this prevents any one section from consuming a disproportionate share of the module.
- **No single section may consume more than 25% of the total word target.** A 5000w module → max 1250w per section. If a plan section would exceed this, you MUST split it.
- Each section must have `section`, `words`, and `points` fields
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
4. Allocate words based on research depth for each cluster

**Example:** A plan section `Читання` with 14 bullet points should NOT become one 3200w meta section. It should become 4-5 sub-sections of 600-800w each. The bullets tell you what the sub-sections should cover.

---

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

### Output Block: Meta Outline

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

### Validation checklist (complete before outputting):

- [ ] All section names are Ukrainian
- [ ] Section names match plan structure
- [ ] Each section has `words` and `points`
- [ ] Sum of all `words` ≈ 5000
- [ ] No section has fewer than 200 words
- [ ] Points reflect research findings
- [ ] 8-12 sections for ≥ 4000w targets

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
