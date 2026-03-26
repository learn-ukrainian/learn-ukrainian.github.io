# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **8: Things Have Gender** (A1, A1.2 [My World]).

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
5. **Place exercise markers only** — do NOT write exercises directly. Place `<!-- INJECT_ACTIVITY: {id} -->` markers where exercises should appear. A separate pipeline step generates the actual exercises from the plan's activity_hints.
6. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
7. **Hit the word target** — you MUST write 1200–1800 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
8. **NO archaic, obsolete, or rare words** — use only modern standard Ukrainian. Do not use words marked as archaic (застаріле) or dialectal in dictionaries. Example: use «кін» not «кон», use «пом'якшені» not «м'якшені». When in doubt, choose the common modern form. Your pre-training contains Russian-influenced archaic forms — verify unfamiliar words.

**Note:** Do NOT add stress marks (´) to any Ukrainian word — a deterministic tool handles this after you write.

## Exercise Placement — Markers Only

**Do NOT write exercises directly.** A separate pipeline step (ACTIVITIES) generates all exercises from the plan's `activity_hints`. Your job is to place markers showing WHERE exercises belong.

### How It Works

1. Read the plan's `activity_hints` — each entry has an `id`, `type`, and `focus`
2. After the relevant teaching section, place an injection marker
3. The ACTIVITIES step reads your prose + the plan hints and generates complete exercises

### Marker Format

Place markers after key teaching sections. Each marker corresponds to ONE `activity_hints` entry from the plan:

```
<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->
```

Rules:
- Use the EXACT `id` from the plan's `activity_hints` — do not invent new IDs
- Place the marker right after the prose that teaches the concept the exercise tests
- Spread markers evenly throughout the module — never cluster them
- If the plan has 4 activity hints, you should place 4 markers in your prose

### Example

If the plan says:
```yaml
activity_hints:
  - id: quiz-sounds-vs-letters
    type: quiz
    focus: "Distinguish звук from літера"
  - id: match-false-friends
    type: match-up
    focus: "Match false friend Cyrillic letters to real sounds"
```

Your prose should contain (after the relevant sections):
```
[...prose about sounds and letters...]

<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->

[...prose about false friend letters...]

<!-- INJECT_ACTIVITY: match-false-friends -->
```

### What NOT to Do

- Do NOT write `:::quiz`, `:::fill-in`, `:::match-up`, or any DSL exercise blocks
- Do NOT write exercise questions, answers, or options — the ACTIVITIES step handles all of this
- Do NOT invent marker IDs — use only IDs from the plan's `activity_hints`

---

## Plan

<plan_content>
module: a1-008
level: A1
sequence: 8
slug: things-have-gender
version: '1.1'
title: Things Have Gender
subtitle: він, вона, воно — every noun has a gender
focus: grammar
pedagogy: PPP
phase: A1.2 [My World]
word_target: 1200
objectives:
- Determine noun gender using the він/вона/воно test
- Recognize gender by word endings (consonant = m, -а/-я = f, -о/-е = n)
- Name 20+ common objects with correct gender
- Use У мене є with objects (extending from M06 family)
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Video call showing your room: — Привіт! Дивись, це моя кімната.
    — Класно! У тебе є стіл? — Так, у мене є стіл і ліжко. Gender emerges naturally
    through мій стіл (m), моя кімната (f), моє ліжко (n).'
  - Dialogue 2 — What's in your bag? — Що у тебе є? — У мене є книга, телефон і фото.
    — А у мене є ручка і зошит.
- section: Він, вона, воно (The Gender Test)
  words: 300
  points:
  - 'Пономарова Grade 3 p.86: Ukrainian nouns have gender. Test: can you replace the
    noun with він, вона, or воно? Чоловічий рід (masculine): стіл — він. Можна додати:
    мій стіл. Жіночий рід (feminine): книга — вона. Можна додати: моя книга. Середній
    рід (neuter): вікно — воно. Можна додати: моє вікно.'
  - 'Вашуленко Grade 3 p.112 — endings by gender: Masculine: usually ends in consonant
    — стіл, телефон, зошит. Feminine: usually ends in -а or -я — книга, лампа, кімната,
    ручка. Neuter: usually ends in -о or -е — вікно, ліжко, крісло, місто. This covers
    ~90% of nouns. Exceptions (like -ь words) come later.'
- section: Предмети навколо (Objects Around Us)
  words: 300
  points:
  - 'Room vocabulary organized by gender: Masculine: стіл (table), стілець (chair),
    телефон (phone), комп''ютер (computer), зошит (notebook), ключ (key). Feminine:
    книга (book), лампа (lamp), сумка (bag), ручка (pen), кімната (room), стіна (wall).
    Neuter: вікно (window), ліжко (bed), крісло (armchair), дзеркало (mirror), фото
    (photo).'
  - 'Extending У мене є from M06 (family) to objects: У мене є стіл. У мене є книга.
    У мене є вікно. Same pattern, new vocabulary.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Gender determination in 3 steps: 1. Say він/вона/воно with the noun — which fits?
    2. Check the ending — consonant? -а/-я? -о/-е? 3. Use the right possessive — мій/моя/моє.
    Self-check: What gender is ''стіл''? What gender is ''книга''? What about ''вікно''?
    Say ''I have a chair'' in Ukrainian.'
vocabulary_hints:
  required:
  - стіл (table, m)
  - книга (book, f)
  - вікно (window, n)
  - кімната (room, f)
  - ліжко (bed, n)
  - стілець (chair, m)
  - лампа (lamp, f)
  - телефон (phone, m)
  - комп'ютер (computer, m)
  - він, вона, воно (he, she, it — gender test words)
  recommended:
  - зошит (notebook, m)
  - ручка (pen, f)
  - сумка (bag, f)
  - крісло (armchair, n)
  - дзеркало (mirror, n)
  - ключ (key, m)
  - фото (photo, n)
  - стіна (wall, f)
activity_hints:
- type: group-sort
  focus: Sort objects into masculine/feminine/neuter
  items: 12
- type: quiz
  focus: він, вона, or воно? Choose for each noun.
  items: 8
- type: fill-in
  focus: мій/моя/моє ___ (match possessive to noun)
  items: 8
- type: quiz
  focus: What gender? Look at the ending.
  items: 6
connects_to:
- a1-009 (What Is It Like?)
prerequisites:
- a1-007 (Checkpoint — First Contact)
grammar:
- 'Noun gender: чоловічий (він, мій), жіночий (вона, моя), середній (воно, моє)'
- 'Gender by ending: consonant=m, -а/-я=f, -о/-е=n'
- У мене є extended to objects (from M06 family)
register: розмовний
references:
- title: Пономарова Grade 3, p.86
  notes: 'Gender test: він/мій, вона/моя, воно/моє.'
- title: Вашуленко Grade 3, p.112
  notes: 'Gender endings table: consonant, -а/-я, -о/-е.'
- title: ULP Season 1, Episode 6 — Gender naturally through family
  url: https://www.ukrainianlessons.com/episode6/
  notes: Gender emerges from possessives already taught.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Things Have Gender
**Module:** things-have-gender | **Phase:** A1.2 [My World]
**Textbook grades searched:** 1, 2, 3

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 5
> УСНЕ І ПИСЕМНЕ МОВЛЕННЯ
> Ти можеш спілкуватись усно 
>  або письмово 
> .
> Назви ситуації, у яких діти спілкуються усно, а в яких — 
> письмово. Розкажи, як ти спілкуєшся в школі.
> Назви те, що допоможе тобі передати повідомлення усно.
> 1
> 2
> читаю
> слухаю
> розповідаю
> пишу
> прощаюся
> вітаюся
> ручка
> олівець
> телефон
> планшет
> мікрофон

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> НАВЧАЮСЯ ЗМІНЮВАТИ СЛОВА — 
> НАЗВИ ПРЕДМЕТІВ
> Я — учителька
> Прочитай і розкажи 
> у класі.
> один — багато^
> Я — учитель
> В українській мові слова можуть називати один 
> предмет або багато предметів.
> тварина 
> рослина
> Додай свої 
> слова.
> 32| Випишіть із лічилки Тамари Коломієць слова — назви 
> предметів.
> один
> багато
> £ Що не так на 
> малюнку?
> Біжить півень із причілка 
> і наспівує лічилку:
> — Раз-два — курчата.
> Три-чотири — зайчата. 
> П'ять-шість — гусаки.
> Сім-вісім — їжаки. 
> Дев'ять-десять — йде лисиця. 
> Нам хо

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 131
> 	
>   Перевірте свої міркування за поданим висновком. 
> крісло
> зручне
> Шукаймо 
> прикметники до назв 
> предметів інтер’єру!
> 	 	
> 3   Склади усну розповідь на тему «Моя кімната», використову-
> ючи іменники з довідки. Добери до іменників прикметники 
> і використай їх у тексті. 
> Кімната, двері, вікно, стеля, стіни, коридор, шафа, стіл, стілець, 
> тумбочка, ліжко, підлога. 
> Довідка
> Навчаюся визначати рід і число прикметників  
> за іменником
> Рід і число прикметників визначаються за формами 
> роду і числа і

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 16
> Й й
> Бачу Й, й (йот). Чую  [й].
> а й в а
>  [ •  =   |  –• ]
> а й с т р и
> * а й в о р о
> а
> о
> и
> і
> Й
> га
> ми
> рі
> Й
> н о к
> лій- 
> 	
> ліній-
> 	
> май- 
> чай- 
> 	
> гай- 
> 	
> чай- 
> мий	
> лий 	
> чай	
> грай
> вимий	
> долий	
> чайник	
> зіграй
> ай
> ой
> ий
> ій
> а
> о
> і
> і
> ч
> й
> д
> м
> й
> Pidruchnyk.com.ua

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> 8
> мова І мовЛЕння 
> мова — це засіб спілкування людей (система звуків 
> і букв, слова, речення, тексти, правила). 
> Мова потрібна, щоб:
> Коли ти розповідаєш про щось, то користуєшся мо-
> вою. Це мовлення. 
> МОВЛЕННЯ
> УСНЕ                               ПИСЕМНЕ
> Я читаю. Я пишу.
> Я говорю. Я слухаю. 
> Привіт!
> Прочитай речення. Спочатку назви ті, у яких ідеться про усне 
> мовлення, потім ті, у яких ідеться про писемне. Спиши ре-
> чення. Зміни речення так, щоб у них про щось запитувалося.
>   Я oлухаЬ gагадку. Я

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 34
>  
> Обговоріть! Для чого існують прислів’я і приказки?
> * * *
> Що тобі не мило, другові не зич.
> Друга шукай, а знайдеш — тримай.
> З добрим дружись, а лихого стережись.
> Нових друзів май, а старих не забувай.
> Прислів’я — це короткий влучний образний 
> вислів, який має повчальний зміст.
> Прислів’я вчить, як на світі жить.
> * * *
> Щоб рибу їсти, треба у воду лізти.
> Хто хоче багато мати, тому треба мало спати.
> Треба нахилитися, щоб із криниці води напитися.
> Любиш кататися — люби й на гору підійматися.
> * *

## Він, вона, воно (The Gender Test)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 47
> Осінь  килим  вишивала,
> Ниточок  пішло  чимало —
> Лис-тя  кле-на  і  ка-ли-ни,
> Ду-ба,  я-се-на,   ма-ли-ни,
> А  між  ни-ми  го-ро-би-на —
> На-че  по-лу-м’я  го-рить!
>                                                 Юлія Ференцева ма
> ом
> му
> мо
> ом
> им
> ми
> [ –•= | –•]
> ми-
> мо-
> ми-
> Що?                               Що робити?
> 	 Визнач, якому слову — назві предмета від-
> повідає схема. 
> 	 Розкажи, для чого використовують ці пред-
> мети.
> Pidruchnyk.com.ua

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> УМОВНІ  ПОЗНАЧЕННЯ
>  — працюємо в парі
>  — працюємо у групі
>  — розвиваємо творчі здібності
>  — словничок
>  — Візьміть до уваги!
> © Вашуленко О. В., 2019
> © Видавничий дiм «Освiта», 2019
>  
> Вашуленко О.  В.
> В23	 	
> Українська мова та читання : підруч. для 2 класу 
> закладів загальної середньої освіти (у 2-х частинах). 
> Ч. 2 / О. В. Вашуленко. — К. : Видавничий дім «Освіта», 
> 2019. — 144 с. : іл.
> 	
> 	 ISBN 978-966-983-013-5.
> УДК 811.161.2*кл2(075.2)
> ISBN 978-966-983-013-5
> УДК 811.161.2*кл2(075.2)
> 	
> В23
> Реко

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

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 21
> Розкажу вам по секрету:
> Хом’ячок жує газету.
> За щоку складає
> Потім  почитає.
> Треба буде ручку дати — 
> Може спробує писати.
> І портфелика. Авжеж.
> В щоки всього не запхнеш…
>                                Світлана Костюк
> 	
> Яку ручку пропонує авторка дати хом’ячкові?
> 	
> Розглянь малюнок. Розкажи, хто на ньому 
> зображений. Який він? Що робить?
> Pidruchnyk.com.ua

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> Інна Большакова
> Марина Пристінська
> УКРАЇНСЬКА МОВА
> ТА ЧИТАННЯ
> ЧАСТИНА 1
> 2 
> КЛАС
> ї
> о
> н
> А
> М

> **Source:** unknown, Grade 3
> **Score:** 0.33
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

## Предмети навколо (Objects Around Us)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 42
> Знайди слово — підпис до малюнка.  
> Відшукай слово до схеми.
> 	 екран	
> лев	
> Ем-ма
> 	 етикет	
> левеня	
> Е-рі-ка
> 	етикетка	
> лелека	
> е-лек-три-ка
> 
> Текст. Тема тексту. Головна думка
> Увечері ти заходиш до кім-
> нати і натискаєш на вимикач. 
> Світло! Від електричної лампи. 
> Вона схожа на скляну грушу. 
> Усередині — нитка з  мета-
> лу. Коли ниткою проходить 
> електричний струм, вона на-
> грівається і світить.
> Чому важливо вимикати електричну лампу, коли нею не 
> користуєшся?
> Розглянь малюнки. Поміркуй, як дже

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> 91
> Доведи, що це текст. Користуйся схемою.
> Є  кілька 
> речень
> Речення розміщені в  пра-
> вильній послідовності
> Речення пов’язані 
> за змістом
> Можна дібрати 
> заголовок
> Ліхтар — це прилад для освітлення. Є ліхтарі вуличні, які 
> освітлюють вулиці і  дороги в  темний час доби. Є  кишенькові 
> ліхтарики, які ми носимо з  собою та вмикаємо, коли потріб-
> но. Є  ліхтарі, якими користуються люди під водою чи під 
> землею. Такі ліхтарі можуть кріпитися на голові. Ліхтар — річ, 
> яка необхідна кожній людині  в

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 39
> Хлопчик, як гномик 
> маленький, в кутку:
> — Чого тобі, любий?
> Книжку яку?
> — Мені — журнали,
> енциклопåдію… 
> Де надрукували 
> про велосипеди!
> Марія Петрівна пішла по драбину
> і зверху знімає журнали сині…
> Марія Петрівна й хвилинки не гає, 
> вона в інтернеті щось довго шукає.
> І тільки під вечір, як школа вже вмîвкла,
> Ма

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Він, вона, воно (The Gender Test)` (~300 words)
- `## Предмети навколо (Objects Around Us)` (~300 words)
- `## Підсумок — Summary` (~300 words)
- `## Підсумок — Summary` (~150 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 10-20% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose. Introduce Ukrainian grammar terms bolded with translation on first use.
- UKRAINIAN CONTENT: Words and short phrases bolded inline: "The word **книга** (book) is feminine."
- TABLES: Vocabulary tables, word families, simple paradigm tables.
- STRUCTURAL RULE: Every paragraph is English. Ukrainian words/phrases appear inline bolded. Full Ukrainian sentences (3+ words with a verb) go in tables or bulleted example lists with English gloss.
Ukrainian sentences max 10 words.

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

GRAMMAR CONSTRAINTS (A1.2 — My World, M08-M14):
Noun gender, adjective agreement, plurals, numbers, demonstratives.

ALLOWED:
- Це + noun, У мене є/немає
- Adjective-noun agreement (nominative only)
- Numbers 1-1000
- Demonstratives цей/ця/це/ці
- Question words: Який? Яка? Яке? Скільки?
- Fixed verbal phrases from A1.1 (Мене звати, працювати)

BANNED: Verb conjugation (taught in A1.3), past/future tense, cases beyond nominative,
participles, passive voice, subordinate clauses

### Vocabulary

**Required:** стіл (table, m), книга (book, f), вікно (window, n), кімната (room, f), ліжко (bed, n), стілець (chair, m), лампа (lamp, f), телефон (phone, m), комп'ютер (computer, m), він, вона, воно (he, she, it — gender test words)
**Recommended:** зошит (notebook, m), ручка (pen, f), сумка (bag, f), крісло (armchair, n), дзеркало (mirror, n), ключ (key, m), фото (photo, n), стіна (wall, f)

### Pronunciation Videos



---

### Style Reference (match this tone and structure)

Look at the text on this page. What you are seeing are letters. Now, say a word out loud. What you just produced is a sound. This distinction is the absolute foundation of the Ukrainian language. There is a golden rule taught to every Ukrainian student in the first grade: **Ми чуємо і вимовляємо звуки, а бачимо і пишемо літери**. We hear and pronounce sounds, but we see and write letters.

These friendly letters are **А**, **О**, **К**, **М**, and **Т**. Because they are so familiar, you can start reading real Ukrainian words immediately. Look at the word **мама**. It means mother, and you already know how to read it. Now look at **тато**. It means father.

*Note: English prose dominates. Ukrainian words appear bolded inline. Short Ukrainian sentences illustrate one concept at a time. No conjugated verbs. Tables and bulleted lists for vocabulary.*



---

## Skeleton — Follow This Structure Exactly

A detailed paragraph-level skeleton was generated for this module. You MUST follow it precisely:
- Write every paragraph listed, in the order listed
- Hit each paragraph's word budget (+-10%)
- Place exercises exactly where the skeleton says
- Use the specific examples named in the skeleton
- Do NOT skip paragraphs, reorder sections, or add unplanned content

The skeleton replaces Step 1 (Pacing Plan) — do NOT output a <pacing_plan> block. Start writing immediately from the first section.

<skeleton>
## Діалоги (Dialogues) (~330 words total)

- P1 (~30 words): Brief scene-setting — Оленка video-calls her friend Марко to show her new room. Context: moving into a new apartment, excited to show everything.

- Dialogue 1 (~110 words): Video call showing your room. Оленка: "Привіт, Марку! Дивись, це моя кімната!" Марко: "О, класно! Велика кімната! У тебе є стіл?" Оленка: "Так, у мене є стіл. Ось мій стіл. А ось моє ліжко." Марко: "А лампа є?" Оленка: "Так, моя лампа ось тут. І є вікно — моє вікно велике!" Марко: "А комп'ютер?" Оленка: "Так, мій комп'ютер на столі." Gender emerges naturally through мій стіл (m), моя кімната (f), моя лампа (f), моє ліжко (n), моє вікно (n). Post-dialogue gloss: 3-4 sentences pointing out мій/моя/моє pattern — "Did you notice? Оленка says мій стіл but моя лампа and моє ліжко. Why?"

- P2 (~20 words): Transition to second dialogue — next day at university, Оленка and Марко compare what's in their bags before class.

- Dialogue 2 (~100 words): What's in your bag? Марко: "Що у тебе в сумці?" Оленка: "У мене є книга, ручка і зошит. А у тебе?" Марко: "У мене є телефон, ключ і фото." Оленка: "Фото? Яке фото?" Марко: "Моє фото з Києва!" Post-dialogue gloss: 3-4 sentences highlighting that книга (вона), ручка (вона) vs. телефон (він), ключ (він) vs. фото (воно) — three different groups. "Ukrainian nouns belong to three groups. Let's learn how to tell them apart."

- P3 (~70 words): Dialogue debrief — pull out key vocabulary from both dialogues. List the objects that appeared: стіл, кімната, ліжко, лампа, вікно, комп'ютер, книга, ручка, зошит, телефон, ключ, фото. Note that some feel like "він" words, some like "вона" words, some like "воно" words. Tease the pattern: "How do Ukrainian speakers know? There's a simple test."

## Він, вона, воно (The Gender Test) (~330 words total)

- P1 (~90 words): Introduce the він/вона/воно test (ref: Пономарова Grade 3 p.86, Вашуленко Grade 3 p.110). Every Ukrainian noun has a gender — чоловічий рід (masculine), жіночий рід (feminine), or середній рід (neuter). The test: replace the noun with він, вона, or воно. Demonstrate with стіл → він (стіл), книга → вона (книга), вікно → воно (вікно). Reinforce with мій/моя/моє: мій стіл, моя книга, моє вікно. "If you can say він about it, it's masculine. If вона — feminine. If воно — neuter."

- P2 (~100 words): Expand with more examples from the dialogues. Walk through 6 nouns one by one using the test: телефон — він, мій телефон (masculine); лампа — вона, моя лампа (feminine); ліжко — воно, моє ліжко (neuter); зошит — він, мій зошит (masculine); ручка — вона, моя ручка (feminine); крісло — воно, моє крісло (neuter). Emphasize that this isn't about biological gender — стіл is він not because tables are male, but because that's how the word works in Ukrainian. Every noun has a grammatical gender.

- Exercise 1: **quiz** — він, вона, or воно? Choose the correct pronoun for each noun. 8 items: стілець, сумка, дзеркало, ключ, стіна, фото, комп'ютер, кімната.

- P3 (~140 words): The ending shortcut (ref: Вашуленко Grade 3 p.112). You don't always need the test — the ending tells you. Present the three patterns as a clear rule: **Чоловічий рід (він, мій):** ends in a consonant — стіл, телефон, зошит, стілець, ключ, комп'ютер. **Жіночий рід (вона, моя):** ends in -а or -я — книга, лампа, сумка, ручка, кімната, стіна. **Середній рід (воно, моє):** ends in -о or -е — вікно, ліжко, крісло, дзеркало, фото. Note: this covers the vast majority of nouns at this level. Some words ending in -ь (like тінь) are trickier — we'll learn those later. For now, consonant = він, -а/-я = вона, -о/-е = воно.

## Предмети навколо (Objects Around Us) (~330 words total)

- P1 (~100 words): Room vocabulary organized by gender — present as a "tour of your room." Masculine (він, мій): стіл (table), стілець (chair), телефон (phone), комп'ютер (computer), зошит (notebook), ключ (key). For each word, a short phrase: "Мій стіл великий. Мій стілець зручний." Feminine (вона, моя): книга (book), лампа (lamp), сумка (bag), ручка (pen), кімната (room), стіна (wall). "Моя книга цікава. Моя лампа яскрава." Neuter (воно, моє): вікно (window), ліжко (bed), крісло (armchair), дзеркало (mirror), фото (photo). "Моє вікно велике. Моє ліжко зручне."

- Exercise 2: **group-sort** — Sort 12 objects into three columns: чоловічий рід / жіночий рід / середній рід. Items: стіл, книга, вікно, телефон, лампа, ліжко, ключ, ручка, крісло, зошит, сумка, дзеркало.

- P2 (~90 words): Extending У мене є from M06 (family) to objects. In Module 6 you learned "У мене є мама, у мене є тато." Same pattern works for things: "У мене є стіл. У мене є книга. У мене є вікно." Show 6 example sentences mixing all three genders. Then combine with possessives: "У мене є мій стіл. У мене є моя книга. У мене є моє ліжко." Point out that in casual speech, Ukrainians often drop мій/моя/моє with У мене є — but the gender is still there in the noun.

- Exercise 3: **fill-in** — мій, моя, or моє? Complete 8 sentences: "___ стіл," "___ книга," "___ вікно," "___ телефон," "___ лампа," "___ крісло," "___ сумка," "___ ключ."

- P3 (~70 words): Mini-dialogue practice — two friends comparing rooms. "У мене є комп'ютер, а у тебе?" "У мене немає комп'ютера, але є дзеркало." Brief note: немає (don't have) is the opposite of є — preview only, full explanation later. Focus stays on recognizing gender through the nouns and possessives used in natural exchanges about what people have in their rooms.

- Exercise 4: **quiz** — What gender? Look at the ending. 6 items with new nouns not yet drilled: парта (desk, f), олівець (pencil, m), місто (city, n), школа (school, f), рюкзак (backpack, m), море (sea, n). Tests whether learners can apply the ending rule to unfamiliar words.

## Підсумок — Summary (~210 words total)

- P1 (~120 words): Gender determination in 3 steps — consolidate everything. Step 1: Say він, вона, or воно with the noun — which sounds right? Step 2: Check the ending — consonant → чоловічий рід (він, мій); -а/-я → жіночий рід (вона, моя); -о/-е → середній рід (воно, моє). Step 3: Use the right possessive — мій for він-words, моя for вона-words, моє for воно-words. Quick reference table showing all three genders with 3 example nouns each. Remind: this works for ~90% of nouns. The few exceptions will come in later modules.

- P2 (~90 words): Self-check questions to test understanding. "What gender is стіл? (він — masculine, ends in consonant). What gender is книга? (вона — feminine, ends in -а). What about вікно? (воно — neuter, ends in -о). Say 'I have a chair' in Ukrainian. (У мене є стілець.) What possessive goes with кімната? (моя)." Bridge to next module: "Now you know that every noun has a gender. In the next module, we'll learn adjectives — words like великий, нова, гарне — and you'll see how they change to match the noun's gender."

Grand total: ~1200 words (330 + 330 + 330 + 210 = 1200, with natural overshoot from dialogues and examples pushing toward ~1320)
</skeleton>

## Output Format

Write in Markdown. Use:
- `## Section Title` for main sections
- `### Subsection` for subsections within a section
- `**bold**` for Ukrainian words being taught — EVERY bold Ukrainian word MUST have an English translation on first use, either in parentheses `**слово** (translation)` or inline `**слово** means "translation"`. No exceptions.
- Tables for paradigms (conjugation, declension)
- `:::tip` / `:::caution` / `:::note` for callout boxes
- `<!-- INJECT_ACTIVITY: {id} -->` for exercise placement (markers only — do NOT write exercise content)

Do NOT write MDX component syntax, JSON, or DSL exercise blocks (:::quiz, etc.). Plain Markdown with injection markers.

Begin writing now. Start with the first section heading.
