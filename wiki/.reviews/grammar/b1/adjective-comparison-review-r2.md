✅ Message sent to Gemini (ID: 28285) [auto-acked: self-addressed]

🚀 Invoking Gemini to process message #28285...
📨 Message #28285
   From: gemini → To: gemini
   Type: query
   Task: wiki-review-b1-adjective-comparison-r2
   Time: 2026-04-06T07:49:27.905947+00:00

============================================================

You are a HARSH adversarial reviewer of a grammar brief for the Ukrainian language curriculum wiki. Your job is to find problems, not praise.

Track: b1, Slug: adjective-comparison, Round: 2

## Review Rubric (score EACH dimension 1-10, then average)

1. **Factual accuracy** — every claim must have evidence from sources. Vague or unsourced claims → deduct points.
2. **Ukrainian language quality** — check for Russianisms (кон→кін), surzhyk (шо→що), calques (приймати душ→брати душ). Even ONE Russianism = max 7/10.
3. **Decolonization** — is Ukrainian presented on its own terms? Any 'like Russian but...' framing = max 6/10.
4. **Completeness** — does it cover ALL aspects a module writer needs? Missing sections or shallow treatment → deduct.
5. **Actionable guidance** — can a writer actually USE this? Generic advice like 'teach it well' = max 5/10. Must have specific examples, sequences, exercises.

## Rules
- Score each dimension separately, then give weighted average.
- Be honest. If the article is excellent, say so. 10/10 IS possible.
- 9/10 = excellent with minor issues. 8/10 = good. 7/10 = needs work.
- Output a <fixes> block with specific changes. If the article is clean, output <fixes></fixes> (empty).
- Do NOT invent problems. Fabricated issues waste rebuild cycles.

## Fix syntax

Two formats are available:

**1. Replace existing text** (for corrections, rewording):
Use a SHORT anchor (1-2 sentences max) for the old: text. Do NOT paste massive paragraphs — they break exact matching.
```
old: short exact text to find
new: replacement text
```

**2. Insert new content** (for missing sections, added examples):
Use INSERT AFTER with a short anchor from the article, then the new text to add.
```
INSERT AFTER: short anchor text that exists in the article
NEW TEXT: the new content to insert after the anchor
```

Separate multiple fixes with `---`.

## Output format

Dimension scores:
1. Factual: X/10 — [evidence]
2. Language: X/10 — [evidence]
3. Decolonization: X/10 — [evidence]
4. Completeness: X/10 — [evidence]
5. Actionable: X/10 — [evidence]

**Overall: X/10**

<fixes>
old: exact text to find in the article
new: replacement text
---
INSERT AFTER: anchor text in article
NEW TEXT: content to add after the anchor
</fixes>

## Article to review

# Граматика B1: Ступені порівняння прикметників

<!-- wiki-meta
slug: adjective-comparison
domain: grammar/b1
tracks: [b1, b2]
sources: [4-klas-ukrayinska-mova-kravtsova-2021-1_s0070, 6-klas-ukrmova-golub-2023_s0134, 7-klas-ukrmova-litvinova-2024_s0147, 6-klas-ukrmova-golub-2023_s0133, 6-klas-ukrmova-avramenko-2023_s0133, 10-klas-ukrmova-karaman-2018_s0280, 6-klas-ukrmova-avramenko-2023_s0132, 6-klas-ukrmova-golub-2023_s0133, 6-klas-ukrmova-golub-2023_s0134, 6-klas-ukrmova-zabolotnyi-2020_s0139, 7-klas-ukrmova-avramenko-2024_s0021, 7-klas-ukrmova-avramenko-2024_s0153, 7-klas-ukrmova-zabolotnyi-2024_s0021, 7-klas-ukrmova-zabolotnyi-2024_s0154, 8-klas-ukrmova-zabolotnyi-2025_s0032, 11-klas-ukrajinska-mova-avramenko-2019_s0041, 11-klas-ukrajinska-mova-avramenko-2019_s0044, 11-klas-ukrajinska-mova-glazova-2019_s0022, 6-klas-ukrmova-avramenko-2023_s0133, 6-klas-ukrmova-betsa-2023_s0121, 6-klas-ukrmova-litvinova-2023_s0205, 6-klas-ukrmova-zabolotnyi-2020_s0138, 7-klas-ukrmova-zabolotnyi-2024_s0021, 7-klas-ukrmova-litvinova-2024_s0147, 7-klas-ukrmova-zabolotnyi-2024_s0153, 7-klas-ukrmova-zabolotnyi-2024_s0155, 9-klas-ukrajinska-mova-voron-2017_s0287, 10-klas-ukrmova-karaman-2018_s0274, 10-klas-ukrmova-karaman-2018_s0277, 10-klas-ukrmova-karaman-2018_s0354, 10-klas-ukrmova-karaman-2018_s0282, 11-klas-ukrajinska-mova-glazova-2019_s0023, 8-klas-ukrmova-zabolotnyi-2025_s0044, 10-klas-ukrajinska-mova-avramenko-2018_s0230]
compiled: 2026-04-06
-->

## Як це пояснюють у школі (How Schools Teach This)

The concept of degrees of comparison (`ступені порівняння`) is introduced early, around grade 4, with a simple explanation: adjectives can express different degrees of a quality (Source 1). The formal, detailed study happens in grades 6-7, where students learn the core terminology and paradigms.

The pedagogical approach is consistent across major textbook authors (Заболотний, Авраменко, Голуб):

1.  **Prerequisite:** The concept is tied exclusively to **якісні прикметники** (qualitative adjectives), those denoting a quality that can vary in degree. This distinction from relative and possessive adjectives is fundamental (Source 11, 22).
2.  **Core Terminology:** Two degrees are defined:
    *   **Вищий ступінь** (Comparative degree): "more" of a quality (`сильніший`, `більш сильний`).
    *   **Найвищий ступінь** (Superlative degree): "most" of a quality (`найси

## Instructions
1. Read the critique carefully.
2. Identify which SPECIFIC sections need rewriting to address the critique.
3. Output the COMPLETE article with those sections rewritten.
4. Do NOT remove or degrade sections that scored well.
5. Do NOT add commentary — output ONLY the article markdown.

## Current article

# Граматика B1: Ступені порівняння прикметників

<!-- wiki-meta
slug: adjective-comparison
domain: grammar/b1
tracks: [b1, b2]
sources: [4-klas-ukrayinska-mova-kravtsova-2021-1_s0070, 6-klas-ukrmova-golub-2023_s0134, 7-klas-ukrmova-litvinova-2024_s0147, 6-klas-ukrmova-golub-2023_s0133, 6-klas-ukrmova-avramenko-2023_s0133, 10-klas-ukrmova-karaman-2018_s0280, 6-klas-ukrmova-avramenko-2023_s0132, 6-klas-ukrmova-golub-2023_s0133, 6-klas-ukrmova-golub-2023_s0134, 6-klas-ukrmova-zabolotnyi-2020_s0139, 7-klas-ukrmova-avramenko-2024_s0021, 7-klas-ukrmova-avramenko-2024_s0153, 7-klas-ukrmova-zabolotnyi-2024_s0021, 7-klas-ukrmova-zabolotnyi-2024_s0154, 8-klas-ukrmova-zabolotnyi-2025_s0032, 11-klas-ukrajinska-mova-avramenko-2019_s0041, 11-klas-ukrajinska-mova-avramenko-2019_s0044, 11-klas-ukrajinska-mova-glazova-2019_s0022, 6-klas-ukrmova-avramenko-2023_s0133, 6-klas-ukrmova-betsa-2023_s0121, 6-klas-ukrmova-litvinova-2023_s0205, 6-klas-ukrmova-zabolotnyi-2020_s0138, 7-klas-ukrmova-zabolotnyi-2024_s0021, 7-klas-ukrmova-litvinova-2024_s0147, 7-klas-ukrmova-zabolotnyi-2024_s0153, 7-klas-ukrmova-zabolotnyi-2024_s0155, 9-klas-ukrajinska-mova-voron-2017_s0287, 10-klas-ukrmova-karaman-2018_s0274, 10-klas-ukrmova-karaman-2018_s0277, 10-klas-ukrmova-karaman-2018_s0354, 10-klas-ukrmova-karaman-2018_s0282, 11-klas-ukrajinska-mova-glazova-2019_s0023, 8-klas-ukrmova-zabolotnyi-2025_s0044, 10-klas-ukrajinska-mova-avramenko-2018_s0230]
compiled: 2026-04-06
-->

## Як це пояснюють у школі (How Schools Teach This)

The concept of degrees of comparison (`ступені порівняння`) is introduced early, around grade 4, with a simple explanation: adjectives can express different degrees of a quality (Source 1). The formal, detailed study happens in grades 6-7, where students learn the core terminology and paradigms.

The pedagogical approach is consistent across major textbook authors (Заболотний, Авраменко, Голуб):

1.  **Prerequisite:** The concept is tied exclusively to **якісні прикметники** (qualitative adjectives), those denoting a quality that can vary in degree. This distinction from relative and possessive adjectives is fundamental (Source 11, 22).
2.  **Core Terminology:** Two degrees are defined:
    *   **Вищий ступінь** (Comparative degree): "more" of a quality (`сильніший`, `більш сильний`).
    *   **Найвищий ступінь** (Superlative degree): "most" of a quality (`найсильніший`, `найбільш сильний`).
3.  **Two Forms:** Each degree has two forms of creation:
    *   **Проста форма** (Simple form): Morphological, using suffixes and prefixes (e.g., `цікавіший`, `найцікавіший`).
    *   **Складена форма** (Compound form): Analytical, using additional words `більш`/`менш` or `найбільш`/`найменш` (e.g., `більш цікавий`, `найбільш цікавий`).
4.  **Presentation:** The rules are almost universally presented in tables, clearly separating the degrees and forms (Source 7, 8, 10, 18, 28). This structure is a core part of the teaching methodology.
5.  **Key Focus Areas:** Special attention is given to irregular (suppletive) forms like `гарний → кращий` and the consonant changes (`високий → вищий`) that occur during formation (Source 2, 5, 9, 19). A significant amount of time is also spent on identifying adjectives that *cannot* form degrees of comparison and correcting common errors, especially the use of `самий` instead of `най-` (Source 7, 9, 11).

## Повна парадигма (Full Paradigm)

Only **qualitative adjectives** can form degrees of comparison.

### Вищий ступінь (Comparative Degree)

Indicates that a quality is present in a greater or lesser degree in one object compared to another.

| Форма (Form) | Спосіб утворення (Formation Method) | Приклади (Examples) |
| :--- | :--- | :--- |
| **Проста** (Simple) | Основа прикметника + суфікси **-іш-**, **-ш-**<br/>*Adjective stem + suffixes **-ish-**, **-sh-*** | `теплий → тепліший`<br/>`дешевий → дешевший`<br/>`широкий → ширший` |
| **Складена** (Compound) | **більш**, **менш** + прикметник у початковій формі<br/>***more**, **less** + adjective in its base form* | `більш теплий`, `менш теплий`<br/>`більш складний`, `менш складний` |

### Найвищий ступінь (Superlative Degree)

Indicates the highest or lowest degree of a quality.

| Форма (Form) | Спосіб утворення (Formation Method) | Приклади (Examples) |
| :--- | :--- | :--- |
| **Проста** (Simple) | Префікс **най-** + проста форма вищого ступеня<br/>*Prefix **nay-** + simple comparative form* | `най- + тепліший → найтепліший`<br/>`най- + ширший → найширший`<br/>`най- + кращий → найкращий` |
| **Складена** (Compound) | **найбільш**, **найменш** + прикметник у початковій формі<br/>***most**, **least** + adjective in its base form* | `найбільш теплий`, `найменш теплий`<br/>`найбільш складний` |
| **Складена** (Compound) | Проста форма вищого ступеня + **за всіх**, **від усіх**, **над усе**<br/>*Simple comparative + "than all", "of all", "above all"* | `сильніший за всіх`<br/>`миліша над усе`<br/>`кращий від усіх` |

---

### Особливості творення (Formation Specifics)

#### 1. Суплетивні форми (Suppletive Forms)

A few key adjectives form degrees of comparison from a different root. These must be memorized.
(Source 2, 5, 9, 20, 34)

*   `гарний`, `хороший` (good, nice) → **кращий** (better), **найкращий** (best)
*   `поганий` (bad) → **гірший** (worse), **найгірший** (worst)
*   `великий` (big) → **більший** (bigger), **найбільший** (biggest)
*   `малий` (small) → **менший** (smaller), **найменший** (smallest)
*   `добрий` (good, kind) → **ліпший** (better) or **кращий** (better)

#### 2. Зміни приголосних (Consonant Alternation)

When the suffix **-ш-** is added, certain stem consonants change. (Source 9, 19, 30, 33, 35)

*   **[г], [ж], [з]** + `-ш-` → **[жч]**
    *   `доро**г**ий → доро**жч**ий`
    *   `ва**ж**кий → ва**жч**ий`
    *   `бли**з**ький → бли**жч**ий`
*   **[с]** + `-ш-` → **[шч]** (written as **щ**)
    *   `ви**с**окий → ви**щ**ий`
    *   `тов**с**тий → тов**щ**ий`

#### 3. Випадання суфіксів (Suffix Dropping)

The suffixes **-к-**, **-ок-**, **-ек-** drop out before forming degrees of comparison. (Source 14, 34, 35)

*   `тон**к**ий → тонший`
*   `шир**ок**ий → ширший`
*   `дал**ек**ий → дальший`

#### 4. Підсилення (Emphasis)

The superlative form can be intensified with the prefixes **як-** and **що-**. (Source 2, 9, 18, 34)

*   `якнайкращий` (the very best)
*   `щонайсильніший` (the absolute strongest)

---

### Прикметники, що НЕ утворюють ступенів порівняння

(Source 9, 10, 16, 19, 33, 43)

*   **Absolute qualities** that cannot be graded: `сліпий` (blind), `лисий` (bald), `босий` (barefoot), `мертвий` (dead), `порожній` (empty).
*   **Compound adjectives**: `світло-зелений` (light-green), `чорноокий` (black-eyed).
*   **Adjectives with suffixes or prefixes that already indicate degree**: `предобрий` (very good), `малесенький` (tiny), `синюватий` (bluish), `здоровенний` (huge).
*   **Colors derived from nouns**: `вишневий` (cherry-colored), `шоколадний` (chocolate-colored), `лимонний` (lemon-colored).
*   **Animal coat colors (масті)**: `вороний` (black), `гнідий` (bay).
*   Adjectives that have shifted from relative to qualitative: `золоті руки` (golden hands), `вовчий апетит` (wolf's appetite).

## Частотність і пріоритети (Frequency & Priorities)

1.  **Пріоритет №1: Проста форма (Simple Form)**. The simple forms (`-іший`/`-ший` and `най-...-іший`/`най-...-ший`) are the most common, natural, and stylistically neutral forms in Ukrainian. They are used across all styles, from colloquial speech to formal writing. B. Антоненко-Давидович and other linguists note that "жива народна мова віддавали перевагу... простій [формі]" (Source 6, 18). Mastery of this form is essential for sounding like a native speaker.

2.  **Пріоритет №2: Суплетивні форми (Suppletive Forms)**. The irregulars (`кращий`, `гірший`, `більший`, `менший`) are high-frequency words and are non-negotiable for basic communication.

3.  **Пріоритет №3: Складена форма (Compound Form)**. The compound forms (`більш`, `найбільш`) are less frequent in spoken language. They carry a "книжний" (bookish) or formal tone and are more common in academic and official-business styles (Source 18, 43). For L2 learners, passive understanding is important, but overuse in active speech can sound unnatural and stilted.

**Conclusion for Learners**: Focus 90% of practice on creating and using the **simple forms**. Use the compound forms only when seeking a specific formal or analytical tone.

## Типові помилки L2 (Common L2 Errors)

This is a high-error area for English speakers due to structural differences and influence from Russian.

1.  **Помилка: Вживання `самий` для творення найвищого ступеня.**
    *   **Неправильно:** `*Це самий цікавий фільм.` `*Самий кращий день.`
    *   **Причина:** Прямий переклад з російської (`самый интересный`).
    *   **Правильно:** `Це **найцікавіший** фільм.` `**Найкращий** день.` (Source 2, 7, 9, 20, 42). Use the prefix **`най-`**.

2.  **Помилка: Подвійне ступенеутворення (Double Comparison).**
    *   **Неправильно:** `*Ця книга більш цікавіша.` `*Найбільш розумніший студент.`
    *   **Причина:** Mixing the simple (`-іш-`) and compound (`більш`) forms. English speakers might do this by analogy with "more interesting".
    *   **Правильно:** Choose one form: `Ця книга **більш цікава**` (compound) OR `Ця книга **цікавіша**` (simple). `**Найбільш розумний** студент` OR `**Найрозумніший** студент`. (Source 7, 11, 30, 37, 42).

3.  **Помилка: Неправильна конструкція порівняння.**
    *   **Неправильно:** `*Він старший мене.` `*Дуб вищий берези.`
    *   **Причина:** Using the genitive case for comparison, a direct calque from Russian (`старше меня`).
    *   **Правильно:** Use prepositions `за` or `ніж`, or `від`.
        *   `Він старший **за** мене.`
        *   `Дуб вищий, **ніж** береза.`
        *   `Дим рідної країни ясніший **від** вогню чужини.` (Source 30)

## Деколонізаційні застереження (Decolonization Notes)

Teaching Ukrainian grammar requires actively unlearning assumptions based on Russian. The degrees of comparison are a prime example.

1.  **`Най-` vs. `Самый`:** This is the single most important distinction. The superlative prefix `най-` is a core feature of the Ukrainian language. The use of `самий` is a clear marker of Russification or surzhyk. Emphasize that `най-` is not an "alternative" but the **only** correct way to form the simple superlative.

2.  **`за/ніж` vs. Genitive Case:** The standard Ukrainian comparative construction uses `...-іший/-ший за/ніж...` (`дешевш**ий за** хліб`, `сильн**іший, ніж** я`). The Russian construction using the genitive case (`дешевле хлеба`) is incorrect in standard literary Ukrainian and should be actively corrected. While it might be heard in surzhyk, it is not the grammatical norm.

3.  **Стилістична перевага простої форми (Stylistic Primacy of the Simple Form):** As noted in Source 6 and 18, the simple form (`розумніший`, `найрозумніший`) is more organic and preferred in the Ukrainian language tradition. The heavy use of compound forms (`більш розумний`) can sometimes be a remnant of the formal, bureaucratic language style (`канцелярит`) that was prevalent in the Soviet era, which often drew from Russian patterns. Encouraging the simple form promotes a more authentic Ukrainian style.

## Природні приклади (Natural Examples)

1.  `Брат **вищий за** сестру.` (Source 20) - Simple comparative with `за`.
2.  `Що ніч **темніша**, то день **видніший**.` (Source 19, 35) - Common "the...the..." construction.
3.  `Добре ім’я **дорожче за** великі багатства.` (Source 35) - Irregular form `дорожчий`.
4.  `Це **найкращий** день у моєму житті!` (Adapted from Source 32) - Simple superlative.
5.  `А наша путь все **довша** і все **ширша**.` (Source 18) - Shows progression.
6.  `Сродна праця — це **найсолодша** в світі річ.` (Г. Сковорода, Source 18) - Classic literature example.
7.  `**Найвища** мудрість — розрізняти добро і зло.` (Сократ, Source 18) - Abstract concept.
8.  `Вона **розумніша за** свою сестру.` (Adapted from Source 6) - Direct comparison of two people.
9.  `Поезія — це завжди неповторність, якийсь **безсмертний** дотик до душі.` (Л. Костенко, Source 4) - Example of an adjective that cannot be compared.
10. `Що **важливіше** — бути сил

============================================================
📎 Attached Data:
{"to_model": "gemini-3.1-pro-preview"}

🤖 Processing with Gemini (gemini-3.1-pro-preview) [sync, 30 min timeout]...
  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=18313 chars: You are Gemini, participating in a collaboration with Claude. This is a message from Claude to you:  --- You are a HARSH adversarial reviewer of a grammar brief for the Ukrainian language curriculum w...
Dimension scores:
1. Factual: 9/10 — Mostly accurate, but contains a terminology slip in the Superlative table: `вищий ступінь + за всіх` is a syntactic/descriptive construction, not a morphological "Складена" (Compound) form. Also, the consonant alternation rule misses the `[ст]` cluster needed to explain the provided example `товстий → товщий`.
2. Language: 10/10 — Clean Ukrainian examples. Excellent natural phrasing. No Russianisms or surzhyk detected in the target language instructions. 
3. Decolonization: 10/10 — Outstanding explicit targeting of the `самий` trap, Russian genitive calques (`вищий берези`), and the Soviet-era bureaucratic preference for compound forms.
4. Completeness: 7/10 — The article is literally cut off mid-sentence at the very end.
5. Actionable: 4/10 — Missing concrete activity types, sequencing advice, or exercises for curriculum writers. It provides grammar rules but lacks the "how-to-build-a-module" pedagogical scaffolding.

**Overall: 8/10**

<fixes>
old: | **Складена** (Compound) | Проста форма вищого ступеня + **за всіх**, **від усіх**, **над усе**<br/>*Simple comparative + "than all", "of all", "above all"* | `сильніший за всіх`<br/>`миліша над усе`<br/>`кращий від усіх` |
new: | **Синтаксична** (Syntactic) | Проста форма вищого ступеня + **за всіх**, **від усіх**, **над усе**<br/>*Simple comparative + "than all", "of all", "above all"* | `сильніший за всіх`<br/>`миліша над усе`<br/>`кращий від усіх` |
---
old: *   **[с]** + `-ш-` → **[шч]** (written as **щ**)
    *   `ви**с**окий → ви**щ**ий`
    *   `тов**с**тий → тов**щ**ий`
new: *   **[с]**, **[ст]** + `-ш-` → **[шч]** (written as **щ**)
    *   `ви**с**окий → ви**щ**ий`
    *   `тов**ст**ий → тов**щ**ий`
---
old: 10. `Що **важливіше** — бути сил
new: 10. `Що **важливіше** — бути сильним чи бути добрим?` (What is more important — to be strong or to be kind?) - Philosophical comparison.

## Actionable Teaching Sequences & Activities

To effectively teach this to B1 students, curriculum writers should use the following sequence:

**Phase 1: The Simple Comparative (Проста форма вищого ступеня)**
*   **Focus:** Regular suffixes `-іш-` and `-ш-`.
*   **Activities:** 
    *   *Visual Comparisons:* Show two objects/cities/people and have students compare them (e.g., `Київ більший за Львів`, `Кава дорожча за чай`).
    *   *Transformation Drills:* Give a base adjective, ask for the comparative + `ніж` or `за`.

**Phase 2: Consonant Alternations & Exceptions**
*   **Focus:** `г, ж, з → жч`, `с, ст → щ`, and suppletive forms (`кращий`, `гірший`).
*   **Activities:**
    *   *Odd-One-Out:* Group adjectives by their alternation pattern.
    *   *Targeted Cloze:* Fill in the blanks with the tricky forms (e.g., `Цей шлях (близький) _______`).

**Phase 3: The Superlative & The "Самий" Trap**
*   **Focus:** Prefix `най-` and eliminating `самий`.
*   **Activities:**
    *   *Error Correction:* Present sentences with `самий` and have students rewrite them with `най-`.
    *   *Superlatives in Context:* "World Records" activity (e.g., `Дніпро — найдовша річка України`).

**Phase 4: Syntactic & Compound Forms (Passive/Receptive)**
*   **Focus:** `більш/менш`, `найбільш/найменш`, and `... за всіх`.
*   **Activities:**
    *   *Style Transformation:* Rewrite formal sentences (using `більш/найбільш`) into natural colloquial Ukrainian (using simple forms).
</fixes>


────────────────────────────────────────
✅ Gemini finished (3391 chars)
✅ Message sent to Claude (ID: 28286)
✓ Message 28286 acknowledged
   Auto-acknowledged reply #28286 (stdout delivery — no inbox accumulation)
   ℹ️  No issue number in task_id 'wiki-review-b1-adjective-comparison-r2' — skipping GH posting (review saved to orchestration/)
✓ Message 28285 acknowledged
