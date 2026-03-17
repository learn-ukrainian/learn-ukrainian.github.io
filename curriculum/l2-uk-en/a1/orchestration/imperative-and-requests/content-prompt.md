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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/imperative-and-requests-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/imperative-and-requests.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("Imperative mood formation Ти/Ви forms", grade=3-5)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 46
**Previous module:** Must and Want

**Cumulative vocabulary (464 words):**
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
потрібний, дно, треба, спа

**Grammar already taught (149 topics):**
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

**Coming next (module after this):** Pain expressions (У мене болить + body part), Health vocabulary, Impersonal necessity (треба + infinitive)
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 20 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- читати/читай (to read / read!) — Читайте текст; classroom command
- писати/пиши (to write / write!) — Пишіть у зошиті; classroom command
- сказати/скажи (to say / say!) — Скажіть, будь ласка; irregular к→ж mutation
- дати/дай (to give / give!) — Дайте, будь ласка; irregular short form
- іти/іди (to go / go!) — Ідіть сюди; movement command
- слухати/слухай (to listen / listen!) — Слухайте уважно; classroom command
- дивитися/дивись (to look / look!) — Дивіться на дошку; classroom command
- стояти/стій (to stand / halt!) — Стійте! Не рухайтеся!; safety command

**Recommended** (use in your content to reach the vocabulary target):
- показати/покажи (to show / show!) — Покажіть, будь ласка; service context
- допомогти/допоможи (to help / help!) — Допоможіть!; emergency context
- взяти/візьми (to take / take!) — Візьміть це; irregular stem
- чекати/чекай (to wait / wait!) — Зачекайте хвилинку; patience context

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
- **Imperative Mood in Ukrainian: grammar and practice | 70+ VERBS!** (Let's Learn Ukrainian)
  URL: https://www.youtube.com/watch?v=q9WyAebMk2U
  Score: 1.0 -- This video directly teaches the imperative mood in Ukrainian, covering its grammar, formation, and usage with multiple verb examples. This is perfectly aligned with the module's topic.
  Suggested placement: After section Наказовий спосіб (Imperative mood) - as a primary instructional resource for the grammar topic.
  Key excerpt: У цьому відео ми поговоримо про наказові способи українською мовою. Ми використовуємо дієслова в наказовому способі, коли ми комусь кажемо, просимо, благаємо, рекомендуємо або наказуємо щось зробити.

- **ULP 3-112 Майстер-клас з приготування вареників – How to cook varenyky + Imperative mood of the s...** (Ukrainian Lessons)
  URL: https://www.youtube.com/watch?v=YTz0inrG1KE
  Score: 0.5 -- The video uses the imperative mood to give instructions for cooking varenyky, but it does not directly teach the grammar point. It could serve as an example of imperative use in a natural context.
  Suggested placement: After section Практика (Practice) - to demonstrate real-world usage of imperative commands in a cultural context.
  Key excerpt: обов'язково надішліть мені фотографію добре а зараз починаємо майстер-клас який ви будете слухати сьогодні досить довгий.

- **ULP 3-114 Майстер-клас з писанкарства – How to make pysanky + Imperative mood of the verbs in the...** (Ukrainian Lessons)
  URL: https://www.youtube.com/watch?v=T_qU1xDThtY
  Score: 0.5 -- Similar to Candidate 1, this video uses imperative forms within instructions for making pysanky. It's a natural application of the mood rather than a direct grammar lesson.
  Suggested placement: After section Практика (Practice) - as another example of imperative commands in a cultural activity.
  Key excerpt: слухайте розповідь Олени білуус це знову ж таки буде досить складний текст але я впевнена ви впораєтесь з ним якщо послухаєте кілька разів.


### Podcast Episodes
*Each episode has audio + transcript + vocabulary list -- recommend to students as supplementary listening.*

- **ULP S3 Ep111: Birthday presents + Imperative mood in Ukrainian**
  URL: https://www.ukrainianlessons.com/episode111/
  Relevance: 1.0
  Topics: grammar, verbs, imperative, conjugation, phrases

- **ULP S3 Ep112: How to cook varenyky + Imperative mood of the second person plural**
  URL: https://www.ukrainianlessons.com/episode112/
  Relevance: 1.0
  Topics: grammar, verbs, imperative, conjugation, plural

- **ULP S3 Ep113: Ukrainian traditional embroidery masterclass + More about the Imperative mood in Ukrainian**
  URL: https://www.ukrainianlessons.com/episode113/
  Relevance: 1.0
  Topics: grammar, verbs, imperative, conjugation, phrases

- **ULP S3 Ep114: How to make pysanky + Imperative mood of the verbs in the first person plural (Let’s…)**
  URL: https://www.ukrainianlessons.com/episode114/
  Relevance: 1.0
  Topics: grammar, verbs, imperative, conjugation, plural

- **3 S3 Ep111: ULP 3-111 Подарунки на День народження – Birthday presents + Imperative mood in Ukrainian**
  URL: https://www.ukrainianlessons.com/lesson/111/
  Relevance: 0.7
  Topics: ULP, Season 3


### Textbook References
- **Grade 11, Сторінка 55**
  55
Наказовий спосіб дієслова
У формі 2-ї особи множини паралельно із закінченням -іть можна вживати й закін-
чення -іте (воно хоч і рідше вживане, але нормативне): ходіть — ходіте, несіть — несіте, 
л...

- **Grade 7, Сторінка 85**
  82
Зауважте!
У дієсловах наказового способу пишемо м’який знак у кінці слова та 
складу після д, т, з, с, ц, л, н:  лізь, лізьте, будь, будьте, глянь, гляньте, 
занось, заносьте.
2.	 Утворіть усі можл...

- **Grade 7, Сторінка 80**
  77
Зауважте!
Дієслова умовного та наказового способу, на відміну від дійсного, не ма-
ють часових форм. 
2.	 Запишіть дієслова в три колонки: 1) дійсного способу; 2) умовного спо-
собу; 3) наказового ...

- **Grade 7, Сторінка 54**
  А. Перепишіть речення, уставивши, де потрібно, м’який знак. Б. Надпишіть над кожним дієсловом його форму. було
кажу
принести...

- **Grade 11, Сторінка 54**
  54
Морфологічна норма
§ 17. НАКАЗОВИЙ СПОСІБ ДІЄСЛОВА
СПОСТЕРЕЖЕННЯ
1.	 Прочитайте уривки з пісень і виконайте завдання.
Давай виключим світло і будем мовчати
Про то, що не можна словами сказати (А. К...






---

## 4. Outline

Write **Imperative and Requests** for the a1 track.

**Targets:** 1200–1800 words | 3+ callout boxes | **8–15 activities total** (required types + additional types to reach minimum) | 20 vocab items

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Наказовий спосіб (Imperative mood)` (~300 words)
  - Formation rule: 2nd person singular and plural. Remove -ти ending, add imperative suffix. Pattern depends on conjugation type and stem final consonant.
  - Ти-form vs Ви-form: читай (ти) → читайте (ви), пиши (ти) → пишіть (ви), говори (ти) → говоріть (ви). Ви-form adds -те/-іть for politeness and plurality.
  - Learner error: confusing imperative with infinitive. "Читати!" is a sign/rule (read!), "Читай!" is a personal command. Context determines which form to use.
- `## Вісім обов'язкових дієслів (Eight required verbs)` (~300 words)
  - State Standard §4.2.4.2 required verbs: читай(те) (read!), пиши(те) (write!), скажи(те) (say/tell!), дай(те) (give!), іди(те) (go!), слухай(те) (listen!), дивись(те) (look!), стій(те) (stop!).
  - Classroom commands context: Читайте текст (Read the text). Пишіть у зошиті (Write in your notebook). Слухайте уважно (Listen carefully). Дивіться на дошку (Look at the board).
  - Irregular stems: дати → дай (not *дайи), сказати → скажи (consonant mutation к→ж), стояти → стій (stem vowel change). These must be memorized as set forms.
- `## Ввічливе прохання (Polite requests)` (~250 words)
  - Будь ласка as universal softener: Дайте, будь ласка (Please give). Position flexibility: beginning, middle, or end of sentence. Most common after the verb.
  - Прошу вас + infinitive: Прошу вас сісти (Please sit down). More formal than будь ласка. Used in official or service contexts.
  - Indirect request pattern: Чи не могли б ви...? (Could you...?). Preview of conditional mood. Чи не могли б ви повторити? (Could you repeat?). Most polite option available at A1.
- `## Заборони (Prohibitions)` (~175 words)
  - Negative imperative: Не + imperative form. Не кури! (Do not smoke!). Не біжи! (Do not run!). Не чіпай! (Do not touch!). Same formation as positive, with не.
  - Preview connection to a1-55 (Prohibitions and Signs): Distinction between personal prohibition (Не чіпай!) and public sign prohibition (Не торкатися! — infinitive form). Both mean "do not touch" but differ in register.
- `## Практика (Practice)` (~175 words)
  - Command drills: Teacher gives situation, learner produces correct imperative form. Focus on the 8 required verbs in varied contexts.
  - Polite request formation: Upgrading direct commands to polite requests. Дай → Дайте, будь ласка → Чи не могли б ви дати? Politeness escalation practice.
- `## Підсумок` (~150 words) — recap + 3-4 self-check questions

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Наказовий спосіб (Imperative mood) | 300+ |
| Вісім обов'язкових дієслів (Eight required verbs) | 300+ |
| Ввічливе прохання (Polite requests) | 250+ |
| Заборони (Prohibitions) | 175+ |
| Практика (Practice) | 175+ |
| **Total** | **1200+ (aim for ~1440)** |

---

## 5. Guidelines

### Workflow
1. **Research first**: `search_text("Imperative mood formation Ти/Ви forms", grade=3-5)` — find how textbooks teach this
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
**Required types:** match-up, quiz, fill-in, true-false

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
