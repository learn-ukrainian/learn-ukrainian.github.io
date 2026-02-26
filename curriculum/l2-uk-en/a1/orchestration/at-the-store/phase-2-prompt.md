# Phase 2: Write the Lesson Content

> **Persona reminder:** You are Patient & Supportive Ukrainian Tutor. Write in the voice of Patient Supportive Tutor. Maintain this persona throughout — do not drift into generic AI tone.

> **Your #1 job: Write 3000 words of rich, structured Ukrainian content.**
> Every concept gets dedicated depth. Every H3 gets 80-100+ words. This is how you hit the target.

## Files to Read

| File | Purpose |
|------|---------|
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/at-the-store-research.md` | Factual foundation — use exhaustively |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/meta/at-the-store.yaml` | Content outline with section word allocations |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/at-the-store.yaml` | Objectives, vocabulary_hints (use ONLY these words) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion %, engagement minimums |

Read ALL four files before writing anything.

## Your Task

Write the full lesson prose for **At the Store** (a1 track).

- **Total minimum**: 2000 words
- **Write at least**: 3000 words (1.5x — aim for depth, not padding)
- **Immersion**: TARGET: 35-55% Ukrainian, 45-65% English. Explanatory prose mixed — short Ukrainian sentences woven into English explanations. Grammar still anchored in English. Examples primarily Ukrainian with translations. Ukrainian sentences max 10 words.
- **Engagement callouts**: 4+ across sections, at least 4 different types
- **Example sentences**: 8+ in varied formats (inline, standalone, tables, dialogues)

## Section Word Budgets

**The global word target is the hard gate. Section budgets are guidance** — aim for each section's target, but natural variation (±30%) between sections is fine as long as no section is starved (<50% of its budget) and the total meets the global minimum.

| Section | Target | Write Minimum (1.5x) |
|---------|--------|---------------------|
| Український супермаркет: більше ніж просто покупки | 300 | 450 |
| Відділи та товари | 400 | 600 |
| Пошук і допомога: де знаходиться...? | 400 | 600 |
| На касі: пакет, картка і чек | 500 | 750 |
| Акції та знижки | 250 | 375 |
| Підсумок: ваш похід у магазин | 150 | 225 |
| **Total** | **2000** | **3000** |

---

## MANDATORY Content Structure Rules

**These rules determine whether your output passes or fails audit. Read each one.**

### Rule 1: Every Concept Gets Dedicated Depth (CRITICAL — #1 word count lever)

When an H2 section teaches multiple items in a category, each item (or logical group of closely related items) MUST get its own `### H3` subsection with dedicated depth.

**Grouping rule:** Closely related items that form a single system (e.g., masculine/feminine/neuter endings of the same paradigm) MAY share one H3 — but that H3 must then cover ALL items with equal depth. Independent concepts MUST get separate H3s.

**Count the items from the plan/outline.** Each concept without dedicated depth = ~100 missing words.

```markdown
❌ WRONG (compressed):
## Частини мови
Іменник та дієслово — найважливіші...
(multiple concepts crammed into one paragraph)

✅ RIGHT (each concept = dedicated depth):
## Частини мови
### Іменник
{Definition, questions, 2+ examples, usage note — 80-100 words}
### Дієслово
{Same depth and pattern — 80-100 words}
### Прикметник
{Same depth and pattern — 80-100 words}

✅ ALSO RIGHT (logical group with equal coverage):
## Рід іменників
### Закінчення за родами
{Covers -а/-я (fem), consonant (masc), -о/-е (neut) as unified system — 200+ words}
```

### Rule 2: Depth Over Compression

Each H3 concept block MUST contain ALL of these:

1. **Definition/explanation** (2+ sentences)
2. **How it works** (formation rules, patterns, grammatical function)
3. **2+ example sentences** in context (not isolated words)
4. **Usage note** — when/why a speaker uses this form

Minimum **80-100 words per H3 block**. A 20-word table row is NOT a lesson.

### Rule 3: Presentation Consistency

All items in a category: SAME format, SAME depth (±20%), SAME example count (±1).

❌ Item A gets 150 words, Item B gets 40 words for equal-weight concepts
✅ All items follow identical pattern: definition → formation → examples → usage note

### Rule 4: Example Variety

FORBIDDEN: 5+ consecutive `_Приклад:_` lines. Mix these formats across sections:
- Standalone examples with context (max 3-4 consecutive)
- **Comparison tables** (paradigms, aspect pairs, case usage)
- Inline examples woven into prose
- **Mini-dialogues** showing real usage
- Callout boxes with examples

### Rule 5: Callout Type Variety

Use at least **4 DIFFERENT** callout types across the module:
- `[!tip]` — practical advice
- `[!warning]` — common mistakes, Russianisms to avoid
- `[!observe]` or `[!context]` — pause and think
- `[!quote]` — literary/cultural quote
- `[!myth-buster]` — debunk misconception
- `[!culture]` or `[!history-bite]` — cultural hook
- `[!fact]` — interesting linguistic/cultural fact
- `[!decolonization]` — decolonial perspective on language

❌ 8 callouts all `[!tip]`
✅ Mix of tip, warning, observe, quote, culture

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
- Прислів'я (proverbs) that illustrate the grammar point
- Literary quotes (Шевченко, Леся Українка, Франко, Стус, Костенко)
- Real-world Ukrainian contexts (news, social media, academic discourse)

### Rule 8: Anti-Robotic Writing

- No 3+ sentences starting with the same phrase
- Vary sentence openers across sections
- No mechanical transitions («Далі ми побачимо...», «Тепер розглянемо...»)
- Use storytelling and real-world scenarios, not dry textbook listing
- Each section should have its own narrative arc, not repeat the same skeleton

---

## How to Hit 3000 Words (Expansion Method)

**Don't just write more — write deeper.** For EVERY concept you introduce:

1. **Define it** (2+ sentences explaining what it is)
2. **Show how it works** (pattern, rule, formation)
3. **Give 2+ examples** in full sentences with context
4. **Add a comparison** (table, before/after, correct vs incorrect)
5. **Connect to real life** (when would a Ukrainian speaker use this?)

**If a section is still under its Write Minimum after this, add:**
- A `[!warning]` with a common mistake and correct alternative
- A `[!culture]` or `[!quote]` connecting to Ukrainian culture
- A mini-dialogue showing the concept in conversation
- A comparison table or mermaid flowchart

**The math:** If your H2 teaches 5 concepts × 100 words each = 500 words. Add an intro paragraph (50w) + 2 callouts (60w each) + a comparison table (80w) = **750 words** for that section. This is how you hit big targets.

---

## Language Quality Rules

### No English Inside Ukrainian Sentences (HARD FAIL)

**ABSOLUTELY NO English words inside Ukrainian sentence structures.** English may ONLY appear in parenthetical equivalents after Ukrainian terms on first introduction.

```markdown
❌ WRONG (English verbs/pronouns leaked into Ukrainian):
"Тепер we переходимо до наступної теми."
"Коли ми розглядаємо дієслово, we analyze три терміни."
"Коли we talk про заперечення, ми маємо на увазі..."

✅ RIGHT (Ukrainian sentence, English only in parenthetical equivalents):
"Тепер ми переходимо до наступної теми."
"**Вид** (aspect) — це граматична категорія."
"Цей термін означає **заперечення** (negation)."
```

This is the #1 generation error from previous rebuilds. Scan EVERY sentence before submitting. If you find ANY English word that is not inside parentheses `()` as a translation, fix it immediately.

### Colonial Framing: Ukrainian Stands on Its Own (HARD FAIL if found)

**NEVER define Ukrainian by contrast with Russian.** Ukrainian is an independent language with its own history — it does not need Russian as a reference point.

**BANNED patterns:**
- "Unlike Russian, Ukrainian..." — presents Russian as the baseline
- "Different from Russian..." — positions Russian as the default
- "Russian does not have/use..." — defines Ukrainian by what Russian lacks
- "Looks/sounds like Russian..." — treats Ukrainian as derivative
- "To a Western eye..." — patronizing outsider framing
- Any reference to "Russian script", "Russian alphabet", or "Russian letters" as comparison point

**How to write instead:**
- Present Ukrainian features positively: "Ukrainian has..." / "In Ukrainian, ..."
- Name the feature directly: "The letter Ї is uniquely Ukrainian — it exists in no other alphabet"
- Use typological comparisons to non-Russian languages when helpful: "Similar to how Portuguese nasalizes vowels..."
- Anchor in Ukrainian identity: "This letter has been part of Ukrainian writing since..."

**Legitimate exceptions** (must be explicitly framed as decolonization/myth-busting):
- `[!myth-buster]` blocks debunking Russian propaganda about Ukrainian
- `[!decolonization]` blocks discussing language resistance and independence
- Historical context about Russification, language bans, or colonial repression
- Kyiv/Kiev transliteration context

**Why this matters:** For decades, Ukrainian was presented in textbooks as "a dialect of Russian" or defined solely through differences from Russian. This is colonial framing. Our curriculum presents Ukrainian on its own terms — as a rich, independent European language.

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

### Euphony / Милозвучність (WARNING if violated)

Ukrainian prose must follow euphony rules. Scan your output before submitting:

| Rule | Avoid (Bad) | Use (Good) |
|------|-------------|------------|
| і → й between vowels | вона і Олена | вона й Олена |
| й → і after consonant | він й Олена | він і Олена |
| у → в before vowel | у Одесі | в Одесі |
| в → у before в, ф | в вікні | у вікні |
| в → у before consonant cluster | в зграї | у зграї |
| з → із/зі before з, с, ш, ч | з зброєю | із зброєю (або зі) |
| Vary conjunctions | він і вона і Іван | він і вона та Іван |

Key: й can ONLY follow a vowel. After a consonant, always use і — even before a vowel.

### Pronunciation: IPA Only (HARD FAIL if Latin transliteration found)

**Level-gated IPA rules:**
- **A1–A2**: IPA allowed ONLY on the **first occurrence** of each new vocabulary word when it is introduced. NEVER transcribe full sentences, example phrases, or words the student has already seen in earlier modules. The goal is a pronunciation hint on unfamiliar words, not a phonetics textbook.
- **B1+**: Do NOT include inline IPA `[...]` transcriptions in the content markdown. IPA belongs ONLY in the vocabulary YAML file. Students at B1+ can read Cyrillic — cluttering prose with `` breaks immersion and readability.

**When IPA IS used (A1–A2 content, or any vocabulary file):**
- ALL pronunciation MUST use IPA symbols. Latin transliterations are BANNED.
- Maximum ~15-25 IPA annotations per module (one per new word). If you have more, you are over-annotating.

```markdown
❌ WRONG (Latin transliteration):
"Х sounds like 'kh' in Scottish 'loch'"
"хліб (khlib)"

✅ RIGHT (IPA with English approximation):
"**Х** — [x], like the «ch» in Scottish «loch»"
"**хліб** — [xlʲib]"
```

**IPA Rules:**
- Use IPA symbols in square brackets: `[x]`, `[ʃ]`, `[tʃ]`, `[ʒ]`, `[ts]`, `[dʒ]`
- Add English approximation for accessibility: `[ʃ] — like «sh» in «shoe»`
- Mark palatalization: `[lʲ]`, `[dʲ]`, `[nʲ]`, `[tʲ]` (NOT just `[l]`, `[d]`)
- Mark the soft Л correctly: `[lʲ]` vs hard `[l]`
- Use `[ʋ]` for Ukrainian В (NOT `[v]` or `[w]` — it's a labiodental approximant)
- Use `/u/` for Ukrainian у (NOT `/ʊ/` — Ukrainian has no lax /ʊ/ phoneme)
- NEVER use Latin shortcuts: kh, sh, ch, zh, ts, ya, yu, ye, shch

### Typography

- **ALWAYS** use Ukrainian angular quotes: «...» (never straight quotes "...")
- Use ONLY vocabulary from the plan's `vocabulary_hints` — do NOT invent new terms

---

## LLM Writing Patterns to Avoid (auto-rejection triggers)

1. **"Це не просто X, а Y"** — max ONE in entire module
2. **Grandiose openers** — don't inflate every topic. Mix: questions, examples, scenarios, direct statements
3. **Purple prose** — no "багатогранний діамант", "хірургічного аналізу", "будівельний блок свідомості"
4. **Duplicate greetings** — "Ласкаво просимо" ONCE (intro only)
5. **Stacked identical callouts** — same title max twice, vary types

### Structural Variety

Sections must NOT follow the same skeleton. Use at least 3 different approaches:
- Dialogue-led, example-first, question-led, comparison, scenario-based, direct explanation

### Opener Rotation (H3 subsections in categories)

Rotate openers: definition-first, question-led, scenario-led, function-first. No pattern 3+ times.

### Visual Aids (Grammar Modules)

Use tables for comparing patterns/paradigms/categories. Use mermaid flowcharts for decision logic (aspect choice, case selection). Don't force — use when pedagogically clearer than prose.

---

## Output Format

> **Content outside delimiters is discarded by extraction.**

```
===CONTENT_START===

<!-- SCOPE
Covers: {what this module teaches}
Not covered:
  - {related topic} → {slug}
Related: {connected slugs}
-->

# {Title}

> **Чому це важливо?**
>
> {2-3 sentences of significance}

## {Section 1 from content_outline}

### {Concept 1}
{80-100+ words: definition, how it works, examples, usage}

### {Concept 2}
{80-100+ words: same depth}

{comparison table or callout}

## {Section 2}

{Content — hit the Write Minimum for this section}

...

---

# Підсумок

{Summary + 4-6 self-check questions (~200 words)}

---

===CONTENT_END===
```

After the content block, report word counts per section:

```
===WORD_COUNTS===
Section "{name}": {count} words (minimum: {allocation})
...
Total: {total} words (target: 2000, ratio: {total/WORD_TARGET}x)
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
- Do NOT write fewer than 2000 words total
- Do NOT request skills or delegate to Claude
- Do NOT fabricate quotes, dates, or historical facts
- Do NOT use straight quotes "..." — always «...»
