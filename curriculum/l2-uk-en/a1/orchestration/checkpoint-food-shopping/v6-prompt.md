# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **41: Checkpoint: Food and Shopping** (A1, A1.6 [Food and Shopping]).

**Target: 1000–1500 words** of prose (Ukrainian examples count toward word total, headings and exercise placeholders do not).

---

## Step 1: Pacing Plan (output this FIRST)

Before writing any content, output a `<pacing_plan>` block. Evaluate each section from the plan and commit to a word budget. This prevents frontloading early sections and rushing later ones.

```
<pacing_plan>
Section 1 "Title": ~XXX words — [1-sentence content focus]
Section 2 "Title": ~XXX words — [1-sentence content focus]
...
Summary: ~150 words
Total: 1000+ words
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
7. **Hit the word target** — you MUST write 1000–1500 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
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
module: a1-041
level: A1
sequence: 41
slug: checkpoint-food-shopping
version: '1.2'
title: 'Checkpoint: Food and Shopping'
subtitle: Can you order food and buy things in Ukrainian?
focus: review
pedagogy: PPP
phase: A1.6 [Food and Shopping]
word_target: 1000
objectives:
- Demonstrate food and drink vocabulary in context
- Use accusative case correctly for both inanimate and animate nouns
- Order at a cafe and buy things at a shop/market
- Combine all A1.6 skills in connected scenarios
content_outline:
- section: Що ми знаємо? (What Do We Know?)
  words: 200
  points:
  - 'Self-check covering M36-M40: Can you name 10 foods and 5 drinks? (M36) Can you
    say what you eat/drink using accusative? (M37) Can you order at a cafe? (M38)
    Can you ask prices and buy things? (M39) Can you use accusative for people? (M40)'
- section: Читання (Reading Practice)
  words: 250
  points:
  - 'A short Ukrainian text using vocabulary from M36-M40. Content: Anna goes to the
    market, buys food, then goes to a cafe. She orders борщ and каву з молоком, asks
    for the bill, then meets a friend and introduces her brother. Uses food vocabulary,
    accusative inanimate and animate, cafe phrases.'
- section: Граматика (Grammar Summary)
  words: 200
  points:
  - 'Key patterns from A1.6: 1. Food/drink vocabulary: їжа, напої, meals (M36) 2.
    Accusative inanimate: masc = nom, fem -а→-у (M37) 3. Ordering: Мені каву, будь
    ласка (M38) 4. Prices: Скільки коштує? Гривня/гривні/гривень (M39) 5. Accusative
    animate: fem -а→-у, masc = genitive (M40) 6. Chunks: кава з молоком, кілограм
    яблук (M36, M39)'
- section: Діалог (Connected Dialogue)
  words: 200
  points:
  - 'A day of food and shopping: — Що ти їш на сніданок? — Я їм кашу і п''ю каву з
    молоком. — Потім іду на ринок. Скільки коштують помідори? — Тридцять гривень.
    — Дайте кілограм, будь ласка. — Потім у кафе: Мені борщ і воду, будь ласка. —
    О, я бачу Олену! Олено, привіт! Ти знаєш мого брата? Combines all A1.6 skills
    in one realistic day.'
- section: Підсумок — Summary
  words: 150
  points:
  - 'A1.6 achievement summary: You can talk about food and drinks. You can use accusative
    for things AND people. You can order at a cafe and pay. You can shop at a market
    and ask prices. Next: A1.7 — Communication (phone, email, making plans).'
vocabulary_hints:
  required: []
  recommended: []
activity_hints:
- type: quiz
  focus: 'Accusative check: choose correct form for inanimate AND animate nouns'
  items:
  - question: Я їм ___.
    options:
    - салат
    - салата
    - салату
  - question: Я бачу ___.
    options:
    - брата
    - брат
    - брату
  - question: Я п'ю ___.
    options:
    - воду
    - вода
    - води
  - question: Я знаю ___.
    options:
    - Олену
    - Олена
    - Олени
  - question: Я люблю ___.
    options:
    - борщ
    - борща
    - борщу
  - question: Я чекаю ___.
    options:
    - друга
    - друг
    - другу
  - question: Я купую ___.
    options:
    - хліб
    - хліба
    - хлібу
  - question: Я бачу ___.
    options:
    - лікаря
    - лікар
    - лікарю
  - question: Я їм ___.
    options:
    - піцу
    - піца
    - піци
  - question: Я люблю ___.
    options:
    - маму
    - мама
    - мами
- type: fill-in
  focus: Complete the cafe + market dialogue with correct forms
  items:
  - — Що ти їш на сніданок? — Я їм {кашу|каша|каші} і п'ю каву.
  - — Потім іду на ринок. Скільки {коштують|коштує|коштувати} помідори?
  - — Тридцять {гривень|гривні|гривня}.
  - — Дайте {кілограм|літр|пляшку} яблук, будь ласка.
  - '— Потім у кафе: {Мені|Я|Меня} борщ і воду, будь ласка.'
  - — Рахунок, будь ласка. Можна {карткою|картка|картки}?
  - — О, я бачу {Олену|Олена|Олени}! Олено, привіт!
  - — Ти знаєш мого {брата|брат|братом}?
- type: group-sort
  focus: 'Sort accusative forms: inanimate (що?) vs animate (кого?)'
  groups:
  - name: Inanimate (що?)
    items:
    - борщ
    - хліб
    - сік
    - чай
    - сир
  - name: Animate (кого?)
    items:
    - брата
    - лікаря
    - сусіда
    - друга
    - вчителя
- type: quiz
  focus: What do you say? Match shopping/cafe situations to correct phrases
  items:
  - question: 'You want to order coffee:'
    options:
    - Мені каву, будь ласка.
    - Скільки коштує?
    - Тут вільно?
  - question: 'You ask for the price:'
    options:
    - Скільки коштує?
    - Можна карткою?
    - Що ви рекомендуєте?
  - question: 'You want to pay with a card:'
    options:
    - Можна карткою?
    - Рахунок, будь ласка.
    - Дорого!
  - question: 'You ask for the bill:'
    options:
    - Рахунок, будь ласка.
    - Мені борщ.
    - Все було дуже смачно!
  - question: 'You ask for 1 kg of apples:'
    options:
    - Дайте кілограм яблук.
    - Скільки коштує?
    - Можна меню?
  - question: 'You think the price is high:'
    options:
    - Дорого!
    - Дешево!
    - Нормальна ціна.
  - question: 'You ask if a seat is free:'
    options:
    - Тут вільно?
    - Можна меню?
    - Рахунок, будь ласка.
  - question: 'You compliment the food:'
    options:
    - Все було дуже смачно!
    - Можна карткою?
    - Це гостре?
connects_to:
- a1-042 (next module in A1.7)
prerequisites:
- a1-040 (People Around Me)
grammar:
- 'Review: accusative inanimate (M37) and animate (M40)'
- 'Review: ordering patterns (M38) and price patterns (M39)'
- 'Review: з + noun chunks (M36, M39)'
register: розмовний
references:
- title: Synthesis of M36-M40 content
  notes: No new material — review and integration of A1.6 phase.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Checkpoint: Food and Shopping
**Module:** checkpoint-food-shopping | **Phase:** A1.6 [Food and Shopping]
**Textbook grades searched:** 4, 5, 6

---

## Що ми знаємо? (What Do We Know?)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 155
> Порядкує коло тих бджіл дядько Роман. Він, кажуть, 
> знає таємну бджолину мову. Ходить серед вуликів і щось 
> намовляє бджолятам. Певно, щоб (як?) ... роїлися, не хво-
> ріли та (як?) ... носили нектар з далеких і близьких квіток 
> (За Олесем Гончарем).
> Слова для довідки: веселіше, тут, краще.
> 2. Які слова вживає автор замість слова бджолята?
> 3. Спишіть другий абзац. Підкресліть дібрані вами при-
> слівники. Поміркуйте, як вони утворилися.
> Від прислівників, що відповідають на питання як?, 
> можна ут

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 164
> і сірим. Сьогодні воно схоже на жінку-художницю, яка завмер-
> ла перед акварельним аркушем — вона ось-ось зробить сімнад-
> цятий начерк, сподіваючись, що бажаний образ не вислизне…
> До речі, знаєш, яка мелодія мені вчора почулася в шумі 
> хвиль? Північний вітер, знущаючись, ганяв їх, але ближче 
> до берега хвилі стримували міць, немов не хотіли налякати 
> мешканців міста… Мелодія Елтона Джона… (Е. Сафарлі).
>  
> ІІ   Зробіть нотатку про вранішнє сонце, про травневу грозу 
> чи серпневе небо. З якою мел

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> І якраз у яму 
> втрапить. А ми вже вириємо, постараємося.

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> 174
> Урок розвитку писемного мовлення
> Привітання до Дня матері ...............................................................176
> Спостереження за роллю прислівників у т е к с т і.........................177
> Вибір прислівників, що відповідають
> меті й типу висловлювання ............................................................ 178
> ПОВТОРЕННЯ ВИВЧЕНОГО
> Що ми знаємо про текст, речення, слово ..................................180
> Що ми знаємо про 
> іменник і прикметник .........................181

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> ЛОВИ МОМЕНТ
> Давньоримський поет Горацій завжди влучно відгукувався 
> на всі важливі проблеми і події сучасності. Тому вважають, що 
> фразеологізм «лови момент» походить від його фрази «лови 
> день, довіряючи якомога менше майбутньому». Він означає: 
> використовуй слушну нагоду, не пропускай жодної можливості, не 
> марнуй часу, намагайся використовувати його найефективніше.
> 2. Випиши з тексту дієслова в колонку. Через риску запиши їх 
> у неозначеній (початковій) формі.
> І
> ЗМІНЮВАННЯ ДІЄСЛІВ ЗА ЧИСЛАМИ
> 2

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 21
> Вступ. Українська мова в житті українців. Види інформації . Робота з підручником
> Іноді, старанно прочитавши текст, ми не можемо запам’я-
> тати інформацію. Існують різні прийоми, які допоможуть упо-
> ратися із цією проблемою.
> Для того, щоб краще запам’ятати прочитане, кілька разів 
> повторіть його. Пригадайте, як ми запам’ятовуємо тексти пі-
> сень: спеціально їх не вчимо, але після кількох прослуховувань 
> уже знаємо напам’ять. Проте велику книжку важко перечита-
> ти кілька разів. Тому виділіть голо

## Читання (Reading Practice)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> « а
> Зміню вання ім енників за числами
> 109. Прочитайте вірш Надії Красоткіної.
> Думала Оленкатак: «Щоб здоров’я мати,
> Треба їсти їй буряк, пити чай із м ’яти, 
> їсти супчики й борщі, вареники з сиром,
> І котлетки, й вергунці, але знати міру».
> •  Випишіть іменники, які вжиті в множині.
> І р  •  Поясніть правопис виділених іменників. Зробіть їх звуко-бук- 
> вений аналіз.
> 110. Прочитайте текст, розкриваючи дужки.
> Україна завжди славилася сво­
> єю кухнею. її (страва) знані дале­
> ко за межами країни. Усім в

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 237
> Відомості із синтаксису й пунктуації. Кома між частинами складного речення
> Кома між частинами складного 
> речення, з’єднаними безсполучниковим 
> і  сполучниковим зв’язком
> Вправа 381
> 1. Прочитайте речення .
> В усьому світі відомі 
> український борщ 
> і вареники.
> В усьому світі відомий україн-
> ський борщ, і вареники не посту-
> паються йому за популярністю.
> Рецепт вергунів 
> передала моїй мамі її 
> прабабця і попросила збе-
> рігати його в нашій сім’ї.
> Рецепт вергунів передала моїй 
> мамі її прабабця, і в

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> Поміркуй над прочитаним
>  
> 1. Коли і де відбуваються події у творі? Як про це сказано 
> в тексті?
>  
> 2. Знайди і прочитай опис дерева життєвих радощів. Які емоції 
> викликає в тебе цей опис?
>  
> 3. Спираючись на текст, поясни, чому весь народ чекав на 
> плід, «як на початок нового життя». У  чому полягала його 
> чудодійна сила? Підтвердь свої слова цитатами.
>  
> 4. У творі не зазначено назви овоча. В  описі виділи ключові 
> слова, які відображають його особливості. Дай назву плоду, 
> намалюй у робочому зоши

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> 145. Складіть і запишіть речення з утвореними словосполучення­
> ми вправи 144. Провідміняйте підкреслені іменники.
> Вибірковий переказ тексту з елементами 
> опису
> 146. Розгляньте малюнок.
> •  Виконайте завдання в «Зошиті з розвитку писемного мов­
> лення».
> ^  | Зміна приголосних [г],[к ],[х ] на [з ], [ц ], [с ] 
> *** 
> перед закінченням -і в іменниках різного роду
> 147. Розгляньте таблицю.
> О Д Н И Н А
> Чол. р.
> Ж ін. р.
> Середи, р.
> Чергування
> поріг
> (на) порозі нога
> (на) нозі
> [Г] -
>  [з ']
> байрак (у) байраці

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 239
> Відомості із синтаксису й пунктуації. Кома між частинами складного речення
> Про борщ я можу розпо-
> відати годинами. Ні для кого 
> не секрет що майже у кожній 
> родині існує свій особливий 
> рецепт борщу. Хтось не уявляє 
> борщ без квасолі а хтось готує 
> його без капусти. Всі ці варіан-
> ти мають право на існування 
> бо немає якогось «правильно-
> го» рецепту, просто в кожного 
> є свій сімейний борщ.
> І досі популярним є узвар із сухофруктів це дуже корисний 
> і поживний напі й.
> Полтава славиться галушк

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 158
> ЖИВИЛЬНІ ДЖЕРЕЛА МУДРИХ КНИГ
> Вона в нас не вимовляє літе-
> ру «р». 
> За мить Яришка вже ставила 
> на стільці переді мною молоко, 
> яєчню, сир і хліб із маслом.
> Я збагнув, що в хаті нікого 
> немає, усі на роботі, і їй доручено 
> доглядати мене.
> – Будь ласка, любий бгатику, 
> їж! – сказала вона солодким голосом.
> Я насторожився.
> А коли вона втретє сказала «любий бгатику» («Любий 
> бгатику, спегшу пгоковтни таблетку»), це вже мене зовсім 
> збентежило.
> «Любий бгатику!» Вона ніколи мене так не називала. 
> В

## Граматика (Grammar Summary)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 47
> 90. 
> 1. Прочитай текст і розглянь малюнок. Постав запи-
> тання до кожного абзацу.
> ОДНА ГРИВНЯ — ОДИН ВІЛ
> Гривня з’явилася за часів Київської Русі. Це був зли-
> ток — срібний, іноді золотий. За одну гривню можна було 
> купити вола.
> Гривні знову з’явилися за часів відродження україн-
> ської державності в 1919–1920 роках. Тепер — це наші 
> українські гроші.
> 2. Визнач рід та відмінок виділених іменників. За потреби 
> користуйся таблицями на сс. 41–42.
> 91. 
> 1. Прочитай і спиши речення. Підкресли в них г

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 27
> 58
>   Розгляньте слова, записані ліворуч і праворуч. Які запозичення, 
> на вашу думку, збагачують мову, а які — шкодять їй? Відповідь 
> обґрунтуйте.
> 1)  грошові одиниці: ліра, 
> лат, крона, фунт стер-
> лінгів, долар;
> 2)  національні 
> страви: 
> паелья, паста, суші;
> 3)  одяг: сарі, кімоно, пончо;
> 4)  танці: фламенко, лез-
> гінка, сальса, самба, 
> танго
> Допис — пост;
> виклик — челендж;
> світлина — фотографія; 
> наплічник — рюкзак; 
> цькування — булінг;
> летовище — аеродром;
> мить — момент;
> зміна — ротація; 
> с

> **Source:** unknown, Gr

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Що ми знаємо? (What Do We Know?)` (~200 words)
- `## Читання (Reading Practice)` (~250 words)
- `## Граматика (Grammar Summary)` (~200 words)
- `## Діалог (Connected Dialogue)` (~200 words)
- `## Підсумок — Summary` (~150 words)
- `## Підсумок` (~150 words)

Each section should follow the word budget specified. The total must reach 1000 words minimum.

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
