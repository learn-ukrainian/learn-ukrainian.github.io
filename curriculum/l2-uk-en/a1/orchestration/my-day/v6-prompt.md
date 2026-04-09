

---

## Your Writing Identity

**You are: Lead Ukrainian Instructor.** Your persona is *The Patient Guide*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **25: My Day** (A1, A1.4 [Time and Nature]).

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
module: a1-025
level: A1
sequence: 25
slug: my-day
version: '1.2'
title: My Day
subtitle: Спочатку, потім, нарешті — telling a story about your day
focus: communication
pedagogy: PPP
phase: A1.4 [Time and Nature]
word_target: 1200
objectives:
- Describe a full day from morning to evening using verbs and time expressions
- Use sequence words to connect events (спочатку, потім, після того, нарешті)
- Combine time (M22), days (M23), weather (M24), and verbs (A1.3)
- Tell a simple coherent story about a typical or specific day
dialogue_situations:
- setting: Writing a blog post / diary entry about your day — reading it to a friend
  speakers:
  - Автор (narrator)
  - Друг (listener, reacting)
  motivation: 'Sequence words: спочатку, потім, нарешті in narration'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - Dialogue 1 — What did you do today? — Як пройшов твій день? — Добре! Вранці я
    працював. — А потім? — Потім обідав о першій. Після обіду гуляв. — А ввечері?
    — Ввечері дивився фільм і читав книгу. Past tense emerges naturally here — teach
    as vocabulary chunks, not grammar (past tense grammar = M48-49).
  - 'Dialogue 2 — Planning tomorrow: — Що ти будеш робити завтра? — Вранці буду працювати.
    — А після обіду? — Буду вивчати українську. А ввечері — гуляти. Future ''буду
    + infinitive'' as a chunk.'
- section: Мій типовий день (My Typical Day)
  words: 300
  points:
  - 'A model text using all A1.3-A1.4 skills: Я прокидаюся о сьомій. Спочатку вмиваюся
    і одягаюся. Потім снідаю. О дев''ятій я працюю. О першій обідаю. Після обіду працюю
    до п''ятої. Ввечері готую вечерю, читаю і дивлюся фільм. О одинадцятій лягаю спати.'
  - 'Parts of the day: вранці (in the morning), вдень (during the day), після обіду
    (in the afternoon — literally ''after lunch''), ввечері (in the evening), вночі
    (at night). These are adverbs — just add them to the beginning of a sentence.'
- section: Від ранку до вечора (From Morning to Evening)
  words: 300
  points:
  - 'Extended sequence words (building on M20): спочатку (first/at first), потім (then/next),
    після того/після цього (after that), нарешті (finally), також (also), а потім
    (and then). These connect sentences into a coherent narrative.'
  - 'Daily activity verbs (review + new): снідати (to have breakfast — review M20),
    обідати (to have lunch), вечеряти (to have dinner), відпочивати (to rest), лягати
    спати (to go to bed — chunk). All Group I (-ати), easy to conjugate with M16 patterns.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Telling your day: Time + sequence + activity = а coherent story. О сьомій прокидаюся.
    Спочатку снідаю. Потім працюю. Після обіду відпочиваю. Ввечері читаю. Нарешті
    лягаю спати. Self-check: Describe your typical Monday from morning to evening.
    Use at least 3 time expressions and 3 sequence words.'
vocabulary_hints:
  required:
  - вранці (in the morning)
  - вдень (during the day)
  - ввечері (in the evening)
  - обідати (to have lunch)
  - вечеряти (to have dinner)
  - відпочивати (to rest)
  - після (after)
  recommended:
  - прокидатися (to wake up — review from M20)
  - вмиватися (to wash — review from M20)
  - одягатися (to get dressed — review from M20)
  - вночі (at night)
  - після обіду (in the afternoon)
  - також (also)
  - лягати спати (to go to bed — chunk)
  - типовий (typical)
  - вільний (free)
activity_hints:
- type: match-up
  focus: Match the activity to the logical time of day
  pairs:
  - прокидаюся ↔ вранці
  - снідаю ↔ вранці
  - працюю ↔ вдень
  - обідаю ↔ вдень
  - вечеряю ↔ ввечері
  - дивлюся фільм ↔ ввечері
  - лягаю спати ↔ вночі
  - сплю ↔ вночі
- type: fill-in
  focus: Complete the logical sequence of the day
  items:
  - '{Спочатку|Потім|Нарешті} я прокидаюся і вмиваюся.'
  - Після того я {снідаю|вечеряю|лягаю спати}.
  - Вдень я {працюю|прокидаюся|снідаю} в офісі.
  - О першій годині я {обідаю|вечеряю|прокидаюся}.
  - '{Потім|Спочатку|Вранці} я читаю книгу або дивлюся фільм.'
  - '{Нарешті|Спочатку|Вдень} я лягаю спати о дванадцятій.'
- type: fill-in
  focus: Choose the correct part of the day
  items:
  - Я п'ю каву {вранці|вночі|ввечері}.
  - Ми вечеряємо {ввечері|вранці|вдень}.
  - Вона працює з дев'ятої до п'ятої {вдень|вночі|вранці}.
  - Вони гуляють у парку {після обіду|вночі|вранці}.
connects_to:
- a1-026 (Free Time)
prerequisites:
- a1-024 (Weather)
grammar:
- 'Sequence words: спочатку, потім, після того, нарешті'
- 'Parts of the day as adverbs: вранці, вдень, ввечері, вночі'
- 'Preview chunks only: працював/працювала, буду + infinitive (grammar in A1.8)'
register: розмовний
references:
- title: Вашуленко Grade 2, p.83
  notes: Planning your day activity — connecting activities to time.

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
- Confirmed: вранці, вдень, ввечері, вночі, обідати, вечеряти, відпочивати, після, прокидатися, вмиватися, одягатися, також, типовий, вільний.
- Not found: None (All words exist and are morphologically correct).

## Grammar Rules
- Adverbs of time (вранці, вдень, ввечері, вночі): Правопис § 30.1.а — "Разом пишуться прислівники, утворені сполученням прийменника з іменником: ввечері, вдень, взимку, вранці...".
- Sequence words: "Спочатку", "потім", "нарешті" — confirmed as standard adverbs (Правопис § 30.1.а).
- Verbs of daily routine: "Снідати", "обідати", "вечеряти" — Group I verbs (-ати), regular conjugation.

## Calque Warnings
- "після обіду": OK (natural) — literally "after lunch", used to denote the period after the midday meal. Often used interchangeably with "вдень" (in the day/afternoon).
- "лягати спати": OK (natural) — standard verbal chunk.
- "як пройшов твій день": OK (natural) — common greeting/question. "Як минув день?" is a slightly more formal/literary alternative.

## CEFR Check
- вранці: A1 — (Confirmed: Grade 1-3 textbook frequency)
- обідати: A1 — (Confirmed: Grade 5 vocab list)
- відпочивати: A1 — (Confirmed: Grade 5 exercise)
- типовий: A2+ — (Found in Grade 8+ literary analysis) — **Recommendation**: Keep for "типовий день" as it's a cognate (typical) and easy for English speakers, but prioritize "звичайний" for high-frequency daily use.
- вільний: A2 — (Confirmed: Grade 7 phraseology) — **Recommendation**: Acceptable for A1 in the context of "вільний час" (free time).
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
# Knowledge Packet: My Day
**Module:** my-day | **Track:** A1

<wiki_context>
## Compiled Wiki Knowledge

The following articles from the project wiki provide compiled knowledge relevant to this module. Use them as authoritative context — they were compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).

### Вікі: pedagogy/a1/my-day.md

# Педагогіка A1: My Day



## Методичний підхід (Methodological Approach)
The "My Day" (`Мій день`) topic is fundamental for A1 learners, as it introduces high-frequency vocabulary and grammatical structures essential for basic personal communication. The pedagogical approach, as gleaned from Ukrainian educational resources, should be grounded in communicative, context-driven learning. Instead of memorizing isolated words, learners should acquire language in functional chunks.

The core principle is to build from the general to the specific, and from simple states to complex actions.

1.  **Time Frames First:** Begin with the broad parts of the day: **`вранці`** (in the morning), **`вдень`** (in the afternoon), **`ввечері`** (in the evening), and **`вночі`** (at night). These adverbs provide the temporal skeleton for the day's narrative (Source: `ext-ulp_youtube-243`, `ext-ulp_youtube-253`). They are introduced as single, unchangeable units.
2.  **Anchor with Meals:** Meals are universal and serve as the next anchor. Introduce the nouns **`сніданок`, `обід`, `вечеря`** and immediately pair them with their corresponding verbs: **`снідати`, `обідати`, `вечеряти`** (Source: `ext-ulp_youtube-253`). This immediately teaches a pattern and avoids the common L2 error of using `мати` (to have).
3.  **Introduce Core Verbs:** Populate the time frames with essential, non-reflexive verbs like **`працювати`** (to work), **`читати`** (to read), and **`відпочивати`** (to rest). Simple sentences like "Вранці я працюю" are constructed.
4.  **Introduce Reflexive Verbs (`-ся`):** The daily routine is impossible to describe without reflexive verbs. Introduce verbs like **`прокидатися`** (to wake up), **`вмиватися`** (to wash one's face), and **`одягатися`** (to get dressed) as a distinct group (Source: `ext-article-0`). Explain their function: the action is directed back at the subject. The example of the frog creating a to-do list in a children's story (`Прокинутися`, `Поснідати`) provides a simple, clear model of listing these daily actions (Source: `4-klas-ukrmova-zaharijchuk_s0150`).
5.  **Expand with Time and Frequency:** Once the basic structure (`[Time Frame] + [Subject] + [Action]`) is solid, introduce basic time-telling (`о дев'ятій годині` - at 9 o'clock) (Source: `ext-ulp_youtube-235`) and adverbs of frequency (`завжди`, `зазвичай`, `іноді`, `ніколи`) to add detail and nuance (Source: `ext-ulp_youtube-253`).

This sequential, chunk-based approach helps learners build a narrative of their day, making the language immediately personal and useful. Every new piece of vocabulary or grammar should be slotted into the existing narrative framework.

## Послідовність введення (Introduction Sequence)

The content writer should introduce concepts in this specific order to build a logical and pedagogically sound foundation.

- **Step 1: The Four Parts of the Day.**
  - Introduce `ранок`, `день`, `вечір`, `ніч` as nouns.
  - Immediately introduce their adverbial forms: **`вранці`, `вдень`, `ввечері`, `вночі`**. Emphasize that these are single words meaning "in the morning," etc., and don't require a separate preposition. This is a high-frequency pattern seen across multiple sources (e.g., `ext-ulp_youtube-243`, `5-klas-ukrmova-uhor-2022-1_s0079`).
  - **Why this order:** These words create the basic canvas on which the rest of the daily routine is painted.

- **Step 2: Meal Vocabulary (Noun-Verb Pairs).**
  - Present meals as fundamental daily events.
  - Teach **`сніданок` / `снідати`**, **`обід` / `обідати`**, **`вечеря` / `вечеряти`**.
  - **Why this order:** This establishes a core pattern of Ukrainian verb formation and usage for common activities. It immediately gives the learner a functional way to talk about their day and preempts the error of using "to have" (Source: `ext-ulp_youtube-253`).

- **Step 3: Foundational Action Verbs (Present Tense).**
  - Introduce a small set of high-frequency, non-reflexive verbs.
  - Examples: `працювати`, `вчитись`, `читати`, `слухати музику`, `відпочивати`.
  - The writer should immediately show them in context: `Вдень я працюю. Ввечері я читаю.` (Source: `ext-ulp_youtube-243`).

- **Step 4: Key Reflexive Verbs (`-ся`).**
  - Explain that many "self-directed" actions use the `-ся` particle.
  - Introduce: **`прокидатися`** (to wake up), **`вмиватися`** (to wash face), **`одягатися`** (to get dressed), **`готуватися`** (to prepare oneself), **`лягати спати`** (to lie down to sleep). (Source: `ext-article-0`, `7-klas-ukrlit-mishhenko-2015_s0229`).
  - **Why this order:** These are essential for describing the beginning and end of the day. Introducing them as a group helps learners recognize the pattern.

- **Step 5: Days of the Week & "On [Day]".**
  - Introduce the seven days of the week (`понеділок`, `вівторок`, etc.).
  - Teach the construction for "on [day]": `у/в` + Accusative case. For example, **`у понеділок`**, **`у суботу`** (Source: `ext-ulp_youtube-243`). This expands the temporal context from a single day to a full week.

- **Step 6: Simple Time-Telling.**
  - Focus on the most common structure: **`о/об` + [ordinal number in Locative case] + `годині`**.
  - Example: `о дев'ятій годині` (at nine o'clock), `об одинадцятій годині` (at eleven o'clock) (Source: `ext-ulp_youtube-235`).
  - **Why this order:** This adds a layer of specificity. It should come after the broader time frames are mastered. For A1, stick to telling the hour.

## Типові помилки L2 (Common L2 Errors)
The writer must explicitly address these common pitfalls for English speakers.

| ❌ Помилково (Incorrect) | ✅ Правильно (Correct) | Чому (Why) |
| :--- | :--- | :--- |
| `Я маю сніданок.` | `Я снідаю.` | Direct translation of "I have breakfast." Ukrainian uses a specific verb for eating each meal (Source: `ext-ulp_youtube-253`). `Мати` implies possession, not consumption. |
| `Я прокидаю о сьомій.` | `Я прокида**юся** о сьомій.` | Forgetting the reflexive particle `-ся`. English uses "wake up," where "up" is a particle. In Ukrainian, the action is reflexive (`-ся` means "oneself"), so the particle is mandatory for this meaning (Source: `ext-article-0`). |
| `Я працюю **в** ранку.` | `Я працюю **вранці**.` | English uses "in the morning," leading learners to combine a preposition and noun. Ukrainian uses a single adverb (`вранці`) for this concept (Source: `ext-ulp_youtube-243`). |
| `Зустріч **в** дев'ятій годині.` | `Зустріч **о** дев'ятій годині.` | Incorrect preposition for time. English "at 9 o'clock" can be confusing. Ukrainian consistently uses `о` (or `об` before a vowel) for telling time on the hour (Source: `ext-ulp_youtube-235`). |
| `Я завжди роблю домашнє завдання ввечері.` | `Я завжди **виконую** домашнє завдання ввечері.` | Overuse of `робити` (to do/make). While not strictly wrong, `виконувати` (to complete/fulfill) is the more natural verb for tasks like homework. `Робити` is more for physical creation. |
| `Я сплю о 11 годині.` | `Я **лягаю спати** об 11 годині.` | `Спати` means "to be asleep." `Лягати спати` means "to go to bed" or "to lie down to sleep," which is the action of starting sleep. The lazy character Павлусь is described as going to sleep all day (`ляже`, `засне`) (Source: `7-klas-ukrlit-mishhenko-2015_s0229`). |

## Деколонізаційні застереження (Decolonization Notes)

This is a critical section. The A1 level is where a learner's foundational phonetic and lexical categories are formed. It is imperative to build a purely Ukrainian framework, free from Russian interference.

1.  **NO Russian Phonetic Analogies:** The writer must **never** explain a Ukrainian sound by comparing it to Russian. For example, do not say "Ukrainian `и` is like Russian `ы`" or "Ukrainian `і` is like Russian `и`." Ukrainian phonetics must be taught on their own terms, using native audio and articulatory descriptions. Ukrainian has its own distinct phonetic system, and drawing parallels to the colonizer's language reinforces a colonial mindset and creates phonetic confusion.
2.  **Vocabulary Purity:** Use authentically Ukrainian vocabulary. Avoid common Surzhyk (mixed Ukrainian-Russian language) or Russianisms. For example, for "next," use `наступний`, not `слідуючий` (a calque from Russian `следующий`). The podcast sources consistently use authentic Ukrainian (e.g., `ext-ulp_youtube-243`).
3.  **Grammar on Its Own Terms:** Present Ukrainian grammar as a complete, independent system. Do not frame it in terms of its differences from Russian. For example, when teaching the days of the week, simply teach the Ukrainian names (`понеділок`, `вівторок`...). Do not mention that some names differ from Russian.
4.  **Cultural Context:** The examples of a "typical day" should feel Ukrainian. Mentioning specific Ukrainian foods (even simple ones like `сирники` or `борщ`), activities, or holidays (`Великдень`, `Різдво`) grounds the language in its proper cultural context (Source: `ext-ulp_youtube-54`). This builds a direct connection to Ukraine, bypassing the historical imposition of Russian as the default Slavic culture.

## Словниковий мінімум (Vocabulary Boundaries)

This vocabulary is appropriate for an A1 learner discussing their day.

**Іменники (Nouns):**
- ★★★ `ранок`, `день`, `вечір`, `ніч` (parts of the day)
- ★★★ `сніданок`, `обід`, `вечеря` (meals)
- ★★★ `робота`, `школа`, `університет`, `дім` (locations)
- ★★★ `година`, `хвилина` (time)
- ★★ `тиждень`, `понеділок`, `вівторок`, `середа`, `четвер`, `п'ятниця`, `субота`, `неділя` (week)
- ★★ `чай`, `кава`, `вода` (drinks)
- ★ `душ`, `зуби`, `ліжко` (personal items)

**Дієслова (Verbs):**
- ★★★ `бути` (to be - past and future forms are key) (Source: `5-klas-ukrmova-uhor-2022-1_s0079`)
- ★★★ `прокидатися`, `вставати` (to wake up, to get up)
- ★★★ `снідати`, `обідати`, `вечеряти` (to eat meals)
- ★★★ `працювати`, `вчитися` (to work, to study)
- ★★★ `іти`, `їхати` (to go - basic forms)
- ★★★ `лягати спати` (to go to bed)
- ★★ `вмиватися`, `чистити зуби` (to wash face, to brush teeth)
- ★★ `одягатися` (to get dressed)
- ★★ `відпочивати` (to rest)
- ★★ `читати`, `писати`, `слухати` (to read, write, listen)
- ★ `приймати душ` (to take a shower)
- ★ `готувати (їжу)` (to prepare food)

**Прислівники (Adverbs):**
- ★★★ `вранці`, `вдень`, `ввечері`, `вночі` (in the morning/afternoon...)
- ★★★ `сьогодні`, `завтра`, `вчора` (today, tomorrow, yesterday)
- ★★★ `завжди`, `зазвичай`, `часто`, `іноді`, `рідко`, `ніколи` (always, usually, often, sometimes, rarely, never)
- ★★ `швидко`, `повільно` (quickly, slowly)
- ★★ `потім`, `спочатку` (then/later, at first)

## Приклади з підручників (Textbook Examples)

The writer should model activities on these proven formats from Ukrainian educational materials.

1.  **Simple Narrative with Comprehension Questions (Source: `ext-ulp_youtube-243`, `5-klas-ukrmova-uhor-2022-1_s0079`)**
    - Provide a short text about someone's day or week.
    - **Текст:** "З понеділка по четвер я вчусь і працюю. Вранці у мене уроки. Ввечері я викладаю українську мову. У п'ятницю я зазвичай працюю вдома. У суботу я записую подкаст, а ввечері розважаюся. У неділю я відпочиваю." (Adapted from `ext-ulp_youtube-243`).
    - **Запитання:**
        - Що ти робиш з понеділка по четвер?
        - Коли ти працюєш вдома?
        - Як ти розважаєшся в суботу?

2.  **Creating a To-Do List (Source: `4-klas-ukrmova-zaharijchuk_s0150`)**
    - This is an excellent exercise for practicing infinitives.
    - **Завдання (Task):** Напиши свій список справ на завтра. (Write your to-do list for tomorrow.)
    - **Приклад (Example):**
        - Прокинутися
        - Поснідати
        - Піти на роботу
        - Пообідати
        - Повечеряти
        - Лягти спати

3.  **Fill-in-the-Blanks with Time Adverbs (Source: `5-klas-ukrmova-zabolotnyi-2023_s0176`)**
    - This reinforces the connection between activities and times of day.
    - **Завдання (Task):** Доповніть речення словами `вранці`, `вдень`, `ввечері`, `вночі`. (Complete the sentences with...)
    - **Речення (Sentences):**
        - Я снідаю ________. (вранці)
        - Багато людей працюють ________. (вдень)
        - Моя сім'я вечеряє ________. (ввечері)
        - Більшість людей сплять ________. (вночі)
        - Чого ______ не зробиш, того ______ не здоженеш. (вранці, ввечері)

4.  **Correct the Sentence (Error Analysis)**
    - Present sentences with common L2 errors and have the learner correct them.
    - **Завдання (Task):** Знайдіть і виправте помилки. (Find and correct the mistakes.)
    - **Помилкові речення (Incorrect sentences):**
        - `Я маю каву в ранку.` -> `Я п'ю каву вранці.`
        - `Він прокидає о восьмій.` -> `Він прокидається о восьмій.`
        - `Ми будемо в кіно в суботу.` -> `Ми будемо в кіно в суботу.` (Accusative is correct here, `у суботу`)

## Пов'язані статті (Related Articles)
- `pedagogy/a1/telling-time`
- `pedagogy/a1/verbs-of-motion-basics`
- `pedagogy/a1/days-of-the-week`
- `grammar/cases/accusative-case`
- `grammar/verbs/reflexive-verbs`

---

### Вікі: pedagogy/a1/checkpoint-my-world.md

# Педагогіка A1: Checkpoint My World



## Методичний підхід (Methodological Approach)
The "My World" checkpoint is a crucial consolidation module for A1 learners. The primary pedagogical goal is to shift the learner from passive recognition and simple responses to active, structured production. This module assesses the learner's ability to synthesize vocabulary and grammar from previous lessons to talk about the most important topic: themselves.

The core methodology is **scaffolding from dialogue to monologue**. Ukrainian pedagogy for young learners heavily emphasizes this transition. We start with simple, structured question-and-answer pairs and gradually build towards a short, coherent narrative. As seen in `Source 15` (`6-klas-ukrmova-betsa-2023_s0018`), a key exercise is to "Трансформуйте діалог у монолог" (Transform the dialogue into a monologue). This provides a clear pathway for learners, reducing the cognitive load of spontaneous production.

The structure of the produced text is explicitly taught, following the model used in Ukrainian primary schools: **Зачин (Introduction), Основна частина (Main Part), and Кінцівка (Conclusion)** (Джерело: `2-klas-ukrmova-kravcova-2019-1_s0119`). This simple three-part structure gives learners a reliable template for organizing their thoughts, whether they are writing about their family, their day, or their hobbies. The goal is not literary prowess, but clear, logical communication.

Finally, this module is an opportunity for **active recall and application**. It is not about introducing a large volume of new material. Instead, it's about activating what has already been learned in a meaningful, personalized context. The focus is on communicative competence and building the learner's confidence in using Ukrainian to express personal information (Source 31: `ext-ulp_youtube-60`).

## Послідовність введення (Introduction Sequence)
The "My World" checkpoint should follow a logical progression from simple questions to a structured personal narrative. The sequence of tasks should be designed to build confidence at each stage.

1.  **Step 1: Foundational Q&A (Recycled Vocabulary).**
    Begin by activating core introductory phrases. The task is a simple dialogue where the learner answers basic questions about themselves. This reinforces patterns they should already know.
    *   *Prompt:* — Як тебе звуть? / — Мене звуть... (Джерело: `6-klas-ukrmova-betsa-2023_s0014`)
    *   *Prompt:* — Як твоє прізвище? / — Моє прізвище... (Джерело: `6-klas-ukrmova-betsa-2023_s0014`)
    *   *Prompt:* — Звідки ти? / — Я з [country/city].
    *   *Prompt:* — Де ти живеш? / — Я живу в [city].

2.  **Step 2: Expanding the Circle (Family & Professions).**
    Introduce questions about the people in the learner's "world." This stage focuses on using third-person pronouns (*він, вона*) and possessives (*його, її*), along with the instrumental case for professions.
    *   *Prompt:* — Розкажи... хто це на фото? (Джерело: `6-klas-ukrmova-betsa-2023_s0018`)
    *   *Model:* — Ось це моя мама. Її звуть... Вона працює лікаркою. (Джерело: `6-klas-ukrmova-betsa-2023_s0018`)
    *   This step requires learners to correctly apply noun gender for family members (мама, тато) and agree possessive pronouns accordingly (моя мама, мій тато).

3.  **Step 3: Transitioning from Dialogue to Monologue.**
    This is the most critical step. Guide the learner to connect their previous answers into a simple, continuous text. The prompt is direct: "Transform the dialogue into a monologue" (Джерело: `6-klas-ukrmova-betsa-2023_s0018`).
    *   *Model:* "Мене звати [Ім'я]. Я з [країна]. Я живу в [місто]. Це моя мама. Її звати... Вона працює вчителькою."

4.  **Step 4: Explicitly Structuring the Narrative.**
    Introduce the formal structure for any simple text, as taught in Ukrainian schools. This provides a mental checklist for the learner.
    *   **Зачин (Introduction):** State the topic. ("Я хочу розповісти про свою сім'ю.")
    *   **Основна частина (Main Part):** Provide the details. (Names, professions, etc.)
    *   **Кінцівка (Conclusion):** A simple closing sentence. ("Я люблю свою родину.")
    *   This framework helps organize the information from Step 3 into a more formal composition (Джерело: `2-klas-ukrmova-kravcova-2019-1_s0119`).

5.  **Step 5: Final Production (Written or Spoken).**
    The culminating task is a free, but guided, production. The prompt should be specific but allow for personalization.
    *   *Prompt Example:* "Напишіть розповідь «Моя сім’я»" (Джерело: `6-klas-ukrmova-betsa-2023_s0018`).
    *   *Alternative Prompts:* "Опиши свого друга / свою подругу", "Розкажи про свій дім".

## Типові помилки L2 (Common L2 Errors)
For English-speaking learners, the "My World" topic surfaces several predictable errors related to gender, case, and sentence structure.

| ❌ Помилково (Incorrect) | ✅ Правильно (Correct) | Чому (Why) |
| :--- | :--- | :--- |
| `Моя тато` і `мій мама`. | `Мій тато` і `моя мама`. | Learners incorrectly associate `моя` with "my" for a female (mom) and `мій` for a male (dad). The possessive pronoun must agree with the **grammatical gender of the noun** it modifies (`тато` is masculine, `мама` is feminine), not the gender of the person. (Джерело: `ext-other_blogs-46`) |
| Я працюю `вчитель`. | Я працюю `вчителем`. | When stating a profession with `працювати` (or being something), the noun for the profession must be in the **Instrumental case (Орудний відмінок)**. English uses the nominative ("I work as a teacher"). A Ukrainian school textbook explicitly models this: `Ким працює? (О. в.) ... учителем` (Джерело: `6-klas-ukrmova-betsa-2023_s0016`). |
| Моє ім'я є Анна. | Мене звати Анна. | This is a direct translation of the English structure "My name is...". While `Моє ім'я Анна` is grammatically possible, the most common and natural way to introduce oneself is the structure `Мене звати...` ("They call me..."). This is the first form taught in Ukrainian textbooks (Джерело: `6-klas-ukrmova-betsa-2023_s0014`). |
| `Привіт, Давид!` | `Привіт, Давиде!` | English does not have a vocative case for direct address. In Ukrainian, it is mandatory. Learners often forget to change the ending of a name when addressing someone directly. `Оксанко, ти знаєш...` is a clear example from a textbook (Джерело: `5-klas-ukrmova-uhor-2022-1_s0015`). |
| Це його сестра. Її звати Ірина. Це **його** брат. | Це його сестра. Її звати Ірина. Це **її** брат. | Learners confuse the meaning of possessive pronouns. When talking about Irina's brother, English would use "her brother". The learner mistakenly uses *його* ("his") again, thinking about the brother's gender, not the owner's (Irina's). This requires drilling the concepts of "his" (`його`) vs. "her" (`її`). |
| Моя сестра має 25 років. | Моїй сестрі 25 років. | Age is expressed using the dative case (`кому?`) + number + `років/рік/роки`, not the verb `мати` (to have) as in English and other European languages. This is a fundamental structural difference. <!-- VERIFY --> |

## Деколонізаційні застереження (Decolonization Notes)
Teaching Ukrainian must be done on its own terms, completely independent of Russian. The "My World" topic is an early opportunity to establish correct, decolonized linguistic habits.

1.  **Ukrainian is Not "Russian with different letters":** The writer must NEVER use Russian as a point of comparison (e.g., "This is like the Russian word..."). This creates a false equivalency and hinders the development of authentic Ukrainian phonetics and intuition. The Ukrainian language has its own distinct history, with some words being borrowed by other languages, including Russian and Polish (Джерело: `ext-istoria_movy-10`). The goal is to build a "Ukrainian mental map" from zero.

2.  **Pronunciation without Russian Interference:** Pronunciation of names and words must be based on Ukrainian phonology. For example, the name `Давид` is pronounced with a hard `д` at the end, not devoiced to `[Давіт]` as would happen in Russian. Emphasize listening to native Ukrainian audio, not relying on transliteration or comparison.

3.  **Vocabulary Purity:** Use exclusively Ukrainian vocabulary. Avoid common Russianisms that have crept into Surzhyk (a mixed Russo-Ukrainian vernacular). For instance, use `Гаразд` or `Добре` for "okay," not the Russian `ладно`. Use `дякую` for "thank you," not `спасибі` (which, while Ukrainian, is often overused due to Russian influence and `дякую` is more common in many regions). Source `ext-imtgsh-151` discusses how Russian was used as a tool of occupation, making linguistic purity a crucial act of decolonization.

4.  **Ukrainian Names:** Always use the standard Ukrainian forms of names (e.g., `Ганна`, `Олексій`, `Дмитро`, `Христина`) and not their Russified equivalents (`Анна`, `Алексей`, `Дмитрий`, `Кристина`). This reinforces Ukrainian identity and cultural norms from the very first lesson.

## Словниковий мінімум (Vocabulary Boundaries)
This checkpoint should only test high-frequency, personally relevant vocabulary that has been introduced in A1.

**Іменники (Nouns):**
*   ***Сім'я / Родина*** (family) ★★★
*   ***Мама (or мати), тато (or батько)*** (mom, dad) ★★★
*   ***Брат, сестра*** (brother, sister) ★★★
*   ***Дідусь, бабуся*** (grandfather, grandmother) ★★
*   ***Чоловік, дружина*** (husband, wife) ★★
*   ***Син, дочка (донька)*** (son, daughter) ★★
*   ***Друг, подруга*** (friend m/f) ★★★
*   ***Робота, школа, університет*** (work, school, university) ★★★
*   ***Дім (будинок), квартира*** (house, apartment) ★★
*   ***Місто, країна*** (city, country) ★★★
*   ***Ім'я, прізвище*** (first name, last name) ★★★

**Дієслова (Verbs):**
*   ***бути*** (to be) ★★★
*   ***звати*** (to be called) ★★★
*   ***жити*** (to live) ★★★
*   ***працювати*** (to work) ★★★
*   ***вчитись / навчатись*** (to study) ★★★
*   ***любити*** (to love, to like) ★★★
*   ***мати*** (to have) ★★★

**Займенники (Pronouns):**
*   ***Я, ти, він, вона, воно, ми, ви, вони*** (I, you, he, she, it, we, you, they) ★★★
*   ***Мій/моя/моє, твій/твоя/твоє, його, її, наш/наша/наше, ваш/ваша/ваше, їхній*** (my, your, his, her, our, your, their) ★★★

**Прислівники (Adverbs):**
*   ***тут, там*** (here, there) ★★
*   ***добре*** (well) ★★

## Приклади з підручників (Textbook Examples)
The module should use activity formats that are common in Ukrainian primary and middle school textbooks. These provide authentic, pedagogically sound models.

1.  **Structured Dialogue Completion (Source `6-klas-ukrmova-betsa-2023_s0014`)**
    *   **Task:** Complete and practice a basic introductory dialogue.
    *   **Format:**
        > — Як тебе звуть?
        > — Мене звуть … .
        > — Як твоє прізвище?
        > — Моє прізвище … .

2.  **Photo Description Role-Play (Source `6-klas-ukrmova-betsa-2023_s0018`)**
    *   **Task:** Use a family photo (real or provided) to ask and answer questions about family members.
    *   **Format:**
        > — Розкажи детальніше, хто це на фото.
        > — Ось це моя мама. Її звуть Еріка Іштванівна. Вона працює лікаркою в лікарні. Праворуч від мами моя сестра Іветта. Вона студентка...

3.  **Written Narrative Prompt (Source `6-klas-ukrmova-betsa-2023_s0018`)**
    *   **Task:** Write a short, structured story based on previously practiced dialogues.
    *   **Format:**
        > Напишіть розповідь «Моя сім’я». Використайте матеріали діалогів §4–5.
        > *(This directly links the written task to the preceding spoken practice).*

4.  **Text Scramble / Structure Identification (Source `2-klas-ukrmova-kravcova-2019-1_s0119`)**
    *   **Task:** Give learners the jumbled sentences of a short personal narrative. Their task is to reorder them into a logical Зачин (Introduction), Основна частина (Main Part), and Кінцівка (Conclusion).
    *   **Format:**
        > *[Кінцівка]* Він дуже веселий.
        > *[Основна частина]* Його звати Сергій. Він працює інженером.
        > *[Зачин]* Це мій друг.
        > **Your task:** Put the sentences in the correct order to make a story.

## Пов'язані статті (Related Articles)
*   `pedagogy/a1/personal-pronouns`
*   `pedagogy/a1/possessive-pronouns`
*   `pedagogy/a1/verb-conjugation-present`
*   `pedagogy/a1/instrumental-case`
*   `pedagogy/a1/noun-gender`
*   `pedagogy/a1/vocative-case`
</wiki_context>

## Plan References

- 

</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Мій типовий день (My Typical Day)` (~300 words)
- `## Від ранку до вечора (From Morning to Evening)` (~300 words)
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
  1. **Writing a blog post / diary entry about your day — reading it to a friend**
     Speakers: Автор (narrator), Друг (listener, reacting)
     Why: Sequence words: спочатку, потім, нарешті in narration

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

**Required:** вранці (in the morning), вдень (during the day), ввечері (in the evening), обідати (to have lunch), вечеряти (to have dinner), відпочивати (to rest), після (after)
**Recommended:** прокидатися (to wake up — review from M20), вмиватися (to wash — review from M20), одягатися (to get dressed — review from M20), вночі (at night), після обіду (in the afternoon), також (also), лягати спати (to go to bed — chunk), типовий (typical), вільний (free)

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
## Діалоги (~330 words total)
- P1 (~40 words): [Introduction to the narrative setting: a blogger recording a daily vlog or writing a diary entry, setting up the context for using time markers and sequence words in a natural, conversational flow.]
- P2 (~100 words): [Dialogue 1: "Як пройшов твій день?" (How was your day?). The narrator describes their day to a friend using past tense chunks like "працював" (worked), "обідав" (had lunch), and "читав" (read). The friend asks "А потім?" (And then?) to prompt sequence.]
- P3 (~60 words): [Linguistic analysis of Dialogue 1: Focusing on "вранці" (in the morning) vs "після обіду" (in the afternoon) as fixed adverbs and explaining that the past tense forms (-в) are introduced here as ready-made vocabulary chunks for storytelling.]
- P4 (~90 words): [Dialogue 2: "Що ти будеш робити завтра?" (What will you do tomorrow?). Planning a future schedule using the chunk "буду + infinitive" (буду працювати, буду вивчати). The dialogue emphasizes the contrast between "вдень" and "ввечері".]
- P5 (~40 words): [Linguistic analysis of Dialogue 2: Explaining the future intention chunk "буду + infinitive" as a simple way to talk about upcoming plans without full conjugation rules yet.]

## Мій типовий день (~340 words total)
- P1 (~80 words): [The Temporal Skeleton: Explaining the four parts of the day as adverbs: вранці, вдень, ввечері, вночі. Contrast with English: emphasize that NO preposition "в" is needed because the adverb already contains the "in the" meaning.]
- P2 (~90 words): [The Reflexive Routine: Introducing the concept of reflexive verbs (-ся) for self-directed actions. Teach "прокидатися" (to wake up), "вмиватися" (to wash), and "одягатися" (to get dressed) as a logical morning sequence.]
- P3 (~100 words): [Model Narrative: "Мій типовий понеділок." A 10-sentence paragraph combining time (о сьомій), reflexive verbs, and parts of the day. Examples: "Я прокидаюся о сьомій. Вранці я працюю. Вдень я обідаю."]
- P4 (~70 words): [Vocabulary deep-dive: "лягати спати" (to go to bed) vs "спати" (to sleep). Explain that "лягати спати" is the action of ending the day, while "вночі я сплю" describes the state.]
- <!-- INJECT_ACTIVITY: match-activity-time --> [match-up, focus: matching the activity to the logical time of day (прокидаюся-вранці, сплю-вночі), 8 items]

## Від ранку до вечора (~340 words total)
- P1 (~80 words): [The Connective Tissue: Introducing sequence words "спочатку" (first), "потім" (then/later), and "нарешті" (finally). Show how they turn a list of facts into a story: "Спочатку я снідаю. Потім я працюю."]
- P2 (~80 words): [Expanding the flow: Teaching "після того" (after that) and "також" (also) to avoid repetitive use of "потім". Example: "Я обідаю. Після того я також гуляю в парку."]
- P3 (~90 words): [The Meal Verbs: Emphasizing the noun-verb pairs сніданок/снідати, обід/обідати, вечеря/вечеряти. Explicitly warn against the English calque "мати сніданок" (I have breakfast); in Ukrainian, you just "breakfast".]
- P4 (~90 words): [Daily Activity Verbs: Reviewing Group I verbs (-ати) in the context of a day: "відпочивати" (to rest), "читати" (to read), "гуляти" (to walk). Show conjugation for "Я" and "Ти" to facilitate the dialogue situations.]
- <!-- INJECT_ACTIVITY: fill-in-sequence --> [fill-in, focus: choosing the correct sequence word (Спочатку... Потім... Нарешті) to complete a logical day, 6 items]
- <!-- INJECT_ACTIVITY: fill-in-parts-of-day --> [fill-in, focus: choosing between вранці, вдень, ввечері, вночі based on activities like "п'ю каву" or "сплю", 5 items]

## Підсумок (~310 words total)
- P1 (~120 words): [The Story Formula: Recap of how to build a coherent narrative by combining Time (о якій годині?) + Sequence (спочатку/потім) + Activity (verb). Model a "Super-Sentence": "Вранці о восьмій я спочатку снідаю, а потім працюю."]
- P2 (~190 words): [Self-check and Final Task. Provide a bulleted checklist for the learner:
    - Can I name 4 parts of the day as adverbs? (вранці, вдень, ввечері, вночі)
    - Can I use 3 words to order my actions? (спочатку, потім, нарешті)
    - Do I remember to use -ся for "прокидатися" and "вмиватися"?
    - Final Narrative Task: Write 6 sentences about your typical Monday using at least 3 sequence words and 3 specific times.]

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
