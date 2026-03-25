# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **44: Той, який...** (A2, A2.7 [Complex Sentences and Conditionals]).

**Target: 2000–3000 words** of prose (Ukrainian examples count toward word total, headings and exercise placeholders do not).

---

## Step 1: Pacing Plan (output this FIRST)

Before writing any content, output a `<pacing_plan>` block. Evaluate each section from the plan and commit to a word budget. This prevents frontloading early sections and rushing later ones.

```
<pacing_plan>
Section 1 "Title": ~XXX words — [1-sentence content focus]
Section 2 "Title": ~XXX words — [1-sentence content focus]
...
Summary: ~150 words
Total: 2000+ words
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
7. **Hit the word target** — you MUST write 2000–3000 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
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
module: a2-044
level: A2
sequence: 44
slug: relative-clauses
version: '1.0'
title: Той, який...
subtitle: Означальні підрядні речення з який, де, куди, звідки
focus: grammar
pedagogy: PPP
phase: A2.7 [Complex Sentences and Conditionals]
word_target: 2000
objectives:
- Learner can form relative clauses using який/яка/яке/які, agreeing in gender and
  number with the noun they describe.
- Learner can use де, куди, and звідки as relative words to describe places in
  subordinate clauses.
- Learner can distinguish який in questions (Який це будинок?) from який in relative
  clauses (Будинок, який стоїть на розі...).
- Learner can produce natural sentences with relative clauses to describe people,
  objects, and places.
content_outline:
- section: 'Який? Яка? Яке? Які? (Which? What Kind?)'
  words: 750
  points:
  - 'Introducing relative clauses (означальні підрядні речення): a clause that
    describes a noun in the main sentence. The relative pronoun який agrees with the
    noun it refers to in gender and number.'
  - 'Gender and number agreement: Книжка, яка лежить на столі... Хлопець, який
    прийшов вчора... Місто, яке я люблю... Друзі, які живуть у Києві...'
  - 'Case of який: it takes the case required by its role in the subordinate clause,
    not the main clause. Людина, яку я зустрів (Acc.) vs. Людина, яка мене зустріла
    (Nom.). At A2 level, focus on Nominative and Accusative cases of який.'
  - 'Comma placement: always a comma before який/яка/яке/які when introducing a
    relative clause.'
  - 'Contrast with questions: Який це фільм? (question) vs. Фільм, який ми
    дивилися вчора, був цікавий (relative clause). Same word, different function.'
- section: 'Де, куди, звідки — місце (Where, Where To, Where From — Place)'
  words: 600
  points:
  - 'Using де as a relative word for places: Кафе, де ми зустрілися, було затишне.
    Місто, де я народився, знаходиться на заході.'
  - 'Using куди for direction: Парк, куди ми ходимо гуляти, дуже гарний.'
  - 'Using звідки for origin: Країна, звідки вона приїхала, — це Україна.'
  - 'When to use де vs. який: Будинок, де живе мій друг = Будинок, в якому живе
    мій друг. At A2 level, де is simpler and more natural for places.'
- section: 'Описуємо людей, речі та місця (Describing People, Things, and Places)'
  words: 650
  points:
  - 'Building longer descriptions by combining relative clauses with previously
    learned grammar: Подруга, яка живе у Львові, працює вчителькою. Ресторан, де
    ми вчора вечеряли, знаходиться біля парку.'
  - 'Avoiding common errors: redundant pronoun (Книжка, яка вона цікава = WRONG),
    wrong gender agreement (Хлопець, яке = WRONG), missing comma.'
  - 'Stacking information naturally: instead of many short sentences (Це мій друг.
    Він живе у Києві. Він працює програмістом.), combine with який: Це мій друг,
    який живе у Києві і працює програмістом.'
  - 'Practical production: describe your favorite place, a person you admire, an
    object you use daily — using relative clauses.'
vocabulary_hints:
  required:
  - який (which, that — masc.)
  - яка (which, that — fem.)
  - яке (which, that — neut.)
  - які (which, that — pl.)
  - де (where — relative)
  - куди (where to — relative)
  - звідки (where from — relative)
  - означальний (attributive, defining)
  - описувати (to describe)
  - речення (sentence, clause)
  recommended:
  - котрий (which — formal synonym of який)
  - затишний (cozy, comfortable)
  - знаходитися (to be located)
  - стояти (to stand, to be situated)
activity_hints:
- type: fill-in
  focus: Insert the correct form of який (яка, яке, які) into relative clauses,
    matching gender and number
  items: 6
- type: quiz
  focus: Choose де, куди, or звідки to complete sentences about places
  items: 6
- type: match-up
  focus: Combine two simple sentences into one using a relative clause
  items: 6
- type: true-false
  focus: Judge whether relative clauses have correct agreement and comma placement
  items: 6
references:
- title: Заболотний Grade 9, §17-18
  notes: Означальні підрядні речення — який, котрий, де, куди, звідки as relative
    words, with agreement rules and examples
- title: Авраменко Grade 9, означальні підрядні
  notes: Relative clauses with який — exercises and literary examples
- title: 'ULP: Relative Clauses in Ukrainian'
  url: https://www.ukrainianlessons.com/який/
  notes: Practical overview of який in relative clauses

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Той, який...
**Module:** relative-clauses | **Phase:** A2.7 [Complex Sentences and Conditionals]
**Textbook grades searched:** 1, 2, 3, 5

---

## Який? Яка? Яке? Які? (Which? What Kind?)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 23
> 	
> Які? (розмір)
> 	
> Які? (колір)
> 	
> Які? (смак)
> (яке?)
> (який?)
> (який?)
> (який?)
> (який?)
> (який?)
> (який?)
> (який?)
> (           ?)
> Слова — назви ознак предметів
> 	 Який у тебе сьогодні настрій? Вибери.
> Який?
> Яка?
> Яке?
> Які?
> (яка?)
> (яка?)
> (яка?)
> (           ?)

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> 55
> оДнина І мноЖина
> Що відбувається? Склади та запиши речення за малюнком. 
> Підкресли слова — назви дій. 
> ганчірка
> витирає
> праска
> підодіяльник
> прибирання
> прасує
> простирадло
> віяло
> Зразок. Дарина несе простирадло в шафу.
>  
> Напиши, яку домашню роботу ти виконуєш один (пиши я), 
> а яку ви в родині виконуєте разом чи по черзі (пиши ми).
> Зразок. Я гуляю з собакою. Ми вибиваємо килим.
> Слова для довідки. Поливаю, підмітаю, прибираю пило-
> сосом, складаю, витираю, прасую, перу, мию, готую.
>  
> Розглянь предм

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 135
> Підмет і присудок становлять основу речення.
> Інші зв’язані між собою слова утворюють слово-
> сполучення. Наприклад: весела дітвора; поспішає
> до школи.
> 3. Прочитай речення. Поясни, як розумієш значення виді-
> леного слова. Добери до нього синоніми. 
> 4. Спиши речення про ошатне місто. Підкресли головні 
> члени. Встанови зв’язок слів у реченні за питаннями і за-
> пиши. 
> Проведи дослідження!
> 1. Прочитай підкреслені словосполучення.
> 2. Поміркуй, яке слово в кожному словосполученні головне, 
> а яке — з

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> В Шелестить пожовкле листя по діброві, гуляють хмари, сонце спить. Г Цілком у твоїх силах зробити, щоб світ довкола став трішки кращим. 3. Перед виділеним сполучником і НЕ треба ставити кому в реченні
> А Одгоріли і погасли останні огні, облетіло жоржиною літо. Б Всихає непокірне верховіття і літнє листя бронзою дзвенить.

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 101
> Повторюємо разом
> Слова — назви ознак. 
> Слова, протилежні за 
> значенням
>  
> 	 Розглянь малюнки. 
> Який?
> Яка? 
> Яка? 
> Слова, які відповідають на питання 
> який? яка? яке? які?, указують на 
> ознаку предмета.
> 	 Перепиши перше речення тексту (с. 99). Під-
> кресли слова — назви ознак кошеняти. По-
> став до цих слів запитання.
> 	 Прочитай текст.
> Чижик-Пижик сидів на високій гілці й 
> крутив головою. Раптом перед ним про-
> летіла яскрава бабка. Він хотів її схопи-
> ти, але зірвався з гілки. Зірвався, за-
> кру

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> НАВЧАЮСЯ СКЛАДАТИ РЕЧЕННЯ 
> З ДІЄСЛОВАМИ
> Прочитайте речення. Простежте, 
> які різні дії означає слово іде.
> складаю
> Іде катер. Іде поїзд. Іде зима. Іде час. Іде концерт.
> • Замініть у кожному реченні слово іде дієсловом, близьким 
> за значенням. Скористайтеся довідкою. Запишіть речення
> за зразком.
> Іде катер. 
> Пливе катер.
> ? годинник
> Довідка
> Відбувається, їде, минає, пливе, настає.
> б| Розглянь малюнки. Напиши, хто як пересувається,
> використавши дієслова з довідки.
> На які питання 
> відповідають 
> дієслов

## Де, куди, звідки — місце (Where, Where To, Where From — Place)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 4
> Я ВИВЧАЮ УКРАЇНСЬКУ МОВУ
> Ми живемо в Україні. Наша мова — українська. 
> Ми будемо вчитися говорити, читати й писати українською. 
> Я читаю 
> українською.
> Я пишу 
> українською.
> Я слухаю 
> українську.
> Я говорю 
> українською.
> Я вітаюсь і знайомлюсь. 
> 1
> Доброго ранку!
> Мене звати Ганна.
> Привіт! Я Тарас. 
> Будемо вчитися разом.
> Будемо дружити!

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> Солом’яному, барвистій, неподалік, відкотився, 
> прямцем, 
> мешкаєш, 
> європеєць, 
> розташована, 
> Австралії, вистрибцем.
> Прочитай правильно
> 26
> Анатолій Григорук
> ДИВОВИЖНІ ІМЕНА
> Якось сидів я в парку на лаві. Поряд зі мною чи-
> тав газету старенький дідусь у солом’яному брилі і 
> барвистій вишиванці. А неподалік грався м’ячиком 
> маленький хлопчик. Підкинув хлопчик м’ячика. Уда-
> рився той об стовбур дерева й відкотився прямцем 
> дідусеві до ніг. Підняв дідусь м’ячика і чекає, що 
> далі буде.
> Підійшов хлоп

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 20
> 3. Прочитай назви міст Львівщини. Які з них тобі відомі?
> Запиши назви міст в алфавітному порядку. Візьми до 
> уваги правило.
> Львів, Дрогîбич, Стрий, Сàмбір, Трускавåць, 
> Червоногрàд, Брîди, Борислàв.
> Якщо перші букви в словах однакові, то під час розташу-
> вання цих слів за алфавітом бери до уваги другу букву.
> 4. Прочитай текст. Що нового ти дізнався/дізналася з нього? 
> 4
> На Львівщині в селі Нагуєвичі народився 
> Іван Франко. Він написав чимало творів для ді-
> тей. Усі знають його збірку дитячих

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> І з циганським родом-племенем нічого спільного вони не мають. Та сонце кличе нас у сусідній із Непорожніми садок. Там під грушею на 
> розкладачці згорнувся калачиком довготелесий білявий хлопчина. Ви не 
> повірите, але й він Сашко. Отже, погодьтеся, прізвиська просто необхідні.

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 59
> Щастик — маленький зайчик. 
> —	А що таке щастя? 
> —	У кожного воно своє! 
> —	 Піду я пошукаю щастя. Привіт, ко-
> зенятко! А що таке щастя?
> —	Це жувати соковиту капусту! 
> —	 Хіба це щастя? Білочко, яке воно? 
> —	 Сидіти в дуплі й гризти горішки.
> —	Ні. Це не моє щастя. 
> —	Повертайся додому. Пізно вже.
> Прочитайте казку в особах.
> Біля хатинки стояла матуся. Вона 
> його обняла й поцілувала. А зайчик 
> подумав: «Немає нічого кращого, ніж 
> обійми моєї матусі. Ось воно, щас-
> тя!» (за Ларисою Ніцой).
> Назви

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> 30 Розгляньте зображення поштового конверта.
> Складіть розповідь про хлопчика Сашка і дівчинку
> Наталочку за адресами їхнього проживання.
> Поясніть уживання великої букви у словах.
> Адргсз агдпрееника, ндекс
> 'Григорівна
> Яисенг#. 6уі>. ^с.уТмі^е,.....
> ЪрООПрСЫфй район, 
> Камська о^ласт^ 
> Урина Л'л' Т,7!
> Адреса соерл.уеача, іцдсис
> Яуцґнцр (Ііґі^ая^р 7/еіярґ№ич 
> /у- ЪринО^’аС’. буд. Л цл Щ
> м. „Яуцы^ 
> волинськарЬласть, 
> Україна
> 3і| Запиши речення. Підкресли назви річок. Як вони пишуться?
> Місто Чернігів с

## Описуємо людей, речі та місця (Describing People, Things, and Places)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 12
> Знайди букви А і а в рядку.
> л 
> М 
> а 
> А 
> д 
> а 
> Л 
> д 
> я 
> а
>  
> Знайди на малюнку предмети, у назвах яких є звук [а]. 
> Скажи, хто де знаходиться. Використай слова 
> за, на, перед, у, під. 
> Прочитай або послухай слова.
> Визнач місце букви а в словах. 
> Яких предметів немає 
> на малюнку? 
>  фа-ра 
> со-ба-ка
>  тра-ва 
> зу-пин-ка
>  ми-ша 
> ав-то-бус
> Як ти поводишся в автобусі?
>  
> Факти і думки
> 1
> 2
> 3
> А а
> А-а-а а-а-а
> Вулицями Лондона їздять 
> автобуси на два поверхи.
> Ці автобуси червоного 
> кольору.
> Усі люблять їзди

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> РОЗРІЗНЯЮ СЛОВА, ЯКІ ВІДПОВІДАЮТЬ 
> НА ПИТАННЯ ХТО? ЩО?
> Я — учителька
> Прочитай і розкажи у класі.
> Я — учитель
> хто? 
> що?
> Слова — назви людей і тварин відповідають на 
> питання хто?.
> Слова — назви інших предметів відповідають на 
> питання що?.
> 8| Допиши речення, відповідаючи на запитання.
> У школі я — ?. 
> В автобусі я — ?.
> У бібліотеці я — ?.
> У крамниці я — ?.
> У театрі я — ?.
> Для мами й тата я — ?. 
> Для дідуся й бабусі я — ?. 
> Для брата й сестри я — ?.
> __________________
> • На які питання відповідають

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 87
> 6. Ознайомся з графіком роботи музею. Випиши назви днів 
> тижня. Познач рід цих іменників.
> 5. Придумай заголовок до тексту про музей. Спиши текст. 
>

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Який? Яка? Яке? Які? (Which? What Kind?)` (~750 words)
- `## Де, куди, звідки — місце (Where, Where To, Where From — Place)` (~600 words)
- `## Описуємо людей, речі та місця (Describing People, Things, and Places)` (~650 words)
- `## Підсумок` (~150 words)

Each section should follow the word budget specified. The total must reach 2000 words minimum.

---

## Content Rules

TARGET: 55-75% Ukrainian.
LANGUAGE ROLES:
- PRIMARY: Ukrainian for all content — dialogues, examples, section intros, cultural context.
- ENGLISH: Only for abstract grammar concepts that need explicit explanation.
- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English. Dialogues, examples, section intros all stay Ukrainian-only.
A2 register. Concrete everyday vocabulary. No literary language, no metaphors. Ukrainian sentences max 15 words. Max 2 clauses. All cases allowed. Simple subordinate clauses only. Aspect pairs introduced. No participles.

GRAMMAR RULES:
- Max 15 words per Ukrainian sentence
- Max 2 clauses per sentence
- All cases allowed
- Simple subordinate clauses allowed (який/що/коли)
- Aspect pairs introduced but not complex
- No participles

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



### Vocabulary

**Required:** який (which, that — masc.), яка (which, that — fem.), яке (which, that — neut.), які (which, that — pl.), де (where — relative), куди (where to — relative), звідки (where from — relative), означальний (attributive, defining), описувати (to describe), речення (sentence, clause)
**Recommended:** котрий (which — formal synonym of який), затишний (cozy, comfortable), знаходитися (to be located), стояти (to stand, to be situated)

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
