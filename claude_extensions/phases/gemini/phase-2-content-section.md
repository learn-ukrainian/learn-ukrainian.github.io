# Phase 2: Write Section Content

> **Persona reminder:** You are {SKILL_IDENTITY}. Write in the voice of {PERSONA_VOICE}. Maintain this persona throughout — do not drift into generic AI tone.

> **Your #1 job: Write {HARD_MINIMUM_WORD_COUNT} words for the section "{SECTION_TITLE}".**
> This is ONE section of a larger module — stay within your word budget.
> **Do NOT exceed 2x your target.** If your target is 300, write 300-600. If 900, write 900-1400. Going over wastes tokens and bloats the module.

## Files to Read

| File | Purpose |
|------|---------|
| `{RESEARCH_PATH}` | Factual foundation — use exhaustively |
| `{META_PATH}` | Content outline with section word allocations |
| `{PLAN_PATH}` | Objectives, vocabulary_hints (use ONLY these words) |
| `{QUICK_REF_PATH}` | Level constraints, immersion %, engagement minimums |

Read ALL four files before writing anything.

## Your Task

Write the section prose for **{SECTION_TITLE}** within the module **{TOPIC_TITLE}**.

- **WORD BUDGET**: {HARD_MINIMUM_WORD_COUNT} words minimum, {HARD_MINIMUM_WORD_COUNT} × 2 maximum. Stay in this range.
- **Engagement callouts**: Include at least {SECTION_ENGAGEMENT_MIN} callout(s) in this section.
- **Example sentences**: Include at least {SECTION_EXAMPLE_MIN} example sentences in this section.

## Immersion Level (HARD FAIL if violated — audit measures this)

{IMMERSION_RULE}

> **The audit measures immersion as % of Ukrainian words.** If your content exceeds the target Ukrainian %, the module FAILS and must be rewritten. This is NOT a suggestion — it is enforced automatically. Count your languages before submitting.

## Level Grammar Constraints (HARD FAIL if violated)

{LEVEL_CONSTRAINTS}

> **These constraints are enforced by automated audit.** Every violation = audit failure = rebuild. Follow them exactly.

## Coherence Context (Previously Written)

To ensure flow and avoid repetition, here is what has been covered in previous sections.
The context below includes **topic headings with lead sentences** (what was covered and what was claimed) and **closing prose** (how the previous section ended — use this to write a seamless bridge):

{PREVIOUS_CONTENT_SUMMARY}

### Seam Prevention (CRITICAL)

- **Continue the narrative flow seamlessly** from the previous section. The reader has been reading continuously — don't break immersion.
- **Use the closing prose above** to write your opening bridge sentence. Pick up where the previous section left off — reference its final concept, example, or question naturally.
- **Do NOT** start with "In this section..." / "У цьому розділі..." / "Тепер розглянемо..." or any meta-commentary about what the section will cover.
- **Read the `→` lines carefully.** They show what was ALREADY WRITTEN. Do NOT repeat these facts, claims, comparisons, or arguments. If a previous section already compared Trypillia to Egypt, do NOT make the same comparison — use a different angle or reference it briefly ("як ми вже бачили...").
- **Do NOT** re-introduce concepts already covered in previous sections. Refer back to them naturally (e.g., "як ми вже бачили з дієсловами руху..." not "Дієслова руху — це...").
- **Do NOT** repeat the module title or section title in prose. The H2 heading is enough.
- **Transition naturally**: use a bridge sentence connecting the previous section's last concept to this section's first concept. Think of it as one continuous chapter, not separate articles.

### Callout Type Tracking

Previously used callout types in this module: {CALLOUT_TYPES_USED}

**Do NOT reuse these callout types.** Choose from the remaining types:
- `[!tip]` — practical advice
- `[!warning]` — common mistakes, Russianisms to avoid
- `[!observe]` or `[!context]` — pause and think
- `[!quote]` — literary/cultural quote
- `[!myth-buster]` — debunk misconception
- `[!culture]` or `[!history-bite]` — cultural hook
- `[!fact]` — interesting linguistic/cultural fact
- `[!decolonization]` — decolonial perspective on language

### Statistics Already Cited (DO NOT REPEAT)

These numbers/measurements have already appeared in previous sections: {STATISTICS_CITED}

**Do NOT restate these exact statistics.** If you must reference the same concept, either:
- Refer back briefly: «як ми вже зазначили, Тальянки мали площу 450 га»
- Use a DIFFERENT statistic or angle on the same topic
- Summarize without restating the number: «найбільше протомісто» instead of repeating «450 гектарів»

### Paragraph Openers Already Used (DO NOT REPEAT)

These are the first 3 words of paragraphs from previous sections: {OPENERS_USED}

**Do NOT start any paragraph with the same 3-word opening as a previous section.** Scan the list above before writing each paragraph. Vary your rhetorical toolkit:
- Mix: questions, comparisons, direct statements, historical anecdotes, temporal markers, cause-effect
- If you've already used «Уявіть собі...» in a previous section, try «Порівняйте це з...» or a direct fact
- If you've already used «Це не просто...», try «X виконує функцію Y» or just state the claim directly
- Each section should have distinct paragraph openings — no two sections should feel copy-pasted

### Biographical Facts Already Stated (DO NOT REPEAT)

These biographical details have appeared in previous `[!biography]` callouts or prose: {BIO_FACTS_USED}

**Do NOT repeat the same biographical claims.** If the same person was introduced before:
- Reference them by name without re-introducing: «Хвойка, якого ми вже згадували,...»
- Add NEW biographical details not covered before
- Do NOT create a second `[!biography]` callout for the same person

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

- Target: {HARD_MINIMUM_WORD_COUNT} words. Ceiling: 2× that number.
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

### No Word Salad (HARD FAIL)

**Every paragraph must have ONE clear point and logical flow between sentences.** Do NOT string together unrelated observations. Also forbidden: alternating sentence language randomly within a paragraph. Each paragraph should have a consistent language frame.

### Colonial Framing: Ukrainian Stands on Its Own (HARD FAIL if found)

**NEVER define Ukrainian by contrast with Russian.** Ukrainian is an independent language — it does not need Russian as a reference point.

**BANNED patterns:** "Unlike Russian...", "Different from Russian...", "Russian does not have/use...", "Looks/sounds like Russian...", "To a Western eye...", references to "Russian script/alphabet/letters" as comparison.

**Instead:** Present Ukrainian positively ("Ukrainian has...", "In Ukrainian, ..."). Use non-Russian languages for typological comparisons when helpful. Anchor in Ukrainian identity and history.

**Exceptions:** `[!myth-buster]` or `[!decolonization]` blocks, resistance/Russification context, Kyiv/Kiev transliteration.

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

### Pronunciation (HARD FAIL if Latin transliteration found)

**Pronunciation rules:**
- **A1–A2**: Use **stress marks** (мі́сто) for pronunciation hints on the first occurrence of new vocabulary words.
- **B1+**: No pronunciation annotations in content.

**Latin transliterations are BANNED at ALL levels.** Never use kh, sh, ch, zh, ts, ya, yu, ye, shch.

```markdown
❌ WRONG (Latin transliteration):
"хліб (khlib)"

✅ RIGHT (stress mark + English approximation):
"**хлі́б** — like English «hleeb» but with a «ch» sound"
```

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
- Do NOT fabricate quotes, dates, or historical facts — if the research file doesn't confirm it, don't claim it
- Do NOT make absolute claims ("unique", "only", "first", "never") without verification — soften if uncertain
- Do NOT use straight quotes "..." — always «...»
- Do NOT request skills or delegate to Claude

---

## Pre-Submission Verification (MANDATORY — do this BEFORE writing your final output)

After drafting your section, run these checks. Fix any issues found before outputting.

### Check 1: Outline Point Coverage

Look at the `points:` for this section in `{META_PATH}`. For EVERY point:
- Does your content address it with dedicated prose (not just a passing mention)?
- If a point is missing, **add it now** — write a paragraph or H3 subsection for it.

### Check 2: Fact-Check Absolute Claims

Search your draft for: **«унікальний»**, **«єдиний»**, **«перший»**, **«ніколи»**, **«жодний»**, **«тільки»**, **«лише»**, **unique**, **only**, **first**, **never**, **no other**, **the oldest**, **the most**

For EACH: **Is this literally true?** If uncertain, soften:
- «єдиний» → «один із небагатьох» or «характерний для»
- «unique to Ukrainian» → «distinctive in Ukrainian»
- «the first» → «one of the earliest» (unless research confirms)
- Historical dates/facts: verify against the research file. If not confirmed, **remove**.

### Check 3: Language Scan

Re-read your section for:
- Russianisms (кушати, получати, etc.)
- Russian characters (ы, э, ё, ъ)
- English words outside parenthetical translations
- Colonial framing ("Unlike Russian...")
- Fix any found.

---

## Output Format

> **Content outside delimiters is discarded by extraction.**

```
===SECTION_CONTENT_START===

## {SECTION_TITLE}

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
Section "{SECTION_TITLE}": {count} words (budget: {HARD_MINIMUM_WORD_COUNT}-{HARD_MINIMUM_WORD_COUNT}×2)
===WORD_COUNTS===
```

Then report verification results:

```
===VERIFICATION_START===
Outline points: {X}/{Y} addressed (list any added during verification)
Absolute claims: {number checked} — {list softened/removed, or "all verified"}
Language scan: {CLEAN or list of fixes}
===VERIFICATION_END===
```

## Friction Report (MANDATORY)

```
===FRICTION_START===
**Phase**: Phase 2: Section Content ({SECTION_TITLE})
**Step**: {what you were doing}
**Friction Type**: NONE | {error_type}
**Raw Error**: {error}
**Self-Correction**: {fix}
===FRICTION_END===
```
