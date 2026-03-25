# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **36: Food and Drink** (A1, A1.6 [Food and Shopping]).

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
module: a1-036
level: A1
sequence: 36
slug: food-and-drink
version: '1.2'
title: Food and Drink
subtitle: Їжа і напої — what Ukrainians eat and drink
focus: vocabulary
pedagogy: PPP
phase: A1.6 [Food and Shopping]
word_target: 1200
objectives:
- Name common Ukrainian foods and drinks
- Use кава з молоком, чай з цукром as memorized chunks (NOT instrumental grammar)
- Talk about what you eat and drink daily
- Recognize iconic Ukrainian dishes (борщ, вареники, сало)
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — At home in the morning: — Що ти хочеш на сніданок? — Каву з молоком
    і хліб з маслом. — А я хочу чай з цукром і кашу. Food + drink combinations as
    chunks (з + noun = memorized phrase).'
  - 'Dialogue 2 — Talking about food preferences: — Що ти зазвичай їш на обід? — Суп
    і салат. — А на вечерю? — М''ясо з картоплею або рибу з рисом. Three meals: сніданок,
    обід, вечеря.'
- section: Їжа (Food)
  words: 300
  points:
  - 'Core food vocabulary by category: Хліб і каша: хліб, каша, рис, макарони. М''ясо
    і риба: м''ясо, курка, риба. Овочі: картопля, морква, цибуля, помідор, огірок.
    Фрукти: яблуко, банан, апельсин. Молочне: молоко, сир, масло, сметана, йогурт.
    Інше: яйце, цукор, сіль, олія.'
  - 'Ukrainian iconic foods (cultural note): борщ (beet soup — national dish), вареники
    (filled dumplings), сало (cured pork fat), галушки (dumplings), деруни (potato
    pancakes). These words are cultural identity, not just vocabulary.'
- section: Напої (Drinks)
  words: 300
  points:
  - 'Core drink vocabulary: Гарячі: кава, чай. Холодні: вода, сік, компот, лимонад.
    Молочні: молоко, кефір. Алкогольні: пиво, вино (for recognition). Key chunk pattern:
    [drink] з [addition] — memorized, NOT grammar: кава з молоком, чай з цукром, чай
    з лимоном, вода з газом.'
  - 'Why ''з + noun'' is a chunk, not grammar: At A1, learn кава з молоком as a fixed
    phrase, like ''coffee with milk.'' The instrumental case ending (-ом, -ою) is
    grammar for A2. For now: memorize the whole phrase. Say it as one unit.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Food and drink toolkit: Що ти хочеш? — Каву з молоком. / Хліб з маслом. Що ти
    їш на сніданок / обід / вечерю? Three meals: сніданок (breakfast), обід (lunch),
    вечеря (dinner). Self-check: Name 5 foods and 3 drinks you like. Name one Ukrainian
    dish and why it matters.'
vocabulary_hints:
  required:
  - їжа (food, f)
  - напій (drink, m)
  - хліб (bread, m)
  - кава (coffee, f)
  - чай (tea, m)
  - вода (water, f)
  - молоко (milk, n)
  - сік (juice, m)
  - м'ясо (meat, n)
  - риба (fish, f)
  - суп (soup, m)
  - сніданок (breakfast, m)
  - обід (lunch, m)
  - вечеря (dinner, f)
  recommended:
  - борщ (beet soup, m)
  - вареник (dumpling, m)
  - каша (porridge, f)
  - сир (cheese, m)
  - масло (butter, n)
  - яйце (egg, n)
  - картопля (potato, f)
  - цукор (sugar, m)
  - сіль (salt, f)
  - сметана (sour cream, f)
  - компот (compote, m)
  - курка (chicken, f)
activity_hints:
- type: match-up
  focus: Match Ukrainian food and drink words to English
  items: 10
  pairs:
  - хліб: bread
  - м'ясо: meat
  - риба: fish
  - молоко: milk
  - вода: water
  - сік: juice
  - сніданок: breakfast
  - обід: lunch
  - вечеря: dinner
  - суп: soup
- type: group-sort
  focus: Categorize into Їжа (Food) and Напої (Drinks)
  items: 10
  groups:
  - name: Їжа
    items:
    - хліб
    - м'ясо
    - риба
    - суп
    - каша
  - name: Напої
    items:
    - кава
    - чай
    - вода
    - сік
    - молоко
- type: fill-in
  focus: Use 'з + noun' as memorized chunks for additions
  items: 6
  blanks:
  - Я хочу каву {з молоком}.
  - Вона п'є чай {з цукром}.
  - Він їсть хліб {з маслом}.
  - Я люблю чай {з лимоном}.
  - Дайте, будь ласка, воду {з газом}.
  - Ми їмо м'ясо {з картоплею}.
- type: quiz
  focus: Identify meals and iconic Ukrainian dishes
  items: 6
  questions:
  - Що ми їмо вранці? (сніданок / обід / вечерю)
  - Що ми їмо ввечері? (вечерю / сніданок / обід)
  - Традиційний український суп — це... (борщ / каша / вода)
  - 'Українська страва з тіста і картоплі або сиру: (вареники / сало / хліб)'
  - 'Популярний холодний напій з фруктів: (компот / борщ / кава)'
  - Що ми їмо вдень? (обід / сніданок / вечерю)
connects_to:
- a1-037 (I Eat, I Drink)
prerequisites:
- a1-035 (Checkpoint — Places)
grammar:
- з + noun as memorized chunk (NOT instrumental grammar)
- Що ти хочеш? — review хотіти from M19
- No new grammar — vocabulary-focused module
register: розмовний
references:
- title: ULP Season 1, Episodes 11-13
  url: https://www.ukrainianlessons.com/episode11/
  notes: Anna introduces food and drink vocabulary, cafe ordering.
- title: State Standard 2024, Topic 3 (ресторан)
  notes: 'Communicative situation: restaurant, food, ordering.'

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Food and Drink
**Module:** food-and-drink | **Phase:** A1.6 [Food and Shopping]
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
> 154
> Сіль необхідна для нормального функціювання нашого 
> організму, як вода, їжа та кисень. Однак, уживаючи її, треба 
> знати міру. Добова норма споживання солі для людини — 5–6 г 
> на день у країнах із помірним кліматом та до 15–20 г — 
> зі спекотним. Упродовж одного дня, щоб отримати норму 
> солі, треба з’їсти 16 кг картоплі, або 200 кг яблук, або 5 кг 
> телятини. Тож досолювати їжу — правильно. Ми не контро-
> люємо, скільки солі споживаємо, інколи пересолюємо стра-
> ви, купуємо готові продукти, у яки

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> 91
> 5. Прочитай заголовок тексту. Чи знаєш ти, що означає цей 
> вислів? Прочитай текст, щоб перевірити свою думку.
> Шведський стіл
> У давнину шведи відвідували своїх родичів, до-
> лаючи велику відстань поганими дорогами. Їм було 
> не до очікування прибуття інших гостей. Тому гос-
> подарі ставили на стіл різні страви. Подавали їх
> у великих мисках, і кожен міг брати стільки, скіль-
> ки хотів. Це давало змогу втамувати перший голод 
> і залишало час для спілкування. Іноземці називали 
> такий спосіб пригощання

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

> **Source:** unknown, Grade 6
> **Score:** 0.33
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

## Їжа (Food)

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
> 1 Кушир — рослина, що росте у воді; водяна кропива. 2 Жлукто, ринка, макітра — види посуду.

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> § 50. Повсякденне життя Риму за часів республіки  155
> 4. Харчування
> Раціон римлян залежав від достатку. Пе-
> ресічні римляни їли пшеничний хліб та 
> кашу. З  овочів споживали капусту, ріпу, 
> цибулю, редьку та боби, а  з молочних про-
> дуктів  — козиний або овечий сир. Пили 
> розведене водою вино. М’ясо їли дуже рідко. Переважно це була свинина, із якої також 
> готували численні види ковбас. Тривалий час 
> бідні римляни мали городи. Однак коли кіль-
> кість населення Рима збільшилася і  місця 
> почало бра

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> Насправді рибі під водою не мокро. Та й замерзнути вона 
> (не)боїться, бо не надто мілкі річки і ставки не зам(е/и)рзають до 
> дна. Тож під кригою риби ж(е/и)вуть своїм риб(’)ячим жи(т/тт)ям.
> 2. Поясни орфограми. Спиши один абзац на вибір, розкриваючи 
> дужки.
> 3. Над кожним дієсловом укажи число.
> 281. Прочитай іменники. Добери до них спільнокореневі дієслова, 
> ужиті у формі однини та множини. Запиши за зразком.
> Зразок. Галас — галасую, галасуємо.
> Галас, біг, плавання, бачення, турбота, стрибок, сто

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 14
> ТЕКСТ. РЕЧЕННЯ. СЛОВО (ПОВТОРЕННЯ)
> 2. Прочитайте речення та виконайте завдання. У віддаленій перспективі в таких пернатих можуть сформуватися так 
> звані «крила ангела», що стирчать у горизонтальній площині, а не обтічно 
> лежать на тілі. Більшість птахів із цією вадою не вміють літати. Хліб — шкідлива їжа для диких водоплавних птахів, що не має ніякої 
> поживної цінності, окрім калорій. Постійне підгодовування хлібом зму-
> шує їх покладатися на людину як на джерело корму, а не на свій природ-
> ни

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 88
> транспорту у великих містах, фактично варіант залізниці, 
> лінії якого можуть бути розташовані під землею й на землі; 
> автомобіль громадського користування з оплатою проїзду 
> за лічильником (таксометром).
> 205   Ознайомтеся зі змістом таблиці. Доповніть її власними при -
> к ладами.
> Рід незмінюваних іменників
> Правило
> Чоловічий рід
> Жіночий рід
> Середній рід
>  Назви осіб
> кюре, рантьє, 
> денді, конфе-
> рансьє, маестро 
> леді, мадам, 
> міледі, міс, 
> пані, фрау
>   Назви тварин 
> і птахів 
> (якщо стать 
> не вказ

## Напої (Drinks)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 109
> 4. Прочитай етикетку улюбленого напою китайців. Розка-
> жи, яку  інформацію вона  містить.  Що в ній для  тебе  як
> споживача  найважливіше?
> 4
> 5. Родзинка дізналася, де винайшли чай. Прочитай і ти.
> Вирощувати й заварювати чай почали в Китаї. 
> А сталося це, коли випадково листок чайного куща 
> впав у чашку з окропом. 
> Чай буває білий, зелений, чорний. Усі вони
> з листя одного куща, який називається «Каме-
> лія китайська». Тільки сушать листя по-різному. 
> Тому й виходить різний смак і властивості ч

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 51
> Спільнокореневі слова
> (різні слова)
> чай
> чайний
> чаювати
> лимон
> лимонний
> лимонад
> Форми слова 
> (одне слово з різними  
> закінченнями)
> чай
> чаю
> чаєм
> лимон
> лимона
> лимоном
> Зверніть увагу!
> У результаті чергування звуків корінь може видозміню-
> ватися (мати різний звуковий склад). НАПРИКЛАД: 1) друг – 
> друзі – дружний; 2) рідня – родина; 3) вітер – вітру.
> 110.	І. Згрупуйте спільнокореневі слова й запишіть. Доберіть до кож-
> ної групи слів ще по одному спільнокореневому. Позначте в усіх сло-
> вах корені, за

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> • прикликати урожай, успіх, лад у сім’ї

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Їжа (Food)` (~300 words)
- `## Напої (Drinks)` (~300 words)
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

PLAN-AWARE EXEMPTIONS: The following bans are RELAXED for this module because the plan explicitly teaches these constructs: Instrumental case (plan teaches it). Exception: If a grammar construct appears in this module's plan grammar list or objectives, it is ALLOWED for this module.

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

**Required:** їжа (food, f), напій (drink, m), хліб (bread, m), кава (coffee, f), чай (tea, m), вода (water, f), молоко (milk, n), сік (juice, m), м'ясо (meat, n), риба (fish, f), суп (soup, m), сніданок (breakfast, m), обід (lunch, m), вечеря (dinner, f)
**Recommended:** борщ (beet soup, m), вареник (dumpling, m), каша (porridge, f), сир (cheese, m), масло (butter, n), яйце (egg, n), картопля (potato, f), цукор (sugar, m), сіль (salt, f), сметана (sour cream, f), компот (compote, m), курка (chicken, f)

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
