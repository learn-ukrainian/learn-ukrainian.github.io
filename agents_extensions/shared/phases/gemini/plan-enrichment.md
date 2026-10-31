# Plan Enrichment: Integrate Research into Content Outline

> **You are Gemini, enriching a module plan with research findings.**
> **Your ONLY output: an enriched `content_outline` and `vocabulary_hints` in YAML, wrapped in delimiters.**
> **Do NOT output anything else — no explanations, no commentary, no preamble.**

---

## Input: Current Plan

```yaml
{PLAN_YAML}
```

## Input: Research Findings

```markdown
{RESEARCH_MD}
```

---

## Rules

### Section Structure

- Section names MUST be in Ukrainian (with English subtitle in parentheses): `"Вступ (Introduction)"`
- Sections should follow a natural pedagogical flow: introduction → presentation → practice → production/summary

### What to Enrich from Research

1. **Cultural hooks** found in research → become dedicated subsection points or section motivators. Add specific cultural references, not generic ones.
2. **Learner errors** documented in research → become explicit drill/practice points with correction patterns. Include the wrong form AND the correct form.
3. **Vocabulary frequency data** from research → inform `vocabulary_hints` (add collocations, frequency notes, register markers).
4. **Cross-references** mentioned in research → ensure `prerequisites` / `connects_to` in plan match what research discovered. Note these in section points where relevant.
5. **State Standard references** from research → add as explicit points where the Standard mandates specific competencies.

### What NOT to Change

Do NOT modify ANY of these fields — they are immutable:
- `slug`, `title`, `subtitle`, `module`, `level`, `sequence`, `version`
- `focus`, `pedagogy`, `prerequisites`, `connects_to`, `objectives`, `grammar`
- `module_type`, `sources`, `immersion`, `phase`, `persona`, `register`
- `word_target` (deprecated compatibility metadata with no teaching authority)

PRESERVE all existing `activity_hints` (you may add more if research suggests gaps, but never remove existing ones).

### Section Point Quality

Each section point should be specific and actionable, not vague:
- BAD: "Common errors with dative case"
- GOOD: "Learner error: confusing «Дякую тебе» (Acc) with correct «Дякую тобі» (Dat) — drill with 3 minimal pairs"

Each point should specify enough detail for a writer to teach it accurately, explain its connections, and choose useful examples.

### Output Format

Output EXACTLY this structure, with no text before or after the delimiters:

===ENRICHED_OUTLINE_START===
content_outline:
- section: "Вступ (Introduction)"
  words: 400  # Deprecated compatibility metadata; no teaching authority
  points:
  - "Point 1 with specific detail from research"
  - "Point 2 referencing cultural hook or learner error"
- section: "Презентація (Presentation)"
  words: 600  # Deprecated compatibility metadata; no teaching authority
  points:
  - "..."
===ENRICHED_OUTLINE_END===

===ENRICHED_VOCAB_START===
vocabulary_hints:
  required:
  - "word (translation) — collocations; frequency/usage notes"
  recommended:
  - "word (translation) — usage notes"
===ENRICHED_VOCAB_END===

### Critical Reminders

- Every section MUST have at least 2 `points`
- Points MUST be strings (quoted YAML), not nested structures
- If the research adds nothing new beyond what the plan already has, output the existing outline with proper Ukrainian section names and existing deprecated `words` metadata — do NOT fabricate content
- Use YAML block scalars or quoted strings for long points containing special characters
