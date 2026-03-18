**Curriculum context:** This is Module 22 of the A1 track (Ukrainian for English speakers). Title: "Numbers & Money" — Counting and Shopping in Ukraine. Phase: A1.2 [Verbs & Sentences]. Previous module: Demonstratives This That. Next module: What Time Is It.

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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/numbers-and-money-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/numbers-and-money.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("Cardinals 0-100 Number agreement (1=nom, 2-4=nom.pl, 5+=gen.pl)", grade=3-5)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 21
**Previous module:** Demonstratives

**Cumulative vocabulary (254 words):**
мама, тато, кіт, молоко, масло, ліс, місто, око, так, ні
сон, ніс, мак, сік, стіл, тут, там, привіт, дякую, це
яблуко, риба, село, Україна, їжак, юнак, край, день, син, моя
вухо, їжа, моє, яйце, юшка, каша, небо, сир, сало, хліб
зуб, дім, вовк, жук, шапка, гора, рука, бабуся, павук, ґанок
сіль, люди, суп, вода, цибуля, люк, Львів, кінь, осінь, м'ясо
п'ять, сім'я, м'яч, цукор, час, чай, черепаха, що, щастя, факт
джерело, бджола, дзвін, склад, голосний, приголосний, перенесення, сестра, вікно, ґудзик
пальці, книга, вулиця, автобус, брат, море, ніч, земля, серце, сонце
машина, ім'я, артефакт, зона, укриття, добрий ранок, добрий день, добрий вечір, до побачення, будь ласка
вибачте, перепрошую, дуже приємно, пане, пані, бувай, здрастуйте, ласкаво просимо, на все добре, добраніч
ти, ви, як справи, я, він, вона, воно, ми, вони, хто
студент, студентка, українець, українка, вчитель, вчителька, звати, ось, друзі, цей
ця, ці, той, та, те, ті, телефон, кімната, стілець, ліжко
лампа, шафа, двері, ніж, ложка, крісло, диван, новий, старий, гарний
великий, малий, добрий, поганий, цікавий, синій, червоний, молодий, дорогий, дешевий
смачний, зелений, рідний, білий, чорний, жовтий, сорочка, штани, сукня, куртка
светр, плаття, джинси, окуляри, вишиванка, колір, одяг, прапор, бордо, одні
дитина, людина, гроші, очі, ножиці, маленький, говорити, робити, бачити, любити
їсти, пити, ходити, просити, сидіти, стояти, платити, вчити, дивитися, борщ
парк, школа, чи, де, коли, не, куди, звідки, чому, як
скільки, завжди, ніколи, часто, іноді, але, а, бо, подобатися, хотіти
кава, музика, читати, піти, нудний, улюблений, гуляти, співати, торт, слухати
мій, твій, його, її, наш, ваш, їхній, свій, чий, чия
чиє, річ, сумка, ключі, паспорт, адреса, прізвище, будинок, озеро, такий
інший, кожний, сам, кафе

**Grammar already taught (71 topics):**
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

**Coming next (module after this):** Clock time expressions (Котра година?), Time prepositions (о, до, після), Days and months in context
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 20 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- один (one) — High frequency (Top 100); collocations: «один раз», «одна гривня»; warning: gender agreement error (один vs одна)
- два (two) — High frequency (Top 100); collocations: «два дні», «дві гривні» (feminine!); warning: gender agreement error (два vs дві)
- три (three) — High frequency; usage in basic counting and price negotiation
- п'ять (five) — High frequency; pronunciation focus [pjat'] with distinct apostrophe; collocations: «п'ять хвилин», «п'ять гривень»
- десять (ten) — High frequency; essential base for teen numbers and currency denominations
- гривня (hryvnia) — High frequency (contextual); historical origin from 'neck' (hryva); collocations: «одна гривня», «скільки гривень?»
- скільки (how much) — High frequency; key collocations: «Скільки з мене?», «Скільки коштує?»
- коштувати (to cost) — Medium frequency; essential for shopping; collocation: «Скільки це коштує?»

**Recommended** (use in your content to reach the vocabulary target):
- сто (hundred) — Usage in large numbers and round prices like «сто гривень»
- копійка (kopeck) — Cultural proverb: «Копійка береже гривню»; historical subunit of the hryvnia
- ціна (price) — Medium frequency; collocations: «яка ціна?», «висока ціна», «низька ціна»
- дорого (expensive) — Context: «Це дуже дорого!»; used for expressing budget constraints
- дешево (cheap) — Context: «Це дешево»; evaluation of value for money
- здача (change) — Essential for completing transactions; collocation: «Чи є у вас здача?»

These are your TARGET words — teach them all and use them heavily. For the rest of the text, use natural, level-appropriate Ukrainian.

**VOCAB-IN-CONTENT RULE:** All vocabulary words from vocabulary_hints MUST appear at least once in the module content. Orphaned vocabulary (listed but never used in content) is a validation failure.

### Immersion Target

TARGET: 15-25% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — explain the grammar concept once, clearly.
- EXAMPLES: Ukrainian sentences in bulleted lists (each line: Ukrainian — English gloss). Max 2-4 per rule.
- TABLES: Paradigm tables, gender sorting, vocabulary groups — all cells Ukrainian.
- PATTERN BOXES: Show transformations and rules: `книга → книги` (singular → plural).
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences go in tables, bulleted lists, or pattern boxes — never in flowing prose.
Ukrainian sentences max 10 words. Mix container types.

### Videos
- **FMU 1-07 | Grammar point: numeral / noun agreement in Ukrainian | 5 Minute Ukrainian** (Ukrainian Lessons)
  URL: https://www.youtube.com/watch?v=l8Zoyl70FXo
  Score: 0.9 -- The video directly teaches 'numeral / noun agreement in Ukrainian' using examples of currency (hryvnia, dollar, euro), which aligns perfectly with the module's grammar points on number agreement and genitive plural with numbers in a 'Numbers & Money' context.
  Suggested placement: After the 'Презентація (Presentation)' section, as it directly explains the grammatical rules for numeral-noun agreement, which is a core concept of the module.
  Key excerpt: Grammar Point numeral noun agreement in Ukrainian... if The numeral Ends with 1 Simply Use The singular Form of noun like 1 201 до 341 до$ then if The numeral S with 2 3 4 two or Three or F Use The plural Form as you know it 2 долари 3 гривні.


### Podcast Episodes
*Each episode has audio + transcript + vocabulary list -- recommend to students as supplementary listening.*

- **ULP S1 Ep5: Numbers 1-20 in Ukrainian + Pronunciation Trainer**
  URL: https://www.ukrainianlessons.com/episode5/
  Relevance: 0.5
  Topics: numbers, pronunciation

- **ULP S2 Ep67: Telling time in Ukrainian + Ordinal numbers & Locative case**
  URL: https://www.ukrainianlessons.com/episode67/
  Relevance: 0.5
  Topics: grammar, cases, locative, numbers, phrases

### Blog Articles & Guides
- **Ukrainian Currency — Hryvnia** (ukrainianlessons.com)
  URL: https://www.ukrainianlessons.com/ukrainian-currency/
  Relevance: 0.6
  Topics: money, currency, numbers, vocabulary

- **Ukrainian Phrasebook: Numbers** (ukrainianlessons.com)
  URL: https://www.ukrainianlessons.com/ph-numbers/
  Relevance: 0.4
  Topics: numbers, counting

- **Ukrainian Phrasebook: Money** (ukrainianlessons.com)
  URL: https://www.ukrainianlessons.com/ph-money/
  Relevance: 0.4
  Topics: money, shopping, prices


### Textbook References
- **Grade 6, Сторінка 155**
  155
ЧИСЛІВНИКИ КІЛЬКІСНІ І ПОРЯДКОВІ, 
ПРОСТІ, СКЛАДНІ ТА СКЛАДЕНІ
§ 59
Як не стати марнотратами
Числівник може визначить тобі число речей, порядок при лічбі (Д. Білоус).
Слово дня: вèтрати, побратèми...

- **Grade 3, Сторінка 80**
  80
225. 1.	 Прочитай. Як ти гадаєш, про яку частину мови йдеться у вірші? 
Пригадай! Числівник — це частина мови, яка називає 
кількість предметів і відповідає на питання скільки?
Назвемо числа по пор...

- **Grade 6, Сторінка 152**
  152
1.	Прочитайте слова й словосполучення та виконайте завдання.
один → перше місце — золота медаль
два → друге місце — срібна медаль
три → третє місце — бронзова медаль
А.	
Які числівники вказують на...

- **Grade 6, Сторінка 150**
  150
1.	Прочитайте слова в колонках і виконайте завдання. 
семиколірний
сім
сімка
семеро
усімох
сьомий
А.	 Слова якої колонки вказують на кількість або порядок при лічбі?
Б.	 До яких частин мови належа...

- **Grade 6, Сторінка 243**
  § 51. Узгодження числівників з іменниками  
243
Вправа 492
Запишіть словосполучення числівників з  іменниками (за потреби 
форму числівника теж можна міняти).
Одна третя (клас), три з  половиною (годи...






---

## 4. Outline

Write **Numbers & Money** for the a1 track.

**Targets:** 1200–1800 words | 3+ callout boxes | **8–15 activities total** (required types + additional types to reach minimum) | 20 vocab items

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Вступ (Introduction)` (~250 words)
  - Державний стандарт (§3.8) та роль чисел у повсякденному житті: фокус на тематиці купівлі основних продуктів, одягу та засобів гігієни.
  - Де ми використовуємо числа: приклади з реальним контекстом 2024 року (наприклад, кава за 50 грн, квиток на автобус) та розкладом руху.
  - Мотиваційний вступ через діалог про покупки, що активує знання з модуля a1-16 (Генітив I) у контексті запиту ціни.
- `## Презентація (Presentation)` (~350 words)
  - Числа 1-20: фокус на правильну вимову «п'ять» [pjat'] (пауза апострофа) та правильний наголос у числівниках 11-19 (одинАдцять, дванАдцять).
  - Десятки (20-100) та застереження щодо помилок: відсутність м'якого знака в середині числівників 50-80 (п'ятдесят, шістдесят).
  - Правило «1-2-5»: узгодження чисел з іменниками (1 гривня - Nom Sg, 2 гривні - Nom Pl, 5 гривень - Gen Pl) з використанням візуальних таблиць.
  - Запитання про ціну та базові конструкції: «Скільки коштує?», «Скільки з мене?», «Яка ціна?».
- `## Практика (Practice)` (~350 words)
  - Лічба та арифметика: інтерактивні вправи на додавання цін у кошику з використанням актуальних цін (хліб ~25 грн, молоко ~40 грн).
  - Робота над помилкою «два» vs «дві»: акцент на жіночому роді слова «гривня» («дві гривні») на відміну від чоловічого («два долари»).
  - Діалоги в магазині: моделювання ситуацій купівлі з використанням фразеології «Це дуже дорого!» та «У вас є здача?».
  - Дрилі на закріплення правила 1-2-5: перетворення форм іменника залежно від випадкового числа (3 гривні -> 10 гривень -> 1 гривня).
- `## Культурний контекст (Cultural Context)` (~250 words)
  - Історія гривні: походження назви від «гриви» (шийна прикраса або злиток із золота чи срібла часів Київської Русі).
  - Символ гривні ₴: аналіз графіки (курсивна літера «г» з двома рисками) як символу стабільності за аналогією до € та ¥.
  - Народна мудрість: вивчення прислів'я «Копійка береже гривню» для ілюстрації традиційного ставлення до грошей та ощадливості.
- `## Підсумок` (~150 words) — recap + 3-4 self-check questions

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Вступ (Introduction) | 250+ |
| Презентація (Presentation) | 350+ |
| Практика (Practice) | 350+ |
| Культурний контекст (Cultural Context) | 250+ |
| **Total** | **1200+ (aim for ~1440)** |

---

## 5. Guidelines

### Workflow
1. **Research first**: `search_text("Cardinals 0-100 Number agreement (1=nom, 2-4=nom.pl, 5+=gen.pl)", grade=3-5)` — find how textbooks teach this
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
**Required types:** fill-in, fill-in, quiz, fill-in

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


FRICTION CONSTRAINTS (from past build reviews — DO NOT repeat these errors):
- [GLOBAL] сес-тра is a VALID word division per Правопис 2019 §49. Do NOT mark it as an error. Phonetic syllabification (се-стра) and typographic word division (сес-тра) follow different rules — both are correct in their respective contexts.
- [GLOBAL] Ukrainian textbooks teach a hands-on-EARS test for voicing (закрий долонями вуха), NOT a hand-on-throat test. The hand-on-throat test is a valid phonetics technique but must NOT be attributed to Ukrainian textbooks. Source: Кравцова 2019, Grade 2, p.39.
- [GLOBAL] Do NOT invent Ukrainian words for minimal pairs. "Сір" is NOT a word meaning "grey" — the correct form is "сірий". Use verified minimal pairs only: кит/кіт, бити/біти, лис/ліс.
