# Phase 2 Fix #2: Content Word Count Expansion

> **You are Gemini, fixing Phase 2 content that failed audit on word count.**

## Current Content (READ FROM DISK)

```
curriculum/l2-uk-en/b1/how-to-talk-about-grammar.md
```

## Audit Failures

The audit found these section word count shortfalls:

| Section | Current | Target | Gap |
|---------|---------|--------|-----|
| Частини мови: самостійні категорії та їхні ролі | 413 | 750 | -337 |
| Будова слова, граматичні категорії та синтаксис | 385 | 650 | -265 |
| Частини мови: службові слова та вигуки | 413 | 600 | -187 |
| Відмінки: сім ключів до системи відмінювання | 622 | 800 | -178 |
| Вступ: психологія та логіка української метамови | 448 | 550 | -102 |
| **TOTAL** | **3869** | **4000** | **-131 (after stripping)** |

### Also fix: Historical Characters

Line 32 contains historical Cyrillic characters (ѵ, ѧ) in the Smotrytskyj book title. Wrap the book title in a `[!quote]` callout to mark it as authentic historical text, or use modern Ukrainian spelling for the title.

## Expansion Instructions

**Section 2 (Самостійні частини мови)** — need +337 words:
- Each H3 (Іменник, Дієслово, Прикметник, etc.) needs longer definitions (2+ sentences)
- Add usage notes to each H3 (e.g., "Прикметники завжди узгоджуються з іменником у роді, числі та відмінку")
- Expand the existing [!observe] and [!tip] callouts with more content
- Add 1 more callout ([!observe] asking student to classify words in a sample sentence)

**Section 5 (Будова слова, граматичні категорії та синтаксис)** — need +265 words:
- Морфеміка: Add concrete decomposition example (e.g., пере-чит-ува-ти: prefix=пере, root=чит, suffix=ува, ending=ти)
- Граматичні категорії: Add 1 example sentence for each category
- Синтаксичні ролі: Add a parsed sentence showing all roles marked

**Section 3 (Службові слова та вигуки)** — need +187 words:
- Each H3 needs a richer real-context example
- Add connection to grammar rules (how each service word appears in textbook instructions)
- Add 1 callout

**Section 4 (Відмінки)** — need +178 words:
- Expand "Додаткова інформація" for at least 3 cases
- Add etymology for 2 more cases (e.g., Родовий ← рід, Орудний ← орудувати)

**Section 1 (Вступ)** — need +102 words:
- Expand the Смотрицький paragraph with 1-2 more historical details
- Add 1 more etymological comparison

## Output Format

Return the COMPLETE expanded content (not just changes):

```
===CONTENT_START===
{full expanded content}
===CONTENT_END===
```

## Boundaries

- Do NOT change H2/H3 structure
- Do NOT remove existing content — only EXPAND
- Do NOT add new sections
- Wrap the historical book title in [!quote] callout
