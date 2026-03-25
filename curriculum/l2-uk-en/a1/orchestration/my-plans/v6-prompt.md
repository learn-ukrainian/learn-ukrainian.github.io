# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **51: My Plans** (A1, A1.8 [Past, Future, Graduation]).

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
module: a1-051
level: A1
sequence: 51
slug: my-plans
version: '1.2'
title: My Plans
subtitle: У суботу я буду... — scheduling and weekend plans
focus: communicative
pedagogy: PPP
phase: A1.8 [Past, Future, Graduation]
word_target: 1200
objectives:
- Talk about weekend and weekly plans using analytic future
- Schedule activities with specific days and times
- Combine future tense with time expressions (у суботу, о третій, ввечері)
- Invite someone and respond to invitations using future tense
content_outline:
- section: Dialogues
  words: 300
  points:
  - 'Dialogue 1 — Making plans: — Що ти будеш робити у суботу? — Зранку я буду прибирати
    квартиру. — А вдень? — Вдень я буду ходити в магазин. А ти? — Я буду відпочивати!
    Може, підемо в кафе ввечері? — Добре! О котрій? — О шостій. Добре? — Чудово! До
    зустрічі у суботу! Future + time + invitation.'
  - 'Dialogue 2 — A busy week: — У тебе є плани на тиждень? — Так, багато! — У понеділок
    я буду працювати допізна. — У вівторок буду вчитися. У середу — зустріч з друзями.
    — А у четвер? — У четвер я буду готувати на вечірку. — А в п''ятницю? — В п''ятницю
    — вечірка! Ти будеш? — Звичайно буду! Days of week + future planning.'
- section: Планування (Planning)
  words: 300
  points:
  - 'Scheduling patterns: У + day: у понеділок, у вівторок, у середу, у четвер, у
    п''ятницю. У суботу / в неділю (on Saturday / on Sunday). О + time: о дев''ятій,
    о третій, о шостій. Зранку / вдень / ввечері (morning / afternoon / evening).
    Combine: У суботу ввечері я буду дивитися фільм.'
  - 'Invitation phrases: Ходімо в кафе! (Let''s go to a cafe! — imperative from M43)
    Може, підемо в кіно? (Maybe we''ll go to the cinema?) Ти будеш вільний/вільна
    у суботу? (Will you be free on Saturday?) Давай зустрінемося о п''ятій! (Let''s
    meet at five!) Responses: Добре! Чудово! З задоволенням! На жаль, не можу.'
- section: Мій тиждень (My Week)
  words: 300
  points:
  - 'Model plan — Taras''s week: У понеділок я буду працювати. Після роботи буду вчити
    українську. У вівторок я буду обідати з другом у кафе. У середу ввечері я буду
    дивитися футбол. У четвер я буду готувати вечерю для родини. У п''ятницю я буду
    відпочивати — піду в кіно. У суботу зранку буду прибирати, а вдень гуляти в парку.
    В неділю я буду спати довго! Each day = буду + activity.'
  - 'Your turn — plan your week: Template: У [day] я буду [activity]. Add details:
    time (о котрій?), place (де?), with whom (з ким?). У суботу о десятій я буду гуляти
    в парку з другом. Use all the A1 vocabulary: places, food, people, activities.'
- section: Summary
  words: 300
  points:
  - 'Planning toolkit: Day + time + буду + infinitive: У суботу о третій я буду готувати
    обід. Invitations: Ходімо! Може, підемо? Давай зустрінемося! Responses: Добре!
    З задоволенням! На жаль, не можу. Days review: понеділок, вівторок, середа, четвер,
    п''ятниця, субота, неділя. Self-check: Plan your ideal weekend — what will you
    do on Saturday and Sunday?'
vocabulary_hints:
  required:
  - план (plan, m)
  - тиждень (week, m)
  - вільний (free, adj)
  - зустріч (meeting, f)
  - відпочивати (to rest)
  - прибирати (to clean)
  - вечірка (party, f)
  recommended:
  - зустрінемося (let's meet — chunk)
  - з задоволенням (with pleasure)
  - на жаль (unfortunately)
  - допізна (until late)
  - звичайно (of course)
  - квартира (apartment, f)
  - кіно (cinema, n)
  - вчити (to study/learn)
activity_hints:
- type: fill-in
  focus: Combine days of the week, time, and future tense
  items:
  - У {понеділок|понеділку|понеділка} я буду працювати.
  - У суботу {зранку|ранок|ранку} я буду прибирати квартиру.
  - '{О|В|На} шостій ми будемо дивитися кіно.'
  - У {неділю|неділя|неділі} він буде відпочивати.
  - У п'ятницю {ввечері|вечір|вечора} буде вечірка.
- type: matching
  focus: Match invitations to natural responses
  pairs:
  - Ходімо в кіно!: З задоволенням!
  - Може, підемо в кафе?: Добре! О котрій?
  - Ти будеш вільний у суботу?: На жаль, не можу.
  - Давай зустрінемося о п'ятій!: Чудово! До зустрічі!
- type: fill-in
  focus: Complete a scheduled plan for the week
  items:
  - У вівторок я {буду вчити|вчив|вчу} українську.
  - У середу ми {будемо готувати|готували|готуємо} вечерю.
  - У четвер вона {буде працювати|працювала|працює} допізна.
connects_to:
- a1-052 (My Story)
prerequisites:
- a1-050 (What Will Happen?)
grammar:
- 'Future tense in scheduling: day + time + буду + infinitive'
- 'Invitation patterns: Ходімо! Може, підемо? Давай зустрінемося!'
- 'Day-of-week prepositions: у понеділок, у суботу, в неділю'
register: розмовний
references:
- title: State Standard 2024, §4.2.4.1
  notes: Future tense applied in planning and scheduling context.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: My Plans
**Module:** my-plans | **Phase:** A1.8 [Past, Future, Graduation]
**Textbook grades searched:** 5, 6, 7

---

## Dialogues

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 28
> 61
>   Пригадайте і запишіть за відведений час якомога більше запо-
> зичених слів, що мають у нашій мові відповідники. Яким із них 
> варто віддавати перевагу?
> 62
>   Прочитайте слова. Виберіть будь-яку пару слів і складіть із ними 
> діалог, в основі якого має бути пропозиція одного зі співрозмов-
> ників і згода іншого.
> Глосарій — словничок, дисонанс — розлад, голкіпер — 
> воротар, кутюр’є — кравець.
> 63   І   Не знаючи вас, ми ось так зобразили світ ваших захоплень. 
> Розгляньте малюнок і скажіть, чи зб

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 33
> 69   Визначте основну думку тексту. Випишіть приклади словозміни 
> і словотворення. Поділіться досвідом прибирання своєї кімнати, 
> квартири чи будинку. Розберіть за будовою виділені слова. Випи-
> шіть слова, уставляючи пропущені букви. Уявімо собі захаращену кімнату. Безлад у ній не утворю-
> ється сам собою. Ви, людина, яка живе в ній, утворюєте без-
> лад. Є такий вислів: «Безлад у кімнаті — безлад у голові». Чи говорили ви собі: «Я просто не вмію приб..рати» або 
> «Немає сенсу пр..бирати: я від п

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> 138
> 138
> Варіант В. Напишіть есе (6–8 речень) на одну із запропонованих тем: «Мій 
> вихідний», «Мої домашні обов’язки», «Мій день народження». Використайте що-
> найменше два дієприслівники та два дієприкметники.
> Виконайте завдання. 
> 1. Пасивними є обидва дієприкметники в рядку
> А перебитий, усвідомлений
> В розбитий, змарнілий
> Б посивілий, змоклий 
> Г замусолений, навислий
> 2. Орфографічну помилку допущено в рядку
> А Відійшов, не здужавши підняти штангу.
> Б Недобачаючи в темряві, спіткнувся.
> В Говорив зав

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 128
> Речення з двома і більше граматичними основами нази-
> вають складним.
> Частини складного речення пов’язані між собою зміс-
> том та інтонацією або змістом і сполучниками.
> Частини складного речення можуть бути:
>  незалежні, рівноправні;
>   залежні, коли від одного речення можна поставити 
> питання до іншого.
> 1. Гуляє вітер, і співає симфонію дощ (Ю. Григорук). 2. Я 
> так люблю, як сонце у кімнаті удосвіта прийде мене будить 
> (Н. Янушевич). 3. Розсипле ранок перлами намисто, заструме-
> ніє сонце по гіл

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> § 55. Будова слова. Словотвір. Орфографія  
> 281
> С..огодні цей термін означає с..туац..ю, коли ви обі-
> цяєте собі або іншим щось (з/с)робити, але п..р..клада-
> єте це (з/с)початку на завтра, потім на післязавтра, і  так 
> тр..ває доволі довго. У п..рекладі з  латин..с..кої мови 
> воно означає «п..р..несення на наступний день». 
> 2. Спишіть текст, заповнивши пропуски й обравши один варіант із пода-
> них у  дужках.
> 3. Які ви маєте способи боротьби з відкладанням «на потім»? Прочитайте 
> поради психологів

> **Source:** unknown, Grade 7
> **Score:** 0.33
>
> § 23  Прислівник як частина мови  
> 137
> Їсти (піцу/смачно), повернутися (надвечір/після уроків), 
> чекати (біля супермаркету/отам), планувати (цієї зими/взим­
> ку), працювати (довго/три години), бути (в школі/деінде), по­
> бачитися (зранку/о дев’ятій), дістатися (пішки/тролейбусом), 
> говорити (по­китайськи/китайською мовою).
> Вправа 186
>  
> Доповніть словосполучення прислівниками, що відповідатимуть на по-
> ставлені питання 
> Іти (куди?), іти (коли?), іти (звідки?), іти (як?); співати (як?), 
> співати (ко

## Планування (Planning)

> **Source:** unknown, Grade 5
> **Score:** 0.50
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
> **Score:** 0.50
>
> § 52. Правильне вживання числівників на позначення дат і часу  
> 245
> § 52. Правильне вживання числівників
> на позначення дат і  часу
> Вправа 496
>  
> Прочитайте напис на дошці. Чому, на вашу думку, було зроблено ви-
> правлення?
> Пригадайте формули визначення часу:
> Котра́ година?  — Сьома. Дванадцята. Третя. Пів-
> день. Північ.
> Перша половина 
> години
> Рівно половина 
> години
> Друга половина 
> години
> на, по
> пів на / о  пів на
> за, до
> 6.20
> двадцять (хви-
> лин) по шостій 
> (годині), двад-
> цять (хвилин) 
> на сьому (г

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> 228
> 228
> Відредагуйте усно речення. Поясніть суть допущених помилок.
> 1. Просимо відповідати за чергою. 2. Відділ по розкриттю 
> зло чинів знаходиться в сусідньому приміщенні. 3. Моя сестра 
> старша мене на два роки. 4. Ми прийшли по їх проханню. 5. Не 
> годиться жити на чужий рахунок. 6. Маринка допустила дві 
> помилки по неуважності. 7. На канікулах я не поїхала до бабусі 
> завдяки тому, що захворіла. 8. Згідно розпорядження директо-
> ра завтра буде вихідний.
> Придумайте, дотримуючись поданих критеріїв

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 11
> Культура мовлення
> ПРАВИЛЬНО
> НЕПРАВИЛЬНО
> Зачиніть двері – протяг!
> У тебе нежить!
> Я буду о третій годині.
> Увімкніть світло.
> Приберіть сміття.
> Закрийте двері – сквозняк!
> У тебе насморк!
> Я буду в три часа.
> Увімкніть свєт.
> Приберіть мусор.
> 11.	 Спишіть речення, замінюючи поданий у дужках іменник спільно-
> кореневим прикметником. 
> 1. Купили (школа) приладдя. 2. Поїхали до (Харків) об-
> ласті. 3. Підійшли до (пішохід) переходу. 4. Я відповів на 
> (телефон) дзвінок. 5. Милувалися (ліс) квітами. 6. Остан

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> Розділ 7. Числівник 
> 246
> Вправа 497
> Спишіть словосполучення, що позначають час, виправивши помилкові 
> форми.
> Двадцята п’ятнадцять, чверть на восьму, без шести 
> вісім, три години сім хвилин, половина одинадцяти, де-
> сять до сьомої, сімнадцять по п’ятій, сорок три хвилини 
> на восьму, за тридцять вісім хвилин шоста, біля сьомої, 
> о  пів на першу. 
> Вправа 498
> Дайте всі можливі варіанти відповіді на питання «Котра година?» щодо 
> позначеного часу.
> 10:00, 10:10, 10:15, 10:30, 10:45, 10:50.
> Вправа 499
> 1

> **Source:** unknown, Grade 7
> **Score:** 0.33
>
> 252
> Повторення
> ***
> У мене стільки планів на канікули. А в підсумку як 
> завжди: комп — спати — комп — спати — комп — спати… 
> Проти системи не попреш.
> ***
> Останній тиждень перед літніми канікулами — це така 
> довга п’ятниця перед великими вихідними.
> 2   Випишіть у три групи прийменники, сполучники та частки 
> Вправа 337
> 1  Спишіть сполучення слів, заповнивши пропуски та знявши риску 
> Не/мов/би/то зна..мо, пиш..мо смс/повідомлення аби/
> кому, без/перестанку роб..ш, чим/дуж намага..мося, при-
> йшли хтоз

## Мій тиждень (My Week)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 28
> 61
>   Пригадайте і запишіть за відведений час якомога більше запо-
> зичених слів, що мають у нашій мові відповідники. Яким із них 
> варто віддавати перевагу?
> 62
>   Прочитайте слова. Виберіть будь-яку пару слів і складіть із ними 
> діалог, в основі якого має бути пропозиція одного зі співрозмов-
> ників і згода іншого.
> Глосарій — словничок, дисонанс — розлад, голкіпер — 
> воротар, кутюр’є — кравець.
> 63   І   Не знаючи вас, ми ось так зобразили світ ваших захоплень. 
> Розгляньте малюнок і скажіть, чи зб

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 78
> Морфологiя та орфографiя 
>  
>  ПОСПІЛКУЙТЕСЯ. Яке народне свято вам подобається найбільше? Чим 
> саме?
> ЧОМУ ТАК? Поясніть, чому в першому реченні виділене с

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Dialogues` (~300 words)
- `## Планування (Planning)` (~300 words)
- `## Мій тиждень (My Week)` (~300 words)
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

**Required:** план (plan, m), тиждень (week, m), вільний (free, adj), зустріч (meeting, f), відпочивати (to rest), прибирати (to clean), вечірка (party, f)
**Recommended:** зустрінемося (let's meet — chunk), з задоволенням (with pleasure), на жаль (unfortunately), допізна (until late), звичайно (of course), квартира (apartment, f), кіно (cinema, n), вчити (to study/learn)

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
