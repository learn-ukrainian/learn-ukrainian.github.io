# Phase Fix-Content: Audit Fix (Attempt 1)

> **You are Gemini, executing a targeted content fix.**
> **Your ONLY task: Fix the CONTENT file based on the audit failures below.**
> **Do NOT output activities or vocabulary — only the fixed content.**

## Your Input

Read the current content (the file you are fixing):
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/how-to-talk-about-grammar.md
```

Read the plan file:
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/b1/how-to-talk-about-grammar.yaml
```

Read the research notes:
```
/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/b1/research/how-to-talk-about-grammar-research.md
```

## Audit Failures to Fix

### 1. CRITICAL: Callout Format (0/4 engagement boxes detected)

**Problem:** ALL callouts are missing the `>` blockquote prefix. The audit cannot detect them.

**Current WRONG format:**
```
[!tip] **Title**
Text here
```

**Required CORRECT format:**
```
> [!tip] Title
>
> Text here. Every line of the callout must start with `>`.
```

**Fix:** Convert ALL callouts to blockquote format. Every line inside a callout MUST start with `> `. The title line format is `> [!type] Title` (no bold `**` on the title).

### 2. Word Count Deficits (3875/4000 audited)

Expand these sections to meet targets:

| Section | Current | Target | Action |
|---------|---------|--------|--------|
| Самостійні категорії | 508 | 750 | Add ~250 words: expand usage notes, add more context per POS |
| Граматичні категорії | 509 | 650 | Add ~150 words: expand рід/число/особа/час/вид explanations |
| Службові слова | 508 | 600 | Add ~100 words: deepen usage notes |
| Відмінки: сім ключів | 707 | 800 | Add ~100 words: expand 2-3 case descriptions |

### 3. Transliteration / English Contamination

**Problem:** The audit found English in parentheses outside the introduction section. At 93.5% immersion, English is only allowed in the Вступ section.

**Fix:** Remove ALL English translations in parentheses EXCEPT in the Вступ section. Specific removals:
- "(noun)" after Іменник → remove
- "(verb)" after Дієслово → remove
- "(adjective)" after Прикметник → remove
- "(adverb)" after Прислівник → remove
- "(pronoun)" after Займенник → remove
- "(numeral)" after Числівник → remove
- "(conjunction)" after Сполучник → remove
- "(preposition)" after Прийменник → remove
- "(particle)" after Частка → remove
- "(interjection)" after Вигук → remove
- "(subject)" after підмет → remove
- "(predicate)" after присудок → remove
- "(object)" after додаток → remove
- "(attribute)" after означення → remove
- "(adverbial)" after обставина → remove
- "(nominative case)" etc. → remove all case English translations
- "(morphemics)" after морфеміки → remove
- "(root)", "(prefix)", "(suffix)", "(ending)" → remove
- "(person)", "(number)", "(tense)", "(aspect)", "(gender)" → remove
- "(to connect)" → remove
- "(word)", "(sentence)", "(grammar)", "(rule)", "(example)" → remove from Вступ too if outside the intro paragraphs

**Keep English ONLY in:**
- The 2 English bridging paragraphs in the Вступ section (starting with "Starting from this module...")
- Parenthetical translations of key structural terms in the FIRST occurrence in the Вступ: (word), (sentence), (grammar), (rule), (example), (parts of speech) — these 6 bridge terms only

### 4. Historical Cyrillic Characters

**Problem:** Historical Cyrillic characters ѧ, ѵ found in the Smotrytsky reference outside a `[!quote]` callout.

**Fix:** Wrap the Smotrytsky book title in a `[!quote]` callout, or replace with a modern transliteration of the title.

### 5. Sentence Length

**Problem:** One sentence is 26 words (max 25 for B1).

**Fix:** Find and split: "Коли ви аналізуєте речення як систему, ви перестаєте робити випадкові помилки в закінченнях, бо бачите логіку зв'язків між «господарем» (підметом) та його «слугами» (другорядними членами речення)."

Split into two sentences.

## Rules

1. **Apply EVERY fix** listed above — do not skip any
2. **Output the COMPLETE fixed content file** — all sections, not just changed parts
3. **Preserve structure** — keep the same H2/H3 headings
4. **Preserve voice** — do not change the writing style of unflagged content
5. **All new content must be in Ukrainian** — no new English text
6. **Use angular quotes** `«...»` for all Ukrainian quotes

## Output Format

**CRITICAL: Output the COMPLETE fixed content between these delimiter lines.**

```
===CONTENT_START===
(complete fixed content markdown — ALL of it, not just changed parts)
===CONTENT_END===
```

After the content:

```
===FRICTION_START===
**Phase**: Phase 4: Fix Content (Audit)
**Step**: {description}
**Friction Type**: NONE | ...
**Raw Error**: {or "None"}
**Self-Correction**: {or "N/A"}
**Proposed Tooling Fix**: {or "N/A"}
===FRICTION_END===
```
