

---

## Your Writing Identity

**You are: Lead Ukrainian Instructor.** Your persona is *The Patient Guide*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **23: Days and Months** (A1, A1.4 [Time and Nature]).

**Target: 1200–1800 words** of prose (Ukrainian examples count toward word total, headings and exercise placeholders do not).

---

## Step 1: Pacing Plan (output this FIRST)

Before writing any content, output a `<pacing_plan>` block. Evaluate each section from the plan and commit to a word budget. This prevents frontloading early sections and rushing later ones.

```
<pacing_plan>
Section 1 "Title": ~XXX words — [1-sentence content focus]
Section 2 "Title": ~XXX words — [1-sentence content focus]
...
Summary: ~150 words
Total: 1200+ words
</pacing_plan>
```

Then begin writing the module content. Follow your own pacing plan — each section must hit its word budget (±10%).

---

## 9 Hard Rules

1. **IMMERSION TARGET: 15-25% Ukrainian** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if immersion is outside this range. For A1 early modules, the learner cannot read Cyrillic — English must dominate. For A2+, Ukrainian must carry a significant share — add Ukrainian Reading Practice blocks, dialogues, and example paragraphs to reach the target. Too little Ukrainian fails audit just as much as too much.
2. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
3. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
4. **You are a warm, encouraging teacher.** Natural teacher phrasing ("Let us look at...", "Have you noticed...") is fine. What to AVOID: self-congratulatory openers ("Welcome to A2! Congratulations!"), gamified language ("You have unlocked...", "You now possess..."), and empty filler sentences that add words but zero information. Every sentence should teach something specific to Ukrainian.
5. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
6. **Place exercise markers only** — do NOT write exercises directly. Place `<!-- INJECT_ACTIVITY: {id} -->` markers where exercises should appear. A separate pipeline step generates the actual exercises from the plan's activity_hints.
7. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
8. **Hit the word target** — you MUST write 1200–1800 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
9. **NO archaic, obsolete, or rare words** — use only modern standard Ukrainian. Do not use words marked as archaic (застаріле) or dialectal in dictionaries. Example: use «кін» not «кон», use «пом'якшені» not «м'якшені». When in doubt, choose the common modern form. Your pre-training contains Russian-influenced archaic forms — verify unfamiliar words.
10. **EVERY module MUST end with `## Підсумок`** — this is the last H2 section before the file ends. It contains a self-check recap. If you forget this section, the audit REJECTS the module and you waste a retry. Write it LAST, after all other sections.

**Note:** Do NOT add stress marks (´) to any Ukrainian word — a deterministic tool handles this after you write.

## Exercise Placement — Markers Only

**Do NOT write exercises directly.** A separate pipeline step (ACTIVITIES) generates all exercises from the plan's `activity_hints`. Your job is to place markers showing WHERE exercises belong.

### How It Works

1. Read the plan's `activity_hints` — each entry has an `id`, `type`, and `focus`
2. After the relevant teaching section, place an injection marker
3. The ACTIVITIES step reads your prose + the plan hints and generates complete exercises

### Marker Format

Place markers after key teaching sections. Each marker corresponds to ONE `activity_hints` entry from the plan:

```
<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->
```

Rules:
- Use the EXACT `id` from the plan's `activity_hints` — do not invent new IDs
- Place the marker right after the prose that teaches the concept the exercise tests
- Spread markers evenly throughout the module — never cluster them
- If the plan has 4 activity hints, you should place 4 markers in your prose

### Example

If the plan says:
```yaml
activity_hints:
  - id: quiz-sounds-vs-letters
    type: quiz
    focus: "Distinguish звук from літера"
  - id: match-false-friends
    type: match-up
    focus: "Match false friend Cyrillic letters to real sounds"
```

Your prose should contain (after the relevant sections):
```
[...prose about sounds and letters...]

<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->

[...prose about false friend letters...]

<!-- INJECT_ACTIVITY: match-false-friends -->
```

### What NOT to Do

- Do NOT write `:::quiz`, `:::fill-in`, `:::match-up`, or any DSL exercise blocks
- Do NOT write exercise questions, answers, or options — the ACTIVITIES step handles all of this
- Do NOT invent marker IDs — use only IDs from the plan's `activity_hints`

---

## Plan

<plan_content>
module: a1-023
level: A1
sequence: 23
slug: days-and-months
version: '1.2'
title: Days and Months
subtitle: У понеділок, у січні — the calendar in Ukrainian
focus: vocabulary
pedagogy: PPP
phase: A1.4 [Time and Nature]
word_target: 1200
objectives:
- Name all 7 days of the week and use "on" (у/в + day as chunk)
- Name all 12 months and 4 seasons
- Say dates using ordinal numbers (as chunks)
- Plan a week using days, times, and activities
dialogue_situations:
- setting: At a doctor's reception — booking an appointment
  speakers:
  - Пацієнт
  - Реєстратор
  motivation: 'Days and months: У понеділок? Ні, у середу. В якому місяці?'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Planning the week (ULP Ep15 pattern): — Що ти робиш у понеділок?
    — Я працюю. А у вівторок? — У вівторок я вивчаю українську. — А у суботу? — У
    суботу гуляю. Неділя — вільний день! Days of the week in practical scheduling.'
  - Dialogue 2 — When is your birthday? — Коли у тебе день народження? — У березні.
    — Якого числа? — П'ятнадцятого березня. А у тебе? — У мене в серпні. — О, це літо!
    Months and seasons in personal context.
- section: Дні тижня (Days of the Week)
  words: 300
  points:
  - 'Seven days — all LOWERCASE in Ukrainian (not capitalized like English): понеділок
    (Monday), вівторок (Tuesday), середа (Wednesday), четвер (Thursday), п''ятниця
    (Friday), субота (Saturday), неділя (Sunday). Вашуленко Grade 2 p.83: planning
    your week activity. Note: неділя = Sunday AND ''week'' in some dialects. Standard
    ''week'' = тиждень.'
  - '''On'' a day = у/в + accusative (chunk — no grammar analysis): у понеділок, у
    вівторок, у середу, у четвер, у п''ятницю, в суботу, в неділю. Note the endings
    change — just memorize each form.'
- section: Місяці і пори року (Months and Seasons)
  words: 300
  points:
  - '12 months — also lowercase, organized by season: Зима: грудень (Dec), січень
    (Jan), лютий (Feb). Весна: березень (Mar), квітень (Apr), травень (May). Літо:
    червень (Jun), липень (Jul), серпень (Aug). Осінь: вересень (Sep), жовтень (Oct),
    листопад (Nov). All months are masculine. Many come from nature words (березень
    ← береза, липень ← липа, листопад ← листя падає).'
  - '4 seasons: зима (winter, f), весна (spring, f), літо (summer, n), осінь (autumn,
    f). ''In'' a month/season = у/в + locative (chunk): у січні, у лютому, в березні...
    влітку, взимку, восени, навесні. Seasonal forms are irregular — memorize as chunks.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Calendar vocabulary: Days: понеділок → неділя (у понеділок, в суботу). Months:
    січень → грудень (у січні, в серпні). Seasons: зима, весна, літо, осінь (взимку,
    навесні, влітку, восени). Self-check: What day is today? What month? What season?
    When is your birthday? Plan your next week in Ukrainian.'
vocabulary_hints:
  required:
  - понеділок, вівторок, середа (Mon, Tue, Wed)
  - четвер, п'ятниця (Thu, Fri)
  - субота, неділя (Sat, Sun)
  - тиждень (week, m)
  - зима, весна, літо, осінь (winter, spring, summer, autumn)
  recommended:
  - січень, лютий, березень (Jan, Feb, Mar)
  - квітень, травень, червень (Apr, May, Jun)
  - липень, серпень, вересень (Jul, Aug, Sep)
  - жовтень, листопад, грудень (Oct, Nov, Dec)
  - день народження (birthday)
activity_hints:
- type: fill-in
  focus: Put days of the week in order
  items:
  - понеділок, {вівторок|субота|четвер}, середа
  - середа, {четвер|п'ятниця|неділя}, п'ятниця
  - п'ятниця, {субота|вівторок|середа}, неділя
  - неділя, {понеділок|вівторок|четвер}, вівторок
  - вівторок, середа, {четвер|п'ятниця|неділя}
  - четвер, п'ятниця, {субота|понеділок|вівторок}
  - субота, {неділя|понеділок|п'ятниця}, понеділок
- type: match-up
  focus: Match the month to the correct season
  pairs:
  - січень ↔ зима
  - квітень ↔ весна
  - липень ↔ літо
  - жовтень ↔ осінь
  - лютий ↔ зима
  - травень ↔ весна
  - серпень ↔ літо
  - листопад ↔ осінь
- type: fill-in
  focus: Use the correct 'in/on' chunk for days and months
  items:
  - Я працюю {у понеділок|понеділок|в понеділок}.
  - Мій день народження {у березні|березень|в березень}.
  - Ми гуляємо {в суботу|субота|у субота}.
  - '{Взимку|Зима|У зима} холодно.'
  - Я вивчаю українську {у вівторок|вівторок|в вівторок}.
  - Вони відпочивають {у серпні|серпень|в серпень}.
connects_to:
- a1-024 (Weather)
prerequisites:
- a1-022 (What Time?)
grammar:
- 'Days of the week: у/в + accusative chunk (у понеділок, в суботу)'
- 'Months: у/в + locative chunk (у січні)'
- 'Seasons: adverbial forms (взимку, навесні, влітку, восени)'
register: розмовний
references:
- title: Вашуленко Grade 2, p.83
  notes: Planning your week — days of the week activity.
- title: Вашуленко Grade 2, p.69-89
  notes: Months through seasonal stories and poems.
- title: ULP Season 1, Episode 15
  url: https://www.ukrainianlessons.com/episode15/
  notes: Days of the week and planning.

</plan_content>

---

## Pre-Verified Facts (from MCP tools — use these, do NOT guess)

A verification step already called VESUM, textbooks, Правопис, and style guide tools. The results below are GROUND TRUTH. Use them:
- If a word is marked ❌ NOT IN VESUM — do NOT use it
- If a textbook excerpt is provided — use that pedagogy
- If a calque is flagged — use the correct alternative
- If CEFR says a word is above target — find a simpler synonym

You do NOT need to call tools yourself — the facts are already verified.

<pre_verified_facts>
## VESUM Verification
- Confirmed: понеділок, вівторок, середа, четвер, п'ятниця, субота, неділя, тиждень, зима, весна, літо, осінь, січень, лютий, березень, квітень, травень, червень, липень, серпень, вересень, жовтень, листопад, грудень, день, народження, взимку, навесні, влітку, восени.
- Not found: None.

## Grammar Rules
- Lowercase calendar terms: Правопис § 54 (by exclusion) and СУМ-11 confirm that names of days (понеділок) and months (січень) are common nouns and are written with a lowercase letter.
- Prepositions for time: 
  - Days (Accusative): "у понеділок", "у середу", "у п'ятницю".
  - Months (Locative): "у січні", "у травні", "у червні".
  - Seasons (Adverbs): "взимку", "навесні", "влітку", "восени".

## Calque Warnings
- день народження: OK — Standard Ukrainian phrase for "birthday".
- у понеділок: OK — Standard usage of preposition "у" with Accusative for days of the week.
- у вихідні: OK — Natural way to say "on the weekend" (confirmed via GRAC).

## CEFR Check
- понеділок: A1 — OK
- січень: A1 — OK
- зима: A1 — OK
- тиждень: A1 — OK
- травень: A1 — OK
</pre_verified_facts>


## Wiki Teaching Brief — Your Authoritative Source

**This is your primary teaching material.** The wiki article below was compiled from real Ukrainian school textbooks, literary sources, and verified references. It contains the correct terminology, paradigm tables, teaching sequences, and examples for this module. Your job is to TRANSFORM this into engaging, level-appropriate content — not to copy it verbatim.

**How to use the wiki article:**
1. **Adopt the Ukrainian terminology.** If the article says «складоподіл», you write «складоподіл» — never CVCCV or "syllable division rules" paraphrased from English phonology. If it says «відкритий склад», you write «відкритий склад» — never "open syllable type."
2. **Follow the teaching sequence.** If the article shows: sound model → syllable → word → sentence, follow that progression. Do not rearrange or substitute your own.
3. **Use the article's examples as your foundation.** Authentic examples from textbooks beat invented ones. Use the article's examples and expand with your own that follow the same patterns.
4. **Synthesize and teach, don't summarize.** You are a teacher, not a summarizer. Take the facts from the article and weave them into engaging explanations with dialogues, situations, and practice. The article tells you WHAT to teach — you decide HOW to teach it for the target level.
5. **Your pre-training is contaminated by Russian and English linguistics.** When the article contradicts your instinct, the article wins. Ukrainian has its own phonetic categories (голосний/приголосний, дзвінкий/глухий, м'який/твердий) that do not map 1:1 to English or Russian. Use the Ukrainian categories.
6. **Do NOT copy paragraphs verbatim.** The article is reference material. Your output must be original teaching prose at the correct CEFR level, not a rephrased version of the article.

<knowledge_packet>
# Knowledge Packet: Days and Months
**Module:** days-and-months | **Track:** A1

<wiki_context>
## Compiled Wiki Knowledge

The following articles from the project wiki provide compiled knowledge relevant to this module. Use them as authoritative context — they were compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).

### Вікі: pedagogy/a1/days-and-months.md

# Педагогіка A1: Days And Months



## Методичний підхід (Methodological Approach)

The native Ukrainian pedagogical approach to teaching days and months is highly contextual and practical, even from Grade 1. It avoids rote memorization in isolation, instead embedding the vocabulary into immediate, usable structures.

1.  **Context First, Vocabulary Second:** Teachers introduce days of the week through the concept of a weekly schedule (`розклад`). The primary structure is "What do you do *on* Monday?" (`Що ти робиш у понеділок?`). This immediately forces the use of the preposition `у/в` and the required case change, making the grammar intuitive. Большакова (Source 5) presents this as a fill-in-the-blank exercise: `Зразок. У понеділок я … .`. This pattern is reinforced in multiple sources (Source 27, 28).

2.  **Grouping for Memory:** Months are not taught as a list of twelve, but are thematically grouped by seasons (`пори року`). Textbooks consistently ask learners to name the spring months (`весняні місяці`), autumn months (`осінні місяці`), etc. (Source 2, 6, 31, 42). This chunking aids memorization and connects the vocabulary to the natural world.

3.  **Etymological Anchoring:** A core feature of Ukrainian pedagogy is explaining the folk etymology of the month names. This is not treated as a dry linguistic exercise but as a storytelling tool that makes the words memorable and culturally rich. For example, `вересень` is linked to the blooming of heather (`верес`), `листопад` to falling leaves (`листя падає`), and `січень` to cutting wood (`сікти`) (Source 8, 19, 20, 41). This narrative approach transforms abstract names into vivid images, which is highly effective for retention.

4.  **From Nominative to Prepositional Case Immediately:** Ukrainian pedagogy does not dwell on the nominative forms. Textbooks and lesson materials immediately pivot to the practical forms `у понеділок` (Accusative) and `у січні` (Locative). The structure is often presented in a simple two-column table: `Що?` (понеділок) -> `Коли?` (у понеділок) (Source 1). This pattern-based learning helps students acquire the case endings as part of the vocabulary chunk itself, rather than as a separate grammar rule.

5.  **Focus on Soft Consonants:** Pronunciation, especially of the soft sign `ь` at the end of many month names (`січень`, `березень`), is a key focus. The ULP podcast explicitly drills this, contrasting hard and soft sounds and providing triggers for softness (the vowels `я, є, і` and the soft sign `ь`) (Source 41).

## Послідовність введення (Introduction Sequence)

The introduction should be staged to build from simple recognition to active use in sentences.

1.  **Step 1: Introduce Days of the Week (Nominative).**
    Present the seven days as a list, starting with `понеділок`. Emphasize that the Ukrainian week begins on Monday (Source 41).
    - `понеділок, вівторок, середа, четвер, п'ятниця, субота, неділя`
    - Also introduce the concept of "weekdays" (`робочі дні`) and "weekend" (`вихідні`) (Source 41).

2.  **Step 2: Introduce "On [Day]" (Accusative Case).**
    Immediately teach the construction `у/в + [день тижня]`. This is the most common use case.
    - Masculine nouns do not change: `у понеділок`, `у вівторок`, `у четвер`.
    - **Crucially, highlight the feminine nouns that change:** `середа` → `у середу`, `п'ятниця` → `у п'ятницю`.
    - Neuter nouns also don't change: `неділя` (fem.) → `у неділю` (Source 1, 44). This is the highest-frequency grammatical transformation and must be mastered early.

3.  **Step 3: Introduce Months Grouped by Season (Nominative).**
    Present the twelve months, but organized into the four seasons (`зима, весна, літо, осінь`).
    - **Зима:** `грудень, січень, лютий`
    - **Весна:** `березень, квітень, травень`
    - **Літо:** `червень, липень, серпень`
    - **Осінь:** `вересень, жовтень, листопад`
    This structure is a standard pedagogical tool in Ukrainian schools (Source 2, 42). Briefly mention the etymological meaning to aid memory (e.g., `квітень` from `квітка` - flower) (Source 3, 8).

4.  **Step 4: Introduce "In [Month]" (Locative Case).**
    Teach the construction `у/в + [місяць]`. This requires the Locative case.
    - The core pattern is adding the ending `-і`: `у січні`, `у березні`, `у квітні`.
    - Point out that the fleeting vowel `е` often drops: `березень` → `у березні` (Source 45).
    - Special forms must be highlighted: `лютий` → `у лютому`, `травень` → `у травні`. (Source 45).

5.  **Step 5: Introduce Basic Dates (Ordinal Number + Genitive Month).**
    For A1, this should be limited to recognition and simple production of birthdays or holidays. The core pattern is: `[number, neuter]` + `[month, genitive]`.
    - Example: `Перше вересня` (The first of September).
    - To say "on the first of September", the structure is `Першого вересня`.
    - The key rule is that months in dates *always* use the Genitive case (Source 26). Example: `п'ятого березня`, `двадцять четвертого грудня` (Source 1, 26).

## Типові помилки L2 (Common L2 Errors)

| ❌ Помилково (Incorrectly) | ✅ Правильно (Correctly) | Чому (Why) |
| :--- | :--- | :--- |
| "The week starts on Sunday." | `Тиждень починається в понеділок.` | English speakers assume a universal Sunday start. Ukrainian and many European calendars start the work week on Monday (`понеділок`) (Source 41, 43). |
| `Я їду в Україну в неділя.` | `Я їду в Україну в неділю.` | Learners forget the Accusative case ending for feminine days of the week when using the preposition `в/у` to mean "on" a day (Source 44). |
| `Російською, неділя це "week".` | `Неділя` це "Sunday". `Тиждень` це "week". | This is a critical false cognate. Russian `неделя` means "week," while Ukrainian `неділя` means "Sunday." This confusion must be addressed directly and early (Source 41). |
| `Мій день народження в березень.` | `Мій день народження в березні.` | Learners often forget to apply the Locative case (`-і` ending) to months when using `в/у` to mean "in" a month. They use the base nominative form instead (Source 45). |
| `Дата сьогодні — п'яте березень.` | `Дата сьогодні — п'яте березня.` | When stating a date, the month must be in the Genitive case (`-я` or `-а` ending for masculine nouns), not the Nominative. This is a fixed rule (Source 26). |
| `лютий` (pronounced with a hard 'т') | `лютий` (pronounced with a soft 'т') | English speakers lack the hard/soft consonant distinction. The `и` vowel softens the preceding consonant. This requires explicit pronunciation practice (Source 41). |

## Деколонізаційні застереження (Decolonization Notes)

This topic is a powerful tool for decolonization and establishing Ukrainian as a language distinct from Russian from the very first lessons.

1.  **Native Slavic Month Names vs. Latin Borrowings:** This is the most important distinction. **Emphasize that Ukrainian retains its original, nature-based Slavic month names** (`січень, квітень, листопад`). In contrast, Russian uses Latin-derived names (`январь, апрель, ноябрь`), similar to English. This is a clear and immediate demonstration of Ukrainian's distinct linguistic heritage (Source 41, 19). The writer should present this not as an oddity, but as a point of cultural pride and authenticity.

2.  **`Неділя` vs. `Воскресенье`:** The Ukrainian word for Sunday, `неділя`, comes from `не ділати` — "not to do/work," reflecting a day of rest (Source 43). The Russian word, `воскресенье`, means "Resurrection" and is a purely religious term imposed later. Teaching the origin of `неділя` reinforces the native, pre-Christian roots of the vocabulary.

3.  **Avoid Russian as a Phonetic Bridge:** **Never** teach Ukrainian sounds by comparing them to Russian (e.g., "Ukrainian `и` is like Russian `ы`"). This creates phonetic interference and reinforces a colonial mindset. Ukrainian phonology must be taught on its own terms, using minimal pairs within Ukrainian itself and referencing the International Phonetic Alphabet (IPA) or audio guides designed for English speakers learning Ukrainian. The goal is to build a new, separate phonetic system in the learner's mind (Source 41).

4.  **Grammatical Independence:** Grammatical structures like the use of Accusative for days vs. Locative for months should be presented as internal rules of Ukrainian, without reference to how Russian does it. This avoids positioning Ukrainian as a "dialect" or "variant" and reinforces its status as a complete and independent language.

## Словниковий мінімум (Vocabulary Boundaries)

**Іменники (Nouns):**
*   ★★★ `понеділок, вівторок, середа, четвер, п'ятниця, субота, неділя`
*   ★★★ `січень, лютий, березень, квітень, травень, червень, липень, серпень, вересень, жовтень, листопад, грудень`
*   ★★★ `тиждень`, `місяць`, `рік`
*   ★★★ `зима, весна, літо, осінь`
*   ★★ `вихідні` (weekend), `день`, `ранок`, `вечір`

**Прислівники (Adverbs):**
*   ★★★ `сьогодні`, `завтра`, `вчора`
*   ★★ `вранці`, `вдень`, `ввечері`, `вночі`
*   ★★ `коли?`
*   ★ `щодня`, `щотижня`, `щороку` (Source 1)

**Прикметники (Adjectives):**
*   ★★★ `перший`, `останній`
*   ★★ `улюблений` (favorite)
*   ★★ `минулий` (last), `наступний` (next) (Source 46)

**Дієслова (Verbs):**
*   ★★★ `бути`, `робити`, `починатися`
*   ★★ `мати`, `любити`, `подобатися`

## Приклади з підручників (Textbook Examples)

1.  **Activity: My Weekly Schedule (Fill-in-the-blank)**
    This exercise from a Grade 2 textbook immediately puts the vocabulary into a practical, personal context.
    *   **Prompt:** `Запиши, які справи ти робиш кожного дня тижня.` (Write what things you do each day of the week.)
    *   **Format:**
        `Зразок. У понеділок я … .`
        `У вівторок я … .`
        `У середу я … .`
    (Source: 2-klas-ukrmova-bolshakova-2019-2_s0070)

2.  **Activity: Answering Factual Questions (Q&A)**
    This exercise from a Grade 4 textbook checks comprehension and active use of both cardinal and ordinal numbers with time-related vocabulary.
    *   **Prompt:** `Запиши повні відповіді на запитання.` (Write full answers to the questions.)
    *   **Format:**
        `1. Скільки днів має тиждень?`
        `2. Котрим за порядком днем тижня є понеділок? вівторок?`
        `4. Скільки місяців триває рік?`
    (Source: 4-klas-ukrayinska-mova-varzatska-2021-1_s0095)

3.  **Activity: Case Transformation Table (What? -> When?)**
    A simple but powerful exercise from a Grade 5 textbook for learners with Hungarian as L1, drilling the transformation from nominative to the correct prepositional case.
    *   **Prompt:** The table implicitly asks the learner to fill in the form for "when."
    *   **Format:**
| Що? | Коли? |
|---|---|
| понеділок | у понеділок |
| середа | у середу |
| січень | у січні |
| квітень | у квітні |
    (Source: 5-klas-ukrmova-uhor-2022-1_s0019)

4.  **Activity: Sentence Building with Activities (Sentence Scramble)**
    This Grade 6 exercise combines days of the week with places and activities, forcing the learner to construct a logical sentence.
    *   **Prompt:** `Утворіть речення. Підкресліть обставину.` (Form sentences. Underline the adverbial modifier.)
    *   **Format:**
        `Зразок: Чілла запланувала в суботу відвідати музей просто неба.`
        `Давид — субота — стадіон` -> `Давид у суботу був на стадіоні.`
        `Наталка — понеділок — екскурсія` -> `Наталка в понеділок була на екскурсії.`
    (Source: 6-klas-ukrmova-betsa-2023_s0046)

## Пов'язані статті (Related Articles)

- `pedagogy/a1/introduction-to-cases`
- `pedagogy/a1/numbers-cardinal-and-ordinal`
- `pedagogy/a1/seasons-and-weather`
- `culture/ukrainian-folk-etymology`

---

### Вікі: pedagogy/a1/this-and-that.md

# Педагогіка A1: This And That



## Методичний підхід (Methodological Approach)

The core pedagogical principle for teaching demonstratives (`цей`, `той`) in Ukrainian is to tightly integrate them with the concept of noun gender. Ukrainian elementary school textbooks do not teach these words in isolation; they are presented as a fundamental tool for identifying and reinforcing a noun's gender from the very beginning (Джерело: `3-klas-ukrainska-mova-kravtsova-2020-1_s0062`).

The primary method is **substitution and association**. Learners are taught to associate a noun with a chain of gender-agreeing words. For a masculine noun like `стіл` (table), the chain is `стіл` → `він` (he) → `мій` (my) → `цей` (this) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0030`, `3-klas-ukrainska-mova-ponomarova-2020-1_s0085`). This creates a powerful mental link between the noun and its grammatical gender, making adjective agreement (e.g., `цей червоний стіл`) intuitive later on.

The unchangeable pronoun `це` ("this/that is") is introduced first as a simple identifier. It is the most frequent and simplest form, used in basic sentence patterns like "**Це** + [іменник]" (e.g., "**Це** стіл," "**Це** книга."). This allows learners to start building sentences before tackling gender agreement (Джерело: `ext-video-4`, `5-klas-ukrmova-uhor-2022-1_s0081`).

Only after `цей/ця/це` are mastered as pointers for "close" objects is the "far" equivalent `той/та/те` introduced, often through direct contrastive exercises (`цю книгу чи ту книгу?` — "this book or that book?") (Джерело: `6-klas-ukrmova-litvinova-2023_s0280`).

Finally, demonstratives are presented as a key tool for creating cohesive text by avoiding noun repetition. Textbooks show how words like `цей`, `ця`, `він`, `вона` connect sentences and make writing flow more naturally (Джерело: `4-klas-ukrmova-zaharijchuk_s0014`, `4-klas-ukrayinska-mova-zaharijchuk-2021-1_s0148`). At the A1 level, the focus is purely on the nominative (subject) case. Full declension is a B1 topic (<!-- VERIFY -->).

## Послідовність введення (Introduction Sequence)

The introduction must be methodical and layered, building from the simplest concept to the more complex.

- **Step 1: The Universal Identifier `Це`**
  - **What:** Introduce the word `це` as the universal, gender-neutral way to say "This is..." or "That is...". It answers the question `Що це?` (What is this?).
  - **Why:** This is the highest frequency demonstrative and requires zero knowledge of gender. It allows learners to immediately start identifying objects. For example: `Що це? - Це стіл.` `Що це? - Це книга.` (Джерело: `ext-video-4`). It functions like "It is" in English.

- **Step 2: The Gender Pointers `Цей`, `Ця`, `Це`**
  - **What:** Introduce the three gendered forms of "this": `цей` (masculine), `ця` (feminine), and `це` (neuter). Explicitly link them to the gender pronouns `він`, `вона`, `воно` and possessives `мій`, `моя`, `моє`.
  - **Why:** This directly reinforces noun gender. The teaching pattern is: see a noun (`стіл`), recall its gender pronoun (`він`), and then select the corresponding demonstrative (`цей стіл`) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0030`, `3-klas-ukrainska-mova-vashulenko-2020-1_s0128`). This builds the grammatical reflex for agreement.

- **Step 3: The Plural Pointer `Ці`**
  - **What:** Introduce the plural form `ці` ("these") for all genders.
  - **Why:** After mastering the three singular forms, the single plural form is a simple next step. It shows how gender distinctions disappear in the plural for demonstratives. Example: `ці столи`, `ці книги`, `ці вікна`. (Джерело: `4-klas-ukrmova-zaharijchuk_s0014`).

- **Step 4: Distinguishing "This" vs. "That" (`Той`, `Та`, `Те`, `Ті`)**
  - **What:** Introduce the "far" pointers `той` (m), `та` (f), `те` (n), and `ті` (pl) to contrast with the "near" pointers (`цей`, `ця`, `це`, `ці`).
  - **Why:** This concept of proximity is familiar to English speakers ("this/that"). It should be taught with contrastive examples, physically pointing to near and far objects. For example: `Цей стілець тут, а той стілець там.` (This chair is here, and that chair is there). `Мені, будь ласка, це/те тістечко` (Source 3) is a perfect textbook example of this choice.

- **Step 5: Demonstratives for Text Cohesion**
  - **What:** Show how `цей`, `він`, `вона` etc., are used to refer back to a previously mentioned noun to avoid clumsy repetition.
  - **Why:** This moves learners from single sentences to basic text construction. It's a key feature of natural Ukrainian writing style. (Джерело: `4-klas-ukrayinska-mova-zaharijchuk-2021-1_s0148`, `4-klas-ukrmova-zaharijchuk_s0014`). For example: "Славко купив букет квітів... **Він** також узяв книжку." (Slavko bought a bouquet... **He** also took a book).

## Типові помилки L2 (Common L2 Errors)

English-speaking learners often make predictable errors when learning Ukrainian demonstratives due to interference from English grammar.

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| `Що цей?` | `Що це?` | Learners mistakenly use the gendered `цей` for the general question "What is this?". The correct form for identification is always the neutral, unchangeable `це`. (Джерело: `ext-video-4`) |
| `Ця стіл великий.` | `Цей стіл великий.` | This is a direct gender agreement error. The learner has not yet internalized that `стіл` is masculine and requires the masculine demonstrative `цей`. This is the most common error and is why linking demonstratives to gender is so critical. (Джерело: `3-klas-ukrainska-mova-ponomarova-2020-1_s0085`) |
| `Це стіл є новий.` | `Цей стіл новий.` or `Це новий стіл.` | Learners overuse the verb `є` (is/are), translating directly from English. In simple descriptive sentences in Ukrainian, the verb "to be" is usually omitted in the present tense. The first correct option uses the demonstrative as a pointer, while the second uses `це` as an identifier. |
| `Це столи.` | `Ці столи.` | The learner incorrectly uses the singular identifier `це` when pointing to multiple items. The correct plural demonstrative is `ці` for "these". (Джерело: `ext-ulp_youtube-261`) |
| `Мені подобається цей дівчина.` | `Мені подобається ця дівчина.` | Another gender agreement error, but with a feminine noun. The learner applies the default/masculine form `цей` to the feminine noun `дівчина`. (Джерело: `5-klas-ukrmova-uhor-2022-1_s0030`) |
| `Я живу в цей будинок.` | `Я живу в цьому будинку.` | This is a case error. While full declension is not an A1 topic, learners will encounter prepositions. They often incorrectly use the nominative form (`цей`) after a preposition instead of the required locative (`цьому`). This should be taught as a fixed chunk (`в цьому будинку`) at A1, with the grammatical explanation delayed. (<!-- VERIFY -->) |

## Деколонізаційні застереження (Decolonization Notes)

Teaching Ukrainian requires a conscious effort to de-link it from Russian and establish its own phonetic and grammatical foundation in the learner's mind.

1.  **Independent Phonetics:** The sound `[ц]` must be taught as a native Ukrainian phoneme. Do not describe it as "like the Russian ц". Use examples from within Ukrainian, like `цукор` (sugar), `палець` (finger), `кінець` (end). The learner's reference point must be Ukrainian itself.

2.  **No Russian Cognates as a Crutch:** Avoid teaching `цей` by comparing it to Russian `этот` or `той` to `тот`. While they are cognates from a common Slavic root, using Russian as the bridge reinforces a colonial linguistic dependency. Teach `цей` and `той` through their function and context within Ukrainian only.

3.  **Emphasize Native Etymology:** Briefly explain that `цей` comes from an older Ukrainian form `отъ + сей` ("lo, this"), which evolved into `отсей` and then was re-analyzed as `о-цей`, eventually yielding the standalone `цей` (Джерело: `ext-istoria_movy-103`). This demonstrates a clear, internal path of development for the word within the Ukrainian language itself, countering any false narrative of it being a Russian import or derivative.

4.  **Ukrainian Sentence Structure:** Stress that the omission of "to be" (`є`) in sentences like `Цей стіл червоний` is a standard feature of Ukrainian grammar. It is not an "informal" version of a structure that "should" have a verb like in Russian (`Этот стол есть красный`). This validates Ukrainian grammar on its own terms.

5.  **Stylistic Norms:** The use of demonstratives and personal pronouns (`цей`, `він`, `вона`) to avoid repeating nouns is a characteristic of good Ukrainian style, as taught in Ukrainian schools (Джерело: `4-klas-ukrmova-zaharijchuk_s0014`, `2-klas-ukrmova-bolshakova-2019-2_s0044`). It should be presented as a native stylistic device, not a calque from another language.

## Словниковий мінімум (Vocabulary Boundaries)

This vocabulary is appropriate for A1 learners when practicing demonstratives. It focuses on concrete, point-able objects found in a classroom or home.

**Іменники (Nouns):**
- ★★★ `стіл` (table) (Джерело: `ext-ulp_youtube-261`)
- ★★★ `стілець` (chair) (Джерело: `ext-ulp_youtube-261`)
- ★★★ `книга` (book)
- ★★★ `ручка` (pen) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0030`)
- ★★★ `вікно` (window) (Джерело: `ext-ulp_youtube-261`)
- ★★☆ `будинок` (house, building) (Джерело: `3-klas-ukrainska-mova-vashulenko-2020-1_s0128`)
- ★★☆ `кімната` (room) (Джерело: `ext-ulp_youtube-261`)
- ★★☆ `двері` (door - *plural only*) (Джерело: `ext-ulp_youtube-261`)
- ★★☆ `олівець` (pencil) (Джерело: `3-klas-ukrainska-mova-savchenko-2020-2_s0009`)
- ★★☆ `шафа` (wardrobe, cabinet) (Джерело: `ext-ulp_youtube-261`)
- ★☆☆ `ліжко` (bed) (Джерело: `ext-ulp_youtube-261`)
- ★☆☆ `поле` (field) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0030`)

**Прикметники (Adjectives):**
- ★★★ `новий` (new) (Джерело: `4-klas-ukrayinska-mova-zaharijchuk-2021-1_s0065`)
- ★★★ `старий` (old) (Джерело: `6-klas-ukrmova-betsa-2023_s0113`)
- ★★★ `великий` (big)
- ★★★ `малий` (small)
- ★★☆ `червоний` (red) (Джерело: `10-klas-ukrajinska-mova-avramenko-2018_s0186`)
- ★★☆ `синій` (blue) (Джерело: `3-klas-ukrainska-mova-vashulenko-2020-1_s0128`)
- ★★☆ `жовтий` (yellow) (Джерело: `6-klas-ukrmova-betsa-2023_s0113`)
- ★★☆ `зелений` (green) (Джерело: `6-klas-ukrmova-betsa-2023_s0113`)
- ★★☆ `гарний` (good, beautiful) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0081`)

**Дієслова (Verbs):**
- ★★★ `бути` (to be)
- ★★★ `мати` (to have)
- ★★★ `бачити` (to see)
- ★★☆ `жити` (to live) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0081`)
- ★★☆ `хотіти` (to want)

## Приклади з підручників (Textbook Examples)

These exercises, adapted from Ukrainian school materials, provide a gold standard for practice activities.

1.  **Gender Sorting with Demonstratives (Джерело: `3-klas-ukrainska-mova-kravtsova-2020-1_s0062`)**
    - **Format:** Sorting task. Provide a list of nouns and three columns.
    - **Prompt:** "Розподіли іменники за родами. Запиши назви в потрібний рядок." (Distribute the nouns by gender. Write the names in the correct row.)
    - **Task:**
        - **Він, мій, цей:** `стіл`, `олівець`, `будинок`
        - **Вона, моя, ця:** `книга`, `ручка`, `шафа`
        - **Воно, моє, це:** `вікно`, `ліжко`, `поле`

2.  **Forced Choice: This vs. That (Джерело: `6-klas-ukrmova-litvinova-2023_s0280`)**
    - **Format:** Multiple choice within a sentence.
    - **Prompt:** "Прочитайте речення, обираючи правильний займенник." (Read the sentences, choosing the correct pronoun.)
    - **Task:**
        - 1. Привал буде за (цією / тією) горою. (The stop will be behind *this* / *that* mountain.)
        - 2. Мені, будь ласка, (це / те) тістечко. (For me, please, *this* / *that* pastry.)
        - 3. Візьміть (цю / ту) книгу, не пошкодуєте. (Take *this* / *that* book, you won't regret it.)

3.  **Adjective and Demonstrative Agreement (Джерело: `6-klas-ukrmova-betsa-2023_s0113`, `3-klas-ukrainska-mova-vashulenko-2020-1_s0128`)**
    - **Format:** Fill-in-the-blanks for endings.
    - **Prompt:** "Оберіть правильний варіант закінчення." (Choose the correct ending.)
    - **Task:**
        - Який? (m): `Нов__ стіл`, `цікав__ фільм`, `цей хорош__ друг` → (`-ий`, `-ий`, `-ій`)
        - Яка? (f): `Ця нов__ сукня`, `цікав__ казка` → (`-а`, `-а`)
        - Яке? (n): `Це нов__ крісло`, `цікав__ оповідання` → (`-е`, `-е`)

4.  **Text Cohesion via Pronoun Substitution (Джерело: `4-klas-ukrmova-zaharijchuk_s0014`)**
    - **Format:** Text rewriting.
    - **Prompt:** "Спишіть текст, уникаючи повторів виділених слів. Підкресліть слова, які зв’язують речення в тексті." (Rewrite the text, avoiding repetition of the highlighted words. Underline the words that connect the sentences in the text.)
    - **Original Text:** "Марусі... подарували маленький рожевий ноутбук. **Ноутбук** став для Марусі найкращим другом. **Ноутбук** зберігав маленькі таємниці дівчинки..."
    - **Expected Output:** "Марусі... подарували маленький рожевий ноутбук. **Він** став для Марусі найкращим другом. **Цей комп'ютер** зберігав маленькі таємниці дівчинки..."

## Пов'язані статті (Related Articles)

- `pedagogy/a1/noun-gender`
- `pedagogy/a1/adjective-agreement`
- `pedagogy/a1/personal-pronouns`
- `pedagogy/a2/introduction-to-cases`
- `grammar/nouns/pluralization`
</wiki_context>

## Plan References

- 
- 
- 

</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Дні тижня (Days of the Week)` (~300 words)
- `## Місяці і пори року (Months and Seasons)` (~300 words)
- `## Підсумок — Summary` (~300 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 15-25% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — explain the grammar concept once, clearly.
- EXAMPLES: Ukrainian sentences in bulleted lists (each line: Ukrainian — English gloss). Max 2-4 per rule.
- TABLES: Paradigm tables, gender sorting, vocabulary groups — all cells Ukrainian.
- PATTERN BOXES: Show transformations and rules: `книга → книги` (singular → plural).
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences go in tables, bulleted lists, or pattern boxes — never in flowing prose.
Ukrainian sentences max 10 words. Mix container types.

HARD GRAMMAR RULES (audit will reject violations):
- Max 10 words per Ukrainian sentence (STRICT — count every word)
- ONLY 1 clause per sentence (no compound sentences)
- Dative case FORBIDDEN (no мені, тобі, йому, їй, вам, їм, -ові/-еві endings)
  Exception: нам is taught as decodable vocabulary in M1 (reading drill word, not grammar)
  Exception (M15 what-i-like): Dative forms мені/тобі/йому/їй/нам/вам/їм allowed
    ONLY in the fixed construction «Мені подобається + noun/infinitive». Teach as a memorized
    chunk — do NOT explain dative case rules or paradigms.
- Instrumental case FORBIDDEN (no з другом, з мамою, -ом/-ою/-ем/-ею endings)
  Exception: M37 introduces basic Instrumental 'з' (кава з молоком)
- NO subordinate clauses: який/яка/яке, що-clause, коли, якщо, тому що, бо, щоб, поки are ALL BANNED
- Only imperfective aspect verbs
- No participles
- Allowed cases: Nominative, Accusative, Locative (from M30), Genitive (basics), Vocative

PLAN-AWARE EXEMPTIONS: The following bans are RELAXED for this module because the plan explicitly teaches these constructs: Subordinate clauses (plan teaches them). Exception: If a grammar construct appears in this module's plan grammar list or objectives, it is ALLOWED for this module.

### Pedagogy
- Start each section with a real situation or dialogue (PPP: Present → Practice → Produce)
- Every grammar rule needs 3+ Ukrainian examples with English translations
- Teach through PATTERNS, not rules: show examples first, then name the pattern
- Cultural context where relevant — this is Ukrainian, not generic L2
- Use vocabulary from the plan's vocabulary_hints. Function words (pronouns, conjunctions) are always allowed.

### Ukrainian Language Quality
- **Zero Russian**: No ы, э, ё, ъ. No Russian words (кот→кіт, хорошо→добре, конечно→звичайно)
- **Zero Surzhyk**: No шо→що, чо→чому, тіпа→типу
- **Zero calques**: No приймати душ→брати душ, приймати рішення→ухвалювати рішення
- **Zero paronyms**: тактична≠тактовна, ефектний≠ефективний — use the right word, not a similar-sounding one
- **Natural Ukrainian**: Write how a Ukrainian teacher would explain this to a student. Not robotic, not textbook-dry, not overly casual.

**Authority hierarchy (if uncertain about a word, check in this order):**
VESUM (does word exist?) → Правопис 2019 (spelling) → Горох (stress) → Антоненко-Давидович (style) → Грінченко (etymology).

**Online fallbacks:** VESUM: vesum.com.ua | Правопис: 2019.pravopys.net | Горох: goroh.pp.ua | Антоненко-Давидович: ukrlib.com.ua/books/printit.php?tid=4002 | Грінченко: hrinchenko.com | Словник.ua: slovnyk.me

### Writing Quality
- Every paragraph: ONE clear point, logical flow to the next
- Vary sentence length (short for emphasis, medium for explanation, long for examples)
- Use callout boxes (:::tip, :::caution, :::note) — at least 3 per module (mnemonics, common mistakes, cultural notes). Space them throughout the module, not clustered.
- **Dialogue formatting** — use blockquote `>` with speaker names in bold. Each turn on its own line. At A1 level, add English translation in italics after each line so learners understand what is being said. At A2, translate only new vocabulary. At B1+, no dialogue translations. Example:

> **Оленка:** Привіт! Як справи? *(Hi! How are you?)*
> **Тарас:** Добре, дякую! А у тебе? *(Good, thanks! And you?)*
> **Оленка:** Теж добре! *(Also good!)*

Without speaker names, the reader cannot tell who is speaking. NEVER use anonymous em dashes (`— text`). After each dialogue, briefly explain the key phrases and patterns the learner just saw.
- **Dialogues must sound like real people talking.** Test: would two Ukrainians actually say this to each other? If the dialogue sounds like a textbook drill ("Це кінь? — Так, це кінь."), rewrite it. Good dialogues have context, reactions, and personality:

  BAD (interrogation): "Це сім'я? — Так, це сім'я. — А де м'ясо? — М'ясо там."
  GOOD (natural): "Це твоя сім'я на фото? — Так! Нас п'ять. — А що ви їсте? М'ясо? — Так, дуже смачне!"

  BAD (labeling objects): "Це дуб. — А там коза. — Ні, це коса."
  GOOD (real reaction): "Дивись, який великий дуб! — Так, старий. А під ним — коза! — Смішна коза."

  Use the knowledge packet's textbook excerpts for dialogue patterns. Adapt real situations, don't invent drills.
- **DIALOGUE VARIETY — CRITICAL.** Each module MUST have DIFFERENT dialogue situations from other modules. Before writing any dialogue, check: have previous modules used this setting? If yes, pick a different one.

  BANNED recurring settings (already used in M01-M09): describing a room (кімната), looking at a table/bed/lamp, generic greetings with no context, labeling objects.

  REQUIRED: Every dialogue must have a SPECIFIC REAL-WORLD SITUATION that motivates the grammar being taught. The situation must be different from all other modules.

  **Module-specific dialogue settings (from plan):**
  1. **At a doctor's reception — booking an appointment**
     Speakers: Пацієнт, Реєстратор
     Why: Days and months: У понеділок? Ні, у середу. В якому місяці?

  Use these settings. Do NOT substitute with a room description or generic greeting.
- **Tone: direct, clear, no filler.** State facts and teach. Don't praise the language ("beautiful", "wonderful", "unique melody"), don't praise the learner ("great job", "you've mastered"), don't narrate what you're doing ("In this section we will", "Now let's look at"). Just teach. Example:

  BAD: "The Ukrainian language has a wonderfully consistent and beautiful phonetic system."
  GOOD: "Ukrainian spelling is highly phonetic — what you see is what you hear."
- **Never guess about Ukrainian.** If you are unsure about a word, grammatical form, or phonetic rule — flag it with `<!-- VERIFY: word/claim -->`. Never invent or describe vaguely to hide uncertainty.

### Forbidden Tropes

If you write any of these patterns, the module will be rejected in review:

- **The Cheerleader:** "Great job!", "Don't worry, it's easy!", "You're doing amazing!", "Good news!" — respect the learner's intelligence; stay professional.
- **The Announcer:** "In this section, we will explore...", "Now let's dive into...", "Let's take a look at...", "To summarize what we learned..." — never use formulaic transitions. Just teach the concept directly.
- **The Translator:** "The Ukrainian word for 'cat' is 'кіт'." — instead, present naturally: "A domestic cat is a **кіт**."
- **The Wall of Text:** 3+ paragraphs of English theory without a single Ukrainian example — every concept must be anchored in immediate Ukrainian examples.
- **The Filler:** "This is a very important concept that you will use frequently in your daily life." — empty sentences that add words but not meaning. Every sentence must teach something.

GRAMMAR CONSTRAINTS (A1.4 — Time & Nature, M22-M28):
Time expressions, days, months, weather, daily routines.

ALLOWED:
- All present tense (from A1.3)
- Time expressions as chunks (О першій, У понеділок)
- Sequence adverbs (спочатку, потім, нарешті)
- Impersonal weather constructions (Сьогодні холодно)

BANNED: Past/future tense, case endings (time chunks only),
participles, passive voice, complex subordination

### Vocabulary

**Required:** понеділок, вівторок, середа (Mon, Tue, Wed), четвер, п'ятниця (Thu, Fri), субота, неділя (Sat, Sun), тиждень (week, m), зима, весна, літо, осінь (winter, spring, summer, autumn)
**Recommended:** січень, лютий, березень (Jan, Feb, Mar), квітень, травень, червень (Apr, May, Jun), липень, серпень, вересень (Jul, Aug, Sep), жовтень, листопад, грудень (Oct, Nov, Dec), день народження (birthday)

### Pronunciation Videos

**Do NOT embed YouTube videos in your prose.** A downstream ENRICH tool automatically places pronunciation videos from the plan. If you embed `<YouTubeVideo>` components, they will be duplicated. Simply reference the videos' existence when relevant (e.g., "Watch the pronunciation video for this letter") but do NOT insert `<YouTubeVideo>` tags.

Available videos (for reference only — ENRICH handles placement):


---

### Style Reference (match this tone and structure)

> **(У магазині / At the store)**
> — Добрий день! Скільки коштує хліб? (Good day! How much does the bread cost?)
> — Дванадцять гривень. (Twelve hryvnias.)
> — Дякую! Ось, будь ласка. (Thanks! Here you go.)

Notice that the shopkeeper uses **Добрий день** — the formal greeting for strangers. If this were a friend, they would say **Привіт** instead.

The word **скільки** (how much/how many) is one of the most useful question words. It always pairs with the genitive case: **скільки коштує** (how much does it cost), **скільки часу** (how much time).

*Note: Short dialogues in Ukrainian with per-line English glosses. Grammar explained in English. Ukrainian sentences in blockquotes and bulleted lists.*



---

## Skeleton — Follow This Structure Exactly

A detailed paragraph-level skeleton was generated for this module. You MUST follow it precisely:
- Write every paragraph listed, in the order listed
- Hit each paragraph's word budget (+-10%)
- Place exercises exactly where the skeleton says
- Use the specific examples named in the skeleton
- Do NOT skip paragraphs, reorder sections, or add unplanned content

The skeleton replaces Step 1 (Pacing Plan) — do NOT output a <pacing_plan> block. Start writing immediately from the first section.

<skeleton>
## Діалоги — Dialogues (~330 words total)
- P1 (~40 words): Introduce the context of time management and scheduling in Ukraine. Explain that planning revolves around the "тиждень" (week) and begins strictly on "понеділок" (Monday).
- P2 (~120 words): Dialogue 1 — Planning the week. Олена and Марко discuss their schedules. Use days as markers: "Що ти робиш у понеділок?" (working), "А у вівторок?" (Ukrainian class), "У суботу?" (walking), "Неділя — вільний день."
- P3 (~50 words): Linguistic breakdown of Dialogue 1. Highlight the question "Що ти робиш у...?" and the concept of "вільний день" (free day) vs. "робочий день" (work day).
- P4 (~100 words): Dialogue 2 — Birthdays and Seasons. Андрій and Софія discuss their birthdays. Use months and seasons: "Коли у тебе день народження?" "У березні." "Якого числа?" "П'ятнадцятого березня." "Це весна?" "Так, початок весни."
- P5 (~20 words): Quick check: Note that "Якого числа?" (What date?) and the response "П'ятнадцятого березня" (The 15th of March) are learned as chunks for now.

## Дні тижня — Days of the Week (~330 words total)
- P1 (~80 words): Present the seven days in order: понеділок, вівторок, середа, четвер, п'ятниця, субота, неділя. Explicitly state the two golden rules: Ukrainian days are NOT capitalized, and the week starts on Monday.
- P2 (~90 words): Explain how to say "on [day]" using "у/в" + the day form. Detail the masculine stability (у понеділок, у вівторок, у четвер) versus the feminine vowel shift (середа -> у середу, п’ятниця -> у п’ятницю, неділя -> в неділю).
- P3 (~80 words): Focus on "неділя" (Sunday). Address the common error for Slavic-language learners: "неділя" is Sunday, while "тиждень" is the whole week. Explain the etymology "не ділати" (no work) to anchor the meaning.
- P4 (~80 words): Expand vocabulary for time-blocks: "робочі дні" (work days, Mon-Fri) vs. "вихідні" (weekend, Sat-Sun). Use examples: "У робочі дні я в офісі," "У вихідні я вдома."
- <!-- INJECT_ACTIVITY: fill-in-days-order --> [fill-in, focus: ordering the days of the week, 7 items]

## Місяці і пори року — Months and Seasons (~340 words total)
- P1 (~80 words): Introduce the 12 months grouped by the four seasons: Зима (грудень, січень, лютий), Весна (березень, квітень, травень), Літо (червень, липень, серпень), Осінь (вересень, жовтень, листопад). All lowercase.
- P2 (~90 words): The story of the months. Connect names to nature: "березень" (birch), "квітень" (flower), "липень" (linden tree), "вересень" (heather), "листопад" (leaf fall). Contrast this native Slavic system with the Latin names in English and Russian.
- P3 (~80 words): Explain "in [month]" using "у/в" + the month name in Locative. Focus on the "-і" ending (у січні, у квітні) and the dropping of the vowel "е" (березень -> у березні, жовтень -> у жовтні). Note the exception for "лютий" -> "у лютому."
- P4 (~90 words): Teaching the seasons as adverbs for "when." Introduce irregular forms that must be memorized: взимку (in winter), навесні (in spring), влітку (in summer), восени (in autumn). Compare them to the base nouns: зима, весна, літо, осінь.
- <!-- INJECT_ACTIVITY: match-up-months-seasons --> [match-up, focus: connecting months to their corresponding season, 8 pairs]
- <!-- INJECT_ACTIVITY: fill-in-day-month-chunks --> [fill-in, focus: using correct 'in/on' chunks for days, months, and seasons, 6 items]

## Підсумок — Summary (~300 words total)
- P1 (~100 words): Provide a consolidated reference table mapping the base noun (Що?) to the time expression (Коли?).
    - понеділок -> у понеділок
    - середа -> у середу
    - січень -> у січні
    - зима -> взимку
- P2 (~80 words): Final recap on decolonization. Reiterate why using "березень" instead of "март" and starting on Monday are vital steps in thinking like a Ukrainian. Mention the soft sign "ь" in months like "січень."
- P3 (~120 words): Interactive Self-Check. Answer the following questions based on today:
    - Який сьогодні день тижня? (Сьогодні ...)
    - Який зараз місяць? (Зараз ...)
    - Яка зараз пора року? (Зараз ...)
    - Коли у тебе день народження? (Мій день народження у ...)
    - Що ти робиш у суботу? (У суботу я ...)

Grand total: ~1300 words
</skeleton>

## Output Format

Write in Markdown. Use:
- `## Section Title` for main sections
- `### Subsection` for subsections within a section
- `**bold**` for Ukrainian words being taught — EVERY bold Ukrainian word MUST have an English translation on first use, either in parentheses `**слово** (translation)` or inline `**слово** means "translation"`. No exceptions.
- Tables for paradigms (conjugation, declension)
- `:::tip` / `:::caution` / `:::note` for callout boxes
- `<!-- INJECT_ACTIVITY: {id} -->` for exercise placement (markers only — do NOT write exercise content)

Do NOT write MDX component syntax, JSON, or DSL exercise blocks (:::quiz, etc.). Plain Markdown with injection markers.

Begin writing now. Start with the first section heading.
