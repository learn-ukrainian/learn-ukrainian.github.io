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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/a1-final-exam-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/a1-final-exam.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("All A1 grammar comprehensive review All four cases", grade=3-5)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 63
**Previous module:** Euphony and Polish

**Cumulative vocabulary (652 words):**
мама, тато, кіт, молоко, масло, ліс, місто, око, так, ні
сон, сом, ніс, мак, сік, стіл, тут, там, сало, кіно
яблуко, риба, село, Україна, їжак, юнак, край, день, син, моя
вухо, їжа, моє, яйце, юшка, каша, небо, сир, суп, сіль
Львів, кінь, осінь, м'ясо, п'ять, сім'я, м'яч, цукор, цибуля, час
чай, черепаха, що, щастя, факт, джерело, бджола, дзвін, сестра, дерево
вулиця, автобус, бібліотека, університет, склад, переніс, голосний, приголосний, острів, ґудзик
вода, кава, замок, рука, писати, школа, добрий, далеко, наголос, інтонація
питання, відповідь, хата, книжка, дорога, кафе, він, вона, воно, книга
слово, мова, дім, вікно, брат, ніч, море, сонце, земля, Добрий день
Добрий ранок, Добрий вечір, Привіт, До побачення, Па-па, Дякую, Будь ласка, Вибачте, Перепрошую, Так
Ні, Як справи?, Добре, Погано, Нормально, Чудово, Смачного, На здоров'я, Добраніч, це
я, ти, ми, ви, вони, хто, студент, студентка, українець, українка
вчитель, вчителька, ось, мене звати, особовий займенник, займенник, граматичний рід, рід, телефон, дуже приємно
давай на ти, удома, на роботі, підручник, паспорт, цей, ця, ці, той, та
те, ті, кімната, стілець, ліжко, лампа, шафа, двері, квартира, новий
старий, гарний, великий, малий, поганий, цікавий, синій, червоний, молодий, дорогий
дешевий, смачний, зелений, який, множина, білий, чорний, жовтий, бордо, беж
хакі, колір, сорочка, штани, сукня, плаття, куртка, светр, джинси, окуляри
носити, одягати, розмір, дієслово, друг, музей, машина, пісня, хлопець, зошит
ручка, словник, читати, говорити, знати, розуміти, питати, відповідати, перевіряти, де
рахунок, смачного, працювати, слухати, грати, чекати, думати, вивчати, відпочивати, лист
повідомлення, новини, музика, радіо, робити, бачити, любити, їсти, пити, ходити
просити, сидіти, стояти, платити, вчити, хліб, гість, природа, домашнє завдання, дивитися
сміятися, вмиватися, одягатися, називатися, вчитися, займатися, повертатися, знайомитися, зустрічатися, вітатися
митися, голитися, зупинятися, цікавитися, мити, називати, себе, часто, швидко, як
скільки, завжди, ніколи, подобатися, хотіти, піти, нудний, хороший, фільм, борщ
квіти, мені, тобі, хобі, інфінітив, мій, твій, твоя, твоє, його
її, наш, наша, ваш, ваша, їхній, свій, чий, чия, чиє
річ, сумка, будинок, озеро, такий, інший, кожний, сам, дівчина, мати
чути, брати, купувати, гречка, пакет, шукати, знаходити, відкривати, проблема, голос
подруга, лікар, пес, колега, сусід, дитина, матуся, татусь, братик, сестричка
знайомий, в, на, через, про, за, готель, вокзал, країна, міст
парк, екскурсія, квиток, іти, їхати, дякувати, у, магазин, робота, банк
підлога, стіна, туалет, нога, маяти, куди, дуже, дужий, йти, людина
метро, багато, використовувати, аптека, простий, український, жаль, відсутність, гроші, сьогодні
українська, означати, форма, водити, закінчення, відмінок, опис, знахідний, правило, правити
жіночий, ом, веліти, вести, йога, зараз, зараза, кий, краса, красити
нове, до, місцевий, звідки, рух, додому, вчора, бути, минулий, раніше
тиждень, місяць, спати, рік, ранок, вечір, чоловічий, середній, завтра, буду
наступний, план, збиратися, скоро, потім, післязавтра, вранці, вдень, ввечері, майбутнє
овочі, фрукти, паляниця, компот, картопля, помідор, коштувати, купити, гривня, кілограм
літр, пачка, пляшка, штука, ринок, мило, зубна паста, шампунь, рушник, туалетний папір
решта, картка, меню, офіціант, замовляти, будь ласка, тістечко, готівка, чайові, принести
лимон, чек, тепло, погода, дощ, холодно, сніг, том, тому, сильний
ліса, обід, вечеря, добре, зазвичай, іноді, рідко, вставати, снідати, погано
можний, могти, вміти, мо, описувати, навичка, повинний, терти, баба, хіть
хота, раз, роба, потрібний, дно, треба, спа, читай, пиши, казати
скажи, дати, дай, іди, слухай, дивись, стій, взяти, візьми, допомогти
допоможи, показати, покажи, чекай, голова, живіт, горло, боліти, лікарня, температура
кашель, нежить, ліки, хворий, здоровий, рецепт, малина, однина, донька, дідусь
бабуся, тітка, дядько, онук, онука, родина, чоловік, дружина, мудрий, старший
молодший, свято, Новий рік, Різдво, Великдень, день народження, Святвечір, вітати, бажати, святкувати
здоров'я, успіх, подарунок, дарувати, отримувати, торт, свічка, Кутя, страва, взаємно
малювати, танцювати, плавати, стадіон, басейн, захоплюватися, велосипед, спортзал, вихідні, співати
готувати, фотографувати, футбол, бігати, гуляти, тролейбус, трамвай, таксі, потяг, літак
маршрутка, аеропорт, зупинка, валіза, прямо, направо, наліво, подорож, замовити, перше
друге, третє, столик, будьмо, гарнір, без м'яса, без глютену, піца, десерт, повинен
запрошувати, поїзд, не курити, увага, обережно, вхід, вихід, зачинено, відчинено, розклад
вихідний, перерва, небезпечно, пішохідний, перехід, площа, провулок, оголошення, знижка, акція
місце, транспорт, вагон, їда, станція, фраза, ласка, дзвонити, сказати, дзвінка
дзвінок, зайнятий, розмова, текст, анкета, написати, поле, стати, стать, листівка
привіт, структура, просто, продавець, ринка, хтіти, товар, огірок, відділ, каса
касир, ціна, супермаркет, знаходитися, працівник, чека, швидка, швидкий, кликати, міна
міні, діалог, поліція, номер, звук, уникати, мат, мата, ставити, речення
пауза, починатися

**Grammar already taught (204 topics):**
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
- Могти conjugation (irregular stem)
- Вміти conjugation
- Можна/не можна impersonal construction
- Треба/потрібно impersonal construction
- Повинен agreement (m/f/n/pl)
- Хотіти conjugation (irregular stem)
- Imperative mood formation
- Ти/Ви forms
- Polite request patterns
- Negative imperative
- Pain expressions (У мене болить + body part)
- Health vocabulary
- Impersonal necessity (треба + infinitive)
- Family vocabulary
- Possessives with family members
- Genitive for relationships (батько + name)
- Basic vocative forms (мамо, тату, бабусю, дідусю)
- Holiday greetings (З + Instrumental)
- Date expressions with Genitive
- Wish expressions (Бажаю + Genitive)
- Грати в/на construction
- Ходити в + Accusative
- Invitation patterns (Ходімо, Давай)
- Instrumental for transport means (потягом, автобусом)
- Direction vocabulary and imperative usage
- Як дістатися до + Genitive
- Practical usage of A1 cases
- Polite requests and questions
- Future tense for ordering
- Modal verbs (могти/вміти/треба/повинен/хотіти)
- Imperative mood (8 required verbs)
- Travel expressions (Instrumental, directions)
- Invitation patterns
- Infinitive in prohibitions
- Sign language conventions
- Schedule reading (з... до... construction)
- Direction with до + genitive
- Time expressions for schedules
- Numbers for platforms and seats
- Direction questions (Як доїхати до...?)
- Imperative for directions
- Locative for stops
- Phone conversation formulas
- Imperative for requests
- Could you... (Чи могли б ви...)
- Written register basics
- Form vocabulary and field types
- Address format (Ukrainian order)
- Genitive for quantities (кілограм + genitive)
- Accusative for requests
- Numbers with nouns
- Location questions (Де знаходиться...?)
- Accusative for shopping
- Quantity expressions
- Vocative case for emergency address (Лікарю!, Поліціє!)
- Urgent requests (Допоможіть!)
- Simple problem descriptions
- Euphony rules (phonological alternations)
- У/В alternation
- І/Й alternation
- З/Із/Зі alternation

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 20 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- знати (to know) — знати мову, знати відповідь, я знаю; Rank 6 / Most Used Verbs
- говорити (to speak) — говорити українською, говорити правду; Rank 16 / Most Used Verbs
- слухати (to listen) — слухати музику, слухати вчителя; Rank 21 / Most Used Verbs
- розуміти (to understand) — добре розуміти, розуміти текст; high frequency in educational context
- читати (to read) — reading comprehension focus per State Standard §4.3.1
- писати (to write) — functional writing task support
- відповідати (to answer) — «Студент відповідає»; classroom interaction vocabulary
- питати (to ask) — asking general and special questions

**Recommended** (use in your content to reach the vocabulary target):
- правильно (correctly) — evaluation and feedback marker
- помилка (mistake) — focus on common learner errors (case/gender/conjugation)
- завдання (task) — домашнє завдання, цікаве завдання; high frequency classroom word
- оцінка (grade) — formal and informal assessment context
- каштан (chestnut) — cultural symbol of Kyiv
- кава (coffee) — cultural hook for Lviv context

These are your TARGET words — teach them all and use them heavily. For the rest of the text, use natural, level-appropriate Ukrainian.

**VOCAB-IN-CONTENT RULE:** All vocabulary words from vocabulary_hints MUST appear at least once in the module content. Orphaned vocabulary (listed but never used in content) is a validation failure.

### Immersion Target

TARGET: 25-40% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — brief and clear. Show, don't tell.
- PARADIGM TABLES: Conjugation/declension tables with all cells Ukrainian.
- EXAMPLE LISTS: Ukrainian sentences in bulleted lists (each: Ukrainian — English gloss).
- DIALOGUES: Mini-dialogues in blockquotes with English gloss per line.
- PATTERN BOXES: Show transformations: `читати → читай → читайте`.
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences go in tables, bulleted lists, dialogues, or pattern boxes.
Ukrainian sentences max 10 words. Mix container types.

### Videos
- **ULP 3-108 Екскурсія Києвом – Kyiv tour + Participle in Ukrainian** (Ukrainian Lessons)
  URL: https://www.youtube.com/watch?v=XSZ66J7KlQc
  Score: 0.8 -- The video is a podcast about a tour of Kyiv ('Екскурсія Києвом'), which directly reinforces the 'Культурна подорож: Київ та Львів' section of the A1 Final Exam module. While it also touches on advanced grammar (participles), the primary focus on a Kyiv tour provides relevant cultural context and listening practice for A1 learners.
  Suggested placement: After section 'Культурна подорож: Київ та Львів' -- because it provides a direct, immersive example of the cultural journey aspect mentioned in the section.
  Key excerpt: це ukra lessens podcast епізод 108 екскурсія Києвом a kїв [музика] Tour ... Тож у сьогоднішньому епізоді ви почуєте розмову Юрка та Христини під час їхньої прогулянки Києвом


### Textbook References
- **Grade 1, Сторінка 3**
  3
Дорогий друже!
Ти хочеш учитися читати?
Ти прагнеш спілкуватися?
Ти любиш фантазувати?
Тоді ця книга саме для тебе! 
Вона допоможе тобі навчитися читати, 
висловлювати думки й почуття, спілкуватися....

- **Grade 4, Сторінка 143**
  ЗМІСТ
з
Звуки і букви. Склад. Наголос. Звуко-буквений склад слів...................... 4
Правильне наголошення слів.................. 4
Правильна вимова та написання слів 
із дзвінкими приголосними в ...

- **Grade 2, Сторінка 128**
  128
ЗМІСТ
Звуки і букви. Склад. Наголос. Звуко-буквений склад слів.................3
Звуки і букви..............................................................................................3
Алфаві...

- **Grade 11, Сторінка 122**
  скоротили? ПЛАН ОЦІНКИ ІНФОРМАЦІЙНОГО ВИСТУПУ
1. Тема й мета промови: їх актуальність, корисність для слухачів. 2. Вступ. • Наскільки вичерпним було самопредставлення....

- **Grade 9, Сторінка 249**
  Хід заняття
	 1. Опрацюйте наведений матеріал і дайте відповіді на запитання. 2. Зробіть висновки відповідно до мети заняття....






---

## 4. Outline

Write **A1 Final Exam** for the a1 track.

**Targets:** 1200–1800 words | 3+ callout boxes | **8–15 activities total** (required types + additional types to reach minimum) | 20 vocab items

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Вступ та орієнтація (Introduction and Orientation)` (~175 words)
  - Структура фінального тесту — supportive tone to reduce stress, emphasis on celebration of progress («Ви готові!», «Чудова робота!»)
  - Як оцінюється кожна частина — alignment with communicative goals and encouragement from the Patient Supportive Tutor
  - Поради для успішного складання — focus on calm confidence and practical strategies for A1 tasks
- `## Морфологічний та синтаксичний огляд (Morphological and Syntactic Review)` (~375 words)
  - Verification of morphological competence per State Standard §4.2: core noun cases (Nominative, Accusative, Locative, Vocative) and basic verb conjugation
  - Correction of Case Confusion (Accusative vs. Locative) — drill with the distinction between motion and location using prepositions *в/на*: «Я йду в магазин» (Acc) vs. «Я в магазині» (Loc)
  - Grammar drill on Gender Agreement — resolving the learner error of mismatching adjectives/pronouns: «Моя велика машина» (Correct) vs. «Мій велика машина» (Error)
  - Conjugation mastery — clarifying the distinction between Class I (-ати) and Class II (-ити) verbs: «Він читає» vs. «Він робить»
  - Syntactic structures per State Standard §4.3.1 — review of SVO word order, general questions («Чи це наш автобус?»), and special questions using «де», «звідки», «куди», «що», «хто»
- `## Культурна подорож: Київ та Львів (Cultural Journey: Kyiv and Lviv)` (~400 words)
  - Thematic narrative «Trip around Ukraine» — integrating transport (§3.3), food (§3.8), and home (§3.2) contexts into the assessment
  - Kyiv — Heart of Ukraine: focus on cultural hooks (Dnipro River, chestnut trees/каштани) and its historical status as a 5th-century foundation
  - Lviv — Cultural Capital: exploring coffee traditions, book culture, and the legacy of the oldest printing house in Ukraine (based on esu.com.ua)
  - Functional application — using numbers, time, and basic communication phrases within the travel narrative
- `## Фінальне оцінювання та перехід до A2 (Final Assessment and Transition to A2)` (~250 words)
  - Listening and Reading Comprehension — verifying understanding of simple sentences and basic complex sentences (using «і», «а», «але») per State Standard §4.3.2
  - Practical scenarios and role-play — oral assessment tasks focused on real-world situations (buying tickets, ordering coffee, introductions)
  - Readiness for Level A2 — setting the foundation for the upcoming Genitive and Dative cases while celebrating A1 mastery
  - Final encouraging summary — reinforcing the progress made through the 44 modules and looking forward to A2-01
- `## Підсумок` (~150 words) — recap + 3-4 self-check questions

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Вступ та орієнтація (Introduction and Orientation) | 175+ |
| Морфологічний та синтаксичний огляд (Morphological and Syntactic Review) | 375+ |
| Культурна подорож: Київ та Львів (Cultural Journey: Kyiv and Lviv) | 400+ |
| Фінальне оцінювання та перехід до A2 (Final Assessment and Transition to A2) | 250+ |
| **Total** | **1200+ (aim for ~1440)** |

---

## 5. Guidelines

### Workflow
1. **Research first**: `search_text("All A1 grammar comprehensive review All four cases", grade=3-5)` — find how textbooks teach this
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
**Required types:** quiz, quiz, fill-in

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

SEQUENCE CONSTRAINTS (A1.6 — Real-World Skills):
Full A1 grammar available including imperatives. The standard A1 LEVEL_CONSTRAINTS apply.

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
