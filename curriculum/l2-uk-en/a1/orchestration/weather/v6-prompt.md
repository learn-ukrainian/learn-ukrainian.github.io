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

## 8 Hard Rules

1. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
2. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
3. **NO "In this lesson we will..."** — never use formulaic openers. Start with a dialogue, a question, or a situation.
4. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
5. **Write exercises directly** — write complete exercises in the DSL format below. Include real questions, real answers, and real distractors. A downstream tool converts them to interactive React components.
6. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
7. **Hit the word target** — you MUST write 1200–1800 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
8. **NO archaic, obsolete, or rare words** — use only modern standard Ukrainian. Do not use words marked as archaic (застаріле) or dialectal in dictionaries. Example: use «кін» not «кон», use «пом'якшені» not «м'якшені». When in doubt, choose the common modern form. Your pre-training contains Russian-influenced archaic forms — verify unfamiliar words.

**Note:** Do NOT add stress marks (´) to any Ukrainian word — a deterministic tool handles this after you write.

## Exercises — Write Them Directly

After each key teaching point, write an exercise directly in DSL format.

**CRITICAL: Each exercise MUST match a specific `activity_hints` entry from the Plan.**
- Use the EXACT `type` specified (quiz, fill-in, match-up, group-sort, true-false)
- Follow the `focus` description EXACTLY — if the plan says "Answer: У тебе є...? Так / Ні", your quiz must test exactly that pattern
- Match the `items` count specified
- Do NOT invent different exercises — the plan's activity_hints are the specification

Write REAL content: real questions, real answers, real distractors. Every exercise must be solvable by a learner who read the preceding prose.

### DSL Format

Use these exact formats. Each block starts with `:::type` and ends with `:::`.

**Quiz** (multiple choice):
```
:::quiz
title: "Звук чи літера?"
---
- q: "Що ми чуємо і вимовляємо?"
  o: ["звуки", "літери", "слова"]
  a: 0
- q: "Що ми бачимо і пишемо?"
  o: ["літери", "звуки", "речення"]
  a: 0
:::
```

**Fill-in** (complete the sentence):
```
:::fill-in
title: "Complete the greeting"
---
- sentence: "Привіт! Як ___?"
  answer: "справи"
- sentence: "Дякую, ___."
  answer: "добре"
:::
```

**Match-up** (connect pairs):
```
:::match-up
title: "Match false friend letters to their real sounds"
---
- left: "В"
  right: "sounds like [в], not [b]"
- left: "Н"
  right: "sounds like [н], not [h]"
:::
```

**Group-sort** (classify into categories):
```
:::group-sort
title: "Classify letters"
---
groups:
  - name: "Голосні"
    items: ["А", "О", "У", "І"]
  - name: "Приголосні"
    items: ["М", "К", "Б", "Ш"]
:::
```

**True-false**:
```
:::true-false
title: "True or false?"
---
- statement: "В українській мові 33 літери."
  answer: true
- statement: "Голосних звуків більше, ніж приголосних."
  answer: false
:::
```

Spread exercises evenly throughout the module. Never cluster them.

### Approved Exercise Patterns

Use these Ukrainian textbook-inspired patterns (Заболотний, Авраменко) instead of generic "quiz" types:

- **Знайди помилку (Find the error):** Give 3 correct sentences and 1 with an error. Learner identifies the mistake. Tests: grammar rules, calques, Russianisms.
- **Обери правильне слово (Choose the right word):** Fill in the blank from 2-3 options (synonyms, paronyms, or confusable words). Tests: vocabulary nuance, register.
- **Утвори пару (Match-up):** Match words to antonyms, translations, or grammatical pairs (e.g., masculine → feminine). Tests: vocabulary, morphology.
- **Розподіли (Group-sort):** Sort items into 2-3 categories (e.g., голосні vs приголосні, hard vs soft consonants). Tests: foundational phonetics, grammar classification.
- **Склади речення (Build a sentence):** Give scrambled words, learner arranges into correct order. Tests: word order, sentence structure.
- **Знайди місце (Find the right place):** Give 4 sentences with blanks and 4 words — each word fits exactly one sentence. Tests: contextual meaning, collocations.

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
  - іде дощ ↔ потрібна парасолька (umbrella)
  - іде сніг ↔ зима
  - світить сонце ↔ сонячно
  - дме вітер ↔ дерева шумлять (trees rustle)
  - мінус десять ↔ холодно
  - плюс тридцять ↔ спекотно
  - плюс двадцять ↔ тепло
  - сіре небо ↔ хмарно
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

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Weather
**Module:** weather | **Phase:** A1.4 [Time and Nature]
**Textbook grades searched:** 3, 4, 5

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 34
>  
> Обговоріть! Для чого існують прислів’я і приказки?
> * * *
> Що тобі не мило, другові не зич.
> Друга шукай, а знайдеш — тримай.
> З добрим дружись, а лихого стережись.
> Нових друзів май, а старих не забувай.
> Прислів’я — це короткий влучний образний 
> вислів, який має повчальний зміст.
> Прислів’я вчить, як на світі жить.
> * * *
> Щоб рибу їсти, треба у воду лізти.
> Хто хоче багато мати, тому треба мало спати.
> Треба нахилитися, щоб із криниці води напитися.
> Любиш кататися — люби й на гору підійматися.
> * *

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 127
> 303.		Прочитай жарт.
> Восени і взимку, навесні і влітку дуже поважають чере-
> вики щітку (І. Січовик).
> 	 Спиши речення, підкресли прислівники. Які з них протилежні за 
> значенням?
> 	 Підкресли головні й другорядні члени речення. Визнач, на яке 
> питання вони відповідають, якою частиною мови виражені.
> 304.		Прочитай групи прислівників.
> 1. Багато, дорого, рано, коротше, менше, весело, да-
> леко, темно, глибше.
> 2. Мілкіше, мало, довше, дешево, пізно, більше, світло, 
> сумно, близько.
> 	 Добери до присл

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 251
> Кажу** літу:
> — Ти вже врізало день, щодня доточуєш ночі, підганяєш 
> усіх достигати, а саме — холоднішати. Навіщо? Я ще нічого 
> літнього не встигла.
> А воно мені каже:
> — Якби я чекало, допоки люди перероблять свою роботу, 
> то так ніколи б і не настало. Або ніколи не скінчилося.
> — Другий варіант мені подобається більше.
> — Ну навряд чи тобі хотілось би жити у світі вічнозелених 
> вишень і ніколи недостиглих кавунів. Усьому свій час. Мені 
> час минати потроху.
> — Але ж…
> — Що але ж? Просто не відклад

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 133
> — Дякуємо, літо!
> Ішло тепле літечко стежками-доріжками. Дрібненько 
> ступало маленькими ніжками. Там, де зупинялося, квіти 
> розцвітали, де землі вклонялося, — пташечки співали. Гомо-
> ніли ріки, літо зустрічали, озерця й ставочки воду зігрівали. 
> — Дякуємо, літо! Дякуємо красно! Ти таке барвисте, 
> сонячне, прекрасне. Ми не будем спати, бо довкола влітку 
> чудеса дарує і веселка, й квітка. І тепленький дощик, що гри-
> бочки сіє, і маленька жабка, що про мушку мріє. Для усіх ти, 
> літо, запасло гос

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> 123
> 293.		Прочитай слова.
> (що?) Добро, (який?) добрий, (… ?) добре;
> (що?) низина, (який?) низький, (… ?) унизу;
> (що?) ранок, (який?) ранній, (… ?) уранці;
> (що?) далечінь, (який?) далекий, (… ?) здалеку.
> 	 Визнач частини мови, які ти знаєш. Постав питання до підкрес-
> лених слів.
> 	 Спиши підкреслені прислівники, укажи в дужках питання.
> 294.		Прочитай сполучення дієслів із прислівниками.
> Світить (як?) яскраво, … ; світить (де?) високо, …. ; хо-
> дить (як?) тихо, … ; співає (як?) весело, … ; прокинув

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 29
> 58.	 Доберіть антоніми до обох слів у словосполученнях і запишіть 
> утворені словосполучення. 
> ЗРАЗОК. Веселий ранок – сумний вечір. 
> Теплий день, минуле літо, добрий друг, гарний початок, 
> перша перемога, корисний холод.
> 59.	 І. Прочитайте текст, визначте його тип мовлення. Що нового ви 
> дізна­лися? 
> ПРО КОРИСТЬ ХОЛОДУ
> Холод – це не завжди погано. Він має і корисні власти-
> вості. Саме морозна, холодна погода змушує організм по-
> силювати свій імунітет. Холод пришвидшує циркулювання 
> крові. Так

## Яка погода? (What's the Weather?)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 103
> ЗЕЛЕНИМ ПРОМЕНЕМ ВЕСНА ПОВІДМИКАЛА ВОДИ
> ВЕСНА ДНЕМ КРАСНА
> ЗЕЛЕНИЙ ПРОМІНЬ
> Зеленим променем весна 
> повідмикала води,
> а доторкнулась до зерна — 
> зазеленіли сходи.
> Відкрила очі сон-трава 
> і глянула із гаю:
> Послухай відеозвернення Анатолія Качана.
> Які вірші продекламував Анатолій Качан? 
> Яку книгу поет рекомендує прочитати?
> Анатолій Качан
> џ
> Розкажи, якою ти уявляєш весну. Які образні висловлю-
> вання, порівняння вживає поет?
> ВЕСНЯНИЙ ДОЩИК
> А дощик йшов і тішився весною,
> то накрапав, то воду лив с

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> Прислівники, близькі й протилежні 
> за значенням
> 3 9 1 . Прочитайте загадки. Відгадайте їх.
> 1. Удень у небі гуляє, а ввечері на землю сідає. 2. Улітку 
> одягається, а взимку одежі цурається. 3. Хто це літає, що 
> зверху чорне суконце, а знизу біле полотенце?
> •  Спишіть загадки. Підкресліть прислівники з протилежним 
> значенням (антоніми). Підкресліть дієслова, з якими зв’я­
> зані прислівники. Поставте питання від дієслів до прислів­
> ників (усно).
> 392. Прочитайте текст.
> Рішуче й упевнено крокує весна-

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 27
>  § 10. Лексичне  значення  слова
> 1. Прочитайте діалог між братом і молодшою сестрою та виконайте зав­
> дання. 
> — На вулиці посіріло, зірвався вітер, мабуть, зараз піде дощ!
> — Піде?! А хіба дощ може ходити? 
> А. Через яке слово сестра не зрозуміла брата?
> Б. Яка причина непорозуміння?
> Лексичне значення — це те, що означає слово. Наприклад, лексичне 
> значення слова дощ — різновид опадів, що випадають із хмар у вигляді 
> краплин води. 
> Лексичне значення слів можна з’ясувати за тлумачним словником.

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 14
> Листячко дубове,
> листячко кленове
> жовкне і спадає
> тихо із гілок.
> Вітер позіхає,
> в купу їх згортає 
> попід білу хату
> та на моріжок.
> Айстри похилились,
> ніби потомились —
> сонечка немає,
> спатоньки пора!
> А красольки в’ялі
> до землі припали.
> Наче під листочком
> вітер догоря.
> РОЗМАЇТТЯМ КОЛЬОРОВИМ 
> ПРИКРАШАЄ ОСІНЬ КРАЙ
> Катерина Перелісна
> ОСІНЬ
> џ
> Відшукай слова, які мають ніжно-пестливе значення. 
> Чому, на твою думку, поетеса їх використала? Як ти розу-
> мієш вислови вітер позіхає, під листочком вітер до

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> 153
> 2. Спишіть словосполучення. Порівняйте прислівники і при-
> кметники за значенням та за будовою. Зіставте питання, 
> на які вони відповідають. З якою частиною мови переваж-
> но зв’язуються в реченні прислівники? А прикметники? 
> Усміхається (як?) востаннє;  Променям (яким?) останнім;
> жебонить (як?) тихо;    
>    струмок (який?) тих ий;
> чорніють (як?) таємничо.    лози (які?) таємничі.
> 3. Від поданих прикметників утворіть і запишіть прислів-
> ники. Прокоментуйте, як ви це зробили.
> Щедрий, голосний,

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 29
> 58.	 Доберіть антоніми до обох слів у словосполученнях і запишіть 
> утворені словосполучення. 
> ЗРАЗОК. Веселий ранок – сумний вечір. 
> Теплий день, минуле літо, добрий друг, гарний початок, 
> перша перемога, корисний холод.
> 59.	 І. Прочитайте текст, визначте його тип мовлення. Що нового ви 
> дізна­лися? 
> ПРО КОРИСТЬ ХОЛОДУ
> Холод – це не завжди погано. Він має і корисні власти-
> вості. Саме морозна, холодна погода змушує організм по-
> силювати свій імунітет. Холод пришвидшує циркулювання 
> крові. Так

## Погода і пори року (Weather and Seasons)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 68
> Зимові дні — це дивне свято. Урочисто стоять дерева, 
> прикрашені білим інеєм. Іскриться від сонця снігова 
> доріжка. Зачаровує зимова тиша. Як загадково стало 
> довкола!
> А буває, що налетить хурделиця, закрутить і почне 
> вигравати не чуту раніше мелодію. Їй допомагає вітерець-
> вітрище.
> Читаючи твори цього розділу, звертай увагу, як 
> письменники і письменниці змальовують зиму, які слова 
> вживають для цього, помічай і запам’ятовуй нові слова 
> та образні вислови, записуй свої враження від художніх

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> Сади цвітуть коли? Навесні,
> Улітку трав поля шовкові,
> А восени врожай збирають,
> Узимку снігу всі чекають.
> Прислівників багато має мова 

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Яка погода? (What's the Weather?)` (~300 words)
- `## Погода і пори року (Weather and Seasons)` (~300 words)
- `## Підсумок — Summary` (~300 words)
- `## Підсумок` (~150 words)

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
- Use callout boxes (:::tip, :::caution, :::note) sparingly — max 3 per module
- **Dialogue formatting** — use blockquote `>` with speaker names in bold. Each turn on its own line. At A1 level, add English translation in italics after each line so learners understand what is being said. At A2, translate only new vocabulary. At B1+, no dialogue translations. Example:

> **Оленка:** Привіт! Як справи? *(Hi! How are you?)*
> **Тарас:** Добре, дякую! А у тебе? *(Good, thanks! And you?)*
> **Оленка:** Теж добре! *(Also good!)*

Without speaker names, the reader cannot tell who is speaking. NEVER use anonymous em dashes (`— text`). After each dialogue, briefly explain the key phrases and patterns the learner just saw.
- Dialogues: natural, not stilted. Real situations, real responses. **Use the knowledge packet** — it contains textbook excerpts with real Ukrainian dialogues and situations. Adapt them, don't invent artificial conversations. A dialogue about немає should show someone SEARCHING for something and not finding it (keys, notebook, phone), not an interrogation. A dialogue about the market should sound like a real market conversation. If the knowledge packet has a textbook dialogue on the topic, use that pattern.
- **Tone:** Authoritative but warm. Like a skilled Ukrainian teacher — confident, clear, culturally grounded. Let the content be interesting on its own.
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



---

### Style Reference (match this tone and structure)

> **(У магазині / At the store)**
> — Добрий день! Скільки коштує хліб? (Good day! How much does the bread cost?)
> — Дванадцять гривень. (Twelve hryvnias.)
> — Дякую! Ось, будь ласка. (Thanks! Here you go.)

Notice that the shopkeeper uses **Добрий день** — the formal greeting for strangers. If this were a friend, they would say **Привіт** instead.

The word **скільки** (how much/how many) is one of the most useful question words. It always pairs with the genitive case: **скільки коштує** (how much does it cost), **скільки часу** (how much time).

*Note: Short dialogues in Ukrainian with per-line English glosses. Grammar explained in English. Ukrainian sentences in blockquotes and bulleted lists.*

## Output Format

Write in Markdown. Use:
- `## Section Title` for main sections
- `### Subsection` for subsections within a section
- `**bold**` for Ukrainian words being taught — EVERY bold Ukrainian word MUST have an English translation on first use, either in parentheses `**слово** (translation)` or inline `**слово** means "translation"`. No exceptions.
- Tables for paradigms (conjugation, declension)
- `:::tip` / `:::caution` / `:::note` for callout boxes
- `:::quiz` / `:::fill-in` / `:::match-up` / `:::group-sort` / `:::true-false` for exercises (using the DSL formats above)

Do NOT write MDX component syntax or JSON. Plain Markdown with the exercise DSL blocks described above.

Begin writing now. Start with the first section heading.
