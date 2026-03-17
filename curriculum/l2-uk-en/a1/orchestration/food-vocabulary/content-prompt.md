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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/food-vocabulary-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/food-vocabulary.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("Food noun gender Я не їм construction", grade=3-5)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 38
**Previous module:** My Daily Routine

**Cumulative vocabulary (436 words):**
мама, тато, кіт, молоко, масло, ліс, місто, око, так, ні
сон, сом, ніс, мак, сік, стіл, тут, там, сало, кіно
яблуко, риба, село, Україна, їжак, юнак, край, день, син, моя
вухо, їжа, моє, яйце, юшка, каша, небо, сир, суп, хліб
зуб, дім, вовк, жук, шапка, гора, рука, бабуся, павук, ґанок
сіль, люди, вода, лук, люк, Львів, м'ясо, п'ять, сім'я, цукор
час, що, джерело, дзвін, осінь, м'яч, щастя, бджола, дзеркало, черепаха
цибуля, хлопець, вчителька, факт, фото, чай, кінь, сестра, дерево, вулиця
автобус, бібліотека, університет, склад, переніс, голосний, приголосний, острів, ґудзик, кава
замок, писати, школа, добрий, далеко, наголос, інтонація, питання, відповідь, хата
книжка, дорога, кафе, він, вона, воно, книга, слово, мова, вікно
брат, ніч, море, сонце, земля, Добрий день, Добрий ранок, Добрий вечір, Привіт, До побачення
Па-па, Дякую, Будь ласка, Вибачте, Перепрошую, Так, Ні, Як справи?, Добре, Погано
Нормально, Чудово, Смачного, На здоров'я, Добраніч, це, я, ти, ми, ви
вони, хто, студент, студентка, українець, українка, вчитель, ось, мене звати, особовий займенник
займенник, граматичний рід, рід, телефон, дуже приємно, давай на ти, удома, на роботі, підручник, паспорт
цей, ця, ці, той, та, те, ті, кімната, стілець, ліжко
лампа, шафа, двері, квартира, новий, старий, гарний, великий, малий, поганий
цікавий, синій, червоний, молодий, дорогий, дешевий, смачний, зелений, який, множина
білий, чорний, жовтий, бордо, беж, хакі, колір, сорочка, штани, сукня
плаття, куртка, светр, джинси, окуляри, носити, одягати, розмір, дієслово, друг
музей, машина, пісня, зошит, ручка, словник, читати, говорити, знати, розуміти
питати, відповідати, перевіряти, де, рахунок, смачного, працювати, слухати, грати, чекати
думати, вивчати, відпочивати, лист, повідомлення, новини, музика, радіо, робити, бачити
любити, їсти, пити, ходити, просити, сидіти, стояти, платити, вчити, гість
природа, домашнє завдання, дивитися, сміятися, вмиватися, одягатися, називатися, вчитися, займатися, повертатися
знайомитися, зустрічатися, вітатися, митися, голитися, зупинятися, цікавитися, мити, називати, себе
часто, швидко, як, скільки, завжди, ніколи, подобатися, хотіти, піти, нудний
хороший, фільм, борщ, квіти, мені, тобі, хобі, інфінітив, мій, твій
твоя, твоє, його, її, наш, наша, ваш, ваша, їхній, свій
чий, чия, чиє, річ, сумка, будинок, озеро, такий, інший, кожний
сам, дівчина, година, хвилина, тиждень, місяць, рік, ранок, вечір, вчасно
понеділок, вівторок, середа, четвер, п'ятниця, субота, неділя, зараз, пізно, рано
січень, мати, чути, брати, купувати, гречка, пакет, шукати, знаходити, відкривати
проблема, голос, подруга, лікар, пес, колега, сусід, дитина, матуся, татусь
братик, сестричка, знайомий, в, на, через, про, за, готель, вокзал
країна, міст, парк, екскурсія, квиток, іти, їхати, дякувати, у, магазин
робота, банк, підлога, стіна, туалет, нога, маяти, куди, дуже, дужий
йти, людина, метро, багато, використовувати, аптека, простий, український, жаль, відсутність
гроші, сьогодні, українська, означати, форма, водити, закінчення, відмінок, опис, знахідний
правило, правити, жіночий, ом, веліти, вести, йога, зараза, кий, краса
красити, нове, до, місцевий, звідки, рух, додому, вчора, бути, минулий
раніше, спати, чоловічий, середній, завтра, буду, наступний, план, збиратися, скоро
потім, післязавтра, вранці, вдень, ввечері, майбутнє

**Grammar already taught (125 topics):**
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
- Vocative case (кличний відмінок)
- Nominative as base form (називний відмінок)
- Case system introduction (7 cases overview)
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
- Genitive case for absence
- Genitive endings
- Немає + genitive
- Locative prepositions (в/у, на)
- Euphonic в/у alternation
- Біля/навпроти + Genitive
- Adjective declension in Accusative
- Adjective declension in Locative
- Gender-case agreement patterns
- Accusative case (inanimate and animate)
- Locative case (location)
- Genitive case (absence)
- Prepositions with Accusative and Locative
- Adjective and pronoun declension in oblique cases
- Direction prepositions + Accusative
- До + Genitive
- З/від + Genitive
- Three-question paradigm (Де/Куди/Звідки)
- Past tense formation with L-participle
- Gender agreement in past tense
- Time expressions for past events
- Compound future (буду + infinitive)
- Буду conjugation for all persons
- Future time expressions
- Reflexive verbs (-ся/-сь) in context
- Sequence adverbs (спочатку, потім, нарешті)
- Daily routine expressions

**Coming next (module after this):** Скільки коштує construction, Genitive with quantities, Shopping imperative phrases (Дайте, будь ласка)
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 20 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- хліб (bread) — свіжий хліб; sacred symbol, хліб-сіль tradition
- борщ (borscht) — смачний борщ; national dish, masculine gender
- м'ясо (meat) — neuter gender; Я не їм м'ясо (vegetarian phrase)
- овочі (vegetables) — plural noun; food category
- фрукти (fruits) — plural noun; food category
- вода (water) — холодна вода, пляшка води; high frequency
- кава (coffee) — кава з молоком; feminine gender
- чай (tea) — чай з лимоном; masculine gender
- молоко (milk) — neuter gender; кава з молоком
- сік (juice) — апельсиновий сік; masculine gender
- суп (soup) — їсти суп (eat, not drink); masculine gender

**Recommended** (use in your content to reach the vocabulary target):
- паляниця (palianytsia) — cultural shibboleth; round wheat bread
- каша (porridge) — гаряча каша; feminine gender, traditional breakfast
- компот (compote) — traditional Ukrainian drink; masculine gender
- риба (fish) — feminine gender; food category
- сир (cheese) — masculine gender; not to confuse with Russian сыр

These are your TARGET words — teach them all and use them heavily. For the rest of the text, use natural, level-appropriate Ukrainian.

**VOCAB-IN-CONTENT RULE:** All vocabulary words from vocabulary_hints MUST appear at least once in the module content. Orphaned vocabulary (listed but never used in content) is a validation failure.

### Immersion Target

TARGET: 20-35% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — brief and clear. Show, don't tell.
- PARADIGM TABLES: Conjugation/declension tables with all cells Ukrainian.
- EXAMPLE LISTS: Ukrainian sentences in bulleted lists (each: Ukrainian — English gloss).
- DIALOGUES: Mini-dialogues in blockquotes with English gloss per line.
- PATTERN BOXES: Show transformations: `читати → читай → читайте`.
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences go in tables, bulleted lists, dialogues, or pattern boxes.
Ukrainian sentences max 10 words. Mix container types.

### Podcast Episodes
*Each episode has audio + transcript + vocabulary list -- recommend to students as supplementary listening.*

- **ULP S1 Ep12: Ordering food in Ukrainian**
  URL: https://www.ukrainianlessons.com/episode12/
  Relevance: 0.5
  Topics: vocabulary, food

- **ULP S1 Ep13: More about food in Ukrainian**
  URL: https://www.ukrainianlessons.com/episode13/
  Relevance: 0.5
  Topics: vocabulary, food

- **ULP S2 Ep47: Food festivals + Genitive case**
  URL: https://www.ukrainianlessons.com/episode47/
  Relevance: 0.5
  Topics: grammar, cases, genitive, vocabulary, food

- **ULP S3 Ep93: At the food fair in Ukraine + Diminutive words in Ukrainian**
  URL: https://www.ukrainianlessons.com/episode93/
  Relevance: 0.5
  Topics: grammar, verbs, conjugation, vocabulary, food

- **FMU Ep16: How to ORDER at the restaurant in Ukrainian**
  URL: https://www.ukrainianlessons.com/fmu16/
  Relevance: 0.5
  Topics: grammar, cases, accusative, vocabulary, food


### Textbook References
- **Grade 1, Сторінка 60**
  58
Іди, іди, дощику,
Зварю тобі борщику,
Залізу на дуба,
Прикличу голуба.
А голуб загуде,
Дрібний дощик піде! (нар. тв.).
	
Вибери продукти для борщу.
	
Назви овочі, з яких варять борщ. Ти любиш 
їст...

- **Grade 1, Сторінка 12**
  12
Прочитай. Знайди слова, у яких три склади.
	
хліб	
булка	
болото	
бу-­тер-­брод
	
краб	
білка	
борода	
бу-­тер-­бро­-дик 
	 батон	
будка	
собака	
бу-­тер-­бро-д­ний

Послідовність дій
Я готую буте...

- **Grade 1, Сторінка 30**
  30
Знайди слово до схеми. 
	
їжа	
ї-жа-чи-ха	
ї-хав	
Ки-їв
	 їжак	
ї-жа-че-ня	
по-ї-хав	
У-кра-ї-на
	 їжаки	 си-ро-їж-ка	
по-їзд	
у-кра-їн-ці

	 Один — багато
Які слова називають багато предметів?
	 ...

- **Grade 1, Сторінка 18**
  16
Й й
Бачу Й, й (йот). Чую  [й].
а й в а
 [ •  =   |  –• ]
а й с т р и
* а й в о р о
а
о
и
і
Й
га
ми
рі
Й
н о к
лій- 
	
ліній-
	
май- 
чай- 
	
гай- 
	
чай- 
мий	
лий 	
чай	
грай
вимий	
долий	
чайник	...

- **Grade 2, Сторінка 40**
  40
• Склади речення зі словами з протилежним значенням.
Зразок. Компот рідкий, а кисіль густий.
Морозиво ..., а чай ... . Сіль солона, а цукор ... .
Сік жовтий, а вода ... . Тістечко маленьке, а пиріг...






---

## 4. Outline

Write **Food and Drink** for the a1 track.

**Targets:** 1200–1800 words | 3+ callout boxes | **8–15 activities total** (required types + additional types to reach minimum) | 20 vocab items

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Їжа (Food)` (~275 words)
  - Basic food categories: хліб, м'ясо, риба, овочі, фрукти, каша, суп, борщ. Organized by food group for memorization.
  - Gender of food nouns: masculine (хліб, суп, борщ, сир), feminine (каша, риба, картопля), neuter (м'ясо, яблуко, молоко). Gender awareness for adjective agreement.
  - Collocations with adjectives: свіжий хліб, гаряча каша, смачний борщ, домашній суп. Building natural-sounding food descriptions.
- `## Напої (Drinks)` (~250 words)
  - Common drinks vocabulary: вода, чай, кава, сік, молоко, компот. Gender and typical modifiers: гаряча кава, холодна вода, апельсиновий сік.
  - Ordering pattern: Я хочу каву (Accusative). Будь ласка, чай з молоком. Building on Accusative knowledge from earlier modules.
  - Cultural note: Ukrainian tea culture (чай з медом, чай з лимоном) vs coffee culture (кава по-львівськи). Regional preferences across Ukraine.
- `## Паляниця (The Shibboleth Bread)` (~175 words)
  - Cultural sidebar: Паляниця — the round wheat bread that became a linguistic shibboleth during 2022. The specific pronunciation of пал-я-ни-ця is difficult for Russian speakers to reproduce.
  - Ukrainian bread traditions: хліб as sacred (never thrown away), the 'хліб-сіль' (bread and salt) hospitality greeting. Connection to the proverb «Хліб — усьому голова».
- `## Мені подобається / Я не їм (Preferences)` (~250 words)
  - Expressing food preferences: Мені подобається борщ (I like borscht). Я люблю каву з молоком (I love coffee with milk). Review of подобатися + Dative construction.
  - Expressing dislikes and restrictions: Я не їм м'ясо (I don't eat meat — vegetarian). Я не п'ю каву (I don't drink coffee). Negation with food verbs.
  - Allergies and dietary needs: У мене алергія на горіхи (I have an allergy to nuts). Я не можу їсти глютен. Practical survival phrases for dietary restrictions.
- `## Практика (Practice)` (~250 words)
  - Food vocabulary drills: Categorization (їжа vs напої), gender sorting, adjective matching. Building automatic recall of food terms.
  - Menu reading preview: Simple Ukrainian menu items. Recognizing food words in authentic format with prices.
  - Preference dialogues: Що ти любиш їсти? Яка твоя улюблена їжа? Conversational practice expressing food tastes.
- `## Підсумок` (~150 words) — recap + 3-4 self-check questions

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Їжа (Food) | 275+ |
| Напої (Drinks) | 250+ |
| Паляниця (The Shibboleth Bread) | 175+ |
| Мені подобається / Я не їм (Preferences) | 250+ |
| Практика (Practice) | 250+ |
| **Total** | **1200+ (aim for ~1440)** |

---

## 5. Guidelines

### Workflow
1. **Research first**: `search_text("Food noun gender Я не їм construction", grade=3-5)` — find how textbooks teach this
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
**Required types:** match-up, quiz, fill-in, group-sort

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

GRAMMAR CONSTRAINTS (A1.4 — Tenses & Daily Life):
Past tense and future tense introduced. All present tense available.
Imperatives available.

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
