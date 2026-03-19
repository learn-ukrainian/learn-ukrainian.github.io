You are about to build a module using the prompt below. Before you start, verify the prompt is ready.

**Default answer: PASS.** Only report genuine issues that would cause audit gate failures or introduce errors.

## The Prompt

<prompt>
**Curriculum context:** This is Module 40 of the A1 track (Ukrainian for English speakers). Title: "Shopping and Market" — How Much Does It Cost?. Phase: A1.4 [Tenses & Daily Life]. Previous module: Food Vocabulary. Next module: At The Cafe.

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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/shopping-and-market-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/shopping-and-market.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("Скільки коштує construction Genitive with quantities", grade=3-5)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 39
**Previous module:** Food and Drink

**Cumulative vocabulary (294 words):**
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
дорогий, дешевий, смачний, зелений, який, будинок, немає, без, гроші, проблема
квиток, ключ, газ, від, на жаль, вогонь, будь ласка, є, магазин, кухня
пошта, біля, навпроти, знаходитися, поруч, між, близько, парк, аптека, банк
зупинка, метро, маленький, красивий, український, важливий, популярний, фільм, ресторан, церква
де, куди, звідки, через, за, про, робота, центр, іти, їхати
до, з, лікар, Київ, повертатися, виходити, аеропорт, вокзал, вчора, бути
робити, їсти, пити, читати, дивитися, ходити, минулий, раніше, тиждень, місяць
спати, працювати, йти, писати, варити, готувати, купувати, гуляти, додому, завтра
наступний, план, хотіти, збиратися, скоро, потім, рік, сподіватися, мріяти, планувати
пізніше, післязавтра, майбутнє, відпочивати, прокидатися, вмиватися, одягатися, снідати, обідати, вечеряти
лягати, зазвичай, спочатку, нарешті, щодня, перерва, одяг, борщ, овочі, фрукти
паляниця, компот, картопля, напій

**Grammar already taught (128 topics):**
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

**Coming next (module after this):** Integration of Accusative, Genitive, Locative, Polite imperatives (принесіть, візьміть), Future tense preview (візьму)
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 20 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- коштувати (to cost) — Скільки коштує?; core shopping verb
- купити (to buy, pf.) — Я хочу купити; perfective for single purchase
- гривня (hryvnia) — одна гривня, дві гривні, п'ять гривень; currency
- кілограм (kilogram) — кілограм яблук; weight unit + Gen
- літр (litre) — літр молока; volume unit + Gen
- пачка (packet) — пачка цукру; container unit + Gen
- пляшка (bottle) — пляшка води; container unit + Gen
- магазин (store) — у магазині; shopping location
- ринок (market) — на ринку; outdoor market location
- мило (soap) — купити мило; basic hygiene item

**Recommended** (use in your content to reach the vocabulary target):
- шампунь (shampoo) — masculine gender; hygiene vocabulary
- рушник (towel) — masculine gender; cultural embroidered towel
- решта (change) — Ваша решта; transaction completion
- картка (card) — банківська картка; modern payment

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

- **FMU Ep18: Vocabulary booster! Shopping Vocabulary in Ukrainian**
  URL: https://www.ukrainianlessons.com/fmu18/
  Relevance: 0.3
  Topics: phrases

- **FMU Ep49: How to shop at the market in Ukrainian**
  URL: https://www.ukrainianlessons.com/fmu49/
  Relevance: 0.3
  Topics: vocabulary, food, phrases, listening

### Blog Articles & Guides
- **Ukrainian Phrasebook: Clothing** (ukrainianlessons.com)
  URL: https://www.ukrainianlessons.com/ph-clothing/
  Relevance: 0.3
  Topics: clothing, shopping

- **Ukrainian Phrasebook: Money** (ukrainianlessons.com)
  URL: https://www.ukrainianlessons.com/ph-money/
  Relevance: 0.3
  Topics: money, shopping, prices


### Textbook References
- **Grade 4, Сторінка 124**
  124
1. Яку інформацію містить кожна купюра?
2. Чим купюри відрізняються, а що в них подібне?
3. Чиї портрети зображають на купюрах? Чому?
4. Чи можна в наш час обійтися без купюр? 
5. Поясніть, як роз...

- **Grade 6, Сторінка 244**
  Розділ 7. Числівник 
244
із  6-річного віку, а  підліток у  віці 
від 14 до 18 (роки) може само-
стійно відкрити рахунок на своє 
ім’я.
Картку можна оформити без-
коштовно. Якщо ви бажаєте інди-
відуа...

- **Grade 11, Сторінка 72**
  замість 40  коп. становив 90  коп. Тепер  ті самі тор-
говельні операції на зовнішньому ринку приносили 
СРСР у  2,25  разу більше прибутків. Переваги отри-
мали галузі економіки, орієнтовані на експо...

- **Grade 8, Сторінка 139**
  137
ЗА ГРОШІ ЩАСТЯ НЕ КУПИШ
Г е р а с и м. Отже, побий мене бог, меж ними є фальшиві; і таких 
грошей можна купить, скільки хочеш... Пристанете в компанію? Купи-
мо сто тисяч. С а в к а. Сто тисяч! Г ...

- **Grade 8, Сторінка 74**
  5. У нашій школі вивчається 
анг­лійська мова. 6. На третій касі покупці не обслуговуються. 7. Про­
токол зборів підписано головою та секретарем. 8. Перелік пам’яток 
архітектури затверджується Верхов...






---

## 4. Outline

Write **Shopping and Market** for the a1 track. Target: 1200–1800 words.

### CRITICAL: EXACT H2 HEADERS (copy-paste, do not alter)

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Скільки коштує? (How much?)` (~275 words)
  - Key question pattern: Скільки коштує...? Скільки це коштує? Forming price questions with коштувати (to cost).
  - Price expressions with гривня: одна гривня, дві гривні, п'ять гривень. Number-noun agreement review from a1-17 (Numbers and Money).
  - Answering price questions: Це коштує двадцять гривень. Борщ коштує сімдесят гривень. Producing full price sentences.
- `## У магазині (In the Store)` (~250 words)
  - Polite request patterns: Дайте, будь ласка... (Give me, please...). Я хочу купити... (I want to buy...). Можна...? (May I...?).
  - Checking availability: Є...? (Is there...?) У вас є...? (Do you have...?). Learner error: using мати instead of є for store availability.
  - Basic shopping dialogue structure: greeting → asking for item → asking price → paying → thanking. Complete transaction flow.
- `## Кількість та одиниці (Quantities and Units)` (~250 words)
  - Units of measurement: кілограм, літр, пачка, пляшка, штука. Gender and typical products for each unit.
  - Genitive with quantities: кілограм яблук, літр молока, пачка цукру, пляшка води. Reinforcing formulaic Genitive from a1-18.
  - Numbers with units: два кілограми (2-4 + Gen. sg.), п'ять кілограмів (5+ + Gen. pl.). Number-noun case agreement patterns.
- `## Засоби гігієни (Hygiene Products)` (~175 words)
  - Essential hygiene vocabulary: мило (soap), зубна паста (toothpaste), шампунь (shampoo), рушник (towel), туалетний папір (toilet paper).
  - Asking where to buy items: Де можна купити...? Де тут аптека? Де тут магазин? Combining location and shopping skills.
- `## Практика (Practice)` (~250 words)
  - Shopping role-play dialogues: Complete transaction from greeting to payment. At the market (ринок) and at the store (магазин).
  - Price asking and answering drills: Скільки коштує...? — Це коштує... гривень. Rapid price negotiation practice.
  - Quantity expression practice: Ordering specific amounts with correct case forms. Shopping list construction.
- `## Підсумок` (~150 words) — recap + 3-4 self-check questions

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Скільки коштує? (How much?) | 275+ |
| У магазині (In the Store) | 250+ |
| Кількість та одиниці (Quantities and Units) | 250+ |
| Засоби гігієни (Hygiene Products) | 175+ |
| Практика (Practice) | 250+ |
| **Total** | **1200+ (aim for ~1440)** |

---

## 5. Rules (read ALL before writing)

### RULE 1: GRAMMAR — see Section 6

Section 6 (Hard Constraints) defines exactly what grammar structures you may use for this module. Follow those constraints — they vary by module number.

### RULE 2: VOCABULARY

Prioritize these Ukrainian words (from the plan). You may also use words from the cumulative vocabulary and common Ukrainian words, but these are your core teaching targets:

**Allowed Ukrainian words:** коштувати, купити, гривня, кілограм, літр, пачка, пляшка, магазин, ринок, мило, шампунь, рушник, решта, картка

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
**Required types:** fill-in, quiz, match-up, unjumble

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


FRICTION CONSTRAINTS (from past build reviews — DO NOT repeat these errors):
- [GLOBAL] сес-тра is a VALID word division per Правопис 2019 §49. Do NOT mark it as an error. Phonetic syllabification (се-стра) and typographic word division (сес-тра) follow different rules — both are correct in their respective contexts.
- [GLOBAL] Ukrainian textbooks teach a hands-on-EARS test for voicing (закрий долонями вуха), NOT a hand-on-throat test. The hand-on-throat test is a valid phonetics technique but must NOT be attributed to Ukrainian textbooks. Source: Кравцова 2019, Grade 2, p.39.
- [GLOBAL] Do NOT invent Ukrainian words for minimal pairs. "Сір" is NOT a word meaning "grey" — the correct form is "сірий". Use verified minimal pairs only: кит/кіт, бити/біти, лис/ліс.
- [GLOBAL] NEVER frame Ukrainian as "lacking" or "missing" letters that Russian has. Ukrainian has its own 33-letter alphabet — it is complete. Do NOT write "Ukrainian lacks Ъ, Ы, Э" or "Ukrainian doesn't have these Russian letters." Instead, highlight what Ukrainian HAS: Ґ, Є, Ї, І are unique to Ukrainian. Present Ukrainian on its own terms.

</prompt>

## The Plan

<plan>
module: a1-040
level: A1
sequence: 40
slug: shopping-and-market
version: '2.0'
title: Shopping and Market
subtitle: How Much Does It Cost?
focus: vocabulary
pedagogy: PPP
phase: A1.4 [Tenses & Daily Life]
word_target: 1200
objectives:
- Ask and understand prices
- Use basic shopping phrases
- Express quantities with correct units
- Buy everyday items including hygiene products
content_outline:
- section: Скільки коштує? (How much?)
  words: 275
  points:
  - 'Key question pattern: Скільки коштує...? Скільки це коштує? Forming price questions with коштувати (to cost).'
  - 'Price expressions with гривня: одна гривня, дві гривні, п''ять гривень. Number-noun agreement review from a1-17 (Numbers
    and Money).'
  - 'Answering price questions: Це коштує двадцять гривень. Борщ коштує сімдесят гривень. Producing full price sentences.'
- section: У магазині (In the Store)
  words: 250
  points:
  - 'Polite request patterns: Дайте, будь ласка... (Give me, please...). Я хочу купити... (I want to buy...). Можна...? (May
    I...?).'
  - 'Checking availability: Є...? (Is there...?) У вас є...? (Do you have...?). Learner error: using мати instead of є for
    store availability.'
  - 'Basic shopping dialogue structure: greeting → asking for item → asking price → paying → thanking. Complete transaction
    flow.'
- section: Кількість та одиниці (Quantities and Units)
  words: 250
  points:
  - 'Units of measurement: кілограм, літр, пачка, пляшка, штука. Gender and typical products for each unit.'
  - 'Genitive with quantities: кілограм яблук, літр молока, пачка цукру, пляшка води. Reinforcing formulaic Genitive from
    a1-18.'
  - 'Numbers with units: два кілограми (2-4 + Gen. sg.), п''ять кілограмів (5+ + Gen. pl.). Number-noun case agreement patterns.'
- section: Засоби гігієни (Hygiene Products)
  words: 175
  points:
  - 'Essential hygiene vocabulary: мило (soap), зубна паста (toothpaste), шампунь (shampoo), рушник (towel), туалетний папір
    (toilet paper).'
  - 'Asking where to buy items: Де можна купити...? Де тут аптека? Де тут магазин? Combining location and shopping skills.'
- section: Практика (Practice)
  words: 250
  points:
  - 'Shopping role-play dialogues: Complete transaction from greeting to payment. At the market (ринок) and at the store (магазин).'
  - 'Price asking and answering drills: Скільки коштує...? — Це коштує... гривень. Rapid price negotiation practice.'
  - 'Quantity expression practice: Ordering specific amounts with correct case forms. Shopping list construction.'
vocabulary_hints:
  required:
  - коштувати (to cost) — Скільки коштує?; core shopping verb
  - купити (to buy, pf.) — Я хочу купити; perfective for single purchase
  - гривня (hryvnia) — одна гривня, дві гривні, п'ять гривень; currency
  - кілограм (kilogram) — кілограм яблук; weight unit + Gen
  - літр (litre) — літр молока; volume unit + Gen
  - пачка (packet) — пачка цукру; container unit + Gen
  - пляшка (bottle) — пляшка води; container unit + Gen
  - магазин (store) — у магазині; shopping location
  - ринок (market) — на ринку; outdoor market location
  - мило (soap) — купити мило; basic hygiene item
  recommended:
  - шампунь (shampoo) — masculine gender; hygiene vocabulary
  - рушник (towel) — masculine gender; cultural embroidered towel
  - решта (change) — Ваша решта; transaction completion
  - картка (card) — банківська картка; modern payment
activity_hints:
- type: fill-in
  focus: Complete shopping dialogue with correct phrases
  items: 10
- type: quiz
  focus: Quantity expressions with correct case forms
  items: 10
- type: match-up
  focus: Match product to appropriate unit of measurement
  items: 10
- type: unjumble
  focus: Reorder words into correct shopping sentences
  items: 6
connects_to:
- a1-41 (At the Cafe)
prerequisites:
- a1-39 (Food and Drink)
persona:
  voice: Patient Supportive Tutor
  role: Market Vendor
grammar:
- Скільки коштує construction
- Genitive with quantities
- Shopping imperative phrases (Дайте, будь ласка)
register: розмовний

</plan>

## Audit Gates

## Audit Gates (your content will be checked against these)

Level: A1
Word target: 1200
Word ceiling: ~1800 (exceeding = FAIL)
Min activities: 0
Min engagement boxes: 1
Min activity types: 0

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
- **луна**: Russian meaning = moon, місяць, lunar; Ukrainian meaning = echo (відлуння). Correct word for 'moon, місяць, lunar' → **місяць**
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