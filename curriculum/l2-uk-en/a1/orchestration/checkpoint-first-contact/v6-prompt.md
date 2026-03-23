<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Missing 1/1 required vocab: All vocabulary from M01-M06 is recycled — no new required words
</correction_directive>

# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **7: Checkpoint: First Contact** (A1, A1.1 [Sounds, Letters, and First Contact]).

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
module: a1-007
level: A1
sequence: 7
slug: checkpoint-first-contact
version: '1.1'
title: 'Checkpoint: First Contact'
subtitle: Can you read, greet, and introduce yourself?
focus: review
pedagogy: PPP
phase: A1.1 [Sounds, Letters, and First Contact]
word_target: 1200
objectives:
- Demonstrate ability to read Ukrainian Cyrillic fluently
- Hold a complete first conversation (greet → introduce → family)
- Self-assess knowledge of sounds, letters, greetings, introductions
- Combine all A1.1 skills in connected speech
content_outline:
- section: Що ми знаємо? (What Do We Know?)
  words: 200
  points:
  - 'Self-check covering M01-M06: Can you read any Ukrainian word? (M01-M02) Do you know what Ь and apostrophe do? (M03) Can
    you place stress correctly? (M04) Can you introduce yourself? (M05) Can you talk about your family? (M06)'
- section: Читання (Reading Practice)
  words: 250
  points:
  - 'A short Ukrainian text (8-10 sentences) using ONLY vocabulary from M01-M06. No new words. The learner reads aloud. Content:
    A person introduces themselves, describes family, mentions professions, says where from.'
  - Following Anna Ep10 'Я і моя сім'я' review pattern.
- section: Граматика (Grammar Summary)
  words: 200
  points:
  - 'Key patterns from A1.1: 1. Це + noun (identification) 2. Subject — Noun (no ''is''): Я — студент 3. У мене є + noun (possession)
    4. Як тебе/вас звати? (asking names) 5. Мій/моя/моє + noun (possession with gender) 6. Звідки ти? — Я з... (origin as
    chunk)'
- section: Діалог (Capstone Dialogue)
  words: 400
  points:
  - 'The Full Introduction — comprehensive dialogue combining EVERYTHING from A1.1. Setting: meeting someone new. Full cycle:
    greeting → name → origin → profession → family → showing photos → goodbye. If learner can follow and produce this dialogue,
    A1.1 is complete.'
  - 'Connected monologue: learner''s own self-introduction. Привіт! Мене звати [name]. Я [nationality]. Я — [profession].
    Моя мама — [profession]. Мій тато — [profession]. У мене є [family]. This is the A1.1 graduation speech.'
- section: Підсумок — Summary
  words: 150
  points:
  - 'Final self-check questions: How many letters/sounds in Ukrainian? Say hello formally and informally. Introduce yourself
    in 5 sentences. Name your family members with possessives.'
vocabulary_hints:
  required:
  - All vocabulary from M01-M06 is recycled — no new required words
  recommended:
  - ім'я (first name)
  - прізвище (surname)
activity_hints:
- type: quiz
  focus: 'Comprehensive review: sounds, letters, greetings, family'
  items: 12
- type: fill-in
  focus: Complete the full self-introduction monologue
  items: 8
- type: match-up
  focus: Match questions with answers (Як звати? → Мене звати...)
  items: 8
connects_to:
- a1-008 (Things Have Gender)
prerequisites:
- a1-006 (My Family)
grammar:
- 'Review: Це + noun, Subject — Noun, У мене є, possessives'
- No new grammar — consolidation only
register: розмовний
references:
- title: ULP Season 1, Episode 10 — Review 1-9
  url: https://www.ukrainianlessons.com/episode10/
  notes: Anna's connected self-introduction review pattern.
pronunciation_videos:
  playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Checkpoint: First Contact
**Module:** checkpoint-first-contact | **Phase:** A1.1 [Sounds, Letters, and First Contact]
**Textbook grades searched:** 1, 2

---

## Що ми знаємо? (What Do We Know?)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 73
> 	 — Але ми все одно будемо дружи-
> ти? Адже ми обидва їжаки.
> 	 — Авжеж. Будемо (за Юрієм  Яр-
> мишем).
> 	 Прочитай заголовок казки. Що він тобі підка-
> зав? Хто з ким познайомився? 
> 	 Що любив слухати Їжак, який жив на гірці? 
> Що любив слухати Морський Їжак? Чому 
> вони любили різні звуки? 
> Повторюємо разом
> Абетка. Звуки та букви
> 	 Звуки, які любили їжаки, є мовні чи немовні?
> 	 Як називаємо підкреслені слова? 
> протилежні за значенням
> подібні за значенням
> 	 Перепиши перше речення. Підкресли букви,

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> 101
> Зразок. Барвінок, клен, ніч. 
> 2.	 Виконайте завдання на вибір.
> 	 Напишіть два слова, що відповідають на питання хто? і два 
> слова, що відповідають на питання що?
> 	 Складіть і запишіть речення з двома іменниками, поєднайте 
> їх службовими словами.
> 361. 1.	 Відгадай загадку.
> На зріст маленька 	 І у лісі в холодку
> пташка сіренька. 	
> все кує: «Ку-ку! Ку-ку!»
> 2.	 Виконай завдання на вибір.
> 	 Випиши прикметники до слова-відгадки.
> 	 Добери і запиши дієслова до слова-відгадки.
> 362. 1.	 Прочитай текст

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 50
> 	
> Що тобі відомо про героїнь казки «Дві білки»? 
> 	
> Розглянь малюнки. Дай відповідь на питан-
> ня: що робить?
> 	
> Визнач, якому слову — назві намальованого 
> предмета відповідає кожна схема.
> [ =•|–•|–• ] 
> [ –•|=•= ] 
> [ =•–|– •–] 
> 	 Назви слова, які відповідають схемам.
> [ –•| – •| =•]
> [ – –•| = •]
> [ –    –•| –•| = •]
> Що робить?
> Pidruchnyk.com.ua

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> 50
> 179. 1.	 Гра «Відшукай слово». «Перестрибуючи» через одну 
> літеру, прочитай слово.
> 2.	 Знайди в тлумачному словнику значення слова диван.
> 180. 1.	 Прочитай текст. Що нового ти дізнався (дізналася)?
> Ми розмовляємо українською мовою. А мова скла-
> дається зі слів. Слова можуть передати думки й почуття. 
> Словом можна назвати предмет, ознаку, дію предмета. Кожне 
> слово має своє значення. Значення 
> слова — це той зміст, який вклали в 
> нього люди. 
> Що краще ми знаємо і розу-
> міємо значення слова, то

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> ЦІКАВИНКИ ЗВІДУСІЛЬ
> Навчися швидко читати слова.
> світлофор 
> пофарбований 
> використовували
> залізничники 
> звичайний 
> відрізнялися
> • Прочитай заголовок твору. Про що, на твою думку, ітиметься в 
> тексті?
> • Попрацюйте разом. Заповніть таблицю (на аркуші).
> Прочитай.
> Світлофор
> Ми вже 
> знаємо
> Хочемо 
> дізнатися
> Де можна знайти 
> інформацію
> З ІСТОРІЇ СВІТЛОФОРА
> Прародичами* світлофорів були звичайні прапорці. їх 
> використовували залізничники, коли керували рухом поїздів. 
> Таких прапорців було... Ану, здога

> **Source:** unknown, Grade 1
> **Score:** 0.25
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

## Читання (Reading Practice)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 6
> Я  і  моя  родина
> Поділюся з вами я:
> В мене дружна є сім’я.
> Люба мама і татусь,
> Бабця Віра і дідусь, 
> Мурка, Барсик, Оля, я  —
> От і вся моя сім’я.
>                     Марія Братко
> 	 Намалюй свою родину на аркуші з альбому.
> 	 Повтори вірш за вчителем / учителькою.

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> Утвори і прочитай слова. Назви одним словом.
> маам
> отат
> дусьід
> басябу
> барт
> састер
> • Поміркуй, якими іншими словами ми називаємо сім’ю. 
> Склади тематичну павутинку (на аркуші паперу).
> Послухай пісню Наталії Май «Родина».
> *—• • Що ти відчував (відчувала), коли звучала пісня?
> • За що дитина дякує батькам?
> ~ Прочитай вірш.
> ДИВО-ТАТУСЬ
> Леся Вознюк
> Як весняне сонечко, 
> усміхалась донечка. 
> В оченятах сяяли 
> щастя промінці. 
> Тішилася донечка, 
> що її долонечка, 
> крихітна долонечка 
> в татовій руці. 
> Щебет

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 70
> Мої навчальні досягнення. Я вмію, можу
> * * *
> Прибрав ліжко САМ. 
> Зробив зарядку САМ. На 
> кухні  САМ поставив на 
> стіл чашку. Після снідан-
> ку САМ помив посуд.
> * * *
> А ... притулився до 
> мами й подумав: «Не-
> має нічого кращого, ніж 
> обійми моєї матусі. Ось 
> воно, щастя!»  
> * * *
> — Якщо ліс знову ста-
> не чистим, то й Лісовуня 
> буде гарною! — сказав 
> … .
> 	
> Пригадай історії, які ти прочитав / прочита-
> ла. Визнач, якому малюнку відповідає кож-
> ний уривок із тексту.
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

> **Source:** unknown, Grade 1
> **Score:** 0.25
>
> 3
> Дорогий друже!
> Ти продовжуєш подорож чудовим сві-
> том рідної мови. Адже ти любиш читати, 
> спілкуватися, фантазувати. 
> Ця книга допоможе тобі навчитися 
> читати, висловлювати думки й почуття, 
> спілкуватися.
> Умовні позначення:
> 	
> 	 — читаю
> 	
> 	 — обговорюю малюнок
> 	
> 	 — досліджую мовлення
> 	
> 	 — мислю критично

> **Source:** unknown, Grade 2
> **Score:** 0.25
>
> — I Мусю любимо й поважаємо. І вона нас теж. Зустрічає 
> всіх біля порога, грається з нами, колискову ввечері 
> муркоче...
> —Ура!—зраділа Ліля. — Виходить, що нас... Я, ти, мама, 
> тато, дідусь, бабуся і кішка Муся. Сім! Справжня СІМ-Я!
> -., • Де відбувалися описані події? Якого віку були діти?
> • У яку гру грали діти? Як вони розподілили між собою ролі?
> • Чому Ліля сумувала? Заповни таблицю (на аркуші паперу). 
> Познач смайликами емоції Лілі в різних частинах тексту.
> Частина тексту
> Емоції Лілі
> Зачин
> О

## Граматика (Grammar Summary)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 4
> Я ВИВЧАЮ УКРАЇНСЬКУ МОВУ
> Ми живемо в Україні. Наша мова — українська. 
> Ми будемо вчитися говорити, читати й писати українською. 
> Я читаю 
> українською.
> Я пишу 
> українською.
> Я слухаю 
> українську.
> Я говорю 
> українською.
> Я вітаюсь і знайомлюсь. 
> 1
> Доброго ранку!
> Мене звати Ганна.
> Привіт! Я Тарас. 
> Будемо вчитися разом.
> Будемо дружити!

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> ■мИ|28| Змініть подані слова за зразком і запишіть.
> навчати — навчання_ >
> Розкажи про свої 
> успіхи в навчанні.
> читати 
> міркувати 
> додавати 
> малювати 
> бажати 
> уміти
> • Поясніть, що називають записані слова. На які питання вони 
> відповідають? Усно складіть речення з однією парою слів 
> (на вибір).
> 29 Заміни сполучення слів за зразком і запиши.
> Книжка з бібліотеки — ? 
> Шафа для книжок — ?
> Вистава в театрі — ?
> Гра на комп'ютері — ?
> розм°ва по телефону — телефонна розмова
> • Запиши утворені сполучення с

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
> 12
> сЛова — назви ПреДметІв
> Слова — назви предметів — це іменники.
> Слово іменник утворене від слова ім’я. Кожний 
> предмет чи явище має своє ім’я, тобто свою назву.  
> Назви зображені предмети спочатку окремо, потім одним 
> словом. 

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Що ми знаємо? (What Do We Know?)` (~200 words)
- `## Читання (Reading Practice)` (~250 words)
- `## Граматика (Grammar Summary)` (~200 words)
- `## Діалог (Capstone Dialogue)` (~400 words)
- `## Підсумок — Summary` (~150 words)
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

GRAMMAR CONSTRAINTS (A1.1 — Communication, M04-M14):
Keep grammar simple — first exposure to Ukrainian sentences.

ALLOWED:
- Це + noun: «Це кіт», «Це мама»
- Fixed verbal phrases: «Мене звати», «У мене є», «Як справи?»
- Simple present tense (я читаю, я бачу) — from M08+
- Question words: «Хто це?», «Що це?», «Де?», «Як?»
- Так/Ні answers
- Adj + noun: «великий дім», «нова книга» — from M09+
- Possessive pronouns: мій/моя/моє — from M06+

BANNED: Past/future tense, conditionals, participles, passive, gerunds,
compound sentences (no і/а/але joining clauses)

METALANGUAGE: English first, Ukrainian in parentheses. Bilingual headings.

### Vocabulary

**Required:** All vocabulary from M01-M06 is recycled — no new required words
**Recommended:** ім'я (first name), прізвище (surname)

### Pronunciation Videos

Playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV

---

### Style Reference (match this tone and structure)

Look at the text on this page. What you are seeing are letters. Now, say a word out loud. What you just produced is a sound. This distinction is the absolute foundation of the Ukrainian language. There is a golden rule taught to every Ukrainian student in the first grade: **Ми чуємо і вимовляємо звуки, а бачимо і пишемо літери**. We hear and pronounce sounds, but we see and write letters.

These friendly letters are **А**, **О**, **К**, **М**, and **Т**. Because they are so familiar, you can start reading real Ukrainian words immediately. Look at the word **мама**. It means mother, and you already know how to read it. Now look at **тато**. It means father.

*Note: English prose dominates. Ukrainian words appear bolded inline. Short Ukrainian sentences illustrate one concept at a time. No conjugated verbs. Tables and bulleted lists for vocabulary.*

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
