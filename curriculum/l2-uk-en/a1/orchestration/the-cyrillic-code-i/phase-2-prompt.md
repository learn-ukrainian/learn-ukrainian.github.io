# Phase 2: Write the Lesson Content

> **Persona reminder:** You are Patient & Supportive Ukrainian Tutor. Write in the voice of Patient Supportive Tutor. Maintain this persona throughout — do not drift into generic AI tone.

> **Your #1 job: Write 3000 words of rich, structured Ukrainian content.**
> Every concept gets dedicated depth. Every H3 gets 80-100+ words. This is how you hit the target.

> **Output capacity: You can generate 65,000+ tokens per response.** A 2000-word Ukrainian module is ~4K tokens — well within your single-turn limit. Do NOT preemptively truncate, self-limit, or report TOKEN_LIMIT_TRUNCATION friction. Write the complete module in full.

## Files to Read

| File | Purpose |
|------|---------|
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/the-cyrillic-code-i-research.md` | Factual foundation — use exhaustively |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/meta/the-cyrillic-code-i.yaml` | Content outline with section word allocations |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/the-cyrillic-code-i.yaml` | Objectives, vocabulary_hints (use ONLY these words) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion %, engagement minimums |

Read ALL four files before writing anything.

## Primary Source Excerpts (Cite These — Don't Invent Quotes)

These passages were retrieved from indexed primary sources (litopys.org.ua). When you need to cite a primary source, prefer these verified passages over inventing quotes from memory. You may paraphrase or excerpt, but attribute correctly.

(No primary source excerpts available from RAG)

## Resource Discoveries

These resources were found during the discover phase. They include videos, blog articles, textbook references, and images where available.

- **Videos**: Consider embedding relevant ones as `{% youtubeVideo %}` components where they add value
- **Textbook references**: Use these as authoritative sources for grammar explanations and examples. Cross-reference your content against these real Ukrainian textbook explanations.
- **Textbook images**: If high-quality images were found, consider referencing them in your lesson. Describe what they illustrate when relevant.
- **Literary sources**: For seminar tracks, use these primary source excerpts as evidence and quotation material.

(No video discoveries available)
### Research Videos
*These videos were found during the research phase. Embed each one next to its corresponding letter/topic section using a markdown link.*

- Anna Ohoiko — Ukrainian Alphabet: Pronunciation, Writing & Examples — https://www.youtube.com/watch?v=ksXIXj7CXwc

### Per-Letter Pronunciation Videos (from plan — MANDATORY embeds)
*Credit: Anna Ohoiko — Ukrainian Lessons*

- **Overview**: https://www.youtube.com/watch?v=ksXIXj7CXwc
- **Full Playlist**: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV

**Each letter below MUST get its video embedded in the corresponding H3 section:**

- **Літера А**: https://www.youtube.com/watch?v=hvB3VpcR3ZE
- **Літера М**: https://www.youtube.com/watch?v=Ez95H4ibuJo
- **Літера Л**: https://www.youtube.com/watch?v=v6-3Xg52Buk
- **Літера У**: https://www.youtube.com/watch?v=VB1O6PmtYRU
- **Літера Н**: https://www.youtube.com/watch?v=vNUfiKHPYaU
- **Літера С**: https://www.youtube.com/watch?v=7UsFBgSL91E

## Module Sequence Constraints (HARD FAIL if violated)

DECODABILITY (M1 — 6 known letters: А, М, Л, У, Н, С):
- Words in reading drills MUST use ONLY these 6 letters (e.g., мама, сума, луна, мул, нам)
- Words with unknown letters (кіт, вода, привіт) may appear ONLY as labelled vocabulary with immediate English translation: «Привіт!» (Hello!)
- Video example words for the letter being taught (ананас for А) are fine — they are heard, not read

GRAMMAR BAN (no verbs exist yet in the student's knowledge):
- NO imperative forms: Слухайте, Читайте, Повторюйте, Пишіть, Дивіться — ALL BANNED
- NO verb conjugation of any kind (present, past, future)
- Classroom instructions MUST be in English: 'Listen carefully', 'Read aloud', 'Repeat after the video'
- Allowed Ukrainian structures: bare nouns only (мама, сума, луна)

METALANGUAGE:
- ALL terminology in English first, Ukrainian in parentheses: 'vowels (голосні)', 'consonants (приголосні)'
- Section headings MUST be bilingual as shown in the content_outline (e.g., '## Голосні — Vowels')
- NEVER write Ukrainian-only section headers or explanatory prose — the student cannot read it yet

> **These constraints enforce what the student has actually learned so far.** Using letters, grammar forms, or vocabulary from future modules is a pedagogical error — the student literally cannot parse text with letters they haven't been taught. Violations will be caught in review.

---

## Your Task

Write the full lesson prose for **The Cyrillic Code I** (a1 track).

- **Total minimum**: 2000 words
- **Write at least**: 3000 words (1.5x — aim for depth, not padding)
- **Immersion**: TARGET: 5-15% Ukrainian, 85-95% English. ALL explanatory prose in English. ALL grammar explanations in English. ALL callout text in English. Ukrainian appears ONLY in: (1) example words/phrases in bold with [IPA] and (English translation), (2) vocabulary items. If you write a paragraph, it MUST be in English. Ukrainian sentences max 10 words.
- **Engagement callouts**: 4+ across sections, at least 4 different types
- **Example sentences**: 8+ in varied formats (inline, standalone, tables, dialogues)

## Downstream Audit Gates (your content will be checked for)

Write with these in mind — errors here trigger Phase D repair cycles:
- **Word count**: minimum **2000** words (hard gate)
- **Colonial framing**: NEVER define Ukrainian by contrast with Russian (hard fail)
- **Russianisms**: banned words — кушати, приймати участь, получати, самий кращий, слідуючий (hard fail)
- **Russian characters**: ы, э, ё, ъ must NEVER appear (hard fail)
- **Euphony**: і/й, у/в, з/із alternation (auto-fixable but better to write correctly)
- **Engagement callouts**: 4+ using counted types ([!tip], [!warning], [!quote], [!myth-buster], [!culture], [!fact], [!context], [!reflection], [!note])
- **Duplicate headers**: no two H2s sharing the same keyword (e.g., two headers containing «спадщина»)

---

## Section Word Budgets

**The global word target is the hard gate. Section budgets are guidance** — aim for each section's target, but natural variation (±30%) between sections is fine as long as no section is starved (<50% of its budget) and the total meets the global minimum.

| Section | Target | Write Minimum (1.5x) |
|---------|--------|---------------------|
| Вступ — Introduction | 300 | 450 |
| Голосні — Vowels: А, У | 400 | 600 |
| Приголосні — Consonants: М, Л, Н, С | 500 | 750 |
| Перші склади — First Syllables | 350 | 525 |
| Практика читання — Reading Practice | 250 | 375 |
| Підсумок — Summary | 200 | 300 |
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

FORBIDDEN: 5+ consecutive examples in the same format (bullet lists, `_Приклад:_` blocks, `**Ukrainian.** (English.)` lines — any uniform pattern). Mix these formats across sections:
- Standalone examples with context (max 3-4 consecutive in one format)
- **Comparison tables** (paradigms, aspect pairs, case usage)
- Inline examples woven into prose
- **Mini-dialogues** showing real usage
- Callout boxes with examples

**Anti-batching rule**: If you notice 3+ sections each presenting examples as identical bullet lists, STOP and vary the format. Use a table in one section, inline examples in another, a dialogue in a third.

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

The Summary section MUST include 4-6 self-assessment questions:

```markdown
**Check yourself:**
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

### Rule 9: Prefer Active Voice

Ukrainian strongly prefers active constructions. Use passive only when:
- The agent is truly unknown: «Книгу було знайдено» (who found it is irrelevant)
- Emphasis is intentionally on the object, not the actor

Avoid: «Це може бути використано...», «Правило застосовується...»
Prefer: «Ви можете використати...», «Ми застосовуємо правило...»

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

```markdown
❌ WRONG (Latin transliteration):
"Х sounds like 'kh' in Scottish 'loch'"
"хліб (khlib)"

✅ RIGHT (stress mark + English approximation):
"**Х**, like the «ch» in Scottish «loch»"
"**хлі́б** — like English «hleeb» but with a «ch» sound"
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

Open the `content_outline` from `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/meta/the-cyrillic-code-i.yaml`. Go through EVERY `points:` item in EVERY section:
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
- If the total is below 2000 → expand the thinnest sections first
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

> **Why does this matter?**
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

# Summary

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
- Do NOT write fewer than 2000 words total
- Do NOT request skills or delegate to Claude
- Do NOT fabricate quotes, dates, or historical facts — if the research file doesn't confirm it, don't claim it
- Do NOT make absolute claims ("unique", "only", "first", "never") without verification — soften if uncertain
- Do NOT use straight quotes "..." — always «...»
