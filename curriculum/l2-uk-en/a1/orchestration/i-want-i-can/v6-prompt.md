# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **18: I Want, I Can** (A1, A1.3 [Actions]).

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
module: a1-018
level: A1
sequence: 18
slug: i-want-i-can
version: '1.1'
title: I Want, I Can
subtitle: Хочу, можу, мушу — expressing wants and abilities
focus: grammar
pedagogy: PPP
phase: A1.3 [Actions]
word_target: 1200
objectives:
- Use хотіти (want), могти (can), мусити (must) + infinitive
- Express desires, abilities, and obligations in present tense
- Handle irregular conjugation of хотіти and могти
- Build practical sentences for everyday needs
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Making plans: — Що ти хочеш робити? — Я хочу гуляти. А ти? — Я не
    можу, я мушу працювати. — Шкода! All three modals in one natural exchange.'
  - 'Dialogue 2 — At a café (preview for A1.6): — Я хочу каву. — Велику чи маленьку?
    — Велику. І ще я хочу їсти. Що ви можете порекомендувати? — Можу порекомендувати
    борщ! Хотіти + noun (no infinitive needed).'
- section: Хотіти (To Want)
  words: 300
  points:
  - 'Хотіти is irregular — it belongs to Group I despite -іти ending: я хочу, ти хочеш,
    він/вона хоче, ми хочемо, ви хочете, вони хочуть. Note: хот- → хоч- (т→ч change
    in all forms). Two uses: хочу + infinitive (Я хочу читати) or хочу + noun (Я хочу
    каву).'
  - 'Negative: Я не хочу. Ти не хочеш? Вона не хоче. Polite requests use хотів/хотіла
    би (conditional) — but that''s later. For now: Я хочу... is the direct way to
    express a want.'
- section: Могти і мусити (Can and Must)
  words: 300
  points:
  - 'Могти (can/able to) — also irregular: я можу, ти можеш, він/вона може, ми можемо,
    ви можете, вони можуть. Note: мог- → мож- (г→ж change). Я можу говорити українською.
    Ти можеш допомогти?'
  - 'Мусити (must/have to) — regular Group II: я мушу, ти мусиш, він/вона мусить,
    ми мусимо, ви мусите, вони мусять. Note: с→ш only in я-form (мушу), rest is regular.
    Я мушу працювати. Ти мусиш вчити слова. Мусити = obligation, not choice. Stronger
    than ''треба'' (impersonal, later).'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Three modals + infinitive: Хочу + inf. = I want to (desire) Можу + inf. = I can
    (ability) Мушу + inf. = I must (obligation) All three: Я хочу гуляти, але не можу
    — мушу працювати. Self-check: Say what you want to do today. Say what you can
    do in Ukrainian. Say what you must do tomorrow.'
vocabulary_hints:
  required:
  - хотіти (to want — irregular!)
  - могти (to be able/can — irregular!)
  - мусити (to must/have to)
  - кава (coffee, f)
  - їсти (to eat)
  recommended:
  - шкода (pity, unfortunately)
  - допомогти (to help)
  - борщ (borscht, m)
  - порекомендувати (to recommend)
  - треба (need to — impersonal, preview)
activity_hints:
- type: fill-in
  focus: 'Conjugate: я хоч__, ти хоч__, він хоч__'
  items: 9
- type: quiz
  focus: Хочу, можу, or мушу? Choose the right modal for the situation.
  items: 8
- type: fill-in
  focus: 'Complete: Я ___ гуляти, але не ___ — ___ працювати.'
  items: 6
- type: quiz
  focus: Regular or irregular? Identify the conjugation pattern.
  items: 6
connects_to:
- a1-019 (Questions)
prerequisites:
- a1-017 (Verbs Group II)
grammar:
- 'Modal verbs: хотіти, могти, мусити + infinitive'
- 'Irregular conjugation: хот-→хоч-, мог-→мож-'
- 'Мусити: regular Group II except я-form (мушу)'
- Хотіти + noun (Я хочу каву) vs хотіти + infinitive (Я хочу їсти)
register: розмовний
references:
- title: Караман Grade 10, p.179
  notes: Хотіти listed as Group I exception (despite -іти infinitive).
- title: Літвінова Grade 7, p.55
  notes: 'Exceptions: хотіти, гудіти, ревіти, іржати — Group I despite -іти.'

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: I Want, I Can
**Module:** i-want-i-can | **Phase:** A1.3 [Actions]
**Textbook grades searched:** 3, 4, 5

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 16
> 2.	 Як ви гадаєте, слово туфелька однозначне чи бага-
> тозначне? Обговоріть це питання. Свою дискусію розпо-
> чинайте словами:
> Я гадаю, що … .
> Я погоджуюся / не погоджуюся з тобою, тому що … .
> 40.
> Випиши з хрестоматії для читання два речення. Підкресли 
> в кожному реченні по одному слову. Досліди за допо-
> могою тлумачного словника, скільки значень мають ці 
> слова.
> 41.	
> 1.	 Пригадай! Слова можуть мати пряме та переносне 
> значення.
> 2.	 Дослідиѳ, яке значення записують у тлумачному слов-
> нику споча

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 1
> 53. 1. Прочитай текст. Що цікавого ти дізнався / дізналася?
> Хочеш здійснити подорож у часі? Тоді уяви себе в старовин­
> ному місті. Як ти гадаєш, де можна побачити найбільше людей? 
> Так, на торжку
> *!
> Ось стельмах продає вози та сани. Ось підійшов гутник. Він 
> виготовляє скло та вироби зі скла.
> Сьогодні все по-іншому. Відповідно — інші професії. Напри­
> клад, коуч або коучка допомагають іншим досягнути поставленої 
> мети. Маркетолог або маркетологйня організовують продаж 
> товарів чи послуг. Дієтол

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 237
> Шукаємо відповіді на запитання:
> 1   Що спільного й відмінного між суперечкою і сваркою?
> 2   Які слова спричиняють конфлікт?
> 533   Прочитайте «слова дня». Що вони означають? Чи можуть ці слова 
> стати причиною сварки й погіршення стосунків? Відповідь 
> обґрунтуйте.
> Суперåчка — зіткнення різних позицій і думок, у якому 
> кожна сторона аргументовано захищає свою позицію і 
> спростовує докази інших. У результаті суперечки учас-
> ники її можуть схилятися до чиєїсь думки, а можуть 
> залишатися зі своєю,

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 89
> 1.	 Прочитай. Розкажи, що б ти хотів / хотіла удосконалити у своє- 
> му помешканні.
> Будинок-мандрівник
> Сучасні архітектори пропонують 
> не лише будинки нових форм, а й оригі-
> нальні способи їх пересування. Зовсім 
> скоро з’являтимуться будинки-мандрів- 
> ники. Набридло жити біля моря, закор-
> тіло подихати лісовим повітрям — викли-
> каєш спеціальну бригаду. Вона робить 
> підкоп, протягує під будинком гумові 
> подушки, надуває їх. І будинок… злітає! 
> Ну, не злітає, а піднімається над землею. 
> Тепер йо

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> уживає такі слова: не переймайтеся, не хвилюйтеся, про0
> шу, усе нормально.
> Уміння чемно відмовитися чи погодитися — теж мис6
> тецтво спілкування. Невміння делікатно відмовитися мо6
> же образити людину. У ситуації відмови користуються
> висловами: дякую, але я сьогодні маю інші справи; спа0
> сибі, але наступним разом; вибачте, але я, на жаль,
> не зможу. Якщо ж погоджуємося з чимось, то викорис6
> товуємо такі вислови: я із задоволенням приймаю Вашу
> пропозицію; щиро дякую; мені приємно, що я теж можу
> бути

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 199
> 462   Прочитайте речення. Визначте комунікативний намір мовців 
> (прохання, умовляння, благання, клянчення чи пропозиція). 
> Обґрунтуйте свій вибір. На  яке прохання ви відгукнулися б? 
> Хто з мовців найкраще обґрунтував свої бажання?
> 1. Мамо, купи мені цю іграшку, купи, купи, купи, купи!!! 
> У Вероніки є точнісінько така, і я хочу! Купи-и-и-и!!! 
> 2. Дідусю, благаю, візьми мене з собою в похід на Говерлу! 
> Я ще там ніколи не був! 3. Тату, можна я не буду пристібатися 
> паском безпеки?! Я ж не мал

## Хотіти (To Want)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 60
> 5.	 Чи правильно зробила білочка, що організувала колек-
> тивний подарунок?
> 6.	 Що потрібно зробити, щоб клас був дружним? Напиши.
> Зразок. 
> На мою думку, кожен із нас мріє мати багато друзів. 
> Але, на жаль, є діти, яким важко спілкуватися в колективі. Їх 
> необхідно підтримати. Можна просто підійти і поговорити, пожар-
> тувати і погратися. І тоді дитина відчує себе потрібною, а колектив 
> стане дружним.
> 3.	 Прочитайте твір однокласника / однокласниці. Скажіть, що 
> вам найбільше сподобалося в його

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 98
> Розрізняймо вживання слів обоє, обидва, обидві. Ка-
> жуть обоє тоді, коли мають на увазі він і вона. Обидва 
> вживають, коли мають на увазі він і він; обидві — вона 
> і вона. Наприклад: Петрику чотири роки. Обидва бра-
> ти старші за нього. Обидві сестри — танцюристки. Їх 
> люб­лять обоє — і тато, і мама. 
> Спілкуймося красно
> 	 Зверни увагу на виділене в лічилці слово. Визнач, хто веде бесіду.
> 238.		Прочитай закодовані займенники.
> 	
> 	
> — 1-ша особа, Ор. в., однина;
> 	
> 	
> — 3-тя особа, М. в., однина;

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 115
> Дайте, будь ласка, три квитки до ... .
> Харків
> Миколаїв
> Канів
> Львів
> Тетіїв
> Чугуїв 
> Фастів
> Бориспіль
> ЗРАЗОК. Дайте, будь ласка, три квитки до Бердичева.
> 280.	І. Спишіть слова, уставляючи на місці пропуску букву е або и. По-
> ясніть орфограми, покликаючись на правила написання е, и в коренях 
> слів та відомості про чергування голосних звуків.
> 1. Вит..рати, вит..рти, вист..лю, вист..лати. 2. Сп..кти, 
> пол..тіти, поч..пити. 
> ІІ. Прокоментуйте чергування звуків у словах. 
> Можу – мігши, вела – вівши,

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 89
> 1.	 Прочитай. Розкажи, що б ти хотів / хотіла удосконалити у своє- 
> му помешканні.
> Будинок-мандрівник
> Сучасні архітектори пропонують 
> не лише будинки нових форм, а й оригі-
> нальні способи їх пересування. Зовсім 
> скоро з’являтимуться будинки-мандрів- 
> ники. Набридло жити біля моря, закор-
> тіло подихати лісовим повітрям — викли-
> каєш спеціальну бригаду. Вона робить 
> підкоп, протягує під будинком гумові 
> подушки, надуває їх. І будинок… злітає! 
> Ну, не злітає, а піднімається над землею. 
> Тепер йо

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> 111
> Зразок. Класти: однина: 1-ша особа — я клад у ; 2-га осо­
> ба — ти клад еш ; 3-тя особа — він, вона, воно клад е ; 
> множина: 1-ша особа — ми клад емо , 2-га особа — ви 
> клад ете , 3-тя особа — вони клад  уть . 
> 263.		Прочитай вірш.
> Біжать, біжать хмариночки
> По небу вдалечінь
> І кидають від сонечка
> Свою легеньку тінь.
> А сонечко всміхається,
> Цілує гай і сад,
> І в листя одягається
> Зелений виноград.
> 	
> 	
> 	
> 	
> 	
>  О. Журлива
> 	 Випиши дієслова, укажи час, число й особу за зразком поперед­
> ньої вправи.
> 2

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 199
> 462   Прочитайте речення. Визначте комунікативний намір мовців 
> (прохання, умовляння, благання, клянчення чи пропозиція). 
> Обґрунтуйте свій вибір. На  яке прохання ви відгукнулися б? 
> Хто з мовців найкраще обґрунтував свої бажання?
> 1. Мамо, купи мені цю іграшку, купи, купи, купи, купи!!! 
> У Вероніки є точнісінько така, і я хочу! Купи-и-и-и!!! 
> 2. Дідусю, благаю, візьми мене з собою в похід на Говерлу! 
> Я ще там ніколи не був! 3. Тату, можна я не буду пристібатися 
> паском безпеки?! Я ж не мал

## Могти і мусити (Can and Must)

> **Source:** unknown, Grade 3
> **Score:** 0.50
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
> **Score:** 0.50
>
> Могутнє море — в..лике, бе..межне, бе..мірне. Ти пов­
> не величі, (дихати) тихо й спокійно, бо (знати), що немає 
> краю твоїй могутності. Уночі на тебе (дивитися)

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Хотіти (To Want)` (~300 words)
- `## Могти і мусити (Can and Must)` (~300 words)
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

**Required:** хотіти (to want — irregular!), могти (to be able/can — irregular!), мусити (to must/have to), кава (coffee, f), їсти (to eat)
**Recommended:** шкода (pity, unfortunately), допомогти (to help), борщ (borscht, m), порекомендувати (to recommend), треба (need to — impersonal, preview)

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
