# Core Content: Write the Lesson

> **Persona reminder:** You are {SKILL_IDENTITY}. Write in the voice of {PERSONA_VOICE}. Maintain this persona throughout.

> **Your #1 job: Write approximately {WORD_TARGET} words of clear, well-structured Ukrainian content.**
> {WRITING_TONE_INSTRUCTION}

> **Output capacity: You can generate 65,000+ tokens per response.** A {WORD_TARGET}-word module is well within your single-turn limit. Do NOT preemptively truncate.

## Files to Read

| File | Purpose |
|------|---------|
| `{RESEARCH_PATH}` | Factual foundation — use exhaustively |
| `{PLAN_PATH}` | Objectives, vocabulary_hints (use ONLY these words) |
| `{QUICK_REF_PATH}` | Level constraints, immersion %, engagement minimums |

Read ALL four files before writing anything.

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

## Your Task

Write the full lesson prose for **{TOPIC_TITLE}** ({TRACK} track).

- **Target**: approximately {WORD_TARGET} words
- **Immersion**: {IMMERSION_RULE}
- **Engagement callouts**: **{ENGAGEMENT_MIN}+ MANDATORY** — spread across sections, at least 4 different types. Content with fewer than {ENGAGEMENT_MIN} callout boxes FAILS validation.
- **Example sentences**: {EXAMPLE_MIN}+ in varied formats (inline, standalone, tables, dialogues)
- **Structure**: Write ALL sections from the outline. Do not skip any section. Missing sections fail validation.

## Audit Gates

- **Word count**: minimum {WORD_TARGET} words (hard gate)
- **Colonial framing**: NEVER define Ukrainian by contrast with Russian (hard fail)
- **Russianisms**: banned words (hard fail)
- **Russian characters**: ы, э, ё, ъ must NEVER appear (hard fail)
- **Euphony**: і/й, у/в, з/із alternation
- **Engagement callouts**: {ENGAGEMENT_MIN}+ using counted types (hard fail if below minimum)
- **Duplicate headers**: no two H2s sharing the same keyword

---

## Section Word Budgets

{SECTION_BUDGET_TABLE}

---

## Content Structure Rules

{STRUCTURAL_RULES}

### Rule 5: Callout Type Variety

Use at least **4 DIFFERENT** callout types:
- `[!tip]`, `[!warning]`, `[!observe]`/`[!context]`, `[!quote]`, `[!myth-buster]`, `[!culture]`/`[!history-bite]`, `[!fact]`, `[!decolonization]`

### Rule 6: Self-Check Questions in Summary

The {SUMMARY_HEADING} section MUST include 4-6 self-assessment questions.

### Rule 7: Cultural Anchoring

Connect 2-3 grammar/vocabulary points to Ukrainian cultural context:
- Прислів'я (proverbs) that illustrate the grammar point
- Literary quotes (Шевченко, Леся Українка, Франко, Стус, Костенко)
- Real-world Ukrainian contexts (news, social media, academic discourse)

### Rule 8: Structural Variety

Sections must NOT follow the same skeleton. Use at least 3 approaches:
dialogue-led, example-first, question-led, comparison, scenario-based, direct explanation.

### Rule 9: Visual Aids

Use tables for comparing patterns/paradigms. Use mermaid flowcharts for decision logic (aspect choice, case selection). Don't force — use when pedagogically clearer.

---

## How to Hit {WORD_TARGET} Words

{EXPANSION_METHOD}

---

## Language Quality Rules

### No English Inside Ukrainian Sentences (HARD FAIL)

English may ONLY appear in parenthetical equivalents after Ukrainian terms on first introduction.

```markdown
❌ WRONG: "Тепер we переходимо до наступної теми."
✅ RIGHT: "**Вид** (aspect) — це граматична категорія."
```

### Colonial Framing: Ukrainian Stands on Its Own (HARD FAIL)

**NEVER** define Ukrainian by contrast with Russian. Ukrainian is an independent language.

**BANNED**: "Unlike Russian...", "Different from Russian...", "Russian does not have..."
**USE**: "Ukrainian has...", "In Ukrainian, ...", "This letter has been part of Ukrainian writing since..."

**Exceptions**: `[!myth-buster]` and `[!decolonization]` blocks, historical context about Russification.

{SHARED_CONTENT_RULES}

---

## Pre-Submission Verification

### Check 1: Plan Compliance
Every `points:` item in the content_outline must have dedicated prose (not just a passing mention). Each point → at least 50-100 words.

### Check 2: Fact-Check Absolute Claims
Search for «унікальний», «єдиний», «перший», «ніколи», «жодний», «тільки», «лише», unique, only, first, never. Soften if uncertain.

### Check 3: Section Word Counts
If any section <70% of budget → expand. If total <{WORD_TARGET} → expand thinnest sections.

### Check 4: Anti-Surzhyk & Language Scan
Re-read for Russianisms, Russian characters, stray English, colonial framing.

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
> {2-3 sentences of significance}

## {Section 1 from content_outline}

### {Concept 1}
{{H3_WORD_RANGE} words}

### {Concept 2}
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
Absolute claims: {number checked}
Language scan: {CLEAN or list of fixes}
===VERIFICATION_END===
```

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
- Do NOT add vocabulary outside the plan's vocabulary_hints
- Do NOT skip sections from the content_outline
- Do NOT write fewer than {WORD_TARGET} words or more than 150%
- Do NOT fabricate quotes, dates, or historical facts
- Do NOT use straight quotes "..." — always «...»
