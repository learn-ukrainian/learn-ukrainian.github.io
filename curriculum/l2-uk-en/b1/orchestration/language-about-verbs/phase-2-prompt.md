# Phase 2: Write the Lesson Content

> **Persona reminder:** You are Patient & Supportive Ukrainian Tutor. Write in the voice of The Helpful Neighbor: Senior Language & Culture Specialist. Maintain this persona throughout — do not drift into generic AI tone.

> **Your #1 job: Write 8000 words of rich, structured Ukrainian content.**
> Every concept gets dedicated depth. Every H3 gets 150-200+ words. This is how you hit the target.

## Files to Read

| File | Purpose |
|------|---------|
| `curriculum/l2-uk-en/b1/research/language-about-verbs-research.md` | Factual foundation — use exhaustively |
| `curriculum/l2-uk-en/b1/meta/language-about-verbs.yaml` | Content outline with section word allocations |
| `curriculum/l2-uk-en/plans/b1/language-about-verbs.yaml` | Objectives, vocabulary_hints (use ONLY these words) |
| `claude_extensions/quick-ref/b1.md` | Level constraints, immersion %, engagement minimums |

Read ALL four files before writing anything.

## Your Task

Write the full lesson prose for **Мова про дієслова** (b1 track).

- **HARD FLOOR**: 4000 words — audit FAILS below this
- **TARGET**: 6000 words — aim here
- **MAX**: 8000 words — natural ceiling
- **Immersion**: 70% Ukrainian. English scaffolding: parenthetical equivalents for ALL new terms on first use, brief English intro paragraph allowed. Ukrainian term always comes first.
- **Engagement callouts**: 5+ across sections, at least 4 different types. Use `> [!type]` format (MUST have `>` blockquote prefix).
- **Example sentences**: 24+ in varied formats (inline, standalone, tables, dialogues)

## Section Word Budgets

**The global word target is the hard gate. Section budgets are guidance** — aim for each section's target, but natural variation (±30%) between sections is fine as long as no section is starved (<50% of its budget) and the total meets the global minimum.

| # | H2 Section Name | Floor (FAIL below) | Target (aim here) |
|---|----------------|---------------------|-------------------|
| 1 | Система дієслова: Вступ | 411 | 617 |
| 2 | Вид дієслова: Доконаний та недоконаний | 308 | 462 |
| 3 | Поняття дії: Процес та результат | 411 | 617 |
| 4 | Час дієслова: Граматична подорож | 616 | 924 |
| 5 | Заперечення та його вплив на вид | 308 | 462 |
| 6 | Додаткові дієслівні категорії | 308 | 462 |
| 7 | Форми дієслова: Синтетична та складена | 513 | 770 |
| 8 | Читання граматичних пояснень | 411 | 617 |
| 9 | Міні-діалоги: Обговорення граматики | 513 | 770 |
| 10 | Підсумок та практичні поради | 201 | 301 |
| **TOTAL** | | **4000** | **6000** |

**How to use:** Floor = the plan allocation (sum = 4000). Target = 1.5× floor (sum = 6000). Write TO THE TARGET, not the floor. If you find yourself at the floor, you are underwriting.

---

## MANDATORY Content Structure Rules

**These rules determine whether your output passes or fails audit. Read each one.**

### Rule 1: Every Concept Gets Dedicated Depth (CRITICAL — #1 word count lever)

When an H2 section teaches multiple items in a category, each item (or logical group of closely related items) MUST get its own `### H3` subsection with dedicated depth.

**Each H3 block: 150-200 words minimum.** This is the key to hitting the target. A 50-word H3 will cause undershoot.

```markdown
❌ WRONG (compressed):
## Вид дієслова
Доконаний та недоконаний вид — найважливіші...
(multiple concepts crammed into one paragraph)

✅ RIGHT (each concept = dedicated depth):
## Вид дієслова: Доконаний та недоконаний
### Що таке вид дієслова?
{Definition, context, why it matters — 150+ words}
### Доконаний вид
{Definition, how to identify, 2+ examples, usage note — 150+ words}
### Недоконаний вид
{Same depth and pattern — 150+ words}
```

### Rule 2: Depth Over Compression

Each H3 concept block MUST contain ALL of these:

1. **Definition/explanation** (2+ sentences)
2. **How it works** (formation rules, patterns, grammatical function)
3. **2+ example sentences** in context (not isolated words)
4. **Usage note** — when/why a speaker uses this form

### Rule 3: Presentation Consistency

All items in a category: SAME format, SAME depth (±20%), SAME example count (±1).

### Rule 4: Example Variety

FORBIDDEN: 5+ consecutive `_Приклад:_` lines. Mix these formats across sections:
- Standalone examples with context (max 3-4 consecutive)
- **Comparison tables** (paradigms, aspect pairs, case usage)
- Inline examples woven into prose
- **Mini-dialogues** showing real usage
- Callout boxes with examples

### Rule 5: Callout Type Variety

Use at least **4 DIFFERENT** callout types across the module. Format: `> [!type]` (with blockquote `>` prefix — MANDATORY):
- `> [!tip]` — practical advice
- `> [!warning]` — common mistakes, Russianisms to avoid
- `> [!observe]` or `> [!context]` — pause and think
- `> [!quote]` — literary/cultural quote
- `> [!myth-buster]` — debunk misconception
- `> [!culture]` or `> [!history-bite]` — cultural hook
- `> [!fact]` — interesting linguistic/cultural fact

**CRITICAL FORMAT:** Every callout line MUST start with `> ` (blockquote prefix). Not `[!tip]` alone.

```markdown
✅ CORRECT:
> [!tip] Порада
> Зверніть увагу на форму...

❌ WRONG (missing > prefix):
[!tip] Порада
Зверніть увагу на форму...
```

### Rule 6: Self-Check Questions in Summary

The Підсумок section MUST include 4-6 self-assessment questions.

### Rule 7: Cultural Anchoring

Connect 2-3 grammar or vocabulary points to Ukrainian cultural context. Research notes mention:
- Richness of Ukrainian future tense (3 forms — unique among Slavic languages)
- Past tense losing person but gaining gender (heritage of ancient perfect forms)

### Rule 8: Anti-Robotic Writing

- No 3+ sentences starting with the same phrase
- Vary sentence openers across sections
- No mechanical transitions («Далі ми побачимо...», «Тепер розглянемо...»)
- Use storytelling and real-world scenarios, not dry textbook listing

---

## How to Hit 6000+ Words (Expansion Method)

**Don't just write more — write deeper.** For EVERY concept:

1. **Define it** (2+ sentences)
2. **Show how it works** (pattern, rule, formation)
3. **Give 2+ examples** in full sentences with context
4. **Add a comparison** (table, before/after, correct vs incorrect)
5. **Connect to real life** (when would a Ukrainian speaker use this?)

**If a section is still under its Target after this, add:**
- A `> [!warning]` with a common mistake and correct alternative
- A `> [!culture]` connecting to Ukrainian culture
- A mini-dialogue showing the concept in conversation
- A comparison table

---

## Language Quality Rules

### Russianisms (Pre-Output Scan — HARD FAIL if found)

| Russicism | Correct Ukrainian |
|-----------|-------------------|
| кушати | їсти |
| приймати участь | брати участь |
| получати | отримувати |
| самий кращий | найкращий |
| відноситися | стосуватися |
| слідуючий | наступний |

Also scan for Russian characters: **ы, э, ё, ъ** — these must NEVER appear.

### Typography

- **ALWAYS** use Ukrainian angular quotes: «...» (never straight quotes "...")
- Use ONLY vocabulary from the plan's `vocabulary_hints`

---

## LLM Writing Patterns to Avoid

1. **"Це не просто X, а Y"** — max ONE in entire module
2. **Grandiose openers** — mix: questions, examples, scenarios, direct statements
3. **Purple prose** — no "багатогранний діамант", "хірургічного аналізу"
4. **Duplicate greetings** — "Ласкаво просимо" ONCE (intro only)
5. **Stacked identical callouts** — same title max twice, vary types
6. **"Operating system" metaphors** — no tech metaphors for language learning

---

## Output Format

> **Content outside delimiters is discarded by extraction.**

```
===CONTENT_START===

<!-- SCOPE
Covers: Verb-specific Ukrainian grammar terminology (aspect, tense, negation, forms)
Not covered:
  - Aspect usage rules → aspect-pairs-essential-40
  - Full conjugation paradigms → reading-grammar-rules
Related: how-to-talk-about-grammar, reading-grammar-rules, aspect-complete-system
-->

# Мова про дієслова

> **Чому це важливо?**
>
> {2-3 sentences of significance}

## Система дієслова: Вступ

{Content — aim for 617 words}

## Вид дієслова: Доконаний та недоконаний

{Content — aim for 462 words}

## Поняття дії: Процес та результат

{Content — aim for 617 words}

## Час дієслова: Граматична подорож

{Content — aim for 924 words}

## Заперечення та його вплив на вид

{Content — aim for 462 words}

## Додаткові дієслівні категорії

{Content — aim for 462 words}

## Форми дієслова: Синтетична та складена

{Content — aim for 770 words}

## Читання граматичних пояснень

{Content — aim for 617 words}

## Міні-діалоги: Обговорення граматики

{Content — aim for 770 words}

---

# Підсумок та практичні поради

{Summary + 4-6 self-check questions (~301 words)}

---

===CONTENT_END===
```

After the content block, report word counts per section:

```
===WORD_COUNTS===
Section "{name}": {count} words (floor: {allocation}, target: {target})
...
Total: {total} words (HARD FLOOR: 4000, target: 6000, ratio: {total/4000}x)
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
