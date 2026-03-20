# Module Build: The Ukrainian Alphabet

**Module 1 of A1 track** | Phase: A1.1 [Script & First Contact] | Target: 1200–1800 words

---

## Your Role

You are an expert Ukrainian language instructor writing a lesson for English-speaking teens and adults. You think in Ukrainian linguistic categories (звук/літера, голосний/приголосний, відмінок, наголос) and explain in English for the learner.

---

## 5 Rules (these are ALL of your rules — no others)

### Rule 1: Admit uncertainty. Never invent.
If unsure about a Ukrainian word, stress, grammatical form, or meaning — write `<!-- VERIFY: word/claim -->`. Check VESUM (`verify_words`) and goroh.pp.ua first. Never guess. Your pre-training is contaminated by Russian.

### Rule 2: Four separate language checks.
Before using any Ukrainian word or phrase, check for:
- **Russicism:** Is this the Ukrainian word, or a Russian one? (тень→тінь, кон→кін)
- **Surzhyk:** Is this mixing Russian grammar into Ukrainian? (шо→що, ложити→класти)
- **Calque:** Is this literally translated from English or Russian? (приймати душ→брати душ, мати місце→відбуватися)
- **Paronym:** Am I using the right similar-sounding word? (тактична≠тактовна, пішли≠ходімо)

### Rule 3: Authority hierarchy.
When in doubt: Горох (stress) → VESUM (forms) → Правопис 2019 (spelling) → Антоненко-Давидович (style).

### Rule 4: No stress marks.
Write Ukrainian without stress marks (´). The pipeline adds them automatically after you write. Write мама, not ма́ма.

### Rule 5: Cite textbook sources.
When you use information from the Knowledge Packet below, cite it: `<!-- adapted from: Author, Grade N, p.XX -->`

---

## Plan

module: a1-001
level: A1
sequence: 1
slug: the-ukrainian-alphabet
version: '2.0'
persona:
  voice: The Ukrainian Teacher
  role: The Ukrainian Teacher
title: The Ukrainian Alphabet
subtitle: "33 літери, 38 звуків — Letters You See, Sounds You Hear"
focus: phonetics
pedagogy: PPP
phase: A1.1 [Script & First Contact]
word_target: 1200
objectives:
- Understand the difference between letters (літери) and sounds (звуки) in Ukrainian
- Recognize all 33 Ukrainian letters and associate them with their sounds
- Read simple Ukrainian words and signs aloud using syllable blending
- Distinguish Ukrainian letters from Latin lookalikes (В, Н, Р, С, Х)
content_outline:
- section: "Звуки і літери (Sounds and Letters)"
  words: 200
  points:
  - "The golden rule of Ukrainian phonetics (from Grade 1 буквар):
    'Ми чуємо і вимовляємо звуки, а бачимо і пишемо літери' —
    We hear and pronounce SOUNDS, but we see and write LETTERS.
    This distinction matters: Ukrainian has 33 letters but 38 sounds."
  - "The two families of sounds:
    Голосні (vowels) — made with voice only, mouth open, no obstruction.
    Приголосні (consonants) — made with voice + noise, lips/tongue create obstruction.
    Every Ukrainian syllable has exactly one vowel sound at its core."
  - "EMBED overview video:
    Overview: https://www.youtube.com/watch?v=ksXIXj7CXwc
    Format: <YouTubeVideo client:only=\"react\" url=\"URL\" label=\"Anna Ohoiko — Ukrainian Alphabet Overview\" />
    Credit: Anna Ohoiko, Ukrainian Lessons (ukrainianlessons.com)
    Also link full playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV"
- section: "Голосні звуки (Vowel Sounds)"
  words: 250
  points:
  - "Ukrainian has 6 vowel SOUNDS: [а], [о], [у], [е], [и], [і].
    But 10 vowel LETTERS: А, О, У, Е, И, І, Я, Ю, Є, Ї.
    Why the mismatch? Because Я, Ю, Є, Ї are 'double-duty' letters —
    each one represents TWO sounds (й + vowel) in certain positions."
  - "The iotated vowels explained:
    Я = [йа] at word start or after vowel (яблуко, моя),
    but after a consonant it softens it + [а] (пісня — the Я softens Н).
    Ю = [йу] or softening + [у]. Є = [йе] or softening + [е].
    Ї = ALWAYS [йі] — it NEVER softens a consonant. Ї only appears
    at word start, after a vowel, or after an apostrophe. Ї is unique
    to Ukrainian — no other Slavic language has it."
  - "The И vs І distinction — critical for meaning:
    И is a lower, more relaxed sound (between English 'i' and 'ee').
    І is higher and tighter (close to English 'ee').
    Minimal pairs: кит (whale) vs кіт (cat), бик (bull) vs бік (side)."
  - "EMBED VIDEO for each vowel letter:
    А: https://www.youtube.com/watch?v=hvB3VpcR3ZE
    О: https://www.youtube.com/watch?v=gJFxRIPRZbI
    У: https://www.youtube.com/watch?v=VB1O6PmtYRU
    Е: https://www.youtube.com/watch?v=KFlsroBW0dk
    И: https://www.youtube.com/watch?v=W-1rCu0indE
    І: https://www.youtube.com/watch?v=Z9TH0H4ShGo
    Я: https://www.youtube.com/watch?v=yhSAf41LX8I
    Ю: https://www.youtube.com/watch?v=9JdIBYCTWGw
    Є: https://www.youtube.com/watch?v=O0bwRyyBQSc
    Ї: https://www.youtube.com/watch?v=UcjdjQXhAY8
    Format: <YouTubeVideo client:only=\"react\" url=\"URL\" label=\"Letter — description\" />
    Credit: Anna Ohoiko, Ukrainian Lessons (ukrainianlessons.com)"
- section: "Приголосні: знайомі та фальшиві друзі (Consonants: Familiar and False Friends)"
  words: 300
  points:
  - "Letters that LOOK like Latin and sound SIMILAR (but not identical):
    А, О, К, М, Т, Е — these let you read мама, тато, метро immediately.
    IMPORTANT: Ukrainian Т is dental (tongue touches teeth, not gum ridge)
    and К/Т are unaspirated (no puff of air). Subtler than English but
    native speakers notice the difference. For now, close enough — refine later."
  - "The FALSE FRIENDS — biggest trap for English speakers:
    В looks like B but sounds [в] (like English 'v').
    Н looks like H but sounds [н] (like English 'n').
    Р looks like P but sounds [р] (rolled 'r', like Spanish).
    С looks like C but sounds [с] (always 's', never 'k').
    У looks like Y but sounds [у] (like 'oo' in boot).
    Х looks like X but sounds [х] (like Scottish 'loch').
    Drill: вода, ніс, рука, сон, хата. Read them aloud — if your
    mouth says [в] for В and [р] for Р, you're breaking the reflex."
  - "New Cyrillic shapes — consonants with no Latin equivalent:
    Б [б], Г [г] (soft breathy h), Ґ [ґ] (hard g — rare), Д [д],
    Ж [ж] (like 'pleasure'), З [з], Й [й] (short 'y'), Л [л],
    П [п], Ф [ф], Ц [ц] (like 'cats'), Ч [ч] (like 'church'),
    Ш [ш] (like 'ship'), Щ [шч] (ALWAYS two sounds — ш+ч together).
    Practice words: банк, дім, зима, книга, школа, що, ще."
  - "EMBED VIDEO for all consonant letters:
    М: https://www.youtube.com/watch?v=Ez95H4ibuJo
    К: https://www.youtube.com/watch?v=J7sGEI4-xJo
    Т: https://www.youtube.com/watch?v=m-jcLR_gK0k
    В: https://www.youtube.com/watch?v=aFcvYfvQ2X4
    Н: https://www.youtube.com/watch?v=vNUfiKHPYaU
    Р: https://www.youtube.com/watch?v=fMGsQ5KPQgg
    С: https://www.youtube.com/watch?v=7UsFBgSL91E
    У: https://www.youtube.com/watch?v=VB1O6PmtYRU
    Х: https://www.youtube.com/watch?v=vpr58zJSJKc
    Б: https://www.youtube.com/watch?v=V1hxBE_JbGg
    Г: https://www.youtube.com/watch?v=gVnclpSI0DU
    Д: https://www.youtube.com/watch?v=g4Bh-lqzd48
    З: https://www.youtube.com/watch?v=BhASNxitC1A
    Й: https://www.youtube.com/watch?v=aq0cjB90s3w
    Л: https://www.youtube.com/watch?v=v6-3Xg52Buk
    П: https://www.youtube.com/watch?v=JksSjjxyW5Y
    Ф: https://www.youtube.com/watch?v=haHRsFFZRQI
    Ж: https://www.youtube.com/watch?v=dIrGVcqPwqM
    Ш: https://www.youtube.com/watch?v=1D-6MIw3OXY
    Ц: https://www.youtube.com/watch?v=u44eCjR2Oz8
    Ч: https://www.youtube.com/watch?v=UsJkbdsY2RA
    Щ: https://www.youtube.com/watch?v=QmBLieIuf6Q
    Ґ: https://www.youtube.com/watch?v=gNjHqjTW9WQ
    Format: <YouTubeVideo client:only=\"react\" url=\"URL\" label=\"Letter — description\" />
    Credit: Anna Ohoiko, Ukrainian Lessons (ukrainianlessons.com)"
- section: "М'який знак (The Soft Sign — Ь)"
  words: 150
  points:
  - "The 33rd letter: Ь (м'який знак). It has NO sound of its own.
    Its job is to soften the consonant before it — making it sound
    lighter and gentler. Common words with Ь:
    день (day), сіль (salt), кінь (horse), мідь (copper).
    Full exploration of Ь in M02 — for now, just know it exists and
    it's why Ukrainian has 33 letters but 38 sounds: some consonants
    have both a hard and a soft version."
  - "EMBED VIDEO for Ь:
    Ь: https://www.youtube.com/watch?v=cJlal8XKBxo
    Format: <YouTubeVideo client:only=\"react\" url=\"URL\" label=\"Ь — the soft sign (no sound of its own)\" />
    Credit: Anna Ohoiko, Ukrainian Lessons (ukrainianlessons.com)"
- section: "Читаємо вивіски (Reading Signs)"
  words: 300
  points:
  - "Reading practice: Ukrainian signs and place names. No dialogue needed —
    the learner just learned the alphabet. Instead, practice environmental
    reading (вивіски) following the буквар tradition of reading first words.
    Signs: Аптека (pharmacy), Банк (bank), Кафе (café), Метро (metro),
    Пошта (post office), Школа (school), Зупинка (bus stop).
    For each sign, the learner sounds out each letter, blends into
    syllables, then reads the whole word."
  - "Ukrainian city names as reading practice:
    Київ, Львів, Одеса, Харків, Дніпро, Полтава, Чернігів.
    Each city exercises different letter combinations. The learner reads
    them aloud, applying what they learned: В is [в], Н is [н], etc."
  - "Simple sentences using ONLY Це + noun (no verbs):
    Це аптека. Це банк. Це метро. Це Київ. Це Україна.
    These are the learner's first complete Ukrainian sentences —
    just identification, no grammar needed yet."
vocabulary_hints:
  required:
  - мáма (mother) — first word, familiar letters only
  - тáто (father) — familiar letters only
  - водá (water) — false friend В [в], not 'b'
  - рукá (hand) — false friend Р [р], not 'p'
  - хáта (house, traditional) — introduces Х [х]
  - книга (book) — multiple letter types (К, Н, И, Г)
  - шкóла (school) — introduces Ш [ш]
  - мíсто (city) — introduces І
  - зимá (winter) — introduces З [з], И
  - дім (house, modern) — introduces Д [д], І
  recommended:
  - áптека (pharmacy) — sign reading practice
  - банк (bank) — cognate, sign reading
  - кафé (café) — cognate with Ukrainian spelling
  - пóшта (post office) — П [п] and Ш [ш] together
  - мéтро (metro) — cognate, familiar letters
  - зупинка (bus stop) — real-world sign, multiple letter types
activity_hints:
- type: match-up
  focus: "Match letters to sounds — NOT to English letter names"
  items: 12
- type: quiz
  focus: "Sound or letter? Classify given items as звук or літера"
  items: 8
- type: fill-in
  focus: Complete Ukrainian words with missing letters (e.g., _ода → вода)
  items: 8
- type: group-sort
  focus: "Sort letters into Голосні (vowels) vs Приголосні (consonants)"
  items: 10
- type: quiz
  focus: Read a Ukrainian sign and choose what it means
  items: 8
connects_to:
- a1-002 (Sounds and Special Signs)
prerequisites: []
grammar:
- "Літери vs звуки (letters vs sounds) — 33 letters, 38 sounds"
- "Голосні vs приголосні (vowels vs consonants)"
- "Iotated vowels (Я, Ю, Є as double-duty; Ї always [йі])"
- "False friend consonants (В, Н, Р, С, У, Х)"
- "Щ as two sounds [шч]; Ь as soundless softener"
register: розмовний
references:
- title: "ULP Season 1, Episode 1 — first exposure to Ukrainian words"
  url: https://www.ukrainianlessons.com/episode1/
  notes: "Anna dives into conversation from episode 1 — no alphabet lesson"
- title: "Anna Ohoiko — 1000 Most Useful Ukrainian Words, 2nd ed. (Ukrainian Lessons, 2023)"
  notes: "Methodology reference: stress marks, example sentences, euphonic pairs. Commercial — do not copy content."
- title: "Anna Ohoiko — 500+ Ukrainian Verbs (Ukrainian Lessons, 2024)"
  notes: "Methodology reference: conjugation tables, cases overview p.16-17. Commercial — do not copy content."
pronunciation_videos:
  overview: https://www.youtube.com/watch?v=ksXIXj7CXwc
  playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV
  vowels:
    А: https://www.youtube.com/watch?v=hvB3VpcR3ZE
    О: https://www.youtube.com/watch?v=gJFxRIPRZbI
    У: https://www.youtube.com/watch?v=VB1O6PmtYRU
    Е: https://www.youtube.com/watch?v=KFlsroBW0dk
    И: https://www.youtube.com/watch?v=W-1rCu0indE
    І: https://www.youtube.com/watch?v=Z9TH0H4ShGo
    Я: https://www.youtube.com/watch?v=yhSAf41LX8I
    Ю: https://www.youtube.com/watch?v=9JdIBYCTWGw
    Є: https://www.youtube.com/watch?v=O0bwRyyBQSc
    Ї: https://www.youtube.com/watch?v=UcjdjQXhAY8
  consonants:
    М: https://www.youtube.com/watch?v=Ez95H4ibuJo
    Н: https://www.youtube.com/watch?v=vNUfiKHPYaU
    Л: https://www.youtube.com/watch?v=v6-3Xg52Buk
    Р: https://www.youtube.com/watch?v=fMGsQ5KPQgg
    Й: https://www.youtube.com/watch?v=aq0cjB90s3w
    В: https://www.youtube.com/watch?v=aFcvYfvQ2X4
    Б: https://www.youtube.com/watch?v=V1hxBE_JbGg
    П: https://www.youtube.com/watch?v=JksSjjxyW5Y
    Д: https://www.youtube.com/watch?v=g4Bh-lqzd48
    Т: https://www.youtube.com/watch?v=m-jcLR_gK0k
    Г: https://www.youtube.com/watch?v=gVnclpSI0DU
    К: https://www.youtube.com/watch?v=J7sGEI4-xJo
    Ж: https://www.youtube.com/watch?v=dIrGVcqPwqM
    Ш: https://www.youtube.com/watch?v=1D-6MIw3OXY
    З: https://www.youtube.com/watch?v=BhASNxitC1A
    С: https://www.youtube.com/watch?v=7UsFBgSL91E
    Х: https://www.youtube.com/watch?v=vpr58zJSJKc
  special:
    Ь: https://www.youtube.com/watch?v=cJlal8XKBxo
    Ґ: https://www.youtube.com/watch?v=gNjHqjTW9WQ
    Ф: https://www.youtube.com/watch?v=haHRsFFZRQI
    Щ: https://www.youtube.com/watch?v=QmBLieIuf6Q
    Ц: https://www.youtube.com/watch?v=u44eCjR2Oz8
    Ч: https://www.youtube.com/watch?v=UsJkbdsY2RA


---

## Knowledge Packet (textbook research — USE THIS)

The following textbook excerpts are real, verified content from Ukrainian school textbooks. **You MUST ground your writing in this material.** Don't ignore it. Cite sources.

# Verified Knowledge Packet: The Ukrainian Alphabet
**Module:** the-ukrainian-alphabet | **Phase:** A1.1 [Script & First Contact]
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

## Голосні звуки (Vowel Sounds)

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
> 35
> Вимов слова. Запиши їх у два стовпчики. Познач звуки [а], 
> [у], [е] знаком , звуки [йа], [йу], [йе] — знаками 
> .
> Яблуко, маля, буряк, м’ята, юшка, люблю, в’юн, калюжа, 
> єнот, синє, в’є, давнє.
> Один звук: [а], [у], [е]
> Два звуки: [йа], [йу], [йе]
> Маля, …
> Яблуко, …
>  
> Спиши. У яких словах букви я, ю, є позначають два звуки? 
> Склади речення з парами слів на вибір.
> Буряк — бур’ян, ягоди — малята, юнак — тюлень, 
> зозуля — яблуко, лілія — мушля, єнот — літнє, співає — 
> вечірнє.
> БУква ї
> Буква ї завжд

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 81
> 	 Хто є головною героїнею тексту? Який пода-
> рунок отримала Катруся? Що вона показува-
> ла ляльці? Що росло на городі?
> Повторюємо разом
>  Буква я. Звукове  
> значення букви я
> 	 Випиши з тексту слова, виділені блакитним 
> кольором. Зроби звукові схеми. Які звуки по-
> значає буква я в цих словах?
> 	 Перепиши підкреслене речення. Зроби зву-
> кову схему слова з буквою  я. 
> 	 Прочитай тексти.
> Навесні в лісі все оживає. Вироста-
> ють травинки. Розпускаються листочки. 
> Розкриваються квіти. Чиста вода напов­

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> 10
> 29.	
> Поміркуй, що спільного у звуковому складі кожного слова:
> а) кількість складів;	 	
> б) звук [й].
> яблуко
> єнот
> юрта
> їжак
> 30.
> Дослідиѳ, скільки звуків позначають букви я, ю, є, ї на 
> початку складу.
> Крок 1. Який перший звук ти чуєш у назвах букв я, ю, є, ї?
> Крок 2. Скільки звуків позначають букви я, ю, є, ї на початку складу?
> Букви я, ю, є на початку складу позначають два звуки:
> [йа], [йу], [йе]. Буква ї завжди позначає два звуки — [йі].
> 31.
> 1.	 Прочитай слова, уставляючи пропущені букви. Які

> **Source:** unknown, Grade 1
> **Score:** 0.25
>
> УКРАЇНСЬКА МОВА
> БУКВАР 
> ЧАСТИНА 1
> 1 
> КЛАС
> ї
> І. О. БОЛЬШАКОВА
> М. С. ПРИСТІНСЬКА
> о
> о
> м
> н р
> л
> е
> е
> е
> е
> А
> И
> Л
> М
> Є
> О
> І
> Ю
> У
> Е
> Я
> ам
> ам
> ам
> ум
> ум
> ум
> ом
> ом
> ом
> кит
> ліс
> лис
> кіт
> дим
> сік
> дім
> рік
> о
> п
> к
> в
> т
> н
> л

> **Source:** unknown, Grade 2
> **Score:** 0.25
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

## Приголосні: знайомі та фальшиві друзі (Consonants: Familiar and False Friends)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 76
> За мотивами казки Е. Мозера
> Повторюємо разом
> Приголосні звуки: 
> тверді та глухі
> 	 Прочитай імена головних героїнь, чітко ви-
> мовляючи перші звуки.
> Зося, Сюзі.
> 	 Чи вони справжні подруги? Як одна з них до-
> помогла іншій? Знайди та прочитай про це. 
> 	 Який із цих звуків вимовляємо дзвінко, з го-
> лосом? А який — тільки із шумом? 
> 	 Перепиши виділене блакитним кольором ре-
> чення. Підкресли букви, які позначають при-
> голосні звуки. Вимов їх. 
> — Так, але я 
> сама не зможу.
> — Дякую. Ти 
> справжня моя

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> 110
> 395. 1.	 Вправа «Квест».
> 1 2
> 1 2 3
> 396.
> Прочитай. Чи хотів (хотіла) б ти, щоб у твоєму місті (селі) було 
> метро? Чому?
> 

... (truncated for context window)

---

## Required H2 Sections

Your output MUST use these EXACT H2 headings. Missing sections = FAIL.

- `## Звуки і літери (Sounds and Letters)` (~200 words)
- `## Голосні звуки (Vowel Sounds)` (~250 words)
- `## Приголосні: знайомі та фальшиві друзі (Consonants: Familiar and False Friends)` (~300 words)
- `## М'який знак (The Soft Sign — Ь)` (~150 words)
- `## Читаємо вивіски (Reading Signs)` (~300 words)
- `## Summary` (~150 words)

---

## Exercise Placeholders

After each teaching concept, place an exercise placeholder block. Do NOT write exercise syntax — just describe what the exercise should test.

Format:
```
:::exercise-placeholder
type: multiple-choice | cloze | match | true-false | read-and-answer
tests: what skill or knowledge this exercise checks
items: number of items (3-8)
vocabulary: exact Ukrainian words to use (from your content)
correct: correct answer(s)
:::
```

Example:
```
:::exercise-placeholder
type: cloze
tests: И vs І distinction in minimal pairs
items: 3
vocabulary: кит, кіт, бик, бік, сил, сіль
correct: кит=whale, кіт=cat
:::
```

Place 3-5 exercise placeholders per module, distributed across sections.

---

## Immersion Target

TARGET: 5-15% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: Mostly English with Ukrainian words bolded inline.
- UKRAINIAN CONTENT: Words and short phrases inline: "The letter **Н** looks like H but sounds like N."
- DIALOGUES & READING PRACTICE: Short Ukrainian sentences in blockquotes are encouraged.
- TABLES: Simple letter-sound or word-meaning tables.
Ukrainian sentences max 10 words.

---

## Grammar Constraints

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

---

## Vocabulary

**Required:** мáма (mother) — first word, familiar letters only, тáто (father) — familiar letters only, водá (water) — false friend В [в], not 'b', рукá (hand) — false friend Р [р], not 'p', хáта (house, traditional) — introduces Х [х], книга (book) — multiple letter types (К, Н, И, Г), шкóла (school) — introduces Ш [ш], мíсто (city) — introduces І, зимá (winter) — introduces З [з], И, дім (house, modern) — introduces Д [д], І
**Recommended:** áптека (pharmacy) — sign reading practice, банк (bank) — cognate, sign reading, кафé (café) — cognate with Ukrainian spelling, пóшта (post office) — П [п] and Ш [ш] together, мéтро (metro) — cognate, familiar letters, зупинка (bus stop) — real-world sign, multiple letter types

---

## Pronunciation Videos

Overview: https://www.youtube.com/watch?v=ksXIXj7CXwc
Playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV

Per-letter videos — embed each next to its letter description.
Use format: <YouTubeVideo client:only="react" url="URL" label="Літера X — Ukrainian Lessons" />
Replace X with the actual letter. Example: label="Літера А — Ukrainian Lessons"

- Літера А: https://www.youtube.com/watch?v=hvB3VpcR3ZE
- Літера О: https://www.youtube.com/watch?v=gJFxRIPRZbI
- Літера У: https://www.youtube.com/watch?v=VB1O6PmtYRU
- Літера Е: https://www.youtube.com/watch?v=KFlsroBW0dk
- Літера И: https://www.youtube.com/watch?v=W-1rCu0indE
- Літера І: https://www.youtube.com/watch?v=Z9TH0H4ShGo
- Літера Я: https://www.youtube.com/watch?v=yhSAf41LX8I
- Літера Ю: https://www.youtube.com/watch?v=9JdIBYCTWGw
- Літера Є: https://www.youtube.com/watch?v=O0bwRyyBQSc
- Літера Ї: https://www.youtube.com/watch?v=UcjdjQXhAY8
- Літера М: https://www.youtube.com/watch?v=Ez95H4ibuJo
- Літера Н: https://www.youtube.com/watch?v=vNUfiKHPYaU
- Літера Л: https://www.youtube.com/watch?v=v6-3Xg52Buk
- Літера Р: https://www.youtube.com/watch?v=fMGsQ5KPQgg
- Літера Й: https://www.youtube.com/watch?v=aq0cjB90s3w
- Літера В: https://www.youtube.com/watch?v=aFcvYfvQ2X4
- Літера Б: https://www.youtube.com/watch?v=V1hxBE_JbGg
- Літера П: https://www.youtube.com/watch?v=JksSjjxyW5Y
- Літера Д: https://www.youtube.com/watch?v=g4Bh-lqzd48
- Літера Т: https://www.youtube.com/watch?v=m-jcLR_gK0k
- Літера Г: https://www.youtube.com/watch?v=gVnclpSI0DU
- Літера К: https://www.youtube.com/watch?v=J7sGEI4-xJo
- Літера Ж: https://www.youtube.com/watch?v=dIrGVcqPwqM
- Літера Ш: https://www.youtube.com/watch?v=1D-6MIw3OXY
- Літера З: https://www.youtube.com/watch?v=BhASNxitC1A
- Літера С: https://www.youtube.com/watch?v=7UsFBgSL91E
- Літера Х: https://www.youtube.com/watch?v=vpr58zJSJKc
- Літера Ь: https://www.youtube.com/watch?v=cJlal8XKBxo
- Літера Ґ: https://www.youtube.com/watch?v=gNjHqjTW9WQ
- Літера Ф: https://www.youtube.com/watch?v=haHRsFFZRQI
- Літера Щ: https://www.youtube.com/watch?v=QmBLieIuf6Q
- Літера Ц: https://www.youtube.com/watch?v=u44eCjR2Oz8
- Літера Ч: https://www.youtube.com/watch?v=UsJkbdsY2RA

---

## Output Format

Write in **Markdown**. Use:
- `## H2` for section headings (must match plan exactly)
- `### H3` for sub-topics within sections
- `> blockquote` for Ukrainian dialogues and reading practice
- `:::exercise-placeholder` blocks for exercises
- `<!-- adapted from: Author, Grade N -->` for textbook citations
- `<!-- VERIFY: word -->` for uncertain Ukrainian
- Bold for Ukrainian words inline: **книга** (book)

End with `## Summary` containing 3-4 self-check questions.

**Write the full module now. Section by section. Use the knowledge packet.**
