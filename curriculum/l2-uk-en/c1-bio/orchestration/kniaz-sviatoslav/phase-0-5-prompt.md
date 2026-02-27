# Phase 0.5: Plan Enrichment from Research

> **You are Gemini, executing Phase 0.5 of an orchestrated rebuild.**
> **Your ONLY task: Enrich the plan's content_outline and vocabulary_hints using findings from the research file.**

## Your Input

Read the research file:

```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/c1-bio/research/kniaz-sviatoslav-research.md
```

Read the plan file:

```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/c1-bio/kniaz-sviatoslav.yaml
```

## Rules

<critical>

- **NEVER** add `words:`, `word_target:`, or `word_count:` fields to the plan
- **NEVER** remove or rename existing sections — preserve `section:` names exactly
- **NEVER** remove existing points — only expand them with specificity
- **NEVER** change `objectives`, `prerequisites`, `grammar`, `connects_to`, `activity_hints`, `focus`, `pedagogy`, `register`, `persona`, or any other top-level fields
- **NEVER** add new sections that don't exist in the original plan
- Preserve YAML structure exactly (`content_outline` is a list of section objects with `section:` and `points:`)
- Each enriched point must be a single YAML string (quote with double quotes if it contains colons)

</critical>

## What to Enrich

You are making existing plan points more **specific and actionable** by integrating research findings. Do NOT rewrite the plan — ADD specificity to what's already there.

### For Core Tracks (A1, A2, B1, B2, C1, C2, PRO)

From the research file, extract and map to relevant section points:

1. **Vocabulary collocations** — Add high-frequency collocations from frequency tables to `vocabulary_hints` as comments
2. **Cultural hooks** — Append cultural context to relevant section points (e.g., `— cultural hook: ...`)
3. **Common learner errors** — Append error warnings to relevant section points (e.g., `— learner error: ...`)
4. **Content writing notes** — Integrate specific teaching suggestions into section points
5. **State Standard references** — Note relevant standard alignment in section points where applicable

### For Seminar Tracks (HIST, ISTORIOHRAFIIA, C1-BIO, LIT, OES, RUTH)

From the research file, extract and map to relevant sections:

1. **Key dates/chronology** — Add specific dates and events to relevant section points
2. **Primary quotes** — Note which sections should include which quotes (e.g., `— include quote from [source]`)
3. **Decolonization angles** — Add decolonial framing to relevant section points
4. **Engagement hooks** — Map specific hooks (`[!myth-buster]`, `[!why-it-matters]`, etc.) to sections
5. **Source references** — Note which sections should cite which sources

### Enrichment Style

**Before** (generic):
```yaml
- "Близька родина (батьки, діти, брати, сестри)"
```

**After** (enriched with research):
```yaml
- "Близька родина (батьки, діти, брати, сестри) — конструкція «У мене є...» як основний спосіб; learner error: чоловік = man AND husband"
```

The enriched point keeps the original content and appends research-informed specificity after a dash.

## Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded by the extraction pipeline.

Output ONLY the enriched `content_outline` and `vocabulary_hints` sections in valid YAML:

```
===ENRICHMENT_START===
content_outline:
  - section: "{exact section name from plan}"
    points:
      - "{enriched point 1}"
      - "{enriched point 2}"
  - section: "{next exact section name}"
    points:
      - "{enriched point}"

vocabulary_hints:
  required:
    - "{word} ({translation}) — {collocations or usage notes from research}"
  recommended:
    - "{word} ({translation}) — {collocations or usage notes from research}"
===ENRICHMENT_END===
```

**Important**: Every section from the original plan must appear in your output, even if you have nothing to add — just reproduce its points unchanged. This ensures the merge logic works correctly.

## Friction Report (MANDATORY)

After your enrichment output, include:

```
===FRICTION_START===
**Phase**: Phase 0.5: Plan Enrichment
**Step**: {what you were doing when friction occurred, or "Full enrichment"}
**Friction Type**: NONE | RESEARCH_TOO_THIN | SECTION_MISMATCH | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if a script/design issue, or "N/A"}
===FRICTION_END===
```

## Boundaries

- Do NOT write lesson content — only enrich plan points
- Do NOT generate activities or vocabulary YAML
- Do NOT add new sections to the outline
- Do NOT change the plan's top-level structure
- Do NOT reference persona names or voice instructions
- Do NOT add word counts or word targets
