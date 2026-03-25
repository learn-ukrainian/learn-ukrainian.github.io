# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **20: My Morning** (A1, A1.3 [Actions]).

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
module: a1-020
level: A1
sequence: 20
slug: my-morning
version: '1.2'
title: My Morning
subtitle: Прокидаюся, вмиваюся — reflexive verbs and routines
focus: grammar
pedagogy: PPP
phase: A1.3 [Actions]
word_target: 1200
objectives:
- Recognize and use reflexive verbs with -ся/-сь
- Describe a morning routine using sequence words
- Conjugate reflexive verbs in present tense (same endings + ся)
- Tell a simple daily story in sequence
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Morning routine: — Коли ти прокидаєшся? — Я прокидаюся о сьомій.
    — Що ти робиш потім? — Вмиваюся, одягаюся і снідаю. — А коли ти йдеш на роботу?
    — О восьмій. Reflexive verbs emerge through describing the morning.'
  - 'Dialogue 2 — Weekend morning (contrast): — У суботу я не поспішаю. Прокидаюся
    пізно, лежу, дивлюся телефон. — А я навчаюся вранці. Потім гуляю. Mix of reflexive
    and non-reflexive verbs.'
- section: Дієслова на -ся (Reflexive Verbs)
  words: 300
  points:
  - 'Караман Grade 10 p.176: Дієслова із суфіксом -ся(-сь) означають дію, спрямовану
    на себе. вмивати (to wash someone) → вмиватися (to wash oneself). одягати (to
    dress someone) → одягатися (to dress oneself). The -ся attaches to the end of
    every conjugated form: я вмиваюся, ти вмиваєшся, він/вона вмивається.'
  - 'Кравцова Grade 4 p.113: pronunciation note: -шся sounds like [с'':а] (long soft
    с): вмиваєшся → [вмиваєс'':а]. -ться sounds like [ц'':а] (long soft ц): вмивається
    → [вмиваєц'':а]. The spelling and pronunciation differ — learn both!'
- section: Мій ранок (My Morning)
  words: 300
  points:
  - 'Morning routine vocabulary (reflexive verbs): прокидатися (to wake up), вмиватися
    (to wash face/hands), одягатися (to get dressed), збиратися (to get ready), повертатися
    (to return home). Non-reflexive morning verbs for contrast: снідати (to have breakfast),
    пити каву (to drink coffee). Йти (to go) — irregular: я йду, ти йдеш, він/вона
    йде. Learn these forms — they don''t follow Group I or II patterns.'
  - 'Sequence words for telling a story: спочатку (first), потім (then), після цього
    (after this), нарешті (finally). Мій ранок: Спочатку я прокидаюся. Потім вмиваюся
    і одягаюся. Після цього снідаю. Нарешті йду на роботу.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Reflexive verbs = regular verb + ся at the end. я -юся, ти -єшся, він/вона -ється
    (Group I pattern + ся). Morning routine: прокидатися → вмиватися → одягатися →
    снідати → йти. Sequence words: спочатку, потім, після цього, нарешті. Self-check:
    Describe your morning in 4-5 sentences using sequence words.'
vocabulary_hints:
  required:
  - прокидатися (to wake up)
  - вмиватися (to wash face/hands)
  - одягатися (to get dressed)
  - снідати (to have breakfast)
  - йти (to go — irregular)
  - спочатку (first, at first)
  - потім (then, next)
  recommended:
  - збиратися (to get ready)
  - повертатися (to return)
  - навчатися (to study/learn)
  - поспішати (to hurry)
  - після цього (after this)
  - нарешті (finally)
  - вранці (in the morning)
  - пізно (late)
activity_hints:
- type: fill-in
  focus: 'Add -ся: я вмиваю__ , ти одягаєш__ , він прокидаєть__'
  items: 10
- type: quiz
  focus: 'Reflexive or not? Choose: Я (вмиваю/вмиваюся) руки.'
  items: 8
- type: fill-in
  focus: 'Put the morning routine in order: спочатку ___, потім ___, нарешті ___'
  items: 6
- type: fill-in
  focus: Describe your morning in 3 sentences
  items: 3
connects_to:
- a1-021 (Checkpoint — Actions)
prerequisites:
- a1-019 (Questions)
grammar:
- 'Reflexive verbs: regular conjugation + -ся/-сь suffix'
- 'Pronunciation: -шся=[с'':а], -ться=[ц'':а] (gemination)'
- 'Sequence words: спочатку, потім, після цього, нарешті'
register: розмовний
references:
- title: Караман Grade 10, p.176
  notes: 'Зворотні дієслова: суфікс -ся(-сь) означає дію, спрямовану на себе.'
- title: Кравцова Grade 4, p.113
  notes: 'Pronunciation: -шся=[с''а], -ться=[ц''а].'
- title: Захарійчук Grade 4, p.162
  notes: 'Дієслова на -ся: вправи з вимовою та правописом.'

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: My Morning
**Module:** my-morning | **Phase:** A1.3 [Actions]
**Textbook grades searched:** 3, 4, 5

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 56
> 18
> Протилежні за значенням  
> слова — антоніми
> Розпізнаю протилежні 
> за значенням слова
> Пригадай і розкажи 
> у класі.
> Я — учителька
> Я — учитель
> Слова, які мають протилежне зна-
> чення, називаються антонімами.
> вечір — ранок
> сидіти — стояти
> вгорі — внизу
> день — ніч
> Хто швидше відгадає загадку?
> Чорна корова всіх людей поборола.
> А білий віл усіх людей побудив.
> Нових друзів май,
> Більше думай,
> Ледачий голодний,
> плакати
> схід
> запитання
> мовчати
> швидкий
> а працьовитий ситий.
> а менше говори.
> а старих не заб

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 85
> 3. Разом із сусідом/сусідкою по парті розіграйте діалог
> за  запитаннями  Родзинки.
> 1. О котрій годині ти просинаєшся в будні?
> 2. До котрої години ти спиш у вихідні?
> 3. З котрої години починаються заняття у школі?
> 4. Котра зараз година?
> 4. Прочитай речення. Знайди на малюнку годинник, який 
> показує зазначений у кожному реченні час. Запиши
> речення в такій послідовності, як розміщені годинники. 
> Підкресли числівники.
> 1. Сьома година п’ятнадцять хвилин, або чверть 
> на восьму.
> 2. Сьома година соро

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

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 148
> Зроби висновок, які зна-
> чення мають дієслова- 
> синоніми.  
> Я — дослідник
> Я — дослідниця
> Навчаюся добирати і вживати  
> в мовленні дієслова-синоніми, дієслова-антоніми
> іти 
> рухатися
> прямувати
> пересуватися
> дрімає
> спить
> куняє
> прокинеться
> встане
> пробудиться
>  заспіває
>  обізветься
>  защебече   
> 6   Прочитай і порівняй слова. Які значення мають ці слова?
> Дієслова-синоніми — це дієслова, близькі за значенням: 
> говорити, казати, балакати, шепотіти, базікати, 
> щебетати.
> Дієслова-антоніми — це дієслова

> **Source:** unknown, Grade 4
> **Score:** 0.33
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
> **Score:** 0.33
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

## Дієслова на -ся (Reflexive Verbs)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 148
> Зроби висновок, які зна-
> чення мають дієслова- 
> синоніми.  
> Я — дослідник
> Я — дослідниця
> Навчаюся добирати і вживати  
> в мовленні дієслова-синоніми, дієслова-антоніми
> іти 
> рухатися
> прямувати
> пересуватися
> дрімає
> спить
> куняє
> прокинеться
> встане
> пробудиться
>  заспіває
>  обізветься
>  защебече   
> 6   Прочитай і порівняй слова. Які значення мають ці слова?
> Дієслова-синоніми — це дієслова, близькі за значенням: 
> говорити, казати, балакати, шепотіти, базікати, 
> щебетати.
> Дієслова-антоніми — це дієслова

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> Дієслова на -ся, -сь виражають дію, спрямовану на самого^ 
> виконавця (на самого себе).
> \________________ _____________________ /
> Крок 1. Прочитай дієслова. Укажи їх особу, число.
> умиваєшся, обливаєшся умивається, обливається
> Крок 2. Прочитай дієслова умиваєшся, умивається. Поділи їх на 
> склади. Швидко пошепки промов останній склад кожного слова.
> шся [с':а]
> ться —> [ц':а]
> КрокЗ. Зроби висновок та порівняй його з правилом.
> ҐУ дієсловах 2-ї особи однини -шся вимовляють як [с':а]. У діє-^і 
> словах 3

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> Ч а с т и н и   м о в и
> Самостійні 
> Іменник 
> сонце
> хто? що?
> Прикметник
> сонячний, мамин
> який? чий?
> Числівник
> три, третій
> скільки? котрий?
> Займенник
> я, ти, він
> хто? що?
> Дієслово
> сидіти
> що робити? що зробити?
> Прислівник 
> сонячно, восени
> як? де? коли? куди?
> Службові
> Прийменник
> на, в, з, до
> Не відповідають на 
> питання
> Сполучник
> і, й, та, але
> Частка
> не, б, хай
> В и д и  р е ч е н ь
> За метою 
> висловлювання
> За емоційним 
> забарвленням
> За будовою
> розповідне
> окличне
> просте
> питальне
> неокличне
> складне
> спонука

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 95
> ДІЄСЛОВА-АНТОНІМИ, ДІЄСЛОВА-СИНОНІМИ, 
> ДІЄСЛОВА З ПРЯМИМ І ПЕРЕНОСНИМ ЗНАЧЕННЯМ
> 265.	 1.	 Прочитай вірш. Пригадай, які слова називають антоні-
> мами. Знайди їх у вірші.
> За Валентиною  Бутрім
> 2.	 До яких частин мови належать антоніми з вірша? Назвиѳ діє- 
> слова-антоніми. Усно склади з ними речення.
> Є слова, як день і ніч, —  
> прямо протилежні.  
> От я обачливий, скажім, 
> а ти — необережний. 
> Слова «великий» і «малий», 
> «сідати» і «вставати», 
> «холодний» — «теплий», 
> «добрий» — «злий»  
> антонімам

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> •  Спишіть текст. Підкресліть дієслова. Укажіть у дужках час, 
> особу й число дієслів за зразком у тексті.
> Дієслова на -ся
> 370. Прочитайте вірш Галини Кирпи.
> Дерево трудиться назеленітися.
> Квіточка трудиться начервонітися.
> Бджілка трудиться налітатися.
> Метеличок трудиться нагойдатися.
> Травичка — водички напитися.
> Росинка — на білий світ надивитися.
> •  Випишіть дієслова на -ся. Доведіть, що вони означають дію, 
> спрямовану на себе. Позначте будову виділених слів.
> •  Зробіть звуко-буквений аналіз ді

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 27
> Лексикологія. Лексичне значення слова
> сир
> рис
> Лексичне значення слова
> Вправа 25
> 1. Доберіть ілюстрації до слів .
> 2. Поміркуйте, чим схожі й  чим відрізняються слова .
> 3. Що допомагає вам зрозуміти значення слів?
> Вправа 26
> 1. Прочитайте слова й  випишіть ті з  них, які мають лексичне значення .
> Щастя, сильний, сьомий, книга, чудово, не, собака, він, 
> про, любити, холодно, але, сміятися, корисний, в, б, знати, 
> сто, комп’ютерний, мій.
> 2. Визначте й  надпишіть, до  яких частин мови належать випи

## Мій ранок (My Morning)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 128
> От покупки я розклав
> і тепер гадаю:
> Комікс швидко прочитав,
> а лінійку мав я.
> Десь машинки розгубив,
> пістолет зламався.
> І навіщо це купив?
> Знов планшет відклався…
> Твердо вирішив собі:
> марнотратства досить!
> Я ощадливий тепер
> до речей і грошей.
> Перш ніж купувати щось, 
> добре обміркую:
> чи потрібне це мені,
> чи не пошкодую.
> І до того ж я завів
> дуже добру звичку:
> відкладати день у день
> гроші у скарбничку.
> Як завжди, мій шлях лежить
> повз два магазини
> і заходжу я туди
> справді на хвилину —
> подивитись

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 145
> 308. 1. Прочи

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Дієслова на -ся (Reflexive Verbs)` (~300 words)
- `## Мій ранок (My Morning)` (~300 words)
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

GRAMMAR CONSTRAINTS (A1.3 — Actions & Desires, M15-M21):
Present tense verbs, modals, questions, reflexives.

ALLOWED:
- Present tense conjugation (both groups: -ати and -ити)
- Modal verbs: хотіти, могти, мусити + infinitive
- Question words: Хто? Що? Де? Куди? Коли? Чому?
- Negation: не/ні
- Reflexive verbs (-ся/-сь)
- 'Мені подобається' as lexical chunk (NO dative grammar)

BANNED: Past/future tense, cases beyond nominative,
participles, passive voice, complex subordinate clauses

### Vocabulary

**Required:** прокидатися (to wake up), вмиватися (to wash face/hands), одягатися (to get dressed), снідати (to have breakfast), йти (to go — irregular), спочатку (first, at first), потім (then, next)
**Recommended:** збиратися (to get ready), повертатися (to return), навчатися (to study/learn), поспішати (to hurry), після цього (after this), нарешті (finally), вранці (in the morning), пізно (late)

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
