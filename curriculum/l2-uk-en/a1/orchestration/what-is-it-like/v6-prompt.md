# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **9: What Is It Like?** (A1, A1.2 [My World]).

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
module: a1-009
level: A1
sequence: 9
slug: what-is-it-like
version: '1.2'
title: What Is It Like?
subtitle: Великий стіл, нова книга — describing things
focus: grammar
pedagogy: PPP
phase: A1.2 [My World]
word_target: 1200
objectives:
- Use adjectives that agree with nouns in gender (nominative case only)
- Ask "What kind?" with який/яка/яке
- Describe objects and rooms using common adjective pairs
- Build descriptive sentences combining M08 nouns with M09 adjectives
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Describing a room (Вашуленко Grade 3 p.131 ''Моя кімната''): — Яка
    твоя кімната? — Моя кімната велика і світла. — А стіл? — Стіл новий. А ліжко —
    старе. Adjective agreement emerges from real description.'
  - 'Dialogue 2 — Shopping (window shopping): — Дивись, яка гарна сумка! — Так, але
    вона дорога. — А цей телефон? — Він великий і дешевий.'
- section: Який? Яка? Яке? (What kind?)
  words: 300
  points:
  - 'The question ''What kind?'' changes by gender — same pattern as мій/моя/моє:
    Який стіл? (m) → Великий стіл. Яка книга? (f) → Нова книга. Яке вікно? (n) → Чисте
    вікно.'
  - 'Пономарова Grade 3 p.98: Adjective has the same gender as the noun. Masculine:
    -ий (великий, новий, чистий) Feminine: -а (велика, нова, чиста) Neuter: -е (велике,
    нове, чисте) Soft-stem adjectives (-ій/-я/-є like синій) come in M10 Colors. This
    pattern will reappear in every case — learn it well now.'
- section: Прикметники (Common Adjectives)
  words: 300
  points:
  - 'Taught in pairs (opposites — easier to remember): великий ↔ маленький (big ↔
    small) новий ↔ старий (new ↔ old) гарний ↔ поганий (nice/beautiful ↔ bad) чистий
    ↔ брудний (clean ↔ dirty) дорогий ↔ дешевий (expensive ↔ cheap) світлий ↔ темний
    (light ↔ dark)'
  - 'Building descriptions with M08 objects: У мене є великий стіл. Моя кімната маленька,
    але гарна. Вікно велике і чисте. Стілець старий, а ліжко — нове. Note: ''а'' =
    and/but (contrast), ''і'' = and (parallel).'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Self-check: What ending does a masculine adjective have? (-ий/-ій) Feminine?
    (-а/-я) Neuter? (-е/-є) Describe your room in 3 sentences using adjectives.'
vocabulary_hints:
  required:
  - який, яка, яке (what kind? — m/f/n)
  - великий (big)
  - маленький (small)
  - новий (new)
  - старий (old)
  - гарний (nice, beautiful)
  - чистий (clean)
  - дорогий (expensive)
  - дешевий (cheap)
  recommended:
  - поганий (bad)
  - брудний (dirty)
  - світлий (light, bright)
  - темний (dark)
  - а (and/but — contrast)
  - але (but)
activity_hints:
- type: fill-in
  focus: 'Add correct adjective ending: нов__ книга, велик__ стіл, чист__ вікно'
  items: 10
- type: match-up
  focus: 'Match adjective opposites: великий ↔ маленький'
  items: 6
- type: quiz
  focus: Який/яка/яке? Choose correct question word.
  items: 6
- type: fill-in
  focus: Describe the room using given nouns and adjectives
  items: 6
connects_to:
- a1-010 (Colors)
prerequisites:
- a1-008 (Things Have Gender)
grammar:
- Adjective-noun agreement in nominative (-ий/-а/-е pattern)
- Question words який/яка/яке/які
- Adjective opposites as vocabulary strategy
- а (contrast) vs і (parallel)
register: розмовний
references:
- title: Пономарова Grade 3, p.98
  notes: '''Прикметник має такий рід, як іменник, з яким він зв''язаний.'''
- title: Вашуленко Grade 3, p.128-131
  notes: Adjective agreement exercises, 'Моя кімната' description task.

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: What Is It Like?
**Module:** what-is-it-like | **Phase:** A1.2 [My World]
**Textbook grades searched:** 1, 2, 3

---

## Діалоги (Dialogues)

> **Source:** unknown, Grade 1
> **Score:** 0.50
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
> **Score:** 0.50
>
> 8. Так, навіть, подарував (подарувала), я, квіти, 
> акторці.
> 9. Варто, виставу, подивитися, мені, і?
> 10. Цю, обов'язково, виставу, подивитися, варто.
> 11. За, дякую, пораду.
> 16 Прочитайте вітальну листівку. Складіть і запишіть 
> вітання своїм друзям до Нового року за цим зразком. 
> Використовуйте слова — назви дій (дієслова).
> • Озвучте свої вітання для класу.
> Любий друже! / Люба подружко!
> Вітаю тебе з Новим роком! Бажаю 
> чудово провести зимові канікули: 
> відвідати театр, прочитати цікаву 
> книжку, зу

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
> **Score:** 0.33
>
> 30
> Що ти відчуваєш, коли споглядаєш світлини?
> Що робить кожне фото привабливим?
> Чи все вдалося фотографові?
> Чи ти хотів би (хотіла б) щось змінити? На котрому фото?
> Що відчувають твої однокласники (однокласниці), 
> споглядаючи ці світлини?
> Чи віриш ти цьому медіапродукту? Чому?
> Яку інформацію ти з нього отримав (отримала)?
> 	 	
>   Добери світлину «Моє дозвілля». З допомогою дорослих 
> підготуйте у класі фотовиставку на цю тему.
> Що я знаю? 
> 	 	
>   Чим текст відрізняється від групи окремих речень?

## Який? Яка? Яке? (What kind?)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 66
> Знайди букви Я і я в рядку.
> Я 
> Ф 
> В 
> Р 
> я 
> р 
> ф 
> ь 
> я 
>  
>  яб 
> яв 
> яг 
> яд 
> яз 
> як 
> ял 
> ям 
> ян 
> яп
>  яр 
> яс 
> ят 
> ях 
> яш 
> ящ 
> яб 
> яв 
> яг 
> яд
>  
> Знайди слово — підпис до малюнка. 
>  
> ягода 
> яма 
> ясен 
> маяк
>  
> ялина 
> явір 
> язик 
> мрія
>  
> яблуня 
> якір 
> ящик 
> надія
>  
> Буква я позначає два звуки [йа] на початку слова і складу.
> М А|Я К
> Я К
> [й а]
> [й а]
> «Зайві» слова
>  Над болотом летить яблуко, крапля, чапля.
>  У вазі стояла конвалія, мелодія, паляниця.
>  У дворі росла парасоля, тополя, яблуня.
> 1
> 2
> 3
> 4
> Я я
> я

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> 36
> Запиши слова з буквою ї. Визнач звуки, які позначає буква ї.
> Мій — мої, твій — твої, вія — вії, лілія — лілії, лінія — лінії.
>  
> Утвори і запиши речення за зразком.
> Зразок. Колюче їжаченя з’їло слимака.
> Колючий
> Колюча
> Колюче
> Колючі
> їжак
> їжачиха
> їжаченя
> їжаки
> їсть
> з’їла
> з’їло
> їдять
> слимака.
> жука.
> равлика.
> черв’яка.
>  
> Редагуємо
> Їжак і жаба допомагають 
> садівнику поїдати комах. 
>  
> Запиши речення на вибір, у якому: 1) пояснюється, чому їжак 
> не робить запаси на зиму; 2) описується поведінка їжачка

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

> **Source:** unknown, Grade 1
> **Score:** 0.33
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
> **Score:** 0.33
>
> Як ти розумієш виділені рядки?
> Чого вчать наука, мрія та школа?
> До чого закликає авторка вірша?
> Що означає вислів вирости Людиною?
> Що має стати другом для кожної дитини? Свої міркування 
> висловлюй за зразком:
> Книжка — найкращий друг людини. Я так вважаю, тому що....
> Наприклад, .... Отже, ... (зроби висновок).
> Читати можна з різною інтонацією: радісно чи сумно, 
> захоплено чи розчаровано. Це залежить від ситуації.
> Прочитай прислів’я з різною інтонацією. *_2 X
> • Гостре словечко коле сердечко.
> Прочи

> **Source:** unknown, Grade 3
> **Score:** 0.33
>
> 27
> Уранці, коли Юрко прокинувся, то найперше, що побачив, 
> була книжка. Він обережно взяв її в руки і ледь стримався, щоб 
> не закричати на весь дім. За ніч книжка знову стала, мов нова.
> — Мабуть, вона мене пробачила. Оце диво! — подумав 
> Юрчик.
> Він хутенько сів на стільчик, дістав із полиць іще кілька 
> книжок та звернувся до них словами, як до живих істот:
> — Я вас також обов’язково прочитаю, ви лишень не обра-
> жайтеся. Домовились?
> — Із ким ти там розмовляєш? — почувся голос мами. — 
> Час умиватис

## Прикметники (Common Adjectives)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 46
> 	
> Упиши  пропущену  букву. Прочитай слова.
> 	
> Хто що малює? Створи речення (усно).
> 	
> Прочитай скоромовку повільно, швидко, ще 
> швидше.
> Ходить посмітюха 
> по смітничку зі своїми
> посмітюшенятами (нар. тв.).
> Юля
> Юрко
> Юстина
> Любомир
>     Я
> в и ш и в а
> с п і в а
> ч и т а
> г р а
> 	 Відшукай нові слова.
> Л Ю Б И С Т О К
> 1 2 3 4 5 6 7 8
> 1 4 5 6 7 8
> 1 4 5 6
> Pidruchnyk.com.ua

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> РОЗПОДІЛЯЮ СЛОВА НА ГРУПИ
> б| Згрупуй близькі за значенням слова і запиши їх.
> великий 
> розумний 
> метикований 
> вєлєтЄнський 
> дотепний
> мудрий 
> гігантський 
> кмітливий 
> безмежний
> ч*  -
> ■и
> групую
> доповнюю
> І к л 
> Г 
> ♦ 
> V 
> ♦ 
> V
> Метиковании — кмітливий, досвідчений. 
> ч
> Знайди слова із протилежним значенням і запиши їх за
> зразком.
> 1
> добро
> смуток
> день — ніч
> темрява
> любов
> радість
> радість
> світло
> ? звуків, ? букв,
> ненависть
> зло
> ? складів
> реготати
> веселитися
> Пограйтесь 
> у гру «Хто 
> більше?»
> сміятися
> міркувати

> **Source:** unknown, Grade 3
>

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Який? Яка? Яке? (What kind?)` (~300 words)
- `## Прикметники (Common Adjectives)` (~300 words)
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

**Required:** який, яка, яке (what kind? — m/f/n), великий (big), маленький (small), новий (new), старий (old), гарний (nice, beautiful), чистий (clean), дорогий (expensive), дешевий (cheap)
**Recommended:** поганий (bad), брудний (dirty), світлий (light, bright), темний (dark), а (and/but — contrast), але (but)

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

- P1 (~40 words): Brief scene-setting for Dialogue 1 — Оленка shows her room to a friend. Mention this is based on Вашуленко Grade 3 "Моя кімната" task. Frame: describing your space is one of the first things you do when someone visits.

- Dialogue 1 (~100 words): Room description dialogue. Оленка and Марко. Марко asks «Яка твоя кімната?» → «Моя кімната велика і світла.» Then about specific objects: «А стіл?» → «Стіл новий. А ліжко — старе.» → «А вікно?» → «Вікно велике і чисте.» Each answer demonstrates adjective agreement with a different gender noun (кімната=f, стіл=m, ліжко=n). Include 2-3 comprehension glosses after the dialogue pointing out the gender pattern.

- P2 (~30 words): Transition to Dialogue 2 — new situation: window-shopping. Two friends look at things in a shop window, reacting with який/яка/яке exclamations.

- Dialogue 2 (~100 words): Shopping dialogue. Андрій and Софія. «Дивись, яка гарна сумка!» → «Так, але вона дорога.» → «А цей телефон?» → «Він великий і дешевий.» → «А це вікно? Яке велике!» → «Так, і чисте!» After dialogue: 2-3 glosses highlighting який/яка/яке matching the noun gender, and the contrast word «але».

- P3 (~60 words): Post-dialogue analysis paragraph. Point out the pattern across both dialogues: when describing кімната (f) → велика, світла; стіл (m) → новий; ліжко (n) → старе, велике. The adjective ending changes to match the noun's gender. Ask the learner: can you predict the pattern? Which endings go with which gender?

## Який? Яка? Яке? (What kind?) (~330 words total)

- P1 (~80 words): Introduce the question "What kind?" — який/яка/яке. Connect to the мій/моя/моє pattern from M08: same gender logic, different word. Three clear question-answer pairs: «Який стіл?» → «Великий стіл.» / «Яка книга?» → «Нова книга.» / «Яке вікно?» → «Чисте вікно.» Emphasize: the question word AND the answer both change gender.

- P2 (~80 words): Grammar box — adjective endings in nominative. Reference Пономарова Grade 3 p.98: "Прикметник має такий рід, як іменник." Masculine: -ий (великий, новий, чистий). Feminine: -а (велика, нова, чиста). Neuter: -е (велике, нове, чисте). Note: soft-stem adjectives like синій/синя/синє come in M10 Colors — for now, focus on the -ий/-а/-е pattern.

- Exercise 1 — Quiz (6 items): Який/яка/яке? Choose the correct question word. Items use M08 nouns: ___ кіт? (який), ___ лампа? (яка), ___ місто? (яке), ___ стілець? (який), ___ кімната? (яка), ___ ліжко? (яке).

- P3 (~80 words): Explain WHY the ending changes — the adjective "agrees" with its noun. Use a metaphor: adjective is like a mirror reflecting the noun's gender. Walk through 3 examples step by step: книга is feminine → яка? → нова (ending -а). Стіл is masculine → який? → новий (ending -ий). Вікно is neuter → яке? → нове (ending -е). Remind: gender was learned in M08, now it has a practical use.

- Exercise 2 — Fill-in (10 items): Add correct adjective ending. нов__ книга, велик__ стіл, чист__ вікно, гарн__ кімната, стар__ телефон, маленьк__ місто, дорог__ сумка, дешев__ стілець, брудн__ вікно, світл__ кімната.

- P4 (~90 words): Plural preview — mention that plural form exists (які?) but keep it simple: «Які стільці?» → «Нові стільці.» All genders use the same plural ending -і. One brief example set: новий стіл / нова книга / нове вікно → нові стільці / нові книги / нові вікна. Don't drill this — just awareness. Also note: який can mean "what a...!" in exclamations: «Яка гарна кімната!» = "What a beautiful room!"

## Прикметники (Common Adjectives) (~330 words total)

- P1 (~90 words): Introduce adjectives in opposite pairs — this is how Ukrainian textbooks teach them (Grade 2 "слова із протилежним значенням"). Present 6 pairs with all three gender forms for the first pair as demonstration: великий/велика/велике ↔ маленький/маленька/маленьке. Then list remaining pairs (masculine form only, learner infers the rest): новий ↔ старий, гарний ↔ поганий, чистий ↔ брудний, дорогий ↔ дешевий, світлий ↔ темний.

- Exercise 3 — Match-up (6 items): Match adjective opposites. великий ↔ маленький, новий ↔ старий, гарний ↔ поганий, чистий ↔ брудний, дорогий ↔ дешевий, світлий ↔ темний.

- P2 (~80 words): Building descriptions with M08 nouns. Model sentences combining possessives (M08) + adjectives (M09): «У мене є великий стіл.» «Моя кімната маленька, але гарна.» «Вікно велике і чисте.» «Стілець старий, а ліжко — нове.» Explain «а» vs «і»: «і» joins similar things (велике і чисте), «а» contrasts (стілець старий, а ліжко нове). Both translate as "and" in English but serve different functions.

- P3 (~80 words): Demonstrate how to describe a room using the full toolkit. Model paragraph: «Моя кімната невелика, але світла. У мене є новий стіл і старий стілець. Ліжко велике і зручне. Вікно чисте. Шафа маленька, а тумбочка — нова.» Then break down: count how many adjectives, identify each gender agreement. This prepares the learner for the production exercise.

- Exercise 4 — Fill-in (6 items): Describe the room — complete sentences using given noun + adjective. «Кімната _____ (великий).» → велика. «Стіл _____ (новий).» → новий. «Вікно _____ (чистий).» → чисте. «Лампа _____ (старий).» → стара. «Ліжко _____ (маленький).» → маленьке. «Стілець _____ (дорогий).» → дорогий.

- P4 (~80 words): Common mistakes and tips. Warn about two frequent errors: (1) forgetting to change the ending — *«велика стіл»* is wrong because стіл is masculine → великий стіл; (2) confusing «а» and «але» — both mean "but," but «а» is lighter contrast within a list, «але» is stronger opposition. Give one pair: «Стіл новий, а стілець старий» (mild contrast) vs «Кімната маленька, але гарна» (unexpected contrast).

## Підсумок — Summary (~210 words total)

- P1 (~80 words): Recap the three key patterns. Self-check questions from the plan: What ending does a masculine adjective have? (-ий). Feminine? (-а). Neuter? (-е). How do you ask "What kind?" — який (m), яка (f), яке (n). What's the difference between «а» and «і»? Quick-reference mini-table: який? → -ий / яка? → -а / яке? → -е.

- P2 (~70 words): Production challenge — describe YOUR room in 3-5 sentences using adjectives from this module. Model: «Моя кімната _____ і _____. У мене є _____ стіл. Вікно _____.» Encourage mixing adjective pairs: not just «великий» everywhere, but «великий стіл, маленька шафа, чисте вікно.» Remind that M10 will add colors to expand descriptions further.

- P3 (~60 words): Connection to what's next. In M10 (Colors), learners will meet soft-stem adjectives (синій/синя/синє) — a small twist on today's pattern. They'll also combine colors with today's adjectives: «великий червоний стіл», «маленька синя сумка.» For now, practice the -ий/-а/-е pattern until it feels automatic.

Grand total: ~1200 words (330 + 330 + 330 + 210 = 1200, with ~10% overshoot built into paragraph budgets summing to ~1320)
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
