You are about to build a module using the prompt below. This prompt has been carefully engineered to produce content that passes all audit gates. Your job is to confirm it is ready.

**Default answer: PASS.** This prompt is designed to work. Only report issues if something will genuinely cause an audit gate to FAIL.

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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/the-genitive-i-absence-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/the-genitive-i-absence.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("Genitive case for absence Genitive endings", grade=3-5)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 31
**Previous module:** Pronoun Declension

**Cumulative vocabulary (393 words):**
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
чек, чека, купа

**Grammar already taught (101 topics):**
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

**Coming next (module after this):** Locative prepositions (в/у, на), Euphonic в/у alternation, Біля/навпроти + Genitive
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 20 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- немає (there is no) — High frequency core word; used in ready-made models: «немає часу», «немає грошей»
- без (without) — High frequency preposition + Genitive; collocations: «без цукру», «без молока», «без газу»
- час (time) — Gen: часу; abstract noun requiring ending -у; State Standard high-frequency item
- гроші (money) — Gen pl: грошей; irregular plural; essential for financial context (§3.8)
- молоко (milk) — Gen: молока; neuter noun, regular neuter-to-genitive shift
- цукор (sugar) — Gen: цукру; uncountable substance requiring ending -у; key for restaurant dialogues
- вода (water) — Gen: води; contrast «вода з газом» vs «вода без газу»
- хліб (bread) — Gen: хліба; concrete object requiring ending -а; context: grocery shopping

**Recommended** (use in your content to reach the vocabulary target):
- проблема (problem) — Gen pl: проблем; used in the ubiquitous phrase «Немає проблем!»
- квиток (ticket) — Gen: квитка; concrete object (ending -а); Learner Error: common neglect of case after «без»
- ключ (key) — Gen: ключа; concrete object focus
- телефон (phone) — Gen: телефона (the device) / телефону (phone number, concept); demonstrates -а/-у semantic split
- газ (gas/sparkling) — Gen: газу; used in the essential collocation «без газу» for ordering water

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

### Videos
- **Ukrainian for beginners: Where are u from? Countries, languages | Genitive case,  Verb conjugations** (Ukrainian with Olha)
  URL: https://www.youtube.com/watch?v=xGrdJHym-9E
  Score: 0.7 -- This video explicitly discusses the Genitive case for indicating origin, which is another specific application of the Genitive, reinforcing the module's focus on specific Genitive functions.
  Suggested placement: After Презентація (Presentation) -- to illustrate another specific usage of the Genitive case, complementing the concept of absence.
  Key excerpt: Today we will learn several grammar points such as a genitive case of nouns when used to inform about someone's origin... Genitive case, родовий відмінок, has multiple uses in Ukrainian.

- **ULP 2-46 | У продуктовому магазині + Родовий відмінок | At the grocery store + Genitive case** (Ukrainian Lessons)
  URL: https://www.youtube.com/watch?v=NuXQSauP8cY
  Score: 0.5 -- The video introduces the Genitive case in the context of grocery shopping, providing general context for the Genitive but not specifically for absence.
  Suggested placement: After Презентація (Presentation) -- to provide additional examples of the Genitive case in a different context.
  Key excerpt: Today We Start a new topic Food ya and the genitive C родовий відмінок почнімо з їжі

- **ULP 2-47 | Гастрономічні фестивалі + Родовий відмінок | Food festivals + Genitive case** (Ukrainian Lessons)
  URL: https://www.youtube.com/watch?v=QhKN_tj05Rg
  Score: 0.5 -- Similar to Candidate 1, this video introduces the Genitive case within the context of food festivals, offering general Genitive usage rather than absence.
  Suggested placement: After Презентація (Presentation) -- as another resource for understanding general Genitive case applications.
  Key excerpt: сьогодні ми будемо вивчати більше про родовий відмінок їжу і звичайно Україну до роботи


### Podcast Episodes
*Each episode has audio + transcript + vocabulary list -- recommend to students as supplementary listening.*

- **ULP S2 Ep46: At the grocery store + Genitive case**
  URL: https://www.ukrainianlessons.com/episode46/
  Relevance: 1.0
  Topics: grammar, cases, genitive, vocabulary, food

- **ULP S2 Ep47: Food festivals + Genitive case**
  URL: https://www.ukrainianlessons.com/episode47/
  Relevance: 0.5
  Topics: grammar, cases, genitive, vocabulary, food

- **ULP S2 Ep48: Eating habits + Genitive case**
  URL: https://www.ukrainianlessons.com/episode48/
  Relevance: 0.5
  Topics: grammar, cases, genitive, prepositions, plural

- **ULP S2 Ep49: Syrnyky recipe + Genitive case**
  URL: https://www.ukrainianlessons.com/episode49/
  Relevance: 0.5
  Topics: grammar, cases, genitive, phrases, introductions

### Blog Articles & Guides
- **Dobra Forma: Genitive Case after Prepositions біля, після, для and без** (dobraforma)
  URL: https://opentext.ku.edu/dobraforma/chapter/7-2/
  Relevance: 0.5
  Topics: genitive, cases, prepositions, grammar


### Textbook References
- **Grade 4, Сторінка 74**
  І У називному відмінку іменники вживаються без при- 
і йменників, у місцевому — тільки з прийменниками, 
1 
а в усіх інших відмінках можуть уживатися з приймен- 
« никами або без них. Наприклад: (біля...

- **Grade 4, Сторінка 61**
  61
	 У яких відмінках іменники вживають без прийменників, у яких — 
із прийменниками? Зроби висновок, користуючись таблицею. 
Звір його з поданим нижче правилом.
	 Провідміняй іменники степи, верби, ...

- **Grade 4, Сторінка 190**
  Змінювання дієслів минулого часу
за родами (в однині) й числами......................................................146
Теперішній час. Змінювання дієслів теперішнього часу 
за особами й числами........

- **Grade 10, Сторінка 211**
  § 84 Частка 
211
Разом
Окремо
без не не вживається
означають одне поняття
не становлять одного поняття; 
є заперечення
Прислівник
незабаром, нещадно
неважко (легко), недалеко (близько)
не далеко, а бл...

- **Grade 6, Сторінка 269**
  § 54. Розряди займенників за значенням та особливості відмінювання   
269
Зверніть увагу на варіанти наголошування запереч-
них займенників ніхто і  ніщо в  непрямих відмінках: 
ніко́го — нíкого, нічо...






---

## 4. Outline

Write **The Genitive I: Absence** for the a1 track.

**Targets:** 1200–1800 words | 3+ callout boxes | **8–15 activities total** (required types + additional types to reach minimum) | 20 vocab items

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Вступ (Introduction)` (~250 words)
  - Контраст конструкцій «є» (possession from a1-13) vs «немає» (absence) — State Standard §4.0: акцент на відтворенні готових моделей у ситуаціях «Покупки» (§3.8) та «Ресторан» (§3.9).
  - Подолання Learner Error: розрізнення граматичного заперечення якості/стану «не» (Я не студент) та заперечення існування/наявності «немає» (У мене немає квитка).
- `## Презентація (Presentation)` (~350 words)
  - Граматична основа: конструкція немає + родовий відмінок — State Standard §4.2.2.2: формування навички на базі сталих сполук «немає часу», «немає грошей» (Gen. pl. exception).
  - Прийменник без + родовий відмінок — ключові колокації для повсякденного вжитку: «кава без цукру», «вода без газу», «їхати без квитка».
  - Систематизація закінчень чоловічого роду: конкретні предмети на -а/-я (хліба, квитка) проти абстрактних та речовинних на -у/-ю (часу, цукру) — фокус на Learner Error 3.
- `## Практика (Practice)` (~350 words)
  - Корекція типової помилки (Case Neglect): використання називного відмінка замість родового після «немає» — дрил на мінімальних парах «є квиток» vs «немає квитка».
  - Трансформаційні вправи за схемою Nom → Gen — візуалізація змін закінчень: -а/-я для чоловічого (конкретне) та -и/-і для жіночого (вода → води).
  - Рольова гра «У ресторані/магазині»: замовлення напоїв «без цукру/молока» та ввічливі запити про наявність товарів.
- `## Культурний контекст (Cultural Context)` (~250 words)
  - Культурний код: вживання фрази «Немає проблем!» як вияву гнучкості та ввічлива відмова через «немає» («На жаль, квитків немає») для пом'якшення прямого «Ні».
  - Лінгвокраїнознавство: розбір прислів'я «Немає диму без вогню» як ілюстрації структури заперечення та вживання прийменника з родовим відмінком.
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
1. **Research first**: `search_text("Genitive case for absence Genitive endings", grade=3-5)` — find how textbooks teach this
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
**Required types:** fill-in, fill-in, fill-in

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

</prompt>

## Audit Gates (what your content will be checked against)

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

## Instructions

Read the prompt carefully. If you can build a module that passes all audit gates using this prompt, return PASS.

Only report an issue if:
- Two instructions **directly contradict** each other AND following one will FAIL a named gate
- A target is **mathematically impossible** to reach given the constraints
- A required gate has **zero guidance** in the prompt (not "could be clearer" — literally missing)

Do NOT report: style preferences, wording suggestions, minor ambiguities, things that "could be improved." Focus on issues that would prevent you from building excellent content.

**Gate names** (only these matter): Words, Activities, Density, Unique_types, Engagement, Vocab, Structure, Pedagogy, Immersion.

## Output Format (YAML)

```yaml
prompt_preflight:
  status: PASS  # or ISSUES_FOUND
  issues:
    - type: CONTRADICTION  # or MISSING_INSTRUCTION, IMPOSSIBLE_TARGET, UNCLEAR
      location: "Section 4, line about tables"
      problem: "Template says tables have highest density but audit strips tables from immersion"
      suggested_fix: "Remove 'highest density' claim, add warning that tables = zero immersion"
      severity: HIGH  # or MEDIUM, LOW
```

If there are no issues, return:
```yaml
prompt_preflight:
  status: PASS
  issues: []
```

Be SPECIFIC. Cite exact text from the prompt. Focus on issues that will cause audit FAILURES, not style preferences.