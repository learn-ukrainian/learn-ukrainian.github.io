# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **5: Who Am I?** (A1, A1.1 [Sounds, Letters, and First Contact]).

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
module: a1-005
level: A1
sequence: 5
slug: who-am-i
version: '1.1'
title: Who Am I?
subtitle: Мене звати... — Your first real conversation
focus: vocabulary
pedagogy: PPP
phase: A1.1 [Sounds, Letters, and First Contact]
word_target: 1200
objectives:
- Introduce yourself with name, nationality, and profession
- Use the Це construction to identify things and people
- Ask and answer "What is your name?" formally and informally
- Understand the Ukrainian sentence without verb "to be" (Я — студент)
content_outline:
- section: Діалоги (Dialogues)
  words: 350
  points:
  - 'Dialogue 1 — At a hostel (informal, following Anna Ep3): — Привіт! Як тебе звати? — Мене звати Марко. А тебе? — Мене
    звати Олена. Звідки ти? — Я з Канади. А ти? — Я з України. — Дуже приємно!'
  - 'Dialogue 2 — At a conference (formal, following Anna Ep3-4): — Добрий день! Як вас звати? — Мене звати Петро. Дуже приємно!
    — Мені також! Ви з України? — Так, я з Києва.'
  - 'Dialogue 3 — Introducing someone else: Це мій друг Андрій. Він зі Львова. Він — інженер.'
- section: Мене звати... (My name is...)
  words: 250
  points:
  - 'Following Anna Ep3: Мене звати... literally ''me they-call.'' Ukrainian doesn''t use ''My name IS'' — no verb ''to be''
    needed. Asking: Як тебе звати? (informal) / Як вас звати? (formal). About others: Як його звати? (his) / Як її звати?
    (her).'
  - 'Pleased to meet you: Дуже приємно! or Приємно познайомитись! Said AFTER exchanging names.'
- section: Це... (This is...)
  words: 200
  points:
  - 'Це = ''this is / it is / these are.'' No verb ''to be'' needed. Це кава. Це Київ. Це мій друг. Questions: Що це? (What
    is this?) Хто це? (Who is this?) Question words go FIRST: Хто це? not *Це хто?'
- section: Я — студент (I am a student)
  words: 200
  points:
  - 'No verb ''to be'' in present tense. Subject — Noun: Я — студент. Він — лікар. Вона — вчителька. The dash (—) marks where
    ''is'' would go.'
  - 'Nationalities (nominative, no verb): українець / українка, американець / американка, канадієць / канадка. Professions:
    студент/студентка, вчитель/вчителька, лікар/лікарка, програміст/програмістка.'
- section: Звідки? (Where from?)
  words: 200
  points:
  - 'Following Anna Ep4: Звідки ти? / Звідки ви? Я з України. Я з Канади. Я зі Штатів. Я з Німеччини. Note: ''з/зі + country''
    uses genitive forms (України, Канади) but teach as MEMORIZED CHUNKS — genitive grammar is A2. Do NOT introduce ''Де ви
    живете?'' here — locative + verb conjugation are taught later (M16 verbs, M29 locative).'
- section: Підсумок — Summary
  words: 0
  points:
  - Self-check folded into dialogue practice above.
vocabulary_hints:
  required:
  - мене звати (my name is)
  - як тебе звати? (what's your name, informal)
  - як вас звати? (what's your name, formal)
  - це (this is / these are)
  - дуже приємно (pleased to meet you)
  - студент, студентка (student m/f)
  - вчитель, вчителька (teacher m/f)
  - лікар, лікарка (doctor m/f)
  - українець, українка (Ukrainian m/f)
  - Україна (Ukraine)
  recommended:
  - програміст, програмістка (programmer m/f)
  - журналіст, журналістка (journalist m/f)
  - інженер, інженерка (engineer m/f)
  - звідки (where from)
  - зараз (now, currently)
  - друг (friend, male)
  - його (his — doesn't change)
  - її (her — doesn't change)
  - Канада (Canada)
  - Німеччина (Germany)
activity_hints:
- type: fill-in
  focus: 'Complete self-introduction: Мене звати..., Я з..., Я —...'
  items: 6
- type: quiz
  focus: Formal or informal? Choose the right introduction.
  items: 6
- type: match-up
  focus: Match professions with male/female forms
  items: 8
- type: fill-in
  focus: Complete the dialogue with correct phrases
  items: 6
connects_to:
- a1-006 (My Family)
prerequisites:
- a1-004 (Stress and Melody)
grammar:
- Мене звати construction (impersonal)
- Це + noun identification
- Zero copula (Я — студент, no verb 'is')
- Nationality and profession vocabulary (nominative)
- Звідки? + country as memorized chunk (NOT genitive grammar)
register: розмовний
references:
- title: ULP Season 1, Episode 3 — How to Introduce Yourself
  url: https://www.ukrainianlessons.com/episode3/
  notes: Мене звати, nationality, Дуже приємно.
- title: ULP Season 1, Episode 4 — Where You Live and Where From
  url: https://www.ukrainianlessons.com/episode4/
  notes: Де ви живете? Звідки ви?
- title: ULP Season 1, Episode 8 — Jobs and Professions
  url: https://www.ukrainianlessons.com/episode8/
  notes: Profession vocabulary with gendered forms.
pronunciation_videos:
  playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Who Am I?
**Module:** who-am-i | **Phase:** A1.1 [Sounds, Letters, and First Contact]
**Textbook grades searched:** 1, 2

---

## Діалоги (Dialogues)

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
> 23
> Розкажи про різницю у вживанні імен у дитячому і доросло-
> му віці. Чому це прийнято? Напиши, як до тебе звертаються 
> зараз і як звертатимуться в майбутньому.
> Андрійко
> Ганнуся 
> Андрій
> Ганна
> Андрій
> Вікторович
> Ганна 
> Сергіївна
>  
> Редагуємо
> Я — дарина Тесленко Андріївна. Я — Іваненко Борисович 
> Микола. Хлопчик Василько, Дівчинка оля.
>  
> Текст. Тема тексту. Заголовок. Головний герой
> Маляку взагалі-то по-справжньому не так звати. У ди-
> тинстві дорослі часто питали Маляку, як її звати. Відповідала 
> во

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 36
> 36
> 	 Розглянь фото дітей. Здогадайся, як звати 
> хлопчика.  Хто з дівчаток — Оксана, а хто — 
> Аліна? 
> 	
> У яких предметах «заховалася» буква о?
> 	 Розглянь малюнки й дай відповідь на запи-
> тання.
> 	
> Що було в клоуна?
> 	
> Хто забрав кульки?
> 	
> Що сорока зробила з кульок?

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> РОЗРІЗНЯЮ СЛОВА, ЯКІ є ЗАГАЛЬНИМИ І ВЛАСНИМИ НАЗВАМИ
> визначаю
> Я — учителька
> Прочитай і розкажи 
> ; у класі.
> розподіляю
> Я — учитель
> В українській мові є слова — загальні назви, 
> які пишуться з малої літери, і є слова — власні 
> назви, які пишуться з великої літери.
> Додай свої 
> слова. у
> українець 
> українка
> Франція, Англія, Румунія, Італія, Угорщина, Іспанія, 
> Німеччина, Чехія.
> • Назвіть слова, які є власними назвами. Як вони пишуться?
> • А які слова є загальними назвами? Як вони пишуться?

> **Source:** unknown, Grade 1
> **Score:** 0.25
>
> 23
> ’
> Апостроф
> і |м’я
> Прочитай. Назви імена. Склади речення з одним іменем.
> 	
> ім’я	
> Дар’я	
> Дем’ян	
> В’ячеслав
> 	
> сім’я	
> Мар’яна	
> Лук’ян	
> Валер’ян
> 
> Відшукай слово до схеми.
> 	
> п’є	
> в’є	
> б’є	
> з’єднати	
> під’їхати
> 	 п’ють	 в’ють	 б’ють	
> роз’єднати	
> від’їхати
> 
> Текст. Театралізуємо
> Моє ім’я
> Я — Мар’яна. 
> Сьогодні на подвір’ї я грала в м’яч. 
> —  Мар’яше! — кличуть подруги. —  
> Кидай м’яч. 
> Потім мене гукнула бабуся:
> —  Мар’яночко! Іди обідати.
> Я пішла додому і зустріла сусідку. 
> —  Як справи, Мар’янко?

> **Source:** unknown, Grade 2
> **Score:** 0.25
>
> 17
> моноЛоГ І ДІаЛоГ
> Слово монолог складається з двох 
> частин: моно — один 
>  і лог — мов-
> лення. Коли ти розповідаєш комусь про 
> щось, описуєш предмет, розмірковуєш 
> наодинці — це монолог.  
> Діалог — це розмова двох (або кількох) осіб. Слово 
> діалог складається з двох частин: діа — два 
>  і лог — 
> мовлення. Коли ти спілкуєшся з другом/подругою, ви гово-
> рите по черзі, тобто обмі нюєтеся репліками.
> А я читаю 
> казку «Коти горошко».
> Я прочитала 
> казку «Рукавичка».
> репліка
> репліка
> Хто з казкови

## Мене звати... (My name is...)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 95
> —	 Доб-ро-го ран-ку! — мов-лю за 
> зви-ча-єм. 
> —	 Доб-ро-го ран-ку! — кож-но-му 
> зи-чу  я. 
> —	 Доб-ро-го  дня! — лю-дям ба-
> жа-ю.
> —	 Ве-чо-ра  доб-ро-го! — стріч-
> них  ві-та-ю.
> І  ус-мі-ха-ють-ся   в   від-по-відь  лю-
> ди  — доб-рі  сло-ва  ж  бо  для  кож-
> но-го лю-бі.
>                                                    Вадим Бі­рюков 
> 	 Як ми називаємо виділені слова?
> 	 Добери до кожної ситуації слова ввічливості.

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> НАВЧАЮСЯ СТВОРЮВАТИ ВИСЛОВЛЮВАННЯ НА ВІДОМУ ТЕМУ
> ІййіД[2і| Прочитайте текст про чемність 
> у спілкуванні між людьми.
> Чемна людина завжди вітається 
> і прощається, ввічливо відповідає на 
> привітання. З такою людиною при­
> ємно спілкуватися, бо вона ніколи 
> не образить і не принизить. Чемність 
> виявляється не тільки у словах, а й у 
> жестах, у виразі очей. Тому в чемної 
> людини завжди багато друзів.
> створюю 
> записую
> £ Яку людину
> •“
> називають
> чЄмною? г
> • Доведіть, що ви — чемні діти. Назвіть слова ввіч

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 25
> Слова — назви дій
> Що робить?
> Що роблять?
> Що чим роблять?
> 	 Який у тебе сьогодні настрій? Вибери.
> Слова — назви дій

> **Source:** unknown, Grade 2
> **Score:** 0.33
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

> **Source:** unknown, Grade 1
> **Score:** 0.25
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
> **Score:** 0.25
>
> 18| Назвіть людей різних професій, які працюють 
> у вашій школі. Згадайте їхні імена і по батькові. 
> Запишіть за зразком.
> бібліотекарка — 
> Софія Миколаївна
> 19| Уяви, що ти будуєш дім. Розкажи, хто буде жити у 
> твоєму будинку. Запиши за зразком слова — назви 
> людей.
> дідусь — Іваненко 
> Іван Іванович
> Хвилинка спілкування
> • Поясни, які зі слів є власними назвами, а які — загальними. 
> Як вони пишуться?
> прізвище 
> ? звуків, ? бук^ 
> ? складів
> 1
> І 
> І
> — Як правильно утворити по 
> батькові від імені Назарій:

## Це... (This is...)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 21
> Хто це?
> Слова — назви живих предметів
> 	 Який у тебе сьогодні настрій? Вибери.
>  [ –    –|–  ] 
>  [ =    –|–   ] 
>  [ –  |–  |– ] 
>  [ =  |–   – ] 
> Що?
> Хто?

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> Олег Попов
> ХТО ЦЕ?
> Запитайте мене, діти,
> хто рідніш мені на світі?
> Безперечно, та людина,
> яка любить свого сина.
> Сильна, мужня, що все знає
> і мене всього навчає.
> Вміє гарно майструвати —
> це мій любий рідний  ?  !
>  
> 	 Про кого цей вірш? З яким почуттям поет розповідає 
> про нього?
>  
> 	 Що розповідає автор про свого тата?
>  
> 	 Дізнайтеся про значення виділених слів. Розкажіть, як ви 
> це робитимете.
> 	
> Пригадай, якими пестливими словами називають тебе твої 
> рідні. А як лагідно ти звертаєшся до них?

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
> На уроці не сумуй, швидко слова розшифруй.
> СТОМІ
> ВЛОЯ
> їКви
> казко
> проДні
> васла
> Перегляньте відео про Київ.
> • Чи відомо вам, чому місто має таку назву?
> Прочитайте уривок з легенди.
> ТРИ БРАТИ — ЗАСНОВНИКИ КИЄВА
> Були три брати. Один на ймення Кий, другий — Щек, а 
> третій — Хорив, і сестра їх — Либідь. Кий сидів* на горі, де 
> нині узвіз Боричів. Щек сидів на горі, яка нині зветься 
> Щекавицею. А Хорив — на третій 

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~350 words)
- `## Мене звати... (My name is...)` (~250 words)
- `## Це... (This is...)` (~200 words)
- `## Я — студент (I am a student)` (~200 words)
- `## Звідки? (Where from?)` (~200 words)
- `## Підсумок — Summary` (~0 words)
- `## Підсумок — Summary` (~150 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 5-15% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: Mostly English with Ukrainian words bolded inline.
- UKRAINIAN CONTENT: Words and short phrases inline: "The letter **Н** looks like H but sounds like N."
- DIALOGUES & READING PRACTICE: Short Ukrainian sentences in blockquotes are encouraged.
- TABLES: Simple letter-sound or word-meaning tables.
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

**Required:** мене звати (my name is), як тебе звати? (what's your name, informal), як вас звати? (what's your name, formal), це (this is / these are), дуже приємно (pleased to meet you), студент, студентка (student m/f), вчитель, вчителька (teacher m/f), лікар, лікарка (doctor m/f), українець, українка (Ukrainian m/f), Україна (Ukraine)
**Recommended:** програміст, програмістка (programmer m/f), журналіст, журналістка (journalist m/f), інженер, інженерка (engineer m/f), звідки (where from), зараз (now, currently), друг (friend, male), його (his — doesn't change), її (her — doesn't change), Канада (Canada), Німеччина (Germany)

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
