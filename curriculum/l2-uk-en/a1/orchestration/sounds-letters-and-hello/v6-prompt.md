<correction_directive>
CRITICAL: Your previous attempt failed the following checks. Write the module FROM SCRATCH. All original constraints still apply.

- FIX: Missing section heading: 'Привіт! (Hello!)'
- FIX: Missing section heading: 'Читаємо (Reading Practice)'
- FIX: Missing section heading: 'Підсумок — Summary'
- FIX: Too short: 482 words (target: 1200, minimum: 1020)
- FIX: Missing 8/10 required vocab: вода (water), рука (hand), книга (book), школа (school), привіт (hi, informal)
</correction_directive>

# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **1: Sounds, Letters, and Hello** (A1, A1.1 [Sounds, Letters, and First Contact]).

**Target: 1200–1800 words** of prose (Ukrainian examples count toward word total, headings and exercise placeholders do not).

---

## 7 Hard Rules

1. **NO stress marks (´)** — do not add stress marks to any Ukrainian word. A deterministic tool adds them after you write.
2. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
3. **NO "In this lesson we will..."** — never use formulaic openers. Start with a dialogue, a question, or a situation.
4. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
5. **Exercise placeholders ONLY** — mark where exercises go using the format below, but do NOT write exercise content. A separate tool fills them.
6. **NO meta-commentary** — do NOT add "Content notes:", word count summaries, or self-audit sections at the end. Just write the module content and stop.
7. **Hit the word target** — you MUST write 1200–1800 words of actual prose. Count as you go. Short modules fail review. Expand explanations, add more examples, include more dialogues — never pad with filler.

## Exercise Placeholder Format

When you want an exercise, write a placeholder block. Be SPECIFIC about what the exercise should contain — include the actual questions, answers, and distractors. The more detail you provide, the better the exercise.

```
:::exercise-placeholder
type: quiz | fill-in | match-up | group-sort | true-false
tests: [what skill this exercise tests — be specific]
after: [what concept was just taught]
items: [number of items]
vocabulary: [comma-separated Ukrainian words to use as stems]
questions: [specific questions with answers, e.g. "Що ми чуємо? → звуки" or "В=? → [в] не [б]"]
groups: [for group-sort: group names and which items go where]
:::
```

**Good example:**
```
:::exercise-placeholder
type: group-sort
tests: classify letters as vowel or consonant
after: голосні vs приголосні explanation
items: 8
groups: Голосні: А, О, У, І; Приголосні: М, К, Б, Ш
:::
```

**Bad example (too vague):**
```
:::exercise-placeholder
type: quiz
tests: understanding
items: 5
:::
```

Place 4–6 exercise placeholders throughout the module, after key teaching points. Never cluster them — spread them evenly.

---

## Plan

module: a1-001
level: A1
sequence: 1
slug: sounds-letters-and-hello
version: '1.0'
title: Sounds, Letters, and Hello
subtitle: "33 літери, 38 звуків, Привіт!"
focus: phonetics
pedagogy: PPP
phase: A1.1 [Sounds, Letters, and First Contact]
word_target: 1200
objectives:
- Understand the difference between sounds (звуки) and letters (літери)
- Recognize the two families of sounds — vowels (голосні) and consonants (приголосні)
- Read your first Ukrainian words using Cyrillic letters
- Say hello and respond to a greeting
content_outline:
- section: "Звуки і літери (Sounds and Letters)"
  words: 250
  points:
  - "Golden rule from Большакова Grade 1 p.24 and Заболотний Grade 5 p.73:
    'Ми чуємо і вимовляємо звуки, а бачимо і пишемо літери.'
    33 letters (літери), 38 sounds (звуки). Letters are symbols on paper.
    Sounds are what we hear and pronounce."
  - "Two families of sounds:
    Голосні (vowels) — made with voice only, mouth open, no obstruction.
    Большакова teaches with a poem: 'Голосні почуєш в пісні.'
    6 vowel sounds: [а], [о], [у], [е], [и], [і].
    10 vowel letters: А, О, У, Е, И, І, Я, Ю, Є, Ї."
  - "Приголосні (consonants) — made with voice + noise or noise only.
    Lips, teeth, tongue create obstruction. 32 consonant sounds.
    Большакова: 'Приголосні деренчать, і тихенько шелестять.'"
- section: "Перші слова (First Words)"
  words: 300
  points:
  - "Some Cyrillic letters look like Latin but may sound different.
    Start with letters that look AND sound familiar: А, О, К, М, Т.
    Read immediately: мама, тато, кома, атом, мак, око.
    Important: Ukrainian Т is dental (tongue touches teeth, not gum ridge)
    and К/Т are unaspirated (no puff of air). Close enough for now."
  - "False friend letters — the biggest trap for English speakers:
    В sounds [в] (not 'b'), Н sounds [н] (not 'h'),
    Р sounds [р] rolled (not 'p'), С sounds [с] (not 'c/k'),
    У sounds [у] (not 'y'), Х sounds [х] (not 'x').
    Practice: вода (water), рука (hand), сон (dream), ніс (nose), хата (house)."
  - "New shapes — letters with no Latin equivalent:
    Б, Г, Ґ, Д, Ж, З, И, Й, Л, П, Ф, Ц, Ч, Ш, Щ.
    Through words: банк, дім, зима, книга, школа.
    Щ always makes TWO sounds [шч]. Ь has NO sound (softens the consonant before it)."
  - "Special: Ї always = [йі], never softens. Unique to Ukrainian.
    Я, Ю, Є can be two sounds OR soften a consonant.
    Full exploration in M02 — for now, just recognize them."
- section: "Привіт! (Hello!)"
  words: 250
  points:
  - "Following Anna Ohoiko ULP Episode 1 — your first conversation.
    Привіт! — Hi! (informal, use with friends, family, peers).
    Як справи? — How are you? Answers: Добре. Чудово. Нормально.
    А у тебе? — And you?"
  - "Рада тебе бачити! (female) / Радий тебе бачити! (male) — Glad to see you!
    Note: Ukrainian has gendered forms. Women say рада, men say радий.
    This is your first encounter with gender in Ukrainian — it will become
    a major topic starting M08."
  - "Reading practice with the greeting:
    Read each letter, blend into syllables: При-віт!
    This word uses letters from all groups:
    П (new), р (false friend!), и (new vowel), в (false friend!), і (vowel), т (familiar)."
- section: "Читаємо (Reading Practice)"
  words: 250
  points:
  - "Environmental reading — signs you see in Ukraine:
    Аптека (pharmacy), Банк (bank), Кафе (cafe), Метро (metro),
    Пошта (post office), Школа (school), Зупинка (bus stop).
    Sound out each letter, blend into syllables, read the whole word."
  - "Ukrainian city names:
    Київ, Львів, Одеса, Харків, Дніпро, Полтава."
  - "First sentences with Це (this is):
    Це мама. Це банк. Це Київ. Що це? Хто це?"
- section: "Підсумок — Summary"
  words: 150
  points:
  - "Self-check: How many letters? How many sounds? Why are they different?
    What are голосні? What are приголосні?
    What does Привіт mean? How do you respond to Як справи?"
vocabulary_hints:
  required:
  - мама (mother)
  - тато (father)
  - вода (water)
  - рука (hand)
  - книга (book)
  - школа (school)
  - привіт (hi, informal)
  - як справи (how are you)
  - добре (fine, good)
  - чудово (great, wonderful)
  recommended:
  - банк (bank)
  - аптека (pharmacy)
  - метро (metro)
  - пошта (post office)
  - зупинка (bus stop)
  - нормально (okay)
activity_hints:
- type: quiz
  focus: "Sound or letter? (звук чи літера?)"
  items: 6
- type: match-up
  focus: "Match false friend letters to their REAL sounds"
  items: 6
- type: fill-in
  focus: "Complete the greeting dialogue"
  items: 4
- type: group-sort
  focus: "Sort into голосні vs приголосні"
  items: 8
connects_to:
- a1-002 (Reading Ukrainian)
prerequisites: []
grammar:
- "Звуки vs літери — 33 letters, 38 sounds"
- "Голосні (6 sounds, 10 letters) vs приголосні (32 sounds)"
- "Cyrillic letter-sound mapping (familiar, false friends, new shapes)"
- "Привіт greeting as first spoken Ukrainian"
register: розмовний
references:
- title: "Большакова Grade 1 буквар, p.24"
  notes: "Голосні/приголосні taught through poems. 'Голосні почуєш в пісні.'"
- title: "Захарійчук Grade 1 буквар (NUS 2025), p.13"
  notes: "Sound notation: [•] for vowels, [–] for consonants."
- title: "Заболотний Grade 5, p.73"
  notes: "38 звуків: 6 голосних + 32 приголосні."
- title: "ULP Season 1, Episode 1 — Informal Greetings"
  url: https://www.ukrainianlessons.com/episode1/
  notes: "Привіт, Як справи?, response patterns."
pronunciation_videos:
  overview: https://www.youtube.com/watch?v=ksXIXj7CXwc
  playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV


---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

# Verified Knowledge Packet: Sounds, Letters, and Hello
**Module:** sounds-letters-and-hello | **Phase:** A1.1 [Sounds, Letters, and First Contact]
**Textbook grades searched:** 1, 2

---

## Звуки і літери (Sounds and Letters)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 24
> ЗВУКИ. ГОЛОСНІ І ПРИГОЛОСНІ
> Ти вимовляєш різні звуки: голосні і приголосні. 
> Голосні звуки утворюються за допомогою голосу.
> Голосні почуєш в пісні,
> І у темному у лісі, 
> І коли дивуєшся,
> І коли милуєшся.
> Легко вимовляються, 
> Весело співаються! 
> Прочитай. Назви букви, які позначають голосні звуки.
> ал – ам – ан 
> ла – ма – на 
> ул – ум – ун
> ол – ом – он 
> ло – мо – но 
> лу – му – ну
>  
> Приголосні звуки утворюються 
> за допомогою голосу і шуму.
> Приголосні деренчать
> І тихенько шелестять, 
> Голосно свистя

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> 9
> ГОЛОСНІ ТА ПРИГОЛОСНІ ЗВУКИ
> 25.	
> Прочитай без букви «ща».
> щ щ г о щ щ л о щ с щ н і щ щ з щ в у щ к и щ
> Під час вимовляння голосних звуків повітря вільно прохо-
> дить через рот, не натрапляючи на перешкоди. Голосні 
> звуки утворюються за допомогою голосу.
> 26.	
> 1.	 Прочитай лічилку і спиши, вставляючи пропущені букви.
> Х  д  л     кв  чк  
> к  л     к  л  чк  .
> В  д  л     д  т  ч  к
> б  л     кв  т  ч  к!   Квок!
> о и а о а
> о о і о а
> о и а і о о
> і я і о о
> 2.	 Де використовують лічилки? Розкажи лічил

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 13
> 	 Вимов голосні звуки в словах — назвах предме-
> тів.   
> 	 Вимов приголосні звуки в словах — назвах 
> предметів.
> 	 Який у тебе сьогодні настрій? Вибери.
> Мовні звуки: голосні та приголосні
> [•]
> [•]
>  [ – ]
>  [ – ]
>  [ – ]
>  [ – ]
> 	 Вимов перший звук у словах — назвах предме-
> тів. Який це звук? Приголосний звук позначає-
> мо так: [–].
> 	 Вимов перший звук у словах — назвах предметів. 
> Який це звук? Голосний звук позначаємо так: [•].

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> 34
> ГоЛоснІ І ПриГоЛоснІ ЗвУки. 
> ПоЗначЕння ГоЛосниХ ЗвУкІв БУквами 
> Звуки мови поділяються на голосні і приголосні.
> Розглянь схему. Розкажи, як утворюються звуки мови.
> голосні
> голос
> голос і шум
> шум
> приголосні
> утворюються
> Звуки
> В українській мові є шість голосних звуків. 
> Ти можеш позначити їх на письмі десятьма буквами.
> голосні 
> звуки
> 6
> [а], [о], [у], [е], [и], [і]
> 10
> букви, що позначають 
> голосні звуки
> а, о, у, е, и, і, я, ю, є, ї
>  
> Спиши слова. Поділи їх на склади. Скільки звуків позначають 
> б

> **Source:** unknown, Grade 1
> **Score:** 0.25
>
> 15
> Приголосні тверді та м’які
> 	 Вимов звуки, які ти чуєш на початку слів — 
> назв намальованих предметів.
> 	 Порівняй вимову перших звуків у словах — на-
> звах предметів. У яких словах перші звуки ви-
> мовляємо м’яко? М’які звуки позначай так: [ =].
> 	 Який у тебе сьогодні настрій? Вибери.
>  [      ] 
>  [      ] 
>  [      ] 
>  [      ] 
>  [      ] 
>  [      ] 
>  [ = ]  
>  [ = ]  
>  [ = ]  
>  [ – ] 
>  [ – ] 
>  [ – ] 
> 	 Хто неправильно поділив слово — назву нама-
> льованого предмета на склади?

> **Source:** unknown, Grade 2
> **Score:** 0.25
>
> 3
> 1.	 Назвиѳ зображені предмети. Чітко вимовляй усі звуки. З перших 
> звуків кожної наѳзви утвори слово.
> 2.	 Вираѳзно вимов утворене слово. Послідовно назвиѳ ланцюжок 
> звуків у ньому. 
> 2.	
> Виконай завдання на вибір.
> 	 Склади речення зі словом школа.
> 	 Продовж речення: У школі навчають … .
> Гра «Друзі».
> 1.	
> Букви
> друковані
> рукописні
> великі            малі
> Звуки
> вимовляємо
> чуємо
> утворюють слова
> Букви
> бачимо
> пишемо
> утворюють слова
> Звуки
> голосні
> приголосні
> тверді
> м’які
> ЗВУКИ І БУКВИ. СКЛАД. НАГОЛОС.

## Перші слова (First Words)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 19
>  
> ам 
> ум 
> ом 
> лу 
> ла 
> ло
>  
> ма 
> мо 
> му 
> ол 
> ал 
> ул
> мама – мамо – маму мул – мула
>  
> Текст. Передбачення
> УСМІШКА
> Був со-ня-чний день. Уля гуляла у дворі. Вона 
> побачила Устима. Він був сум-ний. Уля підійшла 
> до нього та усміхнулася:
> — Давай грати разом?
> Як ти думаєш, що відповів хлопчик? Що буде далі?
> — Ні, не хочу, — відповів Устим. — Бабуся 
> в лікарні. Не до ігор.
> — А як же її квіти на клумбі? — здивувалася 
> Уля. — Вони загинуть?
> Устим і Уля взяли лійки й полили квіти.  
> Уранці з лікарні повер

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
> 49
> 49
> Про кого йдеться в тексті? Вимов перший звук 
> цього слова. Яка буква його позначає? Що по-
> дарували Марині? Як «розумний» подарунок 
> допомагав дівчинці? Скільки в першому реченні 
> тексту є слів із буквою м?
> Марині на день наро-
> дження подарували ма-
> ленький ноутбук. Як зра-
> діла дівчинка! Вона обережно 
> розкрила електронну книжку 
> й погладила екран. Він засві-
> тився приємним світлом. На ньому літали яскраві 
> метелики, розкривали свої пелюстки дивовижні 
> квіти. Марина захоплено спостерігала

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> Прочитай швидко слова. У кожному ряду знайди слово, 
> яке повторюється двічі.
> матуся	
> мамуся	
> мамуня	
> матуся
> татусь	
> татко	
> татусь	
> татунь
> Сашко Дерманський
> ВІРШИК ДЛЯ МАМИ
> Мамо, добре, що ти є, —
> ніжне сонечко моє!
> Від твоєї теплоти
> так і хочеться рости...
> Найгарнішу, найдобрішу,
> я люблю тебе найбільше!
> І коли дорослим стану,
> теж любить не перестану!
> Бо ріднішої, ніж ти,
> в цілім світі не знайти!
> Добре, мамо, що ти є, —
> тепле сонечко моє!
>  
> 	 З якими почуттями поет розповідає про свою маму? Які

> **Source:** unknown, Grade 1
> **Score:** 0.25
>
> 5
> Назви, які букви великі, а які — малі; які букви друковані, 
> а які — писані.
> Т  п  А  у  Л  Ж  г  м  О  t  К  ю  я
> 
> Діти записали слова за абеткою. Перевір, чи правильно 
> вони це зробили. Назви одним словом кожну групу слів.
> 
> Текст. Тема тексту. «Зайві» речення
> У нас живе кіт. Ми назвали його Сніжком. 
> Він білий і пухнастий, наче сніг. Сніг — це опа-
> ди у вигляді сніжинок. Слово опади утворило-
> ся від слова падати. Сніжок любить гратися 
> клубком ниток. Я годую Сніжка молоком. 
> Визнач тему те

> **Source:** unknown, Grade 2
> **Score:** 0.25
>
> НАВЧАЮСЯ УТВОРЮВАТИ СПОЛУЧЕННЯ СЛІВ
> ІЗ ПРИКМЕТНИКАМИ
> 8| Прочитай уривок із вірша Лесі Лужецької, 
> розкриваючи дужки.
> А очі в мами — (добре, ніжна), 
> а голос — (чиста і дзвінка), 
> а руки — (теплий і надійний), 
> а погляд — (сонячні, ясні).
> • Назви слова — ознаки предмета. 
> На які питання вони відповідають?
> утворюю
> Добери такі 
> слова про тата.
> 9| Утвори від назв предметів слова — назви ознак предметів 
> за зразком.
> Тепло
> теплий
> тепла
> тепле
> теплі
> Радість
> ?
> •
> ?
> •
> Щастя
> ?
> • л
> ?
> *
> •
> Розум
> ?
> • ВІ
> ?
> •
> 10|

## Привіт! (Hello!)

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
> 8. Так, навіть, подарував (подарувала), я, квіти, 
> акто

... (truncated for context window)

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Звуки і літери (Sounds and Letters)` (~250 words)
- `## Перші слова (First Words)` (~300 words)
- `## Привіт! (Hello!)` (~250 words)
- `## Читаємо (Reading Practice)` (~250 words)
- `## Підсумок — Summary` (~150 words)
- `## Summary` (~150 words)

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
- **Natural Ukrainian**: Write how a Ukrainian teacher would explain this to a student. Not robotic, not textbook-dry, not overly casual.

### Writing Quality
- Every paragraph: ONE clear point, logical flow to the next
- Vary sentence length (short for emphasis, medium for explanation, long for examples)
- Use callout boxes (:::tip, :::caution, :::note) sparingly — max 3 per module
- Dialogues: natural, not stilted. Real situations, real responses.
- **Tone:** Authoritative but warm. Like a skilled Ukrainian teacher — confident, clear, culturally grounded. Avoid generic LLM cheerfulness ("Good news!", "Don't panic!", "Fun fact!"). Let the content be interesting on its own.
- **Never make claims about specific Ukrainian words** without being 100% sure. If you're not certain about a letter, sound, or form — describe it generally rather than risk an error.

GRAMMAR CONSTRAINTS (A1.1 — Phonetics, M01-M03):
NO CONJUGATED VERBS. NO IMPERATIVES. This is the phonetics phase.

ALLOWED structures (Ukrainian examples only):
- Це + noun: «Це кіт», «Це мама»
- Noun + тут/там: «Мама тут», «Кіт там»
- Question words: «Хто це?», «Що це?», «Де мама?»
- Так/Ні: «Так, це кіт», «Ні, це не кіт»
- Fixed phrases (memorized, no grammar): дякую, будь ласка, привіт

BANNED: ALL verbs, past/future tense, cases, compound sentences

STRESS MARKS: Do NOT add stress marks (´). Write plain Ukrainian.
The pipeline adds stress marks deterministically after you write.

METALANGUAGE: English prose, Ukrainian examples. Bilingual headings.

### Vocabulary

**Required:** мама (mother), тато (father), вода (water), рука (hand), книга (book), школа (school), привіт (hi, informal), як справи (how are you), добре (fine, good), чудово (great, wonderful)
**Recommended:** банк (bank), аптека (pharmacy), метро (metro), пошта (post office), зупинка (bus stop), нормально (okay)

### Pronunciation Videos

Overview: https://www.youtube.com/watch?v=ksXIXj7CXwc
Playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV

---

## Output Format

Write in Markdown. Use:
- `## Section Title` for main sections
- `### Subsection` for subsections within a section
- `**bold**` for Ukrainian words being taught
- Tables for paradigms (conjugation, declension)
- `:::tip` / `:::caution` / `:::note` for callout boxes
- `:::exercise-placeholder` for exercise locations

Do NOT write YAML, JSON, or MDX component syntax. Plain Markdown only.

Begin writing now. Start with the first section heading.
