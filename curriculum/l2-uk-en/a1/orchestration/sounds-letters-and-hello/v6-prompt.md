# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **1: Sounds, Letters, and Hello** (A1, A1.1 [Sounds, Letters, and First Contact]).

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
module: a1-001
level: A1
sequence: 1
slug: sounds-letters-and-hello
version: '1.1'
title: Sounds, Letters, and Hello
subtitle: 33 літери, 38 звуків, Привіт!
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
- section: Звуки і літери (Sounds and Letters)
  words: 250
  points:
  - 'Golden rule from Большакова Grade 1 p.24 and Заболотний Grade 5 p.73: ''Ми чуємо і вимовляємо звуки, а бачимо і пишемо
    літери.'' 33 letters (літери), 38 sounds (звуки). Letters are symbols on paper. Sounds are what we hear and pronounce.'
  - 'Two families of sounds: Голосні (vowels) — made with voice only, mouth open, no obstruction. Большакова teaches with
    a poem: ''Голосні почуєш в пісні.'' 6 vowel sounds: [а], [о], [у], [е], [и], [і]. 10 vowel letters: А, О, У, Е, И, І,
    Я, Ю, Є, Ї.'
  - 'Приголосні (consonants) — made with voice + noise or noise only. Lips, teeth, tongue create obstruction. 32 consonant
    sounds. Большакова: ''Приголосні деренчать, і тихенько шелестять.'''
- section: Перші слова (First Words)
  words: 300
  points:
  - 'Some Cyrillic letters look like Latin but may sound different. Start with letters that look AND sound familiar: А, О,
    К, М, Т. Read immediately: мама, тато, кома, атом, мак, око. Important: Ukrainian Т is dental (tongue touches teeth, not
    gum ridge) and К/Т are unaspirated (no puff of air). Close enough for now.'
  - 'False friend letters — the biggest trap for English speakers: В sounds [в] (not ''b''), Н sounds [н] (not ''h''), Р sounds
    [р] rolled (not ''p''), С sounds [с] (not ''c/k''), У sounds [у] (not ''y''), Х sounds [х] (not ''x''). Practice: вода
    (water), рука (hand), сон (dream), ніс (nose), хата (house).'
  - 'New shapes — letters with no Latin equivalent: Б, Г, Ґ, Д, Ж, З, И, Й, Л, П, Ф, Ц, Ч, Ш, Щ. Through words: банк, дім,
    зима, книга, школа. Щ always makes TWO sounds [шч]. Ь has NO sound (softens the consonant before it).'
  - 'Special: Ї always = [йі], never softens. Unique to Ukrainian. Я, Ю, Є can be two sounds OR soften a consonant. Full exploration
    in M02 — for now, just recognize them.'
- section: Привіт! (Hello!)
  words: 250
  points:
  - 'Following Anna Ohoiko ULP Episode 1 — your first conversation. Привіт! — Hi! (informal, use with friends, family, peers).
    Як справи? — How are you? Answers: Добре. Чудово. Нормально. А у тебе? — And you?'
  - 'Рада тебе бачити! (female) / Радий тебе бачити! (male) — Glad to see you! Note: Ukrainian has gendered forms. Women say
    рада, men say радий. This is your first encounter with gender in Ukrainian — it will become a major topic starting M08.'
  - 'Reading practice with the greeting: Read each letter, blend into syllables: При-віт! This word uses letters from all
    groups: П (new), р (false friend!), и (new vowel), в (false friend!), і (vowel), т (familiar).'
- section: Читаємо (Reading Practice)
  words: 250
  points:
  - 'Environmental reading — signs you see in Ukraine: Аптека (pharmacy), Банк (bank), Кафе (cafe), Метро (metro), Пошта (post
    office), Школа (school), Зупинка (bus stop). Sound out each letter, blend into syllables, read the whole word.'
  - 'Ukrainian city names: Київ, Львів, Одеса, Харків, Дніпро, Полтава.'
  - 'First sentences with Це (this is): Це мама. Це банк. Це Київ. Що це? Хто це?'
- section: Підсумок — Summary
  words: 150
  points:
  - 'Self-check: How many letters? How many sounds? Why are they different? What are голосні? What are приголосні? What does
    Привіт mean? How do you respond to Як справи?'
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
  focus: 'Distinguish between sounds (звуки) and letters (літери). Example questions: ''Що ми чуємо і вимовляємо?'' → ''звуки''
    | ''Що ми бачимо і пишемо?'' → ''літери'' | ''Скільки літер в абетці?'' → ''33'' | ''Скільки звуків в українській мові?''
    → ''38''.'
  items: 6
- type: match-up
  focus: 'Match false friend Cyrillic letters to their REAL sounds. Pairs: В ↔ [в] (not ''b''), Н ↔ [н] (not ''h''), Р ↔ [р]
    (not ''p''), С ↔ [с] (not ''c/k''), У ↔ [у] (not ''y''), Х ↔ [х] (not ''x'').'
  items: 6
- type: fill-in
  focus: 'Complete a basic greeting dialogue with blanks. EXACT pattern: ''— {Привіт}! Як {справи}?'' / ''— {Добре}. А у {тебе}?''
    / ''— {Чудово}.'' Options per blank: Привіт / справи / Добре / тебе / Чудово / Нормально.'
  items: 4
- type: group-sort
  focus: 'Sort Cyrillic letters into Голосні (vowels) and Приголосні (consonants). Голосні: А, О, У, Е, И, І. Приголосні:
    К, М, Т, В, Н, Р, С, Х.'
  items: 8
connects_to:
- a1-002 (Reading Ukrainian)
prerequisites: []
grammar:
- Звуки vs літери — 33 letters, 38 sounds
- Голосні (6 sounds, 10 letters) vs приголосні (32 sounds)
- Cyrillic letter-sound mapping (familiar, false friends, new shapes)
- Привіт greeting as first spoken Ukrainian
register: розмовний
references:
- title: Большакова Grade 1 буквар, p.24
  notes: Голосні/приголосні taught through poems. 'Голосні почуєш в пісні.'
- title: Захарійчук Grade 1 буквар (NUS 2025), p.13
  notes: 'Sound notation: [•] for vowels, [–] for consonants.'
- title: Заболотний Grade 5, p.73
  notes: '38 звуків: 6 голосних + 32 приголосні.'
- title: ULP Season 1, Episode 1 — Informal Greetings
  url: https://www.ukrainianlessons.com/episode1/
  notes: Привіт, Як справи?, response patterns.
pronunciation_videos:
  overview: https://www.youtube.com/watch?v=ksXIXj7CXwc
  playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
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
</knowledge_packet>

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
## Звуки і літери — Sounds and Letters (~275 words total)

- P1 (~90 words): Hook — you already know sounds vs letters instinctively (you hear a dog bark, you see the word "dog"). Ukrainian makes this distinction explicit. Introduce the golden rule from Большакова Grade 1: «Ми чуємо і вимовляємо звуки, а бачимо і пишемо літери.» State the key numbers: 33 літери in the абетка, but 38 звуків in the language. Why more sounds than letters? Some letters do double duty — teaser for я, ю, є, ї explored in M02.

- P2 (~95 words): Голосні звуки (vowels) — made with voice alone, mouth open, air flows freely. Большакова's poem: «Голосні почуєш в пісні.» List all 6 vowel sounds: [а], [о], [у], [е], [и], [і]. Then the 10 vowel letters: а, о, у, е, и, і, я, ю, є, ї. The mismatch (6 sounds, 10 letters) exists because я, ю, є, ї are "двозвучні" — they can represent two sounds. For now, just recognize them; full explanation in M02. Practice pronouncing the 6 pure vowel sounds in sequence.

- P3 (~90 words): Приголосні звуки (consonants) — made when lips, teeth, or tongue create an obstruction. Air hits a barrier, producing noise (with or without voice). Большакова's poem: «Приголосні деренчать, і тихенько шелестять.» 32 consonant sounds from 22 consonant letters (plus ь, which has no sound of its own — it softens the consonant before it). Contrast: say [а] — mouth open, pure voice. Now say [м] — lips close, voice + blocked air. That's the difference between голосний and приголосний.

- Exercise: **Group-sort** — Sort 14 letters into Голосні (А, О, У, Е, И, І) and Приголосні (К, М, Т, В, Н, Р, С, Х). 8 items minimum, drawn from letters introduced so far.

## Перші слова — First Words (~330 words total)

- P1 (~85 words): Friendly letters — Cyrillic letters that look AND sound similar to Latin equivalents. Introduce А [а], О [о], К [к], М [м], Т [т]. Immediate reading: мама, тато, кома, атом, мак, око, кот (careful — кіт is the correct Ukrainian word for "cat," кот is Russian; use only as a decoding exercise if included, or skip). Key pronunciation note: Ukrainian Т is dental (tongue touches upper teeth, not the gum ridge like English T), and К/Т have no aspiration (no puff of air). Close enough for now — awareness, not perfection.

- P2 (~90 words): False friend letters — the biggest trap. These LOOK like Latin letters but sound completely different. Present each with a memorable example word: В = [в] not "b" (вода — water), Н = [н] not "h" (ніс — nose), Р = [р] rolled, not "p" (рука — hand), С = [с] not "c/k" (сон — dream), У = [у] not "y" (вухо — ear), Х = [х] not "x" (хата — house). Warn: this is where English speakers make the most mistakes. Your brain will see B and say "b" — fight that instinct.

- Exercise: **Match-up** — Match 6 false-friend Cyrillic letters to their real Ukrainian sounds. Pairs: В↔[в], Н↔[н], Р↔[р], С↔[с], У↔[у], Х↔[х]. Include English "trap" sound as distractor context.

- P3 (~80 words): New shapes — letters with no Latin lookalike. Group by visual similarity where possible: Б (like 6 with a hat), Г (like an upside-down L), Д (like a triangle), Ж (like a snowflake), З (like the number 3), Л (like a tent), П (like a doorway), Ш (like a comb), Щ (like Ш with a tail — always [шч], two sounds). Introduce through words: банк, дім, зима, книга, школа. Don't memorize all 15 now — just recognize they exist.

- P4 (~75 words): Special letters — Ї always pronounced [йі], never softens a preceding consonant. It is unique to Ukrainian (not found in Russian, Belarusian, or any other Slavic language — a point of pride). Words: їжак (hedgehog), Україна. Letters Я, Ю, Є serve double duty: at the start of a word or after a vowel they are two sounds ([йа], [йу], [йе]); after a consonant they soften it. Full rules in M02 — for now, just recognize these four special letters when you see them.

## Привіт! — Hello! (~275 words total)

- P1 (~80 words): Your first Ukrainian conversation. Informal greetings (use with friends, family, people your age or younger). Core phrases: Привіт! (Hi!), Як справи? (How are you?). Responses: Добре. (Fine.), Чудово! (Great!), Нормально. (Okay.). To ask back: А у тебе? (And you?). Note the music of these phrases — Ukrainian has a natural melodic rise-fall that differs from English. Listen and imitate the rhythm, not just the words.

- Dialogue (~100 words): Two friends meet on the street. Format as a natural mini-script with stage directions:
  — Привіт!
  — О, привіт! Як справи?
  — Добре, дякую. А у тебе?
  — Чудово!
  — Рада тебе бачити! (said by a woman)
  Then repeat with male speaker: Радий тебе бачити! Explain: Ukrainian marks gender in adjectives and some verb forms. Women say рада, men say радий. This is your very first encounter with grammatical gender — it will become a major topic from M08 onward. For now, just pick the form that matches you.

- P2 (~95 words): Letter-by-letter reading of Привіт. Break it down: П (new shape — doorway), р (false friend — rolled, not "p"), и (new vowel — between English "i" and "ы"), в (false friend — not "b"), і (vowel — like English "ee"), т (familiar — but dental!). Blend into syllables: При-віт. Stress falls on the second syllable: приВІТ. This one word uses letters from all three groups (familiar, false friends, new shapes) — if you can read Привіт, you've already started reading Ukrainian.

- Exercise: **Fill-in** — Complete a greeting dialogue with blanks. Pattern: «— ___! Як ___?» / «— ___. А у ___?» / «— ___.» Word bank: Привіт, справи, Добре, тебе, Чудово, Нормально. 4–5 blanks.

## Читаємо — Reading Practice (~275 words total)

- P1 (~90 words): Environmental reading — signs you would see walking through a Ukrainian city. Sound out each word letter by letter, then blend into syllables: Аптека (а-пте-ка — pharmacy), Банк (банк — bank), Кафе (ка-фе — café), Метро (ме-тро — metro), Пошта (по-шта — post office), Школа (шко-ла — school), Зупинка (зу-пин-ка — bus stop). Note how many of these are recognizable from English or other European languages — Ukrainian has plenty of international words. The spelling follows Ukrainian rules, but the meaning is transparent.

- P2 (~80 words): Ukrainian city names — practice with proper nouns that carry cultural weight. Київ (Ки-їв — note the Ї!), Львів (Льві-в — note Ь softening Л), Одеса (О-де-са), Харків (Хар-ків), Дніпро (Дні-про), Полтава (Пол-та-ва). These are not just reading exercises — they are real places. Київ is the capital. Львів is the cultural heart of western Ukraine. Pronouncing them correctly is a sign of respect.

- P3 (~105 words): First sentences using Це (this is). Pattern: Це + noun. Це мама. Це банк. Це Київ. Це школа. Це аптека. Then introduce the question forms: Що це? (What is this? — for things) and Хто це? (Who is this? — for people). Mini-dialogue practice: «Що це?» — «Це банк.» / «Хто це?» — «Це мама.» Note the що/хто distinction: що for objects and places, хто for people and animals. This mirrors Ukrainian thinking — the language distinguishes animate from inanimate from the very start.

- Exercise: **Quiz** — 6 questions testing звуки vs літери distinction and alphabet facts. «Що ми чуємо і вимовляємо?» → звуки. «Що ми бачимо і пишемо?» → літери. «Скільки літер в абетці?» → 33. «Скільки звуків?» → 38. «Що це — голосний чи приголосний: [а]?» → голосний. «Що це — голосний чи приголосний: [м]?» → приголосний.

## Підсумок — Summary (~165 words total)

- P1 (~165 words): Recap what you've learned in this first module. Ukrainian has 33 letters (літери) and 38 sounds (звуки) — we hear and pronounce sounds, we see and write letters. Sounds split into two families: голосні (6 vowel sounds, 10 vowel letters) and приголосні (32 consonant sounds). Cyrillic letters fall into three groups for English speakers: friendly (А, О, К, М, Т), false friends (В, Н, Р, С, У, Х — the biggest trap), and new shapes (Б, Г, Д, Ж, Ш, Щ and more). You learned your first greeting: Привіт! Як справи? — Добре! You read real Ukrainian words and city names. You formed your first sentences with Це. Self-check questions: How many letters in the абетка? How many sounds? Why the difference? What are голосні? What are приголосні? What does Привіт mean? How do you answer Як справи? Next module: Reading Ukrainian — where we dive deeper into how letters combine into syllables.

Grand total: ~1320 words
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
