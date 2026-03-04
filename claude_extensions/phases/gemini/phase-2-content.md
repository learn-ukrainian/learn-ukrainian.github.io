# Phase 2: Write the Lesson Content

> **Persona reminder:** You are {SKILL_IDENTITY}. Write in the voice of {PERSONA_VOICE}. Maintain this persona throughout — do not drift into generic AI tone.

> **Your #1 job: Write approximately {WORD_TARGET} words of clear, well-structured Ukrainian content.**
> {WRITING_TONE_INSTRUCTION}

> **Output capacity: You can generate 65,000+ tokens per response.** A {WORD_TARGET}-word Ukrainian module is ~{WORD_TARGET_TOKENS}K tokens — well within your single-turn limit. Do NOT preemptively truncate, self-limit, or report TOKEN_LIMIT_TRUNCATION friction. Write the complete module in full.

## Files to Read

| File | Purpose |
|------|---------|
| `{RESEARCH_PATH}` | Factual foundation — use exhaustively |
| `{META_PATH}` | Content outline with section word allocations |
| `{PLAN_PATH}` | Objectives, vocabulary_hints (use ONLY these words) |
| `{QUICK_REF_PATH}` | Level constraints, immersion %, engagement minimums |

Read ALL four files before writing anything.

## Primary Source Excerpts (Cite These — Don't Invent Quotes)

These passages were retrieved from indexed primary sources (litopys.org.ua). When you need to cite a primary source, prefer these verified passages over inventing quotes from memory. You may paraphrase or excerpt, but attribute correctly.

{PRIMARY_SOURCE_EXCERPTS}

## Resource Discoveries

These resources were found during the discover phase. They include videos, blog articles, textbook references, and images where available.

- **Videos**: Consider embedding relevant ones as `<YouTubeVideo id="VIDEO_ID" />` JSX components where they add value
- **Textbook references**: Use these as authoritative sources for grammar explanations and examples. Cross-reference your content against these real Ukrainian textbook explanations.
- **Textbook images**: If high-quality images were found, consider referencing them in your lesson. Describe what they illustrate when relevant.
- **Literary sources**: For seminar tracks, use these primary source excerpts as evidence and quotation material.

{VIDEO_DISCOVERY}

{PRONUNCIATION_VIDEOS}

## Module Sequence Constraints (HARD FAIL if violated)

{PEDAGOGICAL_CONSTRAINTS}

> **These constraints enforce what the student has actually learned so far.** Using letters, grammar forms, or vocabulary from future modules is a pedagogical error — the student literally cannot parse text with letters they haven't been taught. Violations will be caught in review.

{DECODABLE_VOCABULARY}

{TEXTBOOK_EXAMPLES}

---

## Your Task

Write the full lesson prose for **{TOPIC_TITLE}** ({TRACK} track).

- **Target**: approximately {WORD_TARGET} words (this is both the minimum AND the approximate ceiling — do not dramatically overshoot)
- **Immersion**: {IMMERSION_RULE}
- **Engagement callouts**: {ENGAGEMENT_MIN}+ across sections, at least 4 different types
- **Example sentences**: {EXAMPLE_MIN}+ in varied formats (inline, standalone, tables, dialogues)

## Downstream Audit Gates (your content will be checked for)

Write with these in mind — errors here trigger Phase D repair cycles:
- **Word count**: minimum **{WORD_TARGET}** words (hard gate)
- **Colonial framing**: NEVER define Ukrainian by contrast with Russian (hard fail)
- **Russianisms**: banned words — кушати, приймати участь, получати, самий кращий, слідуючий (hard fail)
- **Russian characters**: ы, э, ё, ъ must NEVER appear (hard fail)
- **Euphony**: і/й, у/в, з/із alternation (auto-fixable but better to write correctly)
- **Engagement callouts**: {ENGAGEMENT_MIN}+ using counted types ([!tip], [!warning], [!quote], [!myth-buster], [!culture], [!fact], [!context], [!reflection], [!note])
- **Duplicate headers**: no two H2s sharing the same keyword (e.g., two headers containing «спадщина»)

---

## Section Word Budgets

**The global word target is the hard gate. Section budgets are guidance** — aim for each section's target, but natural variation (±30%) between sections is fine as long as no section is starved (<50% of its budget) and the total meets the global minimum.

{SECTION_BUDGET_TABLE}

---

## MANDATORY Content Structure Rules

**These rules determine whether your output passes or fails audit. Read each one.**

{STRUCTURAL_RULES}

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

The {SUMMARY_HEADING} section MUST include 4-6 self-assessment questions:

```markdown
**{SELF_CHECK_HEADING}**
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

### Rule 8b: No Repetitive Filler Patterns (HARD FAIL if detected)

The audit auto-detects **repetitive LLM patterns** — the same transitional phrase used across multiple sections. A single "It's worth noting" is fine. Two or more instances across the module = automatic failure.

**Always banned (even once):**
- "In this lesson, we will..." / "In this module, we will..." — formulaic openers that signal auto-generated text

**Flagged at 2+ occurrences (repetition = LLM pattern):**
- "It's worth noting that..." / "Interestingly..." / "Let's explore..."
- «Давайте розглянемо...» / «Варто зазначити, що...» / «Цікаво, що...»
- Any phrase you catch yourself reusing across sections

**Instead:** Vary your openers. Start each section differently — a fact, a question, a scenario, a Ukrainian phrase. If you notice you're repeating a pattern, stop and rephrase.

### Rule 9: Prefer Active Voice

Ukrainian strongly prefers active constructions. Use passive only when:
- The agent is truly unknown: «Книгу було знайдено» (who found it is irrelevant)
- Emphasis is intentionally on the object, not the actor

Avoid: «Це може бути використано...», «Правило застосовується...»
Prefer: «Ви можете використати...», «Ми застосовуємо правило...»

---

## How to Hit {WORD_TARGET} Words (Expansion Method)

{EXPANSION_METHOD}

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

### No Word Salad (HARD FAIL)

**Every paragraph must have ONE clear point and logical flow between sentences.** Do NOT string together unrelated observations.

```markdown
❌ WRONG (three disconnected claims stitched together):
"Ukraine is a very digital country. You'll often see prices written as «50 грн».
Cashiers speak fast. Telling 50 from 15 by ear is a superpower."

✅ RIGHT (one clear point with logical flow):
"In shops, prices are written as digits — «50 грн». Reading them is easy.
But when the cashier says the total out loud, you need to catch the difference
between п'ятдесят (50) and п'ятнадцять (15). Training your ear for these
pairs is one of the most practical skills in this lesson."
```

**Also forbidden:** Alternating sentence language randomly within a paragraph (Ukrainian sentence, then English sentence, then Ukrainian again with no pattern). Each paragraph should have a consistent language frame — either English prose with Ukrainian terms introduced, or Ukrainian prose with English glosses.

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
| красивий | гарний |
| прекрасне / прекрасний | чудовий / чудове |

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

### Pronunciation (HARD FAIL if Latin transliteration found)

**Pronunciation rules:**
- **A1–A2**: Use **stress marks** (мі́сто) for pronunciation hints on the first occurrence of new vocabulary words.
- **B1+**: No pronunciation annotations in content.

**Latin transliterations are BANNED at ALL levels.** Never use kh, sh, ch, zh, ts, ya, yu, ye, shch.

**IPA and phonetic brackets are BANNED at ALL levels.** Never include IPA symbols (ɑ, ɛ, ʃ, etc.) or bracketed pronunciation guides like `[ma-ma]`, `[a-na-nas]`, `[ˈmɑmɑ]`. The ONLY pronunciation aid is the stress mark (´) on the vowel.

```markdown
❌ WRONG (Latin transliteration):
"Х sounds like 'kh' in Scottish 'loch'"
"хліб (khlib)"

❌ WRONG (IPA / phonetic brackets):
"мама [ˈmɑmɑ]"
"ананас [a-na-nas]"
"сумка [sum-ka]"

✅ RIGHT (stress mark only):
"**мА́ма** (mom)"
"**ананА́с** (pineapple)"
"**сУ́мка** (bag)"

✅ RIGHT (English approximation for letter introduction):
"**Х**, like the «ch» in Scottish «loch»"
```

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

## Pre-Submission Verification (MANDATORY — do this BEFORE writing your final output)

After drafting your content, run these three checks. Fix any issues found before outputting.

### Check 1: Plan Compliance

Open the `content_outline` from `{META_PATH}`. Go through EVERY `points:` item in EVERY section:
- Does your content address this point with dedicated prose (not just a passing mention)?
- If a point is missing or only touched in a phrase, **add it now** — write a full paragraph or subsection for it.
- Each outline point should map to at least 50-100 words of content.

### Check 2: Fact-Check Absolute Claims

Search your draft for these signal words (in both Ukrainian and English):
**«унікальний»**, **«єдиний»**, **«перший»**, **«ніколи»**, **«жодний»**, **«тільки»**, **«лише»**, **unique**, **only**, **first**, **never**, **no other**, **the oldest**, **the most**

For EACH occurrence, ask: **Is this literally true? Can I name a counterexample?**
- If the claim is uncertain or an overgeneralization, **soften it now**:
  - «єдиний» → «один із небагатьох» or «характерний для»
  - «unique to Ukrainian» → «distinctive in Ukrainian» or «sets Ukrainian apart from its neighbors»
  - «the first» → «one of the earliest» or «among the first» (unless you have a citation)
  - «never» → «rarely» or «almost never» (unless it's a grammatical absolute)
- Historical dates and biographical facts: verify against the research file. If the research doesn't confirm it, **remove the claim**.

### Check 3: Section Word Counts

Count words per section. Compare against the `words:` allocation in the content_outline:
- If any section is below 70% of its budget → **expand it** (add examples, callouts, tables)
- If the total is below {WORD_TARGET} → expand the thinnest sections first
- Report the counts honestly in the `===WORD_COUNTS===` block

### Check 4: Anti-Surzhyk & Language Scan

Re-read your entire draft one more time looking for:
- Any Russianisms from the table above (кушати, получати, etc.)
- Any Russian characters (ы, э, ё, ъ)
- Any English words outside of parenthetical translations
- Any colonial framing ("Unlike Russian...", "Different from Russian...")
- If you find any, fix them now.

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

> **{INTRO_HOOK}**
>
> {2-3 sentences of significance}

## {Section 1 from content_outline}

### {Concept 1}
{{H3_WORD_RANGE} words: clear explanation with examples}

### {Concept 2}
{{H3_WORD_RANGE} words: same depth}

{comparison table or callout}

## {Section 2}

{Content — hit the Write Minimum for this section}

...

---

# {SUMMARY_HEADING}

{Summary + 4-6 self-check questions (~200 words)}

---

===CONTENT_END===
```

After the content block, report word counts per section:

```
===WORD_COUNTS===
Section "{name}": {count} words (minimum: {allocation})
...
Total: {total} words (target: {WORD_TARGET}, ratio: {total/WORD_TARGET}x)
===WORD_COUNTS===
```

Then report your verification results:

```
===VERIFICATION_START===
Plan compliance: {X}/{Y} outline points addressed (list any points you added during verification)
Absolute claims: {number checked} — {list each softened or removed claim, or "all verified"}
Language scan: {CLEAN or list of fixes made}
===VERIFICATION_END===
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
- Do NOT write fewer than {WORD_TARGET} words total. Do NOT write more than 150% of {WORD_TARGET} — excess prose is padding, not depth.
- Do NOT request skills or delegate to Claude
- Do NOT fabricate quotes, dates, or historical facts — if the research file doesn't confirm it, don't claim it
- Do NOT make absolute claims ("unique", "only", "first", "never") without verification — soften if uncertain
- Do NOT use straight quotes "..." — always «...»
