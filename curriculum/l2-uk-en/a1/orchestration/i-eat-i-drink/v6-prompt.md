# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **37: I Eat, I Drink** (A1, A1.6 [Food and Shopping]).

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
module: a1-037
level: A1
sequence: 37
slug: i-eat-i-drink
version: '1.2'
title: I Eat, I Drink
subtitle: Я їм хліб, п'ю каву — accusative for what you eat and drink
focus: grammar
pedagogy: PPP
phase: A1.6 [Food and Shopping]
word_target: 1200
objectives:
- Conjugate їсти and пити in present tense
- Use accusative case for inanimate direct objects (Я їм хліб, п'ю каву)
- Recognize feminine accusative ending change (-а → -у): кава → каву, вода → воду
- Describe eating and drinking habits using accusative
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Breakfast conversation: — Що ти їш на сніданок? — Я їм кашу і п''ю
    каву. — А Олена? — Вона їсть хліб з маслом і п''є чай. — А діти? — Вони їдять
    яйця і п''ють молоко. Full conjugation of їсти and пити in natural context.'
  - 'Dialogue 2 — At lunch: — Що ви їсте на обід? — Ми їмо суп і салат. — А що п''єте?
    — Ми п''ємо воду або сік. — Я теж хочу суп. — Добре, замовляй! Review of їсти/пити
    with plural subjects.'
- section: Їсти і пити (To Eat and To Drink)
  words: 300
  points:
  - 'Conjugation of їсти (irregular — NOT Group I or II): я їм, ти їси, він/вона їсть,
    ми їмо, ви їсте, вони їдять. Conjugation of пити (Group I): я п''ю, ти п''єш,
    він/вона п''є, ми п''ємо, ви п''єте, вони п''ють. Both are essential daily verbs
    — high frequency.'
  - 'Ukrainian school approach (Grade 4 — знахідний відмінок): ''Бачу що? кого?''
    — the accusative answers ''what do I see/eat/drink?'' Я їм (що?) хліб. Я п''ю
    (що?) каву. The question що? triggers accusative for inanimate objects.'
- section: Знахідний відмінок — неживе (Accusative Inanimate)
  words: 300
  points:
  - 'Accusative for inanimate nouns — what changes: Masculine inanimate: NO CHANGE
    (= nominative). хліб → хліб (Я їм хліб), суп → суп (Я їм суп), сік → сік (Я п''ю
    сік). Neuter: NO CHANGE (= nominative). молоко → молоко (Я п''ю молоко), яйце
    → яйце (Я їм яйце).'
  - 'Feminine -а → -у (THE key change at A1): кава → каву (Я п''ю каву), вода → воду
    (Я п''ю воду), риба → рибу (Я їм рибу), каша → кашу (Я їм кашу), картопля → картоплю
    (Я їм картоплю). Pattern: feminine nouns ending in -а change to -у, ending in
    -я change to -ю. This is the ONLY accusative change learners need now.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Accusative inanimate summary: Masculine/Neuter: no change (хліб, молоко stay
    the same). Feminine -а → -у, -я → -ю (кава → каву, картопля → картоплю). Test:
    Я їм ___ (риба → рибу). Я п''ю ___ (вода → воду). Self-check: Say 3 things you
    eat and 3 things you drink today. Use the correct accusative form for each.'
vocabulary_hints:
  required:
  - їсти (to eat — irregular)
  - пити (to drink)
  - їм (I eat)
  - п'ю (I drink)
  - каву (coffee — accusative)
  - воду (water — accusative)
  - рибу (fish — accusative)
  recommended:
  - кашу (porridge — accusative)
  - картоплю (potato — accusative)
  - сметану (sour cream — accusative)
  - їсть (he/she eats)
  - п'є (he/she drinks)
  - їдять (they eat)
  - п'ють (they drink)
activity_hints:
- type: fill-in
  focus: Form the accusative case for feminine (-а/-я → -у/-ю) and masculine/neuter
    (no change)
  items: 8
  blanks:
  - Я їм (риба) {рибу}.
  - Вона п'є (вода) {воду}.
  - Він їсть (хліб) {хліб}.
  - Ми п'ємо (молоко) {молоко}.
  - Вони їдять (каша) {кашу}.
  - Ти п'єш (кава) {каву}.
  - Я їм (суп) {суп}.
  - Вона їсть (картопля) {картоплю}.
- type: quiz
  focus: Select the correct accusative form to complete the sentence
  items: 6
  questions:
  - Я п'ю... (каву / кава / кави)
  - Він їсть... (рибу / риба / рибі)
  - Ми п'ємо... (сік / соку / соком)
  - Вона їсть... (м'ясо / м'ясу / м'яса)
  - Вони п'ють... (воду / вода / воді)
  - Ти їш... (кашу / каша / каші)
- type: fill-in
  focus: Conjugate the verbs їсти (irregular) and пити (Group I)
  items: 8
  blanks:
  - Я {їм} суп.
  - Ми {п'ємо} чай.
  - Вона {їсть} хліб.
  - Вони {п'ють} воду.
  - Ти {їси} рибу?
  - Ви {п'єте} каву?
  - Він {п'є} сік.
  - Вони {їдять} кашу.
- type: group-sort
  focus: Sort nouns based on how they change in the accusative case (inanimate)
  items: 8
  groups:
  - name: Змінюється (-у/-ю)
    items:
    - кава
    - вода
    - риба
    - каша
  - name: Не змінюється (як у називному)
    items:
    - хліб
    - сік
    - молоко
    - м'ясо
connects_to:
- a1-038 (At the Cafe)
prerequisites:
- a1-036 (Food and Drink)
grammar:
- 'Accusative inanimate: masculine/neuter = nominative, feminine -а→-у, -я→-ю'
- Conjugation of їсти (irregular) and пити (Group I)
- Question що? as accusative trigger for inanimate
register: розмовний
references:
- title: ULP Season 1, Episode 32
  url: https://www.ukrainianlessons.com/episode32/
  notes: Accusative case introduction — inanimate objects.
- title: 'Grade 4 textbook: Знахідний відмінок (Заболотний)'
  notes: 'Ukrainian school approach: бачу що? кого?'

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: I Eat, I Drink
**Module:** i-eat-i-drink | **Phase:** A1.6 [Food and Shopping]
**Textbook grades searched:** 4, 5, 6

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 103
> 5. Із тексту про японську мову випиши в колонку дієс-
> лова, вжиті у множині. Утвори від них форму однини
> і  запиши  у  другу  колонку.
> 5
> 6. Напиши повідомлення японським школярам про україн-
> ську мову (3–4 речення).
> 6
> 7. Прочитай текст. Випиши в колонку дієслова. Зміни їх
> за числами й запиши поряд. Напиши, які страви з рису 
> ти знаєш. Які тобі доводилося їсти? 
> Рис називають японським хлі-
> бом. Найчастіше японці їдять 
> його без будь-яких приправ, 
> масла і навіть солі. Вони вважа-
> ють, що рис

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

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> Орієнтовний план
> 1. Свині та кабани —жахливі нечупари.
> 2. Дивний кабанчик.
> 3. Змова проти Чепурунчика.
> 4. Кмітливий Чепурунчик.
> 5.......
> 290. 1. Прочитайте переказ одні одним. Обговоріть, що вдало­
> ся найкраще, а над чим потрібно попрацювати.
> 2. Чи можна назвати спільнотою твій клас? Свої міркування 
> розпочинай так:
> Я гадаю, що мій клас можна / не можна назвати спіль­
> нотою, тому що.... Отже,....
> ( ЗМІНЮВАННЯ ДІЄСЛІВ У ТЕПЕРІШНЬОМУ ЧАСІ )
> 291. 1. Пригадай, яку дію називають дієслова теперішнього

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 236
> Відомості із синтаксису й пунктуації. Складне речення
> 4. Яка інформація з  тексту була для вас новою?
> 5. Пригадайте, які хімічні досліди на кухні (з перерахованих у тексті чи інші) 
> проводили ви . Розкажіть про це друзям, використовуючи складні речення .
> Вправа 380
> 1. Прочитайте рекомендації щодо здорового сніданку .
> СМУЗІ
> z
> z яблуко — 1 шт.,
> z
> z банан — 1 шт.,
> z
> z склянка води,
> z
> z кілька заморожених ягід 
> (на ваш смак),
> z
> z ложка лляного насіння.
> ОМЛЕТ З ОВОЧАМИ 
> ТА ЗЕЛЕННЮ
> z
> z яйця — 1—2

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 160
> 1.	Прочитайте діалог і виконайте завдання.
> — Олю, скільки піци тобі відрізати? — запитала мама.
> — Невеличкий шматок. 
> — А тобі, Денисе? 
> — Одну четверту частину.
> А.	  Хто з дітей назвав не приблизну, а точну кількість? 
> Б.	 Як називають числівник, яким передано точну кількість у діалозі?
> У дробових числівниках першу частину (чисельник) відмінюємо, як 
> кількісний числівник, а другу (знаменник) — як порядковий. Чисель­
> ник уживаємо в називному відмінку, а знаменник — у родовому мно­
> жини: дві

## Їсти і пити (To Eat and To Drink)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 89
> Одного разу йде Дядько Федір сходами й бутерброд 
> їсть. А на вікні кіт сидить (...). 
> — А звідки ти знаєш, як мене звати?
> — Я в нашому будинку всіх знаю: на горищі живу й мені 
> все видно, — відповідає кіт (За Е. Успенським).
> 	 Прочитай виділені слова. Спиши перший абзац, уникаючи 
> повторів. До якої частини мови належать слова, якими ти замі-
> нив (замінила) іменники та числівники?
> 	 Випиши займенники із частини тексту, позначеної зеленою 
> рискою.
> 215.		Прочитай слова. До яких частин мови вони

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 232
> Відомості із синтаксису й пунктуації. Складне речення
> Складне речення
> Вправа 374
> 1. Прочитайте речення .
> Іван добре їсть. Іван добре 
> працює.
> Хто добре їсть, той добре 
> працює (Нар. тв.).
> Наше здоров’я залежить 
> від продуктів. Ми щодня спо-
> живаємо продукти.
> Наше здоров’я залежить 
> від продуктів, які ми спожи-
> ваємо щодня.
> 2. Перепишіть і підкресліть у реченнях граматичні основи (підмети й при-
> судки) .
> 3. Зробіть висновки, чим відрізняються речення за  будовою і  за  змістом .
> За будовою ре

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 177
>  Відповідно до запитань сформулюйте особисті цілі. 
> 448   Розгляньте схему. Що вам було відоме, а що нове? Доберіть до 
> кожного пункту власні приклади. 
> З великої букви пишемо займенники Ви, Ваш (Ваша) 
> як форму ввічливості у звертанні до однієї конкретної 
> особи в листах, привітаннях, запрошеннях, в офіцій-
> них документах. 
> Дієслово-присудок із пошанним Ви вживаємо у формі 
> множини. Присудок, виражений прикметником, при 
> пошанному Ви може бути в однині і множині.
> 449   Прочитайте речення з

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> [ В українській мові займенників небагато, але вони 
> і дуже важливі: зв’язують речення між собою; допома­
> гають уникнути повторів. Під час відмінювання за- 
> [ йменники набувають інших форм: я, ти, ми, воно, 
> І вони — мені, мною, тебе, тобі, нас, ними, йому, їх, їм.
> 272. Прочитайте текст. Перекажіть.
> Дядько Федір пригостив кота й 
> запитав:
> — А звідки ти знаєш, як мене 
> звати?
> Кіт відповідає:
> — Я в  нашому будинку всіх 
> знаю: на горищі живу й мені все 
> видно. Тільки тепер моє горище 
> ремонтують і

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> Зв’язок між реченнями тексту виявляється й у дотриманні граматич-
> них форм окремих слів. Виділене слово йому (у другій колонці) треба 
> замінити на займенник жіночого роду їй, щоб вийшов зв’язний текст 
> (сипуха — вона, сипусі — їй). Речення в тексті поєднуються інтонаційно. Заголовок тексту стисло передає його тему або головну думку.

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> І якраз у яму 
> втрапить. А ми вже вириємо, постараємося.

## Знахідний відмінок — неживе (Accusative Inanimate)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 43
>  
> 106.		Розглянь малюнок. Прочитай текст, 
> уставляючи пропущені іменники за 
> змістом у потрібному відмінку.
> У Лесі є (хто?) ... . Дівчинка дуже 
> любить (кого?) ... . Вона дає їсти 
> й пити (кому?) ... . Потім Леся гуляє 
> (з ким?) ... . (на кому?) ... виблиску-
> ють медалі. Він — переможець зма-
> гань.
> 	 Запиши доповнений текст. Назви відмін-
> ки іменників. У яких відмінках немає слів 
> у тексті?
> 107.		Розгляньте таблицю та обговоріть її зміст. 
> Відмінок
> Питання
> Приклади  (однина)
> Н. в.
> Р. в.
> Д. в

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 136
> ОРФОГРАФІЯ 
> 2.	Перепишіть слова, уписуючи на місці крапок, де потрібно, пропущену 
> літеру. 
> Орлин..ий, качин..ий, від..звеніти, реформен..ий, клятвен..ий, осві-
> чен..ість, від..зеркалення, буквен..ий, міськ..ом, розніс..я, воз..’єднання, 
> істин..ий, годин..ик, від..ячити, роз..танути, перед..ень, спорт..овари, 
> від..окремити.  
> 3.	Запишіть у три колонки слова зі збігом однакових приголосних на 
> межі: 1) префікса й кореня; 2) кореня та суфікса; 3) частин складного 
> слова. 
> Законний, відділити

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 57
> 57
> § 30.  Похідні  і  непохідні  слова.  Твірне  слово
> 4.	 Виконайте завдання в тестовій формі.
> 1.	 Непохідним є слово
> А	 чайник
> Б	 лампа
> В	 несмак 
> Г	 дубок


... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Їсти і пити (To Eat and To Drink)` (~300 words)
- `## Знахідний відмінок — неживе (Accusative Inanimate)` (~300 words)
- `## Підсумок — Summary` (~300 words)
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

GRAMMAR CONSTRAINTS (A1.6 — Food & Shopping, M37-M43):
Instrumental з, accusative objects, genitive quantities.

ALLOWED:
- Instrumental case with 'з' (кава з молоком)
- Accusative inanimate and animate objects
- Genitive for quantities (кілограм цукру)
- All cases from previous phases
- All present tense verbs

BANNED: Past/future tense, dative (until A1.7),
participles, passive voice, complex subordination

### Vocabulary

**Required:** їсти (to eat — irregular), пити (to drink), їм (I eat), п'ю (I drink), каву (coffee — accusative), воду (water — accusative), рибу (fish — accusative)
**Recommended:** кашу (porridge — accusative), картоплю (potato — accusative), сметану (sour cream — accusative), їсть (he/she eats), п'є (he/she drinks), їдять (they eat), п'ють (they drink)

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
