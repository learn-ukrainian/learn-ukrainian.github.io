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

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: My Day
**Module:** my-day | **Phase:** A1.4 [Time and Nature]
**Textbook grades searched:** 3, 4, 5

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 152
> Досліди, як змінюються 
> дієслова за часами.
> Я — дослідник
> Я — дослідниця
> Навчаюся змінювати дієслова за часами
> міркували
> міркуємо
> будемо міркувати
> 6   Прочитай слова і порівняй їх.
> Що означає дієслово? Коли відбувається дія?
> На яке питання відповідає дієслово?
> До якої часової форми належить кожне дієслово?
>   Зроби висновок, як змінювати дієслова за часами, і звір його з таблицею.
> Час дієслів
> Питання
> Приклади
> Теперішній час
> що роблю?
> що робиш?
> що робить?
> що роблять?
> лечу, пишу
> летиш, пишеш

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 1
> — Добре, — зам(’)явся хлопчик. — Але, розумієте...
> — Ти хочеш якийсь план на майбутнє?
> — Ага (Юлія Смаль).
> 3. Прочитала оповідання (Ю/ю)лії (С/с)маль «Магазин 
> планів на майбутнє». Я в захваті! Як гарно письме(н/нн)иця 
> розповідає про плани на майбутнє! Саме плани, а не мрії! 
> Бо мрії бувають різні, часто нездійсненні. І не мету! Бо мета має 
> бути чітка і виважена... А плани! Плани — це те, що ти щодня, 
> крок за кроком будеш виконувати. І у визначений тобою час, 
> якщо будеш упертим / упертою,

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 168
>  63 % багатих і лише 5 % бідних слухають аудіокниги 
> під час поїздки на роботу й назад.
>  67 % багатих людей дивляться телевізор одну годину 
> на день або менше порівняно з 23 % бідних людей.
>  79 % багатих людей уважають, що вони несуть відпові-
> дальність за свій фінансовий стан порівняно з 18 % бідних 
> людей (З інтернету).
>  
> ІІ   Розкажіть, звідки в дорослих беруться гроші. Пригадайте, де 
> і коли ми використовуємо гроші. На вашу думку, чи потрібно 
> заощаджувати гроші? Чому? Як саме? Розкажіть

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 151
> 	 	
> 3   Прочитайте розповідь третьокласника 
> про відвідування цирку.  
>   Випишіть дієслова за абеткою. Визначте їхній час. Доведіть свою думку. 
> У неділю ми ходили до цирку. Ми по-
> трапили в казкову країну, де відбувалися 
> справжні дива. Бурхливі оплески викли-
> кали трюки майстерних акробатів. Глядачі із захопленням ди-
> вилися шоу спритних жонглерів і дотепних клоунів. Особливо 
> сподобалися дорослим і дітям фокусники, ілюзіоністи. Мене 
> вразили гарні костюми й декорації, захопливе світлове

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> 108
>  
> чоловічий
> що робив?
> що зробив?
> читав,
> прочитав
> жіночий
> що робила?
> що зробила?
> що робило?
> що зробило?
> читала,
> прочитала
> читало,
> прочитало
> середній
> Однина
> що робили?
> що зробили?
> читали,
> прочитали
> Множина
> 	 Порівняйте зміст таблиць. Зробіть висновок, звірте його з пода-
> ним нижче правилом.
> 	 Від неозначеної форми дієслів малювати, мити утвори дієслова 
> минулого часу в однині та множині. Укажи рід в однині. Познач 
> закінчення чоловічого, жіночого й середнього роду. Користуйся 
> таблицею. 
> 257.

> **Source:** unknown, Grade 5
> **Score:** 0.33
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

## Мій типовий день (My Typical Day)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 86
> 243. 1.	 Прочитай вірш. Про які гарні манери згадує авторка?
> Зранку різних справ багато: 
> вмитись, їсти, одягатись.  
> Треба час розрахувати, 
> за годинником звірятись. 
> П’ять хвилин — 
> на умивання,  
> п’ять також — на одягання, 
> три — щоб постіль 
> поскладати,   
> потім снідати, малята! 
> Є й хвилини на дорогу.   
> З друзями іди у ногу, 
> не спиняйся ні на крок —  
> вчасно встигнеш на урок!
> 242.	 1.	 Прочитай текст. Які гарні манери ти ще знаєш ? Розкажи.
> З людиною, яка має гарні манери, приємно спіл

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> •  Складіть текст-розповідь за малюнком і словосполученнями. 
> Запишіть. Підкресліть словосполучення, яким позначено час.
> Правильно вимовляємо, пишемо, відповідаємо на 
> питання о котр ій год ині? котра година?
> Прокинувся о сьомій годині ранку. Чекатиму об оди­
> надцятій годині. На сімнадцяту годину прийду. Чверть 
> на третю розпочнемо. О пів на д ев’яту продзвенів 
> дзвінок (пів до дев ’ятої). За чверть хвилин дванадця­
> та година буде (чверть хвилин до дванадцятої). 
> Десять хвилин на п ’ятнадцяту го

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 147
> ослаблення імунітету. Крім того, якщо вранці ви не поїли, 
> будьте певні, що за обідом з’їсте мінімум у два рази більше, 
> ніж зазвичай.
> Привчіть себе їсти не раніше, ніж через пів години після 
> пробудження. Уставши з ліжка, випийте пів склянки теплень-
> кої води. Це активізує процеси життєдіяльності в організмі. 
> Можна додати у воду кілька крапель лимонного соку. По-
> тім займіться звичними справами: прийміть душ, одягніться, 
> зберіть сумку. За цей час шлунок почне працювати – і ви від-
> чуєте л

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> Пригадую знання про звуки і букви . . . . . . . . . . . . . . . . . . . . . . . . . . .4
> Спостерігаю за значенням слів  . . . . . . . . . . . . . . . . . . . . . . . . . . . . 23
> Досліджую будову слова . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 34
> Дізнаюся більше про іменники . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 78
> Досліджую прикметники . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 92
> Розпізнаю числівники  . . . . . . . . . . .

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> 86
> 209.		Розгляньте таблицю та обговоріть її зміст.
> 	 Склади п’ять  речень із правильними формулами на позначення 
> часу, які подані в таблиці (на вибір). Запиши.
> 210.		Прочитай слова та формули на позначення часу.
> Працював ...	
> о сьомій годині п’ятнадцять хвилин.
> Прокинулася ...	
> до тринадцятої години.
> Зателефонував ...	чверть по одинадцятій.
> Показує ...	
> о десятій годині.
> 	 З’єднай слова та формули на позначення часу. Запиши.
> 211.		Розглянь малюнки.
> 12 1
> 11
> 2
> 4
> 5
> 7
> 8
> 3
> 9
> 6
> 10
> 12 1
> 11
> 2
> 4
> 5
> 7
> 8

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

## Від ранку до вечора (From Morning to Evening)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 86
> 243. 1.	 Прочитай вірш. Про які гарні манери згадує авторка?
> Зранку різних справ багато: 
> вмитись, їсти, одягатись.  
> Треба час розрахувати, 
> за годинником звірятись. 
> П’ять хвилин — 
> на умивання,  
> п’ять також — на одягання, 
> три — щоб постіль 
> поскладати,   
> потім снідати, малята! 
> Є й хвилини на дорогу.   
> З друзями іди у ногу, 
> не спиняйся ні на крок —  
> вчасно встигнеш на урок!
> 242.	 1.	 Прочитай текст. Які гарні манери ти ще знаєш ? Розкажи.
> З людиною, яка має гарні манери, приємно спіл

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 91
> 5. Прочитай заголовок тексту. Чи знаєш ти, що означає цей 
> вислів? Прочитай текст, щоб 

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Мій типовий день (My Typical Day)` (~300 words)
- `## Від ранку до вечора (From Morning to Evening)` (~300 words)
- `## Підсумок — Summary` (~300 words)
- `## Підсумок` (~150 words)

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

**Required:** вранці (in the morning), вдень (during the day), ввечері (in the evening), обідати (to have lunch), вечеряти (to have dinner), відпочивати (to rest), після (after)
**Recommended:** прокидатися (to wake up — review from M20), вмиватися (to wash — review from M20), одягатися (to get dressed — review from M20), вночі (at night), після обіду (in the afternoon), також (also), лягати спати (to go to bed — chunk), типовий (typical), вільний (free)

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
