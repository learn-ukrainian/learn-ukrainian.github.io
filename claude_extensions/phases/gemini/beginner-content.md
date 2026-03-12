# Beginner Content: Write the Lesson

> **Persona reminder:** You are {SKILL_IDENTITY}. Write in the voice of {PERSONA_VOICE}.

> **Your task: Write approximately {WORD_TARGET} words of clear, beginner-friendly content.**
> {WRITING_TONE_INSTRUCTION}

> **Output capacity: You can generate 65,000+ tokens per response.** Do NOT preemptively truncate.

## Files to Read

| File | Purpose |
|------|---------|
| `{RESEARCH_PATH}` | Research notes |
| `{PLAN_PATH}` | Content outline, section word allocations, vocabulary_hints |
| `{QUICK_REF_PATH}` | Level constraints, immersion % |

Read ALL files before writing.

## Target Vocabulary (MANDATORY)

{VOCABULARY_HINTS}

**Rules:**
- Teach all target vocabulary words listed above. These must appear in your content with clear context.
- For the rest of the text, use natural, level-appropriate Ukrainian guided by the textbook excerpts below.
- Match the syntactic complexity and vocabulary level of the provided textbook excerpts.

## Resource Discoveries

{VIDEO_DISCOVERY}

{PRONUNCIATION_VIDEOS}

{TEXTBOOK_EXAMPLES}

## Module Constraints (HARD FAIL if violated)

{PEDAGOGICAL_CONSTRAINTS}

{CHECKPOINT_GUIDANCE}

---

{PREFLIGHT_INSTRUCTIONS}

---

## Writing Instructions

Write the lesson prose for **{TOPIC_TITLE}** ({TRACK} track).

**Structure**: Use the EXACT H2 section titles listed below. Missing or renamed sections fail validation.

{EXACT_SECTION_TITLES}

### Immersion Target

{IMMERSION_RULE}

### Structural Containment (how to achieve immersion without code-switching)

1. **Paragraphs = English** with Ukrainian vocabulary **bolded inline**: "The word **книга** (book) is feminine."
2. **Full Ukrainian sentences = structural containers only** (tables, bulleted example lists, blockquote dialogues, pattern boxes) — never in flowing prose paragraphs.
3. **Vary containers.** Never use the same container type twice in a row.

### Writing Style

Write for someone seeing Ukrainian for the first time. English explains; Ukrainian is what they're learning. Keep paragraphs short (3-5 sentences). Do NOT use abstract Ukrainian grammar terminology unless the plan explicitly teaches those terms.

### Section Word Budgets

{SECTION_BUDGET_TABLE}

### Callout Types to Use

- `[!tip]` — practical advice for learners
- `[!warning]` — visual traps, common mistakes
- `[!did-you-know]` — fun facts about Ukrainian
- `[!culture]` — cultural connections

---

{QUALITY_DIMENSIONS}

---

## Boundaries

- Do NOT generate activities or vocabulary tables (separate phase)
- Do NOT add vocabulary outside the plan's vocabulary_hints
- **VOCABULARY COVERAGE RULE:** All words from `vocabulary_hints` must appear at least once in the module content.
- Do NOT skip sections from the content_outline
- Do NOT use straight quotes "..." — always «...»

---

## Output Format

```
===CONTENT_START===

<!-- SCOPE
Covers: {what this module teaches}
Not covered:
  - {related topic} → {slug}
-->

# {Title}

> **{INTRO_HOOK}**
>
> {2-3 sentences}

## {Section 1}
...

---

# {SUMMARY_HEADING}

{Summary + 3-4 self-check questions. Each question MUST include an English translation if the question is in Ukrainian.}

---

===CONTENT_END===
```

```
===WORD_COUNTS===
Section "{name}": {count} words (minimum: {allocation})
...
Total: {total} words (target: {WORD_TARGET})
===WORD_COUNTS===
```

## Friction Report (MANDATORY)

```
===FRICTION_START===
**Phase**: Beginner Content
**Step**: {what you were doing}
**Friction Type**: NONE | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if applicable, or "N/A"}
===FRICTION_END===
```
