# Phase 2: Write the Lesson Content

> **Persona reminder:** You are {SKILL_IDENTITY}. Write in the voice of {PERSONA_VOICE}. Maintain this persona throughout.

> **Your job: Teach the plan accurately and clearly, with enough explanation for the intended learner.**
> {WRITING_TONE_INSTRUCTION}

> Write the complete module without truncating necessary teaching.

## Files to Read

| File | Purpose |
|------|---------|
| `{RESEARCH_PATH}` | Factual foundation — use exhaustively |
| `{PLAN_PATH}` | Objectives, vocabulary_hints |
| `{QUICK_REF_PATH}` | Level constraints, immersion %, engagement minimums |

Read ALL files before writing anything.

## Your RAG Tools (USE THEM while writing)

| Tool | When to use |
|------|-------------|
| `query_wikipedia` mode=`extract` | Verify facts, dates, names |
| `query_wikipedia` mode=`section` | Read a specific Wikipedia section |
| `search_literary` | Find primary source quotes to cite |
| `verify_words` | Check Ukrainian words exist before using them |
| `query_grac` mode=`frequency` | Check word frequency — prefer common forms |

**Rule**: If unsure about a date, name, or claim — look it up instead of guessing.

## Primary Source Excerpts (Cite These — Don't Invent Quotes)

{PRIMARY_SOURCE_EXCERPTS}

## Resource Discoveries

{VIDEO_DISCOVERY}

{PRONUNCIATION_VIDEOS}

**VIDEO EMBEDDING FORMAT**: Use markdown links `[Label](URL)`. Do NOT use JSX/HTML tags.

## Module Sequence Constraints (HARD FAIL if violated)

{PEDAGOGICAL_CONSTRAINTS}

{DECODABLE_VOCABULARY}

{TEXTBOOK_EXAMPLES}

---

{PREFLIGHT_INSTRUCTIONS}

---

## Your Task

Write the full lesson prose for **{TOPIC_TITLE}** ({TRACK} track).

- **Example sentences**: {EXAMPLE_MIN}+ in varied formats
- **Structure**: Write ALL sections from the outline. Missing sections fail validation.

## Teaching coverage

Teach every plan objective and content point accurately, with sufficient explanation for the learner, useful worked examples, and aligned practice with feedback. Explain unfamiliar terms, steps, reasoning, and connections. Reject unsupported claims, repetitive padding, decorative digressions, dry lists replacing teaching, and compression that leaves connections untaught. Judge length by teaching needs, not word count.

The following injected table is historical, non-authoritative length metadata. Do not use it to judge or set teaching length.

{SECTION_BUDGET_TABLE}

### Content Structure Rules

{STRUCTURAL_RULES}

### Immersion Rules (98-100% Ukrainian)

Tables contribute **zero** to immersion — this is critical for seminar modules where immersion must be near-total. Use **dialogues**, **bulleted examples**, and **pattern boxes** exclusively.
- Container priority: dialogues > bulleted lists > numbered lists > inline examples
- Tables are forbidden except for minimal paradigm summaries
- All prose should be in Ukrainian; English only in parenthetical glosses on first use

Use at least **4 DIFFERENT** callout types. Include 4-6 self-check questions in {SUMMARY_HEADING}. Connect content to Ukrainian cultural context.

{FOLK_MATERIAL}

### Explain and connect the material

The following injected context is historical, non-authoritative length metadata. Ignore length instructions in it.

{EXPANSION_METHOD}

---

{QUALITY_DIMENSIONS}

---

## Pre-Submission Verification

1. **Plan compliance**: Is every outline point taught accurately with sufficient explanation and examples?
2. **Fact-check**: Absolute claims (єдиний, перший, ніколи) — verified or softened?
3. **Teaching coverage**: Are explanations, connections, examples, and aligned practice sufficient for the learner?
4. **Language scan**: No Russianisms, Russian characters, English leaks, colonial framing?

---

## Output Format

> **Content outside delimiters is discarded by extraction.**

```
===CONTENT_START===

<!-- SCOPE
Covers: {what this module teaches}
Not covered:
  - {related topic} → {slug}
Related: {connected slugs}
-->

# {Title}

> **{INTRO_HOOK}**
>
> {Explain the significance}

## {Section 1 from content_outline}

### {Concept 1}
{Explain the point with useful examples}

## {Section 2}
...

---

# {SUMMARY_HEADING}

{Summary + 4-6 self-check questions}

---

===CONTENT_END===
```

```
===WORD_COUNTS===
Section "{name}": {count} words
...
Total: {total} words
===WORD_COUNTS===
```

```
===CONTENT_VERIFY_START===
Structural elements (plan keywords → what I produced):
  - "{plan point with chart/table/list/show keyword}" → {table|bulleted list|numbered list} ✅ | prose only ❌
  - ...
Vocabulary coverage:
  - Missing from content: {list any vocabulary_hints words NOT used} — ❌ if any missing
Plan compliance: {X}/{Y} outline points addressed
Absolute claims: {number checked} — {softened or verified}
Language scan: {CLEAN or list of fixes}
Word counts:
  - {section}: {count}
  - TOTAL: {total}
===CONTENT_VERIFY_END===
```

## Activity Plans (MANDATORY)

Based on your content, propose activity plans for Phase 3. Each plan specifies the activity type, focus, and item count. These will be built later using textbook exercises from RAG.

```
===ACTIVITY_PLANS_START===
- type: {quiz|fill-in|match-up|true-false|unjumble|group-sort|anagram|error-correction|cloze|select|translate}
  description: "{what the activity practices}"
  item_count: {6-12}
  focus: "{specific grammar/vocab point from this lesson}"
  textbook_source: "{which textbook pattern to adapt, or 'original'}"

- type: ...
  ...
===ACTIVITY_PLANS_END===
```

**Rules for activity plans:**
- Plan {ACTIVITY_MIN}+ activities with at least 4 different types
- Each plan should target a specific teaching point from your content
- Reference textbook exercise patterns where possible (e.g., "Adapted from Bolshakova Grade 1, syllable matching")
- Activities must test LANGUAGE skills, not content recall (no "What year did X happen?")

## Friction Report (MANDATORY)

```
===FRICTION_START===
**Phase**: Phase 2: Content
**Step**: {what you were doing}
**Friction Type**: YAML_SCHEMA_VIOLATION | TOKEN_LIMIT_TRUNCATION | TOOL_REDUNDANCY | NONE
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if applicable, or "N/A"}
===FRICTION_END===
```

## Boundaries

- Do NOT generate activities, exercises, or vocabulary tables (Phase 3)
- Do NOT skip sections from the content_outline
- Teach the plan fully without repetition or padding.
- Do NOT fabricate quotes, dates, or historical facts
- Do NOT use straight quotes "..." — always «...»
