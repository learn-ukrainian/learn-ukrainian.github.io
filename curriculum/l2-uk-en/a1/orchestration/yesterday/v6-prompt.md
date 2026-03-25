# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **49: Yesterday** (A1, A1.8 [Past, Future, Graduation]).

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
module: a1-049
level: A1
sequence: 49
slug: yesterday
version: '1.2'
title: Yesterday
subtitle: Учора я прокинувся, поснідав і пішов — narrating your day
focus: communicative
pedagogy: PPP
phase: A1.8 [Past, Future, Graduation]
word_target: 1200
objectives:
- Narrate a complete past day using sequenced past-tense verbs
- Use time markers to structure a narrative (зранку, вдень, ввечері)
- Combine past tense with known vocabulary (food, places, people)
- Tell a short personal story about yesterday
content_outline:
- section: Dialogues
  words: 300
  points:
  - Dialogue 1 — How was your day? — Як пройшов твій день? — Добре! Зранку я прокинувся
    о сьомій. — Що ти робив зранку? — Я поснідав і пішов на роботу. — А вдень? — Вдень
    я працював і обідав з колегою. — А ввечері? — Ввечері я дивився фільм і рано ліг
    спати. Full day narration using time markers.
  - 'Dialogue 2 — A fun weekend: — Що ти робила у суботу? — О, я мала чудовий день!
    — Розкажи! — Зранку я ходила на ринок і купила фрукти. — А потім? — Потім я готувала
    обід. А вдень гуляла в парку. — А ввечері? — Ввечері ми з подругою ходили в ресторан.
    — Як файно! Sequencing with потім, а потім.'
- section: Розповідь про день (Narrating a Day)
  words: 300
  points:
  - 'Time markers for structuring a story: зранку (in the morning), вдень (in the
    afternoon), ввечері (in the evening), вночі (at night). спочатку (first), потім
    (then), після цього (after that), нарешті (finally). These words turn separate
    sentences into a story: Спочатку я поснідав. Потім я пішов на роботу. Після цього
    я обідав.'
  - 'Daily routine verbs in past tense (all genders): прокинутися → прокинувся / прокинулася
    поснідати → поснідав / поснідала піти → пішов / пішла обідати → обідав / обідала
    повернутися → повернувся / повернулася лягти спати → ліг / лягла спати'
- section: Мій учорашній день (My Yesterday)
  words: 300
  points:
  - 'Model narrative — Anna''s yesterday: Учора був звичайний день. Зранку я прокинулася
    о пів на сьому. Я поснідала — їла кашу і пила каву. Потім я пішла на роботу. Вдень
    я обідала в кафе біля офісу. Я замовила салат і сік. Після роботи я ходила в магазин
    і купила продукти. Ввечері я готувала вечерю і дивилася серіал. О одинадцятій
    я лягла спати. Note all verbs are -ла (Anna is female).'
  - 'Your turn — build your own narrative: Use the template: Учора... Зранку я...
    Потім... Вдень... Ввечері... Combine past-tense verbs with places (кафе, парк,
    магазин), food (каша, кава, салат), and people (друг, колега, подруга). Everything
    you learned in A1 comes together here.'
- section: Summary
  words: 300
  points:
  - 'Narration toolkit: Time structure: зранку → вдень → ввечері → вночі. Sequencing:
    спочатку, потім, після цього, нарешті. Daily routine past forms: прокинувся/-лася,
    поснідав/-ла, пішов/пішла, обідав/-ла, повернувся/-лася, ліг/лягла спати. Gender
    consistency: male speakers use -в/-вся forms throughout, female speakers use -ла/-лася
    throughout. Self-check: Tell the story of your yesterday using at least 5 verbs.'
vocabulary_hints:
  required:
  - учора (yesterday)
  - зранку (in the morning)
  - вдень (in the afternoon)
  - ввечері (in the evening)
  - потім (then)
  - прокинутися (to wake up)
  - поснідати (to have breakfast)
  - обідати (to have lunch)
  recommended:
  - спочатку (first/at first)
  - нарешті (finally)
  - повернутися (to return)
  - лягти (to lie down)
  - звичайний (ordinary, adj)
  - продукти (groceries, pl)
  - серіал (TV series, m)
  - колега (colleague, m/f)
activity_hints:
- type: ordering
  focus: Put the daily routine in chronological order
  items:
  - Зранку я прокинувся.
  - Спочатку я поснідав.
  - Потім я пішов на роботу.
  - Вдень я обідав з колегою.
  - Ввечері я повернувся і дивився серіал.
  - Нарешті я ліг спати.
- type: fill-in
  focus: Complete the narrative with time markers and sequenced verbs
  items:
  - Учора {зранку|вдень|потім} я прокинулася о сьомій.
  - '{Спочатку|Нарешті|Вночі} я поснідала.'
  - '{Потім|Зранку|Ввечері} я пішла на роботу.'
  - Вдень я {обідала|обідав|обідали} в кафе.
  - '{Ввечері|Вдень|Зранку} я готувала вечерю.'
  - О десятій я {лягла|ліг|лягли} спати.
- type: fill-in
  focus: Practice gender consistency in narration (Female speaker 'Anna')
  items:
  - Я мала звичайний день. Я {прокинулася|прокинувся} рано.
  - Потім я {поснідала|поснідав}.
  - Після цього я {пішла|пішов} у магазин.
  - Там я {купила|купив} продукти.
connects_to:
- a1-050 (What Will Happen?)
prerequisites:
- a1-048 (What Happened?)
grammar:
- Past tense in connected narration (not isolated sentences)
- 'Time markers: зранку, вдень, ввечері, вночі'
- 'Sequencing words: спочатку, потім, після цього, нарешті'
- Gender consistency across a narrative
register: розмовний
references:
- title: State Standard 2024, §4.2.4.1
  notes: Past tense applied in narrative context.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Yesterday
**Module:** yesterday | **Phase:** A1.8 [Past, Future, Graduation]
**Textbook grades searched:** 5, 6, 7

---

## Dialogues

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 218
> Доброго ранку! Добрий день! Привіт! Радий бачити тебе. 
> * * *
> До побачення! На все добре! Гарного дня! Бувайте здорові! До зу-
> стрічі!
> Бажаю успіхів! Хай щастить! Рада була зустрітися.
> * * *
> Вибачте. Пробачте. Прошу вибачити (пробачити).
> Даруйте. Перепрошую. Вибачте, що турбую.
> * * *
> Дякую. Щиро дякую. Я тобі дуже вдячний. Будь ласка. Нема 
> за що.
> 528.	І. ПОПРАЦЮЙТЕ В ПАРАХ. Уявіть, що хтось із вас опинився в 
> чужому місті і йому необхідно з’ясувати, де розміщено стадіон (цирк чи 
> театр). А

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 10
> 1.	Прочитайте записи в колонках і виконайте завдання. 
> о сьомій годині 
> кілька вправ 
> контрастним душем
> Я прокидаюсь о сьомій годині.
> Виконую кілька фізичних вправ. 
> Потім загартовуюся контрастним душем. 
> А.	 За допомогою записів якої колонки легше передати думки? 
> Б.	 У якій колонці записано словосполучення, а в якій — речення? 
> Словосполучення складається щонайменше з двох самостійних слів, 
> одне з яких головне, а друге — залежне: прокидаюся (коли?) рано; пи-
> шаюся (чим?) успіхами.  
> Підмет

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> 149
> 149
> ІІ. ПОПРАЦЮЙТЕ В ПАРАХ. Розподіліть між собою світлини. Доберіть за обра-
> ною світлиною 4–6 прислівників і запишіть. Зіставте свої записи. Чи є у вас одна-
> кові прислівники?  
> ІІІ. Складіть усно речення за одним із зображень, використавши кілька дібраних 
> прислівників.
> ПО РІВ НЯЙМО:
> добре
> Ранком
> КОЛО ДУМОК. Поміркуйте, до якої частини мови належить кожне виділене 
> слово. Розберіть ці слова за будовою.
> 1. Вечорами корисно бігати, щоб бути в гарній фізичній фор-
> мі (З довідника). 2. Я суму

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 193
> Відомості із синтаксису й пунктуації. Словосполучення
> 08.00
> 08.15
> 08.30
> 08.45
> 2. Усно назвіть час усіма можливими способами .
> 3. Доповніть і  розіграйте діалог про розклад дзвінків .
> — Коли починається перший урок?
> — О …
> — А закінчується?
> — …
> 4. Об’єднайтесь у  групи й  підготуйте діалоги для різних ситуацій з  вико-
> ристанням позначення часу (зустріч із друзями, відвідування спортивної 
> секції, перегляд улюбленого серіалу…) . Розіграйте ситуації перед класом . 
> Жартувати й  фантазувати можн

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> ви. Не могли вони таку малу дитину надовго кинути. Давай 
> краще чкурнемо звідси. (…)
> Ми не стали баритися. Шугонули вниз і кинулися навтікача. Бігти було важко, 
> бо доісторична трава була густа, висока й колюча. Але коли 
> вам загрожує небезпека й ви тікаєте, то думати про те, щоб 
> бігти було зручно й приємно, не доводиться. Коли ми вже зовсім захекались і відчули, що погоні нема, 
> ми спинилися й сіли перепочити під кущем якоїсь гігантської 
> папороті. (…)
> Поміркуй над прочитаним
>  
> 1. Чому уявні п

> **Source:** unknown, Grade 7
> **Score:** 0.33
>
> 66
> МОРФОЛОГІЯ.  ОРФОГРАФІЯ
> 6.	 Запам’ятайте, як правильно наголошувати слова.
> 7.	 Прочитайте речення та виконайте завдання.
> 1. Кому місяць світить, тому й зорі всміхают..ся. 2. Колос повний до зем-
> лі гнет..ся, а порожній — угору пнет..ся. 3. Узимку сонце так смієт..ся, що 
> аж віконце плаче (нар. тв.). 4. Дивиш..ся і не надивиш..ся, дихаєш і не 
> надишеш..ся тим чистим, гарячим і пахучим повітрям (за І. Нечуєм-Ле­
> вицьким). 5. Тепер я бігаю в поле й годинами слухаю, як у небі співають 
> хори, граю

## Розповідь про день (Narrating a Day)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> Він стежив за їхньою роботою, і по його тілу 
> час од часу пробігали дрижаки, ніби йому було дуже мороз­
> но  або ж  він  знову хотів спробувати вискочити, але сили по­
> ки­нули його. Мабуть, спочатку він нічого не розумів у тій 
> роботі, та коли канал ще більше наблизився до берега, його 
> 1 Наспіти — устигнути. 2 Закуняти — задрімати.

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> «Дозволяю тобі сьогодні встати на десять–п’ятнадцять хвилин». Я підвівся й сів на ліжку. «Хоч глянути на нього востаннє. От гляну, потім ляжу й умру». Я встав і, хитаючись, пошкандибав до вікна.

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> — Нічого, хоч потроху пий, сили набирайся. У Квасольки — найсолодше 
> у світі молоко. Цілий вечір бабця розпитувала мене про тата і маму, а я, сидячи на 
> ґанку, розповідав, не зводячи очей із багряного сонячного диска, що поволі 
> зменшувався, а тоді пірнув за гору. Небо ще трохи палало, а потім якось 
> різко, майже вмить, стемніло, і на землю опустилася ніч. Де-не-де в роз-

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 180
> СИНТАКСИС  І  ПУНКТУАЦІЯ  
> В Прилинув вітер і в нічній хатині він про весняну волю заспівав.
> Г Перед дощем море починає хвилюватись і набирати темної барви. 
> 7.	Прочитайте текст і виконайте завдання.
> Людину споконвіку цікавило, що криється за обрі-
> єм, за синім морем. Імовірно, що першу водну перешко-
> ду вона здолала за допомогою стовбура дерева. Згодом 
> первісна людина навчилася в’язати пліт, видовбувати 
> зі стовбура човен, будувати його з очерету, робити зі шкур тварин. Перші 
> письмові сві

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> свою записку і лягаю в ліжко, накрившись ковдрою з голо-
> вою. Ось цим і закінчиться мій сміливий вчинок! Бр-р-р…
> Подумавши так, я розізлився: от який «матусин сино-
> чок»! нікчема! А цікаво, як раніше люди долали відстані? 
> А як долали відстані справжні мандрівники? А як би вчинив 
> Трістан — той хлопець, що відрубав у чесному бою кіготь 
> ведмедя? Певно, не повернув би назад.
> Я роззирнувся довкола. Попереду пролягала широка ас-
> фальтована дорога. Завертаючи вбік від міста, вона перехо-
> дила у звич

> **Source:** unknown, Grade 7
> **Score:** 0.33
>
> То й що? Зараз і в Москві не 
> дуже заробиш, от і повернулися, не пробувши й двох місяців… Кинулася 
> до відривного календарика: повня! І минулого разу – також… Ці дивні 
> бешкети відбуваються в повню!!! А може, це всього-на-всього фантазія? Софійка читала про людей, котрі піддаються впливу нічного світила. Тоді 
> чому в їхньому старому помешканні було спокійно? – Ха-ха-ха!!! – прокотилося внизу тонко, ніби здавлено. Нетямлячись, рвонулася до спальні:
> – Мамусю, мамусю, вони знову!.. Мама також не сп

## Мій учорашній день (My Yesterday)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 210
> ІІ. На основі інформації, наведеної на діаграмі, та власного досвіду 
> складіть усне висловлення (3–5 речень) про розподіл часу учнів та 
> учениць за добу. Використайте щонайменше одне складне речення. 
> 516.	І. Відновіть текст, уставивши на місці пропусків слова, подані в 
> рамці. Кожне слово можна використати лише один раз.
> склянок / спортом / питний / дієтологи   
> розрахувала / лимонад / неквапливими / людина
> ПИТНИЙ РЕЖИМ
> Відомо, що ... в середньому на 75 % складається з води. 
> Саме тому дуже

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 10
> 1.	Прочитайте записи в колонках і виконайте завдання. 
> о сьомій годині 
> кілька вправ 
> контрастним душем
> Я прокидаюсь о сьомій годині.
> Виконую кілька фізичних вправ. 
> Потім загартовуюся контрастним душем. 
> А.	 За допомогою записів якої колонки легше передати думки? 
> Б.	 У якій колонці записано словосполучення, а в якій — речення? 
> Словосполучення складається щонайменше з двох самостійних слів, 
> одне з яких головне, а друге — залежне: прокидаюся (коли?) рано; пи-
> шаюся (чим?) успіхами.  
> Підмет

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> Ніздрі роздмухувалися. Цей запах, очевидно, нагадував 
> їй матір – стару вівчарку, малих братиків і сестричок, з якими 
> вона розлучилася й більше ніколи не побачиться. Та куди б і до 
> чого не підповзала, запах молока виманював її. Випила його й 
> вилизала тарілку. Дів

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Dialogues` (~300 words)
- `## Розповідь про день (Narrating a Day)` (~300 words)
- `## Мій учорашній день (My Yesterday)` (~300 words)
- `## Summary` (~300 words)
- `## Підсумок` (~150 words)

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

GRAMMAR CONSTRAINTS (A1.8 — Past, Future & Graduation, M51-M60):
Full A1 grammar including past and future tense.

ALLOWED:
- Past tense (він читав, вона читала — gendered!)
- Future tense (я буду читати, ми будемо працювати)
- All cases, moods, and constructions from A1.1-A1.7
- Combining tenses in connected speech

BANNED: Participles, passive voice, complex literary constructions

### Vocabulary

**Required:** учора (yesterday), зранку (in the morning), вдень (in the afternoon), ввечері (in the evening), потім (then), прокинутися (to wake up), поснідати (to have breakfast), обідати (to have lunch)
**Recommended:** спочатку (first/at first), нарешті (finally), повернутися (to return), лягти (to lie down), звичайний (ordinary, adj), продукти (groceries, pl), серіал (TV series, m), колега (colleague, m/f)

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
