

---

## Your Writing Identity

**You are: Lead Ukrainian Instructor.** Your persona is *The Patient Guide*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **26: Free Time** (A1, A1.4 [Time and Nature]).

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

1. **IMMERSION TARGET: 15-30% Ukrainian** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if immersion is outside this range. For A1 early modules, the learner cannot read Cyrillic — English must dominate. For A2+, Ukrainian must carry a significant share — add Ukrainian Reading Practice blocks, dialogues, and example paragraphs to reach the target. Too little Ukrainian fails audit just as much as too much.
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
module: a1-026
level: A1
sequence: 26
slug: free-time
version: '1.2'
title: Free Time
subtitle: Хобі, спорт, музика — what you do for fun
focus: communication
pedagogy: PPP
phase: A1.4 [Time and Nature]
word_target: 1200
objectives:
- Talk about hobbies, sports, and entertainment using learned verb patterns
- Invite someone to an activity using Ходімо! / Давай!
- Express frequency (часто, іноді, рідко, ніколи)
- Combine all A1.4 skills: time + day + weather + activities
dialogue_situations:
- setting: At a community center bulletin board — discussing activity sign-ups
  speakers:
  - Вітя
  - Оленка
  motivation: 'Frequency adverbs: Часто ходиш? Іноді. Ходімо разом!'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Weekend plans: — Що ти робиш у вихідні? — Зазвичай я гуляю і читаю.
    — Ходімо в кіно в суботу! — Добре! О котрій? — О п''ятій. — Чудово! Invitation
    pattern + time + day.'
  - 'Dialogue 2 — Talking about hobbies: — Ти любиш спорт? — Так, я граю у футбол.
    — Як часто? — Двічі на тиждень, у вівторок і четвер. — А ще? — Іноді слухаю музику
    і малюю. Frequency + hobby vocabulary.'
- section: Хобі і спорт (Hobbies and Sports)
  words: 300
  points:
  - 'Hobby vocabulary (extending M15 люблю + infinitive): грати у футбол / баскетбол
    / теніс (to play football/basketball/tennis) грати на гітарі / піаніно (to play
    guitar/piano — ''на'' + instrument as chunk) слухати музику (to listen to music)
    дивитися фільми / серіали (to watch movies/series) малювати (to draw), фотографувати
    (to take photos)'
  - 'Entertainment and culture: ходити в кіно (to go to the cinema) ходити в театр
    (to go to the theater) ходити на концерт (to go to a concert) ходити в музей (to
    go to a museum) Note: ходити + в/на is a chunk — the case grammar comes in A1.5.'
- section: Як часто? (How Often?)
  words: 300
  points:
  - 'Frequency adverbs: завжди (always), зазвичай (usually), часто (often), іноді
    / інколи (sometimes), рідко (rarely), ніколи (never). Word order: frequency adverb
    usually before the verb: Я часто гуляю. Я іноді читаю. Я ніколи не працюю у неділю.
    Ніколи requires не (double negation — review M19).'
  - 'Frequency expressions with numbers: раз на тиждень (once a week), двічі на тиждень
    (twice a week), тричі на тиждень (three times a week), кожен день (every day).
    Я граю у футбол двічі на тиждень. Я ходжу в кіно раз на місяць.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Free time communication: Hobbies: Я люблю + infinitive. Я граю у/на... Invitations:
    Ходімо! Давай! (Let''s go! Let''s!) Frequency: завжди, часто, іноді, рідко, ніколи.
    Self-check: Name 3 hobbies. How often do you do each? Invite a friend to do something
    this weekend.'
vocabulary_hints:
  required:
  - вихідні (weekend, pl)
  - спорт (sport, m)
  - футбол (football, m)
  - кіно (cinema, n — indeclinable)
  - часто (often)
  - іноді (sometimes)
  - рідко (rarely)
  - ходімо (let's go!)
  recommended:
  - завжди (always)
  - зазвичай (usually)
  - ніколи (never)
  - театр (theater, m)
  - концерт (concert, m)
  - музей (museum, m)
  - давай (let's — informal)
  - раз (once/time)
activity_hints:
- type: match-up
  focus: Match the verb to the logical noun (hobbies)
  pairs:
  - грати ↔ у футбол
  - грати ↔ на гітарі
  - слухати ↔ музику
  - дивитися ↔ фільми
  - ходити ↔ в кіно
  - ходити ↔ в театр
  - читати ↔ книгу
  - малювати ↔ вдома
- type: fill-in
  focus: Complete the invitations and frequency sentences
  items:
  - Я {ніколи не|завжди|часто} працюю у неділю.
  - Вона грає у теніс двічі {на тиждень|у тиждень|в тиждень}.
  - — {Ходімо|Давай|Ідемо} в кіно у суботу! — Добре!
  - Я люблю спорт, тому {часто|ніколи|рідко} граю у баскетбол.
  - Я не маю часу, тому {рідко|часто|завжди} читаю книги.
  - — Що ти робиш {у вихідні|вихідні|на вихідні}? — Відпочиваю.
- type: fill-in
  focus: Choose the correct preposition for the activity
  items:
  - Він грає {на|у|в} піаніно.
  - Ми граємо {у|на|в} футбол.
  - Я хочу ходити {на|в|у} концерт.
  - Вони ходять {в|на|у} театр раз на місяць.
connects_to:
- a1-027 (Checkpoint — Time and Nature)
prerequisites:
- a1-025 (My Day)
grammar:
- 'Frequency adverbs: завжди, часто, іноді, рідко, ніколи'
- Ходімо! / Давай! invitation patterns
- Грати у + sport, грати на + instrument (preposition chunks)
register: розмовний
references:
- title: ULP — various episodes on hobbies and sports
  notes: Conversational patterns for discussing free time.

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
- Confirmed: вихідні, спорт, футбол, кіно, часто, іноді, рідко, ходімо, завжди, зазвичай, ніколи, театр, концерт, музей, давай, раз, ходити, грати.
- Not found: None.

## Grammar Rules
- Euphony (у/в): Правопис §23 — "у" is used between consonants or at the start of a sentence before a consonant; "в" is used between vowels or after a vowel before most consonants (e.g., "у вихідні", "в кіно").
- Double Negation: Standard rule for "ніколи" requires "не" before the verb (e.g., "Я ніколи не працюю").
- Prepositions for Hobbies: "грати у" + Accusative for sports (футбол); "грати на" + Locative for instruments (гітарі). "ходити в" + Accusative for buildings (кіно, музей); "ходити на" + Accusative for events (концерт).
- Frequency: Adverbs usually precede the verb ("Я часто гуляю"). Frequency expressions use "на" + Accusative ("раз на тиждень").

## Calque Warnings
- приймати участь: Calque — Use "брати участь" (confirmed by Grade 10 Avramenko textbook).
- на вихідних: Acceptable in modern speech and some textbooks, but "у вихідні" is the preferred traditional form (Standard).
- раз в тиждень: Potential Russism — "раз на тиждень" is the standard Ukrainian construction (confirmed in Grade 2 and 8 textbooks).

## CEFR Check
- вихідні: A1 — OK
- зазвичай: A1 — OK
- футбол: A1 — OK
- кіно: A1 — OK
- театр: A1 — OK
- іноді: A1 — OK
- ходімо: A1 — OK (Functional language)
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
# Knowledge Packet: Free Time
**Module:** free-time | **Track:** A1

<wiki_context>
## Compiled Wiki Knowledge

The following articles from the project wiki provide compiled knowledge relevant to this module. Use them as authoritative context — they were compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).

### Вікі: pedagogy/a1/free-time.md

# Педагогіка A1: Free Time



## Методичний підхід (Methodological Approach)

The topic of "Free Time" (`Вільний час`) and "Hobbies" (`Хобі`) is a cornerstone of A1 communication, enabling learners to share personal information and structure social interactions. The Ukrainian pedagogical approach, as seen in sources for younger learners and adult L2 materials, is highly practical and communicative.

The core methodology is built around **dialogue and personalization** (Source 1, 10, 31). Learners are immediately encouraged to talk about their own lives (`Що ти робиш у вільний час?`) and make plans with others (`Ходімо в кіно!`). The process is not about memorizing lists of hobbies, but about using hobby-related vocabulary in functional contexts like making, accepting, and declining invitations.

Key principles include:
1.  **Start with Function:** The initial question is functional: "What do you like to do?" (`Що ви любите робити у вільний час?`) (Source 13). This immediately frames hobbies as a topic of conversation.
2.  **Verb-Centric Learning:** The topic is introduced through a core set of verbs: `любити`, `робити`, `грати`, `ходити`, `займатися`, `дивитися` (Source 13, 30). Nouns (the hobbies themselves) are then slotted into structures built around these verbs.
3.  **Contextual Scenarios:** Learning happens through realistic scenarios like planning a weekend (`плани на вихідні`) (Source 1, 3), discussing what's on at the cinema, or deciding between different activities like concerts, theatre, or sports (Source 1, 16).
4.  **Habitual vs. Specific Actions:** An early, implicit introduction to aspect and verbs of motion is done through the concept of hobbies. The verb `ходити` (to go regularly) is prioritized for talking about hobbies like `ходити в кіно` or `ходити в спортзал`, establishing the idea of a recurring activity (Source 13, 4). This contrasts with making a specific plan for the future, e.g., `поїдемо в Карпати` (Source 3).
5.  **Pattern Recognition over Rote Memorization:** Key grammatical structures, like `грати в + <sport>` versus `грати на + <instrument>`, are taught as fixed patterns with multiple examples, allowing learners to acquire them naturally (Source 13, 49).

## Послідовність введення (Introduction Sequence)

This topic should be layered progressively to avoid overwhelming the learner.

**Step 1: The Core Question and Verbs**
- Introduce the phrase `Вільний час` (Free time) and the question: `Що ти любиш робити у вільний час?` (What do you like to do in your free time?).
- Teach the essential verbs: `любити` (to love/like), `робити` (to do/make), `дивитися` (to watch), `читати` (to read), `слухати` (to listen) (Source 13, 32).

**Step 2: Basic, Cognate Hobby Nouns**
- Introduce a small set of high-frequency, often international nouns that require minimal cognitive load: `спорт`, `музика`, `кіно`, `футбол`, `книги`, `фільми` (Source 13, 40, 46).
- Practice the simple structure: `Я люблю + <іменник у Зн. в.>` (I like + Noun in Accusative), e.g., `Я люблю спорт. Я люблю музику.`

**Step 3: The "Go" Pattern with `ходити`**
- Introduce the verb `ходити` to describe habitual visits to places. This is a crucial A1 concept (Source 13).
- Teach the pattern `ходити в/на + <місце>`:
    - `ходити в кіно` (to go to the cinema)
    - `ходити в театр` (to go to the theatre)
    - `ходити в спортзал` (to go to the gym)
    - `ходити на концерти` (to go to concerts)
- The distinction between `в` and `на` is taught via chunks, not abstract rules at this stage.

**Step 4: The "Play" Pattern with `грати`**
- Explicitly teach the two main constructions with `грати` (to play), as this is a common point of confusion.
- **`грати в + <game/sport>`**: `грати в футбол`, `грати в теніс`, `грати в комп'ютерні ігри` (Source 13, 49).
- **`грати на + <musical instrument>`**: `грати на гітарі`, `грати на піаніно` (Source 10, 49).

**Step 5: The "Do/Practice" Pattern with `займатися`**
- Introduce the verb `займатися` for activities that are a practice or discipline.
- Teach the pattern `займатися + <іменник в Ор. в.>` (hobby in Instrumental case).
- Start with key examples: `займатися спортом`, `займатися йогою`, `займатися танцями` (Source 13, 29, 30). The Instrumental case ending `-ом`/`-ою` is presented as part of the chunk.

**Step 6: Making Plans and Suggestions**
- Introduce time expressions for planning: `на вихідних` (on the weekend), `у суботу` (on Saturday), `сьогодні ввечері` (this evening) (Source 1, 4, 31).
- Teach the imperative forms for making suggestions: `Ходімо!` (Let's go!), `Зустріньмося` (Let's meet!) (Source 17, 31, 35). This is the native Ukrainian form and should be prioritized.

## Типові помилки L2 (Common L2 Errors)

English-speaking learners often make predictable errors based on L1 transfer and false cognates.

| ❌ Помилково (Incorrect) | ✅ Правильно (Correct) | Чому (Why) |
| :--- | :--- | :--- |
| *Давайте підемо в кіно.* | **Ходімо в кіно!** | The `Давай(те)` construction for the imperative is a calque from Russian. While sometimes heard in colloquial speech due to historical influence, the pure Ukrainian forms are `ходімо`, `пішли`, `зробімо`, etc. (Source 20, 17). |
| *Я іду в спортзал кожну суботу.* | **Я ходжу в спортзал кожну суботу.** | English uses "I go" for both single trips and habitual actions. Ukrainian distinguishes between a single, unidirectional action (`іти`) and a repeated, habitual, or multi-directional action (`ходити`). For hobbies, `ходити` is almost always correct (Source 13). |
| *Я граю футбол.* / *Я граю в гітарі.* | **Я граю у футбол.** / **Я граю на гітарі.** | English "play" doesn't require a preposition for sports or instruments. Ukrainian strictly requires `в` for games/sports and `на` for musical instruments (Source 13, 49). |
| *Я займаюся спорт.* | **Я займаюся спортом.** | The verb `займатися` (to be engaged in) governs the instrumental case. Learners often forget the case ending and use the nominative, as if it were a direct object (Source 29, 30). |
| *Моє хобі є карате.* | **Карате — моє хобі.** / **Моє хобі — карате.** | While grammatically understandable, using `являється` (is) in this context is a common error, often a calque. Natural Ukrainian uses a dash (`тире`) or simple juxtaposition (Source 27). |
| *Я пропоную іти в кіно.* | **Я пропоную піти в кіно.** | Using an imperfective infinitive (`іти`) after `пропонувати` can sound unnatural. The perfective (`піти`) is more appropriate for a concrete suggestion for a single event (Source 11, 35, 37). |

## Деколонізаційні застереження (Decolonization Notes)

This section is mandatory. Teaching the topic of hobbies is an opportunity to establish pure, modern Ukrainian norms from the beginning, free from Russification.

1.  **Imperative Forms (`Наказовий спосіб`):** The most critical point is the formation of suggestions. **DO NOT** teach or accept the construction `Давайте + дієслово` (e.g., `Давайте підемо`). This is a direct calque of the Russian "Давайте пойдём". The authentic Ukrainian forms are the collective 1st person plural imperative (`Ходімо!`, `Подивімося!`, `Зустріньмося!`) or the simple 2nd person plural (`Ідіть!`, `Дивіться!`) (Source 17, 20). Phrases like `Ходімо в кіно!` should be taught as the primary and correct way to make a suggestion (Source 35).

2.  **Vocabulary - Calques:** Be vigilant against subtle Russian calques. For example, the phrase `приймати участь` (to take part) is a common Russianism (`принимать участие`). The correct Ukrainian is `брати участь` (Source 27). While not directly a "hobby" term, it arises in related contexts (e.g., "take part in a competition"). The style guide of Антоненко-Давидович is the authority here (Source `mcp_rag_search_style_guide`).

3.  **Phonetics and Internationalisms:** Many hobby and sport names are internationalisms (`футбол`, `теніс`, `хокей`, `баскетбол`). These words entered Ukrainian directly or via other European languages (Polish, German, French), not necessarily via Russian (Source 42). Pronounce them with Ukrainian phonetics (e.g., the clear `о` in `спорт`, not the `а`-like sound of a Russian unstressed `о`).

4.  **Cultural Context:** When giving examples, use Ukrainian cultural touchstones. Instead of generic examples, mention Ukrainian films, the `Оперний театр` in Kyiv or Lviv, Ukrainian classical music (`Наталка Полтавка`), or traditional activities (Source 1). This grounds the language in its own cultural reality.

## Словниковий мінімум (Vocabulary Boundaries)

This vocabulary is appropriate for the A1 level.

**Іменники (Nouns):**
-   **Activities:** хобі ★★★, спорт ★★★, музика ★★★, кіно ★★★, театр ★★, книги ★★, фільми ★★, футбол ★★★, теніс ★★, йога ★★, танці ★★, подорожі ★★
-   **Places:** парк ★★★, стадіон ★★, спортзал ★★, кінотеатр ★★★, театр ★★, музей ★★, виставка (exhibition) ★, басейн (pool) ★★
-   **Time:** вільний час ★★★, вихідні (weekend) ★★★, субота ★★★, неділя ★★★, вечір ★★★

**Дієслова (Verbs):**
-   любити (to like, love) ★★★
-   робити (to do, make) ★★★
-   ходити (to go, habitual) ★★★
-   грати (в/на) (to play) ★★★
-   займатися (to practice, do) ★★★
-   дивитися (to watch) ★★★
-   слухати (to listen) ★★★
-   читати (to read) ★★★
-   подорожувати (to travel) ★★
-   бігати (to run, jog) ★★
-   готувати (to cook) ★★
-   пропонувати (to suggest) ★★
-   зустрітися (to meet) ★★

**Прислівники та фрази (Adverbs & Phrases):**
-   у вільний час (in free time) ★★★
-   на вихідних (on the weekend) ★★★
-   ввечері (in the evening) ★★★
-   зазвичай (usually) ★★
-   часто (often) ★★
-   рідко (rarely) ★
-   разом (together) ★★★
-   Ходімо! (Let's go!) ★★★
-   Домовились! (Agreed!/Deal!) ★★ (Source 31)

## Приклади з підручників (Textbook Examples)

These are model exercises that the content writer should adapt.

**1. Verb-Activity Matching (Association)**
*Based on Source 38, Source 32*
The learner matches a verb to a noun phrase to form a complete activity. This reinforces verb-noun collocations and case usage.
> **З'єднай слово з малюнком і склади речення.** (Connect the word to the picture and make a sentence.)
> 1. `грати` -> (picture of a football) -> `Я люблю грати у футбол.`
> 2. `читати` -> (picture of a book) -> `Він любить читати книги.`
> 3. `дивитися` -> (picture of a TV) -> `Ми дивимося серіали.`
> 4. `грати` -> (picture of a guitar) -> `Вона грає на гітарі.`
> 5. `займатися` -> (picture of someone doing yoga) -> `Ти займаєшся йогою?`

**2. Dialogue Completion (Fill-in-the-blanks)**
*Based on Source 10, Source 35*
The learner completes a short dialogue about making plans, reinforcing key phrases.
> **Доповни діалог. Використай слова з довідки.** (Complete the dialogue. Use the words from the bank.)
>
> — Привіт, Оксано! **(1) __________** сьогодні ввечері?
> — Привіт! У мене немає планів. А що?
> — **(2) __________** в кіно! Є новий український фільм.
> — Чудова ідея! А о котрій?
> — Сеанс починається о сьомій. **(3) __________** біля кінотеатру о 18:45?
> — **(4) __________**! До зустрічі!
>
> *Довідка: Домовились, Що ти робиш, Ходімо, Зустріньмося*

**3. Situational Dialogue Creation**
*Based on Source 25, Source 31*
Provide a simple situation and ask learners to create a mini-dialogue. This encourages creative use of the language.
> **Розіграйте діалог.** (Role-play the dialogue.)
>
> **Ситуація:** Твій друг / твоя подруга пропонує піти на стадіон грати у футбол у суботу. Але ти не любиш футбол. Запропонуй щось інше (наприклад, піти в парк або подивитися фільм).
>
> *Приклад:*
> *А: Привіт! Ходімо в суботу на стадіон грати у футбол?*
> *Б: Привіт. Дякую, але я не дуже люблю футбол. Може, краще підемо в парк?*
> *А: Добре, ходімо в парк!*

**4. Personalization Questions**
*Based on Source 4, Source 40*
Ask a series of simple questions that prompt the learner to use the target vocabulary and structures to talk about themselves.
> **Дай відповідь на запитання.** (Answer the questions.)
> 1. Що ти любиш робити у вільний час? (Я люблю...)
> 2. Ти любиш спорт? Який? (Так, я люблю... / Ні, я не люблю...)
> 3. Ти часто ходиш у кіно? (Так, я ходжу часто. / Ні, я ходжу рідко.)
> 4. Ти граєш на музичному інструменті? (Так, я граю на... / Ні, я не граю.)
> 5. Що ти зазвичай робиш на вихідних? (Зазвичай я...)

## Пов'язані статті (Related Articles)

-   `pedagogy/a1/verbs-of-motion`
-   `pedagogy/a1/present-tense`
-   `pedagogy/a1/imperative-mood`
-   `pedagogy/a1/cases-accusative-instrumental`
-   `culture/leisure-in-ukraine`

---

### Вікі: pedagogy/a1/what-time.md

# Педагогіка A1: What Time



## Методичний підхід (Methodological Approach)

The native pedagogical approach to teaching time in Ukrainian is rooted in distinguishing between *identity* and *sequence*. This is immediately visible in the core questions taught to first and second graders (Source: `2-klas-ukrmova-vashulenko-2019-1_s0089`, `4-klas-ukrayinska-mova-ponomarova-2021-1_s0082`).

1.  **Question for Time Identity: `Котра година?`**
    *   This translates to "Which hour is it?" and conceptually treats the hours on a clock as items in an ordered set. The answer requires a **feminine ordinal numeral** (`перша`, `друга`, `третя`). This is the foundational concept (Source: `ext-ulp_youtube-236`, `ext-other_blogs-42`). Ukrainian pedagogy emphasizes that `година` is a feminine noun, so the ordinal number must agree with it (Source: `6-klas-ukrmova-golub-2023_s0167`).

2.  **Question for Events: `О котрій годині?`**
    *   This means "At what time?" and is used for scheduling. The answer requires the preposition **`о`** (or `об` before a vowel) followed by the **locative case** of the feminine ordinal numeral (`о першій`, `о другій`, `об одинадцятій`) (Source: `ext-ulp_youtube-236`, `4-klas-ukrayinska-mova-zaharijchuk-2021-1_s0084`).

3.  **Question for Quantity (Minutes): `Скільки хвилин?`**
    *   Minutes are treated as a simple quantity, not a sequence. Therefore, they use **cardinal numerals** (`п'ять`, `десять`, `двадцять`) (Source: `11-klas-ukrajinska-mova-avramenko-2019_s0057`, `6-klas-ukrmova-avramenko-2023_s0180`). This distinction between ordinal hours and cardinal minutes is a critical pedagogical point.

Ukrainian textbooks for young native speakers break down the hour into halves and quarters, introducing colloquial phrases early on. The models are presented visually with clocks and tables, showing multiple correct ways to express the same time (Source: `6-klas-ukrmova-litvinova-2023_s0252`, `2-klas-ukrmova-vashulenko-2019-1_s0089`). This multi-option approach (e.g., `шоста сорок`, `за двадцять сьома`, `двадцять до сьомої`) is standard and should be taught to L2 learners to equip them for real-world conversation (Source: `5-klas-ukrmova-litvinova-2022_s0197`).

## Послідовність введення (Introduction Sequence)

This sequence progresses from the simplest structures to more complex colloquial forms, mirroring the logic in Ukrainian school materials.

1.  **Step 1: The Core Question & Full Hours**
    *   **Concept:** Asking "What time is it?" and answering for times exactly on the hour.
    *   **Question:** `Котра година?` (Source: `4-klas-ukrayinska-mova-zaharijchuk-2021-1_s0083`)
    *   **Answer Structure:** Ordinal Numeral (Feminine, Nominative) + `година`.
    *   **Examples:** `Перша година.` (1:00), `Сьома година.` (7:00), `Дванадцята година.` (12:00) (Source: `ext-ulp_youtube-236`).
    *   **Why:** This establishes the core principle of using ordinal numbers for hours and ensures correct gender agreement from the start.

2.  **Step 2: Scheduling Events on the Hour**
    *   **Concept:** Stating when an event happens.
    *   **Question:** `О котрій годині?` (Source: `4-klas-ukrayinska-mova-ponomarova-2021-1_s0082`)
    *   **Answer Structure:** `О` + Ordinal Numeral (Feminine, Locative).
    *   **Examples:** `Урок починається о дев'ятій годині.` (9:00), `Зустрінемось о третій.` (3:00) (Source: `ext-ulp_youtube-236`).
    *   **Why:** Introduces the locative case in a high-frequency, practical context. The preposition `о` is fundamental for scheduling.

3.  **Step 3: The Half-Hour (`пів на ...`)**
    *   **Concept:** Expressing "__:30". This is the most common and idiomatic way.
    *   **Structure:** `пів на` + Ordinal Numeral (Feminine, **Accusative** case, which looks like Nominative for this form).
    *   **Examples:** `пів на сьому` (6:30, literally "half towards the seventh"), `пів на дванадцяту` (11:30) (Source: `6-klas-ukrmova-betsa-2023_s0164`, `6-klas-ukrmova-litvinova-2023_s0252`).
    *   **Why:** This is a fixed, highly frequent chunk. Teaching it as a single unit is more effective than deconstructing its grammar at A1. It logically follows full hours.

4.  **Step 4: Minutes Past the Hour (First Half)**
    *   **Concept:** Expressing minutes from 1 to 29.
    *   **Structure 1 (Official):** Hour (Ordinal) + `година` + Minutes (Cardinal) + `хвилин`.
        *   Example: `Сьома година п’ятнадцять хвилин.` (7:15) (Source: `4-klas-ukrayinska-mova-ponomarova-2021-1_s0083`).
    *   **Structure 2 (Colloquial `... по ...`):** Minutes (Cardinal) + `(хвилин) по` + Hour (Ordinal, **Locative**).
        *   Example: `П'ятнадцять (хвилин) по сьомій.` (7:15) (Source: `11-klas-ukrajinska-mova-glazova-2019_s0047`).
    *   **Structure 3 (Colloquial `... на ...`):** Minutes (Cardinal) + `(хвилин) на` + Next Hour (Ordinal, **Accusative**).
        *   Example: `П'ятнадцять (хвилин) на восьму.` (7:15, literally "15 minutes onto the eighth hour") (Source: `6-klas-ukrmova-betsa-2023_s0164`).
    *   **Why:** Introduce the official form first for clarity, then the common colloquial variants. The concept of "quarter" (`чверть`) can be introduced here as a substitute for `п'ятнадцять хвилин` (e.g., `чверть по сьомій`, `чверть на восьму`) (Source: `2-klas-ukrmova-vashulenko-2019-1_s0089`).

5.  **Step 5: Minutes To the Hour (Second Half)**
    *   **Concept:** Expressing minutes from 31 to 59.
    *   **Structure 1 (Official):** Hour (Ordinal) + `година` + Minutes (Cardinal) + `хвилин`.
        *   Example: `Сьома година сорок п’ять хвилин.` (7:45) (Source: `4-klas-ukrayinska-mova-ponomarova-2021-1_s0083`).
    *   **Structure 2 (Colloquial `за ...`):** `за` + Minutes Missing (Cardinal) + `(хвилин)` + Next Hour (Ordinal, **Nominative**).
        *   Example: `За п'ятнадцять восьма.` (7:45, literally "in 15 minutes, it's the eighth") (Source: `6-klas-ukrmova-betsa-2023_s0164`).
    *   **Structure 3 (Colloquial `... до ...`):** Minutes Missing (Cardinal) + `(хвилин) до` + Next Hour (Ordinal, **Genitive**).
        *   Example: `П'ятнадцять (хвилин) до восьмої.` (7:45) (Source: `6-klas-ukrmova-litvinova-2023_s0252`).
    *   **Why:** This is often the most confusing part for learners. Teaching `за ...` first is often easier as the hour remains in the nominative case. `... до ...` requires the genitive, adding complexity. Again, `чверть` can be used here (`за чверть восьма`) (Source: `12-klas-ukrmova-vashulenko-2019-1_s0089`).

## Типові помилки L2 (Common L2 Errors)

| ❌ Помилково (Incorrect) | ✅ Правильно (Correct) | Чому (Why) |
| :--- | :--- | :--- |
| `Зараз *сім година.` | `Зараз сьома година.` | Hours require **ordinal** (яка? котра?) not cardinal (скільки?) numbers. The hour is the "seventh" in sequence, not a quantity of "seven". (Source: `6-klas-ukrmova-zabolotnyi-2020_s0185`) |
| `*Без п'ятнадцяти вісім.` | `За п'ятнадцять восьма.` | The preposition `без` for telling time is a direct calque from Russian and is grammatically incorrect in standard Ukrainian. The correct native prepositions are `за` or `до`. (Source: `11-klas-ukrajinska-mova-avramenko-2019_s0060`, `5-klas-ukrmova-litvinova-2022_s0199`) |
| `*Пів восьмої.` | `Пів на восьму.` | This literally means "half of eight" and is incorrect for 6:30. The correct idiomatic phrase is `пів на восьму` ("half towards the eighth hour"). (Source: `6-klas-ukrmova-zabolotnyi-2020_s0185`) |
| `Концерт починається *в дві години.` | `Концерт починається о другій годині.` | To state when an event happens ("at" a time), Ukrainian uses the preposition `о` + the Locative case, never `в` or `у`. (Source: `6-klas-ukrmova-zabolotnyi-2020_s0185`) |
| `*П'ятнадцять хвилин восьмої.` | `П'ятнадцять хвилин на дев'яту.` or `П'ятнадцять хвилин по восьмій.` | This construction uses the genitive case incorrectly. To express "minutes past," use `по` + Locative (`по восьмій`). To express "minutes towards," use `на` + Accusative (`на дев'яту`). (Source: `11-klas-ukrajinska-mova-avramenko-2019_s0059`) |
| `Який зараз час?` | `Котра зараз година?` | While `час` means "time" in general, the specific question for clock time uses `година`. The question word `який` asks about quality ("what kind of"), while `котрий` asks about order/sequence ("which"). (Source: `ext-other_blogs-42`) |

## Деколонізаційні застереження (Decolonization Notes)

This topic is a critical area for decolonization in language teaching, as Russian-influenced forms are common among non-native speakers and even some legacy dialects.

1.  **Forbid the Preposition `Без`:** The construction `*без десяти сім` (for 6:50) is the single most common Russianism in this topic. It must be explicitly marked as incorrect and foreign to the Ukrainian grammatical system. The teacher must insist on the native forms: `за десять сьома` or `десять (хвилин) до сьомої` (Source: `11-klas-ukrajinska-mova-avramenko-2019_s0060`, `5-klas-ukrmova-litvinova-2022_s0199`). Do not present it as a "colloquial" or "acceptable" alternative; it is a grammatical error stemming from another language.

2.  **Reinforce `Котра година?`:** The standard question is `Котра година?`. While a learner might be understood asking `Скільки годин?` or `Який час?`, these are not the idiomatic, native questions taught in Ukrainian schools (Source: `4-klas-ukrayinska-mova-zaharijchuk-2021-1_s0083`). Correcting this from Day 1 establishes a native grammatical foundation and avoids habits from Russian (`сколько времени?`).

3.  **Teach Forms Holistically:** Ukrainian offers multiple correct ways to state the time (e.g., 8:15 can be `восьма п'ятнадцять`, `п'ятнадцять по восьмій`, or `п'ятнадцять на дев'яту`) (Source: `6-klas-ukrmova-betsa-2023_s0164`). Teach all common native forms. Do not simplify the system by teaching only the "official" format or a single colloquialism, as this impoverishes the learner's fluency and makes them unable to understand native speakers. Avoid presenting one form as "better" than another; they are simply different registers (official vs. conversational).

## Словниковий мінімум (Vocabulary Boundaries)

| Part of Speech | Word/Phrase | Frequency | Notes |
| :--- | :--- | :--- | :--- |
| **Іменники** | `година` | ★★★ | The core word for "hour" / "o'clock". |
| | `хвилина` | ★★★ | "minute" |
| | `чверть` | ★★ | "quarter" (of an hour). Very common. |
| | `ранок` / `вранці` | ★★★ | "morning" / "in the morning" |
| | `день` / `вдень` | ★★★ | "day" / "in the afternoon" |
| | `вечір` / `ввечері` | ★★★ | "evening" / "in the evening" |
| | `ніч` / `вночі` | ★★ | "night" / "at night" |
| | `північ` | ★★ | "midnight" |
| | `південь` | ★★ | "noon" |
| **Прислівники** | `зараз` | ★★★ | "now" |
| | `скоро` | ★★ | "soon" |
| | `пізно` | ★★ | "late" |
| | `рано` | ★★ | "early" |
| **Прийменники** | `о` / `об` | ★★★ | "at" (for time) |
| | `пів на` | ★★★ | For 30 minutes past the hour. |
| | `за` | ★★ | "until", "in" (e.g., `за 10 хв`) |
| | `до` | ★★ | "to", "until" |
| | `по` | ★★ | "past", "after" |
| | `на` | ★★ | "onto", "towards" (the next hour) |
| **Дієслова** | `починатися` | ★★★ | "to begin" |
| | `закінчуватися` | ★★★ | "to end" |
| | `зустрічатися` | ★★ | "to meet" |
| | `прокидатися` | ★★ | "to wake up" |

## Приклади з підручників (Textbook Examples)

1.  **Matching Clocks to Written Times (from Ponomarova, Grade 4)**
    *   **Task:** The textbook shows several clock faces. The student must match them to the correct written description.
    *   **Example options:**
        1.  `Сьома година п’ятнадцять хвилин, або чверть на восьму.`
        2.  `Сьома година сорок п’ять хвилин, або за чверть восьма.`
        3.  `Десята година.`
    *   **(Source: `4-klas-ukrayinska-mova-ponomarova-2021-1_s0083`)** This exercise reinforces the equivalence of official and colloquial forms.

2.  **Dialogue Practice (from Ponomarova, Grade 4)**
    *   **Task:** Students work in pairs to ask and answer questions about their daily routine.
    *   **Example questions:**
        *   `О котрій годині ти просинаєшся в будні?` (At what time do you wake up on weekdays?)
        *   `До котрої години ти спиш у вихідні?` (Until what time do you sleep on weekends?)
        *   `Котра зараз година?` (What time is it now?)
    *   **(Source: `4-klas-ukrayinska-mova-ponomarova-2021-1_s0083`)** This grounds the grammar in a practical, communicative context.

3.  **Table Completion: Digital to Words (from Betsa, Grade 6)**
    *   **Task:** Students fill in a table, converting digital time into written Ukrainian for both `Котра година?` and `О котрій годині?`.
    *   **Example Row:**
        | Години | Котра година? | О котрій годині? |
        | :--- | :--- | :--- |
        | 07:30 | `пів на восьму` | `о пів на восьму` |
        | 09:15 | `дев'ята п'ятнадцять` / `чверть по дев'ятій` | `о дев'ятій п'ятнадцять` / `о чверть по дев'ятій` |
    *   **(Source: `6-klas-ukrmova-betsa-2023_s0164`)** This exercise systematically drills the different forms and cases required.

4.  **Error Correction (from Litvinova, Grade 6)**
    *   **Task:** The student is given a list of time expressions, some of which are incorrect, and must write the correct versions.
    *   **Example incorrect forms to fix:**
        *   `*без шести вісім` -> `за шість восьма`
        *   `*половина одинадцяти` -> `пів на одинадцяту`
        *   `*біля сьомої` -> `близько сьомої` or `о сьомій`
    *   **(Source: `6-klas-ukrmova-litvinova-2023_s0253`)** This directly targets common mistakes and reinforces correct usage.

## Пов'язані статті (Related Articles)
- [[pedagogy/a1/ordinal-numbers]]
- [[pedagogy/a1/locative-case]]
- [[pedagogy/a1/genitive-case]]
- [[pedagogy/a1/daily-routine]]
</wiki_context>

## Plan References

- 

</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Хобі і спорт (Hobbies and Sports)` (~300 words)
- `## Як часто? (How Often?)` (~300 words)
- `## Підсумок — Summary` (~300 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 15-30% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — explain the grammar concept once, clearly.
- EXAMPLES: Ukrainian sentences in bulleted lists (each line: Ukrainian — English gloss). Max 2-4 per rule.
- TABLES: Paradigm tables, case endings, vocabulary groups — all cells Ukrainian.
- PATTERN BOXES: Show transformations: `книга → книгу` (nominative → accusative).
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences go in tables, bulleted lists, or pattern boxes.
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
  1. **At a community center bulletin board — discussing activity sign-ups**
     Speakers: Вітя, Оленка
     Why: Frequency adverbs: Часто ходиш? Іноді. Ходімо разом!

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

**Required:** вихідні (weekend, pl), спорт (sport, m), футбол (football, m), кіно (cinema, n — indeclinable), часто (often), іноді (sometimes), рідко (rarely), ходімо (let's go!)
**Recommended:** завжди (always), зазвичай (usually), ніколи (never), театр (theater, m), концерт (concert, m), музей (museum, m), давай (let's — informal), раз (once/time)

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
## Діалоги — Розкажи про плани (~350 words total)
- P1 (~50 words): [Introduction to discussing free time and making weekend plans. Emphasize that in Ukrainian, we often start by asking "Що ти робиш у вихідні?" (What are you doing this weekend?) to gauge availability before suggesting an activity.]
- P2 (~120 words): [Dialogue 1: Weekend plans at a community bulletin board. Вітя and Оленка discuss their Saturday routine. Focus on the invitation pattern "Ходімо в кіно!" (Let's go to the cinema!) and specifying the time "О п'ятій" (At five). Include phrases for agreement like "Чудово!" and "Добре!".]
- P3 (~60 words): [Linguistic note on invitations: Explaining the pure Ukrainian imperative "Ходімо!" (Let's go!) versus the informal "Давай!" (Let's). Explicitly mention that "Давай" is colloquial but "Ходімо" is the standard, grammatically correct form to prioritize.]
- P4 (~120 words): [Dialogue 2: Talking about hobbies and frequency. Вітя asks Оленка if she likes sports. Оленка explains she plays football "двічі на тиждень" (twice a week). They discuss other interests like listening to music "слухати музику" and drawing "малювати". Focus on the question "Як часто?" (How often?).]
- <!-- INJECT_ACTIVITY: fill-in-invitations --> [Fill-in-the-blanks, focus on completing invitations and frequency sentences using context clues from the dialogues, 6 items.]

## Хобі і спорт — Що ти любиш? (~340 words total)
- P1 (~80 words): [Introduction to hobby verbs using "любити" (to love/like) + infinitive. Explain that this is the simplest way to talk about interests. Provide common examples: читати книги (to read books), малювати вдома (to draw at home), фотографувати (to take photos), and готувати (to cook).]
- P2 (~80 words): [The "Play" pattern for sports: "грати у + sport". Explain that games and competitive sports require the preposition "у/в". List examples: грати у футбол (football), грати у баскетбол (basketball), грати у теніс (tennis), and грати у комп'ютерні ігри (computer games).]
- P3 (~80 words): [The "Play" pattern for music: "грати на + instrument". Contrast this with the sports pattern. Explain that musical instruments require "на" + the instrument name as a fixed chunk. Examples: грати на гітарі (guitar), грати на піаніно (piano), грати на скрипці (violin).]
- P4 (~100 words): [Going to places of entertainment using "ходити" (to go habitually). Explain the chunks "ходити в" vs "ходити на". Provide common pairs: ходити в кіно (to the cinema), ходити в театр (to the theater), ходити в музей (to a museum), versus ходити на концерт (to a concert) or ходити на футбол (to a football match).]
- <!-- INJECT_ACTIVITY: match-up-hobbies --> [Match-up, focus on connecting the correct verb (грати, слухати, дивитися, ходити) to the logical hobby noun or prepositional phrase, 8 pairs.]
- <!-- INJECT_ACTIVITY: preposition-check --> [Fill-in-the-blanks, focus on choosing the correct preposition (у, на, в) for sports, instruments, and entertainment venues, 4 items.]

## Як часто? — Прислівники частоти (~330 words total)
- P1 (~100 words): [Introduction to positive frequency adverbs: завжди (always), зазвичай (usually), часто (often), and іноді/інколи (sometimes). Explain the typical word order: the adverb usually sits right before the verb. Example: "Я часто гуляю в парку" or "Ми зазвичай читаємо ввечері".]
- P2 (~100 words): [Negative frequency adverbs: рідко (rarely) and ніколи (never). Explain the critical rule of double negation with "ніколи": it MUST be followed by "не" + the verb. Example: "Я ніколи не граю у футбол" (I never play football). Contrast "рідко" which does not require "не".]
- P3 (~100 words): [Expressions of frequency with numbers and "на тиждень". Explain how to say "once/twice/three times a week" using fixed phrases: раз на тиждень (once a week), двічі на тиждень (twice a week), тричі на тиждень (three times a week). Mention "кожен день" (every day) as a common alternative to "завжди".]
- P4 (~30 words): [Brief synthesis: Combining days of the week with frequency. Example: "У понеділок я завжди займаюся спортом".]
- <!-- INJECT_ACTIVITY: fill-in-frequency --> [Fill-in-the-blanks, focus on placing frequency adverbs in the correct position and ensuring double negation with "ніколи", 5 items.]

## Підсумок — Summary (~300 words total)
- P1 (~100 words): [Recap of the module's core communication goals. Summarize the difference between "грати у" (sports) and "грати на" (instruments), the use of "Ходімо!" for invitations, and the placement of frequency adverbs.]
- P2 (~150 words): [Self-check list for the learner. Output as a bulleted list of questions and model answers:
  * Q: Що ви любите робити у вільний час? A: Я люблю читати і ходити в кіно.
  * Q: Як часто ви граєте у футбол? A: Я граю у футбол двічі на тиждень.
  * Q: Ви граєте на піаніно? A: Ні, я ніколи не граю на піаніно, але я слухаю музику.
  * Q: Як запросити друга в театр? A: Ходімо в театр у суботу!]
- P3 (~50 words): [Closing encouragement. Remind the learner that they can now combine time, weather, and activities to describe their perfect weekend in Ukrainian. Transition to the upcoming Checkpoint.]

Grand total: ~1320 words
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
