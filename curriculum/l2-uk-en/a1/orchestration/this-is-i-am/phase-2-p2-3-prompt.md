# Phase 2: Write Section Content

> **Persona reminder:** You are Patient & Supportive Ukrainian Tutor. Write in the voice of The Helpful Neighbor: Patient Supportive Tutor. Maintain this persona throughout — do not drift into generic AI tone.

> **Your #1 job: Write 230 words for the section "Практика".**
> This is ONE section of a larger module — stay within your word budget.
> **Do NOT exceed 2x your target.** If your target is 300, write 300-600. If 900, write 900-1400. Going over wastes tokens and bloats the module.

## Files to Read

| File | Purpose |
|------|---------|
| `curriculum/l2-uk-en/a1/research/this-is-i-am-research.md` | Factual foundation — use exhaustively |
| `curriculum/l2-uk-en/a1/meta/this-is-i-am.yaml` | Content outline with section word allocations |
| `curriculum/l2-uk-en/plans/a1/this-is-i-am.yaml` | Objectives, vocabulary_hints (use ONLY these words) |
| `claude_extensions/quick-ref/A1.md` | Level constraints, immersion %, engagement minimums |

Read ALL four files before writing anything.

## Your Task

Write the section prose for **Практика** within the module **This Is / I Am**.

- **WORD BUDGET**: 230 words minimum, 230 × 2 maximum. Stay in this range.
- **Immersion**: 
- **Engagement callouts**: Include at least 1 callout(s) in this section.
- **Example sentences**: Include at least 3 example sentences in this section.

## Coherence Context (Previously Written)

To ensure flow and avoid repetition, here is what has been covered in previous sections:

Особові займенники: Я, Ти, Ми, Ви, Вони, Він, Вона, Воно: Рід має значення, Пастка «Воно»: Предмети теж мають «особистість», Магічне слово «Це»: Універсальний вказівник

### Seam Prevention (CRITICAL)

- **Continue the narrative flow seamlessly** from the previous section. The reader has been reading continuously — don't break immersion.
- **Do NOT** start with "In this section..." / "У цьому розділі..." / "Тепер розглянемо..." or any meta-commentary about what the section will cover.
- **Do NOT** re-introduce concepts already covered in previous sections. Refer back to them naturally (e.g., "як ми вже бачили з дієсловами руху..." not "Дієслова руху — це...").
- **Do NOT** repeat the module title or section title in prose. The H2 heading is enough.
- **Transition naturally**: use a bridge sentence connecting the previous section's last concept to this section's first concept. Think of it as one continuous chapter, not separate articles.

### Callout Type Tracking

Previously used callout types in this module: [!tip], [!myth-buster]

**Do NOT reuse these callout types.** Choose from the remaining types:
- `[!tip]` — practical advice
- `[!warning]` — common mistakes, Russianisms to avoid
- `[!observe]` or `[!context]` — pause and think
- `[!quote]` — literary/cultural quote
- `[!myth-buster]` — debunk misconception
- `[!culture]` or `[!history-bite]` — cultural hook
- `[!fact]` — interesting linguistic/cultural fact
- `[!decolonization]` — decolonial perspective on language

---

## MANDATORY Content Structure Rules

### Rule 1: Every Concept Gets Dedicated Depth
Each item in this section MUST get its own `### H3` subsection.
Minimum **100-150 words per H3 block**.

### Rule 2: Depth Components
Each H3 concept block MUST contain:
1. **Definition/explanation** (3+ sentences)
2. **Detailed mechanics** (how it works, formation, patterns)
3. **3+ example sentences** in context
4. **Usage note or comparison** (nuance, common pitfalls)

### Rule 3: Example & Callout Variety
Vary your presentation. Use tables, dialogues, and different callout types.

FORBIDDEN: 5+ consecutive `_Приклад:_` lines. Mix these formats:
- Standalone examples with context (max 3-4 consecutive)
- **Comparison tables** (paradigms, aspect pairs, case usage)
- Inline examples woven into prose
- **Mini-dialogues** showing real usage
- Callout boxes with examples

### Rule 4: Presentation Consistency
All items in a category: SAME format, SAME depth (±20%), SAME example count (±1).

### Rule 5: Anti-Robotic Writing
- No 3+ sentences starting with the same phrase
- Vary sentence openers across H3 blocks
- No mechanical transitions
- Use storytelling and real-world scenarios, not dry textbook listing

---

## How to Stay in Budget (Quality over Quantity)

**Write to your word budget — not more, not less.**

- Target: 230 words. Ceiling: 2× that number.
- If under target: add depth to existing concepts (examples, tables, callouts).
- If OVER target: you are bloating. Cut filler, merge similar points, remove redundant examples.
- **This is ONE section of a multi-section module.** The module has other sections covering other topics. Do not expand beyond your scope.

**Per concept (each H3):** 2-3 sentences of explanation + 2-3 examples + 1 usage note = ~100-150 words. That's enough.

---

## Language Quality Rules

### No English Inside Ukrainian Sentences (HARD FAIL)

**ABSOLUTELY NO English words inside Ukrainian sentence structures.** English may ONLY appear in parenthetical equivalents after Ukrainian terms on first introduction.

```markdown
❌ WRONG (English verbs/pronouns leaked into Ukrainian):
"Тепер we переходимо до наступної теми."
"Коли ми розглядаємо дієслово, we analyze три терміни."

✅ RIGHT (Ukrainian sentence, English only in parenthetical equivalents):
"Тепер ми переходимо до наступної теми."
"**Вид** (aspect) — це граматична категорія."
```

This is the #1 generation error from previous rebuilds. Scan EVERY sentence before submitting.

### Russianisms (Pre-Output Scan — HARD FAIL if found)

Before submitting, scan your ENTIRE output for these. They cause automatic audit failure:

| Russicism | Correct Ukrainian |
|-----------|-------------------|
| кушати | їсти |
| приймати участь | брати участь |
| получати | отримувати |
| самий кращий | найкращий |
| відноситися | стосуватися |
| слідуючий | наступний |
| любий (= будь-який) | будь-який |
| на то, що | на те, що |

Also scan for Russian characters: **ы, э, ё, ъ** — these must NEVER appear in Ukrainian text.

### Pronunciation: IPA Only (HARD FAIL if Latin transliteration found)

**ALL pronunciation guides MUST use IPA symbols.** Latin transliterations are BANNED.

```markdown
❌ WRONG (Latin transliteration):
"Х sounds like 'kh' in Scottish 'loch'"
"Ш = 'sh', Ч = 'ch', Ж = 'zh'"
"хліб (khlib)"

✅ RIGHT (IPA with English approximation):
"**Х** — [x], like the «ch» in Scottish «loch»"
"**Ш** — [ʃ], like «sh» in «shoe»"
"**Ч** — [tʃ], like «ch» in «church»"
"**Ж** — [ʒ], like «s» in «measure»"
"**хліб** — [xlʲib]"
```

**Rules:**
- Use IPA symbols in square brackets: `[x]`, `[ʃ]`, `[tʃ]`, `[ʒ]`, `[ts]`, `[dʒ]`
- Add English approximation for accessibility: `[ʃ] — like «sh» in «shoe»`
- Mark palatalization: `[lʲ]`, `[dʲ]`, `[nʲ]`, `[tʲ]` (NOT just `[l]`, `[d]`)
- Mark the soft Л correctly: `[lʲ]` vs hard `[l]`
- Use `[ʋ]` for Ukrainian В (NOT `[v]` or `[w]` — it's a labiodental approximant)
- NEVER use Latin shortcuts: kh, sh, ch, zh, ts, ya, yu, ye, shch

### Typography

- **ALWAYS** use Ukrainian angular quotes: «...» (never straight quotes "...")
- Use ONLY vocabulary from the plan's `vocabulary_hints` — do NOT invent new terms

---

## LLM Writing Patterns to Avoid (auto-rejection triggers)

1. **"Це не просто X, а Y"** — max ONE across the ENTIRE module (check previous sections!)
2. **Grandiose openers** — don't inflate every topic. Mix: questions, examples, scenarios, direct statements
3. **Purple prose** — no "багатогранний діамант", "хірургічного аналізу", "будівельний блок свідомості"
4. **Duplicate greetings** — "Ласкаво просимо" only in module intro (not in sections)
5. **Stacked identical callouts** — same title max twice across the module

### Structural Variety

Sections must NOT follow the same skeleton. Use at least 3 different approaches across the module:
- Dialogue-led, example-first, question-led, comparison, scenario-based, direct explanation

### Opener Rotation (H3 subsections)

Rotate openers: definition-first, question-led, scenario-led, function-first. No pattern 3+ times.

### Visual Aids (Grammar Modules)

Use tables for comparing patterns/paradigms/categories. Use mermaid flowcharts for decision logic (aspect choice, case selection). Don't force — use when pedagogically clearer than prose.

---

## Boundaries

- Do NOT generate activities, exercises, or vocabulary tables (Phase 3 handles these)
- Do NOT add vocabulary outside the plan's vocabulary_hints
- Do NOT skip any concepts from this section's outline
- Do NOT fabricate quotes, dates, or historical facts
- Do NOT use straight quotes "..." — always «...»
- Do NOT request skills or delegate to Claude

---

## Output Format

> **Content outside delimiters is discarded by extraction.**

```
===SECTION_CONTENT_START===

## Практика

### {Concept 1}
{100-150+ words}

### {Concept 2}
{100-150+ words}

...

===SECTION_CONTENT_END===
```

After the content block, report word count:

```
===WORD_COUNTS===
Section "Практика": {count} words (budget: 230-230×2)
===WORD_COUNTS===
```

## Friction Report (MANDATORY)

```
===FRICTION_START===
**Phase**: Phase 2: Section Content (Практика)
**Step**: {what you were doing}
**Friction Type**: NONE | {error_type}
**Raw Error**: {error}
**Self-Correction**: {fix}
===FRICTION_END===
```
