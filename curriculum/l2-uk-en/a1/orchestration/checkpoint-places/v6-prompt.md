# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **35: Checkpoint: Places** (A1, A1.5 [Places]).

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
module: a1-035
level: A1
sequence: 35
slug: checkpoint-places
version: '1.2'
title: 'Checkpoint: Places'
subtitle: Can you navigate a Ukrainian city?
focus: review
pedagogy: PPP
phase: A1.5 [Places]
word_target: 1200
objectives:
- Demonstrate correct use of euphony (у/в, і/й, з/із/зі)
- Use locative for location (Де?) and accusative for direction (Куди?)
- Navigate using city vocabulary, transport, and directions
- Answer Звідки? with genitive chunks
- Combine all A1.5 skills in connected urban scenarios
content_outline:
- section: Що ми знаємо? (What Do We Know?)
  words: 200
  points:
  - 'Self-check covering M28-M34: Can you apply euphony rules? (M28) Can you say where
    things are? (M29) Can you name city places? (M30) Can you say where you''re going?
    (M31) Can you use transport? (M32) Can you give directions? (M33) Can you say
    where you''re from? (M34)'
- section: Читання (Reading Practice)
  words: 250
  points:
  - 'A short Ukrainian text using vocabulary from M28-M34. Content: a tourist navigates
    Kyiv — asks for directions, takes metro, finds a museum, describes where they''re
    from and where they''re going. Uses euphony, locative, accusative, genitive chunks,
    transport.'
- section: Граматика (Grammar Summary)
  words: 200
  points:
  - 'Key patterns from A1.5: 1. Euphony: у/в, і/й, з/із/зі (M28) 2. Де? → в/на + locative:
    в школі, на роботі (M29) 3. Куди? → в/на + accusative: у школу, на роботу (M31)
    4. Звідки? → з + genitive chunk: з України, з роботи (M34) 5. Transport: автобусом,
    на метро (M32) 6. Directions: прямо, направо, наліво (M33) 7. City places with
    correct prepositions (M30)'
- section: Діалог (Connected Dialogue)
  words: 300
  points:
  - 'A tourist in Kyiv asks for help: — Вибачте, я з Канади. Де тут музей? — Музей
    у центрі. Ідіть на метро до станції Хрещатик. — А як дістатися від метро? — Вийдіть
    і йдіть направо. Музей на площі. — Дякую! А потім я хочу їхати у Львів. Де вокзал?
    — Вокзал далеко, їдьте на метро до станції Вокзальна. Uses all A1.5 skills in
    one realistic scenario.'
- section: Підсумок — Summary
  words: 250
  points:
  - 'A1.5 achievement summary: You can now navigate Ukrainian cities. You know euphony
    rules for natural speech. You can say WHERE something is (locative). You can say
    WHERE you''re GOING (accusative). You can say WHERE you''re FROM (genitive chunks).
    You can use transport and give directions. Next: A1.6 — Food and Shopping (ordering,
    buying, accusative for objects).'
vocabulary_hints:
  required: []
  recommended: []
activity_hints:
- type: quiz
  focus: 'Choose the correct question: Де? Куди? Звідки?'
  items: 8
  questions:
  - '... ти живеш? — У Києві. (Де / Куди / Звідки)'
  - '... ти йдеш? — У магазин. (Куди / Де / Звідки)'
  - '... ви? — Ми з Канади. (Звідки / Де / Куди)'
  - '... музей? — У центрі. (Де / Куди / Звідки)'
  - '... їде автобус? — На вокзал. (Куди / Де / Звідки)'
  - '... ти їдеш? — З роботи. (Звідки / Куди / Де)'
  - '... аптека? — Направо. (Де / Куди / Звідки)'
  - '... вони? — Зі США. (Звідки / Де / Куди)'
- type: fill-in
  focus: Complete the connected dialogue with correct forms
  items: 6
  blanks:
  - Вибачте, я {з Канади}. Де тут музей?
  - Музей {у центрі}. Ідіть на метро.
  - А як дістатися {від метро}?
  - Вийдіть і йдіть {направо}. Музей на площі.
  - Я хочу їхати {у Львів}. Де вокзал?
  - Вокзал далеко, їдьте {на метро}.
- type: group-sort
  focus: Sort phrases by case/function (Locative, Accusative, Genitive chunks)
  items: 9
  groups:
  - name: Локація (Де?)
    items:
    - у школі
    - на площі
    - в центрі
  - name: Напрямок (Куди?)
    items:
    - на роботу
    - у Львів
    - в Канаду
  - name: Походження (Звідки?)
    items:
    - з України
    - зі США
    - з роботи
- type: quiz
  focus: 'Euphony rules check: у/в, і/й, з/із/зі'
  items: 8
  questions:
  - Брат ... сестра (і / й)
  - Вона живе ... Львові (у / в)
  - Я йду ... школи (зі / з)
  - Він ... Києві (у / в)
  - Мама ... тато (і / й)
  - Ми ... України (з / із)
  - Я ... кімнаті (в / у)
  - Вона ... США (зі / з)
connects_to:
- a1-036 (Food and Drink)
prerequisites:
- a1-034 (Where From?)
grammar:
- 'Review: locative for location (Де?)'
- 'Review: accusative for direction (Куди?)'
- 'Review: genitive chunks for origin (Звідки?)'
- 'Review: euphony and transport'
register: розмовний
references:
- title: Synthesis of M28-M34 content
  notes: No new material — review and integration of A1.5 phase.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Checkpoint: Places
**Module:** checkpoint-places | **Phase:** A1.5 [Places]
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
> 157
> ЗМICТ
> ЧИТАЄМО Й РОЗПОВІДАЄМО
> ПРО СВОЇ ЗАХОПЛЕННЯ
> Ліна Костенко. Вже брами літа замикає осінь…  . . . . . . . . . . . . . . . 5
> Олександра Савченко. Як читають книжки? . . . . . . . . . . . . . . . . . . 6
> Марія Манеру. Читач Максимко . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7 
> ВЕСЕЛЕ СЛОВО. Василь Марсюк. Диктант . . . . . . . . . . . . . . . . . . . 8
> Медіавіконце: види і джерела інформації . . . . . . . . . . . . . . . . . 9
> Давид Гуліа. Розум, знання і сила . . . . . . .

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 185
> ЧИТАННЯ. ВИДИ ЧИТАННЯ. 
> МЕТА ЧИТАННЯ
> § 65
> Життєво важлива звичка — 
> читати щодня
> Книжки мають особливу чарівність, вони дають нам насолоду: 
> вони розмовляють з нами, дають добрі поради, стають живими друзями 
> (Ф. Петрарка).
> Слово дня: читàння, розкодувàння, уподобàння, смакîлик.
> 432   Прочитайте епіграф. Про які функції читання ідеться? Чи є зв’язок 
> між темою уроку і «словами дня»?
> Пригадуємо:
> 1  Що таке читання?
> 2  Яку роль у житті людини відіграє читання?
> 3   У яких ситуаціях ми читаємо в

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 1
> Правила  читання
> 1
> Першочергово у тексті твору шукай відповіді 
> на запитання:
> • Хто діє? Які його / її вчинки?
> • Де і коли відбуваються події?
> • Кого або що описує автор/авторка?
> 2
>  
> При повторному читанні:
> 1. Виділи деталі в тексті (портреті, пейзажі, 
> описі предмета чи приміщення).
> 2. Проаналізуй, яку роль вона відіграє:
> • у портреті: передає зовнішню 
> характеристику чи звертає увагу на 
> внутрішні якості героя / героїні;
> • у пейзажі: відтворює різноманітні стани 
> природи чи внутрішній стан г

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> 99
> погралися гори-хвилі —
> і скіпîк1 не стало...
> Знайди та прочитай слова й вислови, які змальовують 
> картини тиші й неспокою в природі.
> Підготуйся до виразного читання вірша: визнач його
> настрій, темп читання кожного речення. Які почуття
> потрібно  передати  інтонацією?
> * * *
> Реве та стогне Дніпр широкий, 
> сердитий вітер завива,
> додолу верби гне високі,
> горами хвилю підійма.
> І блідий місяць на ту пору 
> із хмари де-де виглядав, 
> неначе човен в синім морі, 
> то виринав, то потопав.
> Ще треті півн

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> Навчальне видання
> ЗАХАРІЙЧУК  Мар’яна  Дмитрівна
> УКРАЇНСЬКА МОВА ТА ЧИТАННЯ
> Підручник для 4 класу
> закладів загальної середньої освіти
> (у 2-х частинах)
> ЧАСТИНА 1
> УКРАЇНСЬКА МОВА
> Рекомендовано  
> Міністерством освіти і науки України
> Видано за рахунок державних коштів. Продаж заборонено
> Підручник відповідає Державним санітарним нормам і правилам  
> «Гігієнічні вимоги до друкованої продукції для дітей»
> Для оформлення підручника використано матеріали, що знаходяться  
> у вільному доступі в мережі «Інтер

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 144
> 345   Складіть і запишіть по три словосполучення зі «словами дня». 
> Що вам відомо про «читацький смак», «хист до читання»? 
> 346   Запишіть речення. Знайдіть із-поміж них прості, речення з одним 
> головним членом і складні. 
> 1. Книжку читають не очима, а розумом. 2. У книжці 
> шукай не букви, а думки. 3. Книжка дає крила (Нар. твор-
> чість). 4. Книжки — найбільш мовчазні й найвірніші друзі; 
> вони — найдоступніші й наймудріші порадники і найтерпля-
> чіші вчителі (Ч.-У. Еліот). 5. Багатьох життєвих

## Граматика (Grammar Summary)

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> Умовні позначення:
> — урок розвитку писемного
> мовлення.
> — вивчити 
> напам’ять;
> — словник;
> — домашнє завдання;
> — робота в парах, 
> читання діалогів;
> — тема уроку;
> — завдання на вибір;
> — завдання підвищеної 
> складності;
> С
> — робота в групах;
> ? 
> — ознайомитись;

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 222
> Відомості із синтаксису й пунктуації. Обставина
> Вправа 361
> Виконайте тест . У завданнях 1 і 2 лише один правильний варіант відповіді, 
> у  завданні 3 потрібно встановити відповідність між варіантами .
> 1. Обставинами є  усі виділені слова, ОКРІМ
> Поки ми їдемо до Києва, я думаю про неї. Зараз восьма ве-
> чора, а значить, прабабуня вечеряє. У кімнаті цокає годинник 
> і про щось торохтить радіо.
> А до Києва
> Б зараз
> В у кімнаті
> Г про щось
> 2. Непоширеним є  речення
> А Створіть своє родинне дерево через

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 143
> 143
> § 73. Написання  н  і  нн  у  прикметниках
> 4.	 Виконайте завдання в тестовій формі.
> 	
> Прочитайте речення.
> Усе буяло, усе наливалося життєвою силою в цю благодат..у пору 
> ра..ього літа. Земля ніби прагнула виявити свою нестрим..у щедрість, по-
> радувати людей усім найкращ

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Що ми знаємо? (What Do We Know?)` (~200 words)
- `## Читання (Reading Practice)` (~250 words)
- `## Граматика (Grammar Summary)` (~200 words)
- `## Діалог (Connected Dialogue)` (~300 words)
- `## Підсумок — Summary` (~250 words)
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

GRAMMAR CONSTRAINTS (A1.5 — Places & Movement, M29-M36):
Euphony, locative, accusative direction, genitive origin.

ALLOWED:
- Euphony rules (у/в, і/й, з/із/зі)
- Locative case with в/у/на (Де?)
- Accusative for direction (Куди?)
- Genitive for origin (Звідки? З + genitive)
- All present tense verbs

BANNED: Past/future tense, dative, instrumental,
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
