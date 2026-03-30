<!-- version: 1.0.0 | updated: 2026-03-27 -->
# V6 Review Prompt — Adversarial Module Quality Review

You are reviewing a Ukrainian language module for quality. The writer used a different AI model — your job is adversarial: find every flaw. Be harsh but fair. Every issue you catch now prevents 54 bad modules later.

## Module Under Review

**Module:** 35: Checkpoint: Places (A1, A1.5 [Places])
**Writer:** Gemini Pro
**Word target:** 1200

## Plan (source of truth)

<plan_content>
module: a1-035
level: A1
sequence: 35
slug: checkpoint-places
version: '1.2'
title: 'Checkpoint: Places'
subtitle: Can you navigate a Ukrainian city?
focus: review
pedagogy: PPP
phase: A1.5 [Places]
word_target: 1200
objectives:
- Demonstrate correct use of euphony (у/в, і/й, з/із/зі)
- Use locative for location (Де?) and accusative for direction (Куди?)
- Navigate using city vocabulary, transport, and directions
- Answer Звідки? with genitive chunks
- Combine all A1.5 skills in connected urban scenarios
dialogue_situations:
- setting: 'Video-calling a friend while walking through Одеса (Odesa) — showing:
    Дерибасівська вулиця (f), Потьомкінські сходи (pl, Potemkin Stairs), порт (m,
    port), пляж (m, beach). Describing where you are, where you''re going.'
  speakers:
  - Мешканець (filming)
  - Онлайн-друг (watching)
  motivation: Consolidation with вулиця(f), сходи(pl), порт(m), пляж(m)
content_outline:
- section: Що ми знаємо? (What Do We Know?)
  words: 200
  points:
  - 'Self-check covering M28-M34: Can you apply euphony rules? (M28) Can you say where
    things are? (M29) Can you name city places? (M30) Can you say where you''re going?
    (M31) Can you use transport? (M32) Can you give directions? (M33) Can you say
    where you''re from? (M34)'
- section: Читання (Reading Practice)
  words: 250
  points:
  - 'A short Ukrainian text using vocabulary from M28-M34. Content: a tourist navigates
    Kyiv — asks for directions, takes metro, finds a museum, describes where they''re
    from and where they''re going. Uses euphony, locative, accusative, genitive chunks,
    transport.'
- section: Граматика (Grammar Summary)
  words: 200
  points:
  - 'Key patterns from A1.5: 1. Euphony: у/в, і/й, з/із/зі (M28) 2. Де? → в/на + locative:
    в школі, на роботі (M29) 3. Куди? → в/на + accusative: у школу, на роботу (M31)
    4. Звідки? → з + genitive chunk: з України, з роботи (M34) 5. Transport: автобусом,
    на метро (M32) 6. Directions: прямо, направо, наліво (M33) 7. City places with
    correct prepositions (M30)'
- section: Діалог (Connected Dialogue)
  words: 300
  points:
  - 'A tourist in Kyiv asks for help: — Вибачте, я з Канади. Де тут музей? — Музей
    у центрі. Ідіть на метро до станції Хрещатик. — А як дістатися від метро? — Вийдіть
    і йдіть направо. Музей на площі. — Дякую! А потім я хочу їхати у Львів. Де вокзал?
    — Вокзал далеко, їдьте на метро до станції Вокзальна. Uses all A1.5 skills in
    one realistic scenario.'
- section: Підсумок — Summary
  words: 250
  points:
  - 'A1.5 achievement summary: You can now navigate Ukrainian cities. You know euphony
    rules for natural speech. You can say WHERE something is (locative). You can say
    WHERE you''re GOING (accusative). You can say WHERE you''re FROM (genitive chunks).
    You can use transport and give directions. Next: A1.6 — Food and Shopping (ordering,
    buying, accusative for objects).'
vocabulary_hints:
  required: []
  recommended: []
activity_hints:
- type: quiz
  focus: 'Choose the correct question: Де? Куди? Звідки?'
  items: 8
  questions:
  - '... ти живеш? — У Києві. (Де / Куди / Звідки)'
  - '... ти йдеш? — У магазин. (Куди / Де / Звідки)'
  - '... ви? — Ми з Канади. (Звідки / Де / Куди)'
  - '... музей? — У центрі. (Де / Куди / Звідки)'
  - '... їде автобус? — На вокзал. (Куди / Де / Звідки)'
  - '... ти їдеш? — З роботи. (Звідки / Куди / Де)'
  - '... аптека? — Направо. (Де / Куди / Звідки)'
  - '... вони? — Зі США. (Звідки / Де / Куди)'
- type: fill-in
  focus: Complete the connected dialogue with correct forms
  items: 6
  blanks:
  - Вибачте, я {з Канади}. Де тут музей?
  - Музей {у центрі}. Ідіть на метро.
  - А як дістатися {від метро}?
  - Вийдіть і йдіть {направо}. Музей на площі.
  - Я хочу їхати {у Львів}. Де вокзал?
  - Вокзал далеко, їдьте {на метро}.
- type: group-sort
  focus: Sort phrases by case/function (Locative, Accusative, Genitive chunks)
  items: 9
  groups:
  - name: Локація (Де?)
    items:
    - у школі
    - на площі
    - в центрі
  - name: Напрямок (Куди?)
    items:
    - на роботу
    - у Львів
    - в Канаду
  - name: Походження (Звідки?)
    items:
    - з України
    - зі США
    - з роботи
- type: quiz
  focus: 'Euphony rules check: у/в, і/й, з/із/зі'
  items: 8
  questions:
  - Брат ... сестра (і / й)
  - Вона живе ... Львові (у / в)
  - Я йду ... школи (зі / з)
  - Він ... Києві (у / в)
  - Мама ... тато (і / й)
  - Ми ... України (з / із)
  - Я ... кімнаті (в / у)
  - Вона ... США (зі / з)
connects_to:
- a1-036 (Food and Drink)
prerequisites:
- a1-034 (Where From?)
grammar:
- 'Review: locative for location (Де?)'
- 'Review: accusative for direction (Куди?)'
- 'Review: genitive chunks for origin (Звідки?)'
- 'Review: euphony and transport'
register: розмовний
references:
- title: Synthesis of M28-M34 content
  notes: No new material — review and integration of A1.5 phase.

</plan_content>

## Generated Content

<generated_module_content>
## Що ми знаємо? (What Do We Know?)

Seven modules of A1.5 are behind you — euphony, locative case, city vocabulary, accusative for direction, transport, giving directions, and saying where you're from. Before moving to the next phase, test yourself. Can you apply euphony rules (**у/в**, **і/й**, **з/із/зі**)? Can you say where something is? Where you're going? Where you're from? Can you name city places and use transport words?

Try answering these questions out loud:

- **Де ти живеш?** (Where do you live?) — **У Києві.** (In Kyiv.)
- **Куди ти йдеш?** (Where are you going?) — **У магазин.** (To the store.)
- **Звідки ти?** (Where are you from?) — **Я з Канади.** (I'm from Canada.)
- **Як ти їдеш?** (How do you travel?) — **Автобусом.** (By bus.)
- **Де музей?** (Where is the museum?) — **Музей у центрі.** (The museum is in the centre.)
- Choose **і** or **й**: **Брат ___ сестра.**
- Choose **у** or **в**: **Я живу ___ Львові.**

If those answers came quickly, you're ready for this checkpoint. If some felt tricky, that's exactly what this module is for. We'll bring all seven patterns together — euphony (M28), location (M29), city vocabulary (M30), direction (M31), transport (M32), directions (M33), and origin (M34) — into one connected practice. By the end, you'll see how these pieces form a complete toolkit for navigating a Ukrainian city.

## Читання (Reading Practice)

Read this short text about a tourist in Kyiv. Every sentence uses patterns from M28–M34. See how many you can spot — euphony choices, locative for location, accusative for direction, genitive for origin, transport, and directions.

> **Мене звати Томас.** *(My name is Tomas.)* **Я з Канади.** *(I'm from Canada.)* **Зараз я у Києві.** *(Right now I'm in Kyiv.)*
>
> **Сьогодні я гуляю по місту.** *(Today I'm walking around the city.)* **Вранці я їду на метро до станції Хрещатик.** *(In the morning I take the metro to Khreshchatyk station.)* **Метро у Києві дуже зручне.** *(The metro in Kyiv is very convenient.)*
>
> **Я виходжу зі станції.** *(I exit the station.)* **Іду направо.** *(I go right.)* **Попереду — Хрещатик, головна вулиця міста.** *(Ahead is Khreshchatyk, the main street of the city.)* **Я йду прямо.** *(I walk straight.)* **Бачу красивий парк.** *(I see a beautiful park.)* **У парку є фонтани й лавки.** *(In the park there are fountains and benches.)*
>
<div class="dialogue">

<div class="dialogue-line"><span class="speaker">Потім я питаю перехожого:</span> *(Then I ask a passerby:)* **«Вибачте, де Національний музей?»** *(«Excuse me, where is the National Museum?»)* **Він відповідає:** *(He answers:)* **«Музей на площі. Ідіть прямо, потім наліво.»** *(«The museum is on the square. Go straight, then left.»)*</div>

</div>
>
> **Я іду до музею.** *(I go to the museum.)* **Потім хочу їхати до Лаври.** *(Then I want to go to the Lavra.)* **Сідаю в автобус.** *(I get on a bus.)* **Їду до зупинки Арсенальна.** *(I ride to Arsenalna stop.)* **Від зупинки до Лаври пішки — п'ять хвилин.** *(From the stop to the Lavra on foot — five minutes.)*
>
> **Увечері я у готелі.** *(In the evening I'm at the hotel.)* **Телефоную в Канаду:** *(I call Canada:)* **«Я зараз у Києві! Хочу їхати у Львів!»** *(«I'm in Kyiv now! I want to go to Lviv!»)*

Now check your understanding:

1. **Звідки Томас?** (Where is Tomas from?) — **З Канади.** (From Canada.)
2. **Куди він їде вранці?** (Where does he go in the morning?) — **На метро до станції Хрещатик.** (By metro to Khreshchatyk station.)
3. **Де музей?** (Where is the museum?) — **На площі.** (On the square.)

Notice the patterns at work: **з Канади** (genitive — where from), **у Києві** (locative — where), **на метро** (transport), **зі станції** (euphony — **зі** before **ст-**), **направо** and **прямо** (directions), **до Лаври** (direction — where to), **в автобус** (onto transport). Томас uses every A1.5 skill in one short story — combining patterns naturally rather than thinking about grammar rules one at a time.

<!-- INJECT_ACTIVITY: quiz-de-kudy-zvidky -->

## Граматика (Grammar Summary)

Here are the seven key patterns from A1.5 — your personal grammar card for navigating Ukrainian cities. Each pattern answers a different question.

**Pattern 1: Euphony (M28)** — Ukrainian alternates certain sounds for smooth speech.

- **у/в**: **Я у школі.** (I'm at school.) / **Він в офісі.** (He's in the office.)
- **і/й**: **Брат і сестра.** (Brother and sister.) / **Ольга й Андрій.** (Olha and Andriy.)
- **з/із/зі**: **Я з України.** (I'm from Ukraine.) / **Зі США.** (From the USA.)

<!-- INJECT_ACTIVITY: quiz-euphony -->

**Pattern 2: Де? → в/на + locative (M29)** — where something IS.

- **У школі.** (At school.) **На роботі.** (At work.) **В центрі.** (In the centre.) **На площі.** (On the square.)

**Pattern 3: Куди? → в/на + accusative (M31)** — where you're GOING.

- **У школу.** (To school.) **На роботу.** (To work.) **У Львів.** (To Lviv.) **На площу.** (To the square.)

Compare: **у школі** (at school — you're there) vs. **у школу** (to school — you're heading there). Same preposition, different case ending.

**Pattern 4: Звідки? → з/із/зі + genitive (M34)** — where you're FROM.

- **З України.** (From Ukraine.) **Зі США.** (From the USA.) **З роботи.** (From work.) **З Канади.** (From Canada.)

**Pattern 5: Transport (M32)** — how you travel.

- **Їхати автобусом.** (To go by bus.) **На метро до станції Хрещатик.** (By metro to Khreshchatyk station.)

:::tip
Transport hubs (**станція**, **вокзал**, **зупинка**) always take **на**: **на станції**, **на вокзалі**, **на зупинці** — never **в станції**.
:::

**Pattern 6: Directions (M33)** — imperative forms for giving directions.

- **Ідіть прямо.** (Go straight.) **Направо.** (To the right.) **Наліво.** (To the left.) **Вийдіть тут.** (Exit here.)

**Pattern 7: City places with prepositions (M30)** — each noun pairs with its own preposition.

- **У музеї.** (In the museum.) **На вокзалі.** (At the train station.) **В парку.** (In the park.) **На площі.** (On the square.) **У готелі.** (In the hotel.) **У бібліотеці.** (In the library.)

<!-- INJECT_ACTIVITY: group-sort-cases -->

## Діалог (Connected Dialogue)

Марко is visiting Kyiv for the first time. He stops a local, Оксана, near a metro entrance to ask for help. Watch how all seven A1.5 patterns appear in one real conversation.

<div class="dialogue">

<div class="dialogue-line"><span class="speaker">Марко:</span> Вибачте! Ви місцева? *(Excuse me! Are you local?)*</div>

<div class="dialogue-line"><span class="speaker">Оксана:</span> Так, я з Києва. Що шукаєте? *(Yes, I'm from Kyiv. What are you looking for?)*</div>

<div class="dialogue-line"><span class="speaker">Марко:</span> Я з Канади. Я тут уперше. Де Національний музей? *(I'm from Canada. This is my first time here. Where is the National Museum?)*</div>

<div class="dialogue-line"><span class="speaker">Оксана:</span> Музей у центрі, на вулиці Грушевського. Їдьте на метро до станції Арсенальна. Потім пішки. *(The museum is in the centre, on Hrushevskyi Street. Take the metro to Arsenalna station. Then walk.)*</div>

<div class="dialogue-line"><span class="speaker">Марко:</span> А де станція метро? *(And where is the metro station?)*</div>

<div class="dialogue-line"><span class="speaker">Оксана:</span> Ось тут, за рогом. Ідіть прямо, потім направо. Там — вхід. *(Right here, around the corner. Go straight, then right. The entrance is there.)*</div>

<div class="dialogue-line"><span class="speaker">Марко:</span> Добре! А після музею я хочу їхати у Львів. Де вокзал? *(OK! After the museum I want to go to Lviv. Where is the train station?)*</div>

<div class="dialogue-line"><span class="speaker">Оксана:</span> Центральний вокзал далеко. Їдьте на метро до станції Вокзальна. *(The central station is far. Take the metro to Vokzalna station.)*</div>

<div class="dialogue-line"><span class="speaker">Марко:</span> Скільки їхати? *(How long is the ride?)*</div>

<div class="dialogue-line"><span class="speaker">Оксана:</span> Хвилин двадцять. Вокзал біля станції. *(About twenty minutes. The station is right by the stop.)*</div>

<div class="dialogue-line"><span class="speaker">Марко:</span> А де тут кафе? *(Where is a café around here?)*</div>

<div class="dialogue-line"><span class="speaker">Оксана:</span> Кафе на площі Незалежності. Це одна зупинка на метро. *(There's a café at Independence Square. It's one metro stop.)*</div>

<div class="dialogue-line"><span class="speaker">Марко:</span> Дякую! *(Thanks!)*</div>

<div class="dialogue-line"><span class="speaker">Оксана:</span> Будь ласка! Гарної подорожі! *(You're welcome! Have a good trip!)*</div>

</div>

Every A1.5 pattern appeared naturally. **Де музей?** — locative: **у центрі**. Where to? — **у Львів** (accusative). Where from? — **з Канади**, **з Києва** (genitive). Transport — **на метро до станції**. Directions — **прямо**, **направо**. City places — **на площі**, **біля станції**, **за рогом**. Seven patterns, one conversation.

Now try it yourself. Imagine you're video-calling a friend while walking through **Одеса** (Odesa). Describe what you see:

- **Я зараз на Дерибасівській вулиці.** (I'm on Derybasivska Street now.)
- **Іду до порту.** (I'm heading to the port.)
- **Потім хочу на пляж.** (Then I want to go to the beach.)
- **Я з [your city].** (I'm from [your city].)

Use at least five of the seven patterns from this module.

<!-- INJECT_ACTIVITY: fill-in-dialogue -->

## Підсумок — Summary

You've completed A1.5 — Places. Here's what you can now do in Ukrainian:

- ✅ **Euphony (M28)** — You choose **у/в**, **і/й**, **з/із/зі** automatically based on surrounding sounds
- ✅ **Location (M29)** — **Де?** → в/на + locative: **у школі**, **на роботі**, **в центрі**
- ✅ **City vocabulary (M30)** — **вулиця**, **площа**, **парк**, **музей**, **вокзал**, **аптека**, **бібліотека**
- ✅ **Direction (M31)** — **Куди?** → в/на + accusative: **у школу**, **у Львів**, **на площу**
- ✅ **Transport (M32)** — **їхати автобусом**; **на метро до станції Хрещатик**
- ✅ **Giving directions (M33)** — **ідіть прямо**, **направо**, **наліво**, **вийдіть**
- ✅ **Origin (M34)** — **Звідки?** → з/із/зі + genitive: **з України**, **зі США**, **з Канади**

In A1.6 — Food and Shopping, you'll learn how to order food, buy things at a market, and use the accusative case for objects — not just directions. You'll say things like **Я хочу каву** (I want coffee), **Дайте хліб** (Give me bread), and **Скільки коштує?** (How much does it cost?). The accusative you practiced for direction (**у школу**) now works for objects too — a natural extension of what you already know.

**Deterministic word count: 1572 words** (calculated by pipeline, do NOT estimate manually)

</generated_module_content>

---

## Review Protocol

### Step 1: Scan for linguistic errors

Scan the Ukrainian text for errors. Report ONLY problems found — do not echo correct text.

**Four SEPARATE checks (these are four different problems):**
1. **Russianisms** — Russian words used instead of Ukrainian (кот→кіт, хорошо→добре, конечно→звичайно, сейчас→зараз)
2. **Surzhyk** — mixed Russian-Ukrainian forms (шо→що, чо→чому, тіпа→типу)
3. **Calques** — literal translations from Russian that sound wrong in Ukrainian (приймати душ→брати душ, приймати рішення→ухвалювати рішення)
4. **Paronyms** — similar-sounding words with different meanings used incorrectly (тактична≠тактовна, ефектний≠ефективний)

**Also check:**
- Russian characters (ы, э, ё, ъ) — these must NEVER appear
- Incorrect gender assignment or case endings
- Factually wrong claims about Ukrainian phonetics, grammar, or culture

**Authority hierarchy for verification (check in this order):**
1. VESUM — does this word/form exist? POS? Gender? (415K lemmas)
2. Правопис 2019 — is it spelled correctly? Orthography rules.
3. Горох — stress position, word frequency, synonyms.
4. Антоненко-Давидович «Як ми говоримо» — is this natural Ukrainian or a calque/Russicism?
5. Грінченко «Словарь» — etymology, original meaning.

**Online fallbacks (if RAG/tools are unavailable):**
- VESUM: https://vesum.com.ua/
- Правопис 2019: https://2019.pravopys.net/
- Горох: https://goroh.pp.ua/
- Антоненко-Давидович: https://www.ukrlib.com.ua/books/printit.php?tid=4002
- Грінченко: https://hrinchenko.com/
- Словник.ua (aggregator): https://slovnyk.me/

**VESUM verification data is provided at the end of this prompt.** Use it to verify word existence before flagging linguistic errors. If a word is marked ✓ in the VESUM data, it EXISTS in Ukrainian — do not flag it as an error. If a word is marked ✗ (NOT IN VESUM), investigate further — it may be a proper noun, a compound, or genuinely wrong.

**CRITICAL: Your pre-training is contaminated by Russian.** Do NOT trust your instincts about Ukrainian words. If you are not 100% certain a word/form/usage is wrong, you MUST flag it as `[NEEDS RAG VERIFICATION]` instead of marking it as a definitive error. Wrong review findings cause wrong fixes. A false positive in the review is worse than a missed error.

If no errors found, state: "No linguistic errors found."

**Do NOT check for stress marks** — stress annotation is handled by a separate deterministic tool after the review phase. Their absence is correct.

### Step 2: Check exercises

The writer places `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. A separate ACTIVITIES step generates structured YAML exercises (`activities/{slug}.yaml`) that are injected at these markers during PUBLISH.

Check the markers and any inline exercises:
- Does each marker appear AFTER the relevant teaching section? (exercise should test what was just taught)
- Do marker IDs match the plan's `activity_hints`? (each hint should have a corresponding marker)
- Are markers spread evenly through the module? (not clustered at the end)
- For seminar modules: DSL exercise blocks (:::quiz, :::fill-in) may appear inline — check their logic

For each exercise (DSL or marker), check:
- Does the exercise test what was just taught? (language skill, not content recall)
- Is the logic correct? (correct answers are actually correct, distractors are plausible but wrong)
- Can a learner complete this with the knowledge taught so far in this module?
- Does the exercise match one of the plan's `activity_hints` in type and focus?

Also check: Are there enough exercise markers/blocks total? The plan's `activity_hints` specifies the expected count.

**Note:** Exercise content is generated by a separate tool from YAML. If exercise LOGIC is wrong, flag it. If the FORMAT looks unusual (React components, YAML structure), that is expected.

### PROOF OF ABSENCE — mandatory before claiming ANYTHING is missing

**Before you claim a word, symbol, notation, or plan point is MISSING from the content, you MUST search for it.** Use your MCP tools (`verify_words`, `search_text`) or carefully re-read the specific section where it should appear.

Rules:
- If you claim "[•] notation is missing" — you must have searched the content for `[•]` and confirmed 0 occurrences
- If you claim "vocabulary word X is missing" — you must have searched for that exact word
- If you claim "plan point Y was not covered" — you must quote which section you expected it in and confirm it's not there
- **NO CLAIMS OF ABSENCE WITHOUT EVIDENCE.** Your tokenizer can miss special characters like [•], [–], [=], «», and other non-alphanumeric symbols. Do not trust a quick scan.
- Euphony alternation (у/в, і/й) is a MINOR stylistic issue, NEVER a critical error. Both forms are attested in published Ukrainian literature.

**A false finding wastes an entire rebuild cycle. Be precise.**

### Step 3: Score on 9 dimensions

Rate each dimension 1-10 with SPECIFIC evidence (cite the section/paragraph, quote the actual text).

| # | Dimension | Weight | What to check |
|---|-----------|--------|---------------|
| 1 | **Plan adherence** | 15% | DEDUCT for: missing content_outline points, section word budgets off by >10%, plan references not cited, vocabulary from plan absent from prose. REWARD for: every plan point covered with specific examples, correct section pacing, textbook references integrated naturally. Quote the plan point that was missed or covered. |
| 2 | **Linguistic accuracy** | 15% | All Ukrainian correct? No Russianisms/Surzhyk/calques? Correct phonetic descriptions? Gender/case correct? |
| 3 | **Pedagogical quality** | 15% | DEDUCT for: grammar rules presented as bare lists without examples, concepts taught before prerequisite knowledge, >100 words of English theory without a Ukrainian example, bare vocabulary lists instead of contextualized introduction. REWARD for: PPP flow (situation→pattern→practice), 3+ examples per grammar point, textbook pedagogy (Большакова, Захарійчук), grammar scope respected. |
| 4 | **Vocabulary coverage** | 10% | All required vocab from plan used naturally in prose? Recommended vocab included? New words introduced in context, not as lists? |
| 5 | **Exercise quality** | 15% | DEDUCT for: all correct answers at the same index position, trivially easy exercises (1:9 group sort ratios, every answer is the same word), exercises that test content recall instead of language skill, items fewer than plan's activity_hints count, exercises placed before the concept is taught. REWARD for: varied answer positions, plausible distractors, exercises testing what was just taught, matching plan's activity_hints type and focus exactly. |
| 6 | **Engagement & tone** | 10% | DEDUCT for: motivational openers ("Numbers unlock the real Ukraine!"), meta-commentary ("Let us look at...", "Let us now explore..."), generic enthusiasm ("incredibly melodic", "hugely important"), telling instead of showing ("You now possess...", "You have unlocked..."), gamified language ("unlocked the ability"), corporate-speak ("precision and accuracy"), "The magic of...", any sentence that could apply to any language course unchanged. REWARD for: specific cultural details, natural dialogues, humor, concrete examples, teacher demonstrating rather than lecturing about how great the content is. |
| 7 | **Structural integrity** | 5% | DEDUCT for: missing H2 headings from plan, duplicate summary sections, meta-commentary sections ("Content notes:"), word count outside target range, stray tags or formatting artifacts. REWARD for: clean markdown, all sections present and ordered correctly, word count in range. |
| 8 | **Cultural accuracy** | 5% | Decolonized (Ukrainian on its own terms, never "like Russian but...")? Factually correct claims about Ukrainian? Respectful representation? |
| 9 | **Dialogue & conversation quality** | 10% | DEDUCT for: purely transactional exchanges ("Do you have X? Yes."), dialogues where one speaker interrogates the other, anonymous em dashes instead of named speakers, stilted/textbook-robotic phrasing. REWARD for: natural multi-turn conversations, real situations (searching for keys, ordering at a cafe, meeting a friend), culturally appropriate responses, named speakers with distinct voices. |

**Note:** Vocabulary tables (словник), video embeds, and external resource links are added by a downstream ENRICH step — do NOT penalize their absence or quality. If you see a vocabulary table with wrong translations, missing words, or formatting issues, that content was NOT written by the writer — it was generated deterministically by the ENRICH step. Do NOT flag словník problems as linguistic errors or deduct points from the writer. Report them separately under "ENRICH issues" in your findings (informational only, not scored).

### Step 4: Output raw scores

Output ONLY the raw 1-10 scores in the table below. Do NOT calculate the weighted total — the pipeline script handles the math deterministically. Just write your per-dimension scores.

### Step 5: List findings

**CRITICAL RULE: If you mention ANY error, mistake, or inaccuracy in the evidence column of your scores table, you MUST also list it as a structured finding below AND include it in your `<fixes>` block.** Identifying an error in evidence but not outputting a finding+fix means the error ships to learners. This is a language curriculum — every error you identify must be fixed. No exceptions.

For every issue found, provide:
```
[DIMENSION] [SEVERITY: critical/major/minor]
Location: [specific section/paragraph — quote the actual text]
Issue: [what's wrong]
Fix: [exactly how to fix it]
```

Severity guide:
- **Critical** = factual/linguistic error that teaches wrong Ukrainian (wrong form, wrong rule, wrong example). Module cannot ship.
- **Major** = quality below standard but not factually wrong (weak explanation, awkward phrasing, missing examples).
- **Minor** = polish item (tone, word choice, style).

**Any factual or linguistic error is CRITICAL, not minor.** A wrong syllable division, a wrong phonetic claim, a contradictory grammar rule — these are critical because learners will memorize them as truth.

### Step 6: Verdict

Base your verdict on the **severity of findings** — the pipeline calculates the weighted score separately.

| Verdict | Condition |
|---------|-----------|
| **PASS** | Zero findings mentioning errors/mistakes/inaccuracies. All dimensions ≥9. |
| **REVISE** | Has findings with fixes. Any dimension <9 with identified errors = REVISE, not PASS. |
| **REJECT** | Fundamental structural/pedagogical problems requiring rewrite. |

### Step 7: Fix it yourself (REVISE only)

If your verdict is **REVISE**, you MUST output a `<fixes>` block with exact find/replace pairs. The pipeline applies these deterministically — no LLM regeneration, no rewriting from scratch.

Rules for fixes:
- Each fix is a YAML entry with `find:` (exact text from the module) and `replace:` (corrected text)
- The `find` string must be an EXACT substring of the module content — copy-paste it
- Keep fixes minimal — change only what's wrong, preserve surrounding text
- Do NOT fix словник/vocabulary tables (those are generated by a downstream tool)
- For word count issues: add content as a new `insert_after:` entry instead of find/replace

---

## Output Format

```
## Linguistic Scan
[errors found, or "No linguistic errors found"]

## Exercise Check
[placeholder inventory and issues]

## Scores
| Dimension | Score | Evidence |
|-----------|-------|----------|
| 1. Plan adherence | X/10 | [specific evidence from the text] |
| ... | ... | ... |

## Findings
[list all findings with dimension/severity/location/issue/fix]

## Verdict: PASS / REVISE / REJECT
[justification — reference both score gate and severity gate]

<fixes>
- find: "exact text from module"
  replace: "corrected text"
- find: "another exact problem"
  replace: "the fix"
</fixes>
```

**The `<fixes>` block is REQUIRED for REVISE verdicts.** Without it, the pipeline cannot apply your fixes. For PASS verdicts, omit the `<fixes>` block. For REJECT verdicts, the module needs a full rebuild — `<fixes>` is optional.


<vesum_verification>
The following Ukrainian words from the content were verified against VESUM (415K lemmas). Use this data to check linguistic claims — do NOT guess about words.

Verified: 142 words | Not found: 13 words

Words NOT in VESUM (may be errors, proper nouns, or valid words missing from dict):
  ✗ Андрій — NOT IN VESUM
  ✗ Грушевського — NOT IN VESUM
  ✗ Дерибасівській — NOT IN VESUM
  ✗ Канади — NOT IN VESUM
  ✗ Канаду — NOT IN VESUM
  ✗ Києва — NOT IN VESUM
  ✗ Львові — NOT IN VESUM
  ✗ Львів — NOT IN VESUM
  ✗ Одеса — NOT IN VESUM
  ✗ Оксана — NOT IN VESUM
  ✗ Ольга — NOT IN VESUM
  ✗ Томас — NOT IN VESUM
  ✗ Хрещатик — NOT IN VESUM

All 142 other words are confirmed to exist in VESUM.

</vesum_verification>

## Verification Tools (MCP)

You have MCP tools to VERIFY claims in the content. Use them to cite evidence:

**Core Verification:**
- `mcp__rag__verify_words` — batch-verify Ukrainian words against VESUM (409K lemmas)
- `mcp__rag__verify_lemma` — full declension/conjugation for a lemma
- `mcp__rag__search_style_guide` — **HIGH PRIORITY.** Check for calques/Russianisms (Антоненко-Давидович)
- `mcp__rag__query_r2u` — Russian→Ukrainian equivalents. Confirm Russicism alternatives.
- `mcp__rag__query_pravopys` — verify orthography rules (Правопис 2019)

**Content Quality:**
- `mcp__rag__query_cefr_level` — verify vocabulary is level-appropriate (PULS, 5.9K words)
- `mcp__rag__search_definitions` — exact Ukrainian definitions (СУМ-11, 127K entries)
- `mcp__rag__search_etymology` — historical forms, etymology (Грінченко, 67K entries)
- `mcp__rag__search_idioms` — verify idioms are authentic Ukrainian (25K entries)
- `mcp__rag__search_synonyms` — suggest better word choices (Ukrajinet, 122K synsets)
- `mcp__rag__query_grac` — check collocations and frequency in GRAC corpus (2B tokens)

**Reference:**
- `mcp__rag__search_text` — check how textbooks teach the topic (Grades 1-11)
- `mcp__rag__search_literary` — verify literary references against primary sources
- `mcp__rag__query_wikipedia` — fact-check historical/cultural claims

**Evidence standard:** A review that says "this might be a Russicism" is WEAK. A review that says "`search_style_guide` confirms 'приймати участь' is a calque — correct form: 'брати участь'" is STRONG. Cite tool results.
