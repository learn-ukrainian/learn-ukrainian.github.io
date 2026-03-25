# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **21: Checkpoint: Actions** (A1, A1.3 [Actions]).

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
module: a1-021
level: A1
sequence: 21
slug: checkpoint-actions
version: '1.1'
title: 'Checkpoint: Actions'
subtitle: Can you say what you do, want, and ask questions?
focus: review
pedagogy: PPP
phase: A1.3 [Actions]
word_target: 1200
objectives:
- Demonstrate ability to conjugate Group I and Group II verbs
- Use modal verbs (хотіти, могти, мусити) with infinitives
- Ask questions using all 7 question words
- Describe a routine using reflexive verbs and sequence words
- Combine A1.1-A1.3 skills in connected speech
content_outline:
- section: Що ми знаємо? (What Do We Know?)
  words: 200
  points:
  - 'Self-check covering M15-M20: Can you say what you like? (M15) Can you conjugate
    Group I verbs? (M16) Can you conjugate Group II verbs? (M17) Can you say what
    you want, can, and must? (M18) Can you ask questions? (M19) Can you describe your
    morning? (M20)'
- section: Читання (Reading Practice)
  words: 250
  points:
  - 'A short Ukrainian text (8-10 sentences) using ONLY vocabulary from M15-M20. No
    new words. The learner reads aloud. Content: a person describes their day — morning
    routine, work, hobbies. Example: Я прокидаюся о сьомій. Потім вмиваюся і снідаю.
    Я працюю в офісі. Я люблю читати. Увечері я дивлюся фільм.'
- section: Граматика (Grammar Summary)
  words: 200
  points:
  - 'Key patterns from A1.3: 1. Infinitive: -ти (читати, говорити, хотіти) 2. Group
    I: -ю, -єш, -є, -ємо, -єте, -ють 3. Group II: -ю/-у, -иш, -ить, -имо, -ите, -ять
    4. Modals: хочу/можу/мушу + infinitive 5. Questions: хто, що, де, куди, коли,
    чому, як 6. Negation: не + verb; double negation (ніхто не) 7. Reflexive: verb
    + ся (прокидаюся, вмиваюся)'
- section: Діалог (Connected Dialogue)
  words: 300
  points:
  - 'A complete conversation combining all A1.3 skills: Meeting + plans scenario.
    — Привіт! Що ти робиш? — Я читаю книгу. А ти? — Я хочу гуляти. Можеш піти зі мною?
    — Не можу, мушу працювати. Коли ти повертаєшся? — О шостій. — Добре, тоді гуляємо
    ввечері! Uses: both verb groups, modals, questions, reflexive, negation.'
- section: Підсумок — Summary
  words: 250
  points:
  - 'A1.3 achievement summary: You can now talk about actions in Ukrainian. You can
    conjugate verbs in two groups. You can express wants, abilities, and obligations.
    You can ask questions and negate statements. You can describe your daily routine.
    Next: A1.4 — Time and Nature (time, days, weather).'
vocabulary_hints:
  required: []
  recommended: []
activity_hints:
- type: quiz
  focus: 'Mixed conjugation: choose correct form for Group I and II verbs'
  items: 10
- type: fill-in
  focus: Complete the dialogue with modals, questions, and verb forms
  items: 8
- type: fill-in
  focus: 'Describe your day: morning routine → work → evening'
  items: 6
- type: group-sort
  focus: 'Sort verbs by group: Group I vs Group II vs Reflexive'
  items: 12
connects_to:
- a1-022 (What Time?)
prerequisites:
- a1-020 (My Morning)
grammar:
- 'Review: Group I and II conjugation'
- 'Review: modal verbs + infinitive'
- 'Review: question words and negation'
- 'Review: reflexive verbs and sequence words'
register: розмовний
references:
- title: Synthesis of M15-M20 content
  notes: No new material — review and integration of A1.3 phase.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Checkpoint: Actions
**Module:** checkpoint-actions | **Phase:** A1.3 [Actions]
**Textbook grades searched:** 3, 4, 5

---

## Що ми знаємо? (What Do We Know?)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 113
> 317.	 Дослідиѳ речення.
> Крок 1. Прочитай. Яку групу слів можна назвати речен- 
> ням? Обґрунтуй свою відповідь. 
> ЗВ’ЯЗОК СЛІВ У РЕЧЕННІ
> Рудохвостий, білочки, жити, ліс.
> Рудохвості білочки живуть у лісі.
> Крок 2. Установи в реченні зв’язок між словами за допомогою 
> питань:
> Крок 3. Запиши парами слова, зв’язані між собою.  
> Білочки (що роблять?) живуть; живуть (хто?) білочки; 
> білочки (які?) рудохвості; живуть (де?) у лісі. 
> Крок 4. Зроби висновок. Порівняй його з правилом.
> Слова в реченні зв’яза

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

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 30
> УКРАЇНЦІ, ЩО ПІДКОРИЛИ СВІТ
> Попід гору в’ється річка.
> На горі росте смерічка.
> Над смерічкою високо 
> гордий птах кружляє — сокіл.
> Хлопчик ходить понад річку, 
> поглядає на смерічку.
> Хлопчик сокола побачив —  
> серце тьохнуло хлопчаче:
> ох, якби він міг від річки 
> та доплигнуть до смерічки,
> сам зумів би так високо 
> покружлять, як сизий сокіл.
> Хлопчик ходить і не знає,
> що злетить над рідним краєм,
> як зросте, ввібравши в себе, 
> силу річки, гір і неба.
> Він розправить дужі крила — 
> буде в крилах вірна

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> Пригадую знання про звуки і букви . . . . . . . . . . . . . . . . . . . . . . . . . . .4
> Спостерігаю за значенням слів  . . . . . . . . . . . . . . . . . . . . . . . . . . . . 23
> Досліджую будову слова . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 34
> Дізнаюся більше про іменники . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 78
> Досліджую прикметники . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 92
> Розпізнаю числівники  . . . . . . . . . . .

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

## Читання (Reading Practice)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> Здобуваємо інформацію 
> з різних джерел.
> Роз’єднай слова і прочитай.
> Читаємо правильно.
> Досліджуємо текст.
> Міркуємо і відповідаємо.
> Працюємо в групі. 
> Звертаємо увагу.
> Граємо сценку, виставу.
> Фантазуємо і створюємо.
> Дізнаємося значення слів.
> Працюємо в парі.
> УДК 811.161.2*кл3(075.2.)
>  
> С13
> Рекомендовано Міністерством освіти і науки України
> (наказ Міністерства освіти і науки України від 21.02.2020 № 271)
> ISBN 978-966-991-019-6 (Ч. 2)
> ISBN 978-966-991-024-0
> © О. Я. Савченко, 2020
> © УОВЦ «Оріон», 20

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
> 187
> 437   І   Прочитайте текст мовчки. Якщо в ньому є нові для вас сло-
> ва, випишіть їх. Пригадайте, у яких джерелах можна знайти 
> інформацію про значення цих слів.
> Читати й писати людство навчилося якихось 5000 років 
> тому, натомість бігати, полювати, спілкуватися із собі подіб-
> ними за допомогою звуків і жестів — уже сотні тисячоліть.
> Робота мозку під час читання розгортається в кілька ета-
> пів. Що краще розвинена навичка читання, то швидше ми 
> розкодовуємо і розуміємо текст. Однак прискорення

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> Навчальне видання
> САВЧЕНКО Олександра Яківна 
> Українська мова та читання
> Підручник для 3 класу
>  закладів загальної середньої освіти
> (у 2-х частинах)
> Частина 2
> (відповідно до Типової освітньої програми 
> колективу авторів під керівництвом О. Я. Савченко)
> Рекомендовано Міністерством освіти і науки України
> Головний редактор І. В. Красуцька 
> Редактор І. В. Красуцька
> Головний художник І. П. Медведовська
> Технічний редактор Е. А. Авраменко
> Коректори С. В. Войтенко, Л. А. Еско
> Малюнки художниці Олени Хар

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 38
>  
>   
>  
>  
>  
>  
> Лідія  Повх
> У БІБЛІОТЕЦІ
> — Маріє Петрівно,
> чи є у вас казка —
> казка про царівну
> й летючий корабель?
> — Звичайно! Будь ласка,
> ось вона, казка — 
> казка про царівну
> й летючий корабель!
> — Нам дуже потрібний
> збірник задач!
> Маріє Петрівно,
> негайно, хоч плач!
> — Хлопці, спокійно,
> які ви гарячі! 
> Буде вам збірник! 
> Є в нас задачі!
> — Маріє Петрівно,
> нам про Шевченка,
> про те, як в дячка він 
> відвідував клас!
> На святі шкільному 
> ми ставимо сценку.
> Я буду Оксанка,
> Іванко — Тарас!
> — Звичайно, п

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

## Граматика (Grammar Summary)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 34
> Ненаголошені звуки [е] чи [и] в корені слова — це орфограма.
> Орфограма — це правильне написання, яке можна переві-
> рити за допомогою правила або словника.
> Крок 4. Розглянь схеми. Що, на твою думку, потрібно зробити, 
> щоб дізнатися, яку букву, е чи и, потрібно писати в цих 
> словах?
> Гречаѳний — греѳчка, листиѳ — лист, зимоѳвий — зиѳмонька, 
> медоѳвий — мед.
> Крок 5. Зроби висновок, зістав його з правилом.
> Щоб знати, яку букву, е чи и, потрібно писати, слід змінити сло- 
> во або дібрати спільнокоре

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 115
> 	 Порівняй особові закінчення дієслів теперішнього й майбутнього 
> часу в множині. Зверни увагу на виділені букви в

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
