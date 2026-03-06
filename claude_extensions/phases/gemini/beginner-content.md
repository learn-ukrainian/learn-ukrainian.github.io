# Beginner Content: Write the Lesson

> **Persona reminder:** You are {SKILL_IDENTITY}. Write in the voice of {PERSONA_VOICE}.

> **Your task: Write approximately {WORD_TARGET} words of clear, beginner-friendly content.**
> {WRITING_TONE_INSTRUCTION}

> **Output capacity: You can generate 65,000+ tokens per response.** Do NOT preemptively truncate.

## Files to Read

| File | Purpose |
|------|---------|
| `{RESEARCH_PATH}` | Research notes |
| `{META_PATH}` | Content outline with section word allocations |
| `{PLAN_PATH}` | Objectives, vocabulary_hints |
| `{QUICK_REF_PATH}` | Level constraints, immersion % |

Read ALL files before writing.

## Resource Discoveries

{VIDEO_DISCOVERY}

{PRONUNCIATION_VIDEOS}

## Module Constraints (HARD FAIL if violated)

{PEDAGOGICAL_CONSTRAINTS}

{DECODABLE_VOCABULARY}

{LEXICAL_SANDBOX}

NOTE: The textbook examples below are provided as INSPIRATION for the pedagogical approach, NOT as content to copy. For modules M15+, focus on the communicative patterns, not the letter/syllable exercises.

{TEXTBOOK_EXAMPLES}

{CHECKPOINT_GUIDANCE}

---

## Writing Instructions

Write the lesson prose for **{TOPIC_TITLE}** ({TRACK} track).

- **Target**: {WORD_TARGET}–{WORD_CEILING} words (below {WORD_TARGET} = FAIL, above {WORD_CEILING} = overproduction that increases error surface)
- **Immersion**: {IMMERSION_RULE}
- **Engagement callouts**: **{ENGAGEMENT_MIN}+ MANDATORY** — spread across sections, at least 3 different types. Content with fewer than {ENGAGEMENT_MIN} callout boxes (> [!tip], > [!warning], etc.) FAILS validation.
- **Structure**: Use the EXACT H2 section titles listed below. Missing or renamed sections fail validation.

{EXACT_SECTION_TITLES}

### Beginner Writing Style

Write for someone seeing Ukrainian for the first time. English is the scaffolding language — use it for explanations, instructions, and context. Ukrainian is the target content — letters, words, phrases being taught.

**Do this:**
- Introduce each new letter/word clearly with its sound and meaning
- Use tables to show letter-sound mappings
- Give real Ukrainian words as examples (from the decodable vocabulary only)
- Keep paragraphs short (3-5 sentences)
- Use callout boxes for tips, fun facts, and warnings about visual traps

**Do NOT do this:**
- Use Ukrainian grammar terminology (іменник, дієслово, голосний, приголосний) — students don't know these yet
- Write long paragraphs of linguistic analysis
- Include IPA transcriptions or phonetic brackets
- Use vocabulary from future modules
- Create practice sentences if the constraints say "no sentences"
- Repeat the same Ukrainian phrase pattern more than twice (e.g. don't write "Це склад", "Це слово", "Це правило" in every paragraph — vary your immersion: use contextual labels like "Наприклад — For example", section bridges like "А тепер — And now", vocabulary callouts, or short dialogue snippets)

### Example of Good A1 Content (letter introduction)

```markdown
## Meet the Letters

### А — The Familiar One

The first letter is easy: **А** looks exactly like English A and makes the same sound — /a/ as in "father."

You'll find А in some of the first words you learn:

| Word | Meaning |
|------|---------|
| **мА́ма** | mom |
| **сУ́ма** | sum, amount |

[!tip]
> А is one of the "true friends" — letters that look AND sound the same in both alphabets. Enjoy these while they last!

### Н — The First Visual Trap

Here's where it gets interesting: **Н** looks like English H, but it's actually the /n/ sound.

This is a "visual trap" — your brain sees H and wants to say "h", but in Ukrainian it's always /n/.

| Word | Meaning |
|------|---------|
| **нам** | to us |
| **луна́** | echo |
```

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
