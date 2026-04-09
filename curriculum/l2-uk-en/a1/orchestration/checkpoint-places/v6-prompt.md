

---

## Your Writing Identity

**You are: Lead Ukrainian Instructor.** Your persona is *The Patient Guide*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **35: Checkpoint: Places** (A1, A1.5 [Places]).

**Target: 1200–1800 words** of prose (Ukrainian examples count toward word total, headings and exercise placeholders do not).

---

## Step 1: Pacing Plan (output this FIRST)

Before writing any content, output a `<pacing_plan>` block. Evaluate each section from the plan and commit to a word budget. This prevents frontloading early sections and rushing later ones.

```
<pacing_plan>
Section 1 "Title": ~XXX words — [1-sentence content focus]
Section 2 "Title": ~XXX words — [1-sentence content focus]
...
Summary: ~150 words
Total: 1200+ words
</pacing_plan>
```

Then begin writing the module content. Follow your own pacing plan — each section must hit its word budget (±10%).

---

## 9 Hard Rules

1. **IMMERSION TARGET: 20-35% Ukrainian** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if immersion is outside this range. For A1 early modules, the learner cannot read Cyrillic — English must dominate. For A2+, Ukrainian must carry a significant share — add Ukrainian Reading Practice blocks, dialogues, and example paragraphs to reach the target. Too little Ukrainian fails audit just as much as too much.
2. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
3. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
4. **You are a warm, encouraging teacher.** Natural teacher phrasing ("Let us look at...", "Have you noticed...") is fine. What to AVOID: self-congratulatory openers ("Welcome to A2! Congratulations!"), gamified language ("You have unlocked...", "You now possess..."), and empty filler sentences that add words but zero information. Every sentence should teach something specific to Ukrainian.
5. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
6. **Place exercise markers only** — do NOT write exercises directly. Place `<!-- INJECT_ACTIVITY: {id} -->` markers where exercises should appear. A separate pipeline step generates the actual exercises from the plan's activity_hints.
7. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
8. **Hit the word target** — you MUST write 1200–1800 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
9. **NO archaic, obsolete, or rare words** — use only modern standard Ukrainian. Do not use words marked as archaic (застаріле) or dialectal in dictionaries. Example: use «кін» not «кон», use «пом'якшені» not «м'якшені». When in doubt, choose the common modern form. Your pre-training contains Russian-influenced archaic forms — verify unfamiliar words.
10. **EVERY module MUST end with `## Підсумок`** — this is the last H2 section before the file ends. It contains a self-check recap. If you forget this section, the audit REJECTS the module and you waste a retry. Write it LAST, after all other sections.

**Note:** Do NOT add stress marks (´) to any Ukrainian word — a deterministic tool handles this after you write.

## Exercise Placement — Markers Only

**Do NOT write exercises directly.** A separate pipeline step (ACTIVITIES) generates all exercises from the plan's `activity_hints`. Your job is to place markers showing WHERE exercises belong.

### How It Works

1. Read the plan's `activity_hints` — each entry has an `id`, `type`, and `focus`
2. After the relevant teaching section, place an injection marker
3. The ACTIVITIES step reads your prose + the plan hints and generates complete exercises

### Marker Format

Place markers after key teaching sections. Each marker corresponds to ONE `activity_hints` entry from the plan:

```
<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->
```

Rules:
- Use the EXACT `id` from the plan's `activity_hints` — do not invent new IDs
- Place the marker right after the prose that teaches the concept the exercise tests
- Spread markers evenly throughout the module — never cluster them
- If the plan has 4 activity hints, you should place 4 markers in your prose

### Example

If the plan says:
```yaml
activity_hints:
  - id: quiz-sounds-vs-letters
    type: quiz
    focus: "Distinguish звук from літера"
  - id: match-false-friends
    type: match-up
    focus: "Match false friend Cyrillic letters to real sounds"
```

Your prose should contain (after the relevant sections):
```
[...prose about sounds and letters...]

<!-- INJECT_ACTIVITY: quiz-sounds-vs-letters -->

[...prose about false friend letters...]

<!-- INJECT_ACTIVITY: match-false-friends -->
```

### What NOT to Do

- Do NOT write `:::quiz`, `:::fill-in`, `:::match-up`, or any DSL exercise blocks
- Do NOT write exercise questions, answers, or options — the ACTIVITIES step handles all of this
- Do NOT invent marker IDs — use only IDs from the plan's `activity_hints`

---

## Plan

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

---

## Pre-Verified Facts (from MCP tools — use these, do NOT guess)

A verification step already called VESUM, textbooks, Правопис, and style guide tools. The results below are GROUND TRUTH. Use them:
- If a word is marked ❌ NOT IN VESUM — do NOT use it
- If a textbook excerpt is provided — use that pedagogy
- If a calque is flagged — use the correct alternative
- If CEFR says a word is above target — find a simpler synonym

You do NOT need to call tools yourself — the facts are already verified.

<pre_verified_facts>
## VESUM Verification
- Confirmed: музей, вокзал, центр, станція, площа, школа, робота, прямо, направо, наліво, автобус, метро, Київ, Львів, Україна, Канада, вибачте, ідіть, вийдіть, їдьте.
- Not found: All words from the plan were found in VESUM.

## Grammar Rules
- Euphony у/в: Правопис §23 — Use 'у' between consonants (Десь у житі), at the start of a sentence before a consonant (У лісі), or before specific clusters like 'льв' (у Львові). Use 'в' between vowels or after a vowel before a consonant (Пішла в садок).
- Euphony і/й: Правопис §24 — Use 'і' between consonants (Він іде) or at the start of a sentence. Use 'й' between vowels (Ольга й Андрій) or between a vowel and a consonant (Вона йде).
- Preposition з/із/зі: Правопис §25 — Use 'з' before most consonants (З лісу). Use 'зі' before clusters starting with sibilants (зі Львова, зі школи). Use 'зо' with certain numbers and 'мною'.

## Calque Warnings
- їхати на метро: OK — While "їхати метро" (instrumental) is possible, "на метро" is widely used and acceptable for A1.
- на право/на ліво: Calque/Error — Must be written as one word "направо" and "наліво" when used as adverbs.
- від метро: OK — Correct use of preposition "від" with genitive for distance/origin.

## CEFR Check
- музей: A1 — Target level confirmed.
- вокзал: A1 — Target level confirmed.
- центр: A1 — Target level confirmed.
- метро: A1 — Target level confirmed.
- направо/наліво: A1 — Target level confirmed.
</pre_verified_facts>


## Wiki Teaching Brief — Your Authoritative Source

**This is your primary teaching material.** The wiki article below was compiled from real Ukrainian school textbooks, literary sources, and verified references. It contains the correct terminology, paradigm tables, teaching sequences, and examples for this module. Your job is to TRANSFORM this into engaging, level-appropriate content — not to copy it verbatim.

**How to use the wiki article:**
1. **Adopt the Ukrainian terminology.** If the article says «складоподіл», you write «складоподіл» — never CVCCV or "syllable division rules" paraphrased from English phonology. If it says «відкритий склад», you write «відкритий склад» — never "open syllable type."
2. **Follow the teaching sequence.** If the article shows: sound model → syllable → word → sentence, follow that progression. Do not rearrange or substitute your own.
3. **Use the article's examples as your foundation.** Authentic examples from textbooks beat invented ones. Use the article's examples and expand with your own that follow the same patterns.
4. **Synthesize and teach, don't summarize.** You are a teacher, not a summarizer. Take the facts from the article and weave them into engaging explanations with dialogues, situations, and practice. The article tells you WHAT to teach — you decide HOW to teach it for the target level.
5. **Your pre-training is contaminated by Russian and English linguistics.** When the article contradicts your instinct, the article wins. Ukrainian has its own phonetic categories (голосний/приголосний, дзвінкий/глухий, м'який/твердий) that do not map 1:1 to English or Russian. Use the Ukrainian categories.
6. **Do NOT copy paragraphs verbatim.** The article is reference material. Your output must be original teaching prose at the correct CEFR level, not a rephrased version of the article.

<knowledge_packet>
# Knowledge Packet: Checkpoint: Places
**Module:** checkpoint-places | **Track:** A1

<wiki_context>
## Compiled Wiki Knowledge

The following articles from the project wiki provide compiled knowledge relevant to this module. Use them as authoritative context — they were compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).

### Вікі: pedagogy/a1/checkpoint-places.md

# Педагогіка A1: Checkpoint Places



## Методичний підхід (Methodological Approach)

Навчання теми "Місця" для рівня А1 зосереджується на функціональності та негайному використанні. Українська педагогіка для молодших класів вводить цю концепцію через три фундаментальні питання, що визначають просторові відношення: **Де?**, **Куди?**, і **Звідки?**. Цей підхід дозволяє учням будувати прості, але граматично правильні фрази, ще до повного засвоєння відмінкової системи.

Основа методу — зв'язок дієслова з прислівником місця. У підручниках для 4-го класу прислівник визначається як частина мови, що відповідає на ці ключові питання (Source `4-klas-ukrmova-zaharijchuk_s0165`). Наприклад: `засяяло (де?) угорі`, `повіяв (звідки?) здалеку`. Це створює міцну інтуїтивну базу.

Спочатку вводяться прості діалоги, що моделюють природне спілкування. Вірш-діалог "Струмок" з підручника для 2-го класу є ідеальним зразком: запитання `— Ти куди біжиш, струмок?` отримує відповідь `— Через поле у ярок`, демонструючи зв'язок питання про напрямок (`куди?`) з відповіддю, що містить прийменник та місце (`у ярок`) (Source `2-klas-ukrmova-vashulenko-2019-2_s0095`). Такий підхід "запитання-відповідь" є центральним.

На цьому етапі граматика подається імпліцитно. Учень запам'ятовує готові конструкції (`я йду в парк`, `я живу в Києві`), а не таблиці відмінювання. Основна мета — щоб учень міг відповісти на прості запитання про своє місцезнаходження, походження та пункт призначення.

## Послідовність введення (Introduction Sequence)

1.  **Крок 1: Введення трьох ключових питань.** Пояснити різницю між статичним місцем (`Де?`), напрямком руху до місця (`Куди?`) та походженням з місця (`Звідки?`). Ці три питання є основою всієї теми (Sources `9-klas-ukrmova-zabolotnyi-2017_s0135`, `5-klas-ukrmova-avramenko-2022_s0161`). Почати з найпростіших прислівників:
    *   `Де ти?` — `Я тут.` / `Я вдома.`
    *   `Куди ти йдеш?` — `Я йду додому.`
    *   `Звідки ти?` — `Я з України.`

2.  **Крок 2: `Де?` + Прийменник `у/в` + Місцевий відмінок.** Це найчастотніше питання. Вводьте лексику місць (парк, магазин, школа) у готових фразах.
    *   `Я в парку.`
    *   `Він у магазині.`
    *   `Ми в школі.`
    На цьому етапі важливо, щоб учні розпізнавали закінчення `-у/-ю` та `-і` як маркер місця, а не вивчали правила їх утворення (Source `ext-other_blogs-46`).

3.  **Крок 3: `Куди?` + Прийменники `у/в/на` + Знахідний відмінок.** Важливо протиставити `Де?` і `Куди?`, щоб уникнути плутанини.
    *   Поясніть різницю між `у/в` (всередину, в закритий простір: `у магазин`, `у кінотеатр`) та `на` (на відкритий простір, подію або абстрактне поняття: `на вулицю`, `на роботу`, `на концерт`) (Source `ext-ulp_youtube-197`).
    *   Використовуйте практичні фрази: `Мені треба на вулицю Архипенка` (Source `ext-ulp_youtube-221`).

4.  **Крок 4: `Звідки?` + Прийменник `з/із/зі` + Родовий відмінок.** Це питання завершує тріаду.
    *   Почніть з країн та міст: `Я з Канади.`, `Він з Києва.`
    *   Використовуйте прості приклади з підручників: `З-під снігу` (Source `2-klas-ukrmova-vashulenko-2019-2_s0095`), `повернутися зі школи` (Source `7-klas-ukrmova-litvinova-2024_s0188`).

5.  **Крок 5: Інтеграція в діалогах.** Створюйте міні-діалоги, що комбінують усі три питання, щоб учні тренувалися переключатися між ними. Моделюйте діалоги за зразком простих вправ з підручників (e.g., `6-klas-ukrmova-betsa-2023_s0014`).

## Типові помилки L2 (Common L2 Errors)

Для англомовних учнів основні труднощі полягають у розрізненні понять, які в англійській мові передаються одним словом, та у засвоєнні відмінкової системи.

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| `Де ти йдеш?` | `Куди ти йдеш?` | Англійське "Where are you going?" змішує місце і напрямок. В українській мові для напрямку руху використовується виключно `Куди?`, тоді як `Де?` позначає статичне місцезнаходження. Плутанина цих питань є фундаментальною помилкою (Source `9-klas-ukrajinska-mova-voron-2017_s0094`). |
| `Я в Київ.` (відповідаючи на "Де ти?") | `Я в Києві.` | Англійська мова не використовує відмінки після прийменників. Учні часто забувають змінювати іменник, вживаючи називний відмінок. Необхідно наголосити, що прийменник `в/у` з питанням `Де?` вимагає місцевого відмінка (закінчення `-і` або `-у/-ю`) (Source `ext-other_blogs-46`). |
| `Я їду в робота.` | `Я їду на роботу.` | Неправильний вибір прийменника. Англійське "to" не розрізняє `в` (всередину) і `на` (на поверхню, на подію, на абстрактне поняття). Правило: `в/у` для закритих просторів (будинок, магазин), `на` для відкритих просторів, подій та понять (вулиця, концерт, робота, стадіон) (Source `ext-ulp_youtube-197`). |
| `Я говорю з друзями в телефон.` | `Я говорю з друзями по телефону.` | Прямий переклад з англійської "in the phone". Для позначення засобу зв'язку в українській мові використовується прийменник `по`. <!-- VERIFY --> |
| `Ми були в театр.` / `Ми були з школа.` | `Ми були в театрі.` / `Ми були зі школи.` | Це комбінація двох помилок: ігнорування відмінків та ігнорування правил милозвучності. Потрібно змінювати іменник (`театрі`) і використовувати правильний варіант прийменника (`зі`) перед сполученням приголосних для уникнення важковимовних конструкцій (Sources `5-klas-ukrmova-litvinova-2022_s0266`, `7-klas-ukrmova-zabolotnyi-2024_s0193`). |

## Деколонізаційні застереження (Decolonization Notes)

**Це обов'язковий розділ. Ігнорування цих пунктів призведе до створення неякісного, шкідливого контенту.**

1.  **Жодних порівнянь з російською мовою.** Категорично заборонено пояснювати українську граматику через російську. Фрази на кшталт "це як у російській, але..." є неприпустимими. Українська система відмінків, фонетика та лексика мають вивчатися як самостійне явище. Українська мова розвинулася безпосередньо з діалектів Давньої Русі, а не як відгалуження "спільної давньоруської мови", яка потім розпалася (Source `ext-istoria_movy-25`).
2.  **Тільки українська топоніміка.** Використовуйте виключно українські назви міст: `Київ`, `Львів`, `Харків`, а не їхні екзоніми (`Kiev`, `Lviv`, `Kharkiv`). Це питання поваги та політичної коректності.
3.  **Вимова — українська, не російська.** Наголошуйте на правильній вимові українських звуків, які часто спотворюються під впливом російської:
    *   `и` — це не російське `ы`.
    *   `і` — завжди чітке, не редукується.
    *   `г` — дзвінкий гортанний фрикативний, а не проривний `ґ`.
    *   `ч` — завжди твердий.
4.  **Лексична чистота.** Уникайте поширених русизмів для позначення місць. Навмисно вводьте правильні українські відповідники.
    *   `зупинка`, а не `остановка` (Source `5-klas-ukrmova-avramenko-2022_s0161`).
    *   `будь ласка`, а не `пожалуйста`.
    *   `наступний`, а не `слідуючий`.

## Словниковий мінімум (Vocabulary Boundaries)

На рівні А1 вводьте тільки високочастотну лексику, що стосується безпосереднього оточення учня.

#### Іменники (Nouns)

*   ★★★ (essential): `місто`, `вулиця`, `дім` (or `будинок`), `парк`, `школа`, `магазин`, `робота`, `Україна`, `Київ`, `дім`/`вдома`.
*   ★★ (useful): `аеропорт` (Source `ext-ulp_youtube-221`), `театр`, `кінотеатр` (Source `ext-ulp_youtube-197`), `ресторан` (Source `ext-ulp_youtube-197`), `готель` (Source `ext-ulp_youtube-221`), `лікарня` (Source `6-klas-ukrmova-betsa-2023_s0018`), `університет` (Source `6-klas-ukrmova-betsa-2023_s0018`), `зупинка` (Source `5-klas-ukrmova-avramenko-2022_s0161`), `центр`.
*   ★ (can wait): `бібліотека`, `музей`, `церква`, `пошта`, `банк`, `стадіон`, `аптека`.

#### Прислівники (Adverbs)

*   ★★★: `тут`, `там`, `вдома`, `далеко`, `близько`.
*   ★★: `праворуч` (справа), `ліворуч` (зліва) (Source `6-klas-ukrmova-betsa-2023_s0018`).
*   ★: `вгорі`, `внизу`, `поряд`.

#### Дієслова (Verbs)

*   ★★★: `бути`, `жити`, `йти`, `їхати`, `працювати`, `бачити`.
*   ★★: `знаходитися` (Source `ext-ulp_youtube-197`), `починатися` (Source `9-klas-ukrajinska-mova-voron-2017_s0094`), `любити`.

## Приклади з підручників (Textbook Examples)

Ці формати вправ є перевіреними в українській шкільній системі і повинні бути адаптовані для L2 учнів.

1.  **Вправа "Питання-Відповідь" (за моделлю діалогу).**
    Створіть простий діалог за зразком вірша "Струмок" (Source `2-klas-ukrmova-vashulenko-2019-2_s0095`).
    *   **Завдання:** Прочитайте діалог за ролями.
    *   `— Привіт, Оксано! Куди ти йдеш?`
    *   `— Привіт, Тарасе! Я йду в парк.`
    *   `— А звідки ти йдеш?`
    *   `— Я йду зі школи.`
    *   `— А де твій брат?`
    *   `— Він уже вдома.`

2.  **Вправа "Доповни речення" (з вибором).**
    На основі вправ на підрядні речення місця (Source `9-klas-ukrmova-zabolotnyi-2017_s0135`).
    *   **Завдання:** Виберіть правильне слово: `де`, `куди` або `звідки`.
    1.  `Це місто, ______ я живу.` (де)
    2.  `Покажи, ______ нам іти.` (куди)
    3.  `Я не знаю, ______ він приїхав.` (звідки)

3.  **Вправа "Виправ помилку".**
    Завдання на відпрацювання типових помилок.
    *   **Завдання:** Знайдіть і виправте помилки в реченнях.
    1.  `Я зараз в магазин.` -> `Я зараз в магазині.`
    2.  `Ми йдемо в робота.` -> `Ми йдемо на роботу.`
    3.  `Де ти їдеш?` -> `Куди ти їдеш?`

4.  **Вправа "Склади розповідь" (монолог).**
    Адаптація вправи на трансформацію діалогу в монолог (Source `6-klas-ukrmova-betsa-2023_s0018`, вправа 35).
    *   **Завдання:** Подивіться на картинку (зображення міста/парку). Розкажіть, що ви бачите. Використовуйте слова `тут`, `там`, `ліворуч`, `праворуч`.
    *   **Приклад:** `Це парк. Тут є дерева. Там є озеро. Ліворуч граються діти. Праворуч стоїть лавка.`

## Пов'язані статті

-   `pedagogy-a1-verbs-of-motion`
-   `grammar-locative-case`
-   `grammar-accusative-case-direction`
-   `grammar-prepositions-of-location`
-   `phonetics-euphony-rules`

---

### Вікі: pedagogy/a1/checkpoint-first-contact.md

# Педагогіка A1: Checkpoint First Contact



## Методичний підхід (Methodological Approach)

The Ukrainian pedagogical approach to teaching initial introductions is fundamentally communicative and context-driven. Even from the first lesson, the goal is to enable a learner to participate in a simple, formulaic dialogue (`діалог`). The core concepts of **ім'я** (first name), **прізвище** (surname), and **по батькові** (patronymic) are introduced as functional chunks of language needed to complete a real-world task, such as introducing oneself or filling out a simple form (Джерело: `4-klas-ukrayinska-mova-varzatska-2021-1_s0159`, `6-klas-ukrmova-zabolotnyi-2020_s0032`).

Ukrainian textbooks for early grades (1-2) establish this pattern by immediately presenting model dialogues. They use a "question-and-answer" format that is easy to memorize and adapt (Джерело: `5-klas-ukrmova-uhor-2022-1_s0107`, `6-klas-ukrmova-betsa-2023_s0014`). For example, the structure `— Як тебе звуть? — Мене звуть ... .` is presented as a fixed pair to be practiced with a partner (`Розіграйте діалог із сусідом / сусідкою за партою`) (Джерело: `6-klas-ukrmova-betsa-2023_s0014`).

Key methodological principles are:
1.  **Dialogue First:** The primary mode of instruction is the dialogue or poly-dialogue (`полілог`), where students learn by playing roles in a given situation (`Ситуація`) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0106`, `5-klas-ukrmova-avramenko-2022_s0011`). This makes the language immediately useful.
2.  **Structural Repetition:** Core phrases like `Мене звати...` and `Моє прізвище...` are drilled through repetition, not grammatical analysis at first. The focus is on automaticity. (Джерело: `5-klas-ukrmova-uhor-2022-1_s0106`).
3.  **Immediate Introduction of Capitalization:** From the outset, learners are shown that names, patronymics, and surnames are proper nouns written with a capital letter (`пишуть з великої літери`) (Джерело: `2-klas-ukrmova-kravcova-2019-1_s0070`, `2-klas-ukrmova-bolshakova-2019-2_s0023`). This is treated as a fundamental orthographic rule, not an advanced topic.
4.  **Implicit Grammar:** The accusative case in `Мене звати...` and the vocative case in direct address (`Оксано!`) are introduced implicitly through model phrases. Formal grammatical explanation is delayed until the learner is comfortable with the functional use of the phrases (Джерело: `5-klas-ukrmova-uhor-2022-1_s0106`, `6-klas-ukrmova-litvinova-2023_s0148`).

## Послідовність введення (Introduction Sequence)

The introduction of "first contact" language should follow a logical progression from simple to complex, mirroring the approach in Ukrainian native-speaker textbooks.

1.  **Step 1: Foundational Phrases & Pronouns.** Start with greetings (`Добрий день!`) and the core construction `Мене звати...` (My name is...). This immediately introduces the personal pronoun in the accusative case (`мене`) in a fixed, unanalyzed chunk (Джерело: `5-klas-ukrmova-uhor-2022-1_s0106`). Contrast `Як тебе звати?` (informal 'you') with `Як вас звати?` (formal/plural 'you').

2.  **Step 2: Adding the Surname.** Introduce the concept of `прізвище` (surname) with the parallel construction `Моє прізвище...` (My surname is...). Practice this in a simple dialogue format (Джерело: `6-klas-ukrmova-betsa-2023_s0014`, `5-klas-ukrmova-uhor-2022-1_s0107`). At this stage, learners practice asking and answering both questions in a sequence.

3.  **Step 3: The Vocative Case (Кличний відмінок) for Direct Address.** This is a critical element of natural Ukrainian speech and must be introduced early. Instead of just saying a name, learners must be taught to use the vocative form to call someone.
    *   For feminine names ending in `-а`, it changes to `-о`: `Анна → Анно!`, `Оксана → Оксано!` (Джерело: `6-klas-ukrmova-litvinova-2023_s0148`).
    *   For masculine names ending in a consonant, it changes to `-е`: `Тарас → Тарасе!`, `Павло → Павле!` (Джерело: `6-klas-ukrmova-litvinova-2023_s0148`).
    *   Introduce formal address with `пан/пані`: `пане Іваненку`, `пані Оксано` (Джерело: `6-klas-ukrmova-litvinova-2023_s0148`). This immediately elevates the learner's politeness and authenticity.

4.  **Step 4: Introducing the Patronymic (По батькові).** Explain that `по батькові` is a name derived from one's father's name and is used in formal or respectful situations. Show the full formal structure: `Прізвище, Ім’я, По батькові` (Джерело: `2-klas-ukrmova-bolshakova-2019-2_s0023`). Explain the common suffixes: `-ович` (masculine) and `-івна` (feminine) (Джерело: `6-klas-ukrmova-betsa-2023_s0016`). The goal at A1 is recognition, not productive use. Learners should understand what it is when they see it on a form or hear it in a formal introduction.

5.  **Step 5: Contextual Application.** Embed these skills in practical scenarios like booking a table (`Скажіть будь ласка ваше прізвище`) or making a doctor's appointment (`ваше прізвище ім'я і номер телефону будь ласка`) (Джерело: `ext-ulp_youtube-120`, `ext-ulp_youtube-58`). This reinforces the utility of the language.

## Типові помилки L2 (Common L2 Errors)

English speakers often make predictable errors when learning to introduce themselves. The curriculum should proactively address these.

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| `Я звати Анна.` | `Мене звати Анна.` | This is a direct translation of "I am called Anna." English speakers must learn the fixed Ukrainian construction which uses the accusative pronoun `мене` (me). (Джерело: `5-klas-ukrmova-uhor-2022-1_s0106`) |
| `Привіт, Марія.` | `Привіт, Маріє!` | Forgetting the vocative case (`Кличний відмінок`) in direct address. It sounds unnatural and blunt to a native speaker. The ending must change (`-ія` -> `-іє`, `-а` -> `-о`, consonant -> `-е`). (Джерело: `6-klas-ukrmova-litvinova-2023_s0148`) |
| `Моє ім'я є Тарас.` | `Моє ім'я — Тарас.` or `Мене звати Тарас.` | Overuse of the verb `бути` (`є`) where it's typically omitted in the present tense for identity statements. The dash (`—`) is the correct punctuation, or the `Мене звати` structure should be used. <!-- VERIFY --> |
| `Прізвище моє Ковальчук.` | `Моє прізвище — Ковальчук.` | Unnatural word order based on English. While grammatically possible, the standard, neutral response is `Моє прізвище...` (Джерело: `5-klas-ukrmova-uhor-2022-1_s0106`). |
| "What is your middle name?" (asking about `по батькові`) | "Як вас по батькові?" | Equating the patronymic with an Anglo-American "middle name." A middle name is a second personal name; a patronymic is a grammatical and cultural construct derived from the father's name. This distinction is crucial. (Джерело: `2-klas-ukrmova-bolshakova-2019-2_s0023`) |
| `Пан Шевченко...` (when ordering should be name first) | `Пан Тарас...` | In many formal contexts, the correct address is `пан/пані` + First Name. However, in official documents, it is always Last Name first (`прізвище, ім'я`) (Джерело: `11-klas-ukrajinska-mova-avramenko-2019_s0278`, `9-klas-ukrajinska-mova-avramenko-2017_s0211`). The brief should clarify the context. |

## Деколонізаційні застереження (Decolonization Notes)

Teaching Ukrainian from a decolonized perspective is non-negotiable. This is especially important in foundational topics where Russian-centric habits can form.

1.  **Teach Ukrainian on Its Own Terms:** Never introduce Ukrainian letters or sounds as "like the Russian X." Learners must build a clean Ukrainian phonetic and orthographic foundation from zero. Russian has different letters (e.g., `ы`, `э`) and different pronunciations for shared letters (e.g., `и`, `г`). Using Russian as a reference point pollutes the learning process from day one.
2.  **Patronymics are East Slavic, Not Russian:** Explicitly state that patronymics (`по батькові`) are a feature of Ukrainian, Belarusian, and Russian cultures. Frame it as a shared heritage, not a Russian import. Highlight the distinct Ukrainian suffixes (`-ович`, `-івна`) as seen in textbooks (Джерело: `6-klas-ukrmova-betsa-2023_s0016`).
3.  **Correct Transliteration:** Emphasize the official Ukrainian transliteration system (and the common informal one) which differs from Russian. Key examples: `Г` is `H`, not `G`; `И` is `Y`, not `I`; `І` is `I`. This prevents learners from writing Ukrainian names with Russian spelling conventions.
4.  **Surname Origins:** When discussing surnames, highlight authentic Ukrainian origins related to professions (`Коваль`, `Бондар`, `Гончар`), features, or Cossack history, not just those shared with Russian (Джерело: `2-klas-ukrmova-bolshakova-2019-2_s0025`, `3-klas-ukrainska-mova-vashulenko-2020-2_s0158`).

## Словниковий мінімум (Vocabulary Boundaries)

This vocabulary is the absolute essential minimum for the "First Contact" module.

*   **Іменники (Nouns):**
    *   ім'я ★★★ (first name)
    *   прізвище ★★★ (surname)
    *   по батькові ★★ (patronymic)
    *   учень / учениця ★★★ (student m/f)
    *   вчитель / вчителька ★★★ (teacher m/f)
    *   друг / подруга ★★ (friend m/f)
    *   пан / пані / панно ★★★ (Mr. / Mrs. / Miss)
    *   номер (телефону) ★★ (phone number)
*   **Дієслова (Verbs):**
    *   звати ★★★ (to be called)
    *   бути ★★★ (to be - often omitted in present)
    *   знати ★★ (to know)
    *   жити ★ (to live)
*   **Займенники (Pronouns):**
    *   я, ти, він, вона, ми, ви, вони ★★★ (Nominative: I, you, he, she, etc.)
    *   мене, тебе, його, її, нас, вас, їх ★★★ (Accusative: me, you, him, her, etc.)
    *   мій/моя/моє, твій/твоя/твоє ★★★ (my, your)
*   **Ключові фрази (Key Phrases):**
    *   Добрий день. / Привіт. ★★★
    *   Як тебе/вас звати? ★★★
    *   Мене звати... ★★★
    *   Як твоє/ваше прізвище? ★★★
    *   Моє прізвище... ★★★
    *   Дуже приємно. / Радий (рада) знайомству. ★★
    *   Так / Ні ★★★

## Приклади з підручників (Textbook Examples)

These exercises are models for the content writer, demonstrating the native Ukrainian pedagogical methodology.

1.  **Basic Dialogue Completion (from Source `6-klas-ukrmova-betsa-2023_s0014`)**
    *   **Task:** Побудуйте діалог за зразком. Запишіть. Розіграйте діалог із сусідом / сусідкою за партою.
    *   **Model:**
        > — Як тебе звуть?
        > — Мене звуть … .
        > — Як твоє прізвище?
        > — Моє прізвище … .
    *   **Pedagogical Value:** This simple, repetitive task builds automaticity for the most fundamental introductory exchange. It encourages active, paired practice.

2.  **Identifying Name Components (from Source `5-klas-ukrmova-uhor-2022-1_s0107`)**
    *   **Task:** Уточніть, де ім’я, де по батькові, де прізвище.
    *   **Model:**
        > — Франко — це ім’я?
        > — Ні, це прізвище. Його звати Іван Якович.
    *   **Pedagogical Value:** This exercise moves from simple production to comprehension and analysis. It teaches learners to differentiate between the three components of a full formal name and introduces the structure `Його звати...`.

3.  **Table Fill-in (from Source `2-klas-ukrmova-bolshakova-2019-2_s0023`)**
    *   **Task:** Заповни таблицю за зразком.
    *   **Input:** `Григоренко Святослав Андрійович, Телюк Наталія Григорівна, Шевченко Тарас Григорович.`
    *   **Table Structure:**
| Прізвище | Ім’я | По батькові |
| :--- | :--- | :--- |
| Бондар | Лариса | Вікторівна |
    *   **Pedagogical Value:** This is a classic exercise for reinforcing the structure and order of formal Ukrainian names and practicing reading/writing them correctly.

4.  **Contextual Role-Play (from Source `6-klas-ukrmova-zabolotnyi-2020_s0032`)**
    *   **Task:** Складіть діалог (6–8 реплік) в офіційно-діловому стилі... Ви прийшли записатися до бібліотеки. Повідомте мету свого візиту, а також на прохання бібліотекарки – своє прізвище та ім’я, дату народження, місце проживання (для оформлення картки читача).
    *   **Pedagogical Value:** This places the language skill in a highly realistic, official context (`офіційно-діловий стиль`). It moves beyond simple introductions to a multi-turn conversation where personal information is requested and provided for a clear purpose. This demonstrates the practical value of what has been learned.

## Пов'язані статті (Related Articles)

- `pedagogy/a1/alphabet`
- `pedagogy/a1/greetings-and-farewells`
- `grammar/nouns/vocative-case`
- `grammar/pronouns/personal-pronouns`
- `culture/names-and-address`
</wiki_context>

## Plan References

- 

</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Що ми знаємо? (What Do We Know?)` (~200 words)
- `## Читання (Reading Practice)` (~250 words)
- `## Граматика (Grammar Summary)` (~200 words)
- `## Діалог (Connected Dialogue)` (~300 words)
- `## Підсумок — Summary` (~250 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

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

HARD GRAMMAR RULES (audit will reject violations):
- Max 10 words per Ukrainian sentence (STRICT — count every word)
- ONLY 1 clause per sentence (no compound sentences)
- Dative case FORBIDDEN (no мені, тобі, йому, їй, вам, їм, -ові/-еві endings)
  Exception: нам is taught as decodable vocabulary in M1 (reading drill word, not grammar)
  Exception (M15 what-i-like): Dative forms мені/тобі/йому/їй/нам/вам/їм allowed
    ONLY in the fixed construction «Мені подобається + noun/infinitive». Teach as a memorized
    chunk — do NOT explain dative case rules or paradigms.
- Instrumental case FORBIDDEN (no з другом, з мамою, -ом/-ою/-ем/-ею endings)
  Exception: M37 introduces basic Instrumental 'з' (кава з молоком)
- NO subordinate clauses: який/яка/яке, що-clause, коли, якщо, тому що, бо, щоб, поки are ALL BANNED
- Only imperfective aspect verbs
- No participles
- Allowed cases: Nominative, Accusative, Locative (from M30), Genitive (basics), Vocative

### Pedagogy
- Start each section with a real situation or dialogue (PPP: Present → Practice → Produce)
- Every grammar rule needs 3+ Ukrainian examples with English translations
- Teach through PATTERNS, not rules: show examples first, then name the pattern
- Cultural context where relevant — this is Ukrainian, not generic L2
- Use vocabulary from the plan's vocabulary_hints. Function words (pronouns, conjunctions) are always allowed.

### Ukrainian Language Quality
- **Zero Russian**: No ы, э, ё, ъ. No Russian words (кот→кіт, хорошо→добре, конечно→звичайно)
- **Zero Surzhyk**: No шо→що, чо→чому, тіпа→типу
- **Zero calques**: No приймати душ→брати душ, приймати рішення→ухвалювати рішення
- **Zero paronyms**: тактична≠тактовна, ефектний≠ефективний — use the right word, not a similar-sounding one
- **Natural Ukrainian**: Write how a Ukrainian teacher would explain this to a student. Not robotic, not textbook-dry, not overly casual.

**Authority hierarchy (if uncertain about a word, check in this order):**
VESUM (does word exist?) → Правопис 2019 (spelling) → Горох (stress) → Антоненко-Давидович (style) → Грінченко (etymology).

**Online fallbacks:** VESUM: vesum.com.ua | Правопис: 2019.pravopys.net | Горох: goroh.pp.ua | Антоненко-Давидович: ukrlib.com.ua/books/printit.php?tid=4002 | Грінченко: hrinchenko.com | Словник.ua: slovnyk.me

### Writing Quality
- Every paragraph: ONE clear point, logical flow to the next
- Vary sentence length (short for emphasis, medium for explanation, long for examples)
- Use callout boxes (:::tip, :::caution, :::note) — at least 3 per module (mnemonics, common mistakes, cultural notes). Space them throughout the module, not clustered.
- **Dialogue formatting** — use blockquote `>` with speaker names in bold. Each turn on its own line. At A1 level, add English translation in italics after each line so learners understand what is being said. At A2, translate only new vocabulary. At B1+, no dialogue translations. Example:

> **Оленка:** Привіт! Як справи? *(Hi! How are you?)*
> **Тарас:** Добре, дякую! А у тебе? *(Good, thanks! And you?)*
> **Оленка:** Теж добре! *(Also good!)*

Without speaker names, the reader cannot tell who is speaking. NEVER use anonymous em dashes (`— text`). After each dialogue, briefly explain the key phrases and patterns the learner just saw.
- **Dialogues must sound like real people talking.** Test: would two Ukrainians actually say this to each other? If the dialogue sounds like a textbook drill ("Це кінь? — Так, це кінь."), rewrite it. Good dialogues have context, reactions, and personality:

  BAD (interrogation): "Це сім'я? — Так, це сім'я. — А де м'ясо? — М'ясо там."
  GOOD (natural): "Це твоя сім'я на фото? — Так! Нас п'ять. — А що ви їсте? М'ясо? — Так, дуже смачне!"

  BAD (labeling objects): "Це дуб. — А там коза. — Ні, це коса."
  GOOD (real reaction): "Дивись, який великий дуб! — Так, старий. А під ним — коза! — Смішна коза."

  Use the knowledge packet's textbook excerpts for dialogue patterns. Adapt real situations, don't invent drills.
- **DIALOGUE VARIETY — CRITICAL.** Each module MUST have DIFFERENT dialogue situations from other modules. Before writing any dialogue, check: have previous modules used this setting? If yes, pick a different one.

  BANNED recurring settings (already used in M01-M09): describing a room (кімната), looking at a table/bed/lamp, generic greetings with no context, labeling objects.

  REQUIRED: Every dialogue must have a SPECIFIC REAL-WORLD SITUATION that motivates the grammar being taught. The situation must be different from all other modules.

  **Module-specific dialogue settings (from plan):**
  1. **Video-calling a friend while walking through Одеса (Odesa) — showing: Дерибасівська вулиця (f), Потьомкінські сходи (pl, Potemkin Stairs), порт (m, port), пляж (m, beach). Describing where you are, where you're going.**
     Speakers: Мешканець (filming), Онлайн-друг (watching)
     Why: Consolidation with вулиця(f), сходи(pl), порт(m), пляж(m)

  Use these settings. Do NOT substitute with a room description or generic greeting.
- **Tone: direct, clear, no filler.** State facts and teach. Don't praise the language ("beautiful", "wonderful", "unique melody"), don't praise the learner ("great job", "you've mastered"), don't narrate what you're doing ("In this section we will", "Now let's look at"). Just teach. Example:

  BAD: "The Ukrainian language has a wonderfully consistent and beautiful phonetic system."
  GOOD: "Ukrainian spelling is highly phonetic — what you see is what you hear."
- **Never guess about Ukrainian.** If you are unsure about a word, grammatical form, or phonetic rule — flag it with `<!-- VERIFY: word/claim -->`. Never invent or describe vaguely to hide uncertainty.

### Forbidden Tropes

If you write any of these patterns, the module will be rejected in review:

- **The Cheerleader:** "Great job!", "Don't worry, it's easy!", "You're doing amazing!", "Good news!" — respect the learner's intelligence; stay professional.
- **The Announcer:** "In this section, we will explore...", "Now let's dive into...", "Let's take a look at...", "To summarize what we learned..." — never use formulaic transitions. Just teach the concept directly.
- **The Translator:** "The Ukrainian word for 'cat' is 'кіт'." — instead, present naturally: "A domestic cat is a **кіт**."
- **The Wall of Text:** 3+ paragraphs of English theory without a single Ukrainian example — every concept must be anchored in immediate Ukrainian examples.
- **The Filler:** "This is a very important concept that you will use frequently in your daily life." — empty sentences that add words but not meaning. Every sentence must teach something.

GRAMMAR CONSTRAINTS (A1.5 — Places & Movement, M29-M36):
Euphony, locative, accusative direction, genitive origin.

ALLOWED:
- Euphony rules (у/в, і/й, з/із/зі)
- Locative case with в/у/на (Де?)
- Accusative for direction (Куди?)
- Genitive for origin (Звідки? З + genitive)
- All present tense verbs

BANNED: Past/future tense, dative, instrumental,
participles, passive voice, complex subordination

### Vocabulary



### Pronunciation Videos

**Do NOT embed YouTube videos in your prose.** A downstream ENRICH tool automatically places pronunciation videos from the plan. If you embed `<YouTubeVideo>` components, they will be duplicated. Simply reference the videos' existence when relevant (e.g., "Watch the pronunciation video for this letter") but do NOT insert `<YouTubeVideo>` tags.

Available videos (for reference only — ENRICH handles placement):


---

### Style Reference (match this tone and structure)

> **(У магазині / At the store)**
> — Добрий день! Скільки коштує хліб? (Good day! How much does the bread cost?)
> — Дванадцять гривень. (Twelve hryvnias.)
> — Дякую! Ось, будь ласка. (Thanks! Here you go.)

Notice that the shopkeeper uses **Добрий день** — the formal greeting for strangers. If this were a friend, they would say **Привіт** instead.

The word **скільки** (how much/how many) is one of the most useful question words. It always pairs with the genitive case: **скільки коштує** (how much does it cost), **скільки часу** (how much time).

*Note: Short dialogues in Ukrainian with per-line English glosses. Grammar explained in English. Ukrainian sentences in blockquotes and bulleted lists.*



---

## Skeleton — Follow This Structure Exactly

A detailed paragraph-level skeleton was generated for this module. You MUST follow it precisely:
- Write every paragraph listed, in the order listed
- Hit each paragraph's word budget (+-10%)
- Place exercises exactly where the skeleton says
- Use the specific examples named in the skeleton
- Do NOT skip paragraphs, reorder sections, or add unplanned content

The skeleton replaces Step 1 (Pacing Plan) — do NOT output a <pacing_plan> block. Start writing immediately from the first section.

<skeleton>
## Що ми знаємо? (~220 words total)
- P1 (~100 words): [Introduction to the A1.5 "Places" checkpoint. Motivation on why being able to navigate a city is the first real "survival" skill. Mentioning the transition from single words to connected urban navigation using examples like "у центрі" and "на метро".]
- P2 (~120 words): [A structured self-check list covering M28-M34. Questions: "Чи можу я вибрати між 'у' та 'в'?" (Euphony), "Чи знаю я, як сказати, де я?" (Locative), "Чи можу я запитати дорогу?" (Directions), "Чи можу я сказати, звідки я приїхав?" (Genitive chunks).]
- <!-- INJECT_ACTIVITY: quiz-question-choice --> [quiz, focus: Choose the correct question: Де? Куди? Звідки?, 8 items]

## Читання (~270 words total)
- P1 (~120 words): [Contextual introduction to the reading text. We follow a traveler named Марк who arrives in Kyiv. Explain the logic of the narrative: arriving at the station (вокзал), looking for a hotel (готель), and navigating to a famous landmark (Золоті ворота).]
- P2 (~150 words): [The reading text itself. Narrative prose incorporating: "Я зараз у Києві. Я з Польщі. Мій готель у центрі. Я йду пішки...". Use of "на метро", "направо", and "біля музею" to demonstrate integrated A1.5 vocabulary and grammar.]

## Граматика (~240 words total)
- P1 (~110 words): [Euphony synthesis. Summary of у/в, і/й, and з/із/зі. Provide clear binary examples: "Він у Львові" vs "Вона в Одесі", "брат і сестра" vs "тато й мама", "зі школи" vs "з роботи". Focus on the sound flow as a signature of Ukrainian.]
- P2 (~130 words): [Tri-directional case comparison. Explaining the semantic difference between "Де?" (Locative: в аптеці), "Куди?" (Accusative: в аптеку), and "Звідки?" (Genitive: з аптеки). Contrast "на роботі" (location) with "на роботу" (direction) to clarify the preposition "на" usage for events/open spaces.]
- <!-- INJECT_ACTIVITY: group-sort-cases --> [group-sort, focus: Sort phrases by case/function (Locative, Accusative, Genitive chunks), 9 items]
- <!-- INJECT_ACTIVITY: quiz-euphony-check --> [quiz, focus: Euphony rules check: у/в, і/й, з/із/зі, 8 items]

## Діалог (~320 words total)
- P1 (~100 words): [Setting the scene for the interaction. A tourist from Canada arrives at a Kyiv metro station and asks a local for directions to a museum and then to the train station (вокзал). Emphasize the polite register using "Вибачте" and "Скажіть, будь ласка".]
- P2 (~140 words): [Multi-turn connected dialogue. Tourist: "Вибачте, я з Канади. Де тут музей?". Local: "Музей у центрі. Ідіть на метро...". Incorporation of "направо", "наліво", "станція Хрещатик", and "у Львів".]
- P3 (~80 words): [Functional language note on "дістатися" (to get to) vs "йти/їхати". Explain how to use "від метро" (from the metro) and "до вокзалу" (to the station) in real-world requests.]
- <!-- INJECT_ACTIVITY: fill-in-dialogue-forms --> [fill-in, focus: Complete the connected dialogue with correct forms, 6 items]

## Підсумок (~270 words total)
- P1 (~150 words): [A1.5 Phase achievement summary. A bulleted "Я тепер можу..." (I can now...) list: 1. Use euphony (у/в, і/й) for natural speech. 2. State my location (Де? — в готелі). 3. Indicate my direction (Куди? — у парк). 4. Use city transport (на автобусі, на метро). 5. Give and follow directions (направо, прямо). 6. State my origin (Звідки? — з України).]
- P2 (~120 words): [Transition to A1.6. Explain that now that we can find our way to a shop or restaurant, we need the language to act inside them. Teaser for "Food and Shopping" (M36+), focusing on ordering, buying, and the Accusative case for direct objects (Я хочу каву).]

Grand total: ~1320 words
</skeleton>

## Output Format

Write in Markdown. Use:
- `## Section Title` for main sections
- `### Subsection` for subsections within a section
- `**bold**` for Ukrainian words being taught — EVERY bold Ukrainian word MUST have an English translation on first use, either in parentheses `**слово** (translation)` or inline `**слово** means "translation"`. No exceptions.
- Tables for paradigms (conjugation, declension)
- `:::tip` / `:::caution` / `:::note` for callout boxes
- `<!-- INJECT_ACTIVITY: {id} -->` for exercise placement (markers only — do NOT write exercise content)

Do NOT write MDX component syntax, JSON, or DSL exercise blocks (:::quiz, etc.). Plain Markdown with injection markers.

Begin writing now. Start with the first section heading.
