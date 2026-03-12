# Phase 2: Write the Lesson Content

> **Persona reminder:** You are {SKILL_IDENTITY}. Write in the voice of {PERSONA_VOICE}. Maintain this persona throughout.

> **Your #1 job: Write approximately {WORD_TARGET} words of clear, well-structured Ukrainian content.**
> {WRITING_TONE_INSTRUCTION}

> **Output capacity: You can generate 65,000+ tokens per response.** A {WORD_TARGET}-word module is ~{WORD_TARGET_TOKENS}K tokens — well within your single-turn limit. Do NOT preemptively truncate.

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

### Section Word Budgets

{SECTION_BUDGET_TABLE}

### Content Structure Rules

{STRUCTURAL_RULES}

Use at least **4 DIFFERENT** callout types. Include 4-6 self-check questions in {SUMMARY_HEADING}. Connect content to Ukrainian cultural context.

{FOLK_MATERIAL}

### How to Hit {WORD_TARGET} Words

{EXPANSION_METHOD}

---

{QUALITY_DIMENSIONS}

---

## Pre-Submission Verification

1. **Plan compliance**: Every outline point → dedicated prose (50-100+ words)?
2. **Fact-check**: Absolute claims (єдиний, перший, ніколи) — verified or softened?
3. **Section word counts**: No section below 70% of budget? Total meets {WORD_TARGET}?
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
> {2-3 sentences of significance}

## {Section 1 from content_outline}

### {Concept 1}
{{H3_WORD_RANGE} words}

## {Section 2}
...

---

# {SUMMARY_HEADING}

{Summary + 4-6 self-check questions (~200 words)}

---

===CONTENT_END===
```

```
===WORD_COUNTS===
Section "{name}": {count} words (minimum: {allocation})
...
Total: {total} words (target: {WORD_TARGET}, ratio: {total/WORD_TARGET}x)
===WORD_COUNTS===
```

```
===VERIFICATION_START===
Plan compliance: {X}/{Y} outline points addressed
Absolute claims: {number checked} — {softened or verified}
Language scan: {CLEAN or list of fixes}
===VERIFICATION_END===
```

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
- Do NOT write fewer than {WORD_TARGET} words or more than 150%
- Do NOT fabricate quotes, dates, or historical facts
- Do NOT use straight quotes "..." — always «...»
