# Phase 2: Write the Lesson Content

> **Persona reminder:** You are {SKILL_IDENTITY}. Write in the voice of {PERSONA_FLAVOR}: {PERSONA_VOICE}. Maintain this persona throughout — do not drift into generic AI tone.

> **Your #1 job: Write 1374 words of rich, structured Ukrainian content.**
> Every concept gets dedicated depth. Every H3 gets 80-100+ words. This is how you hit the target.

## Files to Read

| File | Purpose |
|------|---------|
| `# Дослідження: My Family (Slug: my-family)

## State Standard Reference
§3.1: "Сім’я і члени сім’ї, родичі; статус інших людей з оточення (друг / подруга, колега, сусід / сусідка)." (UKRAINIAN-STATE-STANDARD-2024.txt, lines 481-488)
§4.2.1.1: Provides specific examples for A1 morphology using family terms: "мама (маму, на мамі), сестра (сестру, на сестрі), бабуся (бабусю, на бабусі), тато (тата, на татові), син (сина, на синові)." (lines 610-619)
Alignment: This module introduces the core vocabulary for family members and relatives as required by the thematic catalogue, while practicing the Nominative, Accusative, and Locative forms explicitly illustrated in the morphology section of the Standard.

## Vocabulary Frequency
| Word | Frequency / Source | Key collocations |
|------|-------------------|------------------|
| мама | High / General Corpus | рідна мама, молода мама, мама і тато |
| тато | High / General Corpus | рідний тато, мій тато, тато і мама |
| брат | High / General Corpus | старший брат, молодший брат, рідний брат |
| сестра | High / General Corpus | старша сестра, молодша сестра, рідна сестра |
| сім'я | High / General Corpus | велика сім'я, дружна сім'я, моя сім'я |
| родина | High / General Corpus | українська родина, велика родина |
| бабуся | High / General Corpus | стара бабуся, добра бабуся |
| дідусь | High / General Corpus | мудрий дідусь, мій дідусь |

## Cultural Hooks
1. **Multi-generational households**: In Ukraine, it is very common for multiple generations to live together or in close proximity. Grandparents (*бабуся і дідусь*) often play a central role in raising children while parents work. (Source: uvu.edu, visitukraine.today)
2. **"Rodyna" vs. "Sim'ya"**: While both mean family, *родина* (rodyna) often evokes a deeper sense of lineage and ancestry, connecting to the word *рід* (kin/lineage). It is a core concept in Ukrainian identity. (Source: common cultural linguistic analysis in teaching resources like "Dobra Forma").

## Common Learner Errors
1. **Gender Mismatch with Possessives**: English speakers often forget that possessives agree with the family member, not the speaker. Example: *Мій мама* → **Моя мама** (because *мама* is feminine).
2. **Man vs. Husband**: Confusion between *чоловік* (man/husband) and *дружина* (wife). Learners often try to use *жінка* for wife (which is common colloquially) but should learn *дружина* for clarity at A1.
3. **"Have" Construction**: Attempting a literal translation of "I have a brother" as *Я маю брата*. While grammatically correct, the more natural A1 construction is **У мене є брат**.

## Cross-References
- Builds on: `a1-14` (Mine and Yours - possessive pronouns), `a1-31` (Body and Health - vocabulary for physical description like "dark hair", "kind eyes").
- Prepares for: `a1-33` (Holidays and Traditions - family gatherings like Christmas/Easter), `a1-34` (Checkpoint Core Grammar).

## Notes for Content Writing
- Focus on the distinction between *близька родина* (nuclear family) and *розширена родина* (extended family).
- Ensure the Vocative forms (*мамо, тату, бабусю, дідусю*) are highlighted as they are very common in daily address but often skipped by beginners.
- Use simple adjectives from previous modules (A1-31) to describe family members (e.g., *Моя сестра добра і гарна*).
- Integrate the "U mene ye..." (У мене є...) construction as the primary way to talk about family count.
` | Factual foundation — use exhaustively |
| `slug: my-family
title: My Family
word_target: 916
` | Content outline with section word allocations |
| `module: a1-32
level: A1
sequence: 32
slug: my-family
version: '2.0'
title: My Family
subtitle: Родина
content_outline:
- section: Warm-up
  words: 104
  points:
  - Члени сім'ї (мама, тато, брат, сестра)
  - Питання про сім'ю
- section: Presentation
  words: 149
  points:
  - Близька родина (батьки, діти, брати, сестри)
  - Розширена родина (дідусь, бабуся, дядько, тітка)
  - Родинні стосунки (чоловік, дружина, онук, онука)
- section: Presentation 2
  words: 255
  points:
  - Вік (Моєму братові 25 років)
  - Професія (Мій тато — лікар)
  - Характер (Моя сестра дуже добра)
  - Зовнішність (Моя мама має темне волосся)
- section: Practice
  words: 101
  points:
  - Представлення своєї сім'ї
  - Розповідь про родину
- section: Practice 2
  words: 294
  points:
  - Діалог про сім'ю друга
  - Діалог про родинне свято
  - Показ сімейних фото
- section: Practice 3
  words: 13
  points:
  - Опис своєї сім'ї
word_target: 916
vocabulary_hints:
  required:
  - мама (mom)
  - тато (dad)
  - брат (brother)
  - сестра (sister)
  - дідусь (grandfather)
  - бабуся (grandmother)
  - син (son)
  - донька (daughter)
  recommended:
  - дядько (uncle)
  - тітка (aunt)
  - онук (grandson)
  - дружина (wife)
  - чоловік (husband)
  - родина (family)
activity_hints:
- type: match-up
  focus: Family member names
  items: 25
- type: match-up
  focus: Match relationships
  items: 20
- type: fill-in
  focus: Complete family descriptions
  items: 15
- type: fill-in
  focus: Describe your family
  items: 6
- type: match-up
  focus: Vocative forms (Nominative → Vocative)
  items: 10
- type: fill-in
  focus: Calling family members (vocative practice)
  items: 8
focus: vocabulary
pedagogy: PPP
prerequisites:
- a1-14 (Mine and Yours)
- a1-31 (Body and Health)
connects_to:
- a1-33 (Holidays and Traditions)
- a1-34 (Checkpoint Core Grammar)
objectives:
- Learner can name family members
- Learner can describe family relationships
- Learner can talk about their own family
- Learner can use possessives with family terms
- Learner can use basic vocative forms to address family members
grammar:
- Family vocabulary
- Possessives with family members
- Genitive for relationships (батько + name)
- Basic vocative forms (мамо, тату, бабусю, дідусю)
register: розмовний
phase: A1.3 [Consolidation]
persona:
  voice: Patient Supportive Tutor
  role: Family Genealogist
` | Objectives, vocabulary_hints (use ONLY these words) |
| `# A1 Quick Reference

## Workflow Integration

**A1 uses the 4-stage core workflow:**

1. **Write** → Create lesson content and activities manually
2. **Audit** → Validate content quality and completeness
3. **Generate** → Convert to MDX for Docusaurus
4. **Validate** → Final HTML testing and deployment

**Commands:**

- Start: Write content manually in curriculum/l2-uk-en/a1/
- Audit: `.venv/bin/python scripts/audit_module.py curriculum/l2-uk-en/a1/{slug}.md`
- Generate: `python scripts/generate_mdx.py l2-uk-en a1 {num}`
- Validate: Check MDX output in docusaurus/docs/a1/

**Reference:** `docs/SCRIPTS.md` for core workflow details.

## Relaxed Audit Limits

| Metric         | Target | WARN | FAIL |
| -------------- | ------ | ---- | ---- |
| Word count     | 750    | <750 | <650 |
| Activities     | 8      | <8   | <6   |
| Items/activity | 12     | <12  | <8   |

**WARN** = Passes with warning. **FAIL** = Blocks approval.

---

## Pre-flight Checklist

Before writing, confirm:

- [ ] Read module plan from `curriculum/l2-uk-en/plans/a1/{slug}.yaml` for content outline + vocabulary hints
- [ ] All frontmatter fields ready (see template below)
- [ ] Activity plan: 8+ activities, 4+ types, 12+ items each
- [ ] No duplicate explanations planned
- [ ] Immersion target: 10-40% (graduated by module)

## Metadata YAML Template (`meta/{slug}.yaml`)

```yaml
id: { NN }
slug: '{slug}'
title: '{Title}'
subtitle: '{Subtitle}'
version: '2.0'
phase: 'A1.1'
pedagogy: 'PPP'
duration: 45
transliteration: 'full'
tags: ['grammar', 'vocabulary', ...]
grammar: ['grammar-point-1']
objectives:
  - 'Learner can...'
  - 'Learner can...'
# vocabulary_count removed
```

## Content Requirements (Graduated)

| Module Range             | Core Words | Immersion |
| ------------------------ | ---------- | --------- |
| M01-05 (Phonetics)       | 300-450    | 10-15%    |
| M06-10 (First Verbs)     | 500-650    | 15-25%    |
| M11-20 (First Sentences) | 750+       | 25-35%    |
| M21-34 (Consolidation)   | 750+       | 35-40%    |

| Metric            | Target    |
| ----------------- | --------- |
| Vocabulary        | 20+ words |
| Example Sentences | 12+       |
| Engagement Boxes  | 3+        |
| Mini-Dialogues    | 2+        |

**Visual aids (grammar modules):** Use tables for paradigms, comparisons, and category summaries. Use mermaid flowcharts for decision logic (aspect, case selection). Not mandatory — use when they clarify better than prose.

## Activity Requirements

| Requirement        | Target |
| ------------------ | ------ |
| Total Activities   | 8+     |
| Items per Activity | 12+    |
| Unique Types       | 4+     |

### Minimum Item Counts (Schema Requirements)

| Activity Type | A1 Minimum | Notes                                   |
| ------------- | ---------- | --------------------------------------- |
| quiz          | 6 items    | —                                       |
| fill-in       | 6 items    | Must have `options: [...]` (4 per item) |
| true-false    | 6 items    | —                                       |
| match-up      | 6 pairs    | —                                       |
| unjumble      | 4 items    | —                                       |

**Note:** A1 doesn't use cloze, error-correction, select, or translate.

### Mandatory Activity Mix

| Type       | Min | Notes                       |
| ---------- | --- | --------------------------- |
| fill-in    | 2+  |                             |
| match-up   | 2+  |                             |
| quiz       | 1+  |                             |
| true-false | 1+  |                             |
| group-sort | 1+  |                             |
| anagram    | 2+  | M01-10 only, then phase out |
| unjumble   | 2+  | M11+ only                   |

**NOT used at A1:** error-correction, cloze, mark-the-words, select, translate

## Grammar Notes

### Reflexive Verbs (-ся/-сь)

- **Introduced:** M09 (Reflexive Verbs)
- **Key verbs:** називатися, сміятися, зустрічатися, прокидатися
- **Conjugation:** Add -ся after consonants, -сь after vowels
- **Example:** Я називаюсь Андрій (I am called Andriy)

### Verb Terminology

- **Preferred:** "Class I" (-ати verbs) and "Class II" (-ити verbs)
- **Alternative:** "First conjugation" and "Second conjugation" (Dobra Forma style)
- **Note:** Both terms are acceptable, but "Class I/II" aligns with modern Ukrainian linguistics

## Vocabulary YAML Format (`vocabulary/{slug}.yaml`)

Refer to `docs/dev/VOCAB_YAML_SCHEMA.md`.

```yaml
items:
  - lemma: слово
    ipa: /ˈslɔwɔ/
    translation: word
    pos: noun
    gender: n
```

## Transliteration Rules

| Module Range | Rule                  |
| ------------ | --------------------- |
| M01-10       | Full: слово (slovo)   |
| M11-20       | Vocab lists only      |
| M21-34       | First occurrence only |

## Structure (PPP)

1. `## Warm-up` - Hook and context
2. `## Presentation` - New material
3. `## Practice` - Controlled practice
4. `## Cultural Insight` - Optional
5. `## Summary` - Recap
` | Level constraints, immersion %, engagement minimums |

Read ALL four files before writing anything.

## Your Task

Write the full lesson prose for **My Family** (a1 track).

- **Total minimum**: 916 words
- **Write at least**: 1374 words (1.5x — aim for depth, not padding)
- **Immersion**: Write in Ukrainian, except for grammar explanations which should be in English.
- **Engagement callouts**: 5+ across sections, at least 4 different types
- **Example sentences**: 24+ in varied formats (inline, standalone, tables, dialogues)

## Section Word Budgets

**The global word target is the hard gate. Section budgets are guidance** — aim for each section's target, but natural variation (±30%) between sections is fine as long as no section is starved (<50% of its budget) and the total meets the global minimum.

{SECTION_BUDGET_TABLE}

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

## How to Hit 1374 Words (Expansion Method)

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

**Level-gated IPA rules:**
- **A1–A2**: Inline IPA transcriptions allowed in content (students learning pronunciation)
- **B1+**: Do NOT include inline IPA `[...]` transcriptions in the content markdown. IPA belongs ONLY in the vocabulary YAML file. Students at B1+ can read Cyrillic — cluttering prose with `[tʃɪˈtɑu̯]` breaks immersion and readability.

**When IPA IS used (A1–A2 content, or any vocabulary file):**
- ALL pronunciation MUST use IPA symbols. Latin transliterations are BANNED.

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
Total: {total} words (target: 916, ratio: {total/WORD_TARGET}x)
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
- Do NOT write fewer than 916 words total
- Do NOT request skills or delegate to Claude
- Do NOT fabricate quotes, dates, or historical facts
- Do NOT use straight quotes "..." — always «...»


## FIX PREVIOUS ERRORS
Your previous attempt failed validation with these errors:

```
Auditing: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/my-family.md
Saving log to: curriculum/l2-uk-en/krisztiankoos/audit/my-family-audit.log


========================================
  📋 Loaded Plan from: plans/a1/my-family.yaml
  📋 Loaded Metadata from YAML sidecar

📋 Auditing: A1 M32 — My Family
   File: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/my-family.md | Target: 916 words
  📋 Required activity types from meta: fill-in, match-up
  📋 Template: docs/l2-uk-en/templates/a1-module-template.md (pedagogy: PPP)
  ⚠️  Template violations: 1 critical, 0 warnings, 0 info
     🔴 [FORBIDDEN_HEADER] Forbidden header '## Vocabulary' violates Clean MD standard (Issue #398)

  📊 Section Word Analysis:
     Warm-up          189 /  104  ✅ (+85)
     Presentation     211 /  149  ✅ (+62)
     Presentation 2   279 /  255  ✅ (+24)
     Practice         119 /  101  ✅ (+18)
     Practice 2       147 /  294  ❌ (-147)
     Practice 3        24 /   13  ✅ (+11)
     ───────────────────────────────────────
     TOTAL            969 /  916  ✅ (+53)
❌ Structure check failed: Missing '## Activities' header OR activities sidecar
  ❌ Missing required activity types from meta.yaml: fill-in, match-up
  ✨ Purity violations found: 1
     ❌ [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'we use...'.

📚 IMMERSION TOO LOW (26.8% vs 35-55% target)
   FIX: Convert simple explanations to Ukrainian
   FIX: Add more Ukrainian narratives/dialogues
   FIX: Use Ukrainian for engagement boxes (💡🎬🌍)

--- STRICT GATES (Level A1) ---
Persona      ✅ Persona Defined
Words        ✅ 1131/916 (raw: 1268)
Activities   ❌ 0/8
Density      ❌ 0 < 12
Unique_types ❌ 0/4 types
Priority     ❌ No priority types
Engagement   ❌ 0/3
Audio        ℹ️ No audio
Vocab        ⚠️ 0 < 1 (soft target)
Structure    ❌ Missing '## Activities' header OR activities sidecar
Ipa          ⚠️ 2 IPA issues (run lint_ipa.py --fix)
Lint         ✅ Clean Format
Pedagogy     ❌ 4 violations
Content_heavy ℹ️ N/A (standard module)
Grammar      ℹ️ N/A (covered by naturalness)
Naturalness  ℹ️ PENDING — awaiting review
Activity_quality ℹ️ Quality validation N/A (A1/A2)
Immersion    ❌ 26.8% LOW (target 35-55% (M32))

📚 PEDAGOGICAL VIOLATIONS FOUND:
  [GRAMMAR] Instrumental case used at A1: 'нами'
     → FIX: Instrumental case not allowed until A2 (M36+). Restructure sentence.
  [HEADING_LEVEL] Main section 'Vocabulary' uses H2 (##) but spec requires H1 (#)
     → FIX: Change '## Vocabulary' to '# Vocabulary' for top-level TOC compliance
  [FORBIDDEN_HEADER] Forbidden header '## Vocabulary' violates Clean MD standard (Issue #398)
     → FIX: Remove '## Vocabulary' header. This section is auto-injected from vocabulary/{slug}.yaml at build time. See docs/l2-uk-en/templates/ for correct pattern.
  [ROBOTIC_STRUCTURE] Robotic structure: 3 sentences start with 'we use...'.
     → FIX: Vary sentence structure.


📋 TEMPLATE COMPLIANCE VIOLATIONS FOUND:
  🔴 [FORBIDDEN_HEADER] Forbidden header '## Vocabulary' violates Clean MD standard (Issue #398)
     → FIX: Remove '## Vocabulary' header. Template 'a1-module-template.md' specifies this section is auto-injected from YAML sidecars.


📝 RECOMMENDATION: UPDATE (patch fixes) (severity 70/100)
   → Revision recommended (severity 70/100)
   → 5 violations (moderate)
   → Immersion 8% off target (minor)
   → Structure issue: Missing '## Activities' header OR activities sidecar
   → Activity count below minimum
   → Activity density below minimum


Report: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/audit/my-family-audit.md
Status: /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/status/my-family.json

❌ AUDIT FAILED. Correct errors before proceeding.

Critical Failures:
  • 1 Critical Template Violations
  • Structure: Missing '## Activities' header OR activities sidecar
  • Missing required activity types: fill-in, match-up

❌ AUDIT FAILED (see curriculum/l2-uk-en/krisztiankoos/audit/my-family-audit.log for details)

```

Please fix these issues and regenerate the content.