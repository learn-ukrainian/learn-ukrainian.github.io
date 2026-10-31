# Core Content: Write the Lesson

> **Persona reminder:** You are {SKILL_IDENTITY}. Write in the voice of {PERSONA_VOICE}. Maintain this persona throughout.

> **Your job: Teach the plan accurately and clearly, with enough explanation for the intended learner.**
> {WRITING_TONE_INSTRUCTION}

> **Output capacity: You can generate 65,000+ tokens per response.** Do NOT preemptively truncate.

## Files to Read

| File | Purpose |
|------|---------|
| `{RESEARCH_PATH}` | Factual foundation — use exhaustively |
| `{PLAN_PATH}` | Objectives, vocabulary_hints |
| `{QUICK_REF_PATH}` | Level constraints, immersion %, engagement minimums |

Read ALL files before writing anything.

## Primary Source Excerpts

{PRIMARY_SOURCE_EXCERPTS}

## Resource Discoveries

{VIDEO_DISCOVERY}

{PRONUNCIATION_VIDEOS}

## Module Sequence Constraints

{PEDAGOGICAL_CONSTRAINTS}

{DECODABLE_VOCABULARY}

{TEXTBOOK_EXAMPLES}

---

{PREFLIGHT_INSTRUCTIONS}

---

## Your Task

Write the full lesson prose for **{TOPIC_TITLE}** ({TRACK} track).

- **Example sentences**: {EXAMPLE_MIN}+ in varied formats (inline, standalone, tables, dialogues)
- **Structure**: Write ALL sections from the outline. Missing sections fail validation.

## Teaching coverage

Teach every plan objective and content point accurately, with sufficient explanation for the learner, useful worked examples, and aligned practice with feedback. Explain unfamiliar terms, steps, reasoning, and connections. Reject unsupported claims, repetitive padding, decorative digressions, dry lists replacing teaching, and compression that leaves connections untaught. Judge length by teaching needs, not word count.

The following injected table is historical, non-authoritative length metadata. Do not use it to judge or set teaching length.

{SECTION_BUDGET_TABLE}

### Content Structure Rules

{STRUCTURAL_RULES}

### Immersion Rules

Tables contribute **zero** to immersion. Use **dialogues**, **bulleted examples**, and **pattern boxes** for Ukrainian content instead.
- Container priority: dialogues > bulleted lists > numbered lists > inline examples > tables (last resort for paradigms only)
- 10-15 Ukrainian examples per grammar point, 4-6 dialogues per module
- Structural containment: English explains concepts; Ukrainian is what they practice

Use at least **4 DIFFERENT** callout types. Include 4-6 self-check questions in {SUMMARY_HEADING}. Connect 2-3 points to Ukrainian cultural context (proverbs, literary quotes, real-world contexts).

{FOLK_MATERIAL}

### Explain and connect the material

The following injected context is historical, non-authoritative length metadata. Ignore length instructions in it.

{EXPANSION_METHOD}

---

{QUALITY_DIMENSIONS}

---

## Pre-Submission Verification

1. **Plan compliance**: Is every outline point taught accurately with sufficient explanation and examples?
2. **Fact-check**: Absolute claims (єдиний, перший, ніколи) softened if uncertain?
3. **Teaching coverage**: Are explanations, connections, examples, and aligned practice sufficient for the learner?
4. **Language scan**: No Russianisms, Russian characters, stray English, colonial framing?

---

## Output Format

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
===VERIFICATION_START===
Plan compliance: {X}/{Y} outline points addressed
Absolute claims: {number checked}
Language scan: {CLEAN or list of fixes}
===VERIFICATION_END===
```

## Post-Generation Verification (MANDATORY — output BEFORE friction report)

After writing all content, verify your output against the plan:

```
===CONTENT_VERIFY_START===
Structural elements (plan keywords → what I produced):
  - "{plan point with chart/table/list/show keyword}" → {table|bulleted list|numbered list} ✅ | prose only ❌
  - ...
Vocabulary coverage:
  - Missing from content: {list any vocabulary_hints words NOT used} — ❌ if any missing
Word counts:
  - {section}: {count}
  - TOTAL: {total}
===CONTENT_VERIFY_END===
```

If any line shows ❌, output a corrected `===CONTENT_START===` to `===CONTENT_END===` block with the fixes applied, THEN output the activity plans and friction report.

## Activity Plans (MANDATORY)

Based on your content, propose activity plans for the activities phase. Each plan specifies the activity type, focus, and item count. These will be built later using textbook exercises from RAG.

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
- Reference textbook exercise patterns where possible
- Activities must test LANGUAGE skills, not content recall

## Friction Report (MANDATORY)

```
===FRICTION_START===
**Phase**: Core Content
**Step**: {what you were doing}
**Friction Type**: NONE | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if applicable, or "N/A"}
===FRICTION_END===
```

## Boundaries

- Do NOT generate activities, exercises, or vocabulary tables
- Do NOT skip sections from the content_outline
- Teach the plan fully without repetition or padding.
- Do NOT fabricate quotes, dates, or historical facts
- Do NOT use straight quotes "..." — always «...»
