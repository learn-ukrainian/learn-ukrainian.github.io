

---

## Your Writing Identity

**You are: Lead Ukrainian Instructor.** Your persona is *The Patient Guide*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **46: Holidays** (A1, A1.7 [Communication]).

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

1. **IMMERSION TARGET: 20-35% Ukrainian** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if immersion is outside this range. For A1 early modules, the learner cannot read Cyrillic — English must dominate. For A2+, Ukrainian must carry a significant share — add Ukrainian Reading Practice blocks, dialogues, and example paragraphs to reach the target. Too little Ukrainian fails audit just as much as too much.
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
module: a1-046
level: A1
sequence: 46
slug: holidays
version: '1.1'
title: Holidays
subtitle: Різдво, Великдень, День Незалежності — Ukrainian celebrations
focus: cultural
pedagogy: PPP
phase: A1.7 [Communication]
word_target: 1200
objectives:
- Name and describe major Ukrainian holidays (Різдво, Великдень, День Незалежності)
- Use holiday greetings appropriately (З Різдвом! З Великоднем! З Днем Незалежності!)
- Talk about what people do on holidays using known vocabulary
- Understand the cultural significance of Ukrainian holidays
dialogue_situations:
- setting: 'Ukrainian Святвечір (m, Christmas Eve) dinner — explaining 12 dishes:
    кутя (f, kutia), борщ (m), вареники (pl), риба (f, fish), узвар (m, dried fruit
    compote). З Різдвом Христовим! Зі святом!'
  speakers:
  - Українська родина
  - Іноземний гість
  motivation: 'Holiday food: кутя(f), борщ(m), вареники(pl), узвар(m) + greetings'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Before Christmas: — Коли в тебе Різдво? — Двадцять п''ятого грудня.
    А в тебе? — У нас — теж! Раніше святкували сьомого січня, але тепер — двадцять
    п''ятого. — Що ви робите на Різдво? — Ми співаємо колядки і їмо кутю. — Як гарно!
    З Різдвом! — З Різдвом Христовим! Різдво vocabulary: колядки (carols), кутя (kutia
    — ritual dish), святкувати.'
  - 'Dialogue 2 — Independence Day: — Двадцять четверте серпня — День Незалежності!
    — Так, це головне державне свято України. — Що ви робите? — Ми дивимося парад
    і ходимо на концерт. — А ввечері? — Ввечері — салют і святковий вечір з друзями.
    — З Днем Незалежності! — Слава Україні! National holiday: парад, концерт, салют.'
- section: Українські свята (Ukrainian Holidays)
  words: 300
  points:
  - 'Різдво (Christmas) — December 25: Ukraine moved Christmas from January 7 to December
    25 in 2023. January 7 was the Russian Orthodox date; December 25 aligns with Europe.
    Traditions: Свята вечеря (Holy Supper) on December 24 — 12 страв (12 dishes).
    кутя (kutia) — wheat porridge with honey and poppy seeds — the first dish. колядки
    (carols) — traditional Christmas songs. Колядники go door to door.'
  - 'Великдень (Easter): The biggest religious holiday. Date changes each year (spring).
    Traditions: писанки (decorated eggs — unique Ukrainian art), паска (Easter bread),
    святити кошик (blessing the Easter basket at church). Greeting: Христос воскрес!
    — Воістину воскрес! (Christ is risen! — Indeed risen!)'
- section: Державні свята (National Holidays)
  words: 300
  points:
  - 'День Незалежності — August 24, 1991: Ukraine declared independence from the Soviet
    Union. The most important державне свято (national holiday). Celebrations: парад
    (parade), концерти, салют (fireworks), прапори (flags). Greeting: З Днем Незалежності!
    (Happy Independence Day!) Слава Україні! — Героям слава! (Glory to Ukraine! —
    Glory to the heroes!)'
  - 'Other holidays to know: Новий рік (New Year) — January 1 — biggest secular celebration.
    Вишиванковий день (Vyshyvanka Day) — third Thursday of May. Everyone wears вишиванка
    (embroidered shirt) — symbol of Ukrainian identity. День Конституції (Constitution
    Day) — June 28. День захисників і захисниць (Defenders'' Day) — October 1.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Holiday greetings pattern: З + instrumental case! З Різдвом! (Merry Christmas!)
    З Великоднем! (Happy Easter!) З Новим роком! (Happy New Year!) З Днем Незалежності!
    З днем народження! (Happy birthday!) Pattern: З + [holiday/occasion in instrumental]
    + ! You already know instrumental from з + noun (кава з молоком). Here it''s the
    same: ''with'' the holiday → instrumental. Quick calendar: грудень 25 — Різдво,
    січень 1 — Новий рік, весна — Великдень, серпень 24 — День Незалежності. Self-check:
    How do you say ''Merry Christmas'' and ''Happy New Year''?'
vocabulary_hints:
  required:
  - свято (holiday, n)
  - святкувати (to celebrate)
  - Різдво (Christmas, n)
  - Великдень (Easter, m)
  - Новий рік (New Year)
  - вітати (to congratulate/greet)
  recommended:
  - кутя (kutia, f)
  - колядка (carol, f)
  - писанка (decorated Easter egg, f)
  - паска (Easter bread, f)
  - парад (parade, m)
  - прапор (flag, m)
  - вишиванка (embroidered shirt, f)
  - незалежність (independence, f)
  - салют (fireworks, m)
activity_hints:
- type: quiz
  focus: 'Match holiday to date: Різдво → 25 грудня, День Незалежності → 24 серпня'
  items: 8
- type: fill-in
  focus: 'Greetings: З ___! (Різдвом, Великоднем, Новим роком)'
  items: 8
- type: quiz
  focus: Which holiday? Кутя, колядки, Свята вечеря → (Різдво / Великдень / Новий
    рік)
  items: 8
- type: group-sort
  focus: 'Sort traditions by holiday: Різдво vs Великдень vs День Незалежності'
  items: 10
connects_to:
- a1-047 (Checkpoint — Communication)
prerequisites:
- a1-045 (When and Where)
grammar:
- 'З + instrumental for holiday greetings: З Різдвом! З Великоднем!'
- 'Review: dates (М18), instrumental chunks (М36)'
register: розмовний
references:
- title: ULP Season 1, Episode 23
  url: https://www.ukrainianlessons.com/episode23/
  notes: Ukrainian holidays and celebrations.
- title: State Standard 2024, §3 (традиції)
  notes: 'Thematic area: traditions, holidays, cultural practices.'

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
- Confirmed: свято, святкувати, різдво (Різдво), великдень (Великдень), новий (Новий), рік (рік), вітати, кутя, колядка, писанка, паска, парад, прапор, вишиванка, незалежність, салют.
- Not found: None (all plan words verified as existing in standard Ukrainian forms).

## Grammar Rules
- **Holiday Capitalization**: Правопис §52 — In names of holidays, the first word is capitalized: *Новий рік*, *День учителя*. 
- **National Holidays**: Правопис §52, Примітка 1 — In the names *День Незалежності України*, *День Соборності України*, *День Конституції України*, all words are capitalized.
- **Greetings Pattern**: Greetings use the preposition *З* + the name of the holiday in the Instrumental case: *З Різдвом!*, *З Новим роком!*, *З Днем Незалежності!*.

## Calque Warnings
- **приймати участь**: Calque from Russian — The correct Ukrainian form is **брати участь**.
- **наступаюче свято**: Calque from Russian — Use **прийдешнє свято** or simply **наближення свята**.
- **салют**: OK, but **феєрверк** is often preferred for festive displays.

## CEFR Check
- **свято**: A1 — OK
- **Різдво**: A1 — OK
- **Великдень**: A1 — OK
- **прапор**: A1 — OK
- **незалежність**: A1 (Contextual) — OK for a module on national holidays.
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
# Knowledge Packet: Holidays
**Module:** holidays | **Track:** A1

<wiki_context>
## Compiled Wiki Knowledge

The following articles from the project wiki provide compiled knowledge relevant to this module. Use them as authoritative context — they were compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).

### Вікі: pedagogy/a1/holidays.md

# Педагогіка A1: Holidays



## Методичний підхід (Methodological Approach)
Holidays (**свя́та**) are a cornerstone of early language learning in Ukrainian schools, serving as a high-interest vehicle for cultural immersion and foundational grammar. The approach is holistic, combining language with tradition.

1.  **Categorization as a Framework:** Ukrainian pedagogy introduces holidays by classifying them into three main groups: **релігійні** (religious), **традиційні** (traditional), and **державні** (state) (Source 1, 19). This helps learners organize vocabulary and cultural context from the start. A1 focuses on the most prominent examples from each category.

2.  **Seasonal Cycles:** The curriculum is often structured around the seasons, particularly the **зимовий цикл свят** (winter cycle of holidays) (Source 3). This is because it is rich in distinct, memorable traditions (Миколая, Різдво, Новий Рік), each with its own songs and rituals that are easy for beginners to grasp (Source 3, 38, 39). The spring cycle with **Великдень** (Easter) is another major focus (Source 10, 37).

3.  **Function-First Grammar:** Grammatical concepts are not taught in isolation but through their immediate function in holiday contexts.
    *   The instrumental case is introduced via the universal greeting formula: `(Вітаю) з + [назва свята в орудному відмінку]` (Source 2).
    *   The genitive case is introduced for making wishes: `Бажаю + [побажання в родовому відмінку]` (e.g., `щастя`, `здоров'я`, `миру`) (Source 2).

4.  **Tangible & Sensory Vocabulary:** The vocabulary is tied to concrete objects, foods, and actions, which aids memorization. For Різдво, learners are taught **кутя**, **вертеп**, **колядки** (Source 6, 19). For Великдень, they learn **паска**, **крашанки**, **писанки** (Source 5, 10). This makes the language feel alive and useful.

5.  **Songs and Poems as Core Material:** Simple, repetitive holiday songs (**колядки**, **щедрівки**) and poems are not supplementary but core teaching tools in primary grades (Source 36, 38, 39). Their rhythm and rhyme make pronunciation and sentence structure more intuitive for learners.

## Послідовність введення (Introduction Sequence)
The introduction of holidays and related language should follow a logical progression from simple, universal concepts to more specific cultural and grammatical structures.

-   **Step 1: The Concept of "Свято" and Universal Greeting.**
    -   Introduce the word **свя́то** (holiday).
    -   Teach the most basic, all-purpose greeting: **«Зі свя́том!»** ("Happy Holiday!"). Explain that this can be used for almost any occasion when you're not sure of the specific greeting (Source 2).

-   **Step 2: Foundational Greeting Formula (`З + Instrumental`).**
    -   Introduce the core structure for greetings: `(Вітаю) з + [Іменник в Орудному відмінку]`.
    -   Start with the two most internationally recognized holidays: **Нови́й рік** → **«З Нови́м ро́ком!»** and **Різдво́** → **«З Різдво́м (Христо́вим)!»**.
    -   Add the most personal holiday: **день наро́дження** → **«З днем наро́дження!»** (Source 2). This provides three high-frequency, immediately useful examples.

-   **Step 3: The Winter Cycle (Зимовий цикл).**
    -   Introduce the holidays sequentially as they occur:
        1.  **День Свято́го Микола́я** (Dec 19): Taught as the first winter holiday that brings gifts to children (Source 2, 3). Greeting: **«З Днем Свято́го Микола́я!»**.
        2.  **Різдво́** (Dec 25): Presented as a major family holiday with key vocabulary: **Святве́чір** (Christmas Eve), **кутя́**, **коля́дки**, **верте́п** (Sources 3, 6, 8).
        3.  **Нови́й Рік** (Jan 1): Taught with vocabulary like **яли́нка** (Christmas/New Year tree) and **подару́нки** (gifts) (Source 18).

-   **Step 4: The Spring Cycle (Весняний цикл).**
    -   Introduce **Вели́кдень / Па́сха** (Easter) as the next major holiday.
    -   Teach associated vocabulary: **па́ска** (Easter bread), **кра́шанки** (dyed eggs), and **пи́санки** (decorated eggs) (Source 5, 10, 36).
    -   Introduce the traditional call-and-response greeting: **«Христо́с Воскре́с!»** — **«Воі́стину Воскре́с!»** (Source 10).

-   **Step 5: Foundational "Wish" Formula (`Бажаю + Genitive`).**
    -   Once learners are comfortable with greetings, introduce the concept of making wishes.
    -   Teach the pattern `Бажа́ю + [Іменник в Родовому відмінку]`.
    -   Provide a memorizable list of the most common wishes: **ща́стя, здоро́в'я, ра́дості, коха́ння, ми́ру** (Source 2). This provides a gentle introduction to the genitive case through functional chunks.

-   **Step 6: Introduction to State Holidays.**
    -   Briefly introduce key state holidays primarily as vocabulary and cultural knowledge, without deep historical dives at A1.
    -   **День Незале́жності Украї́ни** (Aug 24) (Source 9, 23).
    -   **День Собо́рності Украї́ни** (Jan 22) (Source 1, 9). The concept of *соборність* (unity) can be simplified as "Схід і Захід разом" (East and West together) (Source 1).

## Типові помилки L2 (Common L2 Errors)
English speakers often fall into predictable traps due to language transfer or exposure to Russian-influenced Ukrainian. These must be actively corrected.

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| «З наступаючим святом!» | «З прийдешнім святом!» або просто «З Новим роком!», «З Різдвом!» | The word `наступаючий` is a calque from Russian. Ukrainian uses `прийдешній` for "upcoming" or, more naturally, just names the holiday directly. The best practice is to avoid denoting the time proximity altogether (Source 27, 28, 31). |
| «Вітаю з Новий рік» | «Вітаю з Новим роком» | Greetings with the preposition `з` require the instrumental case (`ким/чим?`), not the nominative. This is a core rule for all holiday greetings in Ukrainian (Source 2). |
| «Я їм паску на Великдень.» (Meaning the holiday) | «Я їм паску на Великдень.» (Meaning the bread) | This is a vocabulary error. **Па́сха** can be a synonym for the holiday **Вели́кдень**, but **па́ска** is the specific Easter bread. Learners must be taught to differentiate them to avoid saying "I'm eating Easter (the holiday)" (Source 10, 11, 36). |
| «Хочу привітати тебе...» | «Вітаю тебе...» | The `хочу + інфінітив` construction is a weak form often used by learners. Direct, active verbs are more natural in Ukrainian greetings. It's not a grammatical error, but a stylistic one to be corrected early (Source 13). |
| «Коли є твій день народження?» | «Коли в тебе день народження?» | A direct, word-for-word translation from English ("When is your birthday?"). Ukrainian uses the structure "When at you is birthday?", similar to "I have" (`у мене є`). |
| «Різдво сьомого січня.» | «Різдво двадцять п'ятого грудня.» | This is now a factual error. While some may still celebrate on Jan 7, the official state and church date in Ukraine has moved to Dec 25. Teaching Jan 7 as the primary date is outdated and ignores a significant decolonization step (Source 6, 8). |

## Деколонізаційні застереження (Decolonization Notes)
**This is a mandatory section.** Teaching holidays is a prime opportunity to establish a decolonized understanding of Ukrainian culture from day one.

1.  **The Christmas Date is Political:** The content writer MUST present **December 25th** as the primary and official date for Christmas (Різдво) in Ukraine (Source 8, 9). The shift from January 7th should be explained as a conscious political and cultural decision to "від'єднатися від традиції святкувати Різдво за старим календарем" and align with the majority of the Christian world, breaking from the Russian Orthodox calendar (Source 6, 7). This is non-negotiable.

2.  **Ukrainian Traditions are NOT Russian:** Emphasize the uniqueness of Ukrainian holiday traditions.
    *   **Вертеп** (nativity play): Explain that the Ukrainian tradition evolved into a unique travelling puppet theatre and then a live street performance, which is a hallmark of Ukrainian culture (Source 8).
    *   **Дідух:** Teach the **дідух** (a sheaf of wheat) as the traditional Ukrainian Christmas decoration, symbolizing family ancestors and harvest, pre-dating the German tradition of the Christmas tree (**ялинка**) (Source 6).
    *   **Колядування/Щедрування:** Highlight that the tradition of going from house to house singing carols is a strong, living tradition in Ukraine, unlike in Russia where it is far less prevalent. Mention the suppression of these traditions in the USSR (the "заарештована коляда") to underscore their role in preserving national identity (Source 8).

3.  **No "Shared" East Slavic Ambiguity:** Avoid presenting Ukrainian traditions as generically "East Slavic." While roots may be shared, the lesson must focus on how these traditions manifest *specifically* in Ukraine. The mythology of Коляда turning into a goat to give birth to the new sun, for instance, provides a distinctly Ukrainian folkloric explanation for the "водіння кози" ritual (Source 8).

4.  **Linguistic Purity:** Use only Ukrainian vocabulary. Do not use Russian names for holidays or traditions as parallels or translations. For example, use **Святвечір**, not the Russian `Сочельник`.

## Словниковий мінімум (Vocabulary Boundaries)
This vocabulary should be introduced within the context of A1 holiday modules.

**Іменники (Nouns):**
*   ★★★ (Essential): **свя́то**, **Різдво́**, **Нови́й рік**, **Вели́кдень**, **день наро́дження**, **подару́нок** (gift), **яли́нка** (fir tree), **кутя́**, **па́ска** (Easter bread).
*   ★★ (Useful): **коля́дка** (Christmas carol), **щедрі́вка** (New Year's carol), **верте́п** (nativity play), **пи́санка** (decorated Easter egg), **Святи́й Микола́й**, **День Незале́жності**, **гість** (guest).
*   ★ (Can wait): **Святве́чір** (Christmas Eve), **діду́х**, **Водо́хреще** (Epiphany), **тради́ція**, **зви́чай**.

**Дієслова (Verbs):**
*   ★★★ (Essential): **святкува́ти** (to celebrate), **віта́ти** (to greet), **бажа́ти** (to wish), **дарува́ти** (to give a gift), **співа́ти** (to sing), **готува́ти** (to prepare).
*   ★★ (Useful): **колядува́ти** (to sing carols), **щедрува́ти** (to sing New Year's songs), **прикраша́ти** (to decorate), **ходи́ти в го́сті** (to visit).
*   ★ (Can wait): **посіва́ти** (to sow grains for New Year's), **ворожи́ти** (to tell fortunes).

**Прикметники (Adjectives):**
*   ★★★ (Essential): **новий**, **різдвя́ний**, **велико́дній**, **щасли́вий**, **до́брий**, **смачни́й**.
*   ★★ (Useful): **держа́вний** (state), **релігі́йний** (religious), **традиці́йний**, **святи́й** (holy).

**Фрази (Phrases):**
*   ★★★: **З Нови́м ро́ком!**, **З Різдво́м!**, **З днем наро́дження!**, **Зі свя́том!**, **Смачно́го!** (Enjoy your meal!).
*   ★★: **Христо́с Воскре́с! — Воі́стину Воскре́с!**, **Ще́дрий ве́чір, до́брий ве́чір!**

## Приклади з підручників (Textbook Examples)

**1. Greeting Construction (based on Source 2)**
*   **Завдання:** Складіть привітання. (Create a greeting.)
*   **Інструкція:** Combine the holiday with the wish. For example: `Новий рік + щастя` → `З Новим роком! Бажаю щастя!`
    1.  Різдво + достаток (wealth) → `________________`
    2.  День народження + здоров'я → `________________`
    3.  Великдень + мир (peace) → `________________`

**2. Vocabulary Completion (based on Source 19)**
*   **Завдання:** Вставте правильні слова. (Insert the correct words.)
    *   `співають, готують, стоять, святкують, ходять`
*   **Текст:**
    1.  На Різдво діти і дорослі ... колядки.
    2.  На Святвечір українці ... 12 пісних страв.
    3.  У будинках ... прикрашені ялинки.
    4.  На свята люди ... в гості до родичів.

**3. Holiday Identification (based on Source 12, 36)**
*   **Завдання:** Прочитайте і скажіть, що це за свято. (Read and say what holiday it is.)
    1.  "На столі — духмяна паска, а круг неї — писанки." (Source 37) → **Це ...**
    2.  "Добрий вечір тобі, пане господарю! Винеси ти нам ковбасок пару." (Source 39) → **Це ...**
    3.  "Нова радість стала, яка не бувала: над вертепом звізда ясна світлом засіяла." (Source 38) → **Це ...**

**4. Correcting Common Errors (based on Source 13, 27)**
*   **Завдання:** Знайдіть помилку і напишіть правильно. (Find the mistake and write correctly.)
    1.  `З наступаючим Різдвом!` → `________________`
    2.  `Вітаю з День Незалежності!` → `________________`
    3.  `Паска - моє улюблене свято.` → `________________` (when referring to the holiday, not the bread)

## Пов'язані статті (Related Articles)
- `pedagogy/a1/instrumental-case`
- `pedagogy/a1/genitive-case`
- `culture/traditions/rizdvo-in-ukraine`
- `culture/traditions/velykden-in-ukraine`
- `vocabulary/food/holiday-dishes`

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

</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Українські свята (Ukrainian Holidays)` (~300 words)
- `## Державні свята (National Holidays)` (~300 words)
- `## Підсумок — Summary` (~300 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 20-35% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — brief and clear. Show, don't tell.
- PARADIGM TABLES: Conjugation/declension tables with all cells Ukrainian.
- EXAMPLE LISTS: Ukrainian sentences in bulleted lists (each: Ukrainian — English gloss).
- DIALOGUES: Mini-dialogues in blockquotes with English gloss per line.
- PATTERN BOXES: Show transformations: `читати → читай → читайте`.
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences go in tables, bulleted lists, dialogues, or pattern boxes.
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

PLAN-AWARE EXEMPTIONS: The following bans are RELAXED for this module because the plan explicitly teaches these constructs: Instrumental case (plan teaches it). Exception: If a grammar construct appears in this module's plan grammar list or objectives, it is ALLOWED for this module.

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
  1. **Ukrainian Святвечір (m, Christmas Eve) dinner — explaining 12 dishes: кутя (f, kutia), борщ (m), вареники (pl), риба (f, fish), узвар (m, dried fruit compote). З Різдвом Христовим! Зі святом!**
     Speakers: Українська родина, Іноземний гість
     Why: Holiday food: кутя(f), борщ(m), вареники(pl), узвар(m) + greetings

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

GRAMMAR CONSTRAINTS (A1.7 — People & Communication, M44-M50):
Vocative, imperative, dative, conjunctions, subordinate clauses.

ALLOWED:
- Vocative case (Олено! Тарасе!)
- Imperative mood (Читай! Скажіть! Дайте!)
- Dative case basics (мені, тобі, йому)
- Conjunctions (і, а, але, бо, тому що)
- Simple subordinate clauses (що, де, коли, якщо)
- All cases and tenses from previous phases

BANNED: Past/future tense, participles, passive voice

### Vocabulary

**Required:** свято (holiday, n), святкувати (to celebrate), Різдво (Christmas, n), Великдень (Easter, m), Новий рік (New Year), вітати (to congratulate/greet)
**Recommended:** кутя (kutia, f), колядка (carol, f), писанка (decorated Easter egg, f), паска (Easter bread, f), парад (parade, m), прапор (flag, m), вишиванка (embroidered shirt, f), незалежність (independence, f), салют (fireworks, m)

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
## Вступ: Що таке свято? (~120 words)
- P1 (~120 words): Introduce the general concept of "свято" (holiday) in Ukraine. Categorize holidays into religious (релігійні), traditional (традиційні), and state (державні). Introduce the universal, all-purpose greeting "Зі святом!" (Happy Holiday!) and the verb "святкувати" (to celebrate). Explain that holidays are essential for understanding the Ukrainian soul.

## Діалоги: Говоримо про свята (~330 words)
- P1 (~110 words): Contextual introduction to the first dialogue. Two friends discuss the upcoming Christmas season. Mention the shift in the Ukrainian calendar: celebrating on December 25th (грудень) to align with Europe and break from the Russian Orthodox tradition.
- P2 (~110 words): Dialogue 1 — Christmas Traditions. Two speakers (Українська родина та Іноземний гість) discuss what they do on Dec 24 and 25. Focus on: "Коли в тебе Різдво?", "Ми їмо кутю і співаємо колядки", and the specific greeting "З Різдвом Христовим!".
- P3 (~110 words): Dialogue 2 — Independence Day. Setting: August 24th in a city center. Speakers discuss the atmosphere: "Сьогодні День Незалежності!", "Дивись, який гарний парад і прапори!", "Ввечері буде салют". End with the iconic exchange: "Слава Україні! — Героям слава!".
- <!-- INJECT_ACTIVITY: quiz-holiday-match --> [quiz, Match holiday to date (e.g., Різдво → 25 грудня, День Незалежності → 24 серпня), 8 items]

## Українські свята: Традиції та символи (~340 words)
- P1 (~170 words): Christmas (Різдво) — The Winter Cycle. Detail the significance of December 25th. Describe "Свята вечеря" (Holy Supper) on Christmas Eve with its mandatory "12 страв" (12 dishes). Focus on "кутя" (ritual wheat porridge) as the most important dish. Explain "колядки" (carols) and "колядники" (carolers) who go door to door with a star. Mention the "дідух" (sheaf of wheat) as a traditional decoration.
- P2 (~170 words): Easter (Великдень) — The Spring Cycle. Explain that this is the biggest religious celebration. Introduce "писанки" (artfully decorated eggs) as a unique Ukrainian art form. Distinguish between "Пасха" (the holiday name) and "паска" (the specific Easter bread). Describe the tradition of "святити кошик" (blessing the basket at church). Teach the ritual greeting: "Христос воскрес! — Воістину воскрес!".
- <!-- INJECT_ACTIVITY: quiz-holiday-clues --> [quiz, Identify holiday based on clues (e.g., Кутя, колядки, 12 страв → Різдво), 8 items]

## Державні свята: Громадянська ідентичність (~340 words)
- P1 (~170 words): Independence Day (День Незалежності) — August 24, 1991. Explain that this is the most important "державне свято" (state holiday). Describe the festive atmosphere: military parades (парад), concerts, and the sea of blue and yellow flags (прапори). Use the phrase "вітати з Днем Незалежності" to show how we celebrate freedom and sovereignty.
- P2 (~170 words): Other key celebrations. Introduce "Новий рік" (New Year, Jan 1) as the main secular holiday with the tree (ялинка) and gifts (подарунки). Explain "Вишиванковий день" (Vyshyvanka Day, 3rd Thursday of May) as a living tradition where everyone wears the embroidered shirt ("вишиванка") to show identity. Briefly mention Defenders' Day (October 1) and Constitution Day (June 28).
- <!-- INJECT_ACTIVITY: group-sort-traditions --> [group-sort, Sort traditions and symbols by holiday: Різдво vs Великдень vs День Незалежності, 10 items]

## Підсумок: Граматика вітань та побажань (~210 words)
- P1 (~110 words): Grammar Recap — The Greeting Formula. Explain the pattern: "З + [Holiday in Instrumental Case]!". Show the transformations: Новий рік → "З Новим роком!", Різдво → "З Різдвом!", Великдень → "З Великоднем!", День народження → "З днем народження!". Relate this to the "з + noun" (with) construction they already know (e.g., кава з молоком).
- P2 (~100 words): Wishes and the Calendar. Introduce the "Бажаю + Genitive" formula from the pedagogy brief: "Бажаю щастя, здоров'я, миру" (I wish you happiness, health, peace). Provide a quick calendar overview: 25.12, 01.01, 24.08. 
- P3 (~60 words): Self-check Q&A. 
  - Q: How do you greet someone on August 24? 
  - A: З Днем Незалежності! 
  - Q: What is the ritual response to "Христос воскрес!"? 
  - A: Воістину воскрес! 
  - Q: When is Christmas in Ukraine? 
  - A: Двадцять п'ятого грудня.
- <!-- INJECT_ACTIVITY: fill-in-greetings --> [fill-in, Complete the greeting: З ___! (Новим роком, Різдвом, Великоднем, святом), 8 items]

Grand total: ~1340 words
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
