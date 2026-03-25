# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **27: Checkpoint: Time and Nature** (A1, A1.4 [Time and Nature]).

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
module: a1-027
level: A1
sequence: 27
slug: checkpoint-time-nature
version: '1.2'
title: 'Checkpoint: Time and Nature'
subtitle: Can you tell time, plan a week, and describe the weather?
focus: review
pedagogy: PPP
phase: A1.4 [Time and Nature]
word_target: 1200
objectives:
- Demonstrate ability to tell time and use "at" + time expressions
- Name days, months, and seasons with correct preposition chunks
- Describe weather using impersonal constructions
- Tell a coherent story about a typical day
- Discuss hobbies and make plans using frequency words
content_outline:
- section: Що ми знаємо? (What Do We Know?)
  words: 200
  points:
  - 'Self-check covering M22-M26: Can you tell time? (M22) Can you name days and months?
    (M23) Can you describe the weather? (M24) Can you describe your day? (M25) Can
    you talk about hobbies? (M26)'
- section: Читання (Reading Practice)
  words: 250
  points:
  - 'A short Ukrainian text (8-10 sentences) using vocabulary from M22-M26. Content:
    a person describes their typical week — schedule, weather, hobbies. Example: У
    понеділок я працюю з дев''ятої до п''ятої. У вівторок вивчаю українську. Влітку
    я часто гуляю. Взимку ходжу в кіно. Мені подобається осінь.'
- section: Граматика (Grammar Summary)
  words: 200
  points:
  - 'Key patterns from A1.4: 1. Time: Котра година? О котрій? (ordinal chunks) 2.
    Days: у понеділок, в суботу (accusative chunks) 3. Months: у січні, в серпні (locative
    chunks) 4. Seasons: взимку, навесні, влітку, восени 5. Weather: холодно, тепло,
    іде дощ, іде сніг 6. Sequence: спочатку, потім, нарешті 7. Frequency: завжди,
    часто, іноді, рідко, ніколи'
- section: Діалог (Connected Dialogue)
  words: 300
  points:
  - 'A complete conversation combining all A1.4 skills: Planning a weekend outing.
    — Яка завтра погода? — Тепло і сонячно. — Чудово! Ходімо в парк! О котрій? — О
    десятій ранку. — Добре! Я часто гуляю в суботу. — А потім ходімо в кіно! — О п''ятій?
    — Так! Uses: time, day, weather, invitation, frequency.'
- section: Підсумок — Summary
  words: 250
  points:
  - 'A1.4 achievement summary: You can now talk about time, schedules, and the world
    around you. You can tell time and plan meetings. You can name all days, months,
    and seasons. You can describe the weather. You can tell a story about your day.
    You can discuss hobbies and make plans. Next: A1.5 — Places (city, directions,
    transport).'
vocabulary_hints:
  required: []
  recommended: []
activity_hints:
- type: fill-in
  focus: Mixed review of time, days, and weather chunks
  items:
  - Зустріч {о п'ятій|в п'ятій|у п'ята} годині.
  - Ми йдемо в кіно {у суботу|в суботі|на суботу}.
  - Мій день народження {у січні|в січень|січень}.
  - Сьогодні {іде дощ|іде дощова|дощить}, візьми парасольку.
  - Взимку дуже {холодно|спекотно|тепло}.
  - Я прокидаюся о сьомій {ранку|рано|вранці}.
- type: match-up
  focus: Match the questions to logical answers
  pairs:
  - Котра година? ↔ Десята тридцять.
  - О котрій зустріч? ↔ О першій.
  - Яка сьогодні погода? ↔ Тепло і сонячно.
  - Коли твій день народження? ↔ У жовтні.
  - Що ти робиш у суботу? ↔ Граю у футбол.
  - Як часто ти читаєш? ↔ Щодня ввечері.
  - Ходімо в парк! ↔ Добре, о котрій?
  - Що ти будеш робити завтра? ↔ Буду працювати.
- type: fill-in
  focus: Complete the paragraph describing a day
  items:
  - '{Спочатку|Потім|Нарешті} я прокидаюся і снідаю.'
  - '{Потім|Вранці|Вночі} я йду на роботу.'
  - Я працюю з дев'ятої {до|і|по} п'ятої.
  - '{Після обіду|Вранці|Вночі} я гуляю в парку.'
  - Я гуляю, тому що сьогодні {тепло|холодно|дощ} і сонячно.
  - '{Ввечері|Вдень|Вранці} я вечеряю і слухаю музику.'
  - '{Нарешті|Спочатку|Потім} я лягаю спати о дванадцятій.'
connects_to:
- a1-028 (Euphony)
prerequisites:
- a1-026 (Free Time)
grammar:
- 'Review: time expressions and ordinal chunks'
- 'Review: calendar vocabulary with prepositions'
- 'Review: impersonal weather constructions'
- 'Review: sequence and frequency words'
register: розмовний
references:
- title: Synthesis of M22-M26 content
  notes: No new material — review and integration of A1.4 phase.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Checkpoint: Time and Nature
**Module:** checkpoint-time-nature | **Phase:** A1.4 [Time and Nature]
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
> 79
> 4   Пригадай назви днів тижня. Запиши їх правильно, користуючись 
> орфографічним словником.  
> 5   Знайди у тлумачному словнику значення 
> трьох невідомих тобі слів і запиши їх.
> 	 	
> 6   Запиши подані слова в абетковій 
> послідовності.
> 	 	
> 3   Прочитайте прізвища сучасних українських 
> дитячих письменників та письменниць.
> 	
>   Запиши ці прізвища в абетковій послідовності.
> 	
>   З допомогою дорослих назви твори цих авторів (авторок). 
> 	
>   Підкресли орфограми  у словах.
> 	
>   Спробуй скласти речен

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
> ЛЮБІ ДІВЧАТКА І ХЛОПЧИКИ!
> У новому підручнику з літературного читання 
> ви прочитаєте різні твори — народні й авторські. 
> У казках, віршах, оповіданнях відкриєте цікавий світ 
> природи й дитинства, дізнаєтесь про те, як виникла
> й  розвивалась  наша  мова,  створювалися  книжки.
> Ознайомитеся з новими для вас видами текстів —
> п’єсою, байкою, науково-художнім оповіданням.
> Прочитаєте твори про почуття, які об’єднують нас; 
> про історію рідного краю, видатних людей; про те, де 
> знайти і як працювати з і

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
> 30
> ТЕКСТ. РЕЧЕННЯ. СЛОВО (ПОВТОРЕННЯ)
> Сполучники сполучають однорідні члени речення та частини складно-
> го речення: казки й легенди; Приказка навчає мудрості, а загадка роз-
> виває мислення (сполучає → сполучник). Решта службових слів — частки. Вони додають словам відтінків (на­
> віть я встиг, саме він, знав же, майже дочитав); надають заперечно-
> го значення (не буду, ні з ким, ані в кого); за допомогою них також 
> утворюють граматичні форми слів (хай читають, читала б). 3. Перепишіть приказки та в

## Граматика (Grammar Summary)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> Узагальнюю знання про числівник як частину мови
> Скільки годин триває доба? 
> Скільки годин триває день сьогодні? 
> Скільки годин триває ніч сьогодні?
> 	 	
> 12   Постав замість цифри числівник, щоб утворилися слова.
> 14   Дай письмові відповіді на запитання.
> 13   Склади і запиши два речення з числівником три. Виконай розбір 
> цього числівника як частини мови за зразком.
>   Склади подібну задачу і запропонуй її розв’язати своїм однокласникам 
> (однокласницям).
>   Запиши утворені слова, прочитай їх для

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> •  Складіть текст-розповідь за малюнком і словосполученнями. 
> Запишіть. Підкресліть словосполучення, яким позначено час.
> Правильно вимовляємо, пишемо, відпові

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

TARGET: 15-30% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — explain the grammar concept once, clearly.
- EXAMPLES: Ukrainian sentences in bulleted lists (each line: Ukrainian — English gloss). Max 2-4 per rule.
- TABLES: Paradigm tables, case endings, vocabulary groups — all cells Ukrainian.
- PATTERN BOXES: Show transformations: `книга → книгу` (nominative → accusative).
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences go in tables, bulleted lists, or pattern boxes.
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

GRAMMAR CONSTRAINTS (A1.4 — Time & Nature, M22-M28):
Time expressions, days, months, weather, daily routines.

ALLOWED:
- All present tense (from A1.3)
- Time expressions as chunks (О першій, У понеділок)
- Sequence adverbs (спочатку, потім, нарешті)
- Impersonal weather constructions (Сьогодні холодно)

BANNED: Past/future tense, case endings (time chunks only),
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
