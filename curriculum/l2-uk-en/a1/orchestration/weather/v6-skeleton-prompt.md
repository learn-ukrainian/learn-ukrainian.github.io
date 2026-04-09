<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Skeleton Prompt — Module Structure Planning

You are planning the detailed paragraph-level structure of a Ukrainian language module. Do NOT write the full content — only plan the structure.

## Your task

Create a detailed paragraph-level skeleton for module **24: Weather** (A1, A1.4 [Time and Nature]).

**Word target: 1200 words** of prose. Your skeleton must budget every word.

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

## Wiki Teaching Brief

Skim this for the key concepts, paradigms, and examples you must cover. Reference specific examples from the article that you plan to use in each paragraph.

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

## Output format

Output a single `<skeleton>` block. For each section from the plan's `content_outline`, list every paragraph and exercise with its word budget and content focus.

Be SPECIFIC about what each paragraph covers — not "explain grammar" but "explain accusative case endings for feminine nouns (-у/-ю), with 3 examples: книгу, каву, землю."

```
<skeleton>
## Section Title (~XXX words total)
- P1 (~XX words): [specific content — what concept, what examples, what comparison]
- P2 (~XX words): [specific content]
- <!-- INJECT_ACTIVITY: activity-id --> [type from activity_hints, focus, number of items]
- P3 (~XX words): [specific content]
...

## Section Title (~XXX words total)
- P1 (~XX words): [specific content]
- <!-- INJECT_ACTIVITY: activity-id --> [type, focus]
...

## Підсумок (~150 words)
- P1 (~150 words): [Follow the plan's points for this section EXACTLY. If the plan says "Self-check questions", output a bulleted Q&A list — NOT prose. If the plan says "recap", write a brief recap.]

Grand total: ~1200 words
</skeleton>
```

## Rules

1. **Every paragraph has ONE clear purpose.** If you can't describe it in one sentence, split it.
2. **Word budgets must sum to 1200+.** Aim for ~10% overshoot (1320 words) — writers tend to undershoot.
3. **Section budgets must match the plan's `content_outline` word allocations** (±10%).
4. **Place exercise injection markers in the correct section.** Each activity hint in the plan may have a `section:` field that tells you which section it belongs in. Place `<!-- INJECT_ACTIVITY: descriptive-id -->` AFTER the teaching content of that section, never before. Use a descriptive kebab-case id (e.g., `fill-in-genitive`, `quiz-aspect-choice`). If no `section:` is specified, place the marker after the most relevant teaching point. **CRITICAL: An exercise must ONLY test concepts already taught above it. Never test a concept from a later section. Every plan `activity_hints` entry MUST have a corresponding `<!-- INJECT_ACTIVITY: id -->` marker in the skeleton.**
5. **Name specific Ukrainian examples** you plan to use in each paragraph. This prevents vague skeletons that produce vague content.
6. **Dialogues count as paragraphs.** Budget 80-120 words per multi-turn dialogue.
7. **No meta-commentary.** Output only the `<skeleton>` block, nothing else.
