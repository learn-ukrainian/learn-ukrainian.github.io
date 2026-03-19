**Curriculum context:** This is Module 45 of the A1 track (Ukrainian for English speakers). Title: "Can and Know How" — Ability and Permission. Phase: A1.5 [Modals, Commands & Life]. Previous module: Checkpoint Daily Life. Next module: Must And Want.

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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/can-and-know-how-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/can-and-know-how.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("Могти conjugation (irregular stem) Вміти conjugation", grade=3-5)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 44
**Previous module:** Checkpoint: Daily Life

**Cumulative vocabulary (444 words):**
мама, тато, кіт, молоко, масло, ліс, місто, око, так, ні
сон, сом, ніс, мак, сік, стіл, тут, там, сало, кіно
яблуко, риба, село, Україна, їжак, юнак, край, день, син, мій
вухо, їжа, яйце, юшка, каша, небо, сир, Європа, хліб, зуб
дім, вовк, жук, шапка, гора, рука, бабуся, павук, ґанок, кінь
люди, суп, вода, дим, люк, сіль, Львів, м'ясо, п'ять, сім'я
цукор, час, що, джерело, дзвін, осінь, м'яч, щастя, факт, бджола
дзеркало, черепаха, чай, фото, склад, голосний, приголосний, перенос, сестра, дерево
вулиця, автобус, бібліотека, університет, буква, звук, слово, книга, замок, добрий
школа, мука, хата, кава, книжка, дорога, далеко, наголос, інтонація, питання
відповідь, кафе, голос, брат, вікно, море, ніч, земля, серце, сонце
собака, ім'я, артефакт, зона, укриття, привіт, ранок, вечір, побачення, дякувати
ласка, вибачити, перепрошувати, приємно, пан, пані, ти, ви, дуже, щиро
бувати, здрастуйте, справа, це, я, він, вона, воно, ми, вони
хто, студент, студентка, вчитель, вчителька, українець, українка, ось, звати, цей
ця, ці, той, та, те, ті, телефон, кімната, стілець, ліжко
лампа, шафа, двері, квартира, ніж, ложка, блюдо, диван, крісло, річ
новий, старий, гарний, великий, малий, поганий, цікавий, синій, червоний, молодий
дорогий, дешевий, смачний, зелений, який, будинок, білий, чорний, жовтий, сорочка
штани, сукня, куртка, светр, плаття, джинси, окуляри, одяг, вишиванка, калина
дитина, людина, гроші, ножиці, маленький, де, торт, читати, писати, знати
працювати, слухати, питати, грати, чекати, думати, розуміти, вивчати, відпочивати, гуляти
відповідати, журнал, лист, радіо, повідомлення, новини, текст, говорити, робити, бачити
любити, їсти, пити, ходити, просити, сидіти, стояти, платити, вчити, дивитися
природа, сміятися, вмиватися, одягатися, називатися, вчитися, займатися, повертатися, голитися, зупинятися
знайомитися, цікавитися, подобатися, митися, зустрічатися, вітатися, цілуватися, мити, одягати, називати
розминатися, розслаблятися, чи, коли, куди, звідки, чому, як, скільки, не
завжди, часто, іноді, ніколи, але, і, а, подо́батися, люби́ти, хоті́ти
ка́ва, му́зика, чита́ти, ї́сти, піти́, ціка́вий, нудни́й, смачни́й, улю́блений, немає
без, проблема, квиток, ключ, газ, від, на жаль, вогонь, будь ласка, є
магазин, кухня, пошта, біля, навпроти, знаходитися, поруч, між, близько, парк
аптека, банк, зупинка, метро, красивий, український, важливий, популярний, фільм, ресторан
церква, через, за, про, робота, центр, іти, їхати, до, з
лікар, Київ, виходити, аеропорт, вокзал, вчора, бути, минулий, раніше, тиждень
місяць, спати, йти, варити, готувати, купувати, додому, завтра, наступний, план
хотіти, збиратися, скоро, потім, рік, сподіватися, мріяти, планувати, пізніше, післязавтра
майбутнє, прокидатися, снідати, обідати, вечеряти, лягати, зазвичай, спочатку, нарешті, щодня
перерва, борщ, овочі, фрукти, паляниця, компот, картопля, напій, коштувати, купити
гривня, кілограм, літр, пачка, пляшка, штука, ринок, мило, шампунь, зубна паста
туалетний папір, рушник, решта, картка, можна, меню, рахунок, офіціант, замовляти, тістечко
готівка, чайові, принести, кав'ярня, замовлення, лимон, бариста, оплата, добре, швидко
погано, повільно, рідко, голосно, тихо, сьогодні, легко, важко, гарно, смачно
трохи, майже, зовсім, погода, дощ, сніг, вітер, хмара, тепло, холодно
спекотно, прохолодно, весна, літо, зима, озеро, річка, прогноз, парасолька, температура
обід, вечеря, хмарно, сонячно

**Grammar already taught (143 topics):**
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
- Food noun gender
- Я не їм construction
- Food collocations with adjectives
- Скільки коштує construction
- Genitive with quantities
- Shopping imperative phrases (Дайте, будь ласка)
- Integration of Accusative, Genitive, Locative
- Polite imperatives (принесіть, візьміть)
- Future tense preview (візьму)
- Adverbs of manner (adjective stem + -о)
- Adverbs of frequency
- Adverb placement in sentences
- Impersonal weather expressions
- Seasons with prepositions
- Temperature and weather adjectives
- Past tense (-в/-ла/-ло/-ли)
- Future tense (буду + infinitive)
- Weather expressions (impersonal constructions)

**Coming next (module after this):** Треба/потрібно impersonal construction, Повинен agreement (m/f/n/pl), Хотіти conjugation (irregular stem)
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 20 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- могти (can/be able to) — можу, можеш, може; circumstantial ability
- вміти (know how to) — вмію, вмієш, вміє; learned skill
- можна (it is allowed) — impersonal; permission construction
- плавати (to swim) — classic вміти example; Я вмію плавати
- готувати (to cook) — Я вмію готувати; skill vocabulary
- фотографувати (to photograph) — Тут можна фотографувати?; permission context
- курити (to smoke) — Тут не можна курити; prohibition sign
- водити (to drive) — водити машину; Я вмію водити; skill vocabulary

**Recommended** (use in your content to reach the vocabulary target):
- кататися (to ride/skate) — кататися на велосипеді; skill context
- малювати (to draw) — Я вмію малювати; creative skill
- співати (to sing) — Я вмію співати; talent context
- грати (to play) — грати на гітарі; skill with instrument

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

### Textbook References
- **Grade 3, Сторінка 116**
  116
Досліди, чи всі іменни-
ки можуть мати фор-
му однини і множини.
Я — дослідник
Я — дослідниця
Спостерігаю за іменниками, які вживаються тільки  
в однині або тільки у множині
6   Прочитай слова і...

- **Grade 10, Сторінка 30**
  Проте вона може визначатись 
і  мовною традицією (наприклад: завдати горя, шкоди, але не завдати радості, 
щастя; відкрити портфель, але не відчинити портфель). Несподіване сполучення слів, які не з’є...

- **Grade 5, Сторінка 103**
  До ре­чі, ри­му­ван­ня мо­же від­бу­ва­ти­ся і в ін­ший спо­сіб: нап­рик­лад, 
пер­ший ря­док ри­му­єть­ся з тре­тім, а дру­гий — із чет­вер­тим, як у 
та­ко­му урив­ку. Розвиваємо компетентності
Теор...

- **Grade 5, Сторінка 175**
  Порівняйте: 
Я, на жаль, запізнився і Я запізнився. Речення, що містять вставні слова, звертання або однорідні члени, на-
зиваємо ускладненими....

- **Grade 6, Сторінка 40**
  40
1.	Прочитайте слова в колонках і виконайте завдання.
палата
обхід
щеплення
щогла
палуба
вітрило
апеляція
адвокат
позов
А.	 За яким принципом згруповано слова?
Б.	 Люди яких професій використовують ...






---

## 4. Outline

Write **Can and Know How** for the a1 track. Target: 1200–1800 words.

### CRITICAL: EXACT H2 HEADERS (copy-paste, do not alter)

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Могти (Can/Be able to)` (~300 words)
  - Full conjugation: можу, можеш, може, можемо, можете, можуть. Irregular stem change мог- → мож-. High-frequency verb (Top 50).
  - Physical and circumstantial ability: Я можу прийти завтра (I can come tomorrow). Я не можу зараз (I cannot right now). Expressing temporary capacity.
  - Request pattern: Можу я...? (May I...?). Polite alternative to Можна. Можу я запитати? Можу я подивитися?
- `## Вміти (Know how to)` (~250 words)
  - Conjugation: вмію, вмієш, вміє, вміємо, вмієте, вміють. Regular -іти verb pattern with -ію ending in 1st person singular.
  - Learned skills: Я вмію плавати (I know how to swim). Я вмію готувати (I know how to cook). Я вмію водити машину (I know how to drive).
  - Key contrast: можу (circumstantial — can right now) vs вмію (acquired skill — learned how to). Я можу плавати (the pool is open) vs Я вмію плавати (I learned to swim).
- `## Можна / Не можна (It is allowed / Not allowed)` (~250 words)
  - Impersonal permission construction: Тут можна фотографувати? (Is it allowed to photograph here?). Тут не можна курити (Smoking is not allowed here).
  - Можна + infinitive for polite requests: Можна увійти? (May I enter?). Можна подивитися? (May I look?). More formal than Можу я...?
  - Common signs and rules: Не можна паркуватися (No parking). Тут можна їсти (Eating is allowed here). Reading prohibition signs as practical skill.
- `## Не можу vs Не вмію vs Не можна (Contrasting Negations)` (~200 words)
  - Three-way contrast: Не можу = I am unable (right now, circumstance). Не вмію = I never learned (permanent gap). Не можна = It is not allowed (external rule).
  - Contextual examples: Я не можу прийти сьогодні (busy today). Я не вмію кататися на ковзанах (never learned). Тут не можна голосно розмовляти (library rule).
  - Learner error prevention: Mixing можу and вмію is the most common mistake. Drill: "Can you swim?" — if asking about skill → Ти вмієш? If asking about now → Ти можеш?
- `## Практика (Practice)` (~200 words)
  - Situation-based modal choice drills: Given a scenario, select the correct modal (могти/вміти/можна). Context determines the right verb.
  - Permission dialogues: Asking and granting/denying permission in school, museum, restaurant, workplace contexts. Building communicative competence.
- `## Підсумок` (~150 words) — recap + 3-4 self-check questions

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Могти (Can/Be able to) | 300+ |
| Вміти (Know how to) | 250+ |
| Можна / Не можна (It is allowed / Not allowed) | 250+ |
| Не можу vs Не вмію vs Не можна (Contrasting Negations) | 200+ |
| Практика (Practice) | 200+ |
| **Total** | **1200+ (aim for ~1440)** |

---

## 5. Rules (read ALL before writing)

### RULE 1: GRAMMAR — see Section 6

Section 6 (Hard Constraints) defines exactly what grammar structures you may use for this module. Follow those constraints — they vary by module number.

### RULE 2: VOCABULARY

Prioritize these Ukrainian words (from the plan). You may also use words from the cumulative vocabulary and common Ukrainian words, but these are your core teaching targets:

**Allowed Ukrainian words:** могти, вміти, можна, плавати, готувати, фотографувати, курити, водити, кататися, малювати, співати, грати

### RULE 3: VARIATION

Vary your formatting across sections. Do NOT start 3+ sections the same way. Mix: bulleted lists, dialogues, comparison patterns, callout boxes, practice exercises.

### RULE 4: STRESS MARKS

Write Ukrainian without stress marks — the pipeline adds them after. Exception: if the plan uses capitalized stress (молокО, далекО) to indicate stress position, you may use that notation in teaching examples.

### RULE 5: ENGLISH PROSE STYLE

You are a warm tutor. Use "you/your" often. Include encouragement. Keep it conversational.

Cite textbook adaptations: `<!-- adapted from: {author}, Grade {N} -->`

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

- Activity **answers** must use words from your content. **Distractors** must be VESUM-verified Ukrainian words — call `verify_words` before including any distractor. Never use made-up or unverified words.
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

SEQUENCE CONSTRAINTS (A1.5 — Modals, Commands & Life):
All tenses available. Imperative mood is TAUGHT in this phase (M47).
Imperative forms are ALLOWED after M47 introduces them.

For M47 itself: Use imperative forms freely — читай/читайте, пиши/пишіть, скажи/скажіть, дай/дайте, іди/ідіть.
Both imperfective AND perfective verbs allowed for imperatives.

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


FRICTION CONSTRAINTS (from past build reviews — DO NOT repeat these errors):
- [GLOBAL] сес-тра is a VALID word division per Правопис 2019 §49. Do NOT mark it as an error. Phonetic syllabification (се-стра) and typographic word division (сес-тра) follow different rules — both are correct in their respective contexts.
- [GLOBAL] Ukrainian textbooks teach a hands-on-EARS test for voicing (закрий долонями вуха), NOT a hand-on-throat test. The hand-on-throat test is a valid phonetics technique but must NOT be attributed to Ukrainian textbooks. Source: Кравцова 2019, Grade 2, p.39.
- [GLOBAL] Do NOT invent Ukrainian words for minimal pairs. "Сір" is NOT a word meaning "grey" — the correct form is "сірий". Use verified minimal pairs only: кит/кіт, бити/біти, лис/ліс.
- [GLOBAL] NEVER frame Ukrainian as "lacking" or "missing" letters that Russian has. Ukrainian has its own 33-letter alphabet — it is complete. Do NOT write "Ukrainian lacks Ъ, Ы, Э" or "Ukrainian doesn't have these Russian letters." Instead, highlight what Ukrainian HAS: Ґ, Є, Ї, І are unique to Ukrainian. Present Ukrainian on its own terms.
