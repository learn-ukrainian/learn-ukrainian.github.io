# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **19: Questions** (A1, A1.3 [Actions]).

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
module: a1-019
level: A1
sequence: 19
slug: questions
version: '1.1'
title: Questions
subtitle: Хто? Що? Де? — asking about the world
focus: grammar
pedagogy: PPP
phase: A1.3 [Actions]
word_target: 1200
objectives:
- Ask questions using хто, що, де, куди, коли, чому, як
- Use negation with не (verb) and ні (nothing/nobody)
- Form yes/no questions with intonation (no word order change)
- Combine question words with verbs from M16-M18
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Getting to know someone (extending M05): — Хто ти? — Я студент.
    — Що ти вивчаєш? — Я вивчаю українську. — Де ти живеш? — Я живу в Києві. — Коли
    ти приїхав? — Місяць тому. Question words demonstrated in real conversation.'
  - 'Dialogue 2 — Lost in the city (preview for A1.5): — Де бібліотека? — Я не знаю.
    — А хто знає? — Запитай там. — Чому? — Тому що там працює мій друг. Questions
    + negation in practical context.'
- section: Питальні слова (Question Words)
  words: 300
  points:
  - 'Seven essential question words: Хто? (Who?) — Хто це? Хто говорить? Що? (What?)
    — Що це? Що ти робиш? Де? (Where?) — Де ти живеш? Де книга? Куди? (Where to?)
    — Куди ти йдеш? Коли? (When?) — Коли ти працюєш? Чому? (Why?) — Чому ти не працюєш?
    Як? (How?) — Як справи? Як тебе звати?'
  - 'Word order: question word + verb + subject (flexible): Де ти живеш? = Ти де живеш?
    (both acceptable). Yes/no questions: just raise intonation at the end: Ти говориш
    українською? ↑ (no special word needed). Чи ти говориш? — formal/written (optional
    for A1).'
- section: Заперечення (Negation)
  words: 300
  points:
  - 'Не = not (before verb): Я не знаю. Він не працює. Ми не розуміємо. Не goes directly
    before the verb — never separated. Review: Я не хочу. Мені не подобається. (from
    M15, M18)'
  - 'Ні = no (standalone) / nothing, nobody (with pronouns): Ні, я не знаю. (No, I
    don''t know.) Нічого (nothing), ніхто (nobody), ніколи (never), ніде (nowhere).
    Double negation is REQUIRED in Ukrainian: Я нічого не знаю. (literally: I nothing
    don''t know = I don''t know anything.) Ніхто не говорить. (Nobody speaks.) — unlike
    English, both не and ні- are needed.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Questions: Хто? Що? Де? Куди? Коли? Чому? Як? Yes/no: intonation only (Ти знаєш?
    ↑) Negation: не before verb (Я не знаю). Double negation: Ніхто не знає. Я нічого
    не бачу. Self-check: Ask 3 questions about a friend (Де...? Що...? Коли...?).
    Make 2 negative sentences (Я не... / Ніхто не...).'
vocabulary_hints:
  required:
  - хто (who)
  - що (what)
  - де (where)
  - куди (where to)
  - коли (when)
  - чому (why)
  - як (how)
  - не (not)
  - ні (no)
  recommended:
  - ніхто (nobody)
  - нічого (nothing)
  - ніколи (never)
  - жити (to live)
  - розуміти (to understand)
  - тому що (because)
activity_hints:
- type: quiz
  focus: 'Choose the right question word: ___ ти живеш? (Де/Що/Хто)'
  items: 8
- type: fill-in
  focus: 'Make it negative: Я знаю → Я не знаю, Хтось знає → Ніхто не знає'
  items: 8
- type: match-up
  focus: 'Match question to answer: Де ти живеш? ↔ У Києві.'
  items: 6
- type: quiz
  focus: 'Double negation: choose the correct Ukrainian sentence.'
  items: 6
connects_to:
- a1-020 (My Morning)
prerequisites:
- a1-018 (I Want, I Can)
grammar:
- 'Question words: хто, що, де, куди, коли, чому, як'
- Yes/no questions with rising intonation
- 'Negation: не before verb'
- 'Double negation: ніхто не + verb, нічого не + verb'
register: розмовний
references:
- title: Варзацька Grade 4, p.41
  notes: Question words in case system context (хто? що? кого? чого?).
- title: ULP Season 1, Episode 35
  url: https://www.ukrainianlessons.com/episode35/
  notes: Questions in Ukrainian — word order and intonation.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Questions
**Module:** questions | **Phase:** A1.3 [Actions]
**Textbook grades searched:** 3, 4, 5

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> Частини  мови
> У розділі ти будеш вивчати:
> ІМЕННИКИ
> хто? що?
> який? яка? 
> яке? які?
> що робить? 
> що роблять?
> скільки?  
> котрий?
> ЧИСЛІВНИКИ
> ДІЄСЛОВА
> ПРИКМЕТНИКИ

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> 4
> 	 Розглянь фото Оксани. Чому в неї поганий настрій? Як можна її 
> втішити? 
> 	 Склади й запиши кілька речень про очікування від навчання в 
> цьому році.
> 3.	 	Розгляньте діаграму. Прочитайте назви розділів, які ви буде-
> те вивчати в 4 класі. 
> Діаграма — це малюнок, креслення чи графічне зображення, 
> подані як певні позначення об’єктів і понять, що порівнюються, 
> і можуть показувати відношення між ними.
> Мова і мовлення.
> Українська абетка:
> звуки та букви
> Іменник
> Прикметник
> Числівник
> Займенник
>  Діє

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

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 17
> 8. Разом з однокласниками/однокласницями дайте відпо-
> відь на запитання Читалочки.
> 5. Запиши пари слів з попереднього завдання, встав
> пропущені букви. Підкресли перевірні слова.
> 5
> 7. Прочитай прислів’я. Поясни, як їх розумієш. Спиши 
> речення. Встав пропущені букви, добираючи перевірні 
> слова.
> 7
> 1. Ж..ття без кн..жок, як в..сна без квітів.
> 2. Золото добувають із з..млі, а знання — із кн..жок.
> 9. Прочитай текст. Чи є в ньому щось таке, чого ви не назва-
> ли, відповідаючи на запитання Читалочки?

> **Source:** unknown, Grade 4
> **Score:** 0.33
>
> ДОБРИДЕНЬ, УЧНІВСЬКА СПІЛЬНОТО!
> Ось і вересень. Розпочинається цікаве навчання. Разом ми 
> помандруємо стежками рідної мови. У цій подорожі знаходити­
> мемо відповіді на запитання, проводитимемо дослідження слів, 
> речень, текстів, поглибимо свої знання та неодноразово пере­
> свідчимось у силі українського слова.
> Готові? Тоді до подорожі під назвою «ЗНАННЯ»!
> Умовні позначення
> Д — початок уроку
> — домашнє завдання
> — мовно-логічні завдання
> ¿V — дослідження мовних явищ
> Ш — робота в парі, групі
> — цікаві

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> 8
> У цьому розділі ми поговоримо про таке: 
>  Для чого нам потрібна мова та чому її варто вивчати?
>  Чому мову називають основним засобом спілкування?
>  Чому українцям важливо розмовляти 
> українською  мовою?
> ВСТУП. 
> УКРАЇНСЬКА  МОВА  В  ЖИТТІ  УКРАЇНЦІВ

## Питальні слова (Question Words)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> Частини  мови
> У розділі ти будеш вивчати:
> ІМЕННИКИ
> хто? що?
> який? яка? 
> яке? які?
> що робить? 
> що роблять?
> скільки?  
> котрий?
> ЧИСЛІВНИКИ
> ДІЄСЛОВА
> ПРИКМЕТНИКИ

> **Source:** unknown, Grade 4
> **Score:** 0.50
>
> •  Поясніть написання великої букви в словах. Поставте виді­
> лені дієслова в множині.
> 337. Розгляньте таблицю змінювання дієслів теперішнього часу в 
> однині та множині за особами.
> ОДНИНА
> МНОЖИНА
> Особа
> Питання
> Приклад
> Особа
> Питання
> Приклад
> 1-ша
> 1-ша
> я
> ЩО
> пливу
> ми
> ЩО
> пливемо
> 2-га
> роблю?
> кричу
> 2-га
> робимо?
> кричимо
> ти
> що
> пливеш
> ви
> що
> пливете
> 3-тя
> робиш?
> кричиш
> 3-тя
> робите?
> кричите
> він, вона,
> що
> пливе
> вони
> що
> пливуть
> воно
> робить?
> кричить
> роблять?
> кричать
> 4 , •  Зверніть увагу на особові закінчення. П

> **Source:** unknown, Grade 5
> **Score:** 0.50
>
> 274
> Словник термінів
> Питальне речення  — речення, яке містить запитання й  ви-
> мовляється з  питальною інтонацією. У  кінці питального 
> речення ставимо знак питання.
> Підмет — головний член речення, який указує на предмет чи 
> особу, що є  виконавцем дії або носієм стану, і  відповідає 
> на  питання хто? що?
> Приголосні звуки  — звуки, які вимовляємо за  допомогою 
> голосу та  шуму або тільки шуму.
> Приказка  — короткий влучний вислів, що образно називає 
> якесь життєве явище, наприклад: або пан, або п

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
> 123
> 293.		Прочитай слова.
> (що?) Добро, (який?) добрий, (… ?) добре;
> (що?) низина, (який?) низький, (… ?) унизу;
> (що?) ранок, (який?) ранній, (… ?) уранці;
> (що?) далечінь, (який?) далекий, (… ?) здалеку.
> 	 Визнач частини мови, які ти знаєш. Постав питання до підкрес-
> лених слів.
> 	 Спиши підкреслені прислівники, укажи в дужках питання.
> 294.		Прочитай сполучення дієслів із прислівниками.
> Світить (як?) яскраво, … ; світить (де?) високо, …. ; хо-
> дить (як?) тихо, … ; співає (як?) весело, … ; прокинув

> **Source:** unknown, Grade 5
> **Score:** 0.33
>
> Ч а с т и н и   м о в и
> Самостійні 
> Іменник 
> сонце
> хто? що?
> Прикметник
> сонячний, мамин
> який? чий?
> Числівник
> три, третій
> скільки? котрий?
> Займенник
> я, ти, він
> хто? що?
> Дієслово
> сидіти
> що робити? що зробити?
> Прислівник 
> сонячно, восени
> як? де? коли? куди?
> Службові
> Прийменник
> на, в, з, до
> Не відповідають на 
> питання
> Сполучник
> і, й, та, але
> Частка
> не, б, хай
> В и д и  р е ч е н ь
> За метою 
> висловлювання
> За емоційним 
> забарвленням
> За будовою
> розповідне
> окличне
> просте
> питальне
> неокличне
> складне
> спонука

## Заперечення (Negation)

> **Source:** unknown, Grade 3
> **Score:** 0.50
>
> 56
> 18
> Протилежні за значенням  
> слова — антоніми
> Розпізнаю протилежні 
> за значенням слова
> Пригадай і розкажи 
> у класі.
> Я — учителька
> Я — учитель
> Слова, які мають протилежне зна-
> чення, називаються антонімами.
> вечір — ранок
> сидіти — стояти
> вгорі — внизу
> день — ніч
> Хто швидше відгадає загадку?
> Чорна корова всіх людей поборола.
> А білий віл усіх людей побудив.
> Нових друзів май,
> Більше думай,
> Ледачий голодний,
> плакати
> схід
> запитання
> мовчати
> швидкий
> а працьовитий ситий.
> а менше говори.
> а старих не заб

> **Source:** unknown, Grade 4
> **Score:** 0.50
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
> **Score:** 0.50
>
> 28
> Багатозначне слово може мати кілька антонімічних пар. 
> ПОРІВНЯЙМО:
>  тихий (який здійснюється повільно) – швидкий;
>  тихий (який звучить слабо) – голосний;
>  тихий (без хвилювання) – тривожний.
> Є спеціальні словники антонімів. 
> Антоніми допомагають:
> чітко розрізнити поняття
> висловити протилежні думки
> яскраво й образно показати різні явища
> Зверніть ув

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Питальні слова (Question Words)` (~300 words)
- `## Заперечення (Negation)` (~300 words)
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

PLAN-AWARE EXEMPTIONS: The following bans are RELAXED for this module because the plan explicitly teaches these constructs: Subordinate clauses (plan teaches them). Exception: If a grammar construct appears in this module's plan grammar list or objectives, it is ALLOWED for this module.

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

**Required:** хто (who), що (what), де (where), куди (where to), коли (when), чому (why), як (how), не (not), ні (no)
**Recommended:** ніхто (nobody), нічого (nothing), ніколи (never), жити (to live), розуміти (to understand), тому що (because)

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
