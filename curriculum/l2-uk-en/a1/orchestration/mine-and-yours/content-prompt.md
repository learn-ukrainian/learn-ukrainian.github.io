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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/mine-and-yours-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/mine-and-yours.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("Possessive pronouns Gender agreement", grade=3-5)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 19
**Previous module:** Likes and Preferences

**Cumulative vocabulary (286 words):**
мама, тато, кіт, молоко, масло, ліс, місто, око, так, ні
сон, сом, ніс, мак, сік, стіл, тут, там, сало, кіно
яблуко, риба, село, Україна, їжак, юнак, край, день, син, моя
вухо, їжа, моє, яйце, юшка, каша, небо, сир, суп, хліб
зуб, дім, вовк, жук, шапка, гора, рука, бабуся, павук, ґанок
сіль, люди, вода, люк, Львів, м'ясо, п'ять, сім'я, цукор, час
що, джерело, дзвін, осінь, м'яч, щастя, факт, бджола, дзеркало, черепаха
цибуля, кінь, сестра, дерево, вулиця, автобус, бібліотека, університет, склад, переніс
голосний, приголосний, острів, ґудзик, кава, чай, замок, писати, школа, добрий
далеко, наголос, інтонація, питання, відповідь, хата, книжка, дорога, кафе, він
вона, воно, книга, слово, мова, вікно, брат, ніч, море, сонце
земля, Добрий день, Добрий ранок, Добрий вечір, Привіт, До побачення, Па-па, Дякую, Будь ласка, Вибачте
Перепрошую, Так, Ні, Як справи?, Добре, Погано, Нормально, Чудово, Смачного, На здоров'я
Добраніч, це, я, ти, ми, ви, вони, хто, студент, студентка
українець, українка, вчитель, вчителька, ось, мене звати, особовий займенник, займенник, граматичний рід, рід
телефон, дуже приємно, давай на ти, удома, на роботі, підручник, паспорт, цей, ця, ці
той, та, те, ті, кімната, стілець, ліжко, лампа, шафа, двері
квартира, новий, старий, гарний, великий, малий, поганий, цікавий, синій, червоний
молодий, дорогий, дешевий, смачний, зелений, який, множина, білий, чорний, жовтий
бордо, беж, хакі, колір, сорочка, штани, сукня, плаття, куртка, светр
джинси, окуляри, носити, одягати, розмір, дієслово, друг, музей, машина, пісня
хлопець, зошит, ручка, словник, читати, говорити, знати, розуміти, питати, відповідати
перевіряти, де, рахунок, смачного, працювати, слухати, грати, чекати, думати, вивчати
відпочивати, лист, повідомлення, новини, музика, радіо, робити, бачити, любити, їсти
пити, ходити, просити, сидіти, стояти, платити, вчити, гість, природа, домашнє завдання
дивитися, сміятися, вмиватися, одягатися, називатися, вчитися, займатися, повертатися, знайомитися, зустрічатися
вітатися, митися, голитися, зупинятися, цікавитися, мити, називати, себе, часто, швидко
як, скільки, завжди, ніколи, подобатися, хотіти, піти, нудний, хороший, фільм
борщ, квіти, мені, тобі, хобі, інфінітив

**Grammar already taught (65 topics):**
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

**Coming next (module after this):** Demonstrative pronouns, Gender agreement, Proximity distinction
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 20 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- мій (my m.) — мій друг, мій телефон, мій дім; High Frequency (Top 50)
- моя (my f.) — моя мама, моя книга, моя адреса; обов’язкове узгодження з жіночим родом
- моє (my n.) — моє ім'я, моє місто, моє рішення; узгодження з середнім родом
- його (his) — його батько, його машина, його робота; незмінна форма
- її (her) — її сумка, її кімната, її паспорт; незмінна форма
- наш (our) — наша країна, наше місто, наш клас; High Frequency (Top 100)
- чий (whose m.) — чий це?, чий телефон?, чий паспорт?; ключове питання для володіння
- чия (whose f.) — чия це сумка?, чия книга?; питання до жіночого роду

**Recommended** (use in your content to reach the vocabulary target):
- ваш (your formal/pl.) — ваш квиток, ваша адреса, ваше прізвище; High Frequency (Top 200)
- їхній (their) — їхній будинок, їхня сім’я, їхнє рішення; літературний стандарт (уникайте форми «їх»)
- свій (one's own) — свій час, своя справа, своє місце; рефлексивний присвійний займенник
- чиє (whose n.) — чиє це взуття?, чиє ім’я?; питання до середнього роду
- річ (thing) — ключовий контекстний іменник для сценаріїв «Бюро знахідок»

These are your TARGET words — teach them all and use them heavily. For the rest of the text, use natural, level-appropriate Ukrainian.

**VOCAB-IN-CONTENT RULE:** All vocabulary words from vocabulary_hints MUST appear at least once in the module content. Orphaned vocabulary (listed but never used in content) is a validation failure.

### Immersion Target

TARGET: 25-40% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — explain the grammar concept once, clearly.
- EXAMPLES: Ukrainian sentences in bulleted lists (each line: Ukrainian — English gloss). Max 2-4 per rule.
- TABLES: Paradigm tables, gender sorting, vocabulary groups — all cells Ukrainian.
- PATTERN BOXES: Show transformations and rules: `книга → книги` (singular → plural).
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences (3+ words with a verb) go in tables, bulleted example lists, or pattern boxes. Never write a Ukrainian sentence followed by its English translation in a prose paragraph.
Ukrainian sentences max 10 words. Mix container types — don't use tables for everything.

### Videos
- **ULP 2-45 | Повторення: 41-44 + Мій дім | Review: 41-44 + My home** (Ukrainian Lessons)
  URL: https://www.youtube.com/watch?v=bW-KetoCIuQ
  Score: 0.9 -- The video explicitly focuses on describing 'my home' using possessive pronouns (мій, моя, моє) in various contexts, directly aligning with the module's grammar topic of possessive forms and agreement. It provides multiple clear examples of natural usage.
  Suggested placement: After Презентація: Система форм та узгодження (Presentation: System of Forms and Agreement) -- it offers a practical, contextual demonstration of the grammar points just introduced.
  Key excerpt: Я хочу розповісти вам про мій дім в Україні... Моя кімната не тільки моя ми жили там разом з моїм молодшим братом Миколою.

- **ULP 2-60 | Повторення: 56-60 – Мій тиждень | Review: 56-60 – My week in Ukrainian** (Ukrainian Lessons)
  URL: https://www.youtube.com/watch?v=Kv_vJHT9_L8
  Score: 0.7 -- The video uses the possessive pronoun 'мій' in its title ('Мій тиждень') and content ('Мій розклад'), providing an example of its usage. While relevant, its primary focus is a review of prior lessons and discussing a weekly schedule, rather than explicitly teaching possessive forms.
  Suggested placement: After Культурний контекст: Етикет та еволюція стосунків (Cultural Context: Etiquette and Relationship Evolution) -- it serves as a listening practice that includes the target grammar, complementing the cultural section.
  Key excerpt: хочете знати Мій розклад на тиждень з понеділка по четвер я Вчусь і працюю у пенсильванському університеті.


### Textbook References
- **Grade 1, Сторінка 48**
  46
Бачу М, м (ем).  Чую [м].
м а *
а
*
*
м и * о
* о м а * * а
	
Визнач, яка схема відповідає намальовано-
му предмету. 
а
о
у
и
М
ма
мо
му
ми
а
о
у
и
ам
ом
ум
им
М
ма     
ма  
мо
ма
ми
му
ма-     
м...

- **Grade 1, Сторінка 25**
  23
	
Які? (розмір)
	
Які? (колір)
	
Які? (смак)
(яке?)
(який?)
(який?)
(який?)
(який?)
(який?)
(який?)
(який?)
(           ?)
Слова — назви ознак предметів
	 Який у тебе сьогодні настрій? Вибери.
Яки...

- **Grade 5, Сторінка 245**
  Ч а с т и н и   м о в и
Самостійні 
Іменник 
сонце
хто? що?
Прикметник
сонячний, мамин
який? чий?
Числівник
три, третій
скільки? котрий?
Займенник
я, ти, він
хто? що?
Дієслово
сидіти
що робити? що зро...

- **Grade 1, Сторінка 23**
  21
Хто це?
Слова — назви живих предметів
	 Який у тебе сьогодні настрій? Вибери.
 [ –    –|–  ] 
 [ =    –|–   ] 
 [ –  |–  |– ] 
 [ =  |–   – ] 
Що?
Хто?...

- **Grade 1, Сторінка 79**
  79
Я вивчаю українську мову . . . . . . . 4
Усне і писемне мовлення . . . . . . . 5
Слова — назви предметів . . . . . . . 6
Слова — назви дій . . . . . . . . . . . . . 7
Слово і речення . . . . . . . ...






---

## 4. Outline

Write **Mine and Yours** for the a1 track.

**Targets:** 1200–1800 words | 3+ callout boxes | **8–15 activities total** (required types + additional types to reach minimum) | 20 vocab items

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Вступ: Чия це річ? (Introduction: Whose Thing is This?)` (~250 words)
  - Ситуація «Бюро знахідок» (Lost and Found) для природної генерації обміну репліками про власність — використання реальних побутових предметів (телефон, ключі, паспорт) як візуальної опори для відпрацювання питання «Чий? Чия? Чиє?».
  - Пряме порівняння незмінних англійських займенників (my, your) з розгалуженою системою українського узгодження для підготовки учнів до концепції граматичного роду присвійних займенників.
- `## Презентація: Система форм та узгодження (Presentation: System of Forms and Agreement)` (~375 words)
  - Вивчення змінюваних форм (мій, твій, наш, ваш) відповідно до §4.2.2 Державного стандарту: детальні парадигми узгодження за родом (ч.р., ж.р., с.р.) та числом іменника з використанням колірного кодування для візуалізації.
  - Аналіз незмінюваних форм (його, її) — акцент на тому, що ці займенники залишаються стабільними незалежно від роду предмета володіння, що є поширеною точкою полегшення для початківців.
  - Специфіка займенника «їхній» як літературного стандарту: чітке розмежування з помилковим вживанням «їх» як присвійного займенника (Russianism), що подається як важливий маркер деколонізації та чистоти мовлення.
  - Початкове ознайомлення з рефлексивним займенником «свій» — базовий контраст для уникнення помилок типу «Він бачить його маму» (не свою) vs «Він бачить свою маму» (власну).
- `## Культурний контекст: Етикет та еволюція стосунків (Cultural Context: Etiquette and Relationship Evolution)` (~250 words)
  - Соціальна дистанція та етикет: суворе розрізнення «Твій» vs «Ваш». Опис ритуалу «переходу на ти» (switching to informal) як важливої віхи у розвитку особистих стосунків.
  - Аналіз та виправлення типових помилок (Learner Errors): стратегії подолання 'Gender Mismatch' (наприклад, помилкове *мій мама*) та запобігання 'Case Freeze' (вживання називного відмінка у випадках, де потрібен непрямий).
- `## Практика та продукція (Practice and Production)` (~325 words)
  - Керована практика (Guided Practice): вправи на заміну іменників займенниками та узгодження форм у контексті подорожей та повсякдення (мій рюкзак, ваша адреса, наша країна).
  - Продуктивний етап (§3.1 Державного стандарту): створення діалогів про особисту власність та рольова гра «Чия це сумка?», спрямована на автоматизацію використання питальних та присвійних займенників.
- `## Підсумок` (~150 words) — recap + 3-4 self-check questions

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Вступ: Чия це річ? (Introduction: Whose Thing is This?) | 250+ |
| Презентація: Система форм та узгодження (Presentation: System of Forms and Agreement) | 375+ |
| Культурний контекст: Етикет та еволюція стосунків (Cultural Context: Etiquette and Relationship Evolution) | 250+ |
| Практика та продукція (Practice and Production) | 325+ |
| **Total** | **1200+ (aim for ~1440)** |

---

## 5. Guidelines

### Workflow
1. **Research first**: `search_text("Possessive pronouns Gender agreement", grade=3-5)` — find how textbooks teach this
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
**Required types:** fill-in, match-up, fill-in, fill-in, quiz

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

GRAMMAR CONSTRAINTS (A1.2 — Verbs & Sentences):
Present tense verbs are fully available. Simple sentences.

ALLOWED:
- Present tense (я читаю, він іде, вони мають)
- Basic imperatives (читай/читайте, слухай/слухайте, дивись/дивіться)
- Infinitives in simple contexts (можна читати, треба слухати)
- Simple questions and answers

BANNED (too complex for A1.2):
- Past tense, future tense, conditionals
- Participles, passive voice
- Complex subordinate clauses

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
