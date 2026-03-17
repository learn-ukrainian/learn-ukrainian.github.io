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
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/a1/research/the-accusative-ii-people-research.md` | Background knowledge, engagement hooks |
| `/Users/krisztiankoos/projects/learn-ukrainian/curriculum/l2-uk-en/plans/a1/the-accusative-ii-people.yaml` | Objectives, vocabulary_hints (source of truth) |
| `/Users/krisztiankoos/projects/learn-ukrainian/claude_extensions/quick-ref/A1.md` | Level constraints, immersion band |
| `schemas/activities-a1.schema.json` | Activity field definitions (`additionalProperties: false`) |

### RAG Tools

| Tool | When | Example |
|------|------|---------|
| `search_text` | Find textbook pedagogy | `search_text("Accusative for animate nouns Masculine animate: accusative = genitive", grade=3-5)` |
| `verify_words` | Check words exist in VESUM | `verify_words(["книга", "великий"])` |
| `verify_lemma` | Get inflected forms | `verify_lemma("книга")` |
| `query_pravopys` | Spelling/grammar rules | `query_pravopys("апостроф")` |

### What the Learner Already Knows

**Modules completed before this one:** 25
**Previous module:** The Accusative I: Things

**Cumulative vocabulary (315 words):**
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
такий, інший, кожний, сам, дівчина, година, хвилина, тиждень, місяць, рік
ранок, вечір, вчасно, понеділок, вівторок, середа, четвер, п'ятниця, субота, неділя
зараз, пізно, рано, січень, мати, чути, брати, купувати, гречка, пакет
шукати, знаходити, відкривати, проблема, голос

**Grammar already taught (83 topics):**
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

**Coming next (module after this):** Accusative prepositions (в/у, на, за, через, про), Direction expressions with Accusative, Preposition semantics and contrast
You may use related words as fixed phrases for foreshadowing, but do NOT explain the grammar rule.

**Rule:** Do not re-explain grammar already taught. Do not use vocabulary words the learner hasn't seen unless you introduce them explicitly.

### Vocabulary



**Target vocabulary** (from the plan — teach and use these). Include ALL required words. Include recommended words by using them naturally in your content — they count toward your 20 vocabulary target:

### Vocabulary from Plan (MANDATORY — include ALL required items)

**Required** (MUST appear in vocabulary YAML):
- брат (brother) — рідний брат, старший/молодший брат; diminutive: братик (High frequency)
- сестра (sister) — рідна сестра, старша/молодша сестра; diminutive: сестричка (High frequency)
- друг (friend m.) — найкращий друг, вірний друг; implies deep trust/soulmate connection
- подруга (friend f.) — вірна подруга, давня подруга
- мама (mother) — люба мама, чекаю маму; diminutive: матуся (Very high frequency)
- тато (father) — бачу тата, знаю тата; diminutive: татусь (Very high frequency)
- лікар (doctor) — викликати лікаря, чекати лікаря; professions often follow the animate rule
- вчитель (teacher) — знати вчителя, бачу вчителя (State Standard §4.2.1.1 example)

**Recommended** (use in your content to reach the vocabulary target):
- кіт (cat) — grammatically animate (бачу кота); focus on Acc=Gen ending
- пес (dog) — grammatically animate (маю пса); irregular stem change (пес -> пса)
- студент (student) — знати студента, бачу студента
- колега (colleague) — чекати колегу; note: declines like feminine nouns
- сусід (neighbor) — знати сусіда, бачу сусіда
- дитина (child) — люблю дитину, бачу дитину

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
- **Як звати твого тата? - What is your father’s name? #ukrainianlessons #ukrainianlanguage** (Ukrainian with Olha)
  URL: https://www.youtube.com/watch?v=dhGtS3yWrX0
  Score: 0.9 -- This video directly demonstrates the use of the Accusative case with animate nouns (people) by asking about family members' names, which is highly relevant to the module's topic.
  Suggested placement: After Презентація (Presentation) -- directly reinforces the grammar of accusative case for people through practical examples.
  Key excerpt: Як звати твого тата? Як звати твого дядька? Як звати твого дідуся? Як звати твою маму?

- **Ukrainian for beginners: MY FAMILY | Where do you live? Possessive pronouns, Verbs TO BE, TO HAVE** (Ukrainian with Olha)
  URL: https://www.youtube.com/watch?v=-f6UHBi8nU0
  Score: 0.8 -- The video explicitly mentions touching on accusative cases and focuses on family vocabulary, which includes animate nouns (people) relevant to the module's topic.
  Suggested placement: After Презентація (Presentation) or Культурний контекст (Cultural Context) -- reinforces family vocabulary and introduces accusative in context.
  Key excerpt: And with we will touch a little accusative and locative cases. And the topic of today's lesson is family. We will learn vocabulary of family members and how to describe your family and relations between the members of the families.

- **ULP 2-66 | Спогади + Місцевий відмінок з місцями | Sharing memories + Locative case with places** (Ukrainian Lessons)
  URL: https://www.youtube.com/watch?v=XaGcakHYd2Y
  Score: 0.6 -- The video provides a general recap of all cases, including the Accusative case ('знахідний відмінок'), but does not specifically focus on animate nouns or people, making it tangentially related.
  Suggested placement: After Розминка (Warm-up) -- provides a useful recap of grammatical cases before diving into specifics.
  Key excerpt: accusative Case знахідний знахідний відмінок from thebзнайти to find We have looked at each of those


### Podcast Episodes
*Each episode has audio + transcript + vocabulary list -- recommend to students as supplementary listening.*

- **ULP S1 Ep33: Talking about books in Ukrainian — Accusative case of people**
  URL: https://www.ukrainianlessons.com/episode33/
  Relevance: 0.7
  Topics: grammar, cases, accusative

- **FMU Ep15: Grammar point: Accusative case / Direct object in Ukrainian**
  URL: https://www.ukrainianlessons.com/fmu15/
  Relevance: 0.6
  Topics: grammar, cases, accusative, review

- **ULP S1 Ep32: Shopping for clothes — Accusative case in Ukrainian**
  URL: https://www.ukrainianlessons.com/episode32/
  Relevance: 0.5
  Topics: grammar, cases, accusative, vocabulary, clothing

- **ULP S2 Ep56: Asking for advice + Accusative case in Ukrainian**
  URL: https://www.ukrainianlessons.com/episode56/
  Relevance: 0.5
  Topics: grammar, cases, accusative, adjectives, phrases

### Blog Articles & Guides
- **ULP 1-33 Talking about books in Ukrainian – Accusative case of people** (ukrainianlessons.com)
  URL: https://www.ukrainianlessons.com/lesson/33/
  Relevance: 0.8


### Textbook References
- **Grade 5, Сторінка 160**
  157
Пробачив братові, подякував бабусі, дорікати одноклас-
нику, кепкувати з невдахи, насміхатися з однолітка, до-
класти зусиль, потребує допомоги, оволодівати знаннями. 
ІІ. Виберіть із поданих два ...

- **Grade 4, Сторінка 66**
  66
2. Пригадай назви відмінків іменників і їхні питання. Перевір
себе за таблицею на с. 38. Познач відмінок іменників
у  записаних  словосполученнях.
2
3. Розглянь таблицю відмінювання прикметників.
3...

- **Grade 6, Сторінка 109**
  109
109
§ 55.  Відмінювання іменників, що мають форму тільки множини
2. Форму тільки множини мають обидва іменники рядка
А	 іменини, пахощі
Б	 ночви, будинки
В	 острови, Піренеї
Г	 парфуми, аромати
3....

- **Grade 5, Сторінка 214**
  214
Відомості із синтаксису й пунктуації.  Додаток
Відмінок
Запитання
Приклад іменника
Непрямі 
відмінки
Родовий
Давальний
Знахідний
Орудний
Місцевий 
Кличний 
Немає питання
2.	 Провідмінюйте слова др...

- **Grade 7, Сторінка 169**
  166
2.	 «Лінгвістичне спостереження». Які особливості вживання прийменни-
ка по?
1.	 Прочитайте речення та виконайте завдання.
Сестра сміється з брата.
Сестра сміється над братом. 
А.	 У якому реченні...






---

## 4. Outline

Write **The Accusative II: People** for the a1 track.

**Targets:** 1200–1800 words | 3+ callout boxes | **8–15 activities total** (required types + additional types to reach minimum) | 20 vocab items

## REQUIRED H2 Sections and Points (MANDATORY)

Your output MUST use these EXACT H2 headings and cover EVERY bullet point listed under each section. Missing sections or missing points = review FAIL. Use EXACT vocabulary from the points (e.g., if the plan says *айтішник*, use *айтішник*, not a synonym).

- `## Розминка (Warm-up)` (~175 words)
  - Введення метафори 'Живі слова' (Heart Words) проти 'Кам'яних слів' (Stone Words) для візуалізації категорії істот/неістот
  - Контраст між Accusative I (things) та Accusative II (people) — чому граматика змінюється, коли ми говоримо про живих істот
  - Посилання на Державний стандарт §4.2.1.1: компетенція розрізнення відмінкових форм для назв людей (син, тато, учитель, мама, сестра)
- `## Презентація (Presentation)` (~375 words)
  - Логіка чоловічого роду: знахідний = родовий (Acc=Gen) — чоловічі назви істот 'жадібні' до закінчень, щоб відрізнятися від об'єктів (бачу сина, тата, учителя)
  - Логіка жіночого роду: збереження стандартного закінчення знахідного відмінка (-у/-ю), ігноруючи правило 'Acc=Gen' (бачу маму, сестру)
  - Тварини як люди: пояснення, що домашні улюбленці (кіт, пес) граматично є істотами і потребують закінчень знахідного-родового (бачу кота, пса)
  - Специфіка м'якої та мішаної груп для назв професій (учителя, лікаря) згідно з параграфом §4.2.1.1
- `## Культурний контекст (Cultural Context)` (~250 words)
  - Глибинне значення слова 'друг' в українській культурі — відмінність між близьким другом (soulmate) та просто знайомим (acquaintance)
  - Експресивна роль демінутивів (пестливих форм) у сімейному колі — використання форм 'матуся', 'татусь', 'братик', 'сестричка' дорослими як знак тепла та близькості
  - Ввічливе звертання та запитання про людей в українському соціумі: використання назв професій та імен
- `## Типові помилки та практика (Common Errors and Practice)` (~275 words)
  - Learner error: 'The Masculine Animate Trap' — залишення назви істоти в називному відмінку (напр. 'Я бачу брат' замість правильного 'Я бачу брата')
  - Learner error: 'Feminine Overthinking' — помилкове застосування правила Acc=Gen до жіночого роду (напр. 'Я бачу сестри' замість 'Я бачу сестру')
  - Learner error: 'Animal Animacy Confusion' — сприйняття тварин як неістот через порівняння з іншими мовами (напр. 'Я маю кіт' замість 'Я маю кота')
  - Трансформаційні вправи: перетворення речень з неістотами (бачу стіл) на речення з людьми (бачу студента)
- `## Вироблення навичок та підсумок (Production and Summary)` (~125 words)
  - Опис своєї родини та друзів з використанням дієслів 'любити', 'знати', 'чекати' (Я люблю свою матусю і тата)
  - Діалог-знайомство: обговорення друзів та колег (Ти знаєш мого найкращого друга Андрія?)
  - Підсумковий чек-лист: коли Accusative дорівнює Genitive, а коли ні

### Section Word Budgets

| Section | Minimum |
|---------|---------|
| Розминка (Warm-up) | 175+ |
| Презентація (Presentation) | 375+ |
| Культурний контекст (Cultural Context) | 250+ |
| Типові помилки та практика (Common Errors and Practice) | 275+ |
| Вироблення навичок та підсумок (Production and Summary) | 125+ |
| **Total** | **1200+ (aim for ~1440)** |

---

## 5. Guidelines

### Workflow
1. **Research first**: `search_text("Accusative for animate nouns Masculine animate: accusative = genitive", grade=3-5)` — find how textbooks teach this
2. **Write content** following the outline and lesson arc below
3. **Verify as you write**: `verify_words` on any Ukrainian word you're unsure about
4. **Create activities** from your content
5. **Verify activities**: batch `verify_words` on all activity items

### Beginner Lesson Arc

1. **WELCOME** — warm greeting, set context
2. **PREVIEW** — "By the end of this module, you'll be able to..."
3. **PRESENT** — the main content sections
4. **PRACTICE** — examples, dialogues, reading practice
5. **CELEBRATE** — in the final `## Вироблення навичок та підсумок (Production and Summary)` section, tell learners what they can now do

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
**Required types:** fill-in, match-up, fill-in

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
- **MUST end with `## Вироблення навичок та підсумок (Production and Summary)`** with self-check questions

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