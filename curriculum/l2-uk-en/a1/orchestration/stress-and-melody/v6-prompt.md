# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **4: Stress and Melody** (A1, A1.1 [Sounds, Letters, and First Contact]).

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
module: a1-004
level: A1
sequence: 4
slug: stress-and-melody
version: '1.1'
title: Stress and Melody
subtitle: Наголос changes meaning, intonation changes intent
focus: phonetics
pedagogy: PPP
phase: A1.1 [Sounds, Letters, and First Contact]
word_target: 1200
objectives:
- Understand that Ukrainian stress is free and can change word meaning
- Place stress correctly on common A1 words
- Use rising intonation for yes/no questions and falling for statements
- Read aloud with natural Ukrainian rhythm
content_outline:
- section: Наголос (Stress)
  words: 350
  points:
  - 'Заболотний Grade 5 p.73: Ukrainian has 38 sounds, and stress (наголос) determines which syllable is louder and longer.
    Stress is FREE — it can fall on any syllable, and it MOVES between forms of the same word. This is unlike French (always
    last) or Czech (always first).'
  - 'Stress changes meaning — real pairs learners will encounter: замок (castle) vs замок (lock), мука (torment) vs мука (flour),
    атлас (atlas) vs атлас (satin). Wrong stress = wrong word. This is why stress marks matter.'
  - In writing, stress marks (') appear in textbooks and dictionaries but NOT in everyday Ukrainian text. As a learner, always
    check goroh.pp.ua for stress when unsure.
  - 'Common patterns for beginners: First syllable: мама, тато, ранок, кава, книга. Last syllable: вода, зима, рука, метро,
    кафе. No shortcut — learn each word''s stress individually.'
- section: Інтонація (Intonation)
  words: 300
  points:
  - 'Ukrainian uses intonation (melody) to distinguish sentence types. Same words, different melody, different meaning. Statement:
    Це кава. ↘ (falling — telling) Question: Це кава? ↗ (rising on last stressed syllable — asking) Exclamation: Як гарно!
    ↘↘ (strong fall — expressing emotion)'
  - 'Question words (хто, що, де, коли) make questions WITHOUT rising: Що це? ↘ (falling — the question word does the work).
    Де метро? ↘ (falling). But yes/no questions always rise: Це метро? ↗'
  - 'Ukrainian classifies sentences by purpose: розповідні (declarative), питальні (interrogative), спонукальні (imperative).
    Any of these can also be окличні (exclamatory) — a separate dimension. For A1: focus on the three punctuation patterns:
    . for statements, ? for questions, ! for exclamations/commands.'
- section: Читаємо вголос (Reading Aloud)
  words: 300
  points:
  - 'Multisyllable reading with correct stress: у-кра-їн-ська (Ukrainian — stress on ї), фо-то-гра-фі-я (photograph — stress
    on third а: фотографія), ві-дпо-чи-нок (rest — stress on и). Method: break → find stressed syllable → read at natural
    speed.'
  - 'Short text reading practice: Це Київ. Київ — столиця України. Тут є метро, аптеки, кафе. Read aloud: find the stress
    on each word, use falling intonation for statements.'
  - 'Dialogue practice using greetings from M01: — Привіт! ↘ (statement/greeting) — Привіт! Як справи? ↗ (yes/no question)
    — Добре! А у тебе? ↗ — Теж добре! ↘ Apply intonation patterns to the greetings already learned.'
- section: Підсумок — Summary
  words: 250
  points:
  - 'Self-check: What is наголос? Can it change word meaning? Give an example. What intonation do you use for a yes/no question?
    For a statement? Read this aloud: Це аптека? Так, це аптека. Як гарно!'
vocabulary_hints:
  required:
  - наголос (stress/accent) — metalanguage word
  - замок (castle) — stress pair (first syllable)
  - замок (lock) — stress pair (second syllable)
  - кава (coffee) — first-syllable stress
  - вода (water) — second-syllable stress
  - столиця (capital) — Київ — столиця України
  recommended:
  - мука (flour) — stress pair with мука (torment)
  - ранок (morning) — first-syllable stress
  - метро (metro) — last-syllable stress
  - фотографія (photograph) — long word practice
activity_hints:
- type: quiz
  focus: Where is the stress? Choose the correct syllable.
  items: 8
- type: match-up
  focus: 'Match stress pairs: замок (castle) ↔ замок (lock)'
  items: 4
- type: quiz
  focus: Statement, question, or exclamation? Choose based on punctuation.
  items: 6
- type: fill-in
  focus: 'Add the correct punctuation: Це кава_ Де метро_ Як гарно_'
  items: 6
connects_to:
- a1-005 (Who Am I?)
prerequisites:
- a1-003 (Special Signs)
grammar:
- Free stress system (наголос)
- Stress-meaning pairs
- 'Three intonation patterns: statement ↘, question ↗, exclamation ↘↘'
- Question words don't need rising intonation
register: розмовний
references:
- title: Заболотний Grade 5, p.73
  notes: 38 звуків, наголос. Stress as free and mobile.
- title: Авраменко Grade 5, p.19
  notes: Інтонація речень — розповідні, питальні, окличні.
- title: ULP Season 1, Episode 5 — Pronunciation Trainer
  url: https://www.ukrainianlessons.com/episode5/
  notes: Stress practice with numbers.
pronunciation_videos:
  playlist: https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV

</plan_content>

---

## Knowledge Packet (textbook excerpts from RAG)

Use these as source material. Cite specific examples and adapt pedagogy from Ukrainian textbooks. Write original prose — do not copy excerpts verbatim.

<knowledge_packet>
# Verified Knowledge Packet: Stress and Melody
**Module:** stress-and-melody | **Phase:** A1.1 [Sounds, Letters, and First Contact]
**Textbook grades searched:** 1, 2

---

## Наголос (Stress)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 28
> НАГОЛОС
> Вимов слово на|го|лос. Один зі складів у слові 
> ти вимовляєш сильніше. Це наголошений склад. 
> Наголос позначають знаком ’.
> МАМА
> МА
> А  О  У 
> М  Л  Н  С
> Який склад наголошений? 
>  
> ка|ка|о 
> о|ко 
> сум|ка
>  
> со|ло|ма 
> а|ку|ла 
> мо|ло|ко
>  
> Текст. Тема тексту
> Прочитай або послухай текст. 
> У дів-чин-ки Марини живе кіт Мур-чик. 
> Марина годує котика молоком. Мурчик лю-
> бить гуляти на по-дві-р’ї. А ще Мурчик любить 
> бігати за голубами.
> Визнач тему тексту.
>  
> Кіт Мурчик 
> Про котів  
> Голуби
> А
> О
> У
> 1

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> 9[ Про кого так кажуть?
> Воду носить — рука болить, 
> кашу варить — рука болить, 
> а каша готова — і рука здорова.
> • Зроби висновок про роль наголосу.
> У
> Добра людина хоче добра всім людям.
> носить — носить 
> варить — варить
> 10| Запиши вислови. Постав наголос у виділених словах.
> Дешева рибка, та дорога з неї юшка.
> Тоді дорога успішна, коли розмова втішна.
> 11
> Відгадай загадку Дмитра Білоуса.
> Склади і запиши речення зі словами-відгадками. 
> Постав у них наголос.
> Слово це — старовинна будова 
> з гостряками

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 54
> Знайди слова — підписи до малюнків. 
> 	 загадка	
> замок	
> золотий	
> заєць
> 	забавка	
> замок	
> залізний	
> зайчик
> 	зупинка	
> зерно	
> зелений	
> заячий
> 
> Лічилка. Опис
> Я малюю зайчика для вас. Раз. 
> Це у нього, бачте, голова. Два. 
> Це у нього вуха догори. Три. 
> Це стирчить у нього хвостик сірий. 
> 	
> Чотири. 
> Це очиці весело горять. П’ять. 
> Ротик, зубки — хай морквину їсть. 
> 	
> Шість. 
> Шубка тепла, хутряна на нім. 	Сім. 
> Ніжки довгі, щоб гасав він лісом. 
> 	
> Вісім. 
> Ще навколо насаджу дерева. 
> 	
> Дев’ять. 
> І х

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> ЕКСПЕРИМЕНТУЮ З НАГОЛОСОМ
> б| Змініть слова за зразком і запишіть. 
> Запам'ятайте, як наголошуються ці 
> слова.
> ручка 
> нитка 
> ложка
> шапка
> картка
> стежка
> -------------------------------------------------
> порівнюю 
> пояснюю
> зірка — зірки
> 7| Змініть слова за зразком і прочитайте. Складіть 
> і запишіть речення із трьома словами (на вибір).
> казка
> немає казки
> цікаві казкии
> книжка
> •
> )
> •
> загадка
> •
> J
> •
> приказка
> •
> )
> •
> і
> -у
> Щоб запам'ятати наголос у слові, правильно 
> проговори його кілька разів.
> 8| Зміни слова з

> **Source:** unknown, Grade 1
> **Score:** 0.25
>
> 59
> Знайди слово — підпис до малюнка.
> Відшукай слово до схеми.
>  
> хата 
> муха 
> вухо 
> хвіст
>  хатка 
> мураха 
> тихо 
> хвости
>  хатинка 
> мухомор комаха 
> пастух
>  
> Текст. Послідовність подій. Головна думка
> У лісі ріс мухомор. Бігла мураха, шукала 
> поживу. Залізла мураха на мухомор. Гарно видно 
> навколо. Недалеко грушка впала з дерева. Мура-
> ха побігла грушку шукати.  
> Летіла муха. Мухомор за-при-мі-ти-ла. Сіла, 
> відпочила та й полетіла далі.
> Біжить ховрах. Хворий. Живіт болить. Аж тут — 
> мухомор. Скуштував

> **Source:** unknown, Grade 2
> **Score:** 0.25
>
> Розсердився капловухий Заєць. Лежить у холодку, 
> не поворухнеться.
> А зайці повсідалися на осонні, ласують морквою, 
> капустою.
> Капловухому мулько стало лежати і їсти хочеться.
> — Ідіть уже в холодок! — гукає до зайців.
> — А хіба то наш холодок? То ж твій, — відказують 
> йому зайці.
> Капловухий Заєць як підскочить та як загаласує 
> на весь ліс:
> — Це наш холодок! Наш!
> А зайці як засміються! Отож-то.
>  
> 	 Чи є у тексті слова, значення яких вам незрозуміле? 
> Обговоріть, що вони означають.
>  
> 	 Знайди в ка

## Інтонація (Intonation)

> **Source:** unknown, Grade 1
> **Score:** 0.50
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
> **Score:** 0.50
>
> 111
> пасажирів установлено інформаційні 
> монітори. Вони полегшують користу-
> вання метро пасажирам з порушенням 
> слуху. На нових станціях змонтовані 
> ліфти-підйомники для тих, хто не може 
> самостійно пересуватися сходами.
> Пригадай! Розмову двох людей називають діалогом.
> Учасники діалогу обмінюються репліками.
> Зразок. 
> — Привіт, Кирилку!
> — Привіт, Соломійко!
> — Тобі сподобалося їздити на ескалаторі*?
> — Так, дуже! Пам’ятаєш правила безпечної поведінки 
> в метро?
> — Будьте уважні в метро. У вагоні не пр

> **Source:** unknown, Grade 1
> **Score:** 0.33
>
> 86
> Бачу Т, т (те). Чую  [т], [т'].
> т о р т
> т * л * п а н и
> к і т
>  [ –•  –  – ]
>  [  =  • –  ]
> а
> о
> у
> и
> і
> Т
> та
> то
> ту
> ти
> ті
> а
> о
> у
> и
> і
> ат
> от
> ут
> ит
> іт
> Т
> ті-	 	
> 	
>      тро-	          	
>   та-
>              -то	 	
>    	
>      -та	        	         -ти	
> Та-то  ку-пив  Ро-ма-но-ві 
>  .
> — Тім! Тім! — по-кли-кав  Ро-ман 
> так-су. — На 
>  .
> Т т

> **Source:** unknown, Grade 2
> **Score:** 0.33
>
> 110
> 395. 1.	 Вправа «Квест».
> 1 2
> 1 2 3
> 396.
> Прочитай. Чи хотів (хотіла) б ти, щоб у твоєму місті (селі) було 
> метро? Чому?
> Метро — швидкий, зручний та екологічно чистий 
> вид транспорту. На ньому щодня здійснюють майже поло-
> вину 
> міських 
> перевезень. 
> Довжина 
> київського 
> метро- 
> політену  — майже 70 км. У київському метро є дві станції- 
> «рекордсменки». Найглибша станція  — «Арсенальна». Її 
> глибина  — 105  м 5  см. Станція «Золоті ворота» — одна з 
> найкрасивіших станцій світу. Для покращення о

> **Source:** unknown, Grade 1
> **Score:** 0.25
>
> 60
> Бачу  Ф, ф (еф). Чую  [ф]. 
> а
> о
> у
> и
> і
> Ф
> фа
> фо
> фу
> фи
> фі
> а
> о
> у
> и
> і
> аф
> оф
> уф
> иф
>  іф
> Ф
> фа-
> фу-
> фі-
> фон	
> 	
> 	
> фінал	 	
> 	
> фея
> фонтан	
> 	
> фініш	 	
> 	
> ферма
> теле-
> фон
> граф фла-
> кон
> мінго
> фру-
> кти
> ктовий
> н
> ф л е й т
> ф а з а
> ф л а м
>  [ –•|–•– ]  
>  [ –  –• = | –•] 
> і н г о
> а
> Ф ф
> 	 Прочитай самостійно.
> фа
> фата
> фасон
> фу
> футбол
> футболка
> Pidruchnyk.com.ua

> **Source:** unknown, Grade 2
> **Score:** 0.25
>
> 72
> Напиши смс-повідомлення мамі, татові, учительці, друзям.
> Розкажи про щось
> Я прийшов до …
> Спонукай до чогось
> Прийди… Напиши…
> Запитай про щось
> Хто? Що? Куди? Де?
> розПовІДнІ речення
> Речення, у якому про щось розповідається або пові-
> домляється, називається розповідним. У кінці розпо-
> відного речення ставиться крапка     або знак оклику.
> Визнач, яке речення в кожному рядку є розповідним. Поясни 
> чому. Спиши розповідні речення. 
> 1
> Діти пішли 
> до зоопарку.
> Куди пішли 
> діти?
> Діти, йдіть 
> до зоопарку

## Читаємо вголос (Reading Aloud)

> **Source:** unknown, Grade 1
> **Score:** 0.50
>
> 60
> Бачу  Ф, ф (еф). Чую  [ф]. 
> а
> о
> у
> и
> і
> Ф
> фа
> фо
> фу
> фи
> фі
> а
> о
> у
> и
> і
> аф
> оф
> уф
> иф
>  іф
> Ф
> фа-
> фу-
> фі-
> фон	
> 	
> 	
> фінал	 	
> 	
> фея
> фонтан	
> 	
> фініш	 	
> 	
> ферма
> теле-
> фон
> граф фла-
> кон
> мінго
> фру-
> кти
> ктовий
> н
> ф л е й т
> ф а з а
> ф л а м
>  [ –•|–•– ]  
>  [ –  –• = | –•] 
> і н г о
> а
> Ф ф
> 	 Прочитай самостійно.
> фа
> фата
> фасон
> фу
> футбол
> футболка
> Pidruchnyk.com.ua

> **Source:** unknown, Grade 2
> **Score:** 0.50
>
> 64
> Прочитай слова парами. Як вимовляються перші звуки в сло-
> вах? Запиши три пари слів на вибір і звукові схеми до них.
> фіалка — хвіртка
> фонтан — хвоя
> ферма — хвала
> фігура — хвіст
> фазан — хвалько
> фішка — хвиля
>  
> Яка улюблена справа в кожного з хлопчиків?
>                                      
> фотограф
> фотографує
> фотоапарат
> футбольний

... (truncated for context window)
</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Наголос (Stress)` (~350 words)
- `## Інтонація (Intonation)` (~300 words)
- `## Читаємо вголос (Reading Aloud)` (~300 words)
- `## Підсумок — Summary` (~250 words)
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

**Required:** наголос (stress/accent) — metalanguage word, замок (castle) — stress pair (first syllable), замок (lock) — stress pair (second syllable), кава (coffee) — first-syllable stress, вода (water) — second-syllable stress, столиця (capital) — Київ — столиця України
**Recommended:** мука (flour) — stress pair with мука (torment), ранок (morning) — first-syllable stress, метро (metro) — last-syllable stress, фотографія (photograph) — long word practice

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
