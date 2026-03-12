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
| `{PLAN_PATH}` | Objectives, vocabulary_hints |
| `{QUICK_REF_PATH}` | Level constraints, immersion % |

Read ALL files before writing.

## Resource Discoveries

{VIDEO_DISCOVERY}

{PRONUNCIATION_VIDEOS}

## Module Constraints (HARD FAIL if violated)

{PEDAGOGICAL_CONSTRAINTS}

{DECODABLE_VOCABULARY}

**Target vocabulary** (from the plan — you MUST teach and use these words heavily):

{VOCABULARY_HINTS}

**Rules:**
- Teach all target vocabulary words listed above. These must appear in your content with clear context.
- For the rest of the text, use natural, level-appropriate Ukrainian guided by the textbook excerpts below.
- Match the syntactic complexity, sentence length, and vocabulary level of the provided textbook excerpts. Do not exceed their lexical density.
- When textbook excerpts contain vocabulary or grammar not yet taught at this level, simplify or provide an English gloss in parentheses.

NOTE: The textbook examples below are provided as INSPIRATION for the pedagogical approach, NOT as content to copy. For modules M15+, focus on the communicative patterns, not the letter/syllable exercises.

{TEXTBOOK_EXAMPLES}

{CHECKPOINT_GUIDANCE}

---

## Writing Instructions

Write the lesson prose for **{TOPIC_TITLE}** ({TRACK} track).

- **Target**: {WORD_TARGET}–{WORD_CEILING} words (below {WORD_TARGET} = FAIL, above {WORD_CEILING} = overproduction that increases error surface)
- **Engagement callouts**: **{ENGAGEMENT_MIN}+ MANDATORY** — spread across sections, at least 3 different types. Content with fewer than {ENGAGEMENT_MIN} callout boxes (> [!tip], > [!warning], etc.) FAILS validation.
- **Structure**: Use the EXACT H2 section titles listed below. Missing or renamed sections fail validation.

{EXACT_SECTION_TITLES}

### Immersion Target

{IMMERSION_RULE}

### Structural Containment (how to achieve immersion without code-switching)

**Three rules govern where each language appears:**

1. **Paragraphs = English** with Ukrainian vocabulary **bolded inline**: "The word **книга** (book) is feminine." Short phrases and grammatical fragments (e.g., comparing **Я йду** vs **Я іду**) may appear inline.

2. **Full Ukrainian sentences = structural containers only.** Any Ukrainian sentence (3+ words with a verb) must go in one of these containers — never in flowing prose paragraphs:
   - **Tables** — paradigms, vocabulary groups, gender sorting (highest immersion density)
   - **Bulleted example lists** — Ukrainian line + English gloss: `- **Читай книгу!** — Read the book!`
   - **Blockquote dialogues** — mini-conversations with labeled speakers
   - **Pattern boxes** — transformations: `читати → читай → читайте`

3. **Vary containers.** Never use the same container type twice in a row. Alternate between tables, example lists, dialogues, and pattern boxes to keep the rhythm natural.

### Writing Style

Write for someone seeing Ukrainian for the first time. English explains; Ukrainian is what they're learning.

Follow the structural containment rules above. In each section:
1. **Explain** the concept in an English paragraph (with Ukrainian vocabulary bolded inline)
2. **Show** the pattern in a Ukrainian structural container (table, example list, dialogue, or pattern box)
3. **Reinforce** with a callout box (tip, warning, culture note, or fun fact)

Keep paragraphs short (3-5 sentences). Do NOT use abstract Ukrainian grammar terminology (іменник, дієслово, відмінок, прикметник) — students don't know these yet. Exception: terms the plan explicitly teaches (e.g., голосні, приголосні, букви, звуки for alphabet modules) — always introduce English-first with Ukrainian in parentheses. Do NOT write IPA or Latin transliteration.

### Section Word Budgets

{SECTION_BUDGET_TABLE}

### Callout Types to Use

- `[!tip]` — practical advice for learners
- `[!warning]` — visual traps, common mistakes
- `[!did-you-know]` — fun facts about Ukrainian
- `[!culture]` — cultural connections

### Audit Gates (your content will be checked for)

- **Word count**: minimum {WORD_TARGET} words
- **Russianisms**: banned (кушати, получати, etc.)
- **Russian characters**: ы, э, ё, ъ must NEVER appear
- **Euphony**: і/й, у/в alternation
- **Engagement callouts**: {ENGAGEMENT_MIN}+
- **IPA/phonetic brackets**: BANNED

{SHARED_CONTENT_RULES}

---

## Pre-Submission Checks

1. **Plan compliance**: Does every point in the content_outline have dedicated prose?
2. **Word count**: Does the total meet {WORD_TARGET}?
3. **Language scan**: No Russianisms, no Russian characters, no IPA, no Latin transliteration?
4. **Decodable vocabulary**: Does every Ukrainian word use only the allowed letter set?
5. **Target vocabulary**: Are all target vocabulary words used in the content?

{SELF_AUDIT_SNIPPET}

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

{Summary + 3-4 self-check questions. Each question MUST include an English translation if the question is in Ukrainian. Format: "Який? (Which?) — answer / відповідь"}

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

## Boundaries

- Do NOT generate activities or vocabulary tables (separate phase)
- Do NOT add vocabulary outside the plan's vocabulary_hints
- **VOCABULARY COVERAGE RULE:** All words from `vocabulary_hints` in the plan MUST appear at least once in the module content. Vocabulary listed but never used in the prose is a validation failure.
- Do NOT skip sections from the content_outline
- Do NOT write fewer than {WORD_TARGET} words
- Do NOT use straight quotes "..." — always «...»
