# Module Build: Content + Activities + Vocabulary

## 1. Goal

> **You are Patient & Supportive Ukrainian Tutor, writing in the voice of Patient Supportive Tutor.**
>
> Build a complete beginner module for English-speaking teens and adults learning Ukrainian at the a1 level. Your job: **search Ukrainian school textbooks using RAG tools**, then **adapt** the pedagogy for L2 learners.
>
> **Output capacity: 65,000+ tokens.** Do NOT truncate.

**What L2 learners need** (that L1 textbooks assume):
1. Explicit grammar rules in English (L1 learners know intuitively)
2. Level-appropriate vocabulary only
3. Setting/purpose for dialogues (L1 assumes shared cultural context)

## 2. Scoring Dimensions

Your content will be scored on these 7 dimensions (see GEMINI.md for details):
1. **Experience Quality** — would the learner continue?
2. **Language Accuracy** — correct Ukrainian, no Russianisms
3. **Pedagogy** — clear progression, quick wins
4. **Activities** — variety, appropriate difficulty
5. **Beginner Safety** — warm tone, not overwhelming
6. **LLM Fingerprint** — natural voice, not robotic
7. **Linguistic Accuracy** — factual correctness

---

## 3. Context

### Input Files (read ALL before writing)

| File | What to extract |
|------|----------------|
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/prepositions-of-place-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/prepositions-of-place.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("Locative prepositions (в/у, на) Euphonic в/у alternation", grade=3-5)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 32
**Previous module:** The Genitive I: Absence

**Cumulative vocabulary (400 words):**
мама, тато, кіт, молоко, масло, ліс, місто, око, так, ні
сон, сом, ніс, мак, сік, стіл, тут, там, сало, кіно
яблуко, риба, село, Україна, їжак, юнак, край, день, син, моя
вухо, їжа, моє, яйце, юшка, каша, небо, сир, суп, хліб
зуб, дім, вовк, жук, шапка, гора, рука, бабуся, павук, ґанок
сіль, люди, вода, лук, люк, сестра, дерево, вулиця, автобус, бібліотека
університет, склад, переніс, голосний, приголосний, острів, сім'я, ґудзик, кава, чай
замок, писати, школа, добрий, далеко, наголос, інтонація, питання, відповідь, хата
книжка, дорога, кафе, він, вона, воно, книга, слово, мова, вікно
брат, ніч, час, море, сонце, земля, Добрий день, Добрий ранок, Добрий вечір, Привіт
До побачення, Па-па, Дякую, Будь ласка, Вибачте, Перепрошую, Так, Ні, Як справи?, Добре
Погано, Нормально, Чудово, Смачного, На здоров'я, Добраніч, це, я, ти, ми
ви, вони, хто, що, студент, студентка, українець, українка, вчитель, вчителька
ось, мене звати, особовий займенник, займенник, граматичний рід, рід, телефон, дуже приємно, давай на ти, удома
на роботі, підручник, паспорт, цей, ця, ці, той, та, те, ті
кімната, стілець, ліжко, лампа, шафа, двері, квартира, новий, старий, гарний
великий, малий, поганий, цікавий, синій, червоний, молодий, дорогий, дешевий, смачний
зелений, який, множина, білий, чорний, жовтий, бордо, беж, хакі, колір
сорочка, штани, сукня, плаття, куртка, светр, джинси, окуляри, носити, одягати
розмір, дієслово, друг, музей, машина, пісня, хлопець, зошит, ручка, словник
читати, говорити, знати, розуміти, питати, відповідати, перевіряти, де, рахунок, смачного
працювати, слухати, грати, чекати, думати, вивчати, відпочивати, лист, повідомлення, новини
музика, радіо, робити, бачити, любити, їсти, пити, ходити, просити, сидіти
стояти, платити, вчити, гість, природа, домашнє завдання, дивитися, сміятися, вмиватися, одягатися
називатися, вчитися, займатися, повертатися, знайомитися, зустрічатися, вітатися, митися, голитися, зупинятися
цікавитися, мити, називати, себе, часто, швидко, як, скільки, завжди, ніколи
цукор, подобатися, хотіти, піти, нудний, хороший, фільм, борщ, квіти, мені
тобі, хобі, інфінітив, мій, твій, твоя, твоє, його, її, наш
наша, ваш, ваша, їхній, свій, чий, чия, чиє, річ, сумка
будинок, озеро, такий, інший, кожний, сам, дівчина, година, хвилина, тиждень
місяць, рік, ранок, вечір, вчасно, понеділок, вівторок, середа, четвер, п'ятниця
субота, неділя, зараз, пізно, рано, січень, мати, чути, брати, купувати
гречка, пакет, шукати, знаходити, відкривати, проблема, голос, подруга, лікар, пес
колега, сусід, дитина, матуся, татусь, братик, сестричка, знайомий, в, на
через, про, за, готель, вокзал, країна, міст, парк, екскурсія, квиток
іти, їхати, дякувати, у, магазин, робота, банк, підлога, стіна, туалет
нога, маяти, куди, дуже, дужий, йти, людина, метро, багато, використовувати
аптека, простий, український, закінчення, відмінок, форма, опис, знахідний, правило, правити
жіночий, ом, йога, баба, го, приклад, прикласти, давати, тепло, до
чек, чека, купа, жаль, відсутність, гроші, сьогодні, українська, означати, водити

**Grammar already taught (104 topics):**
- Full alphabet overview (33 letters)
- Sound-letter correspondence (букви vs звуки)
- Vowel vs consonant classification
- Basic syllable blending and word reading
- Base vowel pronunciation (А О У Е И І)
- Iotated vowels dual function (Я Ю Є Ї)
- И vs І distinction
- Word stress basics (наголос)
- Vowel purity rule (no reduction)
- Sonorant consonants (Л М Н Р В)
- Voiced/voiceless consonant pairs
- No final devoicing rule
- Hard/soft consonant distinction
- Г vs Ґ distinction
- Soft sign palatalization (Ь)
- Apostrophe function and rules
- Affricates (Ц, Ч, Щ)
- Digraphs (ДЖ, ДЗ)
- Ф — rare native, common in borrowings
- Full alphabet mastery
- Syllable structure
- Open and closed syllables
- Word division rules
- Word stress
- Stress mobility
- Intonation patterns
- Three-gender system
- Declension families overview
- Gender prediction rules
- T-V distinction
- Imperative forms in politeness expressions
- Personal pronouns
- Zero copula construction
- Demonstrative це
- Demonstratives цей/ця/це/ці (this)
- Demonstratives той/та/те/ті (that)
- Gender agreement with demonstratives
- Adjective endings for gender (m/f/n)
- Hard stem adjectives (-ий/-а/-е/-і)
- Soft stem adjectives (-ій/-я/-є/-і)
- Color adjectives with agreement
- Clothing vocabulary
- Adjective + noun gender agreement with clothing items
- Noun plural formation
- Vowel alternation (і → о/е)
- Adjective plural agreement
- Cyrillic alphabet (all 33 letters)
- Noun gender (m/f/n)
- Adjective-noun agreement
- Plural formation
- First Conjugation pattern (-ати → -аю, -аєш...)
- Personal verb endings
- Imperfective aspect introduction
- Second Conjugation pattern (-ити → -у, -иш...)
- Consonant mutation patterns
- Irregular verbs
- Reflexive particle -ся/-сь
- Conjugation of reflexive verbs
- Transitive vs reflexive pairs
- Yes/no questions with чи
- Question words
- Negation with не
- Dative construction Мені подобається
- Люблю + Accusative
- Хочу + infinitive
- Possessive pronouns
- Gender agreement
- Variable vs invariable forms
- Reflexive possessive свій (свій vs його/її)
- Demonstrative pronouns
- Proximity distinction
- Cardinals 0-100
- Number agreement (1=nom, 2-4=nom.pl, 5+=gen.pl)
- Genitive plural with numbers
- Clock time expressions (Котра година?)
- Time prepositions (о, до, після)
- Days and months in context
- Present tense conjugation (I and II)
- Question words and Чи-questions
- Preference constructions (Dative, Accusative, Infinitive)
- Accusative case (inanimate)
- Feminine: -а → -у, -я → -ю
- Masculine/Neuter: no change
- Accusative for animate nouns
- Masculine animate: accusative = genitive
- Feminine animate: same as inanimate
- Accusative prepositions (в/у, на, за, через, про)
- Direction expressions with Accusative
- Preposition semantics and contrast
- Locative case endings
- Prepositions в/у and на
- Location expressions
- Locative case in context
- Directional expressions
- Prepositions of location
- Adjective declension in Accusative
- Adjective declension in Locative
- Gender-case agreement patterns
- Personal pronoun declension (Acc, Loc, Dat, Gen)
- Prefix н- after prepositions for 3rd person
- Pronoun case paradigm and form overlaps
- Genitive case for absence
- Genitive endings
- Немає + genitive

**Coming next (module after this):** Accusative case (inanimate and animate), Locative case (location), Genitive case (absence)
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 20 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- магазин (store) — в магазині; high frequency location noun
- школа (school) — у школі; euphonic у before ш-cluster
- вулиця (street) — на вулиці; surface preposition на
- стіл (table) — на столі; basic surface location
- кухня (kitchen) — на кухні; traditional на exception
- пошта (post office) — на пошті; institutional на usage
- біля (near) — біля + Gen; proximity preposition
- навпроти (opposite) — навпроти + Gen; orientation preposition
- знаходиться (is located) — formal location verb; Де знаходиться...?

**Recommended** (use in your content to reach the vocabulary target):
- поруч (nearby) — поруч з + Inst; preview chunk
- між (between) — між + Inst; preview chunk
- далеко (far) — далеко від + Gen; distance expression
- близько (near/close) — близько від + Gen; distance expression

These are your TARGET words — teach them all and use them heavily. For the rest of the text, use natural, level-appropriate Ukrainian.

**VOCAB-IN-CONTENT RULE:** All vocabulary words from vocabulary_hints MUST appear at least once in the module content. Orphaned vocabulary (listed but never used in content) is a validation failure.

### Immersion Target

TARGET: 30-55% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — MAXIMUM 2 sentences per concept. You must explain grammar primarily by demonstrating it. Show, don't tell.
- PARADIGM TABLES: Conjugation/declension tables with all cells Ukrainian. This is the highest-density immersion tool. Do not explain usage nuances in English prose — instead, create dual-column tables (Ukrainian Sentence | English Context/Translation) that map out the nuances. Move the teaching logic inside the tables.
- EXAMPLE LISTS: Ukrainian sentences in bulleted lists (each: Ukrainian — English gloss).
- DIALOGUES: Mini-dialogues in blockquotes with English gloss per line.
- PATTERN BOXES: Show transformations: `читати → читай → читайте`.
- INLINE: Ukrainian words/phrases bolded in English prose.
- IMMERSION BLOCKS: Every major H2 section MUST conclude with a substantial Ukrainian-only dialogue or narrative blockquote (>) of at least 80-150 words demonstrating the concepts in context. If translations are needed, place them in a separate table BELOW the blockquote.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences go in tables, bulleted lists, dialogues, or pattern boxes — never in flowing prose paragraphs. Vary your containers — never use the same type twice in a row.
Ukrainian sentences max 10 words.
NOTE: When the lexical sandbox has fewer than 20 lemmas, the immersion floor is lowered to prevent repetitive padding. Focus on quality immersion with the available vocabulary rather than forcing high percentages.

BEFORE/AFTER EXAMPLE — follow the AFTER pattern:

❌ BAD (too much English, ~10% immersion):
To form the imperative mood in Ukrainian, you take the infinitive form of the verb and remove the -ти ending. Then you add the appropriate suffix depending on whether you are speaking to one person informally or to multiple people formally. For the informal singular form, you simply use the stem. For the formal or plural form, you add -те to the informal form.

✅ GOOD (tables + dialogue + examples, ~45% immersion):
Drop **-ти** from the infinitive to form commands.

| Infinitive | ти-command | ви-command |
|---|---|---|
| читати | читай | читайте |
| писати | пиши | пишіть |

> — **Читай** текст! — Read the text!
> — **Пишіть** відповідь. — Write the answer.
> — **Слухайте** уважно! — Listen carefully!

Add **будь ласка** to soften any command.

- **Дайте, будь ласка, воду.** — Please give water.
- **Скажіть, будь ласка, де метро?** — Please tell me, where is the metro?

### Podcast Episodes
*Each episode has audio + transcript + vocabulary list -- recommend to students as supplementary listening.*

- **ULP S2 Ep57: Your schedule in Ukrainian + Accusative case with prepositions**
  URL: https://www.ukrainianlessons.com/episode57/
  Relevance: 0.4
  Topics: grammar, cases, accusative, prepositions, phrases

### Blog Articles & Guides
- **Talk Ukrainian: Ukrainian prepositions** (talkukrainian)
  URL: https://talkukrainian.com/prepositions/
  Relevance: 0.6
  Topics: prepositions, прийменник, grammar

- **Prepositions У and НА in Ukrainian** (ukrainianlessons.com)
  URL: https://www.ukrainianlessons.com/prepositions-u-na/
  Relevance: 0.4
  Topics: prepositions, grammar

- **Prepositions and Cases in Ukrainian** (ukrainianlessons.com)
  URL: https://www.ukrainianlessons.com/prepositions-cases/
  Relevance: 0.3
  Topics: prepositions, cases, grammar

- **Prepositions of Time in Ukrainian** (ukrainianlessons.com)
  URL: https://www.ukrainianlessons.com/prepositions-of-time-in-ukrainian/
  Relevance: 0.3
  Topics: prepositions, time, grammar


### Textbook References
- **Grade 4, Сторінка 83**
  біле поле
білі ліси, хустки, поля 
синій олівець 
синя кулька 
синє озеро
сині олівці, кульки, озёра
білому полю
(у) білих лісах, хустках, полях
синім олівцем
синьою кулькою
(у) синьому озері
синіх ол...

- **Grade 4, Сторінка 74**
  І У називному відмінку іменники вживаються без при- 
і йменників, у місцевому — тільки з прийменниками, 
1 
а в усіх інших відмінках можуть уживатися з приймен- 
« никами або без них. Наприклад: (біля...

- **Grade 4, Сторінка 72**
  72
174.		Розгляньте узагальнюючу таблицю відмінкових закінчень 
прикметників.
Н. в.
Р. в.
Д. в.
Зн. в. 
Ор. в.
М. в.
-і
-их
-им
-і, -их 
-ими
-их
-і, -ї
-іх
-ім
-і, -іх 
-іми
-іх
ч. р.
ж. р.
с. р.
-ий...

- **Grade 7, Сторінка 178**
  § 29  Синонімічні й антонімічні прийменники  
175
§ 29  Синонімічні й  антонімічні прийменники
Вправа 247 
1  Прочитайте речення 
Край/біля/обабіч дороги проклали велодоріжку.
Цей магазин розташований...

- **Grade 7, Сторінка 170**
  § 27  Прийменник як службова частина мови  
167
Прийменники за будовою
Прості
Складні
Складені
Непохідні
Похідні
під, з, над, 
через
пишемо разом 
або з дефісом:
задля, з­над, 
попід
пишемо 
окремо:
в...






---

## 4. Outline

Write **Prepositions of Place** for the a1 track.

**Targets:** 1200–1800 words | 3+ callout boxes | **8–15 activities total** (required types + additional types to reach minimum) | 20 vocab items

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## В/У + Місцевий (In + Locative)` (~300 words)
  - Location inside enclosed spaces: в магазині, у школі, в Україні. High-frequency collocations with в/у + Locative for buildings, cities, and countries.
  - Euphonic в/у rule per Pravopys §23: у between consonants and before в/ф/льв/зв/св clusters; в between vowels and at sentence start before vowels. Drill common learner errors: «У Львові» (not «В Львові» — у before льв-cluster).
  - Consonant alternations in Locative: г→з (нога → на нозі), к→ц (рука → у руці), х→с (вухо → у вусі). Review from a1-13 with expanded drills.
- `## На + Місцевий (On + Locative)` (~300 words)
  - Location on surfaces: на столі, на стіні, на підлозі. Physical contact meaning of на.
  - Location at events and institutions: на концерті, на роботі, на пошті, на уроці. The social/activity exception where на replaces в/у.
  - Contrast pairs: в кімнаті (inside a room) vs на кухні (in the kitchen — traditional usage). в театрі (inside the building) vs на виставі (at the performance).
- `## Біля/Поруч/Між (Near/Next to/Between)` (~250 words)
  - Біля + Genitive for proximity: біля школи, біля парку, біля зупинки. High-frequency pattern for giving directions.
  - Навпроти + Genitive for opposite position: навпроти банку, навпроти аптеки. Useful for city orientation tasks.
  - Preview of Instrumental prepositions: поруч з + Instrumental (next to), між + Instrumental (between). Introduced as formulaic chunks, not full case explanation.
- `## Де знаходиться...? (Where is...?)` (~200 words)
  - Asking location questions: Де знаходиться пошта? Де знаходиться найближча аптека? The verb знаходитися (to be located) as a formal alternative to бути.
  - Answering with full sentences: Пошта знаходиться на вулиці Хрещатик. Аптека знаходиться біля метро. Combining prepositions with correct case forms.
  - Cultural context: Using Kyiv landmarks as location reference points — Хрещатик, Майдан, Золоті Ворота.
- `## Практика (Practice)` (~150 words)
  - Location description drills: Describe where objects are in a room, where buildings are in a city. Multiple prepositions in connected speech.
  - Dialogues: asking and answering "Where is...?" in realistic scenarios — tourist asking for directions, describing your neighbourhood.
- `## Підсумок` (~150 words) — recap + 3-4 self-check questions

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| В/У + Місцевий (In + Locative) | 300+ |
| На + Місцевий (On + Locative) | 300+ |
| Біля/Поруч/Між (Near/Next to/Between) | 250+ |
| Де знаходиться...? (Where is...?) | 200+ |
| Практика (Practice) | 150+ |
| **Total** | **1200+ (aim for ~1440)** |

---

## 5. Guidelines

### Workflow
1. **Research first**: `search_text("Locative prepositions (в/у, на) Euphonic в/у alternation", grade=3-5)` — find how textbooks teach this
2. **Write content** following the outline and lesson arc below
3. **Verify as you write**: `verify_words` on any Ukrainian word you're unsure about
4. **Create activities** from your content
5. **Verify activities**: batch `verify_words` on all activity items

### Beginner Lesson Arc

1. **WELCOME** — warm greeting, set context
2. **PREVIEW** — "By the end of this module, you'll be able to..."
3. **PRESENT** — the main content sections
4. **PRACTICE** — examples, dialogues, reading practice
5. **CELEBRATE** — in the final `## Підсумок` section, tell learners what they can now do

### Emotional Safety (scored — Beginner Safety dimension)

Use direct address ("you", "your") at least 15 times throughout the module. Include encouragement ("Great job!", "You're doing well", "Don't worry"), quick wins (learner reads their first word early), and reassurance ("This is normal", "Take your time"). The learner should feel supported, not overwhelmed.

### Writing Style

English explains; Ukrainian is what they're learning. In each section:
1. **Explain** the concept in English (with Ukrainian vocabulary **bolded inline**). Short Ukrainian phrases are fine inline.
2. **Show** with **5-10 Ukrainian examples** per grammar point using bulleted lists, dialogues, and pattern boxes.
3. **Reinforce** with a callout box (`[!tip]`, `[!warning]`, `[!note]`, `[!culture]`, `[!challenge]`, `[!practice]`)

Tables contribute zero to immersion. Use **dialogues** and **bulleted examples** for Ukrainian content.

**MANDATORY for A2+:** Reading Practice blocks after each major section (5-8 Ukrainian sentences + English translation).

**Grammar terminology by level:**
- A1 M1-M10: English terms in prose, bilingual section headings with em-dash: `## Голосні — Vowels`
- A1 M11+: Introduce Ukrainian terms with gloss: **іменник** (noun)
- A2+: Ukrainian terms freely after first gloss

### Dialogue Quality

**No echo drills.** For M5+: every dialogue MUST start with `> **(Location / Місце)**`, have a real situation, 4-6 dialogues, 4-8 lines each.

**Alphabet modules (M1-M10):** Include 4-5 micro-dialogues using decodable words + sight words. Keep them short (2-4 lines each) and conversationally natural. Good patterns:
- Greeting: `— Привіт! — Привіт!`
- Identification: `— Це кіт? — Так, це кіт.`
- Location: `— Молоко тут? — Ні, молоко там.`
- Combined: `— Мама тут? — Так, мама тут. А тато там.`

Every line must make conversational sense. Do NOT pair unrelated speech acts (e.g., "Це мама?" → "Дякую!" makes no sense). Use `search_text` to find real dialogue patterns from Grade 1 textbooks (Заhaрійчук, Большакова) and adapt them to the available letter set.

**Cite textbook adaptations:** `<!-- adapted from: {author}, Grade {N} -->`

## Language Quality Rules (Beginner Tier)

### Russian Characters (HARD FAIL)

**ы, э, ё, ъ** must NEVER appear in Ukrainian text. These are Russian-only characters.

### Stress Mark Typography

Use lowercase letters with a combining acute accent (´) on the stressed vowel:
- Correct: ма́ма, анана́с, оса́, сосна́
- Wrong: мА́ма, ананА́с, осА́, соснА́ (do NOT capitalize the stressed vowel)

### IPA and Latin Transliteration (BANNED at ALL levels)

Never include IPA symbols (ɑ, ɛ, ʃ, etc.) or bracketed pronunciation guides like `[ma-ma]`, `[a-na-nas]`, `[ˈmɑmɑ]`. The ONLY pronunciation aid is the stress mark (´) on the vowel.

Latin transliterations are BANNED: never use kh, sh, ch, zh, ts, ya, yu, ye, shch.

```markdown
❌ WRONG: "мама [ˈmɑmɑ]" or "хліб (khlib)"
✅ RIGHT: "**ма́ма** (mom)" or "**Х**, like the «ch» in Scottish «loch»"
```

### Typography

- **ALWAYS** use Ukrainian angular quotes: «...» (never straight quotes "...")
- Base content vocabulary on the plan's `vocabulary_hints`. Function words (pronouns, conjunctions, particles, question words) are always allowed

### No Word Salad (HARD FAIL)

Every paragraph must have ONE clear point and logical flow between sentences. Do NOT string together unrelated observations.

### LLM Writing Patterns to Avoid

1. **Grandiose openers** — don't inflate every topic
2. **Stacked identical callouts** — same title max twice, vary types
3. **"In this lesson, we will..."** — ALWAYS banned (formulaic opener)


### Activity Rules

- Activity **answers** must use words from your content. **Distractors** may use other level-appropriate words.
- Follow schemas exactly — `additionalProperties: false` means any unlisted field = FAIL.
- Read `schemas/activities-a1.schema.json` for full field definitions.

**Allowed types:** quiz, true-false, fill-in, match-up, anagram, unjumble, group-sort, watch-and-repeat, classify, image-to-letter
**Forbidden types:** cloze, error-correction, mark-the-words, select, translate, essay-response, critical-analysis, comparative-study, authorial-intent
**Required types:** fill-in, quiz, match-up, true-false

| Module range | Use these | Avoid these |
|-------------|-----------|-------------|
| M1-M4 (alphabet) | quiz, match-up, group-sort, anagram, true-false, fill-in, watch-and-repeat, image-to-letter, classify | unjumble, cloze, translate |
| M5-M10 | + unjumble, fill-in with sentences | cloze, translate |
| M11+ | all types including translate | cloze (needs 14+ blanks) |

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

### Vocabulary YAML

Object with `items:` wrapper. Each entry: `lemma` (dictionary form), `translation`, `pos`. Optional: `gender`, `notes`, `usage`, `example`. No `ipa` field.

---

## 6. Hard Constraints

GRAMMAR CONSTRAINTS (A1.3 — Cases & Navigation):
Present tense and imperatives available. Cases being introduced.

ALLOWED: present tense, imperatives, infinitives, basic cases
BANNED: participles, passive voice, complex subordination

- **No Russianisms**: кушати→їсти, получати→отримувати, самий→найкращий
- **No Russian characters**: ы, э, ё, ъ — never
- **No colonial framing**: never define Ukrainian by comparing it to Russian. Don't say "unlike Russian..." or "not found in Russian." Present Ukrainian on its own terms
- **No IPA or Latin transliteration** — stress marks (´) only
- **Ukrainian quotes** in content: «...» | **YAML values**: plain text or single quotes (never «»)
- **Euphony** (у/в, і/й alternation): follow rules in the shared content rules section below — audit flags violations
- **YAML colon values**: quote with single quotes: `'text: with colon'`
- H2 titles must match the outline EXACTLY. You MAY add H3 sub-headings within H2 sections (e.g., for individual letters, grammar sub-topics)
- **MUST end with `## Підсумок`** with self-check questions

### Common Irregular Imperatives

If your module uses imperative verbs:
- взяти → **візьми/візьміть** (NOT ~~взяй~~)
- стояти → **стій/стійте** (NOT ~~стояй~~)
- сісти → **сядь/сядьте** (NOT ~~сісь~~)
- їсти → **їж/їжте** (NOT ~~їсь~~)

The Russian conjunction **"и"** (meaning "and") is forbidden. Use Ukrainian conjunctions **і**, **й** (after vowels), or **та**.

---

## 7. Output Format

> **Content outside delimiters is automatically discarded.**

Output FIVE blocks in this exact order (plus optional friction report):

**Block 1: Content** — `===CONTENT_START===` ... `===CONTENT_END===`
**Block 2: Word Counts** — `===WORD_COUNTS_START===` ... `===WORD_COUNTS_END===`
**Block 3: Activities** — `===ACTIVITIES_START===` ... `===ACTIVITIES_END===` (bare list, no wrapper)
**Block 4: Vocabulary** — `===VOCABULARY_START===` ... `===VOCABULARY_END===` (object with `items:`)
**Block 5: Builder Notes** — `===BUILDER_NOTES_START===` ... `===BUILDER_NOTES_END===`

### Builder Notes (MANDATORY)

```
===BUILDER_NOTES_START===
phase: CONTENT
status: SUCCESS | PARTIAL | BLOCKED
word_count: {actual}
deviations:
  - section: "{section}"
    reason: "{why}"
frictions:
  - type: TEMPLATE_CONSTRAINT | SCHEMA_MISMATCH | PLAN_GAP | RAG_FAILURE
    description: "{what went wrong}"
    proposed_fix: "{fix}"
research_gaps:
  - "{what you couldn't find}"
unverified_terms:
  - "{words you couldn't verify}"
review_focus:
  - "{what reviewer should check}"
rag_tools_used:
  - "{tool}: {query} → {result}"
===BUILDER_NOTES_END===
```

### Friction Report (OPTIONAL — only if you hit pipeline/schema issues)

```
===FRICTION_START===
**Phase**: Full Build
**Friction Type**: YAML_SCHEMA_VIOLATION | PLAN_GAP | CONTRADICTION
**Problem**: {what went wrong}
**Proposed Fix**: {how to fix the template/pipeline}
===FRICTION_END===
```
