# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **12: This and That** (A1, A1.2 [My World]).

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
module: a1-012
level: A1
sequence: 12
slug: this-and-that
version: '1.1'
title: This and That
subtitle: Цей стіл, та книга — pointing at things
focus: grammar
pedagogy: PPP
phase: A1.2 [My World]
word_target: 1200
objectives:
- Use цей/ця/це (this) and той/та/те (that) with correct gender agreement
- Point at and identify objects using demonstratives + nouns from M08-M10
- Combine demonstratives with adjectives and colors (цей великий червоний стіл)
- Distinguish цей (near/this) from той (far/that)
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Shopping (extending M10 colors + M11 prices): — Скільки коштує ця
    сумка? — Яка? Ця червона? — Ні, та синя. — Та коштує двісті гривень. — А цей рюкзак?
    — Цей — сто п''ятдесят. Demonstratives emerge naturally: цей/ця = the one here,
    той/та = the one there.'
  - 'Dialogue 2 — In a room (extending M08-M09): — Що це? — Це мій стіл. — А те? —
    Те — крісло. — Цей стілець новий, а той — старий. Contrast near/far with objects
    already known.'
- section: Цей, ця, це (This)
  words: 300
  points:
  - 'Demonstrative pronouns follow the same gender pattern as мій/моя/моє and який/яка/яке:
    Цей стіл (m) — this table. Ця книга (f) — this book. Це вікно (n) — this window.
    Заболотний Grade 6 p.210: вказівні займенники цей, той змінюються за родами. At
    A1 we learn nominative only — other forms come later.'
  - 'Combining with adjectives and colors: Цей великий червоний стіл. Ця нова синя
    сумка. Це маленьке біле вікно. Word order: demonstrative + adjective(s) + noun
    (same as English!).'
- section: Той, та, те (That)
  words: 300
  points:
  - 'Той/та/те = that (farther away, or previously mentioned): Той стіл (m) — that
    table. Та книга (f) — that book. Те вікно (n) — that window. Contrast: Цей стілець
    новий, а той — старий. Warning: ''та'' also means ''and'' (like і/й). Context
    makes it clear: мама та тато (and) vs та книга (that book).'
  - 'Practical usage — pointing and choosing: Який стіл? — Цей чи той? (This one or
    that one?) Яка сумка? — Ця червона чи та синя? Яке вікно? — Це велике чи те маленьке?
    Note: ''Це'' as demonstrative (це вікно = this window) vs ''це'' as ''this is''
    (Це вікно = This is a window). Context makes it clear.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Gender agreement table — all patterns from A1.2 together: | | m | f | n | | мій
    | моя | моє | (M06 possessives) | який | яка | яке | (M09 questions) | цей | ця
    | це | (M12 this) | той | та | те | (M12 that) Same endings, same logic — Ukrainian
    is consistent! Self-check: Point at 3 things near you (цей/ця/це), then 3 things
    far away (той/та/те).'
vocabulary_hints:
  required:
  - цей, ця, це (this — m/f/n)
  - той, та, те (that — m/f/n)
  - чи (or — in questions)
  recommended:
  - ось (here is, look — pointing word)
  - там (there)
  - тут (here)
  - він, вона, воно (review from M08 — used for reference)
activity_hints:
- type: quiz
  focus: Цей, ця, or це? Choose the right demonstrative for each noun.
  items: 8
- type: fill-in
  focus: 'Complete: ___ книга нова, а ___ — стара. (ця/та)'
  items: 8
- type: match-up
  focus: Match цей/ця/це with мій/моя/моє and який/яка/яке — same gender!
  items: 6
- type: quiz
  focus: Той, та, or те? Point at the far object.
  items: 6
connects_to:
- a1-013 (Many Things)
prerequisites:
- a1-009 (What Is It Like?)
grammar:
- Demonstrative pronouns цей/ця/це (this) and той/та/те (that) — nominative only
- 'Gender agreement pattern: same as мій/який'
- 'Word order: demonstrative + adjective + noun'
- та = 'that' (demonstrative) vs та = 'and' (conjunction) — context distinguishes
register: розмовний
references:
- title: Заболотний Grade 6, p.210
  notes: Вказівні займенники цей, той змінюються за родами, числами, відмінками.
- title: Літвінова Grade 6, p.273
  notes: Full declension table for той — we use nominative only at A1.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: This and That
**Module:** this-and-that | **Phase:** A1.2 [My World]
**Textbook grades searched:** 1, 2, 3

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 36
> Бачу  Ї, ї. Чую  [й], [і].
> Ї ї
> у к р а ї
> У к р а
> К и ї в
> ї
> *
> н
> н а
> і
>  [ –•| = •– ] 
> сво
> тво
> мо
> Ї
> м
> ж
> жа
> жак
> сти
> їжа		
> 	
>   мої   	 	
> доїхав   
>  [ =•|–• ] 
>  [ –•| =•]  
>  [ –•| =•|–•– ] 
> Їжак, їжаченя
> Їздять по гриби щодня.
> Їжачиха помагає —
> Сироїжки їм збирає (нар. тв.).
> Скоромовка
> 	
> Прочитай скоромовку.
> 	 Які звуки позначає буква, виділена червоним 
> кольором? Вимов ці звуки. 
> Pidruchnyk.com.ua

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> ПРОТИЛЕЖНІ ЗА ЗНАЧЕННЯМ 
> СЛОВА
> РОЗПІЗНАЮ ПРОТИЛЕЖНІ ЗА ЗНАЧЕННЯМ СЛОВА
> Я — учителька
> Пригадай і розкажи 
> ; у класі.
> Я — учитель
> визначаю 
> складаю
> Слова можуть мати протилежні значення.
> Випиши парами протилежні за значенням слова.
> Жовтий котиться клубок, та клубок цей — без ниток. 
> Ані його розмотати, ні нового намотати. 
> Цілий день катається: 
> спершу піднімається, 
> згодом опускається. 
> Як це називається?
> 2| Пригадайте і назвіть заголовки казок 
> зі словами з протилежним значенням. 
> Допишіть назви

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 136
> Я ДРУЗІВ НЕ ПРОДАЮ
> Жила собі одна дівчинка і мріяла вона назбирати 
> більше за всіх папірців для крамниці, щоб усе-пре-
> все купити: і ляльку, і стрічку, і візочок для ляльки.
> Та найбільше за все вона хотіла купити собі друга,
> бо друзів у неї не було. Мала вона живого кролика, 
> і  дуже  їй  хотілося  його  продати.
> Сидить дівчинка й чекає — коли ж із нею хто-небудь 
> у «крамницю» пограється. А ніхто не приходить.
> І раптом бачить вона: йде хлопчик, а в руках у нього 
> кролик — такий самий, як у н

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 52
> Ц ц
> Бачу  Ц, ц (це). Чую  [ц], [ц′].
> а
> о
> у
> и
> і
> Ц
> ца
> цо
> цу
> ци
> ці
> а
> о
> у
> и
> і
> ац
> оц
> уц
> иц
> іц
> Ц
> цу
> ци
> це
> цві
> т
> ркун
> це
> дра
> сарка
> ці
> лина
> кавий
> 	
> Пограємо в гру «Так / ні».
> Летить 
> ? — _____ !
> Летить 
> ?  — _____!
> Летить 
> ? — ____!
> Летить 
> ? — _______!
> у
> г о р о б е
> в і р
> ц
> к
> и м б
> ц
> а
> ц
>  [ –  =•– |–•– ]  
>  [ –•| –•| –•= ] 
> ь
> л и
> н
> Pidruchnyk.com.ua

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> 3[ Запишіть віршовані рядки, додаючи слова 
> з довідки. Поставте наголос у словах.
> У портфелі в нас книжки, 
> пенали, зошити й ? .
> У кожного з нас є бажання 
> вирвзне слухати ? .
> Довідка
> Читання, ручки.
> Відгадай загадку, вивчи її і запиши з пам
> Паперовий кораблик щодня 
> перевозить для учнів знання. 
> Після плавання цей корабель 
> повертається в рідний портфель.
> • Постав наголос у словах. Потренуйся у 
> правильному вимовлянні виділених слів. 
> Загадай загадку своїм друзям.
> 5ДЗапиши спочатку слова, у яки

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 31
> 85.	
> Як перетворити кошеня на кишеню?
> Підказка. Нам допоможуть букви, які позначають голосні звуки, 
> та наголос.
> ?
> кишеѳня
> 86.	
> 1.	 Прочитай вислови та їх пояснення.
> 1. Повна кишеня — багато грошей. 2. Лазити по кишенях — 
> красти гроші. 3. Класти до своєї кишені — привласнювати чужі 
> гроші. 4. Перепадати в кишеню — мати грошовий прибуток.
> 2.	 Дослідиѳ виділені слова. Це споріднені слова чи форми одного 
> слова? Чому ти так гадаєш?
> 3.	 Спиши два вислови та їх пояснення. Познач закінчення у виді

## Цей, ця, це (This)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 16
> Й й
> Бачу Й, й (йот). Чую  [й].
> а й в а
>  [ •  =   |  –• ]
> а й с т р и
> * а й в о р о
> а
> о
> и
> і
> Й
> га
> ми
> рі
> Й
> н о к
> лій- 
> 	
> ліній-
> 	
> май- 
> чай- 
> 	
> гай- 
> 	
> чай- 
> мий	
> лий 	
> чай	
> грай
> вимий	
> долий	
> чайник	
> зіграй
> ай
> ой
> ий
> ій
> а
> о
> і
> і
> ч
> й
> д
> м
> й
> Pidruchnyk.com.ua

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> 36
> Запиши слова з буквою ї. Визнач звуки, які позначає буква ї.
> Мій — мої, твій — твої, вія — вії, лілія — лілії, лінія — лінії.
>  
> Утвори і запиши речення за зразком.
> Зразок. Колюче їжаченя з’їло слимака.
> Колючий
> Колюча
> Колюче
> Колючі
> їжак
> їжачиха
> їжаченя
> їжаки
> їсть
> з’їла
> з’їло
> їдять
> слимака.
> жука.
> равлика.
> черв’яка.
>  
> Редагуємо
> Їжак і жаба допомагають 
> садівнику поїдати комах. 
>  
> Запиши речення на вибір, у якому: 1) пояснюється, чому їжак 
> не робить запаси на зиму; 2) описується поведінка їжачка

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 150
>  МЕДIАВІКОНЦЕ: 
> мініпроєкт —
> колаж «Про мене»
> Хто побачить твій колаж? Обговоріть у групах,
> як краще представити колажі. Зверніть увагу, що в
> цій творчій роботі ви можете давати волю своїй
> фантазії: приклеювати фотографії, малюнки, тексти, 
> дрібні предмети…
> У цьому проєкті кожен/кожна зможе виявити свою твор-
> чість по-різному, розповідаючи про себе, свою родину. 
> Навіть придумати інтерв’ю про себе як друга/подружку, 
> свої захоплення, мрії.
> Розповісти про улюблені предмети. 
> Порадити прочитат

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 17
> — У мене скоро день народження. 
> Допоможи вибрати страви для свят-
> кового обіду.
> — Не знаю, що тобі порадити! Така 
> смакота! 
> Йшов до річки звіробій,
> Похвалявся: — Я такий —
> Наче сонце, золотий, 
> Всім люблю допомагати,
> Вмію добре лікувати,
> А ще є у мене — от
> Буква «Й», що зветься «ЙОТ».
> Лариса Верьовка
> бульйон
> піца
> «Казковий 
> метелик»
> «Веселий 
>   зайчик»
> чай
> какао
> коктейль
> «Злий 
> пес»
> «Мудра 
> сова»
> 	
> Вибери страви, у назвах яких є й.
> Pidruchnyk.com.ua

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> 92
> Текст 2. На письмовому столі Іванка жив 
> пенал. Він був великий і  серйозний. Жодна 
> маленька гумка чи гострий олівець не спере-
> чалися з ним. У п’ятницю в пенал поклали ручку. Автоматичну 
> і блискучу. Ручка всім посміхалася і віталася. А пенал злився. 
> «Немає чого радіти», — скрипів він. За тиждень ручку дістали 
> з пеналу. Її не було день, два, три. Пенал сумував, що немає 
> блискучої ручки, яка посміхається. А коли ручка повернулася 
> на місце, з  подивом і  захопленням слухав її історію. 
> Те

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> Добери свій 
> заголовок.
> А що ти напишеш 
> на цю тему?
>   Назвіть у тексті його частини.
> 	 	
>   Назвіть у тексті його частини.
> 	 	
> 11   Прочитайте текст учениці. Доведіть, що це есе.
> 	 	
> 12   Прочитайте. Поміркуйте, чи правильно учень побудував текст-
> есе. Свої міркування доведіть.
> 	 	
> 13   Склади і запиши невеликий твір-есе на тему «Яким (якою) 
> я мрію стати в майбутньому?». Пам’ятай про те, що в тексті 
> мають бути твої розмірковування (думки).
> МОЯ  ЗАПОВІТНА  МРІЯ
> У кожного є своя заповітна м

## Той, та, те (That)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 86
> Бачу Т, т (те). Чую  [т], [т'].
> т о р т
> т * л * п а н и
> к і т
>  [ –•  –  – ]
>  [  =  • –  ]
> а
> о
> у
> и
> і
> Т
> та
> то
> ту
> ти
> ті
> а
> о
> у
> и
> і
> ат
> от
> ут
> ит
> іт
> Т
> ті-	 	
> 	
>      тро-	          	
>   та-
>              -то	 	
>    	
>      -та	        	         -ти	
> Та-то  ку-пив  Ро-ма-но-ві 
>  .
> — Тім! Тім! — по-кли-кав  Ро-ман 
> так-су. — На 
>  .
> Т т

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> НАВЧАЮСЯ ЗМІНЮВАТИ СЛОВА — 
> НАЗВИ ПРЕДМЕТІВ
> Я — учителька
> Прочитай і розкажи 
> у класі.
> один — багато^
> Я — учитель
> В українській мові слова можуть називати один 
> предмет або багато предметів.
> тварина 
> рослина
> Додай свої 
> слова.
> 32| Випишіть із лічилки Тамари Коломієць слова — назви 
> предметів.
> один
> багато
> £ Що не так на 
> малюнку?
> Біжить півень із причілка 
> і наспівує лічилку:
> — Раз-два — курчата.
> Три-чотири — зайчата. 
> П'ять-шість — гусаки.
> Сім-вісім — їжаки. 
> Дев'ять-десять — йде лисиця. 
> 

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Цей, ця, це (This)` (~300 words)
- `## Той, та, те (That)` (~300 words)
- `## Підсумок — Summary` (~300 words)
- `## Підсумок — Summary` (~150 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 10-20% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose. Introduce Ukrainian grammar terms bolded with translation on first use.
- UKRAINIAN CONTENT: Words and short phrases bolded inline: "The word **книга** (book) is feminine."
- TABLES: Vocabulary tables, word families, simple paradigm tables.
- STRUCTURAL RULE: Every paragraph is English. Ukrainian words/phrases appear inline bolded. Full Ukrainian sentences (3+ words with a verb) go in tables or bulleted example lists with English gloss.
Ukrainian sentences max 10 words.

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

GRAMMAR CONSTRAINTS (A1.2 — My World, M08-M14):
Noun gender, adjective agreement, plurals, numbers, demonstratives.

ALLOWED:
- Це + noun, У мене є/немає
- Adjective-noun agreement (nominative only)
- Numbers 1-1000
- Demonstratives цей/ця/це/ці
- Question words: Який? Яка? Яке? Скільки?
- Fixed verbal phrases from A1.1 (Мене звати, працювати)

BANNED: Verb conjugation (taught in A1.3), past/future tense, cases beyond nominative,
participles, passive voice, subordinate clauses

### Vocabulary

**Required:** цей, ця, це (this — m/f/n), той, та, те (that — m/f/n), чи (or — in questions)
**Recommended:** ось (here is, look — pointing word), там (there), тут (here), він, вона, воно (review from M08 — used for reference)

### Pronunciation Videos



---

### Style Reference (match this tone and structure)

Look at the text on this page. What you are seeing are letters. Now, say a word out loud. What you just produced is a sound. This distinction is the absolute foundation of the Ukrainian language. There is a golden rule taught to every Ukrainian student in the first grade: **Ми чуємо і вимовляємо звуки, а бачимо і пишемо літери**. We hear and pronounce sounds, but we see and write letters.

These friendly letters are **А**, **О**, **К**, **М**, and **Т**. Because they are so familiar, you can start reading real Ukrainian words immediately. Look at the word **мама**. It means mother, and you already know how to read it. Now look at **тато**. It means father.

*Note: English prose dominates. Ukrainian words appear bolded inline. Short Ukrainian sentences illustrate one concept at a time. No conjugated verbs. Tables and bulleted lists for vocabulary.*

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
