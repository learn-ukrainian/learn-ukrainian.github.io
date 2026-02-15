# Phase 2: Write the Lesson Content

> **Persona reminder:** You are a Senior Language & Culture Specialist, acting as a Construction Architect. Write in the voice of someone who reveals how Ukrainian sentences are built from the inside — showing the blueprint before the building. Maintain this persona throughout — do not drift into generic AI tone.

> **Your #1 job: Write 8000 words of rich, structured Ukrainian content.**
> Every concept gets dedicated depth. Every H3 gets 80-100+ words. This is how you hit the target.

## Files to Read

| File | Purpose |
|------|---------|
| `curriculum/l2-uk-en/b1/research/sentence-structure-research.md` | Factual foundation — use exhaustively |
| `curriculum/l2-uk-en/b1/meta/sentence-structure.yaml` | Content outline with section word allocations |
| `curriculum/l2-uk-en/plans/b1/sentence-structure.yaml` | Objectives, vocabulary_hints (use ONLY these words) |
| `claude_extensions/quick-ref/B1.md` | Level constraints, immersion %, engagement minimums |

Read ALL four files before writing anything.

## Your Task

Write the full lesson prose for **Структура речення** (B1 track).

- **Total minimum**: 4000 words
- **Write at least**: 8000 words (2.0x — you consistently underwrite, so aim high)
- **Immersion**: 85% Ukrainian. English only for disambiguation (false friends, confusing pairs). No English paragraphs in body text. Ukrainian term FIRST, English in parentheses on FIRST introduction only. After first introduction — Ukrainian term exclusively.
- **Engagement callouts**: 5+ across sections, at least 4 different types
- **Example sentences**: 24+ in varied formats (inline, standalone, tables, dialogues)

## Section Word Budgets

**The global word target is the hard gate. Section budgets are guidance** — aim for each section's target, but natural variation (±30%) between sections is fine as long as no section is starved (<50% of its budget) and the total meets the global minimum.

| Section | Allocation | Write Minimum (2x) |
|---------|-----------|---------------------|
| Вступ: Архітектура українського речення | 350 | 700 |
| Головні члени речення: Підмет і присудок | 550 | 1100 |
| Другорядні члени речення | 550 | 1100 |
| Типи речень та сполучники | 450 | 900 |
| Структура складного речення | 350 | 700 |
| Пунктуація та порядок слів | 350 | 700 |
| Культурний код: Синтаксичний розбір | 500 | 1000 |
| Діалоги: Граматика в контексті | 550 | 1100 |
| Підсумок: Ваша синтаксична карта | 350 | 700 |

---

## MANDATORY Content Structure Rules

**These rules determine whether your output passes or fails audit. Read each one.**

### Rule 1: Every Concept Gets Dedicated Depth (CRITICAL — #1 word count lever)

When an H2 section teaches multiple items in a category, each item MUST get its own `### H3` subsection with dedicated depth.

For example, in "Головні члени речення" — Підмет and Присудок each get their own H3 with definition, question patterns, 2+ examples, underlining convention.

### Rule 2: Depth Over Compression

Each H3 concept block MUST contain ALL of these:
1. **Definition/explanation** (2+ sentences)
2. **How it works** (formation rules, patterns, grammatical function)
3. **2+ example sentences** in context (not isolated words)
4. **Usage note** — when/why a speaker uses this form

Minimum **80-100 words per H3 block**.

### Rule 3: Presentation Consistency

All items in a category: SAME format, SAME depth (±20%), SAME example count (±1).

### Rule 4: Example Variety

FORBIDDEN: 5+ consecutive `_Приклад:_` lines. Mix these formats:
- Standalone examples with context (max 3-4 consecutive)
- **Comparison tables** (paradigms, sentence types)
- Inline examples woven into prose
- **Mini-dialogues** showing real usage
- Callout boxes with examples

### Rule 5: Callout Type Variety

Use at least **4 DIFFERENT** callout types across the module:
- `[!tip]` — practical advice
- `[!warning]` — common mistakes
- `[!observe]` or `[!context]` — pause and think
- `[!quote]` — literary/cultural quote
- `[!culture]` or `[!history-bite]` — cultural hook
- `[!fact]` — interesting linguistic/cultural fact

### Rule 6: Self-Check Questions in Summary

The Підсумок section MUST include 4-6 self-assessment questions.

### Rule 7: Cultural Anchoring

Connect 2-3 grammar points to Ukrainian cultural context. The research mentions "синтаксичний розбір" — the sentence analysis ritual in Ukrainian schools. Use this prominently.

### Rule 8: Anti-Robotic Writing

- No 3+ sentences starting with the same phrase
- Vary sentence openers across sections
- No mechanical transitions
- Use storytelling and real-world scenarios

### Rule 9: Dialogue Format (CRITICAL — audit hard fail)

All dialogues MUST use blockquote format:

```markdown
> **Олена:** Яка тут частина мови?
> **Тарас:** Це підмет, бо відповідає на питання «хто?».
```

NOT plain text or bullet points. This is a hard audit requirement.

---

## Language Quality Rules

### No English Inside Ukrainian Sentences (HARD FAIL)

English may ONLY appear in parenthetical equivalents after Ukrainian terms on first introduction:
- ✅ "**Підмет** (subject) — це головний член речення."
- ❌ "Тепер we розглядаємо підмет."

### Russianisms (HARD FAIL if found)

| Russicism | Correct Ukrainian |
|-----------|-------------------|
| кушати | їсти |
| приймати участь | брати участь |
| получати | отримувати |
| самий кращий | найкращий |
| відноситися | стосуватися |
| слідуючий | наступний |

### Typography

- **ALWAYS** use Ukrainian angular quotes: «...» (never straight quotes "...")
- Use ONLY vocabulary from the plan's `vocabulary_hints`

---

## Output Format

> **Content outside delimiters is discarded by extraction.**

```
===CONTENT_START===

<!-- SCOPE
Covers: Ukrainian sentence analysis terminology — sentence parts (підмет, присудок, додаток, означення, обставина), sentence types (просте, складне), clause types (головне, підрядне), conjunctions, punctuation terms
Not covered:
  - Complex sentence construction rules → b1-26 (relative clauses)
  - Concessive clauses → b1-35
Related: b1-01 (grammar terms), b1-02 (verb terms), b1-03 (grammar rules), b1-05 (checkpoint)
-->

# Структура речення

> **Чому це важливо?**
>
> {2-3 sentences of significance}

## {Section 1 from content_outline}

### {Concept 1}
{80-100+ words}

...

---

# Підсумок: Ваша синтаксична карта

{Summary + 4-6 self-check questions (~200 words)}

---

===CONTENT_END===
```

After the content block, report word counts per section:

```
===WORD_COUNTS===
Section "{name}": {count} words (minimum: {allocation})
...
Total: {total} words (target: 4000, ratio: {total/4000}x)
===WORD_COUNTS===
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

- Do NOT generate activities, exercises, or vocabulary tables (Phase 3 handles these)
- Do NOT add vocabulary outside the plan's vocabulary_hints
- Do NOT skip sections from the content_outline
- Do NOT write fewer than 4000 words total
- Do NOT request skills or delegate to Claude
- Do NOT fabricate quotes, dates, or historical facts
- Do NOT use straight quotes "..." — always «...»
