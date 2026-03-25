# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **15: What I Like** (A1, A1.3 [Actions]).

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
module: a1-015
level: A1
sequence: 15
slug: what-i-like
version: '1.1'
title: What I Like
subtitle: Я люблю читати — your first verbs
focus: grammar
pedagogy: PPP
phase: A1.3 [Actions]
word_target: 1200
objectives:
- Use люблю + infinitive to express what you like doing
- Use мені подобається + noun to express what you like (as memorized chunk)
- Recognize Ukrainian infinitive form (-ти ending)
- Talk about hobbies and interests using simple verb phrases
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Meeting someone''s interests (ULP Ep14 pattern): — Що ти любиш робити?
    — Я люблю читати і слухати музику. — А я люблю готувати. — Правда? Що ти готуєш?
    Infinitives introduced naturally through ''люблю + verb''.'
  - 'Dialogue 2 — Describing preferences: — Тобі подобається ця книга? — Так, мені
    подобається. — А цей фільм? — Ні, мені не подобається. Мені подобається музика.
    ''Подобається'' as a fixed chunk — dative grammar NOT analyzed.'
- section: Я люблю... (I Like...)
  words: 300
  points:
  - 'Люблю + infinitive (what you enjoy doing): Я люблю читати (I like to read). Я
    люблю гуляти (I like to walk). Я люблю готувати (I like to cook). Я люблю слухати
    музику (I like to listen to music). Pattern: subject + люблю + infinitive (-ти
    ending). Infinitive = dictionary form of the verb, always ends in -ти.'
  - 'Common infinitives for hobbies (new vocabulary): читати (to read), гуляти (to
    walk), готувати (to cook), слухати (to listen), дивитися (to watch), грати (to
    play), малювати (to draw), подорожувати (to travel), співати (to sing). Pronunciation:
    the stress in infinitives varies — learn each one.'
- section: Мені подобається... (I Like...)
  words: 300
  points:
  - 'Two ways to say ''I like'' — different grammar, same meaning at A1: Я люблю +
    infinitive = I love/like doing something. Мені подобається + noun = I like something
    (a thing). Мені подобається музика. Мені подобається ця книга. Мені подобається
    Київ. Note: ''мені подобається'' is a chunk — we don''t analyze WHY мені (dative).
    Just use it.'
  - 'Negative: Я не люблю / Мені не подобається: Я не люблю готувати. Мені не подобається
    цей фільм. Question: Ти любиш читати? Тобі подобається? Note: люблю changes by
    person (я люблю, ти любиш) — full conjugation in M17 (Group II).'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Two structures for ''like'': 1. Я люблю + infinitive (-ти) — for activities 2.
    Мені подобається + noun — for things Negative: не before the verb (не люблю, не
    подобається). Self-check: Name 3 things you like doing (Я люблю...). Name 2 things
    you like (Мені подобається...). Name 1 thing you don''t like (Я не люблю... /
    Мені не подобається...).'
vocabulary_hints:
  required:
  - любити (to love/like — verb)
  - подобатися (to be pleasing — used as 'to like')
  - читати (to read)
  - гуляти (to walk)
  - готувати (to cook)
  - слухати (to listen)
  - дивитися (to watch)
  - грати (to play)
  recommended:
  - малювати (to draw)
  - подорожувати (to travel)
  - співати (to sing)
  - музика (music, f)
  - фільм (film, m)
  - книга (book — review from M08)
activity_hints:
- type: fill-in
  focus: 'Complete: Я люблю ___. (choose infinitive for the picture)'
  items: 8
- type: quiz
  focus: Люблю or подобається? Choose the right structure.
  items: 8
- type: match-up
  focus: 'Match infinitives to their meanings: читати ↔ to read'
  items: 8
- type: fill-in
  focus: 'Make it negative: Я люблю → Я не люблю'
  items: 6
connects_to:
- a1-016 (Verbs Group I)
prerequisites:
- a1-014 (Checkpoint — My World)
grammar:
- 'Infinitive form: all verbs end in -ти'
- Люблю + infinitive for activities
- Мені подобається + noun (chunk — no dative analysis)
- Negation with не before the verb
register: розмовний
references:
- title: ULP Season 1, Episode 14
  url: https://www.ukrainianlessons.com/episode14/
  notes: Hobbies and interests — люблю + infinitive pattern.
- title: Літвінова Grade 7, p.26-27
  notes: 'Infinitive definition: форма, що закінчується суфіксом -ти.'

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: What I Like
**Module:** what-i-like | **Phase:** A1.3 [Actions]
**Textbook grades searched:** 3, 4, 5

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 5
> ЩО  Я  ЛЮБЛЮ
> Люблю я маму, люблю тата.
> Люблю я свою рідну хату.
> Люблю...
> 	 	
> 4   Склади невеликий текст «Що я люблю робити», запиши його 
> і підготуйся прочитати у класі.
> 3   Прочитай. Чи можна цей запис назвати завершеним висловлюванням? 
> Чому ти так думаєш?
> 	 	
> 2   З поданих пазлів склади і запиши прислів’я. Поясни, як ти його 
> розумієш. Чи можна назвати твоє висловлювання текстом?
> Пригадай і розкажи 
> у класі.
> Я — учителька
> Я — учитель
> Зв’язані за змістом речення 
> становлять текст. До текс

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 6
> ЯК ЧИТАЮТЬ КНИЖКИ?
> Люди читають книжки по-різному. Одні швидко,
> інші — повільно, а деякі так швидко, ніби «ковтають» 
> сторінки.
> Швидкість читання значною мірою залежить від того, 
> що і з якою метою ми читаємо. Скажімо, підручник із 
> математики та збірку казок ти, очевидно, читаєш по-
> різному. Текст задачі, наприклад, треба прочитати не 
> поспішаючи кілька разів, щоб зрозуміти кожне слово, 
> запам’ятати дані, розібратися у змісті запитання. Без 
> цього задачу не розв’яжеш. Казку ж ти читаєш зовсім

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 217
> ТЕМА 2. ПРАВИЛА СПІЛКУВАННЯ.  
> МОНОЛОГІЧНЕ ТА ДІАЛОГІЧНЕ СПІЛКУВАННЯ.  
> СКЛАДАННЯ ДІАЛОГІВ
> 525.	Ознайомтеся з основними правилами спілкування. Поясніть, чому 
> їх потрібно дотримуватися.
> Правила спілкування
>  Бути ввічливими, привітними й доброзичливими.
>  Уважно, не перебиваючи, слухати співрозмовника.
>  Заохочувати співрозмовника до висловлення власної 
> думки.
>  Уміти доброзичливо висловити незгоду з позицією 
> співрозмовника.
>  Не розмовляти без потреби голосно.
>  Не використовувати груби

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 35
> Книжки треба шанувати. Не можна 
> їх бруднити, рвати. Пошкоджені книжки 
> слід полагодити.
> Прочитай і розкажи 
> у класі.
> Я — учителька
> Я — учитель
> Якщо речення вимовляють з особ­
> ливим почуттям, із підсилювальною 
> інтонацією, то вони стають оклич-
> ними. У кінці окличних речень став-
> лять знак оклику.
> 2   Прочитай текст. Визнач, які це речення 
> за метою висловлювання.
> 	 	
> 3   Розгляньте малюнки. Складіть за одним із них невеликий 
> текст, використовуючи окличні речення. Прочитайте його 
> з потріб

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> 27
> 1. Прочитай словосполучення. Нагадай Ґаджикові, до якої 
> частини мови належать виділені слова. Що ти знаєш
> про цю частину мови?   
> розмовляти з друзями  
>         зайти до друзів
> покладатися на друзів 
>         дізнатися від друзів 
> приготувати для друзів 
>         побувати в друзів
> 2. Запиши словосполучення. За потреби скористайся 
> правилом. Підкресли прийменники і познач співзвучні 
> з  ними  префікси.
> 2
> (по) бігти (по) дорозі 
>  
> (з) ліпити (з) пластиліну
> (від) пливти (від) берега 
> (в) лучити (

> **Source:** unknown, Grade 5
> **Score:** 0.33
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

## Я люблю... (I Like...)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 5
> ЩО  Я  ЛЮБЛЮ
> Люблю я маму, люблю тата.
> Люблю я свою рідну хату.
> Люблю...
> 	 	
> 4   Склади невеликий текст «Що я люблю робити», запиши його 
> і підготуйся прочитати у класі.
> 3   Прочитай. Чи можна цей запис назвати завершеним висловлюванням? 
> Чому ти так думаєш?
> 	 	
> 2   З поданих пазлів склади і запиши прислів’я. Поясни, як ти його 
> розумієш. Чи можна назвати твоє висловлювання текстом?
> Пригадай і розкажи 
> у класі.
> Я — учителька
> Я — учитель
> Зв’язані за змістом речення 
> становлять текст. До текс

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> Люблю я осінь, коли опадає (облітає, зеленіє, осипа­
> ється) пожовкле листя. Уночі крізь голе (безлисте, густе) 
> гілля видніються (проглядаються, ясніють, виходять) зорі.
> А вечори... Осінь чарує (зачакловує. сміється, заворо­
> жує) мене й тими смутками, коли разками намиста 
> (коралів) одлітають журавлі у вирій, коли в холодному, 
> ясному осінньому небі і вдень і вночі повно їхнього пла­
> чу: крру! крру!.. (За Степаном Васильченком).
> •  Випишіть підкреслені слова, доберіть до них із дужок синоні­
> ми.

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 129
> подякувати
> звернутися 
> з проханням
> пояснити свій 
> учинок
> порадити
> поділитися 
> досвідом, 
> враженнями
> висловити 
> припущення
> За допомогою складних 
> речень можна реалізувати 
> будь-який комунікативний 
> намір:
> 1. Розкажи мені щось цікаве, щоб я слухав і мав з того 
> користь. 2. Люблю гортати старі книги, бо від них віє спо-
> коєм. 3. Дай мені розуміння і сили прощати, щоб і я був про-
> щений. 4. Люблю писати історії, у яких слова грають, як 
> інструменти в оркестрі. 5. Якщо зробиш крок назад, застряг-

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 144
> Поняття про дієслово як частину 
> мови
> Навчаюся визначати дієслова
> Пригадай і розкажи 
> у класі.
> Я — учителька
> Я — учитель
> писати
> пише
> пишуть
> писав
> написав
> напише
> 45
> Слова, які називають дії предметів і відповідають на 
> питання що робити? що робить? що роблять? що 
> робив? що зробив? що буде робити? що зробить?, 
> є дієсловами. Дієслово — це частина мови.
> 	 	
> 1   Вивчіть напам’ять вірш Володимира Верховеня. Розкажіть одне 
> одному.
>   Випишіть із вірша дієслова за абеткою. Що вони називають? На

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

## Мені подобається... (I Like...)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 5
> ЩО  Я  ЛЮБЛЮ
> Люблю я маму, люблю тата.
> Люблю я свою рідну хату.
> Люблю...
> 	 	
> 4   Склади невеликий текст «Що я люблю робити», запиши його 
> і підготуйся прочитати у класі.
> 3   Прочитай. Чи можна цей запис назвати завершеним висловлюванням? 
> Чому ти так думаєш?
> 	 	
> 2   З поданих пазлів склади і запиши прислів’я. Поясни, як ти його 
> розумієш. Чи можна назвати твоє висловлювання текстом?
> Пригадай і розкажи 
> у класі.
> Я — учителька
> Я — учитель
> Зв’язані за змістом речення 
> становлять текст. До текс

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 6
> ЯК ЧИТАЮТЬ КНИЖКИ?
> Люди читають книжки по-різному. Одні швидко,
> інші — повільно, а деякі так швидко, ні

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Я люблю... (I Like...)` (~300 words)
- `## Мені подобається... (I Like...)` (~300 words)
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

PLAN-AWARE EXEMPTIONS: The following bans are RELAXED for this module because the plan explicitly teaches these constructs: Dative case (plan teaches it). Exception: If a grammar construct appears in this module's plan grammar list or objectives, it is ALLOWED for this module.

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

**Required:** любити (to love/like — verb), подобатися (to be pleasing — used as 'to like'), читати (to read), гуляти (to walk), готувати (to cook), слухати (to listen), дивитися (to watch), грати (to play)
**Recommended:** малювати (to draw), подорожувати (to travel), співати (to sing), музика (music, f), фільм (film, m), книга (book — review from M08)

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
