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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/my-family-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/my-family.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("Family vocabulary Possessives with family members", grade=3-5)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 48
**Previous module:** Body & Health

**Cumulative vocabulary (495 words):**
мама, тато, кіт, молоко, масло, ліс, місто, око, так, ні
сон, сом, ніс, мак, сік, стіл, тут, там, сало, кіно
яблуко, риба, село, Україна, їжак, юнак, край, день, син, моя
вухо, їжа, моє, яйце, юшка, каша, небо, сир, суп, сестра
дерево, вулиця, автобус, бібліотека, університет, склад, переніс, голосний, приголосний, острів
сім'я, ґудзик, вода, кава, чай, замок, рука, писати, школа, добрий
далеко, наголос, інтонація, питання, відповідь, хата, книжка, дорога, кафе, він
вона, воно, книга, слово, мова, дім, вікно, брат, ніч, час
море, сонце, земля, Добрий день, Добрий ранок, Добрий вечір, Привіт, До побачення, Па-па, Дякую
Будь ласка, Вибачте, Перепрошую, Так, Ні, Як справи?, Добре, Погано, Нормально, Чудово
Смачного, На здоров'я, Добраніч, це, я, ти, ми, ви, вони, хто
що, студент, студентка, українець, українка, вчитель, вчителька, ось, мене звати, особовий займенник
займенник, граматичний рід, рід, телефон, дуже приємно, давай на ти, удома, на роботі, підручник, паспорт
цей, ця, ці, той, та, те, ті, кімната, стілець, ліжко
лампа, шафа, двері, квартира, новий, старий, гарний, великий, малий, поганий
цікавий, синій, червоний, молодий, дорогий, дешевий, смачний, зелений, який, множина
білий, чорний, жовтий, бордо, беж, хакі, колір, сорочка, штани, сукня
плаття, куртка, светр, джинси, окуляри, носити, одягати, розмір, дієслово, друг
музей, машина, пісня, хлопець, зошит, ручка, словник, читати, говорити, знати
розуміти, питати, відповідати, перевіряти, де, рахунок, смачного, працювати, слухати, грати
чекати, думати, вивчати, відпочивати, лист, повідомлення, новини, музика, радіо, робити
бачити, любити, їсти, пити, ходити, просити, сидіти, стояти, платити, вчити
хліб, гість, природа, домашнє завдання, дивитися, сміятися, вмиватися, одягатися, називатися, вчитися
займатися, повертатися, знайомитися, зустрічатися, вітатися, митися, голитися, зупинятися, цікавитися, мити
називати, себе, часто, швидко, як, скільки, завжди, ніколи, цукор, подобатися
хотіти, піти, нудний, хороший, фільм, борщ, квіти, мені, тобі, хобі
інфінітив, мій, твій, твоя, твоє, його, її, наш, наша, ваш
ваша, їхній, свій, чий, чия, чиє, річ, сумка, будинок, озеро
такий, інший, кожний, сам, дівчина, мати, чути, брати, купувати, гречка
пакет, шукати, знаходити, відкривати, проблема, голос, подруга, лікар, пес, колега
сусід, дитина, матуся, татусь, братик, сестричка, знайомий, в, на, через
про, за, готель, вокзал, країна, міст, парк, екскурсія, квиток, іти
їхати, дякувати, у, магазин, робота, банк, підлога, стіна, туалет, нога
маяти, куди, дуже, дужий, йти, людина, метро, багато, використовувати, аптека
простий, український, жаль, відсутність, гроші, сьогодні, українська, означати, форма, водити
закінчення, відмінок, опис, знахідний, правило, правити, жіночий, ом, веліти, вести
йога, зараз, зараза, кий, краса, красити, нове, до, місцевий, звідки
рух, додому, вчора, бути, минулий, раніше, тиждень, місяць, спати, рік
ранок, вечір, чоловічий, середній, завтра, буду, наступний, план, збиратися, скоро
потім, післязавтра, вранці, вдень, ввечері, майбутнє, м'ясо, овочі, фрукти, паляниця
компот, картопля, помідор, коштувати, купити, гривня, кілограм, літр, пачка, пляшка
штука, ринок, мило, зубна паста, шампунь, рушник, туалетний папір, решта, картка, меню
офіціант, замовляти, будь ласка, тістечко, готівка, чайові, принести, лимон, чек, тепло
погода, дощ, холодно, сніг, том, тому, сильний, ліса, обід, вечеря
добре, зазвичай, іноді, рідко, вставати, снідати, погано, можний, могти, вміти
мо, описувати, навичка, повинний, терти, баба, хіть, хота, раз, роба
потрібний, дно, треба, спа, читай, пиши, казати, скажи, дати, дай
іди, слухай, дивись, стій, взяти, візьми, допомогти, допоможи, показати, покажи
чекай, голова, живіт, горло, боліти, лікарня, температура, кашель, нежить, ліки
хворий, здоровий, рецепт, малина, однина

**Grammar already taught (156 topics):**
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

**Coming next (module after this):** Holiday greetings (З + Instrumental), Date expressions with Genitive, Wish expressions (Бажаю + Genitive)
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 20 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- мама (mom) — рідна мама, молода мама; найвища частотність, клична форма: мамо!
- тато (dad) — рідний тато, мій тато; клична форма: тату!
- брат (brother) — старший брат, молодший брат, рідний брат
- сестра (sister) — старша сестра, молодша сестра, рідна сестра
- дідусь (grandfather) — мудрий дідусь, мій дідусь; клична форма: дідусю!
- бабуся (grandmother) — добра бабуся; клична форма: бабусю!
- син (son) — мій син, єдиний син
- донька (daughter) — моя донька, доросла донька

**Recommended** (use in your content to reach the vocabulary target):
- сім'я (family) — велика сім'я, моя сім'я; ядерний підрозділ
- родина (family) — вся родина, збиратися родиною; ширший контекст роду та зв'язків
- чоловік (husband) — мій чоловік; важливо розрізняти зі значенням 'man'
- дружина (wife) — моя дружина; стандартний нейтральний термін
- дядько (uncle) — добрий дядько
- тітка (aunt) — рідна тітка
- онук (grandson) — мій онук
- онука (granddaughter) — маленька онука

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

### Videos
- **Наша родина - Our family #ukrainianlessons #ukrainianlanguage #studyukrainian #languagelearning** (Ukrainian with Olha)
  URL: https://www.youtube.com/watch?v=LD6eFDIGKrU
  Score: 0.9 -- The video directly introduces and names family members (мама, тато, бабуся, сестра, родичів), perfectly aligning with the 'My Family' topic and relevant vocabulary such as Родина, мама, тато.
  Suggested placement: After section Презентація: Близька та розширена родина -- The video demonstrates introducing and naming family members, which is a direct application of the concepts taught in this section.
  Key excerpt: Наша родина. Це наша родина. Це мама і тато. Маму звати Ольга Петрівна, а тата Микола Андрійович.


### Podcast Episodes
*Each episode has audio + transcript + vocabulary list -- recommend to students as supplementary listening.*

- **ULP S1 Ep6: Talking about your family in Ukrainian + I have, you have**
  URL: https://www.ukrainianlessons.com/episode6/
  Relevance: 0.5
  Topics: vocabulary, family

- **ULP S1 Ep7: More about your family in Ukrainian + Possessive Pronouns**
  URL: https://www.ukrainianlessons.com/episode7/
  Relevance: 0.5
  Topics: grammar, pronouns, vocabulary, family

### Blog Articles & Guides
- **Family Vocabulary in Ukrainian** (ukrainianlessons.com)
  URL: https://www.ukrainianlessons.com/vocabulary-family/
  Relevance: 0.8

- **ULP 1-06 Talking about your family in Ukrainian + I have, you have** (ukrainianlessons.com)
  URL: https://www.ukrainianlessons.com/lesson/6/
  Relevance: 0.8

- **Talk Ukrainian: Family – Родина** (talkukrainian)
  URL: https://talkukrainian.com/family/
  Relevance: 0.8
  Topics: family, родина, сім'я, vocabulary


### Textbook References
- **Grade 1, Сторінка 8**
  6
Я  і  моя  родина
Поділюся з вами я:
В мене дружна є сім’я.
Люба мама і татусь,
Бабця Віра і дідусь, 
Мурка, Барсик, Оля, я  —
От і вся моя сім’я.
                    Марія Братко
	 Намалюй свою род...

- **Grade 3, Сторінка 110**
  110
Навчаюся визначати рід іменників
34
Рід іменників:  
чоловічий, жіночий, середній
	 	
1   Визначте, істоту якого роду називає 
кожний іменник.
	 	
3   Допишіть пари слів за зразком.
2   Прочита...

- **Grade 4, Сторінка 35**
  35
1. Розгляньте у групі однокласників таблицю. Дайте
відповіді  на  запитання  Читалочки.
Роди іменників
Чоловічий рід
(він, мій)
Жіночий рід
(вона, моя)
Середній рід
(воно, моє)
берег
кінь
батько
рі...

- **Grade 2, Сторінка 32**
  Утвори і прочитай слова. Назви одним словом.
маам
отат
дусьід
басябу
барт
састер
• Поміркуй, якими іншими словами ми називаємо сім’ю. 
Склади тематичну павутинку (на аркуші паперу).
Послухай пісню Нат...

- **Grade 2, Сторінка 30**
  БЕЗ СІМ’Ї НЕМА ЩАСТЯ НА ЗЕМЛІ 
Прочитай швидко. Вимовляй голосно виділений склад, 
мама 
матуся 
матінка
неня 
ненька 
ненечка
• Поміркуй, як ще можна назвати маму.
Послухай пісню Наталії Май «Мамочко...






---

## 4. Outline

Write **My Family** for the a1 track.

**Targets:** 1200–1800 words | 3+ callout boxes | **8–15 activities total** (required types + additional types to reach minimum) | 20 vocab items

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Вступ: Моя сім'я (Introduction: My Family)` (~250 words)
  - Введення базової лексики: мама, тато, брат, сестра (Державний стандарт §3.1). Питання «Хто це?» для ідентифікації членів родини.
  - Культурний контекст: Різниця між поняттями «сім'я» (ядерна родина, що живе разом) та «родина» (ширше коло родичів, лінія предків та походження).
- `## Презентація: Близька та розширена родина (Presentation: Immediate and Extended Family)` (~350 words)
  - Побудова речень через конструкцію «У мене є...» (Державний стандарт §4.2.1.1). Виправлення помилки-кальки з англійської «Я маю...», яка є менш природною для рівня А1.
  - Розширена родина (дідусь, бабуся, дядько, тітка). Культурний аспект: активна роль бабусь та дідусів у вихованні онуків в Україні та традиція проживання кількома поколіннями.
  - Узгодження присвійних займенників (мій, моя) з назвами родичів (Державний стандарт §4.2.2). Drill: запобігання помилці «мій сестра» через акцент на жіночому роді іменника «сестра».
- `## Презентація: Характеристики та стосунки (Presentation: Characteristics and Relationships)` (~300 words)
  - Терміни для подружжя: чоловік (husband/man) та дружина (wife). Розрізнення значень слова «чоловік» та вибір терміна «дружина» як нейтрального стандарту замість розмовного «жінка».
  - Опис зовнішності та характеру родичів з використанням прикметників (добрий, мудрий, темне волосся). Вживання форм давального відмінка для віку: «моєму братові...» (Державний стандарт §4.2.1.1).
- `## Практика: Звертання та спілкування (Practice: Address and Communication)` (~300 words)
  - Кличний відмінок як основа природного мовлення: навчання форм «мамо», «тату», «бабусю», «дідусю» для звертання до рідних (Державний стандарт §4.2.1.1).
  - Підготовка до теми свят (А1-33): обговорення сімейних зборів та традицій через вираз «збиратися всією родиною».
  - Створення та опис сімейного дерева: застосування знань про родинні зв'язки (онук, онука) та присвійні форми (батько Олени, мама Остапа).
- `## Підсумок` (~150 words) — recap + 3-4 self-check questions

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Вступ: Моя сім'я (Introduction: My Family) | 250+ |
| Презентація: Близька та розширена родина (Presentation: Immediate and Extended Family) | 350+ |
| Презентація: Характеристики та стосунки (Presentation: Characteristics and Relationships) | 300+ |
| Практика: Звертання та спілкування (Practice: Address and Communication) | 300+ |
| **Total** | **1200+ (aim for ~1440)** |

---

## 5. Guidelines

### Workflow
1. **Research first**: `search_text("Family vocabulary Possessives with family members", grade=3-5)` — find how textbooks teach this
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
**Required types:** match-up, match-up, fill-in, fill-in, match-up

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

</prompt>

## The Plan

<plan>
module: a1-049
level: A1
sequence: 49
slug: my-family
version: '2.0'
title: My Family
subtitle: Родина
focus: vocabulary
pedagogy: PPP
phase: A1.5 [Modals, Commands & Life]
word_target: 1200
objectives:
- Learner can name family members
- Learner can describe family relationships
- Learner can talk about their own family
- Learner can use possessives with family terms
- Learner can use basic vocative forms to address family members
content_outline:
- section: 'Вступ: Моя сім''я (Introduction: My Family)'
  words: 250
  points:
  - 'Введення базової лексики: мама, тато, брат, сестра (Державний стандарт §3.1). Питання «Хто це?» для ідентифікації членів
    родини.'
  - 'Культурний контекст: Різниця між поняттями «сім''я» (ядерна родина, що живе разом) та «родина» (ширше коло родичів, лінія
    предків та походження).'
- section: 'Презентація: Близька та розширена родина (Presentation: Immediate and Extended Family)'
  words: 350
  points:
  - Побудова речень через конструкцію «У мене є...» (Державний стандарт §4.2.1.1). Виправлення помилки-кальки з англійської
    «Я маю...», яка є менш природною для рівня А1.
  - 'Розширена родина (дідусь, бабуся, дядько, тітка). Культурний аспект: активна роль бабусь та дідусів у вихованні онуків
    в Україні та традиція проживання кількома поколіннями.'
  - 'Узгодження присвійних займенників (мій, моя) з назвами родичів (Державний стандарт §4.2.2). Drill: запобігання помилці
    «мій сестра» через акцент на жіночому роді іменника «сестра».'
- section: 'Презентація: Характеристики та стосунки (Presentation: Characteristics and Relationships)'
  words: 300
  points:
  - 'Терміни для подружжя: чоловік (husband/man) та дружина (wife). Розрізнення значень слова «чоловік» та вибір терміна «дружина»
    як нейтрального стандарту замість розмовного «жінка».'
  - 'Опис зовнішності та характеру родичів з використанням прикметників (добрий, мудрий, темне волосся). Вживання форм давального
    відмінка для віку: «моєму братові...» (Державний стандарт §4.2.1.1).'
- section: 'Практика: Звертання та спілкування (Practice: Address and Communication)'
  words: 300
  points:
  - 'Кличний відмінок як основа природного мовлення: навчання форм «мамо», «тату», «бабусю», «дідусю» для звертання до рідних
    (Державний стандарт §4.2.1.1).'
  - 'Підготовка до теми свят (А1-33): обговорення сімейних зборів та традицій через вираз «збиратися всією родиною».'
  - 'Створення та опис сімейного дерева: застосування знань про родинні зв''язки (онук, онука) та присвійні форми (батько
    Олени, мама Остапа).'
vocabulary_hints:
  required:
  - 'мама (mom) — рідна мама, молода мама; найвища частотність, клична форма: мамо!'
  - 'тато (dad) — рідний тато, мій тато; клична форма: тату!'
  - брат (brother) — старший брат, молодший брат, рідний брат
  - сестра (sister) — старша сестра, молодша сестра, рідна сестра
  - 'дідусь (grandfather) — мудрий дідусь, мій дідусь; клична форма: дідусю!'
  - 'бабуся (grandmother) — добра бабуся; клична форма: бабусю!'
  - син (son) — мій син, єдиний син
  - донька (daughter) — моя донька, доросла донька
  recommended:
  - сім'я (family) — велика сім'я, моя сім'я; ядерний підрозділ
  - родина (family) — вся родина, збиратися родиною; ширший контекст роду та зв'язків
  - чоловік (husband) — мій чоловік; важливо розрізняти зі значенням 'man'
  - дружина (wife) — моя дружина; стандартний нейтральний термін
  - дядько (uncle) — добрий дядько
  - тітка (aunt) — рідна тітка
  - онук (grandson) — мій онук
  - онука (granddaughter) — маленька онука
activity_hints:
- type: match-up
  focus: Family member names
  items: 25
- type: match-up
  focus: Match relationships
  items: 20
- type: fill-in
  focus: Complete family descriptions
  items: 15
- type: fill-in
  focus: Describe your family
  items: 6
- type: match-up
  focus: Vocative forms (Nominative → Vocative)
  items: 10
- type: fill-in
  focus: Calling family members (vocative practice)
  items: 8
connects_to:
- a1-50 (Holidays and Traditions)
- a1-34 (Checkpoint Core Grammar)
prerequisites:
- a1-20 (Mine and Yours)
- a1-48 (Body and Health)
persona:
  voice: Patient Supportive Tutor
  role: Family Genealogist
grammar:
- Family vocabulary
- Possessives with family members
- Genitive for relationships (батько + name)
- Basic vocative forms (мамо, тату, бабусю, дідусю)
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