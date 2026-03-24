<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Too short: 1135 words (target: 2000, minimum: 1700)
- FIX: Russian/archaic words: кот→кіт
</correction_directive>

# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **4: У мене немає...** (A2, A2.1 [Foundation and Aspect Introduction]).

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
module: a2-004
level: A2
sequence: 4
slug: genitive-intro
version: '1.0'
title: У мене немає...
subtitle: Родовий відмінок для вираження відсутності та кількості
focus: grammar
pedagogy: PPP
phase: A2.1 [Foundation and Aspect Introduction]
word_target: 2000
objectives:
- Learner can correctly use the Genitive singular after `немає` to express the absence
  of an object.
- Learner can form the Genitive singular endings for all three noun genders (-а/-я,
  -у/-ю, -и/-і).
- Learner can use quantity words `багато`, `мало`, `кілька`, `декілька` with the Genitive
  plural.
- Learner can form the Genitive plural endings for all three noun genders (-ів, -ей,
  нульове закінчення).
content_outline:
- section: 'Родовий відмінок: Коли чогось немає (The Genitive Case: When Something
    Isn''t There)'
  words: 600
  points:
  - Introducing the Genitive case (Родовий відмінок), answering 'Кого? Чого?'.
  - 'Its first key function: expressing absence or non-existence with the construction
    `(У мене) немає + Genitive`.'
  - 'Contrast: ''У мене є брат'' (Accusative implied, but Nom. form used) vs. ''У
    мене немає брата'' (Genitive).'
  - 'Practice with simple sentences: ''Тут є стіл.'' -> ''Тут немає стола.'''
- section: Закінчення родового відмінка однини (Genitive Singular Endings)
  words: 700
  points:
  - 'Masculine nouns: the -а/-я vs. -у/-ю puzzle. -а/-я for concrete, animate, specific
    items (стола, брата, комп''ютера). -у/-ю for abstract concepts, substances, locations
    (часу, цукру, Києву).'
  - 'Feminine nouns: -и for hard stems (книги, мами), -і for soft stems and stems
    in -я (землі, пісні).'
  - 'Neuter nouns: -а for stems in -о (вікна), -я for stems in -е (моря, сонця).'
  - Provide clear charts and practice drills for forming the Genitive singular.
- section: Коли є багато або мало (When There Is a Lot or a Little)
  words: 700
  points:
  - 'Introducing quantity words that require the Genitive plural: багато (a lot),
    мало (a little, few), кілька/декілька (a few, some), скільки (how many).'
  - 'Genitive Plural Endings: a tricky topic. Masculine: often -ів (столів, братів).
    Feminine/Neuter: often a zero ending with a possible vowel insertion (книг, сестер,
    вікон). Feminine soft stems: -ей (пісень).'
  - 'Lots of examples: багато друзів, мало грошей, кілька книжок, скільки студентів?'
  - Focus on recognizing and using the most common forms, not memorizing every exception.
vocabulary_hints:
  required:
  - родовий відмінок (genitive case)
  - немає ((there) is not, (I) don't have)
  - багато (a lot, many, much)
  - мало (a little, few)
  - кілька (a few, several)
  - скільки (how many, how much)
  - закінчення (ending (grammar))
  - однина (singular)
  - множина (plural)
  recommended:
  - кількість (quantity)
  - відсутність (absence)
  - гроші (money)
  - час (time)
activity_hints:
- type: quiz
  focus: Possession vs. Absence Drill (`Є` vs. `Немає`)
  items: 6
- type: fill-in
  focus: Genitive Singular Formation
  items: 6
- type: match-up
  focus: Genitive Plural Formation with Quantity Words
  items: 6
- type: match-up
  focus: Translate sentences with 'a lot of...' / 'I don't have...'
  items: 6

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: У мене немає...
**Module:** genitive-intro | **Phase:** A2.1 [Foundation and Aspect Introduction]
**Textbook grades searched:** 1, 2, 3, 5

---

## Родовий відмінок: Коли чогось немає (The Genitive Case: When Something Isn't There)

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
> 110
> Навчаюся визначати рід іменників
> 34
> Рід іменників:  
> чоловічий, жіночий, середній
> 	 	
> 1   Визначте, істоту якого роду називає 
> кожний іменник.
> 	 	
> 3   Допишіть пари слів за зразком.
> 2   Прочитай, уставляючи замість крапок слова мій, моя, моє, він, 
> вона, воно. Визнач рід іменників і поясни свою відповідь. Запиши 
> утворені речення.
> мати — тато
> дочка — син
> малюк — маля
> Іменники бувають чоловічого, 
> жіночого і середнього роду. 
> Досліди, як визнача-
> ють рід іменників.
> Я — дослідник
> Я — дослід

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 214
> Відомості із синтаксису й пунктуації.  Додаток
> Відмінок
> Запитання
> Приклад іменника
> Непрямі 
> відмінки
> Родовий
> Давальний
> Знахідний
> Орудний
> Місцевий 
> Кличний 
> Немає питання
> 2.	 Провідмінюйте слова друг і  книга.
> Вправа 348
> 1.	 Спишіть речення.
> Катерина запросила подругу. — Подруга запросила Кате-
> рину.
> Я прочитала книжку. — Книжка мені сподобалася.
> Наша команда виграла кубок. — Кубок дістався нашій ко-
> манді.
> Я хочу запросити тебе на  день народження. — Ти хочеш 
> запросити мене на  день народже

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 61
> М’ЯКИЙ ПРИГОЛОСНИЙ ЗВУК [й]
> Назви предмети. Як вимовляється звук [й] у словах?
> М АЙ|К А
> Й О Д
> СЛОВА — НАЗВИ ОЗНАК
> Добери слова до малюнків.
>  
> холодний 
> сірий 
> білий 
> зелений
>  
> високий 
> довгий 
> теплий 
> голодний 
>  
>  
>  
>  
>  
> Назви кольори предметів. Подумай, які малюнки можуть 
> бути в останньому стовпчику.
> ЯКИЙ?
> ЯКА?
> ЯКЕ?
> ЯКІ?
> 1
> 1
>  
> 2

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> • Поставте питання до виділених слів. Які з них називають дії,
> а які — предмети?
> • Випишіть виділені слова разом із 
> тими, з якими вони зв'язані в реченні.
> гарний ніс — 
> ніс подарунки
> я - дослідник
> Поміркуй і скажи, від 
> якого дієслова походить
> слово подарунок.
> В
> Я — ДОСЛІДНИЦЯ

## Закінчення родового відмінка однини (Genitive Singular Endings)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 47
> Текст. Тема тексту. Заголовок 
> У бабусі Ганни — город. На городі — багато 
> городини. Тут і морква, і капуста, і огірки, і по-
> мідори. Граки літали і псу-ва-ли городину. 
> Дід Богдан по-ста-вив на городі о-пу-да-ло. 
> Два дні о-пу-да-ло лякало граків.  
> А потім граки звикли до о-пу-да-ла. Літали та 
> сідали на нього. Гарно гракам на городі.
> Визнач тему тексту. 
>  
>  
>  
> Город 
> Граки на городі 
> Огірки
> ТВЕРДІ І ПОМ’ЯКШЕНІ ПРИГОЛОСНІ ЗВУКИ
> Назви предмети. Як вимовляється перший звук у словах? 
> Г А ЛК А

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> 98
> 349.
> За малюнками та планом придумай кінцівку казки. За потреби 
> використовуй слова для довідки.
> 1. Що спочатку зробив Чоловік? 2. Як зійшло зерно? 
> 3. Якою стала нива? 4. Що зробив Чоловік із зерном? 5. Які 
> вироби випекли із зерна? 6. Як подякував Чоловік Сонцю?
> Слова для довідки: засіяв, зійшло, заколосилася, 
> достигло, зібрав, змолов, випік, подякував.
> 351. Вправа «Квест». 
> 2 1
> 1 3 4 1
> — Охо-хо... Якби-то була така чарівна комора, щоб 
> усіх на світі годувала.
> Почуло те Сонце та й каже:
> —

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 112
> Спостерігаю за закінченнями 
> іменників різних родів
> Пригадай і розкажи 
> у класі.
> Я — учителька
> Я — учитель
> Чоловічий рід
> можна додати  
> слова мій, він,  
> закінчення -о  
> або нульове
>  тато, Петро
>  вечір, Артем
> Жіночий рід
> можна додати  
> слова моя, вона,  
> закінчення -а, -я 
> або нульове
>  мама, Оксана
>  земля, Юлія
>  тінь, заметіль
> Середній рід
> можна додати  
> слова моє, воно,  
> закінчення  
> -о, -е, -а, -я
>  літо
>  сонце
>  курча
>  маля
> 6   Прочитай. Наведи власні приклади іменників. 
> учень
> школя

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 124
> Мої досягнення сьогодні — це … . Мені важливо було дізна-
> тися про … . У мене сьогодні … настрій, тому що … . Цікавим 
> на уроці вважаю … . Сьогодні мені бракувало … .
> 309   І   Дайте письмові відповіді за запитання, використовуючи 
> в них однорідні члени речення. 
>   Які вчинки й дії людини свідчать про те, що вона небай-
> дужа до своєї країни?
>   Як зробити наші міста й села чистішими, охайнішими?
>   Хто для вас є взірцем громадянської мужності?
>   Яку розмову можна назвати щирою?
>   Що б ви хотіл

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 38
> 	
> «Збери» склади на весняних «хмарах». Утво-
> ри нові слова.
> 	
> Розгадай ребус.
> ,
> ,
> ,,,
> кра
> Ки
> ї
> при
> їв
> ї
> їхали
> ра
> на
> са
> на
> Укра
> 	
> Утвори нові слова.
> КИЇВ
> Наш Київ розіслався
> На горах над Дніпром,
> Садами заквітчався,
> Мов дівчина вінком.
> Його побудували
> Брати, батьки, діди.
> І славно захищали
> Від лютої біди… 
>           Максим Рильський
> У К Р А Ї Н С Ь К О Ї
> 1 2 3 4 5 6 7 8 9 1011
> 1 3 4
> 5 11
> Pidruchnyk.com.ua

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> 89
> 322. 1.	 Прочитай оповідання.
> Як хлопці мед поїли
> Мати послала Олега і Романа до 
> дідуся. Брати поласували в нього яблу-
> ками. Зібралися хлопці додому. Дав дідусь 
> баночку меду й каже:
> — Хай і мама скуштує. 
> Поки дійшли брати додому — увесь 
> мед з’їли. Вийшла мама з хати, дивиться — сини плачуть. 
> Стривожилася вона. Розповіли хлопці, як мед поїли. Мама 
> зраділа, сміється. Хлопці дивуються, питають:
> — Мамо, чого ви радієте?
> — Того, що ви плачете... (За Василем Сухомлинським)
> 2.	 Як гадаєш: хло

## Коли є багато або мало (When There Is a Lot or a Little)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 106
> б і л к а
> к у л ь б
> б у з о к
> Бачу Б, б (бе). Чую  [б].
> б
> а
> а
> Бі-лі ко-ти си-
> ді-ли в бі-ло-му 
> бу-дин-ку. У-се-ре-
> ди-ні все бу-ло бі-
> ле. Бі-лі сто-ли з 
> бі-ли-ми ска-тер-
> ти-на-ми. 
> а
> о
> у
> и
> і
> Б
> ба
> бо
> бу
> би
> бі
> а
> о
> у
> и
> і
> аб
> об
> уб
> иб
> іб
> Б
> ба
> бу
> бе
> ба
> лет
> лкон
> бу
> ква
> квар
> бі
> лизна
> ла
>  [  = •   –  | –•]
>  [ –• | –  • – ]
> Б б

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> Скоро всі діти у групі були вже не хлопчиками й дівчат­
> ками, а родичами — різними-різними. Для всіх знайшлися 
> обов’язки в родині. І для бабусі й дідуся, і для тітоньки й 
> дядечка, і для братиків і сестричок... Цілісіньку годину 
> гралися діти. Ходили один до одного в гості, їздили на роботу, 
> готували обід. Тільки маленька Ліля чомусь сумно сиділа на 
> стільчику. Вона щось тихенько шепотіла й загинала пальчики. 
> І раптом як заплаче!
> — Лілечко, що сталося? — підбігла до дівчинки Оленка. 
> Підійшла

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 33
> Олександр  Єфімов
> «ДРУКÀР КНИГ, ПЕРЕД

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Родовий відмінок: Коли чогось немає (The Genitive Case: When Something Isn't There)` (~600 words)
- `## Закінчення родового відмінка однини (Genitive Singular Endings)` (~700 words)
- `## Коли є багато або мало (When There Is a Lot or a Little)` (~700 words)
- `## Підсумок — Summary` (~150 words)

Each section should follow the word budget specified. The total must reach 2000 words minimum.

---

## Content Rules

TARGET: 45-65% Ukrainian.
LANGUAGE ROLES:
- THEORY: English prose for grammar explanations that would be too complex in Ukrainian at this level.
- EXAMPLES & CONTEXT: Ukrainian — dialogues, example sentences, cultural context.
- HEADERS: Ukrainian with English in parentheses.
- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English — never mix languages within a sentence. Ukrainian paragraphs and dialogues carry most content. English appears for grammar theory and in callout boxes.
A2 register ONLY. Concrete everyday vocabulary. No literary/poetic language. No abstract nouns. Ukrainian sentences max 15 words. Max 2 clauses. All cases allowed. Simple subordinate clauses only (який/що/коли). Aspect pairs introduced. No participles.

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
- Dialogues: natural, not stilted. Real situations, real responses.
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

**Required:** родовий відмінок (genitive case), немає ((there) is not, (I) don't have), багато (a lot, many, much), мало (a little, few), кілька (a few, several), скільки (how many, how much), закінчення (ending (grammar)), однина (singular), множина (plural)
**Recommended:** кількість (quantity), відсутність (absence), гроші (money), час (time)

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
