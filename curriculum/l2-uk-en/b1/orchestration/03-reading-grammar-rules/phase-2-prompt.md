# Phase 2: Write the Lesson Content

> **Persona reminder:** You are Patient & Supportive Ukrainian Tutor. Write in the voice of The Helpful Neighbor: Senior Language & Culture Specialist. Maintain this persona throughout — do not drift into generic AI tone.

> **Your #1 job: Write 8000 words of rich, structured Ukrainian content.**
> Every concept gets dedicated depth. Every H3 gets 80-100+ words. This is how you hit the target.

## Files to Read

| File | Purpose |
|------|---------|
| `curriculum/l2-uk-en/b1/research/03-reading-grammar-rules-research.md` | Factual foundation — use exhaustively |
| `curriculum/l2-uk-en/b1/meta/03-reading-grammar-rules.yaml` | Content outline with section word allocations |
| `curriculum/l2-uk-en/plans/b1/reading-grammar-rules.yaml` | Objectives, vocabulary_hints (use ONLY these words) |
| `claude_extensions/quick-ref/B1.md` | Level constraints, immersion %, engagement minimums |

Read ALL four files before writing anything.

## Your Task

Write the full lesson prose for **Читаємо граматичні правила** (b1 track).

- **Total minimum**: 4000 words
- **Write at least**: 8000 words (2.0x — you consistently underwrite, so aim high)
- **Immersion**: 80% Ukrainian — English only in tip/note callouts for tricky concepts. No English paragraphs in body text. Ukrainian terms first, English equivalents in parentheses on FIRST introduction only. After first introduction, Ukrainian term exclusively.
- **Engagement callouts**: 5+ across sections, at least 4 different types
- **Example sentences**: 24+ in varied formats (inline, standalone, tables, dialogues)

## Section Word Budgets

**The global word target is the hard gate. Section budgets are guidance** — aim for each section's target, but natural variation (±30%) between sections is fine as long as no section is starved (<50% of its budget) and the total meets the global minimum.

| Section | Budget | Write Minimum (2x) |
|---------|--------|-------------------|
| Вступ: Читаємо граматику українською | 295 | 590 |
| Шаблони пояснення граматики | 392 | 784 |
| Слова-інструкції та маркери уваги | 313 | 626 |
| Шаблони порівняння та протиставлення | 200 | 400 |
| Дієслова для виконання вправ | 392 | 784 |
| Аналітична термінологія | 392 | 784 |
| Термінологія стилю та регістру | 392 | 784 |
| Терміни словотвору | 313 | 626 |
| Практика: Аналіз правил | 428 | 856 |
| Діалоги: Обговорення правил | 588 | 1176 |
| Підсумок | 295 | 590 |
| **TOTAL** | **4000** | **8000** |

---

## MANDATORY Content Structure Rules

**These rules determine whether your output passes or fails audit. Read each one.**

### Rule 1: Every Concept Gets Dedicated Depth (CRITICAL — #1 word count lever)

When an H2 section teaches multiple items in a category, each item (or logical group of closely related items) MUST get its own `### H3` subsection with dedicated depth.

**Count the items from the plan/outline.** Each concept without dedicated depth = ~100 missing words.

### Rule 2: Depth Over Compression

Each H3 concept block MUST contain ALL of these:

1. **Definition/explanation** (2+ sentences)
2. **How it works** (formation rules, patterns, grammatical function)
3. **2+ example sentences** in context (not isolated words)
4. **Usage note** — when/why a speaker uses this form

Minimum **80-100 words per H3 block**. A 20-word table row is NOT a lesson.

### Rule 3: Presentation Consistency

All items in a category: SAME format, SAME depth (±20%), SAME example count (±1).

### Rule 4: Example Variety

FORBIDDEN: 5+ consecutive `_Приклад:_` lines. Mix these formats across sections:
- Standalone examples with context (max 3-4 consecutive)
- **Comparison tables** (paradigms, patterns, correct vs incorrect)
- Inline examples woven into prose
- **Mini-dialogues** showing real usage
- Callout boxes with examples

### Rule 5: Callout Type Variety

Use at least **4 DIFFERENT** callout types across the module:
- `[!tip]` — practical advice
- `[!warning]` — common mistakes, Russianisms to avoid
- `[!observe]` or `[!context]` — pause and think
- `[!quote]` — literary/cultural quote
- `[!culture]` or `[!history-bite]` — cultural hook
- `[!fact]` — interesting linguistic/cultural fact

### Rule 6: Self-Check Questions in Summary

The Підсумок section MUST include 4-6 self-assessment questions:

```markdown
**Перевірте себе:**
1. {question testing core concept 1}
2. {question testing core concept 2}
3. {question requiring application, not recall}
...
```

### Rule 7: Cultural Anchoring

Connect 2-3 grammar or vocabulary points to Ukrainian cultural context:
- Meletiy Smotrytsky's 1619 Grammar (first codification)
- Ivan Ohiienko and language purity movement
- Real-world Ukrainian contexts (news, social media, academic discourse)

### Rule 8: Anti-Robotic Writing

- No 3+ sentences starting with the same phrase
- Vary sentence openers across sections
- No mechanical transitions
- Use storytelling and real-world scenarios, not dry textbook listing
- Each section should have its own narrative arc

---

## How to Hit 8000 Words (Expansion Method)

**Don't just write more — write deeper.** For EVERY concept you introduce:

1. **Define it** (2+ sentences explaining what it is)
2. **Show how it works** (pattern, rule, formation)
3. **Give 2+ examples** in full sentences with context
4. **Add a comparison** (table, before/after, correct vs incorrect)
5. **Connect to real life** (when would a Ukrainian speaker use this?)

---

## Language Quality Rules

### No English Inside Ukrainian Sentences (HARD FAIL)

**ABSOLUTELY NO English words inside Ukrainian sentence structures.** English may ONLY appear in parenthetical equivalents after Ukrainian terms on first introduction.

```markdown
❌ WRONG: "Тепер we переходимо до наступної теми."
✅ RIGHT: "Тепер ми переходимо до наступної теми."
✅ RIGHT: "**Вид** (aspect) — це граматична категорія."
```

### Russianisms (Pre-Output Scan — HARD FAIL if found)

Before submitting, scan your ENTIRE output for these:

| Russicism | Correct Ukrainian |
|-----------|-------------------|
| кушати | їсти |
| приймати участь | брати участь |
| получати | отримувати |
| самий кращий | найкращий |
| відноситися | стосуватися |
| слідуючий | наступний |

Also scan for Russian characters: **ы, э, ё, ъ** — these must NEVER appear in Ukrainian text.

### Typography

- **ALWAYS** use Ukrainian angular quotes: «...» (never straight quotes "...")
- IPA for all phonetics (no Latin transliteration)
- Use ONLY vocabulary from the plan's `vocabulary_hints` — do NOT invent new terms

---

## LLM Writing Patterns to Avoid (auto-rejection triggers)

1. **"Це не просто X, а Y"** — max ONE in entire module
2. **Grandiose openers** — mix: questions, examples, scenarios, direct statements
3. **Purple prose** — no "багатогранний діамант", "хірургічного аналізу"
4. **Duplicate greetings** — "Ласкаво просимо" ONCE (intro only)
5. **Stacked identical callouts** — same title max twice, vary types

### Structural Variety

Sections must NOT follow the same skeleton. Use at least 3 different approaches:
- Dialogue-led, example-first, question-led, comparison, scenario-based, direct explanation

---

## Output Format

> **Content outside delimiters is discarded by extraction.**

```
===CONTENT_START===

<!-- SCOPE
Covers: Reading Ukrainian grammar explanations, instruction vocabulary, analytical terms, style/register terminology, word formation terms
Not covered:
  - Sentence structure → b1-04
  - Metalanguage checkpoint → b1-05
Related: b1-01, b1-02
-->

# Читаємо граматичні правила

> **Чому це важливо?**
>
> {2-3 sentences of significance}

## Вступ: Читаємо граматику українською

...

## Шаблони пояснення граматики

...

## Слова-інструкції та маркери уваги

...

## Шаблони порівняння та протиставлення

...

## Дієслова для виконання вправ

...

## Аналітична термінологія

...

## Термінологія стилю та регістру

...

## Терміни словотвору

...

## Практика: Аналіз правил

...

## Діалоги: Обговорення правил

...

---

# Підсумок

{Summary + 4-6 self-check questions (~295 words)}

---

===CONTENT_END===
```

After the content block, report word counts per section:

```
===WORD_COUNTS===
Section "name": {count} words (minimum: {allocation})
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
