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
  - 'Заболотний Grade 5 p.73: Ukrainian has 38 sounds, and stress (наголос) determines
    which syllable is louder and longer. Stress is FREE — it can fall on any syllable,
    and it MOVES between forms of the same word. This is unlike French (always last)
    or Czech (always first).'
  - 'Stress changes meaning — real pairs learners will encounter: замок (castle) vs
    замок (lock), мука (torment) vs мука (flour), атлас (atlas) vs атлас (satin).
    Wrong stress = wrong word. This is why stress marks matter.'
  - In writing, stress marks (') appear in textbooks and dictionaries but NOT in everyday
    Ukrainian text. As a learner, always check goroh.pp.ua for stress when unsure.
  - 'Common patterns for beginners: First syllable: мама, тато, ранок, кава, книга.
    Last syllable: вода, зима, рука, метро, кафе. No shortcut — learn each word''s
    stress individually.'
- section: Інтонація (Intonation)
  words: 300
  points:
  - 'Ukrainian uses intonation (melody) to distinguish sentence types. Same words,
    different melody, different meaning. Statement: Це кава. ↘ (falling — telling)
    Question: Це кава? ↗ (rising on last stressed syllable — asking) Exclamation:
    Як гарно! ↘↘ (strong fall — expressing emotion)'
  - 'Question words (хто, що, де, коли) make questions WITHOUT rising: Що це? ↘ (falling
    — the question word does the work). Де метро? ↘ (falling). But yes/no questions
    always rise: Це метро? ↗'
  - 'Ukrainian classifies sentences by purpose: розповідні (declarative), питальні
    (interrogative), спонукальні (imperative). Any of these can also be окличні (exclamatory)
    — a separate dimension. For A1: focus on the three punctuation patterns: . for
    statements, ? for questions, ! for exclamations/commands.'
- section: Читаємо вголос (Reading Aloud)
  words: 300
  points:
  - 'Multisyllable reading with correct stress: у-кра-їн-ська (Ukrainian — stress
    on ї), фо-то-гра-фі-я (photograph — stress on third а: фотографія), ві-дпо-чи-нок
    (rest — stress on и). Method: break → find stressed syllable → read at natural
    speed.'
  - 'Short text reading practice: Це Київ. Київ — столиця України. Тут є метро, аптеки,
    кафе. Read aloud: find the stress on each word, use falling intonation for statements.'
  - 'Dialogue practice using greetings from M01: — Привіт! ↘ (statement/greeting)
    — Привіт! Як справи? ↗ (yes/no question) — Добре! А у тебе? ↗ — Теж добре! ↘ Apply
    intonation patterns to the greetings already learned.'
- section: Підсумок — Summary
  words: 250
  points:
  - 'Self-check: What is наголос? Can it change word meaning? Give an example. What
    intonation do you use for a yes/no question? For a statement? Read this aloud:
    Це аптека? Так, це аптека. Як гарно!'
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
## Наголос (Stress) (~385 words total)

- P1 (~90 words): Introduce наголос as the core concept — Ukrainian has 38 sounds, and stress determines which syllable is louder and longer. Stress is FREE (вільний) — it can fall on any syllable: МАма (first), водА (last), столИця (middle). It also MOVES between forms: рукА → рУки, водА → вОди. Compare briefly: French always stresses the last syllable, Czech the first — Ukrainian has no such shortcut. Every word must be learned with its stress.

- P2 (~80 words): Stress changes meaning — present three concrete minimal pairs. замок (ЗАмок = castle, замОК = lock), мука (мУка = torment, мукА = flour), атлас (Атлас = atlas/book of maps, атлАс = satin fabric). Wrong stress doesn't just sound odd — it produces a completely different word. A learner saying замОК when pointing at a castle will confuse listeners. This is why dictionaries and textbooks mark stress.

- P3 (~70 words): Explain stress notation — in textbooks and dictionaries, stress is marked with ´ over the vowel. But everyday Ukrainian text (books, signs, messages) has NO stress marks. As a learner, use goroh.pp.ua to check stress on any word. Over time, stress becomes automatic — like knowing where the beat falls in a familiar song.

- P4 (~85 words): Common A1 stress patterns with examples grouped by position. First syllable: мАма, тАто, рАнок, кАва, кнИга, хАта. Last syllable: водА, зимА, рукА, метрО, кафЕ. Middle syllable: столИця, аптЕка, дитИна. Emphasize: these groupings are for convenience — there is no reliable rule. The only strategy is to learn each word's stress when you first meet it. Say each word aloud three times (textbook advice from Grade 2: "Щоб запам'ятати наголос у слові, правильно проговори його кілька разів").

- Exercise: Quiz — "Where is the stress? Choose the correct syllable." 8 items: кава, вода, столиця, ранок, метро, аптека, книга, зима.

- P5 (~60 words): Stress moves between forms — show with two familiar words. рукА → рУки (singular → plural), водА → вОди (singular → plural). This is why you can't just memorize "вода = last syllable" — the stress shifts in other forms. For now, just notice this happens. Later modules will cover it systematically as you learn noun forms.

## Інтонація (Intonation) (~330 words total)

- P1 (~80 words): Introduce intonation as melody — the rise and fall of your voice across a sentence. Same words with different melody = different meaning. Present the core trio with Це кава as the base: Statement: Це кава. ↘ (voice falls at the end — you're telling someone). Question: Це кава? ↗ (voice rises on the last stressed syllable — you're asking). Exclamation: Це кава! ↘↘ (voice falls sharply — you're surprised or excited). The words are identical — only the melody and punctuation change.

- P2 (~85 words): Question words change the rule — when a sentence starts with хто, що, де, коли, the question word itself signals "this is a question," so intonation falls: Що це? ↘ Де метро? ↘ Коли? ↘ But yes/no questions (no question word) MUST rise: Це метро? ↗ Ти тут? ↗ Вона вдома? ↗ Simple test: if you can answer так/ні, the intonation rises. If the question starts with a question word, it falls. Practice pairs: Де кава? ↘ vs. Це кава? ↗

- Exercise: Quiz — "Statement, question, or exclamation? Choose based on punctuation and context." 6 items using: Це аптека. / Це аптека? / Де аптека? / Як гарно! / Тут метро. / Тут метро?

- P3 (~75 words): Ukrainian grammar names for sentence types — розповідні речення (declarative — telling, ends with .), питальні речення (interrogative — asking, ends with ?), спонукальні речення (imperative — commanding/requesting, ends with ! or .). Any of these can also be окличні (exclamatory) — that's a separate quality, not a fourth type. For A1, focus on recognizing the three punctuation marks and their melody patterns.

- Exercise: Fill-in — "Add the correct punctuation: Це кава_ Де метро_ Як гарно_ Ти тут_ Це Київ_ Вона вдома_" 6 items.

- P4 (~90 words): Mini-dialogue demonstrating all three intonation types in a natural exchange. Two friends meeting at a café: — Привіт! Це нове кафе? ↗ (yes/no question — rising) — Так, це нове кафе. ↘ (statement — falling) — Де кава? ↘ (question-word question — falling) — Ось кава. ↘ (statement — falling) — Як гарно! ↘↘ (exclamation — sharp fall). Point out which pattern each line uses. This dialogue recycles кафе and кава from the stress section and Привіт from M01.

## Читаємо вголос (Reading Aloud) (~330 words total)

- P1 (~80 words): Method for reading multisyllable words — three steps: (1) break into syllables, (2) find the stressed syllable, (3) read at natural speed. Demonstrate with three words: у-кра-ї́н-ська (stress on ї — fourth syllable), фо-то-гра́-фі-я (stress on third а), від-по-чи́-нок (stress on и). Show the broken form first, then the natural form. Emphasize: breaking into syllables is a learning tool, not how Ukrainians actually speak. The goal is smooth, natural reading.

- P2 (~90 words): Short connected text for reading practice — all words from A1 vocabulary already encountered or transparently simple. "Це Ки́їв. Ки́їв — столи́ця Украї́ни. Тут є метро́, апте́ки, кафе́. А це Льві́в. Льві́в — гарне мі́сто. Тут є ка́ва і кни́ги." Instruction: read aloud, paying attention to stress (marked) and falling intonation on each statement. Then read again without looking at stress marks — can you remember them? Note: in real Ukrainian text, these marks wouldn't appear.

- Exercise: Match-up — "Match stress pairs: замок (castle) ↔ ЗАмок, замок (lock) ↔ замОК, мука (torment) ↔ мУка, мука (flour) ↔ мукА." 4 items.

- P3 (~100 words): Dialogue practice combining stress awareness and intonation — use greetings from M01 with intonation arrows. — Приві́т! ↘ (greeting — falling) — Приві́т! Як спра́ви? ↗ (yes/no-like question — rising) — До́бре! А у те́бе? ↗ (reciprocal question — rising) — Те́ж до́бре! ↘ (statement — falling) — Де ка́ва? ↘ (question-word — falling) — Ось ка́ва. ↘ (statement — falling). Instructions: read with a partner or record yourself. Check: does your voice rise on Як справи? and fall on Де кава? Replay and compare.

- P4 (~60 words): Encouragement and real-world connection — stress and intonation feel like a lot to track, but native speakers do it automatically. Every time you hear Ukrainian (music, podcasts, conversations), listen for the melody. Notice which syllable is louder, whether the voice rises or falls. Your ear learns faster than your eyes. Read the dialogue above one more time — slower, then at natural speed.

## Підсумок — Summary (~275 words total)

- P1 (~100 words): Recap the three key concepts. (1) Наголос is free and mobile — it can fall on any syllable and moves between word forms. Wrong stress can change meaning entirely (замок/замок, мука/мука). (2) Інтонація distinguishes sentence types — statements fall ↘, yes/no questions rise ↗, question-word questions fall ↘, exclamations fall sharply ↘↘. (3) Reading aloud combines both skills — find the stress, apply the melody, build toward natural speed. These are not abstract rules — they are how Ukrainian sounds. Without them, even perfect grammar sounds foreign.

- P2 (~90 words): Self-check questions for the learner. Що таке наголос? (What is stress?) — The syllable you say louder and longer. Чи може наголос змінити значення слова? (Can stress change word meaning?) — Yes: зАмок (castle) vs замОк (lock). Яка інтонація у питанні "Це кава?" — Rising ↗. А у питанні "Де кава?" — Falling ↘. Read aloud: "Це апте́ка? Так, це апте́ка. Як га́рно!" — did your voice rise on the first sentence, fall on the second, and drop sharply on the third?

- P3 (~85 words): Bridge to next module — you now have the building blocks of Ukrainian sound: letters and sounds (M02-M03), special signs (M03), and now stress and melody (M04). In the next module (M05: Who Am I?), you'll use all of these to introduce yourself in Ukrainian. You'll say your name, where you're from, and what you do — with correct stress and natural intonation. The sounds become words, the words become sentences, and the sentences become you speaking Ukrainian.

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
