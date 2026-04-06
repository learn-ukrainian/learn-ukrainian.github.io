✅ Message sent to Gemini (ID: 28163) [auto-acked: self-addressed]

🚀 Invoking Gemini to process message #28163...
📨 Message #28163
   From: gemini → To: gemini
   Type: query
   Task: wiki-review-a1-at-the-cafe-final
   Time: 2026-04-05T22:11:07.032639+00:00

============================================================

You are a HARSH adversarial reviewer of a A1 pedagogical brief for the Ukrainian language curriculum wiki. Your job is to find problems, not praise.

Track: a1, Slug: at-the-cafe, Round: final

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

# Педагогіка A1: At The Cafe

<!-- wiki-meta
slug: at-the-cafe
domain: pedagogy/a1
tracks: [a1, a2]
sources: [6-klas-ukrmova-betsa-2023_s0109, 10-klas-ukrajinska-mova-zabolotnij-2018_s0122, 5-klas-ukrmova-avramenko-2022_s0005, 5-klas-ukrmova-avramenko-2022_s0194, 5-klas-ukrmova-litvinova-2022_s0228, 5-klas-ukrmova-uhor-2022-1_s0018, 8-klas-ukrmova-zabolotnyi-2025_s0224, 9-klas-ukrajinska-mova-zabolotnij-2017_s0088, 2-klas-ukrmova-kravcova-2019-2_s0054, 4-klas-ukrmova-zaharijchuk_s0008, 5-klas-ukrmova-avramenko-2022_s0028, 5-klas-ukrmova-avramenko-2022_s0057, ext-article-0, ext-article-1, ext-article-2, ext-article-3, ext-video-4, ext-video-5]
compiled: 2026-04-06
-->

## Методичний підхід (Methodological Approach)

The pedagogical approach for teaching the "At the Cafe" (`У кав'ярні`) scenario to A1 learners must be overwhelmingly communicative and situational. Ukrainian textbooks for native speakers, even at early grades, favor task-based, interactive learning that mimics real-life situations. The goal is not to have students memorize grammar tables, but to equip them with functional language chunks to successfully complete a task: ordering food and drinks.

**Core Principles:**

1.  **Dialogue-First:** The primary teaching tool is the dialogue. As seen in sources from Betsa (Source 1), Zabolotnyi (Source 14), and Litvinova (Source 8), interaction is key. Lessons should be structured around a core dialogue between a customer and a waiter (`офіціант`). This provides context, models natural turn-taking, and demonstrates intonation patterns.

2.  **Situational Role-Playing:** The most effective exercise, demonstrated in Grade 6 materials (Source 1: `Ситуація. Уявіть, що хтось із вас турист...`), is role-playing. Learners should be given simple roles (`клієнт`, `офіціант`) and a clear goal (order a coffee, ask for the bill). This moves language from passive knowledge to active skill.

3.  **Chunking over Conjugation:** At A1, learners should acquire phrases as unbreakable "chunks." `Можна, будь ласка...`, `Дайте, будь ласка...`, `Скільки це коштує?`. The internal grammar of these phrases (e.g., why `можна` is used) can be explored later. The immediate goal is communicative success. Textbooks for young learners are filled with these "etiquette formulas" (`ФРАЗИ ЕТИКЕТУ`, Source 9).

4.  **Politeness as a Framework:** The entire interaction is frame

## Instructions
1. Read the critique carefully.
2. Identify which SPECIFIC sections need rewriting to address the critique.
3. Output the COMPLETE article with those sections rewritten.
4. Do NOT remove or degrade sections that scored well.
5. Do NOT add commentary — output ONLY the article markdown.

## Current article

```markdown
# Педагогіка A1: At The Cafe

<!-- wiki-meta
slug: at-the-cafe
domain: pedagogy/a1
tracks: [a1, a2]
sources: [6-klas-ukrmova-betsa-2023_s0109, 10-klas-ukrajinska-mova-zabolotnij-2018_s0122, 5-klas-ukrmova-avramenko-2022_s0005, 5-klas-ukrmova-avramenko-2022_s0194, 5-klas-ukrmova-litvinova-2022_s0228, 5-klas-ukrmova-uhor-2022-1_s0018, 8-klas-ukrmova-zabolotnyi-2025_s0224, 9-klas-ukrajinska-mova-zabolotnij-2017_s0088, 2-klas-ukrmova-kravcova-2019-2_s0054, 4-klas-ukrmova-zaharijchuk_s0008, 5-klas-ukrmova-avramenko-2022_s0028, 5-klas-ukrmova-avramenko-2022_s0057, ext-article-0, ext-article-1, ext-article-2, ext-article-3, ext-video-4, ext-video-5]
compiled: 2026-04-06
-->

## Методичний підхід (Methodological Approach)

The pedagogical approach for teaching the "At the Cafe" (`У кав'ярні`) scenario to A1 learners must be overwhelmingly communicative and situational. Ukrainian textbooks for native speakers, even at early grades, favor task-based, interactive learning that mimics real-life situations. The goal is not to have students memorize grammar tables, but to equip them with functional language chunks to successfully complete a task: ordering food and drinks.

**Core Principles:**

1.  **Dialogue-First:** The primary teaching tool is the dialogue. As seen in sources from Betsa (Source 1), Zabolotnyi (Source 14), and Litvinova (Source 8), interaction is key. Lessons should be structured around a core dialogue between a customer and a waiter (`офіціант`). This provides context, models natural turn-taking, and demonstrates intonation patterns.

2.  **Situational Role-Playing:** The most effective exercise, demonstrated in Grade 6 materials (Source 1: `Ситуація. Уявіть, що хтось із вас турист...`), is role-playing. Learners should be given simple roles (`клієнт`, `офіціант`) and a clear goal (order a coffee, ask for the bill). This moves language from passive knowledge to active skill.

3.  **Chunking over Conjugation:** At A1, learners should acquire phrases as unbreakable "chunks." `Можна, будь ласка...`, `Дайте, будь ласка...`, `Скільки це коштує?`. The internal grammar of these phrases (e.g., why `можна` is used) can be explored later. The immediate goal is communicative success. Textbooks for young learners are filled with these "etiquette formulas" (`ФРАЗИ ЕТИКЕТУ`, Source 9).

4.  **Politeness as a Framework:** The entire interaction is framed by etiquette. Phrases like `Добрий день`, `Будь ласка`, `Дякую`, `Прошу`, and `До побачення` are non-negotiable bookends to the dialogue. Their correct and automatic use is a primary learning objective (Source 19, 34).

5.  **Aural-Oral Primacy:** Before students see the written words, they should hear them. Audio recordings of dialogues are essential to model correct pronunciation, stress (`наголос`), and intonation, which are critical for politeness and clarity. The distinction between `про́шу` and `прошу́` (Sources 1, 2) is purely auditory and must be taught with audio.

## Послідовність введення (Introduction Sequence)

A logical progression is crucial to avoid overwhelming the A1 learner. The sequence should build from simple phrases to a complete, albeit basic, transaction.

1.  **Level 0: Foundational Etiquette.**
    *   **Greeting:** `Добрий день` (Good day).
    *   **Core Politeness:** `Будь ласка` (Please) and `Дякую` (Thank you).
    *   **Leaving:** `До побачення` (Goodbye).
    *   These are presented as essential, indivisible units.

2.  **Level 1: The Basic Request.**
    *   **Vocabulary:** Introduce 3-5 core cafe nouns: `кава`, `чай`, `вода`, `сік`. Use flashcards or images.
    *   **The "Can I have?" construction:** Introduce `Можна...?` as the simplest way to ask for something. `Можна каву?` (Can I have a coffee?).
    *   **Combine with politeness:** `Можна каву, будь ласка?`. This is the single most important transactional phrase.

3.  **Level 2: The Waiter's Side & Basic Answers.**
    *   **Waiter's greeting and question:** `Добрий день. Що ви бажаєте?` (Good day. What would you like?) or simply `Що для вас?` (What for you?).
    *   **Responding:** `Каву, будь ласка.` (A coffee, please).
    *   **The "Here you go" response:** `Про́шу.` (Here you are). This is a critical point to introduce the difference between `будь ласка` (please) and `про́шу` (you're welcome/here you are). See Source 1.
    *   **Responding to thanks:** Customer says `Дякую`. Waiter responds `Про́шу`.

4.  **Level 3: Expanding the Menu & Asking Questions.**
    *   **More vocabulary:** `тістечко` (cake/pastry), `морозиво` (ice cream), `салат` (salad), `піца` (pizza), `меню`.
    *   **Asking "Do you have...?":** `У вас є...?` (`У вас є піца?`).
    *   **Asking for the menu:** `Можна меню, будь ласка?`.

5.  **Level 4: Paying for the Meal.**
    *   **Asking for the bill:** `Рахунок, будь ласка.` (The bill, please).
    *   **Asking "How much?":** `Скільки це коштує?` (How much does it cost?).
    *   **Numbers:** Introduce basic numbers needed for prices (e.g., 10, 20, 50, 100).
    *   **Payment Method:** Introduce `карткою` (by card) and `готівкою` (in cash). Waiter asks: `Карткою чи готівкою?`
    *   **Paying:** `Ось, будь ласка.` (Here you go).

This sequence creates a "scaffolded" dialogue that learners can practice and build upon in each step.

## Типові помилки L2 (Common L2 Errors)

Content must be designed to preemptively address common errors made by English speakers.

1.  **Over-translation of Politeness:** English speakers often translate elaborate politeness like "I was wondering if I could possibly have..." This is unnatural.
    *   **Prevention:** Emphasize that `Можна... будь ласка?` is the polite and standard form. Directness is not rudeness.

2.  **`Будь ласка` vs. `Прошу`:** This is a major point of confusion.
    *   **Prevention:** Create a clear table.
        | Situation | You Say |
        | :--- | :--- |
        | You want something (Please) | `Будь ласка` |
        | You give something (Here you are) | `Про́шу` |
        | Someone thanks you (You're welcome)| `Про́шу` |
    *   Use audio to drill the stress difference between `про́шу` (here you are) and `прошу́` (I ask), as highlighted in Sources 1 & 2.

3.  **Using `Дякуючи` for "Thanks to":** A common false cognate trap.
    *   **Prevention:** Explicitly teach that `завдяки` is used for positive outcomes ("Thanks to your help..."), while `дякуючи` is a verbal participle (Source 38). For A1, simply teach `завдяки` as the correct form in relevant contexts, if any.

4.  **Calques and Russianisms (Суржик):** Learners exposed to other Slavic languages may import incorrect words.
    *   **Prevention:** Use a `ПРАВИЛЬНО / НЕПРАВИЛЬНО` table (style from Source 12).
        | НЕПРАВИЛЬНО (Суржик/Помилка) | ПРАВИЛЬНО (Українською) |
        | :--- | :--- |
        | Я рахую, що... | Я **вважаю**, що... (Source 37) |
        | На рахунок цього | **Щодо** цього (Source 37) |
        | Слідуючий | **Наступний** (Source 12) |
        | Приймати участь | **Брати участь** (Source 12) |
        | Відкривати двері | **Відчиняти** двері (Source 12) |
        | Кава **вкусна** | Кава **смачна** |
        | **Счёт**, будь ласка | **Рахунок**, будь ласка |

## Деколонізаційні застереження (Decolonization Notes)

Teaching Ukrainian must be done on its own terms, completely independent of Russian. This is a non-negotiable pedagogical principle.

1.  **No Russian Analogies:** Never teach a Ukrainian sound, letter, or word by comparing it to Russian (e.g., "Ukrainian И is like Russian Ы"). This creates a false dependency and reinforces a colonial linguistic hierarchy. Ukrainian phonetics must be taught from a neutral (English) baseline.

2.  **Embrace Distinctly Ukrainian Etiquette:** Highlight the use of `Пане/Пані/Панно` (Sir/Madam/Miss) as traditional and correct forms of address to strangers, as shown in Source 27. While a simple `Перепрошую` (Excuse me) is more common for getting a waiter's attention, explaining this tradition grounds the learner in Ukrainian culture, not a generic "Slavic" one.

3.  **Verify All Vocabulary:** The writer must ensure every vocabulary item is standard, modern Ukrainian and not a Soviet-era calque from Russian. Avoid words that are now considered Russianisms, even if they appear in older texts. The cafe context is rife with potential pitfalls (e.g., `морожене` vs. `морозиво` - `морозиво` is standard; `кофе` is Russian, `кава` is Ukrainian).

4.  **Pronunciation Purity:** Stress the correct, hard pronunciation of `Ч` and `Ш` (Source 2) and the clear, un-devoiced pronunciation of final consonants (e.g., `хліб`, not `хліп`). These are key phonetic differentiators from Russian and core to the sound of Ukrainian.

## Словниковий мінімум (Vocabulary Boundaries)

The vocabulary should be tightly controlled to ensure it is learnable and functional for the specific task.

*   **Places:** `кав'ярня` (cafe), `ресторан` (restaurant).
*   **People:** `офіціант` (waiter), `клієнт` (customer).
*   **Core Items:** `меню` (menu), `рахунок` (bill), `картка` (card), `готівка` (cash).
*   **Drinks:** `кава` (coffee), `чай` (tea), `сік` (juice), `вода` (water).
*   **Food:** `піца` (pizza), `салат` (salad), `тістечко` (cake/pastry), `морозиво` (ice cream), `цукор` (sugar).
*   **Essential Verbs (in context):** `хочу` (I want), `бажаю` (I wish/desire - used in questions), `є` (is/are - in `У вас є...?`), `коштує` (it costs).
*   **Etiquette & Functional Phrases:** `Добрий день`, `Будь ласка`, `Дякую`, `Про́шу`, `До побачення`, `Перепрошую` (Excuse me, to get attention), `Вибачте` (Excuse me/Sorry, for a mistake), `Можна...?`, `У вас є...?`, `Скільки...?`.

Avoid teaching the grammar of declensions. Teach the accusative forms of food and drink (e.g., `каву`, `воду`, `піцу`) as fixed vocabulary chunks attached to verbs like `хочу` or `можна`. Do not explain the accusative case paradigm at this stage. The goal is a successful communicative act, not grammatical mastery.

## Приклади з підручників (Textbook Examples)

The module writer should model activities directly on those found in Ukrainian source materials.

**Example 1: The Core Dialogue (adapted from various sources)**

This simple dialogue should be the spine of the lesson.

> **Офіціант:** Добрий день! Що ви бажаєте?
> **Клієнт:** Добрий день. Можна меню, будь ласка?
> **Офіціант:** Так, звичайно. Про́шу.
> *(пауза)*
> **Клієнт:** Я хочу каву і тістечко.
> **Офіціант:** Добре.
> *(пауза)*
> **Офіціант:** Про́шу, ваша кава і тістечко.
> **Клієнт:** Дякую.
> *(пауза)*
> **Клієнт:** Перепрошую, можна рахунок, будь ласка?
> **Офіціант:** Так. 120 гривень. Карткою чи готівкою?
> **Клієнт:** Карткою. Ось, будь ласка.
> **Офіціант:** Дякую. Про́шу. До побачення.
> **Клієнт:** До побачення.

**Example 2: Role-Play Situation Card (style of Source 1)**

> **Ситуація: "У кав'ярні"**
>
> **Партнер А (Клієнт):**
> 1. Привітайтеся з офіціантом.
> 2. Замовте один напій (`кава` або `чай`) і одну страву (`піца` або `салат`).
> 3. Подякуйте.
> 4. Попросіть рахунок.
> 5. Попрощайтеся.
>
> **Партнер Б (Офіціант):**
> 1. Привітайтеся з клієнтом.
> 2. Запитайте, що він бажає.
> 3. Прийміть замовлення.
> 4. Принесіть уявне замовлення (скажіть `Про́шу`).
> 5. Дайте рахунок.
> 6. Попрощайтеся.

**Example 3: Phonetic/Culture Note (style of Sources 1, 2, 3)**

> **Культура мовлення: Про́шу чи Прошу́?**
>
> Слово `прошу` змінює своє значення залежно від наголосу!
>
> *   `Про́шу` (наголос на **О**) = "Here you are" or "You're welcome". Це відповідь.
>     > — Дякую!
>     > — **Про́шу**!
> *   `Прошу́` (наголос на **У**) = "I ask" or "I beg". Це прохання.
>     > Я **прошу́** вас допомогти. (I ask you to help).
>
> У ресторані ви будете чути і казати **про́шу**.

## Пов'язані статті (Related Articles)
- [[pedagogy/a1/politeness-and-greetings]]
- [[pedagogy/a1/asking-questions]]
- [[grammar/a1/nominative-case]]
- [[vocabulary/a1/food-and-drink]]
- [[culture/decolonization/surzhyk-and-russianisms]]
```


============================================================
📎 Attached Data:
{"to_model": "gemini-3.1-pro-preview"}

🤖 Processing with Gemini (gemini-3.1-pro-preview) [sync, 30 min timeout]...
  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=18391 chars: You are Gemini, participating in a colla

============================================================
📎 Attached Data:
{"to_model": "gemini-3.1-pro-preview"}

🤖 Processing with Gemini (gemini-3.1-pro-preview) [sync, 30 min timeout]...
  [gemini] attempt 1/5, model=gemini-3.1-pro-preview, prompt=18315 chars: You are Gemini, participating in a collaboration with Claude. This is a message from Claude to you:  --- You are a HARSH adversarial reviewer of a A1 pedagogical brief for the Ukrainian language curri...
Dimension scores:
1. Factual: 9/10 — [The brief accurately cites textbooks (e.g., distinguishing `про́шу` and `прошу́` using Sources 1 and 2) and correctly identifies etiquette frameworks.]
2. Language: 9/10 — [The core Ukrainian phrases provided are natural and standard. There are no Russianisms in the instructional text itself.]
3. Decolonization: 9/10 — [Strong framing. Explicitly forbids Russian phonetic comparisons and correctly highlights `морозиво` vs `морожене` and `кава` vs `кофе`.]
4. Completeness: 6/10 — [The brief misses absolutely critical modern cafe vocabulary for A1 learners, specifically the concept of "here or to go" (`тут чи із собою`), and sizing. Furthermore, the Surzhyk table is filled with generic errors completely irrelevant to a cafe scenario.]
5. Actionable: 7/10 — [The role-play cards and sequence are highly actionable. However, a module writer cannot effectively use the 'Типові помилки' section because it provides generic advice (`брати участь`, `відчиняти двері`) instead of the specific cafe-related calques they need to watch out for when writing the module.]

**Overall: 8/10**

<fixes>
old: 4.  **Level 3: Expanding the Menu & Asking Questions.**
    *   **More vocabulary:** `тістечко` (cake/pastry), `морозиво` (ice cream), `салат` (salad), `піца` (pizza), `меню`.
    *   **Asking "Do you have...?":** `У вас є...?` (`У вас є піца?`).
    *   **Asking for the menu:** `Можна меню, будь ласка?`.
new: 4.  **Level 3: Expanding the Menu & Asking Questions.**
    *   **More vocabulary:** `тістечко` (cake/pastry), `морозиво` (ice cream), `салат` (salad), `піца` (pizza), `меню`.
    *   **Asking "Do you have...?":** `У вас є...?` (`У вас є піца?`).
    *   **Asking for the menu:** `Можна меню, будь ласка?`.
    *   **Here or to go?:** Waiter asks `Вам тут чи із собою?`. Customer replies `Тут, будь ласка` or `Із собою, будь ласка`.
---
old:         | НЕПРАВИЛЬНО (Суржик/Помилка) | ПРАВИЛЬНО (Українською) |
        | :--- | :--- |
        | Я рахую, що... | Я **вважаю**, що... (Source 37) |
        | На рахунок цього | **Щодо** цього (Source 37) |
        | Слідуючий | **Наступний** (Source 12) |
        | Приймати участь | **Брати участь** (Source 12) |
        | Відкривати двері | **Відчиняти** двері (Source 12) |
        | Кава **вкусна** | Кава **смачна** |
        | **Счёт**, будь ласка | **Рахунок**, будь ласка |
new:         | НЕПРАВИЛЬНО (Суржик/Помилка) | ПРАВИЛЬНО (Українською) |
        | :--- | :--- |
        | Кава **вкусна** | Кава **смачна** |
        | **Счёт**, будь ласка | **Рахунок**, будь ласка |
        | Кава **на винос** | Кава **із собою** |
        | Дайте **кулечок** | Дайте **пакетик** (або торбинку) |
        | Пити через **трубочку** | Пити через **соломинку** |
        | **Чашка кофе** | **Філіжанка/горнятко/чашка кави** |
        | **Пірожене** | **Тістечко** |
---
INSERT AFTER: *   **Essential Verbs (in context):** `хочу` (I want), `бажаю` (I wish/desire - used in questions), `є` (is/are - in `У вас є...?`), `коштує` (it costs).
NEW TEXT: *   **Modern Cafe Essentials:** `із собою` (to go / takeaway), `тут` (here / have in), `великий/маленький` (big/small - simplified for A1 as chunks: `велику каву`, `маленьку каву`).
</fixes>


────────────────────────────────────────
✅ Gemini finished (3233 chars)
✅ Message sent to Claude (ID: 28164)
✓ Message 28164 acknowledged
   Auto-acknowledged reply #28164 (stdout delivery — no inbox accumulation)
   ℹ️  No issue number in task_id 'wiki-review-a1-at-the-cafe-final' — skipping GH posting (review saved to orchestration/)
✓ Message 28163 acknowledged
