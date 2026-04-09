

---

## Your Writing Identity

**You are: Lead Ukrainian Instructor.** Your persona is *The Patient Guide*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **24: Weather** (A1, A1.4 [Time and Nature]).

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
module: a1-024
level: A1
sequence: 24
slug: weather
version: '1.2'
title: Weather
subtitle: Сьогодні холодно — talking about the weather
focus: vocabulary
pedagogy: PPP
phase: A1.4 [Time and Nature]
word_target: 1200
objectives:
- Describe weather using impersonal constructions (cold, warm, hot)
- Use "іде дощ / іде сніг" pattern for precipitation
- Combine weather with seasons and months
- Ask and answer "What's the weather like?"
dialogue_situations:
- setting: Two friends deciding whether to go hiking — checking weather together
  speakers:
  - Іванко
  - Галя
  motivation: 'Impersonal: Сьогодні холодно, Завтра буде тепло, Іде дощ'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Looking out the window (ULP Ep16 pattern): — Яка сьогодні погода?
    — Сьогодні холодно і йде дощ. — А завтра? — Завтра буде тепло і сонячно. — Добре!
    Тоді завтра гуляємо! Weather + future plans (буде as chunk).'
  - 'Dialogue 2 — Seasons conversation: — Яка пора року тобі подобається? — Мені подобається
    літо. — Чому? — Тому що влітку тепло і сонячно. А тобі? — Мені подобається осінь.
    Восени красиво. Weather + seasons + opinion verbs from M15.'
- section: Яка погода? (What's the Weather?)
  words: 300
  points:
  - 'Impersonal weather expressions (no subject — the weather just IS): Сьогодні холодно.
    (It''s cold today.) Сьогодні тепло. (It''s warm.) Сьогодні спекотно. (It''s hot.)
    Сьогодні прохолодно. (It''s cool.) Заболотний Grade 8 p.126: безособові речення
    передають явища природи. These are adverbs — no subject needed, just the state.'
  - 'Precipitation patterns: Іде дощ. (It''s raining — literally ''rain goes''.) Іде
    сніг. (It''s snowing — ''snow goes''.) Дме вітер. (The wind is blowing.) Світить
    сонце. (The sun is shining.) Хмарно / ясно. (Cloudy / clear.) Note: іде дощ (not
    ''дощить'') is the natural conversational form.'
- section: Погода і пори року (Weather and Seasons)
  words: 300
  points:
  - 'Connecting weather to seasons (M23): Взимку холодно. Іде сніг. (In winter it''s
    cold. It snows.) Навесні тепло. Все зелене. (In spring it''s warm. Everything''s
    green.) Влітку спекотно. Світить сонце. (In summer it''s hot. The sun shines.)
    Восени прохолодно. Іде дощ. (In autumn it''s cool. It rains.)'
  - 'Temperature vocabulary: градуси (degrees) — Сьогодні двадцять градусів. (20 degrees.)
    плюс / мінус — Мінус десять. (Minus 10.) тепло / холодно as nouns: На вулиці тепло.
    (It''s warm outside.) Time words: сьогодні (today), завтра (tomorrow), вчора (yesterday).'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Weather toolkit: Question: Яка сьогодні погода? Temperature: холодно, тепло,
    спекотно, прохолодно. Precipitation: іде дощ, іде сніг, дме вітер, світить сонце.
    Sky: хмарно, ясно, сонячно. Seasons: взимку холодно, влітку спекотно. Self-check:
    Describe today''s weather. What''s winter like where you live?'
vocabulary_hints:
  required:
  - погода (weather, f)
  - холодно (cold — adverb)
  - тепло (warm — adverb)
  - дощ (rain, m)
  - сніг (snow, m)
  - сонце (sun, n)
  - сьогодні (today)
  - завтра (tomorrow)
  recommended:
  - спекотно (hot)
  - прохолодно (cool)
  - вітер (wind, m)
  - хмарно (cloudy)
  - ясно (clear)
  - сонячно (sunny)
  - градус (degree, m)
  - вчора (yesterday)
activity_hints:
- type: match-up
  focus: Match the weather phrase to its logical context or season
  pairs:
  - іде дощ ↔ холодно і мокро
  - іде сніг ↔ зима
  - світить сонце ↔ сонячно
  - дме вітер ↔ прохолодно
  - мінус десять ↔ холодно
  - плюс тридцять ↔ спекотно
  - плюс двадцять ↔ тепло
  - хмарно ↔ сонце не світить
- type: fill-in
  focus: Choose the logical weather for the season
  items:
  - Взимку часто {іде сніг|іде дощ|світить сонце}.
  - Влітку дуже {спекотно|холодно|хмарно}.
  - Восени часто {іде дощ|іде сніг|сонячно}.
  - Навесні {тепло|холодно|спекотно} і красиво.
  - Сьогодні мінус п'ять, дуже {холодно|тепло|спекотно}.
  - Сьогодні плюс двадцять п'ять, {тепло|прохолодно|холодно}.
- type: fill-in
  focus: Complete the dialogue about the weather
  items:
  - — Яка сьогодні {погода|сонце|дощ}? — Сьогодні тепло.
  - — Завтра {буде|є|був} сонячно. — Добре, гуляємо!
  - — Яка пора року тобі {подобається|любить|робить}? — Літо.
  - — Чому ти любиш літо? — Тому що влітку {сонячно|холодно|хмарно}.
connects_to:
- a1-025 (My Day)
prerequisites:
- a1-023 (Days and Months)
grammar:
- 'Impersonal constructions: cold/warm/hot (no subject)'
- Іде дощ / іде сніг pattern (literally 'goes rain/snow')
- 'Time adverbs: сьогодні, завтра, вчора'
register: розмовний
references:
- title: Заболотний Grade 8, p.126
  notes: 'Безособові речення: явища природи, стан людини.'
- title: ULP Season 1, Episode 16
  url: https://www.ukrainianlessons.com/episode16/
  notes: Weather vocabulary and expressions.

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
- Confirmed: погода, холодно, тепло, дощ, сніг, сонце, сьогодні, завтра, спекотно, прохолодно, вітер, хмарно, ясно, сонячно, градус, вчора.
- Not found: [none]

## Grammar Rules
- Impersonal weather expressions (adverbs): Правопис §[syntax] — Standard Ukrainian syntax uses adverbs (холодно, тепло) in impersonal sentences without a subject to describe the state of the environment (e.g., "Сьогодні холодно").
- Precipitation patterns: Textbook Grade 5 (Avramenko) and Grade 7 confirm the naturalness of "Іде дощ" (literally 'rain goes') and "Іде сніг". While "дощить" is also valid, "іде дощ" is the preferred conversational form for A1.
- Future tense chunk: Use of "буде" + weather adverb (e.g., "завтра буде сонячно") is the standard construction for future state.

## Calque Warnings
- іде дощ: OK — standard Ukrainian expression (confirmed via Grade 5/7 textbooks).
- на вулиці: OK — used in Grade 2 textbooks for "outside," though "надворі" is a more formal/literary alternative. Both are natural.
- яка сьогодні погода: OK — standard question for weather.

## CEFR Check
- погода: A1 — Fundamental vocabulary (appears in Grade 2 textbooks).
- дощ: A1 — Fundamental vocabulary.
- холодно: A1 — Fundamental adverb.
- сонце: A1 — Fundamental noun.
- вітер: A1 — Fundamental noun.
- [Note]: All plan vocabulary items are present in primary school textbooks (Grade 2), confirming A1 appropriateness.
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
# Knowledge Packet: Weather
**Module:** weather | **Track:** A1

<wiki_context>
## Compiled Wiki Knowledge

The following articles from the project wiki provide compiled knowledge relevant to this module. Use them as authoritative context — they were compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).

### Вікі: pedagogy/a1/weather.md

# Педагогіка A1: Weather



## Методичний підхід (Methodological Approach)

The native approach to teaching weather in early grades is conversational and built around simple, observable states. It starts with impersonal constructions, which are foundational for describing weather and feelings in Ukrainian. The core question `Яка погода?` (What's the weather like?) is introduced early and serves as the primary conversational trigger (Source 2, 9).

The methodology progresses from general states to specific phenomena:
1.  **Core States using Adverbs:** Instruction begins with basic adverbs like `тепло` (warm) and `холодно` (cold) (Source 2, 42). This establishes the impersonal sentence structure that is central to weather descriptions (e.g., `Сьогодні холодно` - Today it is cold).
2.  **Contrasting Examples:** Teachers often use contrasting locations to reinforce vocabulary, for instance, comparing the weather in Kyiv (`холодно`, `іде дощ`) with Los Angeles (`тепло`, `сонячно`) (Source 2). This makes the lesson more dynamic and memorable.
3.  **Personification of Precipitation:** A key pedagogical technique is to describe rain and snow using the verb `іти` (to go/walk). Phrases like `іде дощ` (the rain is "going") and `іде сніг` (the snow is "going") are taught as fixed expressions (Source 2). This animistic view is memorable for learners and reflects a natural feature of the language.
4.  **Connecting to Feelings:** The impersonal structure is extended to personal feelings related to weather, such as `Мені холодно` (I am cold / To me it is cold) or `Я змерзла` (I got cold/froze) (Source 1, 12). This links external conditions to internal states, a common pattern in Ukrainian.
5.  **Integration with Seasons:** Weather is not taught in isolation but is immediately tied to the four seasons (`пори року`). Textbooks for young Ukrainians consistently link weather conditions (`сніжно`, `спекотно`) to the relevant season (`зима`, `літо`) (Source 3, 29, 36).

## Послідовність введення (Introduction Sequence)

**Step 1: Core States (Impersonal Adverbs)**
- Introduce the fundamental question: `Яка сьогодні погода?` (What is the weather like today?).
- Teach the four core adverbs: `тепло` (warm), `холодно` (cold), `сонячно` (sunny), `хмарно` (cloudy).
- Practice forming simple, one-word answers: `- Яка погода? - Тепло.`
- Add qualifiers like `дуже` (very): `дуже тепло`, `дуже холодно` (Source 2).

**Step 2: Precipitation as an Action**
- Introduce the nouns `дощ` (rain) and `сніг` (snow).
- Teach the fixed expressions `іде дощ` and `іде сніг`. Emphasize that this is the natural way to say "it is raining/snowing" (Source 2).
- Contrast this with the static states from Step 1.

**Step 3: Temperature**
- Introduce the question: `Яка температура?`
- Teach the structure: `плюс/мінус + [number] + градусів/градуси`.
- Example: `Сьогодні плюс двадцять (+20)` (Source 2), `Температура плюс три (+3)` (Source 2).

**Step 4: Adjectives for General Description**
- Introduce adjectives to describe the weather in general terms: `погода` (weather) is feminine, so adjectives take feminine endings.
- Key pairs: `хороша погода` (good weather) vs. `погана погода` (bad weather) (Source 2, 18).
- More descriptive adjectives: `чудова погода` (wonderful weather), `мінлива погода` (changeable weather) (Source 2, 4, 13).

**Step 5: Connecting Weather to Personal Experience**
- Teach how to express being affected by the weather using the dative case or past tense verbs.
- `Мені холодно.` (I am cold.) (Source 1)
- `Мені жарко.` (I am hot.) <!-- VERIFY -->
- `Я змерз / Я змерзла.` (I'm freezing / I've gotten cold.) (Source 12)

**Step 6: Seasons and Months**
- Introduce the four seasons (`весна`, `літо`, `осінь`, `зима`) and link typical weather to each. For example: `Взимку холодно і сніжно, а влітку досить спекотно.` (In winter it's cold and snowy, and in summer it's quite hot.) (Source 3).
- Introduce key month names tied to weather phenomena, like `лютий` (February), named for its "fierce" (`лютий`) cold (Source 5, 7).

## Типові помилки L2 (Common L2 Errors)

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| `Це є тепло.` | `Тепло.` / `Сьогодні тепло.` | English speakers often try to replicate "It is..." using a subject (`це`) and verb (`є`). Ukrainian weather descriptions are typically impersonal sentences where the adverb (`тепло`) functions as the predicate. The verb `є` is almost never used in this context (Source 2, 33). |
| `Воно дощить.` | `Іде дощ.` | This is a direct translation of the English "It is raining." Ukrainian personifies precipitation with the verb `іти` (to go/walk). The structure `іде дощ` is a fixed, idiomatic expression that must be memorized (Source 2). |
| `Сьогодні є сонячний.` | `Сьогодні сонячно.` | Learners confuse the adjective `сонячний` (sunny, as in "a sunny day" - `сонячний день`) with the adverb `сонячно` (it is sunny). For describing the state of the weather, the adverb form ending in `-о` is required (Source 2). |
| `Я є холодний.` | `Мені холодно.` | This error comes from translating "I am cold." In Ukrainian, to express feeling cold, one uses the dative construction `мені` (to me) + the adverb `холодно`. The adjective `холодний` describes an object (e.g., `холодний чай` - cold tea), not a person's feeling. |
| `Дуже тепла погода.` | `Дуже тепло.` or `Погода дуже тепла.` | While `дуже тепла погода` is grammatically possible as "very warm weather", the common way to state the condition is with the simple adverbial `Дуже тепло` (It is very warm). The former describes the noun `погода`, while the latter describes the state of the environment (Source 2). |

## Деколонізаційні застереження (Decolonization Notes)

**This section is mandatory for the writer.** Teaching Ukrainian weather provides a key opportunity to build a Ukraine-centric linguistic foundation, free from Russian influence.

1.  **No Russian Phonetic Analogies:** The writer must **never** explain Ukrainian sounds by comparing them to Russian. For example, do not describe the sound in `дощ` or `холодно` as "like the Russian 'o' under stress." Ukrainian phonetics must be taught on their own terms, using native audio examples and articulatory descriptions.
2.  **Emphasize Slavic Month Names:** Ukrainian, like Polish and Belarusian, preserves many Slavic month names that reflect natural phenomena. The writer should highlight this. For example, `лютий` is the "fierce" month, not simply *fevral'* (Source 5, 7). `Квітень` is the "blossoming" month (Source 21). This contrasts with the Russian system based on Latin names and reinforces a distinct Ukrainian worldview tied to nature.
3.  **`Іде дощ` is not "Quirky":** Present the `іде дощ / іде сніг` construction not as a strange idiom, but as a core, natural feature of the Ukrainian language's metaphorical system (Source 2). It's a window into how the language conceives of the world. Avoid framing it as "weird" or "funny" compared to an English or Russian norm.
4.  **Folk Proverbs (Прикмети) are Cultural Data:** When introducing weather-related folk sayings, present them as part of a unique Ukrainian tradition of observing nature, not as generic "Slavic" proverbs. For example, `Яка погода на Покрову, такою буде і зима` links weather prediction to a specific Ukrainian religious and cultural holiday (Source 10). These are data points about a specific culture's relationship with its environment.

## Словниковий мінімум (Vocabulary Boundaries)

### Іменники (Nouns)
- `погода` ★★★ (weather)
- `дощ` ★★★ (rain)
- `сніг` ★★★ (snow)
- `сонце` ★★★ (sun)
- `вітер` ★★ (wind)
- `температура` ★★ (temperature)
- `небо` ★★ (sky)
- `хмара` ★ (cloud)
- `зима`, `весна`, `літо`, `осінь` ★★★ (winter, spring, summer, autumn)

### Прислівники (Adverbs)
- `холодно` ★★★ (cold)
- `тепло` ★★★ (warm)
- `сонячно` ★★★ (sunny)
- `хмарно` ★★ (cloudy)
- `спекотно` / `жарко` ★★ (hot) (Source 3, 6)
- `морозно` ★★ (frosty) (Source 7)
- `вітряно` ★★ (windy) (Source 7)
- `сьогодні`, `завтра`, `вчора` ★★★ (today, tomorrow, yesterday) (Source 18, 42)

### Дієслова (Verbs)
- `іде (дощ, сніг)` ★★★ (it's raining/snowing)
- `світить (сонце)` ★★ (the sun is shining)
- `прогнозувати` ★ (to forecast) (Source 12)

### Прикметники (Adjectives)
- `гарний` / `хороший` ★★★ (good)
- `поганий` ★★★ (bad)
- `теплий` ★★ (warm, for objects/days)
- `холодний` ★★ (cold, for objects/days)
- `чудовий` ★ (wonderful)

## Приклади з підручників (Textbook Examples)

**1. Conversational Q&A Practice (Based on Source 2)**
- **Format:** Question and Answer Drill.
- **Prompt:** "Answer the questions about the weather in different cities. Use the words in parentheses."
  - `Яка погода в Києві? (холодно, +3)` -> `У Києві холодно, температура плюс три.`
  - `Яка погода в Лос-Анджелесі? (тепло, сонячно)` -> `В Лос-Анджелесі тепло і сонячно.`
  - `Яка погода у вашому місті?` -> (Learner provides their own answer).

**2. Dialogue Completion (Based on Source 12, 17)**
- **Format:** Fill-in-the-blanks dialogue.
- **Prompt:** "Complete the dialogue between two friends talking about the weather."
  - **Анна:** `Яка __________ сьогодні?`
  - **Марк:** `Сьогодні __________ і йде __________.`
  - **Анна:** `А яка __________?`
  - **Марк:** `Тільки __________ п'ять градусів.`
  - **Анна:** `Ой, мені дуже __________!`
  - *Word bank: `погода`, `холодно`, `дощ`, `температура`, `плюс`, `холодно`.*

**3. Folk Sayings Interpretation (Based on Source 10, 38)**
- **Format:** Reading and discussion.
- **Prompt:** "Read the folk sayings about weather. How did ancient Ukrainians predict the weather? Do you have similar sayings in your country?"
  - `Якщо на Покрову вітер, весна буде вітряна.` (If it's windy on Pokrova holiday, the spring will be windy.) (Source 10)
  - `Ластівки літають низько — завтра буде дощ.` (Swallows are flying low — tomorrow it will rain.) (Source 38)
  - `Яка погода на Покрову, такою буде і зима.` (Whatever the weather is on Pokrova, so will be the winter.) (Source 10)

**4. Adjective to Adverb Transformation (Based on Source 2, 44)**
- **Format:** Transformation drill.
- **Prompt:** "Change the adjective describing an object into an adverb describing the weather."
  - `Це теплий чай.` -> `Сьогодні тепло.`
  - `Це холодний день.` -> `Надворі холодно.`
  - `Це сонячний ранок.` -> `Зранку сонячно.`
  - `Це хмарне небо.` -> `Сьогодні хмарно.`

## Пов'язані статті (Related Articles)
- `pedagogy/a1/seasons-and-months`
- `pedagogy/a1/impersonal-sentences`
- `pedagogy/a1/adverbs-of-state`
- `pedagogy/a1/dative-case`

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
- `## Яка погода? (What's the Weather?)` (~300 words)
- `## Погода і пори року (Weather and Seasons)` (~300 words)
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
  1. **Two friends deciding whether to go hiking — checking weather together**
     Speakers: Іванко, Галя
     Why: Impersonal: Сьогодні холодно, Завтра буде тепло, Іде дощ

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

**Required:** погода (weather, f), холодно (cold — adverb), тепло (warm — adverb), дощ (rain, m), сніг (snow, m), сонце (sun, n), сьогодні (today), завтра (tomorrow)
**Recommended:** спекотно (hot), прохолодно (cool), вітер (wind, m), хмарно (cloudy), ясно (clear), сонячно (sunny), градус (degree, m), вчора (yesterday)

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
## Діалоги (Dialogues) (~300 words total)
- P1 (~60 words): [Setting the scene: Intro to Ivan and Halya looking out the window. Mentioning the context of morning routine and deciding on outdoor plans.]
- D1 (~120 words): [Dialogue 1: Focus on immediate weather and future prediction. Phrases: "Яка сьогодні погода?", "Сьогодні холодно і йде дощ", "Завтра буде тепло і сонячно". Using "буде" as a chunk for future weather.]
- D2 (~120 words): [Dialogue 2: Conversation about personal preferences for seasons from M23. Phrases: "Яка пора року тобі подобається?", "Мені подобається літо", "Влітку тепло і сонячно", "Восени красиво і прохолодно".]

## Яка погода? (What's the Weather?) (~300 words total)
- P1 (~100 words): [Explanation of impersonal weather expressions. Ukrainian describes the state without a subject or the verb "to be". Contrast "It is cold" with "Холодно". Specifically warning against the L2 error "Це є тепло" or "Воно є сонячно".]
- P2 (~100 words): [Core weather adverbs: тепло, холодно, спекотно, прохолодно. Explaining how to use "дуже" (very) to modify these states. Examples: "Сьогодні дуже спекотно", "Вчора було прохолодно".]
- P3 (~100 words): [Precipitation as an action using the verb "іти" (to go). Teaching the fixed paradigms "іде дощ" (it's raining) and "іде сніг" (it's snowing). Mentioning "світить сонце" (the sun is shining) and "дме вітер" (the wind is blowing).]
- <!-- INJECT_ACTIVITY: fill-in-weather-dialogue --> [fill-in, focus: Complete the dialogue about the weather using vocabulary like погода, буде, подобається, 4 items]

## Погода і пори року (Weather and Seasons) (~330 words total)
- P1 (~110 words): [Connecting weather states to seasonal adverbs from M23: взимку, навесні, влітку, восени. Examples: "Взимку холодно і часто йде сніг", "Влітку зазвичай спекотно і сонячно".]
- P2 (~110 words): [Sky conditions: хмарно (cloudy), ясно (clear), сонячно (sunny). Explaining the logical link between sky state and precipitation: "Коли хмарно, сонце не світить і може йти дощ".]
- P3 (~110 words): [Talking about temperature using numbers. Introduction of "градуси" (degrees), "плюс" (plus), and "мінус" (minus). Question: "Яка температура?". Answer: "Сьогодні плюс двадцять градусів" or "Зараз мінус десять".]
- <!-- INJECT_ACTIVITY: match-up-weather-season --> [match-up, focus: Match weather phrases to logical context/season, 8 pairs]
- <!-- INJECT_ACTIVITY: fill-in-season-weather --> [fill-in, focus: Choose the logical weather adverb or precipitation for the season, 6 items]

## Підсумок — Summary (~300 words total)
- P1 (~150 words): [Comprehensive recap of the Weather Toolkit. Listing the key question "Яка сьогодні погода?", temperature adverbs (холодно/тепло/спекотно), precipitation patterns (іде дощ/сніг), and sky states (хмарно/ясно).]
- P2 (~150 words): [Self-check Q&A. Provide the following bulleted list for the learner to practice answering:
    - Яка сьогодні погода у твоєму місті?
    - Яка температура сьогодні: плюс чи мінус?
    - Яка твоя улюблена пора року? Чому?
    - Що йде взимку: дощ чи сніг?]

Grand total: ~1230 words
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
