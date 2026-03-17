You are about to build a module using the prompt below. Before you start, verify the prompt is ready.

**Default answer: PASS.** Only report genuine issues that would cause audit gate failures or introduce errors.

## The Prompt

<prompt>
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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/the-locative-where-things-are-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/the-locative-where-things-are.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("Locative case endings Prepositions в/у and на", grade=3-5)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 28
**Previous module:** Accusative Prepositions

**Cumulative vocabulary (338 words):**
мама, тато, кіт, молоко, масло, ліс, місто, око, так, ні
сон, сом, ніс, мак, сік, стіл, тут, там, сало, кіно
яблуко, риба, село, Україна, їжак, юнак, край, день, син, моя
вухо, їжа, моє, яйце, юшка, каша, небо, сир, суп, сіль
Львів, м'ясо, п'ять, сім'я, цукор, час, що, джерело, дзвін, осінь
м'яч, щастя, бджола, дзеркало, черепаха, цибуля, хлопець, вчителька, факт, фото
чай, кінь, сестра, дерево, вулиця, автобус, бібліотека, університет, склад, переніс
голосний, приголосний, острів, ґудзик, вода, кава, замок, рука, писати, школа
добрий, далеко, наголос, інтонація, питання, відповідь, хата, книжка, дорога, кафе
він, вона, воно, книга, слово, мова, дім, вікно, брат, ніч
море, сонце, земля, Добрий день, Добрий ранок, Добрий вечір, Привіт, До побачення, Па-па, Дякую
Будь ласка, Вибачте, Перепрошую, Так, Ні, Як справи?, Добре, Погано, Нормально, Чудово
Смачного, На здоров'я, Добраніч, це, я, ти, ми, ви, вони, хто
студент, студентка, українець, українка, вчитель, ось, мене звати, особовий займенник, займенник, граматичний рід
рід, телефон, дуже приємно, давай на ти, удома, на роботі, підручник, паспорт, цей, ця
ці, той, та, те, ті, кімната, стілець, ліжко, лампа, шафа
двері, квартира, новий, старий, гарний, великий, малий, поганий, цікавий, синій
червоний, молодий, дорогий, дешевий, смачний, зелений, який, множина, білий, чорний
жовтий, бордо, беж, хакі, колір, сорочка, штани, сукня, плаття, куртка
светр, джинси, окуляри, носити, одягати, розмір, дієслово, друг, музей, машина
пісня, зошит, ручка, словник, читати, говорити, знати, розуміти, питати, відповідати
перевіряти, де, рахунок, смачного, працювати, слухати, грати, чекати, думати, вивчати
відпочивати, лист, повідомлення, новини, музика, радіо, робити, бачити, любити, їсти
пити, ходити, просити, сидіти, стояти, платити, вчити, хліб, гість, природа
домашнє завдання, дивитися, сміятися, вмиватися, одягатися, називатися, вчитися, займатися, повертатися, знайомитися
зустрічатися, вітатися, митися, голитися, зупинятися, цікавитися, мити, називати, себе, часто
швидко, як, скільки, завжди, ніколи, подобатися, хотіти, піти, нудний, хороший
фільм, борщ, квіти, мені, тобі, хобі, інфінітив, мій, твій, твоя
твоє, його, її, наш, наша, ваш, ваша, їхній, свій, чий
чия, чиє, річ, сумка, будинок, озеро, такий, інший, кожний, сам
дівчина, мати, чути, брати, купувати, гречка, пакет, шукати, знаходити, відкривати
проблема, голос, подруга, лікар, пес, колега, сусід, дитина, матуся, татусь
братик, сестричка, знайомий, в, на, через, про, за, готель, вокзал
країна, міст, парк, екскурсія, квиток, іти, їхати, дякувати

**Grammar already taught (92 topics):**
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

**Coming next (module after this):** Locative case in context, Directional expressions, Prepositions of location
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 20 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- де (where) — primary question; collocations: Де ти? Де ви? Де це? Де туалет?
- в/у (in) — Top 10 frequency; euphony rules are critical: У Львові (avoid clusters)
- на (on/at) — usage for surfaces and activities: на роботі, на столі, на вулиці, на вокзалі
- кімната (room) — locative: у кімнаті; cultural context: housing types
- стіл (table) — usage: на столі
- магазин (store) — usage: в магазині
- школа (school) — usage: у школі
- робота (work) — social/activity exception: на роботі (Learner error: *в роботі)

**Recommended** (use in your content to reach the vocabulary target):
- банк (bank) — usage: у банку
- вокзал (station) — usage: на вокзалі
- підлога (floor) — triggers mutation г→з: на підлозі
- стіна (wall) — usage: на стіні
- вулиця (street) — high frequency: на вулиці
- парк (park) — usage: у парку

These are your TARGET words — teach them all and use them heavily. For the rest of the text, use natural, level-appropriate Ukrainian.

**VOCAB-IN-CONTENT RULE:** All vocabulary words from vocabulary_hints MUST appear at least once in the module content. Orphaned vocabulary (listed but never used in content) is a validation failure.

### Immersion Target

TARGET: 15-30% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — explain the grammar concept once, clearly.
- EXAMPLES: Ukrainian sentences in bulleted lists (each line: Ukrainian — English gloss). Max 2-4 per rule.
- TABLES: Paradigm tables, case endings, vocabulary groups — all cells Ukrainian.
- PATTERN BOXES: Show transformations: `книга → книгу` (nominative → accusative).
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences go in tables, bulleted lists, or pattern boxes.
Ukrainian sentences max 10 words. Mix container types.

### Podcast Episodes
*Each episode has audio + transcript + vocabulary list -- recommend to students as supplementary listening.*

- **5 S5 Ep161: ULP 5-161 Як у мене справи і що нового в Ukrainian Lessons**
  URL: https://www.ukrainianlessons.com/lesson-161/
  Relevance: 0.3
  Topics: ULP, Season 5

### Blog Articles & Guides
- **Prepositions У and НА in Ukrainian** (ukrainianlessons.com)
  URL: https://www.ukrainianlessons.com/prepositions-u-na/
  Relevance: 0.3
  Topics: prepositions, grammar


### Textbook References
- **Grade 4, Сторінка 67**
  67
Відмінок
Питання (однина)
Питання (множина)
Н. в.
Р. в.
Д. в.
Зн. в.
Ор. в.
М. в.
який? яка? яке?
якого? якої? якого?
якому? якій? якому?
як у Н. в. або Р. в.
яким? якою? яким?
(на, у) якому? якій?...

- **Grade 4, Сторінка 48**
  РОЗРІЗНЕННЯ ДАВАЛЬНОГО І МІСЦЕВОГО ВІДМІНКІВ )
135.1. Пригадай відмінки іменників та питання, на які вони від­
повідають. Визнач відмінок виділених іменників.
Ми дали білочці горішки. На білочці руда ...

- **Grade 4, Сторінка 38**
  38
73. 
1. Розгляньте таблицю. Зверніть увагу на назви від-
мінків. На які питання відповідає кожен з них? Чим 
відрізняється кличний відмінок від інших відмінків?
ВІДМІНЮВАННЯ ІМЕННИКІВ
Назва  
відмі...

- **Grade 4, Сторінка 61**
  61
	 У яких відмінках іменники вживають без прийменників, у яких — 
із прийменниками? Зроби висновок, користуючись таблицею. 
Звір його з поданим нижче правилом.
	 Провідміняй іменники степи, верби, ...

- **Grade 4, Сторінка 74**
  І У називному відмінку іменники вживаються без при- 
і йменників, у місцевому — тільки з прийменниками, 
1 
а в усіх інших відмінках можуть уживатися з приймен- 
« никами або без них. Наприклад: (біля...






---

## 4. Outline

Write **The Locative: Where Things Are** for the a1 track.

**Targets:** 1200–1800 words | 3+ callout boxes | **8–15 activities total** (required types + additional types to reach minimum) | 20 vocab items

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Вступ (Introduction)` (~250 words)
  - Introduction to the question «Де?» (Where?) as the functional trigger for the Locative case, focusing on high-frequency survival collocations: «Де ти?», «Де ви?», «Де це?», and «Де туалет?».
  - Cultural Hook: The 'Shoes Off' Rule. Explain the mandatory ritual of removing street shoes and entering with «капці» (slippers) to establish the domestic spatial context (вдома, у кімнаті).
- `## Презентація (Presentation)` (~350 words)
  - Grammar: Locative endings -і/-ї for most nouns per State Standard §4.2.3.3. Detailed presentation of velar mutations (к→ц, г→з, х→с) using the 'Hand and Leg' mnemonic: рука → у руці, нога → на нозі, вухо → у вусі.
  - Preposition logic: у/в (container/interior) vs. на (surface/activity/event). Explicitly address the rule of euphony (13j) to avoid clusters, e.g., correcting «В Львові» to «У Львові».
  - Mapping the activity exception: Contrast «у банку» (building) with the frequent social exception «на роботі» (work) to prevent English calques like «*в роботі».
- `## Практика (Practice)` (~300 words)
  - Drills on consonant mutations: Transformation tasks from Nominative to Locative targeting common learner errors like «*на ногі» vs. the correct «на нозі».
  - Discrimination exercise: Static Location (Locative) vs. Directional Motion (Accusative). Contrast «Я у парку» (I am in the park) with the common error «*Я в парк» to reinforce static case usage.
  - Roleplay: 'Where is...?' using city vocabulary (вокзал, пошта, парк). Focus on preposition selection and correct vocalic flow (в vs. у).
- `## Займенники у місцевому (Pronouns in Locative)` (~125 words)
  - Personal pronouns in locative: на мені, на тобі, на ньому, на ній, на нас, на вас, на них. У мене вдома. У тебе на столі.
  - 3rd person adds н- after prepositions: у нього, на ньому, у ній, на них. Same rule as accusative — preposition triggers н-.
- `## Виробництво та підсумок (Production and Summary)` (~175 words)
  - Describing your environment: Vocabulary for room and table (в кімнаті, на столі). Introduction to housing types (Stalinka, Khrushchevka, Novobudova) as authentic descriptors for describing 'where I live'.
  - Kyiv City Guide Task: Describe the location of people and objects in a city map context, applying mutations and preposition rules to landmarks (на вокзалі, у школі, на вулиці).

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Вступ (Introduction) | 250+ |
| Презентація (Presentation) | 350+ |
| Практика (Practice) | 300+ |
| Займенники у місцевому (Pronouns in Locative) | 125+ |
| Виробництво та підсумок (Production and Summary) | 175+ |
| **Total** | **1200+ (aim for ~1440)** |

---

## 5. Guidelines

### Workflow
1. **Research first**: `search_text("Locative case endings Prepositions в/у and на", grade=3-5)` — find how textbooks teach this
2. **Write content** following the outline and lesson arc below
3. **Verify as you write**: `verify_words` on any Ukrainian word you're unsure about
4. **Create activities** from your content
5. **Verify activities**: batch `verify_words` on all activity items

### Beginner Lesson Arc

1. **WELCOME** — warm greeting, set context
2. **PREVIEW** — "By the end of this module, you'll be able to..."
3. **PRESENT** — the main content sections
4. **PRACTICE** — examples, dialogues, reading practice
5. **CELEBRATE** — in the final `## Виробництво та підсумок (Production and Summary)` section, tell learners what they can now do

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
**Required types:** fill-in, fill-in, fill-in, match-up

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
- **MUST end with `## Виробництво та підсумок (Production and Summary)`** with self-check questions

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

</prompt>

## The Plan

<plan>
module: a1-029
level: A1
sequence: 29
slug: the-locative-where-things-are
version: '2.0'
title: 'The Locative: Where Things Are'
subtitle: Finding Your Way Around Ukrainian Spaces
focus: grammar
pedagogy: PPP
phase: A1.3 [Cases & Navigation]
word_target: 1200
objectives:
- Learner can ask and answer 'Where is X?' using locative case
- Learner can distinguish between в/у and на prepositions
- Learner can describe locations of people and objects
- Learner can name common places in Ukrainian
content_outline:
- section: Вступ (Introduction)
  words: 250
  points:
  - 'Introduction to the question «Де?» (Where?) as the functional trigger for the Locative case, focusing on high-frequency
    survival collocations: «Де ти?», «Де ви?», «Де це?», and «Де туалет?».'
  - 'Cultural Hook: The ''Shoes Off'' Rule. Explain the mandatory ritual of removing street shoes and entering with «капці»
    (slippers) to establish the domestic spatial context (вдома, у кімнаті).'
- section: Презентація (Presentation)
  words: 350
  points:
  - 'Grammar: Locative endings -і/-ї for most nouns per State Standard §4.2.3.3. Detailed presentation of velar mutations
    (к→ц, г→з, х→с) using the ''Hand and Leg'' mnemonic: рука → у руці, нога → на нозі, вухо → у вусі.'
  - 'Preposition logic: у/в (container/interior) vs. на (surface/activity/event). Explicitly address the rule of euphony (13j)
    to avoid clusters, e.g., correcting «В Львові» to «У Львові».'
  - 'Mapping the activity exception: Contrast «у банку» (building) with the frequent social exception «на роботі» (work) to
    prevent English calques like «*в роботі».'
- section: Практика (Practice)
  words: 300
  points:
  - 'Drills on consonant mutations: Transformation tasks from Nominative to Locative targeting common learner errors like
    «*на ногі» vs. the correct «на нозі».'
  - 'Discrimination exercise: Static Location (Locative) vs. Directional Motion (Accusative). Contrast «Я у парку» (I am in
    the park) with the common error «*Я в парк» to reinforce static case usage.'
  - 'Roleplay: ''Where is...?'' using city vocabulary (вокзал, пошта, парк). Focus on preposition selection and correct vocalic
    flow (в vs. у).'
- section: "Займенники у місцевому (Pronouns in Locative)"
  words: 125
  points:
  - "Personal pronouns in locative: на мені, на тобі, на ньому, на ній, на нас,
    на вас, на них. У мене вдома. У тебе на столі."
  - "3rd person adds н- after prepositions: у нього, на ньому, у ній, на них.
    Same rule as accusative — preposition triggers н-."
- section: Виробництво та підсумок (Production and Summary)
  words: 175
  points:
  - 'Describing your environment: Vocabulary for room and table (в кімнаті, на столі). Introduction to housing types (Stalinka,
    Khrushchevka, Novobudova) as authentic descriptors for describing ''where I live''.'
  - 'Kyiv City Guide Task: Describe the location of people and objects in a city map context, applying mutations and preposition
    rules to landmarks (на вокзалі, у школі, на вулиці).'
vocabulary_hints:
  required:
  - 'де (where) — primary question; collocations: Де ти? Де ви? Де це? Де туалет?'
  - 'в/у (in) — Top 10 frequency; euphony rules are critical: У Львові (avoid clusters)'
  - 'на (on/at) — usage for surfaces and activities: на роботі, на столі, на вулиці, на вокзалі'
  - 'кімната (room) — locative: у кімнаті; cultural context: housing types'
  - 'стіл (table) — usage: на столі'
  - 'магазин (store) — usage: в магазині'
  - 'школа (school) — usage: у школі'
  - 'робота (work) — social/activity exception: на роботі (Learner error: *в роботі)'
  recommended:
  - 'банк (bank) — usage: у банку'
  - 'вокзал (station) — usage: на вокзалі'
  - 'підлога (floor) — triggers mutation г→з: на підлозі'
  - 'стіна (wall) — usage: на стіні'
  - 'вулиця (street) — high frequency: на вулиці'
  - 'парк (park) — usage: у парку'
activity_hints:
- type: fill-in
  focus: Change nouns to locative
  items: 25
- type: fill-in
  focus: Choose в/у or на
  items: 20
- type: fill-in
  focus: Where is...? conversations
  items: 8
- type: match-up
  focus: Label locations in pictures
  items: 15
connects_to:
- a1-30 (Around the City)
prerequisites:
- a1-28 (Accusative Prepositions)
persona:
  voice: Patient Supportive Tutor
  role: Kyiv City Guide
grammar:
- Locative case endings
- Prepositions в/у and на
- Location expressions
register: розмовний

</plan>

## Audit Gates

## Audit Gates (your content will be checked against these)

Level: A1
Word target: 1200
Word ceiling: ~1800 (exceeding = FAIL)
Min activities: 8
Min engagement boxes: 3
Min activity types: 4

### Immersion
Target range: defined in the prompt's Immersion Target section (varies by module).
Tables count ZERO for immersion — only blockquotes, bulleted lists, and pattern boxes count.

### Grammar constraints
Max words per Ukrainian sentence: 10
Participles allowed: False
Max clauses: 1

### Structure
MUST have a Summary/Підсумок section (structure gate FAILS without it).

### Pedagogy
Sentences exceeding word limit = COMPLEXITY violation.
Participles before B1 = GRAMMAR violation.
Euphony (у/в alternation) errors are flagged.

## Scoring Dimensions (7 — Beginner Tier)
Your content will be scored on these dimensions (9-10 = PASS):
1. Language Quality — no Russianisms, correct Ukrainian, natural phrasing
2. Engagement — would the learner continue reading? Hook in first 50 words
3. Writing Quality — clarity, pacing, no word salad, logical flow
4. Immersion — % Ukrainian must hit target range (tables = ZERO)
5. Structure — lesson arc: WELCOME → PREVIEW → PRESENT → PRACTICE → CELEBRATE
6. Emotional Safety — ≥15 direct address, encouragement, quick wins
7. Lesson Quality — does it feel like a patient, encouraging tutor?

## Check 1: Prompt Feasibility

Only report if:
- Two instructions **directly contradict** each other AND following one will FAIL a named gate
- A target is **mathematically impossible** to reach given the constraints
- A required gate has **zero guidance** in the prompt (literally missing, not "could be clearer")

**Gate names**: Words, Activities, Density, Unique_types, Engagement, Vocab, Structure, Pedagogy, Immersion.

## Check 2: Semantic False Friends (Russianisms)

These Ukrainian words exist in BOTH Ukrainian and Russian but have DIFFERENT meanings:

- **лук**: Russian meaning = onion, цибуля, onions; Ukrainian meaning = bow (weapon). Correct word for 'onion, цибуля, onions' → **цибуля**
- **город**: Russian meaning = city, місто, town; Ukrainian meaning = garden, vegetable patch. Correct word for 'city, місто, town' → **місто**
- **неділя**: Russian meaning = week, тиждень; Ukrainian meaning = Sunday. Correct word for 'week, тиждень' → **тиждень**
- **річ**: Russian meaning = speech; Ukrainian meaning = thing, item. Correct word for 'speech' → **промова**
- **шар**: Russian meaning = ball, sphere; Ukrainian meaning = layer. Correct word for 'ball, sphere' → **куля**
- **мешкати**: Russian meaning = to dawdle, to delay, dawdle; Ukrainian meaning = to live, to dwell. Correct word for 'to dawdle, to delay, dawdle' → **баритися**
- **лічити**: Russian meaning = to treat, to heal, treatment; Ukrainian meaning = to count. Correct word for 'to treat, to heal, treatment' → **лікувати**
- **наглий**: Russian meaning = arrogant, impudent, insolent; Ukrainian meaning = sudden, unexpected. Correct word for 'arrogant, impudent, insolent' → **зухвалий**
- **лаяти**: Russian meaning = to bark, bark, barking; Ukrainian meaning = to scold, to swear at. Correct word for 'to bark, bark, barking' → **гавкати**
- **палиця**: Russian meaning = finger; Ukrainian meaning = stick, cane. Correct word for 'finger' → **палець**
- **сварка**: Russian meaning = welding; Ukrainian meaning = quarrel, argument. Correct word for 'welding' → **зварювання**

**Only flag if the prompt USES or DEFINES a word with the Russian meaning.** Do NOT flag:
- Warnings about the false friend (e.g., "неділя ≠ week")
- Discussions explaining the difference
- Correct Ukrainian usage

## Check 3: Plan-Prompt Coherence

Compare the plan (above) to the rendered prompt. Check:
1. **Section coverage**: Every plan `content_outline` section has a matching section in the prompt
2. **Word target**: Plan's `word_target` matches the prompt's word budget
3. **Vocabulary**: All `vocabulary_hints.required` items appear in the prompt
4. **Objectives**: The prompt's instructions would achieve all plan `objectives`

Only flag if a plan section is **completely missing**, the word target **differs**, or required vocabulary is **absent**. Do NOT flag rewordings or extra scaffolding.

## Output Format (YAML)

```yaml
prompt_preflight:
  status: PASS  # or ISSUES_FOUND
  issues:
    - type: CONTRADICTION  # MISSING_INSTRUCTION, IMPOSSIBLE_TARGET, RUSSICISM, MISSING_PLAN_SECTION, PLAN_CONTRADICTION, WORD_TARGET_MISMATCH
      location: "where in the prompt"
      problem: "what's wrong"
      suggested_fix: "how to fix it"
      severity: HIGH  # or MEDIUM, LOW
```

If no issues: `prompt_preflight: {status: PASS, issues: []}`

Be SPECIFIC. Cite exact text.