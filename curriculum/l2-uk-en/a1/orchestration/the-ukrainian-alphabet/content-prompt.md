# Full Module Build: Content + Activities + Vocabulary

> **You are Patient & Supportive Ukrainian Tutor, writing in the voice of Patient Supportive Tutor.**
>
> **Your role:** You are an **editor and adapter**, not an author writing from scratch.
> Ukrainian school textbooks have already solved "how to teach this topic." Your job is to **find the right pedagogical approach in the textbook excerpts below** and **transform it** for English-speaking learners (teens and adults) at the a1 level.
>
> **Your task:** Build a complete beginner module — lesson content, practice activities, and vocabulary — in one pass.
> Writing content and activities together ensures consistency: the same words, the same gender pairings, the same phrases appear in both.
>
> **Output capacity: 65,000+ tokens.** Do NOT truncate.

---

## 1. Read These Files

| File | What to extract |
|------|----------------|
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/the-ukrainian-alphabet-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/the-ukrainian-alphabet.yaml` | Objectives, content_outline, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

Read ALL files before writing anything.

---

## 2. Constraints (apply to EVERYTHING you write)

### Grammar Constraints (HARD FAIL if violated)

GRAMMAR BAN (pre-verbal phase — no verbs exist yet):
- NO imperative forms: Слухайте, Читайте, Повторюйте, Пишіть, Дивіться — ALL BANNED
- NO verb conjugation of any kind (present, past, future)
- Classroom instructions MUST be in English: 'Listen carefully', 'Read aloud', 'Repeat'
- Allowed Ukrainian structures: bare nouns, noun phrases, Це + noun

METALANGUAGE:
- ALL terminology in English first, Ukrainian in parentheses: 'vowels (голосні)'
- Section headings MUST be bilingual (e.g., '## Голосні — Vowels')
- NEVER write Ukrainian-only explanatory prose

VERB-FREE UKRAINIAN PATTERN BANK:
- Це + noun: «Це кіт», «Це стіл»
- Question particles: «Хто це?», «Що це?»
- Adj + noun: «великий дім», «нова книга»
- Contextual labels: «Наприклад — For example», «А тепер — And now»
DO NOT use conjugated verbs, imperatives, or infinitives.

### Vocabulary Guidance

DECODABLE VOCABULARY (only letters: І, А, К, Л, М, Н, О, С, Т, У):
Use ONLY these words in reading drills and prose examples.
Any word with a letter outside this set will FAIL the decodability audit gate.
Sight words from the plan are exempt — they are recognized as whole shapes,
not decoded letter-by-letter. Label them clearly.
Video pronunciation examples are also exempt (heard, not read).

Available decodable words: мама, тато, кіт, молоко, масло, ліс, місто, око, так, ні, сон, сом, ніс, мак, сік, стіл, тут, там, лук, кіно

If you need a word not on this list, check that ALL its letters are in the
allowed set above. Words with unknown letters need English translation.

**Target vocabulary** (from the plan — you MUST teach and use these words heavily):

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- мама (mom) — decodable (М+А+М+А); universal first word; Bolshakova p.14
- тато (dad) — decodable (Т+А+Т+О); high-frequency family word
- кіт (cat) — decodable (К+І+Т); high-frequency; Bolshakova
- молоко (milk) — decodable (М+О+Л+О+К+О); Bolshakova p.14
- масло (butter) — decodable (М+А+С+Л+О); Bolshakova p.15
- ліс (forest) — decodable (Л+І+С); high-frequency
- місто (city) — decodable (М+І+С+Т+О); high-frequency
- око (eye) — decodable (О+К+О); Bolshakova p.13
- так (yes) — decodable (Т+А+К); survival word
- ні (no) — decodable (Н+І); survival word

**Recommended** (include if space allows):
- сон (dream/sleep) — decodable (С+О+Н); Bolshakova p.22
- сом (catfish) — decodable (С+О+М); Bolshakova p.22
- ніс (nose) — decodable (Н+І+С); body vocabulary
- мак (poppy) — decodable (М+А+К); Bolshakova
- сік (juice) — decodable (С+І+К); everyday food word
- стіл (table) — decodable (С+Т+І+Л); everyday object
- тут (here) — decodable (Т+У+Т); high-frequency adverb
- там (there) — decodable (Т+А+М); high-frequency adverb
- лук (onion/bow) — decodable (Л+У+К); everyday food
- кіно (cinema) — decodable (К+І+Н+О); everyday word

These are your TARGET words — teach them all and use them heavily. For the rest of the text, use natural, level-appropriate Ukrainian.

**VOCAB-IN-CONTENT RULE:** All vocabulary words from vocabulary_hints MUST appear at least once in the module content. Orphaned vocabulary (listed but never used in content) is a validation failure.

**Rules:**
- Teach all target vocabulary words listed above. These must appear in your content with clear context.
- For the rest of the text, use natural, level-appropriate Ukrainian guided by the textbook excerpts below.
- Match the syntactic complexity, sentence length, and vocabulary level of the provided textbook excerpts. Do not exceed their lexical density.
- When textbook excerpts contain vocabulary or grammar not yet taught at this level, simplify or provide an English gloss in parentheses.
- Activities may ONLY use Ukrainian words that appear in the content you wrote above. Do not introduce new vocabulary in activities.

### Immersion Target

TARGET: 5-15% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: 100% English.
- UKRAINIAN CONTENT: Individual letters and words only — bolded inline in English prose with translation in parentheses: "The letter **Н** looks like H but sounds like N."
- TABLES: Simple letter-sound or word-meaning tables (Ukrainian in left column, English in right).
- STRUCTURAL RULE: Every paragraph is English. Ukrainian never appears as a standalone sentence.
Ukrainian sentences max 10 words.

### Structural Containment (how to achieve immersion without code-switching)

**IMPORTANT**: The immersion calculator STRIPS markdown tables when counting Ukrainian content. Tables still work for grammar paradigms and explanations, but they contribute ZERO to your immersion score. Use **blockquote dialogues**, **bulleted example lists**, and **pattern boxes** for Ukrainian content that counts toward immersion. Tables are for English-language grammar explanations and paradigm displays.

**Three rules govern where each language appears:**

1. **Paragraphs = English** with Ukrainian vocabulary **bolded inline**: "The informal command of **читати** (to read) is **читай**." Short phrases and grammatical fragments (e.g., comparing **Я йду** vs **Я іду**) may appear inline.

2. **Full Ukrainian sentences = structural containers only.** Any Ukrainian sentence (3+ words with a verb) must go in one of these containers — never in flowing prose paragraphs:
   - **Tables** — paradigms, vocabulary groups, gender sorting (highest immersion density)
   - **Bulleted example lists** — Ukrainian line + English gloss: `- **Читай книгу!** — Read the book!`
   - **Blockquote dialogues** — mini-conversations with labeled speakers
   - **Pattern boxes** — transformations: `читати → читай → читайте`

3. **Vary containers.** Never use the same container type twice in a row. Alternate between tables, example lists, dialogues, and pattern boxes to keep the rhythm natural.

### Style Rules

- Ukrainian section headers with English in parentheses: `## Наказовий спосіб (The Imperative Mood)`
- **No Russianisms**: кушати→їсти, получати→отримувати, самий→найкращий
- **No Russian characters**: ы, э, ё, ъ — never
- **No IPA or phonetic brackets**
- **Quotes**: Use «...» not "..."

---

## 3. Write the Lesson Content

Write **The Ukrainian Alphabet** for the a1 track.

**Targets:**
- 1200–1800 words (under 1200 = FAIL)
- 3+ callout boxes (`[!tip]`, `[!warning]`, `[!did-you-know]`, `[!culture]`)
- EXACT H2 titles from the outline below — missing/renamed sections fail validation

## REQUIRED H2 Sections (use EXACT titles)

Your output MUST use these EXACT H2 headings — do NOT rephrase, translate differently, or add creative subtitles. The audit will reject any section with a different title.

- `## Вступ — Introduction` (~150 words)
- `## Букви і звуки — Letters and Sounds` (~200 words)
- `## Голосні та приголосні — Vowels and Consonants` (~200 words)
- `## Перші 10 літер — First 10 Letters` (~350 words)
- `## Перші слова — First Words in Context` (~200 words)
- `## Підсумок — Summary` (~100 words)

### Section Word Budgets

| Section | Target |
|---------|--------|
| Вступ — Introduction | 150 |
| Букви і звуки — Letters and Sounds | 200 |
| Голосні та приголосні — Vowels and Consonants | 200 |
| Перші 10 літер — First 10 Letters | 350 |
| Перші слова — First Words in Context | 200 |
| Підсумок — Summary | 100 |
| **Total** | **1200** |

### Writing Style (Alphabet / Phonology Module)

You're writing for someone seeing Ukrainian for the first time. English explains; Ukrainian is what they're learning.

Follow the structural containment rules above. Each H2 section MUST follow this sequence:

1. **EXPLAIN** — English paragraph introducing the concept (with Ukrainian letters/words bolded inline)
2. **SHOW** — A table, chart, or bulleted example list demonstrating the letters/sounds
3. **REINFORCE** — A callout box (tip, warning, culture note, or fun fact)

**This is an alphabet/phonology module — NOT a grammar module.** There are no grammar patterns to discover. Do NOT write dialogues. Do NOT use the DISCOVER-UNDERSTAND-PRACTICE pattern. Focus on:
- Letter shapes and their sounds
- False friends (letters that look like English but sound different)
- Blending letters into syllables, syllables into words
- Reading practice with decodable words

**FORBIDDEN patterns (HARD FAIL):**
- Dialogues (verbs are banned in this phase — dialogues need verbs)
- Starting a section with Ukrainian sentences (start with English explanation)
- Bulleted example lists longer than 8 items
- Abstract phonetic descriptions (use comparisons to English sounds instead)

Keep paragraphs short (3-5 sentences). Use 3+ callout boxes spread across sections.

Ukrainian grammar terminology (голосні, приголосні, іменник, дієслово, etc.) — introduce English-first with Ukrainian in parentheses: "vowels (голосні)". Only use terms relevant to this module's grammar scope (see PEDAGOGICAL_CONSTRAINTS above). Do NOT write IPA or Latin transliteration.

**Deliberate errors (showing common mistakes):**
When showing a wrong pattern to avoid, use strikethrough: ~~великий книга~~ → велика книга. This tells the validator the error is intentional. In activities, wrong forms in `options` arrays are always fine (they're distractors) — no special marking needed.

## Language Quality Rules (All Tiers)

### Russianisms (HARD FAIL if found)

Scan your ENTIRE output for these. They cause automatic audit failure:

| Russicism | Correct Ukrainian |
|-----------|-------------------|
| кушати | їсти |
| приймати участь | брати участь |
| получати | отримувати |
| самий кращий | найкращий |
| відноситися | стосуватися |
| слідуючий | наступний |
| любий (= будь-який) | будь-який |
| на то, що | на те, що |
| красивий | гарний |
| прекрасне / прекрасний | чудовий / чудове |

Also scan for Russian characters: **ы, э, ё, ъ** — these must NEVER appear in Ukrainian text.

### English Calque Checklist

As an English-dominant model, you may produce English-to-Ukrainian calques. Check and avoid:

| English Pattern | WRONG Ukrainian | CORRECT Ukrainian |
|---|---|---|
| "will have" | буду мати | матиму |
| "do work" | робити роботу | працювати |
| "save money" | зберегти гроші | заощадити гроші |
| "make a decision" | зробити рішення | прийняти рішення |
| "take a photo" | брати фото | фотографувати / робити фото |
| "have attention" | мати увагу | звертати увагу |
| "give an answer" | давати відповідь | відповідати |
| "make sense" | робити сенс | мати сенс |

### Euphony / Милозвучність (WARNING if violated)

Ukrainian prose must follow euphony rules:

| Rule | Avoid (Bad) | Use (Good) |
|------|-------------|------------|
| і → й between vowels | вона і Олена | вона й Олена |
| й → і after consonant | він й Олена | він і Олена |
| у → в before vowel | у Одесі | в Одесі |
| в → у before в, ф | в вікні | у вікні |
| в → у before consonant cluster | в зграї | у зграї |
| з → із/зі before з, с, ш, ч | з зброєю | із зброєю (або зі) |
| Vary conjunctions | він і вона і Іван | він і вона та Іван |

Key: й can ONLY follow a vowel. After a consonant, always use і — even before a vowel.

### Stress Mark Typography

Use lowercase letters with a combining acute accent (´) on the stressed vowel:
- Correct: ма́ма, анана́с, оса́, сосна́
- Wrong: мА́ма, ананА́с, осА́, соснА́ (do NOT capitalize the stressed vowel)

### Non-Decodable Ukrainian in Beginner Modules (M1-M6)

In Cyrillic primer modules, the learner can only read letters taught so far. Any Ukrainian phrase using letters outside the cumulative charset MUST include an English translation in parentheses immediately after. No exceptions — the learner literally cannot read it otherwise.

- Correct: "Все буде добре (Everything will be fine)."
- Wrong: "Все буде добре." (no translation — learner cannot read Б or Д at M2)

### IPA and Latin Transliteration (BANNED at ALL levels)

Never include IPA symbols (ɑ, ɛ, ʃ, etc.) or bracketed pronunciation guides like `[ma-ma]`, `[a-na-nas]`, `[ˈmɑmɑ]`. The ONLY pronunciation aid is the stress mark (´) on the vowel.

Latin transliterations are BANNED: never use kh, sh, ch, zh, ts, ya, yu, ye, shch.

```markdown
❌ WRONG: "мама [ˈmɑmɑ]" or "хліб (khlib)"
✅ RIGHT: "**ма́ма** (mom)" or "**Х**, like the «ch» in Scottish «loch»"
```

### Typography

- **ALWAYS** use Ukrainian angular quotes: «...» (never straight quotes "...")
- Use ONLY vocabulary from the plan's `vocabulary_hints` — do NOT invent new terms

### No Word Salad (HARD FAIL)

Every paragraph must have ONE clear point and logical flow between sentences. Do NOT string together unrelated observations.

### LLM Writing Patterns to Avoid

1. **"Це не просто X, а Y"** — max ONE in entire module
2. **Grandiose openers** — don't inflate every topic
3. **Purple prose** — no "багатогранний діамант", "хірургічного аналізу"
4. **Duplicate greetings** — "Ласкаво просимо" ONCE (intro only)
5. **Stacked identical callouts** — same title max twice, vary types
6. **"In this lesson, we will..."** — ALWAYS banned (formulaic opener)
7. **Repetitive transitions** — "It's worth noting...", «Варто зазначити...», «Давайте розглянемо...» flagged at 2+ occurrences

### Anti-Robotic Writing

- No 3+ sentences starting with the same phrase
- Vary sentence openers across sections
- No mechanical transitions («Далі ми побачимо...», «Тепер розглянемо...»)
- Each section should have its own narrative arc

### Active Voice Preference

Ukrainian strongly prefers active constructions. Use passive only when the agent is truly unknown.

Avoid: «Це може бути використано...», «Правило застосовується...»
Prefer: «Ви можете використати...», «Ми застосовуємо правило...»


### Videos
- **Український алфавіт. Ukrainian Alphabet. Буква И та І.** (Bright Kids Ukrainian)
  URL: https://www.youtube.com/watch?v=iANCDByts4M
  Score: 0.9 -- The video directly focuses on teaching the Ukrainian letters 'И' and 'І' and introduces words starting with them, which aligns perfectly with the module's objective of introducing letters and first words.
  Suggested placement: After section Букви і звуки — Letters and Sounds, as it introduces specific letters and sounds in a child-friendly format.
  Key excerpt: Ми сьогодні будемо вивчати дуже цікаву літеру... літеру И літеру і... дітки Давайте ми з вами познайомимося словами які розпочинаються на літеру і.

- **Український алфавіт. Ukrainian Alphabet. Буква К** (Bright Kids Ukrainian)
  URL: https://www.youtube.com/watch?v=DvqBLjMGwv0
  Score: 0.9 -- The video directly focuses on teaching the Ukrainian letter 'К' and introduces several words beginning with it, which is highly relevant to the module's sections on letters and first words.
  Suggested placement: After section Букви і звуки — Letters and Sounds, as it introduces specific letters and sounds in a child-friendly format.
  Key excerpt: де ми вивчаємо український алфавіт... літеро к... познайомся і привітайся з нашими дітками дітки скажіть Добрий день Вітаю Вітаю пані літеро.


### Blog Articles & Guides
- **Ukrainian Cyrillic Alphabet — Letters and Sounds** (ukrainianlessons.com)
  URL: https://www.ukrainianlessons.com/ukrainian-cyrillic-alphabet/
  Relevance: 0.4
  Topics: alphabet, cyrillic, letters, sounds

- **Ukrainian Phrasebook: Alphabet** (ukrainianlessons.com)
  URL: https://www.ukrainianlessons.com/ph-alphabet/
  Relevance: 0.4
  Topics: alphabet, pronunciation, basics

- **Talk Ukrainian: Ukrainian alphabet with pronunciation** (talkukrainian)
  URL: https://talkukrainian.com/ukrainian-alphabet/
  Relevance: 0.4
  Topics: alphabet, letters, pronunciation, cyrillic

- **Ukrainian Alphabet: Full Guide with Examples and Pronunciation** (ukrainianlessons.com)
  URL: https://www.ukrainianlessons.com/ukrainian-alphabet/
  Relevance: 0.3
  Topics: alphabet, cyrillic, pronunciation, letters

- **Transliteration of Ukrainian — How to Write Ukrainian in Latin Letters** (ukrainianlessons.com)
  URL: https://www.ukrainianlessons.com/transliteration/
  Relevance: 0.3
  Topics: transliteration, writing, alphabet


### Textbook References
- **Grade 2, Сторінка 27**
  27
ЗвУки І БУкви. аБЕтка
Звуки мови ти можеш позначити буквами. Букви — 
це умовні знаки. Букви ти можеш побачити 
 
і написати 
.
Розглянь малюнки. Коли діти чують і вимовляють звуки мови, 
а коли во...

- **Grade 1, Сторінка 11**
  11
БУКВИ 
Ти можеш записати те, що говориш, буквами. 
Букви — це умовні знаки, які позначають звуки мови.
Букви ти можеш побачити 
 і написати 
.
Якщо ти запишеш букви української мови в певному 
поря...

- **Grade 2, Сторінка 6**
  6
11.	
1.	 Чи пам’ятаєш ти алфавіт? Назви́ всі букви укра-
їнської мови в алфавітному порядку. Проскануй 
QR-код та прослухай пісню про алфавіт.
Український алфавіт
Зразок. Каштан.
2.	 Дослідиѳ алфаві...

- **Grade 4, Сторінка 5**
  5
5.	 	Розгляньте діаграму. Обговоріть її зміст. Визначте, що ви вже 
вивчили із цього розділу, а що будете вивчати. Повторіть 
вивчене.
Застарілі й нові слова
	
Синоніми до слова абетка — … , … .
	
Б...

- **Grade 4, Сторінка 159**
  159
ЗМІСТ
МОВА І МОВЛЕННЯ. Українська абетка: звуки та букви. . . . . . . . . . . . . . 5
СЛОВО. ЗНАЧЕННЯ СЛОВА. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 16
ІМЕННИ...


### Pronunciation Videos (from plan — MANDATORY embeds)
*Credit: Anna Ohoiko — Ukrainian Lessons*

- **Overview**: [Anna Ohoiko — Ukrainian Lessons — Overview](https://www.youtube.com/watch?v=ksXIXj7CXwc)
- **Full Playlist**: [Anna Ohoiko — Ukrainian Lessons — Playlist](https://www.youtube.com/playlist?list=PLpkSIXDyaJi3mlJlKXWKhdiJZj67fPXQV)

**Each letter below MUST get its video embedded in the corresponding H3 section:**

- **Літера А**: [Anna Ohoiko — Ukrainian Lessons — А](https://www.youtube.com/watch?v=hvB3VpcR3ZE)
- **Літера О**: [Anna Ohoiko — Ukrainian Lessons — О](https://www.youtube.com/watch?v=gJFxRIPRZbI)
- **Літера У**: [Anna Ohoiko — Ukrainian Lessons — У](https://www.youtube.com/watch?v=VB1O6PmtYRU)
- **Літера І**: [Anna Ohoiko — Ukrainian Lessons — І](https://www.youtube.com/watch?v=Z9TH0H4ShGo)
- **Літера М**: [Anna Ohoiko — Ukrainian Lessons — М](https://www.youtube.com/watch?v=Ez95H4ibuJo)
- **Літера Н**: [Anna Ohoiko — Ukrainian Lessons — Н](https://www.youtube.com/watch?v=vNUfiKHPYaU)
- **Літера Т**: [Anna Ohoiko — Ukrainian Lessons — Т](https://www.youtube.com/watch?v=m-jcLR_gK0k)
- **Літера К**: [Anna Ohoiko — Ukrainian Lessons — К](https://www.youtube.com/watch?v=J7sGEI4-xJo)
- **Літера С**: [Anna Ohoiko — Ukrainian Lessons — С](https://www.youtube.com/watch?v=7UsFBgSL91E)
- **Літера Л**: [Anna Ohoiko — Ukrainian Lessons — Л](https://www.youtube.com/watch?v=v6-3Xg52Buk)

### Textbook Source Material (ADAPT, don't ignore)

## Textbook Reference Examples (from real Ukrainian буквар)

These are real exercises from Ukrainian 1st-grade primers. Use them as **inspiration for style and difficulty level** — notice how they use simple syllable combinations, short words, and build progressively. Do NOT copy them verbatim, but match their pedagogical approach and simplicity.

**Grade 1, zaharijchuk** — Сторінка 96:
```
94
Бачу Д, д (де). Чую [д], [д'].
д р і * д
д * т е л
дро-ва
две-рі
до-ріж-ка схо-ди
ве-ран-да
л е * і д *
 [ –    =  • –  – ]
 [ = • |  –•  – ]
 [ – • |  =•  =  ]
а
о
у
и
і
Д
да
до
ду
ди
ді
а
о
у
и
і
ад
од
уд
ид
ід
Д
бу-ди-нок
під-ві-кон-ня
дах
ди-мар
Д д
```

**Grade 1, zaharijchuk** — Сторінка 113:
```
111
	 Запиши слова, добираючи до кожного відпо-
відну схему.
   півень          ялинка               джміль
[ – =  = ]            [ =  |–  = ]            [ =  |–  – |–  ]
	 Розглянь малюнки.
	 Запиши слова — назви намальованих пред-
метів за групами: овочі та шкільне приладдя.
	 Розглянь малюнки.
	 Запиши слова — назви намальованих пред-
метів, які відповідають на питання хто?
	 Прочитай текст.
ВЕСНА
Настала весна. Прилетіли птахи. На 
березі шпаки.
	 Випиши речення, яке відповідає схемі.
    
```

**Grade 1, zaharijchuk** — Сторінка 75:
```
73
	 — Але ми все одно будемо дружи-
ти? Адже ми обидва їжаки.
	 — Авжеж. Будемо (за Юрієм  Яр-
мишем).
	 Прочитай заголовок казки. Що він тобі підка-
зав? Хто з ким познайомився? 
	 Що любив слухати Їжак, який жив на гірці? 
Що любив слухати Морський Їжак? Чому 
вони любили різні звуки? 
Повторюємо разом
Абетка. Звуки та букви
	 Звуки, які любили їжаки, є мовні чи немовні?
	 Як називаємо підкреслені слова? 
протилежні за значенням
подібні за значенням
	 Перепиши перше речення. Підкресли букви, 
```

**Grade 1, zaharijchuk** — Сторінка 78:
```
76
За мотивами казки Е. Мозера
Повторюємо разом
Приголосні звуки: 
тверді та глухі
	 Прочитай імена головних героїнь, чітко ви-
мовляючи перші звуки.
Зося, Сюзі.
	 Чи вони справжні подруги? Як одна з них до-
помогла іншій? Знайди та прочитай про це. 
	 Який із цих звуків вимовляємо дзвінко, з го-
лосом? А який — тільки із шумом? 
	 Перепиши виділене блакитним кольором ре-
чення. Підкресли букви, які позначають при-
голосні звуки. Вимов їх. 
— Так, але я 
сама не зможу.
— Дякую. Ти 
справжня моя 
```

**Grade 1, bolshakova** — Сторінка 24:
```
24
ЗВУКИ. ГОЛОСНІ І ПРИГОЛОСНІ
Ти вимовляєш різні звуки: голосні і приголосні. 
Голосні звуки утворюються за допомогою голосу.
Голосні почуєш в пісні,
І у темному у лісі, 
І коли дивуєшся,
І коли милуєшся.
Легко вимовляються, 
Весело співаються! 
Прочитай. Назви букви, які позначають голосні звуки.
ал – ам – ан 
ла – ма – на 
ул – ум – ун
ол – ом – он 
ло – мо – но 
лу – му – ну
 
Приголосні звуки утворюються 
за допомогою голосу і шуму.
Приголосні деренчать
І тихенько шелестять, 
Голосно свистя
```

**Grade 1, bolshakova** — Сторінка 79:
```
. . . . . . . . . . . . . . . . . . 44
Т т . . . . . . . . . . . . . . . . . . . . . . . . . . . 45
Тверді і пом’якшені  
приголосні звуки . . . . . . . . . . . . . . 45
Г г . . . . . . . . . . . . . . . . . . . . . . . . . . . 46
Г г . . . . . . . . . . . . . . . . . . . . . . . . . . . 47
Тверді і пом’якшені  
приголосні звуки . . . . . . . . . . . . . . 47
Ґ ґ . . . . . . . . . . . . . . . . . . . . . . . . . . . 48
Ґ ґ . . . . . . . . . . . . . . . . . . . . . . . . . . . 49
Е е  . . . . . .
```

**L1→L2 Transformation Rules:** The excerpts above are from Ukrainian school textbooks that teach Ukrainian to **native speakers (L1)**. Your learners are **English-speaking teens and adults (L2)**. When adapting:

1. **L1 assumes intuitive grammar** → L2 needs explicit rule statements in English
2. **L1 uses native-level vocabulary** → L2 uses level-appropriate vocabulary guided by textbook excerpts
3. **L1 dialogues assume cultural context** → L2 dialogues need setting/purpose explanation
4. **L1 exercises test metalinguistic knowledge** → L2 exercises test production/comprehension

**Cite your adaptations:** For each dialogue or exercise you adapt from the textbook excerpts, add an HTML comment:
```
<!-- adapted from: Заболотний Grade 5, вправа 221 -->
```
Even when no exact textbook exercise matches, ground your content in textbook pedagogy — use their progression patterns, example types, and exercise formats. Do NOT add fallback comments.



---

## 4. Create Activities (from YOUR content above)

After writing the content, create activities that practice the Ukrainian you just taught. This is why we do both in one pass — you know exactly which words, phrases, and gender pairings you used.

**Targets:**
- 8–15 activities
- Required types: watch-and-repeat, image-to-letter, classify, match-up, fill-in
- 20 vocabulary items

### Item Minimums (HARD FAIL if under)

| Type | Minimum |
|------|--------|
| quiz | ≥6 items |
| true-false | ≥6 items |
| fill-in | ≥6 items |
| match-up | ≥6 pairs |
| anagram | ≥6 items |
| unjumble | ≥6 items |
| group-sort | ≥8 items |
| watch-and-repeat | ≥1 items |
| classify | ≥1 items |
| image-to-letter | ≥5 items |

### Real Textbook Exercises (вправи) — Pedagogical Inspiration

These are real exercises from Ukrainian school textbooks (grade 1/2). Study their **pedagogical patterns** — how they build progressively, use familiar vocabulary, and test specific skills. Since your students are English-speaking adults, **translate exercise instructions to English** while keeping Ukrainian content words. Adapt the pedagogical approach (progressive difficulty, real-world context) but not the language of instruction.

**Grade 1, zaharijchuk** — Сторінка 73:
```
71
	
Відшукай предмети, у назвах яких є буква ї, 
звуки [йа], звук [дз].
Вийди, вийди, ... ,
На дідове ... ,
На бабине ... ,
На наше ... ,
На весняні ... ,
На маленькі ... .
полечко
зіллячко
 квіточки
сонечко
подвір’ячко
 діточки
	
Знайди «загублений» склад у словах — на-
звах намальованих предметів. 
	
Прочитай слова в рамках. Розмісти їх у по-
трібних місцях у закличці. Прочитай її. 
__ -мін-го	
фук-,	
фла-,	
фут-
__ -ре-ло	
дзе-,	
джи-,	
дже-
лі- __ -на	
-ши-,	
-щи-,	
-чи-
Pidruchnyk.com.ua
```

**Grade 1, zaharijchuk** — Сторінка 11:
```
9
Склад слова.  
Наголошені та ненаголошені склади
	 Що «зайве»? Поділи слова на склади. Визнач 
наголошений склад.
        
        
        
	 Який у тебе сьогодні настрій? Вибери.
```

**Grade 1, zaharijchuk** — Сторінка 30:
```
28
Вшниі, шаркептик, шмкруаа, 
шшпииан, аачкш.
	
«Збери» слова — назви намальованих пред-
метів. Поділи на склади слово, у якому дві 
букви ш (усно).
Бачу Ш, ш (ша). Чую [ш].
ш и н ш и
ш и ш к
к о м и ш
и
а
л
а
о
у
и
і
Ш
ша
шо
шу
ши
ші
а
о
у
и
і
аш
ош
уш
иш
іш
Ш
ша-                  
шо-                       шпа-                   
ши
шка
на
шу
м
міти
ше
лест
рех
 [  –  •–  |  –•|  –•] 
 [  –  •|  –  •– ] 
Ш ш
Pidruchnyk.com.ua
```

**Grade 1, zaharijchuk** — Сторінка 24:
```
22
	 Утвори слова — нáзви предметів.
Х
	
Що тобі відомо про персонажів казки «Ко-
тигорошко»?  Роз­кажи.
	
Прочитай склади. Знайди слова із цими 
складами.
	
Розділи речення на слова, прочитай при­
слів’я. У при­слі­в’ї є 4, 5 чи 6 слів? Вибери 
правильну відповідь.
	
Зимабезснігу — літобезхліба.
	
Які букви нагадують ці предмети?
хвилина
мухомор
горіхи
горох
хви-
-хо-
-рох
-хи
Pidruchnyk.com.ua
```

### Which Activity Types to Use

**ALLOWED:** quiz, true-false, fill-in, match-up, anagram, unjumble, group-sort, watch-and-repeat, classify, image-to-letter
**FORBIDDEN:** cloze, error-correction, mark-the-words, select, translate, essay-response, critical-analysis, comparative-study, authorial-intent

Choose types based on what the constraints allow:

| Constraint level | Use these | Avoid these |
|-----------------|-----------|-------------|
| Letters/syllables only (M1-M10) | quiz, match-up, group-sort, anagram, true-false | fill-in, unjumble, cloze, translate |
| Words + simple phrases | + fill-in, match-up with phrases | unjumble, cloze |
| Basic sentences allowed | + unjumble, fill-in with sentences, translate | cloze (needs 14+ blanks) |

### Language Rules (A1/A2)

- **Questions, instructions, explanations** → English (students can't read Ukrainian metalanguage)
- **Content being practiced** → Ukrainian (words, letters, phrases from the lesson)
- **Options** → Ukrainian when choosing Ukrainian words, English when choosing concepts
- Never use grammar terms like іменник, дієслово, відмінок

### Irregular Forms Warning (CRITICAL for activities)

Some Ukrainian verbs have **irregular imperative forms**. NEVER guess — use ONLY the forms from your content above. Common traps:
- взяти → **візьми/візьміть** (NOT ~~взяй/взяйте~~)
- стояти → **стій/стійте** (NOT ~~стояй/стояйте~~)
- сісти → **сядь/сядьте** (NOT ~~сісь/сісьте~~)
- їсти → **їж/їжте** (NOT ~~їсь/їсьте~~)
- **и** is RUSSIAN. The Ukrainian conjunction is **і** (or **й** after vowels, **та**).

If a verb's imperative isn't in your content, don't use it in activities.

### Consistency Rules (the whole point of single-pass)

1. **Same words**: Every Ukrainian word in activities must appear in your content above
2. **Correct agreement in answers**: Activity `answer` fields must have correct adj-noun gender agreement. If you wrote `великий стіл` in content, the correct answer in activities must also be `великий стіл` — NOT `велика стіл`
3. **Wrong forms are OK as distractors**: In `options` arrays, wrong gender/case forms are expected — they're the incorrect choices. Example: `options: ["нова", "новий", "нове", "нові"]` for a feminine noun — only `нова` is correct, the rest are intentional distractors
4. **Same forms**: If content uses `книга` (nominative), don't use `книги` (genitive) in the `answer` unless genitive also appears in the content

### Activity Schemas (EXACT field structures — any unlisted field = FAIL)

**quiz** — English questions, Ukrainian options:
```yaml
- type: quiz
  title: "Check Your Knowledge"
  instruction: Choose the correct answer.   # optional
  items:  # minItems: 6
    - question: "What does мама mean?"      # ≥5 words
      explanation: "Мама means mom."        # at QUESTION level, NOT inside options
      options:                              # exactly 4, exactly 1 correct
        - text: "mom"
          correct: true
        - text: "dad"
          correct: false
        - text: "sister"
          correct: false
        - text: "brother"
          correct: false
```

**anagram** — letter scramble (M1-M10 ONLY, not M11+):
```yaml
- type: anagram
  title: "Unscramble the Word"
  instruction: "Rearrange the letters."     # optional
  items:  # minItems: 8
    - scrambled: "А М А М"                  # SPACE-SEPARATED, same letters as answer
      answer: "МАМА"
```

**unjumble** — sentence word reorder (M11+ ONLY, not M1-M10):
```yaml
- type: unjumble
  title: "Put the Words in Order"
  items:  # minItems: 8
    - words: ["книга", "Це", "нова"]        # array of strings
      answer: "Це нова книга"               # single string
```
Do NOT use `sentence`, `jumbled`, or `scrambled` — only `words` + `answer`.

**match-up**:
```yaml
- type: match-up
  title: "Match the Pairs"
  pairs:  # minItems: 6, use "pairs:" NOT "items:"
    - left: "книга"
      right: "book"
```

**fill-in** — MUST include `options`:
```yaml
- type: fill-in
  title: "Complete the Sentence"
  items:  # minItems: 6
    - sentence: "Це ___ стіл."
      answer: "великий"
      options: ["великий", "велика", "велике", "великі"]  # exactly 4, answer must be in list
```

**group-sort**:
```yaml
- type: group-sort
  title: "Sort by Gender"
  groups:  # 2-4 groups
    - name: "Masculine"
      items: ["стіл", "брат", "дім"]
    - name: "Feminine"
      items: ["книга", "мама", "мова"]
```

**true-false**:
```yaml
- type: true-false
  title: "True or False?"
  items:  # minItems: 8
    - statement: "The letter Н makes the same sound as English H."
      correct: false
      explanation: "Н looks like H but sounds like N."
```

### Vocabulary YAML

- **Object with `items:` wrapper** (not bare list)
- Each entry: `lemma`, `translation`, `pos` (required); `gender`, `notes`, `usage`, `example` (optional)
- NO `ipa` field
- Include ALL words from `vocabulary_hints` in the plan

### YAML Formatting (HARD FAIL)

**Content** uses Ukrainian quotes «...». **YAML values** must NOT use «» — they break parsing with colons.

```yaml
❌ WRONG:  title: «Знайдіть пару: термін»
✅ RIGHT:  title: 'Знайдіть пару: термін'
```

Rules for YAML:
1. Never use `«»` — use plain text or single/double quotes
2. Quote any value containing `:` with single quotes
3. No IPA, no Latin transliteration in YAML values

---

## 5. Self-Audit Before Output

## Self-Audit (Run BEFORE Final Output)

After writing all content, you MUST run the audit and fix any issues — all within this session.

### Step 1: Write Content to Disk

Write your complete content to `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-ukrainian-alphabet.md` using write_file or bash:

```bash
cat > /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-ukrainian-alphabet.md << 'CONTENT_EOF'
... your content here ...
CONTENT_EOF
```

### Step 2: Run Audit

```bash
bash scripts/audit_module.sh /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-ukrainian-alphabet.md --skip-activities --no-rag-verify
```

This checks: word count, Russianisms, engagement callouts, euphony, structure, immersion %.

### Step 3: Parse Results

- If you see `AUDIT PASSED` — proceed to output.
- If you see `AUDIT FAILED` — read the violations, fix content in-place, and re-run the audit.

### Step 4: Fix Loop (max 2 iterations)

If the audit fails:
1. Read the specific gate failures and violation details from the audit output
2. Edit `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-ukrainian-alphabet.md` to fix each issue (add words if under target, remove Russianisms, add callout boxes, etc.)
3. Re-run: `bash scripts/audit_module.sh /Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/the-ukrainian-alphabet.md --skip-activities --no-rag-verify`
4. If still failing after 2 fix attempts, proceed to output anyway — the validate phase will handle remaining issues.

### Step 5: Report Self-Audit Result

After audit (pass or fail), include this block in your output:

```
===SELF_AUDIT_START===
status: PASS | FAIL
iterations: {number of audit runs}
final_word_count: {word count from last audit}
gates_passed: {list of passed gates}
gates_failed: {list of failed gates, or "none"}
fixes_applied: {brief description of what you fixed, or "none"}
===SELF_AUDIT_END===
```

**IMPORTANT**: Do NOT skip the audit. Do NOT fabricate audit results. Run the actual command and report real output.


### Content Checks
- [ ] Word count ≥ 1200?
- [ ] Every plan section has prose?
- [ ] 3+ callout boxes?
- [ ] All target vocabulary words used in content?
- [ ] No Russianisms, Russian characters, IPA?
- [ ] No bilingual ping-pong? (Scan for Ukrainian sentence → English translation in the same paragraph. If found, move the Ukrainian to a table, list, or dialogue.)
- [ ] **Dialogue quality**: Max 2-3 dialogues total. Every dialogue starts with `> **(Location)**`. No echo-drill patterns (speaker A commands → speaker B echoes the verb). If you find an echo drill, REWRITE it with a real situation and varied responses.
- [ ] **Textbook citations**: At least 1 `<!-- adapted from: ... -->` or `<!-- original: ... -->` comment per H2 section.

### Activity Checks
- [ ] 8–15 activities?
- [ ] Activities use only words from content above?
- [ ] Every Ukrainian word also appears in content?
- [ ] Adjective-noun pairings match content?
- [ ] Quiz: exactly 1 `correct: true`, `explanation` at question level?
- [ ] Anagram: scrambled letters = answer letters?
- [ ] Fill-in: `answer` appears in `options`?
- [ ] Match-up: uses `pairs:` not `items:`?
- [ ] No extra fields (schema is `additionalProperties: false`)?
- [ ] No `hint` fields in any activity items?

---

## 6. Output Format

> **DELIMITER ENFORCEMENT**: Content outside delimiters is automatically discarded.

Output FOUR blocks in this exact order:

**Block 1: Content**
```
===CONTENT_START===

<!-- SCOPE
Covers: {what this module teaches}
Not covered:
  - {related topic} → {slug}
-->

# {Title}

> **Why does this matter?**
>
> {2-3 sentences}

## {Section 1}
...

---

# Summary

{Summary + 3-4 self-check questions. Each question includes English translation.}

---

===CONTENT_END===
```

**Block 2: Word Counts**
```
===WORD_COUNTS===
Section "{name}": {count} words (minimum: {allocation})
...
Total: {total} words (target: 1200)
===WORD_COUNTS===
```

**Block 3: Activities (BARE LIST — no `activities:` wrapper)**
```
===ACTIVITIES_START===

- type: quiz
  title: "..."
  items:
    ...

- type: match-up
  title: "..."
  pairs:
    ...

===ACTIVITIES_END===
```

**Block 4: Vocabulary (object with `items:` wrapper)**
```
===VOCABULARY_START===

items:
  - lemma: "книга"
    translation: "book"
    pos: "noun"
    gender: "f"

===VOCABULARY_END===
```

**Block 5: Friction Report (MANDATORY)**
```
===FRICTION_START===
**Phase**: Full Build (Content + Activities + Vocabulary)
**Step**: {what you were doing when friction occurred, or "Complete build"}
**Friction Type**: NONE | YAML_SCHEMA_VIOLATION | WORD_BANK_LIMITATION | ...
**Raw Error**: {actual error or "None"}
**Self-Correction**: {what you changed, or "N/A"}
**Proposed Tooling Fix**: {if applicable, or "N/A"}
===FRICTION_END===
```
