# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **46: Holidays** (A1, A1.7 [Communication]).

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
module: a1-046
level: A1
sequence: 46
slug: holidays
version: '1.1'
title: Holidays
subtitle: Різдво, Великдень, День Незалежності — Ukrainian celebrations
focus: cultural
pedagogy: PPP
phase: A1.7 [Communication]
word_target: 1200
objectives:
- Name and describe major Ukrainian holidays (Різдво, Великдень, День Незалежності)
- Use holiday greetings appropriately (З Різдвом! З Великоднем! З Днем Незалежності!)
- Talk about what people do on holidays using known vocabulary
- Understand the cultural significance of Ukrainian holidays
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Before Christmas: — Коли в тебе Різдво? — Двадцять п''ятого грудня.
    А в тебе? — У нас — теж! Раніше святкували сьомого січня, але тепер — двадцять
    п''ятого. — Що ви робите на Різдво? — Ми співаємо колядки і їмо кутю. — Як гарно!
    З Різдвом! — З Різдвом Христовим! Різдво vocabulary: колядки (carols), кутя (kutia
    — ritual dish), святкувати.'
  - 'Dialogue 2 — Independence Day: — Двадцять четверте серпня — День Незалежності!
    — Так, це головне державне свято України. — Що ви робите? — Ми дивимося парад
    і ходимо на концерт. — А ввечері? — Ввечері — салют і святковий вечір з друзями.
    — З Днем Незалежності! — Слава Україні! National holiday: парад, концерт, салют.'
- section: Українські свята (Ukrainian Holidays)
  words: 300
  points:
  - 'Різдво (Christmas) — December 25: Ukraine moved Christmas from January 7 to December
    25 in 2023. January 7 was the Russian Orthodox date; December 25 aligns with Europe.
    Traditions: Свята вечеря (Holy Supper) on December 24 — 12 страв (12 dishes).
    кутя (kutia) — wheat porridge with honey and poppy seeds — the first dish. колядки
    (carols) — traditional Christmas songs. Колядники go door to door.'
  - 'Великдень (Easter): The biggest religious holiday. Date changes each year (spring).
    Traditions: писанки (decorated eggs — unique Ukrainian art), паска (Easter bread),
    святити кошик (blessing the Easter basket at church). Greeting: Христос воскрес!
    — Воістину воскрес! (Christ is risen! — Indeed risen!)'
- section: Державні свята (National Holidays)
  words: 300
  points:
  - 'День Незалежності — August 24, 1991: Ukraine declared independence from the Soviet
    Union. The most important державне свято (national holiday). Celebrations: парад
    (parade), концерти, салют (fireworks), прапори (flags). Greeting: З Днем Незалежності!
    (Happy Independence Day!) Слава Україні! — Героям слава! (Glory to Ukraine! —
    Glory to the heroes!)'
  - 'Other holidays to know: Новий рік (New Year) — January 1 — biggest secular celebration.
    Вишиванковий день (Vyshyvanka Day) — third Thursday of May. Everyone wears вишиванка
    (embroidered shirt) — symbol of Ukrainian identity. День Конституції (Constitution
    Day) — June 28. День захисників і захисниць (Defenders'' Day) — October 1.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Holiday greetings pattern: З + instrumental case! З Різдвом! (Merry Christmas!)
    З Великоднем! (Happy Easter!) З Новим роком! (Happy New Year!) З Днем Незалежності!
    З днем народження! (Happy birthday!) Pattern: З + [holiday/occasion in instrumental]
    + ! You already know instrumental from з + noun (кава з молоком). Here it''s the
    same: ''with'' the holiday → instrumental. Quick calendar: грудень 25 — Різдво,
    січень 1 — Новий рік, весна — Великдень, серпень 24 — День Незалежності. Self-check:
    How do you say ''Merry Christmas'' and ''Happy New Year''?'
vocabulary_hints:
  required:
  - свято (holiday, n)
  - святкувати (to celebrate)
  - Різдво (Christmas, n)
  - Великдень (Easter, m)
  - Новий рік (New Year)
  - вітати (to congratulate/greet)
  recommended:
  - кутя (kutia, f)
  - колядка (carol, f)
  - писанка (decorated Easter egg, f)
  - паска (Easter bread, f)
  - парад (parade, m)
  - прапор (flag, m)
  - вишиванка (embroidered shirt, f)
  - незалежність (independence, f)
  - салют (fireworks, m)
activity_hints:
- type: quiz
  focus: 'Match holiday to date: Різдво → 25 грудня, День Незалежності → 24 серпня'
  items: 8
- type: fill-in
  focus: 'Greetings: З ___! (Різдвом, Великоднем, Новим роком)'
  items: 8
- type: quiz
  focus: Which holiday? Кутя, колядки, Свята вечеря → (Різдво / Великдень / Новий
    рік)
  items: 8
- type: group-sort
  focus: 'Sort traditions by holiday: Різдво vs Великдень vs День Незалежності'
  items: 10
connects_to:
- a1-047 (Checkpoint — Communication)
prerequisites:
- a1-045 (When and Where)
grammar:
- 'З + instrumental for holiday greetings: З Різдвом! З Великоднем!'
- 'Review: dates (М18), instrumental chunks (М36)'
register: розмовний
references:
- title: ULP Season 1, Episode 23
  url: https://www.ukrainianlessons.com/episode23/
  notes: Ukrainian holidays and celebrations.
- title: State Standard 2024, §3 (традиції)
  notes: 'Thematic area: traditions, holidays, cultural practices.'

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Holidays
**Module:** holidays | **Phase:** A1.7 [Communication]
**Textbook grades searched:** 5, 6, 7

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 114
> Комунікативні можливості речень
> 291   Прочитайте текст. Про що в ньому йдеться? Які емоції викликає 
> у вас це свято? Які очікування і передчуття у вас напередодні 
> Різдва? Які речення за метою висловлювання використовує 
> письменниця? Чому? Напишіть, що для вас означає це свято.
> Різдво для мене — це не просто біблійний сюжет, можли-
> вість замислитися над мудрістю Божого промислу, занурити-
> ся в його барвистість. Це набагато більше. Бо моєму Різдву 
> не одна тисяча літ. Воно з житніх нив та з т

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> Підсумки та саморефлексія  
> 249
> Про що говорять слова
> Дати можна записувати кількома способами: 10  лю-
> того 2024 року, 10 лютого 2024 р., 10.02.2024, 10.02.24. 
> Для уникнення непорозумінь рекомендовано дати до 
> десятого числа записувати двома цифрами: 01, 02...
> Проєкт
> Презентуйте в класі результати своєї роботи над про-
> єктом. Прокоментуйте, які числівники ви використали 
> у своєму плані подорожі, до яких розрядів вони на-
> лежать; розкажіть про особливості їхнього правопису. 
> Оцініть результати

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> 118
> 118
> комісією. 5. Рушник для подарунка вишито Оксаною. 6. На
> новорічне свято учнями нашого класу підготовлено цікаву ви-
> ставу. 7. Пиріг до дня народження спечено бабусею.
> СИТУАЦІЯ.
> І. Відновіть і запишіть прислів’я та приказки, уставляючи на місці пропуску
> дієслівні форми на -но, -то (оберіть із поданих у рамці).
> помазано  /  набуто   /  написано  /  писано  /  бито
> 1. На роду ... . 2. За наше жито ще нас і ... . 3. Неначе ме-
> дом ... . 4. Вилами по воді ... . 5. Як ... , так і збуто. 
> ІІ. П

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> РОЗДІЛ 2
> 52
> А
> Б
> В
> Г
> Д
> Е
> 4.	 ІСТОРИЧНИЙ І КАЛЕНДАРНИЙ ЧАС
> Розгадайте ребус. Що ви знаєте про закодоване в ребусі поняття? 
> Де ви з ним зустрічалися в житті? Навіщо ця річ потрібна людині? Ви-
> словіть припущення, яку роль відіграє закодована річ у вивченні історії.
> Поміркуймо!
> Історичний час не слід плутати з календарним часом.
> Календар — це система відліку часу, яка ґрунтується 
> на астрономічних явищах: зміні пір року, обертанні Землі 
> навколо Сонця та зміні фаз Місяця.
> Також календарем називають

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 25
> НАРОДНІ КАЛЕНДАРНО-ОБРЯДОВІ ПІСНІ
> стилем, 7 січня за новим стилем). У колядках цього періоду 
> прославляють Сина Божого, а також змальовують образ 
> Діви Марії, яка народила Ісуса. 
> Щедрівка – це величальна пісня, яку виконують на 
> Щедрий вечір (Маланку) напередодні Нового року. Цього 
> вечора (31 грудня за старим стилем, 13 січня за новим сти-
> лем) господині варили кутю, накривали багатий стіл, для 
> якого можна було готувати й м’ясні страви, а не лише пісні, 
> як на Святвечір. Молодь, переважно

> **Source:** unknown, Grade 7
> **Score:** 0.33
>
> Розділ 4  ПРИСЛІВНИК
> 160
> Підсумкові тести
> Виконайте тестові завдання.
> 1   Прислівниками є  обидва слова в  рядку
> А  вечеря, увечері
> Б  зранку, рано
> В літній, літувати
> Г половина, наполовину
> 2  Прислівник є  в реченні
> А Шановні відвідувачі зоопарку, годувати тварин заборо-
> нено.
> Б Обережно, двері зачиняються.
> В Кінцева станція. Шановні пасажири, не залишайте свої 
> речі.
> Г Пані та панове, ми розпочинаємо. Переведіть свої теле-
> фони у беззвучний режим.
> 3  Прислівник є  в усіх реченнях, ОКРІМ
> А Усі

## Українські свята (Ukrainian Holidays)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> Розділ 1. МИСТЕЦЬКИЙ СПАДОК НАЩАДКАМ
> 62
> не знав, що воно за дівка. Стали ліпити шишки; та дівка злі­
> пила з тіста голуба й голубку та й пустила додолу, а вони 
> ожили. Голубка й почала говорити до голуба:
> — А ти забув, як я за тебе луг викорчовувала й там пшеницю 
> сіяла, а з тієї пшениці паляницю спекла, щоб ти до змії відніс?
> А голуб каже:
> — Забув, забув!
> Потім знову голубка каже:
> — А ти забув, як я за тебе гору розкопувала й туди Дніпро 
> пустила, щоб човни ходили до комор і щоб ти пшеницю про­

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> 27
> НАРОДНІ КАЛЕНДАРНО-ОБРЯДОВІ ПІСНІ
> Застеляйте столи, 
> та все килимами. (Приспів)
> Та кладіть калачі 
> з ярої пшениці. (Приспів)
> Бо прийдуть до тебе 
> три празники в гості. (Приспів)
> Ой перший же празник – 
> то Різдво Христове. (Приспів)
> А другий же празник – 
> Василя святого. (Приспів)
> А третій же празник – 
> Святе Водохреща. (Приспів)
> А що перший празник 
> зішле тобі віку. (Приспів)
> А що другий празник 
> зішле тобі щастя. (Приспів)
> А що третій празник 
> зішле всім нам долю. (Приспів)
> ÙÅÄÐÈÊ, ÙÅÄÐÈÊ, Ù

> **Source:** unknown, Grade 7
> **Score:** 0.50
>
> 252
> 252
> 5. Чи вдалось автору, на вашу думку, в образі козака втілити гіркі роздуми про
> історичну долю батьківщини? Чи допомагає колірна гама підкреслити глибину й
> складність цих роздумів? 
> ІІІ. Складіть колективно складний план твору-опису зовнішності козака за поданою
> картиною. Напишіть твір-опис, використавши одиничний дієприкметник і дієприкмет-
> никовий зворот. Ви можете скористатися поданим нижче лексичним матеріалом.
> ЛЕКСИЧНИЙ МАТЕРІАЛ. Мужня вдача, борець за народну волю, розду-
> ми про дол

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 155
> Писанка випромінює радість, красу, тепло рук людини 
> (За Т. Глушенком).
> ІІ. Складіть словосполучення зі словами писанка, музей, орнамент. 
> 380.	І. Поєднайте й запишіть слова правої та лівої колонок так, щоб 
> спочатку вийшло словосполучення, а потім – фразеологізм. 
> заварити
> кашу
> каву
> народитися
> восени
> в сорочці
> ІІ. Поміркуйте, що означає кожен фразеологізм.  
> 381.	Заповніть пропуски в реченнях одним із наведених у рамці слів, 
> утворивши правильне словосполучення з виділеним словом. 
> 1. Ти ме

> **Source:** unknown, Grade 6
> **Score:** 0.33
>
> 25
> НАРОДНІ КАЛЕНДАРНО-ОБРЯДОВІ ПІСНІ
> стилем, 7 січня за новим стилем). У колядках цього періоду 
> прославляють Сина Божого, а також змальовують образ 
> Діви Марії, яка народила Ісуса. 
> Щедрівка – це величальна пісня, яку виконують на 
> Щедрий вечір (Маланку) напередодні Нового року. Цього 
> вечора (31 грудня за старим стилем, 13 січня за новим сти-
> лем) господині варили кутю, накривали багатий стіл, для 
> якого можна було готувати й м’ясні страви, а не лише пісні, 
> як на Святвечір. Молодь, переважно

> **Source:** unknown, Grade 7
> **Score:** 0.33
>
> 90
> Розділ 2. І ДИТИНСТВО, Й РОЗЛУКА, Й ТВОЯ МАТЕРИНСЬКА ЛЮБОВ 
> І твоя незрадлива материнська ласкава усмішка,
> І засмучені очі хороші, блакитні твої.
> Я візьму той рушник, простелю, наче долю,
> В тихім шелесті трав, в щебетанні дібров.
> І на тім рушничкові оживе все знайоме до болю:
> І дитинство, й розлука, і вірна любов.
> І на тім рушничкові оживе все знайоме до болю:
> І дитинство, й розлука, й твоя материнська любов.
> Ö²ÊÀÂÎ ÇÍÀÒÈ
> Вишитий рушник – це не просто 
> предмет побуту, а й важливий еле-
> мент в

## Державні свята (National Holidays)

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 229
> Відомості із синтаксису й пунктуації. Кома між однорідними членами речення
> й родової пам’яті, любові та святковості; оберегом і захистом 
> від лихого ока та слова.
> Елементи української вишивки все частіше використо-
> вують у дизайні сучасного одягу. Не лише українці, а й гол-
> лівудські красуні залюбки вбирають ніжну вишиту вдяган-
> ку. Тепер носити вишиванку стало не тільки патріотично, 
> а й модно та ексклюзивно.
> (За матеріалами сайту «Еспресо»)
> 2. Знайдіть у  тексті однорідні члени речення .
> 3

> **Source:** unknown, Grade 6
> **Score:** 0.50
>
> Розділ 5. Іменник 
> 124
> 7. Найменування історичних подій, знаменних дат, 
> загальнонародних свят (із великої літери пишемо 
> перше слово): День захисників і  

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Українські свята (Ukrainian Holidays)` (~300 words)
- `## Державні свята (National Holidays)` (~300 words)
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

GRAMMAR CONSTRAINTS (A1.7 — People & Communication, M44-M50):
Vocative, imperative, dative, conjunctions, subordinate clauses.

ALLOWED:
- Vocative case (Олено! Тарасе!)
- Imperative mood (Читай! Скажіть! Дайте!)
- Dative case basics (мені, тобі, йому)
- Conjunctions (і, а, але, бо, тому що)
- Simple subordinate clauses (що, де, коли, якщо)
- All cases and tenses from previous phases

BANNED: Past/future tense, participles, passive voice

### Vocabulary

**Required:** свято (holiday, n), святкувати (to celebrate), Різдво (Christmas, n), Великдень (Easter, m), Новий рік (New Year), вітати (to congratulate/greet)
**Recommended:** кутя (kutia, f), колядка (carol, f), писанка (decorated Easter egg, f), паска (Easter bread, f), парад (parade, m), прапор (flag, m), вишиванка (embroidered shirt, f), незалежність (independence, f), салют (fireworks, m)

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
