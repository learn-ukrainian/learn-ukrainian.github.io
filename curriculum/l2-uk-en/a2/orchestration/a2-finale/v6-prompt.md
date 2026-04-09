

---

## Your Writing Identity

**You are: Lead Ukrainian Instructor.** Your persona is *The Conversation Partner*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **69: Фінал A2** (A2, A2.10 [Refinement and Graduation]).

**Target: 1500–2250 words** of prose (Ukrainian examples count toward word total, headings and exercise placeholders do not).

---

## Step 1: Pacing Plan (output this FIRST)

Before writing any content, output a `<pacing_plan>` block. Evaluate each section from the plan and commit to a word budget. This prevents frontloading early sections and rushing later ones.

```
<pacing_plan>
Section 1 "Title": ~XXX words — [1-sentence content focus]
Section 2 "Title": ~XXX words — [1-sentence content focus]
...
Summary: ~150 words
Total: 1500+ words
</pacing_plan>
```

Then begin writing the module content. Follow your own pacing plan — each section must hit its word budget (±10%).

---

## 9 Hard Rules

1. **IMMERSION TARGET: 70-90% Ukrainian — near-full immersion. English only in vocabulary tab.** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if immersion is outside this range. For A1 early modules, the learner cannot read Cyrillic — English must dominate. For A2+, Ukrainian must carry a significant share — add Ukrainian Reading Practice blocks, dialogues, and example paragraphs to reach the target. Too little Ukrainian fails audit just as much as too much.
2. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
3. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
4. **You are a warm, encouraging teacher.** Natural teacher phrasing ("Let us look at...", "Have you noticed...") is fine. What to AVOID: self-congratulatory openers ("Welcome to A2! Congratulations!"), gamified language ("You have unlocked...", "You now possess..."), and empty filler sentences that add words but zero information. Every sentence should teach something specific to Ukrainian.
5. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
6. **Place exercise markers only** — do NOT write exercises directly. Place `<!-- INJECT_ACTIVITY: {id} -->` markers where exercises should appear. A separate pipeline step generates the actual exercises from the plan's activity_hints.
7. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
8. **Hit the word target** — you MUST write 1500–2250 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
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
module: a2-069
level: A2
sequence: 69
slug: a2-finale
version: '1.0'
title: Фінал A2
subtitle: Підсумкове завдання — один день в українському місті
focus: review
pedagogy: Review
phase: A2.10 [Refinement and Graduation]
word_target: 1500
objectives:
- Learner can sustain an extended conversation in Ukrainian across multiple everyday situations (transport,
  shopping, dining, asking directions).
- Learner can narrate events in the past, describe the present, and discuss future plans using all A2
  grammar structures fluently.
- Learner can complete practical real-world tasks in Ukrainian (order food, buy tickets, ask for help,
  describe a problem).
- Learner can demonstrate readiness for B1 through integrated use of cases, aspect, comparison, complex
  sentences, and opinion expression.
dialogue_situations:
- setting: 'Full day in Lviv — morning: arriving at вокзал (m), checking into готель (m, hotel). Day:
    Площа Ринок (f, main square), кав''ярня (f), книгарня (f, bookshop). Evening: зустріч з друзями (meeting
    friends), вечеря (f, dinner), обговорення планів на майбутнє.'
  speakers:
  - Турист
  - Різні мешканці Львова
  motivation: 'Full A2 capstone: all cases, aspects, tenses in one day trip'
content_outline:
- section: 'Ранок: прибуття та орієнтація (Morning: Arrival and Orientation)'
  words: 400
  points:
  - 'Scenario: the learner arrives in Lviv by train. Tasks: buy a transit ticket, ask for directions to
    the hotel, check in at the hotel (give name, passport, ask about room).'
  - 'Dialogues integrating: Locative (у Львові, на вокзалі), Accusative (купити квиток), Genitive (немає
    вільних кімнат), formal imperative (Покажіть, будь ласка, паспорт).'
  - 'Cultural note: how to navigate a Ukrainian city — маршрутка, трамвай, таксі, пішки.'
- section: 'День: ринок, кав''ярня, прогулянка (Day: Market, Cafe, Walk)'
  words: 400
  points:
  - 'At the market: buy food, discuss quantities and prices (numeral agreement: два кілограми яблук, п''ять
    помідорів), compare products (Ці яблука солодші за ті).'
  - 'At a cafe: order food and drinks, discuss preferences (Я волію каву з молоком. А що ви порадите?),
    deal with a small problem (Вибачте, я замовляв борщ, а не суп).'
  - 'Walking around: describe what you see using all cases naturally, ask locals about sights (Що це за
    будівля? Коли її збудували?).'
- section: 'Вечір: друзі, розмови, плани (Evening: Friends, Conversations, Plans)'
  words: 400
  points:
  - 'Meeting Ukrainian friends: discuss your day using past tense and aspect (Сьогодні я побачив/побачила
    стільки цікавого!). Share opinions (На мою думку, Львів — найгарніше місто).'
  - 'Extended conversation: discuss favorite places, compare Lviv with your home city, talk about Ukrainian
    traditions (Я дізнався/ дізналася про Івана Купала — це так цікаво!).'
  - 'Making future plans: discuss what to do tomorrow using future tense and щоб/якщо (Якщо буде гарна
    погода, поїдемо у Карпати. Я хочу поїхати, щоб побачити гори).'
- section: 'Підсумок: від A2 до B1 (Summary: From A2 to B1)'
  words: 300
  points:
  - 'Reflection: what the learner can now do — a summary of all A2 competencies expressed as "Я можу..."
    statements. Connect to CEFR A2 can-do descriptors.'
  - 'What changes in B1: more Ukrainian in explanations (metalanguage bridge is complete), longer texts,
    more nuanced grammar (participles, complex aspect, passive), richer vocabulary.'
  - 'Encouragement and celebration: completing A2 is a major milestone. The learner can handle everyday
    situations in Ukraine. Вітаємо! Ви готові до рівня B1!'
vocabulary_hints:
  required:
  - прибуття (arrival)
  - вокзал (train station)
  - квиток (ticket)
  - ринок (market)
  - замовити (to order)
  - порадити (to recommend)
  - будівля (building)
  - враження (impression)
  - підсумок (summary)
  - вітаємо (congratulations)
  recommended:
  - маршрутка (minibus)
  - прогулянка (walk, stroll)
  - дізнатися (to find out, to learn)
  - готовий (ready)
activity_hints:
- type: fill-in
  focus: Complete dialogues in real-world Ukrainian city situations
  items: 8
- type: quiz
  focus: Choose the correct grammar form in integrated context (mixed cases, aspect)
  items: 8
- type: match-up
  focus: Match situations to appropriate Ukrainian phrases and expressions
  items: 8
- type: error-correction
  focus: Find and correct grammar errors in sentences covering module topics
  items: 6
references:
- title: 'ULP: Travelling in Ukraine'
  url: https://www.ukrainianlessons.com/travel-ukraine/
  notes: Practical travel vocabulary and dialogues for real-world situations
- title: Заболотний Grade 6, Повторення наприкінці року
  notes: End-of-year capstone review format

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
- Confirmed: прибуття, вокзал, квиток, ринок, замовити, порадити, будівля, враження, підсумок, вітаємо, маршрутка, прогулянка, дізнатися, готовий.
- Not found: None.

## Grammar Rules
- **Numeral Agreement**: 2, 3, 4 require Nominative Plural (два кілограми, три яблука), while 5+ require Genitive Plural (п'ять кілограмів, шість яблук). Fractions like "з половиною" follow the whole number (два з половиною лимони). (Grade 6 Mova, Zabolotnyi § 185; Avramenko § 170).
- **Comparison of Adjectives**: Formed with suffixes -ш-, -іш- (солодший) and prefix най- (найсолодший). Composite forms use більш/найбільш + positive degree. (Grade 6 Mova, Zabolotnyi § 221).
- **Apostrophe**: § 7 — Used after labials (б, п, в, м, ф) before я, ю, є, ї (п'ять, м'ясо), after 'р' (пір'я), and after prefixes ending in a consonant (з'їсти).
- **Appositions (Прикладка)**: § 37 — Hyphenation rules for descriptive nouns (дівчина-розумниця, місто Київ).

## Calque Warnings
- **приймати участь**: Calque — Use **брати участь**.
- **вірний**: Often used incorrectly for "correct" — Use **правильний** (вірний means faithful/loyal).
- **рахувати**: Often used incorrectly for "to consider/think" — Use **вважати**.
- **замовити/порадити**: OK — Standard Ukrainian verbs for "to order" and "to recommend".

## CEFR Check
- **вокзал, квиток, ринок, готовий**: A1/A2 — OK (Essential vocabulary).
- **прибуття, будівля, враження, підсумок**: A2 — OK (Slightly advanced but appropriate for graduation).
- **маршрутка**: A2 — OK (Culturally essential for navigation in Ukraine).
- **дізнатися**: A2 — OK (Common verb for learning information).
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
# Knowledge Packet: Фінал A2
**Module:** a2-finale | **Track:** A2

<wiki_context>
## Compiled Wiki Knowledge

The following articles from the project wiki provide compiled knowledge relevant to this module. Use them as authoritative context — they were compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).

### Вікі: grammar/a2/a2-finale.md

# Граматика A2: Фінал A2



## Як це пояснюють у школі (How Schools Teach This)
На рівні A2, українські підручники переходять від вивчення ізольованих граматичних форм до їхнього інтегрованого використання в комунікативних ситуаціях. Фінальний огляд A2 консолідує всі 7 відмінків, часи дієслів, і, що найважливіше, вводить фундаментальну концепцію **виду дієслова** (доконаний/недоконаний).

Основний підхід — практичний і контекстуальний:
1.  **Функціональність на першому місці:** Граматика подається як інструмент для вирішення конкретних завдань: запитати дорогу, зробити замовлення, розповісти про минулі події, поділитися планами. Наприклад, у підручнику Авраменко (7 клас) тема прислівників і напрямку вивчається через діалог про орієнтування в метро (Source 10).
2.  **Діалогічна основа:** Велика увага приділяється діалогам, що імітують реальне спілкування. Учні розігрують телефонні розмови (Source 1, Source 8), планують вихідні (Source 2) або запитують поради (Source 46). Це допомагає засвоїти етикетні формули та правильну інтонацію.
3.  **Введення виду через протиставлення:** Найважливіша тема A2, вид дієслова, пояснюється через пари "процес/повторювана дія" (недоконаний) проти "результат/одноразова дія" (доконаний). Підручники та онлайн-ресурси часто використовують питання: недоконаний вид відповідає на `що робити?`, а доконаний — на `що зробити?` (Source 46). Приклади, як `Я там завжди купую овочі` (процес) проти `Де можна купити фрукти?` (одноразова потреба), є типовими (Source 46).
4.  **Закріплення відмінків через прийменники:** Замість сухого заучування відмінкових закінчень, акцент робиться на вживанні прийменників, які вимагають певного відмінка. Наприклад, конструкції з `біля`, `для`, `без` + родовий відмінок є ключовими для A2 (Source 43). Так само відпрацьовується місцевий відмінок для позначення місця: `на вокзалі`, `у театрі`, `в селі` (Source 8, Source 4).
5.  **Узгодження в реченні:** Особлива увага приділяється складним випадкам узгодження, наприклад, між підметом, вираженим числівником, і присудком (`П’ятеро фігуристів вибули` vs `Минуло три місяці`) (Source 5, Source 34).

Таким чином, фінал A2 — це не просто тест на знання правил, а перевірка здатності учня функціонально використовувати мову в типових життєвих сценаріях.

## Повна парадигма (Full Paradigm)
Оскільки це оглядова тема, тут представлені ключові парадигми, що консолідуються наприкінці рівня A2.

### 1. Вид дієслова (Verb Aspect)
Це центральна концепція A2. Більшість дієслів існують у парах.

| Недоконаний вид (Imperfective) | Доконаний вид (Perfective) | Спосіб утворення |
| :--- | :--- | :--- |
| *що робити?* (процес, повторювана дія) | *що зробити?* (результат, одноразова дія) | |
| купувати | **купити** | Зміна суфікса `~ува~` → `~и~` |
| допомагати | **допомогти** | Зміна суфікса `~а~` → `~Ø~`, чергування `г/ж` |
| писати | **написати** | Додавання префікса `на-` |
| робити | **зробити** | Додавання префікса `з-` |
| їсти | **поїсти** / **з'їсти** | Додавання префікса `по-` / `з'-` |
| читати | **прочитати** | Додавання префікса `про-` |
| надсилати | **надіслати** | Зміна суфікса, чергування |
| знаходити | **знайти** | Зміна суфікса, чергування |

### 2. Майбутній час (Future Tense)

| Особа | Недоконаний вид (Compound Future) | Доконаний вид (Simple Future) |
| :--- | :--- | :--- |
| Я | **буду** читати / писати | прочит**а́ю** / напи**шу́** |
| Ти | **будеш** читати / писати | прочит**а́єш** / напи**́шеш** |
| Він / Вона / Воно | **буде** читати / писати | прочит**а́є** / напи**́ше** |
| Ми | **будемо** читати / писати | прочит**а́ємо** / напи**́шемо** |
| Ви | **будете** читати / писати | прочит**а́єте** / напи**́шете** |
| Вони | **будуть** читати / писати | прочит**а́ють** / напи**́шуть** |

### 3. Наказовий спосіб (Imperative Mood)

| Форма | Однина (ти) | Множина (ви) | Запрошення (ми) |
| :--- | :--- | :--- | :--- |
| Читати | Чит**а́й**! | Чит**а́йте**! | Чит**а́ймо**! |
| Писати | Пиш**и́**! | Пиш**і́ть**! | Пиш**і́мо**! |
| Говорити | Говор**и́**! | Говор**і́ть**! | Говор**і́мо**! |
| Забути | Заб**у́дь**! | Заб**у́дьте**! | Заб**у́дьмо**! |
| Їсти | **Їж**! | **Їжте**! | **Їжмо**! |

### 4. Ключові прийменники та відмінки (Key Prepositions & Cases)

| Прийменник | Питання | Відмінок | Приклад | Джерело |
| :--- | :--- | :--- | :--- | :--- |
| `без` | без кого? чого? | Родовий (Genitive) | без кави, без цукру, без проблем | (Source 43) |
| `для` | для кого? чого? | Родовий (Genitive) | для мами, для друзів, для роботи | (Source 43) |
| `до` | до кого? чого? | Родовий (Genitive) | до вокзалу, до театру, до кінця | (Source 5, 43) |
| `з / від` | з/від кого? чого? | Родовий (Genitive) | з України, від станції | (Source 10) |
| `біля` | біля кого? чого? | Родовий (Genitive) | біля готелю, біля банку | (Source 43) |
| `після` | після чого? | Родовий (Genitive) | після роботи, після Різдва | (Source 43) |
| `в / у` | в/у кому? чому? | Місцевий (Locative) | у селі, у Києві, в театрі | (Source 4, 8) |
| `на` | на кому? чому? | Місцевий (Locative) | на вокзалі, на Подолі, на вулиці | (Source 8, 48) |
| `з` | з ким? чим? | Орудний (Instrumental) | з мамою, з цукром | (Source 5) |

## Частотність і пріоритети (Frequency & Priorities)

Для успішного завершення рівня A2, учень повинен зосередитись на наступних пріоритетах:

1.  **Майстерність у виді дієслова:** Це найважливіший стрибок в A2. Учень повинен автоматично розрізняти ситуації, що вимагають процесу (`Я готував вечерю 2 години`) і результату (`Я приготував вечерю`). Питання `що робити?` / `що зробити?` є ключовим інструментом самоперевірки (Source 46).
2.  **Активне використання 6 основних відмінків:** На кінець A2 учень має не просто "знати" відмінки, а впевнено використовувати їх у мовленні для вираження:
    *   **Належності/відсутності** (Родовий): `у мене немає часу`, `чашка кави`.
    *   **Напрямку** (Родовий `до`, Знахідний `в/на`): `я йду до магазину`, `я їду в Київ`.
    *   **Місцезнаходження** (Місцевий): `я живу в Києві`, `книга на столі`.
    *   **Інструменту/компанії** (Орудний): `я пишу ручкою`, `я розмовляю з другом`.
    *   **Адресата** (Давальний): `допомогти мамі`, `подарунок другу`.
3.  **Часові вирази:** Уміння говорити про час, дні тижня, дати.
    *   **Дні тижня:** `у понеділок`, `щосуботи` (Source 33).
    *   **Дати:** `Першого січня`, `двадцять третього лютого` (родовий відмінок місяця) (Source 9, 33, 50).
    *   **Час:** `о п'ятій годині`, `о десятій ранку` (Source 50).
4.  **Побутові та соціальні ситуації:** Пріоритетним є засвоєння мови для конкретних сценаріїв:
    *   **Привітання/прощання:** `Добрий день!` / `Доброго дня!`, `До побачення!`, `На добраніч!` (Source 22, 49).
    *   **Подяка/вибачення:** `Дякую!`, `Дуже вдячний`, `Вибачте!` (Source 10, 22).
    *   **Запит інформації:** `Де можна...?`, `Як дістатися до...?`, `Скільки коштує?` (Source 10, 46).

Менш пріоритетними на цьому етапі є складні випадки узгодження, пасивні конструкції та дієприкметники, які є фокусом рівня B1 (хоча пасивні форми як `заснований`, `збудований` можуть зустрічатись у текстах) (Source 48).

## Типові помилки L2 (Common L2 Errors)

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| `Я приймав участь у зборах.` | `Я **брав участь** у зборах.` | Калька з російської мови "принимать участие". В українській мові усталений вираз "брати участь" (Source 30, 36). |
| `Доброго дня!` (як відповідь на привітання) | `Добрий день!` (як вітання) / `І вам доброго дня!` (як побажання у відповідь) | `Доброго дня` є формою побажання (родовий відмінок), тоді як `Добрий день` — стандартна вітальна формула (називний відмінок). Хоча `Доброго дня` все частіше вживається як вітання, класична норма — `Добрий день` (Source 22, 49). |
| `Вибачаюсь.` | `**Вибачте!**` або `**Перепрошую!**` | Дієслово на `-ся` означає дію, спрямовану на себе ("вибачаю себе"). Це вважається некоректним і є калькою. Правильно просити вибачення в іншого (Source 22). |
| `П'ять студентів прийшов.` | `П'ять студентів **прийшли**.` | Після числівників 2, 3, 4 + іменник у Н.в. мн. дієслово йде у множині. Після 5 і більше + іменник у Р.в. мн., дієслово частіше ставиться у множині, коли йдеться про активних діячів (людей) (Source 5, 34). |
| `Ви, пані Олю, дуже **чарівні**.` | `Ви, пані Олю, дуже **чарівна**.` | При звертанні на "Ви" до однієї особи з повагою, прикметник, що її описує, залишається в однині, узгоджуючись з реальною статтю особи, а не з формальною множиною займенника (Source 34). |
| `Я читав цю книгу вчора.` (маючи на увазі завершену дію) | `Я **прочитав** цю книгу вчора.` | Це класична помилка з видом дієслова. Якщо дія завершена і є результат (книга прочитана), слід використовувати доконаний вид. Недоконаний вид означав би процес читання без вказівки на результат (Source 46). |
| `Заказати обід.` | `**Замовити** обід.` | Слово `заказати` є поширеною калькою з російської. Правильний український відповідник — `замовити` (Source 30). |

## Деколонізаційні застереження (Decolonization Notes)

**Обов'язково для засвоєння:** Українська граматика є самостійною системою, а не "варіантом російської з винятками".

1.  **Вид дієслова — не російський винахід:** Категорія виду (аспекту) є спільною для багатьох слов'янських мов. Методи творення видових пар в українській мові мають свої унікальні риси (напр., суфіксальні зміни `купувати/купити`), і їх слід вивчати як самостійне явище.
2.  **Лексична чистота:** Особливу увагу слід приділяти уникненню русизмів, які стали поширеними за часів СРСР. Навчальний матеріал повинен активно просувати питомо українські вирази.
    *   `брати участь` (не `приймати участь`) (Source 30, 36)
    *   `будь-який` (не `любий` у значенні "any") (Source 30)
    *   `наступний` (не `слідуючий`)
    *   `заважати` (не `мішати`)
3.  **Звертання та етикет:** Українська мова зберегла активне використання **кличного відмінка** (`пане`, `Ольго`, `земле`, `друже`), що є важливою культурною та граматичною рисою, яка значно менш виражена в сучасній російській мові. Ігнорування кличного відмінка (`Шановний директор...`) є ознакою зневаги до норми (Source 22, 24).
4.  **"Барахолка" vs. "Блошиний ринок":** У розмовному мовленні (навіть у носіїв) можна почути слово `барахолка` (Source 46). Це пряме запозичення з російської (`барахло` - мотлох). Письмова та літературна норма — `блошиний ринок`. Важливо пояснити учням цю різницю.
5.  **Фонетичні відмінності:** Слід наголошувати на унікальних рисах української фонетики, які впливають на вимову, наприклад, дзвінкість приголосних перед іншими дзвінкими (`вокзал` вимовляється як `[воґзал]`), на відміну від російської, де оглушення є більш поширеним (Source 26).

## Природні приклади (Natural Examples)

### Група 1: Питання про можливість і плани (Вид дієслова)
*   `Де можна десь тут **купити** фрукти й овочі, але не в супермаркеті?` (Source 46) - *Одноразова дія, результат.*
*   `Я там завжди **купую** овочі, фрукти, крупи, горішки...` (Source 46) - *Повторювана дія, процес.*
*   `Якщо хочеш, **можемо поїхати** цієї суботи разом.` (Source 46) - *Пропозиція одноразової дії в майбутньому.*

### Група 2: Місцезнаходження та напрямок (Місцевий та Родовий відмінки)
*   `Виставка **знаходиться біля 14-ї колії на центральному вокзалі** Києва.` (Source 42)
*   `Ми вийшли **на Яблуницький перевал**.` (Source 35)
*   `Треба **дістатися від станції** «Майдан Конституції» **до станції** «Перемога».` (Source 10)

### Група 3: Розповідь про минулі події (Минулий час, види)
*   `Ми з батьками часто **катались** у лісопарку по велодоріжці.` (Source 2) - *Процес/повторювана дія в минулому.*
*   `Наш великий переїзд зі Стокгольма у новий будинок **був 23 лютого 2022-го року**.` (Source 50) - *Факт у минулому.*
*   `Уперше ім’я Сагайдачного **набуло популярності** 1605 року після морського походу.` (Source 38) - *Завершений результат у минулому.*

### Група 4: Соціальна взаємодія (Етикет, звертання)
*   `**Доброго ранку!**` / `**Добрий день!**` / `**Добрий вечір!**` (Source 22, 49)
*   `**Дуже вдячний** / **вдячна!**` (Source 10)
*   `**Пане Юрію,** щиро вітаємо з днем народження!` (Source 24)

### Група 5: Вираження думок, потреб і бажань
*   `Я **не можу жити без кави**.` (Source 43)
*   `Я **хочу**, аби він відчув до мене прихильність.` (Source 13)
*   `З нетерпінням **чекаю** екскурсії до зоопарку.` (Source 40)

## Рекомендації для вправ (Activity Concepts)

**Фаза 1: Розпізнавання та ідентифікація**
*   **"Знайди пару":** Дати учням текст (напр., уривок з Source 46) і попросити знайти та виписати всі видові пари дієслів, які вони побачать (`купити/купую`, `надіслати/надсилала`).
*   **"Контекст вирішує все":** Подати речення з пропущеним дієсловом і двома варіантами (доконаний/недоконаний). Учень має вибрати правильний, пояснюючи свій вибір (напр., `Щосуботи я (ходжу/піду) на ринок.` vs `Завтра я (ходжу/піду) на ринок.`).

**Фаза 2: Контрольована практика**
*   **Трансформація:** Перетворити речення з теперішнього часу (недоконаний вид) на майбутній доконаний. `Я читаю книгу.` → `Я прочитаю книгу.`
*   **Заповнення пропусків з прийменниками:** Створити вправи на основі Source 43. `Я купив подарунок ___ (сестра).` (для сестри). `Ми гуляли ___ (парк).` (у парку).
*   **Складання речень:** Дати набір слів у початковій формі і попросити скласти граматично правильне речення. Наприклад: `(ми, з, друзі, вчора, ходити, в, кіно)` → `Ми з друзями вчора ходили в кіно.`.

**Фаза 3: Вільне мовлення**
*   **Рольові ігри:**
    *   **"На пошті":** Один учень — клієнт, хоче надіслати листівку. Інший — працівник пошти. Використовуються фрази `я хочу надіслати`, `куди?`, `скільки коштує?` (Source 46).
    *   **"Планування подорожі":** Учні в парах планують поїздку на вихідні, використовуючи майбутній час. `Куди ми поїдемо?`, `Що ми будемо робити?`, `Ми відвідаємо музей.` (Source 2, 32).
    *   **"Інтерв'ю":** Учні ставлять один одному запитання про їхній типовий день (недоконаний вид) та про плани на завтра (доконаний вид) (Source 32, 35).

## Зв'язки з іншими темами (Connections)

*   **Базується на:**
    *   **Граматика A1:** Впевнене володіння теперішнім часом, знання родів іменників, базове відмінювання в 4 основних відмінках (Н. З. М. О.).
*   **Відкриває шлях до:**
    *   **Граматика B1:** Розуміння виду є абсолютною передумовою для вивчення **дієслів руху з префіксами** (`приїхати`, `вийти`, `перейти`), **дієприкметників** (`прочитана книга`, `зачинені двері`) (Source 48) та складних підрядних речень часу (`коли я прийду...`). Без міцного засвоєння виду на рівні A2, подальший прогрес у B1 є практично неможливим.

## Пов'язані статті (Related Articles)

- `verb-aspect`
- `genitive-case`
- `locative-case`
- `instrumental-case`
- `future-tense`
- `imperative-mood`
- `greetings-and-farewells`

---

### Вікі: pedagogy/a1/a1-finale.md

# Педагогіка A1: A1 Finale



## Методичний підхід (Methodological Approach)

The A1 Finale is not about introducing new grammar, but about **synthesis and production**. The primary goal is to move the learner from using isolated, memorized phrases to combining them into meaningful, purposeful communication. The pedagogical approach should be heavily task-based, simulating real-world situations where the learner must integrate all their A1 knowledge.

Ukrainian pedagogy at this stage emphasizes moving from simple recognition to active use. The focus shifts from "what is this word?" to "how do I use this word to get something done?"

1.  **Functional Scenarios:** The core of the finale module(s) should be built around practical tasks that require planning and communication. Examples include planning a trip, booking a room (Source 44), ordering food, or having a first meeting (Source 41, 43). These tasks naturally integrate vocabulary for time, dates, numbers, questions, and basic verbs.
2.  **Descriptive Production:** Learners should be challenged to produce short, connected descriptive texts. A highly effective activity is the "словесний портрет" (verbal portrait), where a learner describes a friend or family member (Source 24). This consolidates knowledge of adjectives, noun genders, and basic sentence structure (`Він/вона має...`, `Його/її звати...`). Another excellent task is describing a typical day, which reinforces adverbs of time (`вранці`, `вдень`, `ввечері`) and present tense verbs (Source 39).
3.  **Systematic Review through Contrast:** Re-activate and solidify vocabulary by using antonyms. Exercises that ask learners to find opposites (`холодний` vs. `теплий`, `ранок` vs. `вечір`) are common in early grades and very effective for A1 learners (Source 9, 26).
4.  **Grammar Consolidation:** The finale must include targeted review of A1's most critical (and challenging) grammar points:
    *   **Noun Gender & Pronoun Agreement:** `мій/моя/моє` (Source 5).
    *   **Verb Aspect (Introductory):** The distinction between infinitive (`хочу подорожувати`) and other verb forms (`я подорожую`) (Source 7).
    *   **Basic Case Usage:** Reviewing prepositional and accusative cases for location (`в/у` + L), time (`о` + L), and direct objects (`я бачу` + A).

## Послідовність введення (Introduction Sequence)

The finale should be structured as a multi-stage review process that builds confidence and culminates in a comprehensive production task.

-   **Step 1: Etiquette Refresh.** Begin with a fast-paced review of essential etiquette formulas for greetings, farewells, thanks, and apologies. This is a low-stress way to activate passive knowledge and build momentum (Source 4, 21, 49).
-   **Step 2: Thematic Vocabulary & Grammar Drills.** Introduce a thematic scenario, like "Planning a Weekend Trip."
    -   Review vocabulary for days, months, and times of day (`у понеділок`, `вранці`, `ввечері`) (Source 27, 39).
    -   Drill numbers for telling time and dates (`о п'ятій годині`, `п'ятого квітня`) (Source 19, 34).
    -   Practice future tense constructions (`ми поїдемо`, `я буду...`) needed for planning (Source 44).
-   **Step 3: Guided Production (Dialogue).** Engage learners in a role-playing activity based on the theme. For example, one learner is a hotel receptionist and the other is a tourist booking a room. Provide a template based on authentic dialogues (Source 44). The goal is successful communication, not grammatical perfection.
-   **Step 4: Expressive Production (Monologue).** Assign a short descriptive task. For example, "Describe your best friend" or "What do you do on Saturdays?" This allows learners to use the language more creatively and personally, drawing on adjective and verb vocabulary (Source 24).
-   **Step 5: Capstone "Interview".** The final assessment should be a simulated conversation, like the interview in Source 47. The instructor asks a series of questions covering all major A1 topics: `Як вас звати?`, `Де ви живете?`, `Що ви любите робити у вільний час?`, `Яка ваша улюблена пора року?`. This holistically evaluates the learner's ability to understand and produce basic spoken Ukrainian.

## Типові помилки L2 (Common L2 Errors)

English-speaking learners at the end of A1 often make predictable errors based on L1 interference or incomplete understanding of Ukrainian grammar. The finale must address these directly.

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| `Доброго дня!` (as a greeting) | `Добрий день!` | While common, `Доброго дня!` is grammatically a wish ("(I wish you) a good day"), not a statement greeting like `Добрий день` ("The day is good"). Native-speaker sources emphasize that `Добрий день!` and `Добрий вечір!` are the established literary norms, whereas `Доброго ранку!` is the standard for morning (Source 2, 4, 21, 49). The writer should explain this nuance. |
| `Я вибачаюсь.` | `Вибачте!` / `Перепрошую!` | This is a direct calque from Russian. The reflexive particle `-ся` implies the action is directed at oneself ("I forgive myself"). Ukrainian pedagogy strictly corrects this, teaching `вибачте` (forgive me) or `перепрошую` (I apologize) (Source 2, 25). |
| `пам’ятний сувенір` | `сувенір` | A tautology (redundancy). The word `сувенір` itself implies it's a memorable object. This is an example of learners over-translating from English ("memorable souvenir"). Other examples include `вільна вакансія` (vacant vacancy) -> `вакансія` (Source 32). |
| `Моя друг` | `Мій друг` | Basic gender agreement error. Learners often forget that possessive pronouns (`мій`, `моя`, `моє`) must match the gender of the noun they describe, not the gender of the speaker. This requires constant drilling with exercises like those in Source 5. |
| `Я їду в Київ в квітень.` | `Я їду в Київ у квітні.` | English uses prepositions + noun (`in April`), while Ukrainian uses prepositions + locative case (`у квітні`). Learners must internalize that prepositions of time and place trigger case changes. Exercises with months and days of the week are critical (Source 27). |
| `Десять гривнів` | `Десять гривень` | Incorrect plural genitive for numbers. After numbers 5-20 (and higher numbers ending in 5-9, 0), nouns take the genitive plural. Learners often default to the nominative plural. This is a key concept to review with prices and counting.<!-- VERIFY --> |

## Деколонізаційні застереження (Decolonization Notes)

This section is non-negotiable. The A1 curriculum must establish a purely Ukrainian foundation, free from Russian linguistic or pedagogical influence.

-   **No Russian Analogies:** Never explain a Ukrainian letter, sound, or grammar point by comparing it to Russian (e.g., "Ukrainian `и` is like Russian `ы`"). This creates a "Russian-plus" mental model. All phonetics and grammar must be taught on their own terms, using Ukrainian examples only.
-   **Correcting "Common" Russianisms:** Actively teach against common Surzhyk and Russianisms that have seeped into spoken language. The `вибачаюсь` vs. `вибачте` distinction is a prime example (Source 25). The goal is to teach the literary standard, not colloquial corruptions.
-   **Greeting Nuances:** Be precise about greetings. While a learner might hear `Доброго дня` in the wild, it's crucial to explain *why* `Добрий день` is the codified, traditional standard (Source 2, 4). This teaches them to be observant but also grounded in the literary language. It's a matter of prescription vs. description.
-   **Vocabulary Purity:** When teaching vocabulary, prioritize authentically Ukrainian words over recent loanwords, especially from Russian. For example, when discussing professions, use `водій` (driver), not `шофер`. When discussing feelings, use `мені подобається` (I like it), and avoid Russian-influenced phrasing. The style guide of Антоненко-Давидович is the gold standard for this (Source `mcp_rag_search_style_guide`).

## Словниковий мінімум (Vocabulary Boundaries)

By the end of A1, learners should have active command of a core set of vocabulary enabling them to handle simple, everyday situations.

**Іменники (Nouns)**
-   ★★★: `день`, `ранок`, `вечір`, `ніч`, `тиждень`, `місяць`, `рік`, `час`
-   ★★★: `мама`, `тато`, `друг`, `сестра`, `брат`, `діти`
-   ★★★: `сніданок`, `обід`, `вечеря`, `чай`, `кава`, `вода`
-   ★★☆: `місто`, `вулиця`, `дім`, `кімната`, `готель` (Source 44)
-   ★★☆: `поїзд`, `автобус`, `квиток` (Source 19, 29)
-   ★☆☆: `музей`, `театр`, `кіно` (Source 41, 34)

**Дієслова (Verbs)**
-   ★★★: `бути`, `мати`, `жити`, `робити`, `хотіти`, `любити`, `говорити`, `знати`
-   ★★★: `їсти`, `пити`, `спати`
-   ★★☆: `їхати`, `йти`, `бачити`, `дивитися`
-   ★★☆: `подорожувати` (Source 7), `бронювати` (Source 44), `купувати` (Source 7), `планувати` (Source 19)
-   ★☆☆: `запрошувати` (Source 1), `допомагати` (Source 4)

**Прикметники & Прислівники (Adjectives & Adverbs)**
-   ★★★: `добрий`, `поганий`, `великий`, `малий`, `новий`, `старий`
-   ★★★: `вранці`, `вдень`, `ввечері`, `вночі`, `сьогодні`, `завтра`, `вчора` (Source 27)
-   ★★☆: Кольори (`червоний`, `синій`, `жовтий`, `зелений`)
-   ★★☆: `тепло`, `холодно`, `добре`, `погано`
-   ★☆☆: `швидко`, `повільно`, `довго`, `недовго` (Source 41)

**Етикетні формули (Etiquette Formulas)**
-   ★★★: `Добрий день!`, `Доброго ранку!`, `Добрий вечір!` (Source 4, 21)
-   ★★★: `Дякую!`, `Будь ласка.`, `Вибачте.`, `До побачення.` (Source 4)
-   ★★☆: `Привіт!`, `Бувай!`, `Як справи?` (Source 35, 49)
-   ★☆☆: `Дуже приємно познайомитися.` (Source 43), `Смачного!`<!-- VERIFY -->

## Приклади з підручників (Textbook Examples)

The finale should use activity formats that are familiar from Ukrainian textbooks. These are proven to be effective for native-speaking children and are excellent for L2 learners.

1.  **Словесний портрет (Verbal Portrait)** (Based on Source 24)
    > **Завдання:** Намалюйте «словесний» портрет вашого друга або члена сім'ї. Використайте щонайменше 5 прикметників.
    >
    > *Приклад:*
    > Мій друг — високий. У нього темне волосся і блакитні очі. Він дуже добрий і веселий.
    >
    > **Слова для допомоги:**
    > Обличчя (яке?), Очі (які?), Волосся (яке?), Високий/низький, добрий/злий, веселий/сумний.

2.  **Розподіл за родом (Gender Sorting)** (Based on Source 5)
    > **Завдання:** Розподіліть слова за групами: `Мій`, `Моя`, `Моє`.
    >
    > *Слова:* Карта, брат, школа, місто, країна, олівець, суп, клас, стіл, подруга, друг, автобус.
    >
    > | Мій | Моя | Моє |
    > | :-- | :-- | :-- |
    > | брат | карта | місто |
    > | ... | ... | ... |

3.  **Складання діалогу: "Плани на вихідні"** (Based on Source 19, 27, 44)
    > **Завдання:** Уявіть, що ви розмовляєте з другом. Запитайте, що він/вона робить у суботу. Запропонуйте піти в кіно.
    >
    > *Корисні фрази:*
    > - Що ти робиш у суботу?
    > - У суботу ввечері я вільний/вільна.
    > - Ходімо в кіно?
    > - О котрій годині?
    > - О сьомій вечора.
    > - Добре, домовились!

4.  **Пошук антонімів (Finding Antonyms)** (Based on Source 9, 26)
    > **Завдання:** З'єднайте слова з протилежним значенням.
    >
    > | A | B |
    > | :-- | :-- |
    > | 1. день | а. вечір |
    > | 2. добрий | б. холодний |
    > | 3. теплий | в. ніч |
    > | 4. ранок | г. поганий |

## Пов'язані статті (Related Articles)

-   `pedagogy/a1/a1-greetings-and-farewells`
-   `pedagogy/a1/a1-nouns-gender-and-pronouns`
-   `pedagogy/a1/a1-present-tense-conjugation`
-   `pedagogy/a1/a1-telling-time-and-dates`
-   `pedagogy/a2/a2-introduction-to-cases`
-   `reference/common-l2-errors-ukrainian`
</wiki_context>

## Plan References

- 
- 

</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Ранок: прибуття та орієнтація (Morning: Arrival and Orientation)` (~400 words)
- `## День: ринок, кав'ярня, прогулянка (Day: Market, Cafe, Walk)` (~400 words)
- `## Вечір: друзі, розмови, плани (Evening: Friends, Conversations, Plans)` (~400 words)
- `## Підсумок: від A2 до B1 (Summary: From A2 to B1)` (~300 words)

Each section should follow the word budget specified. The total must reach 1500 words minimum.

---

## Content Rules

TARGET: 70-90% Ukrainian.
LANGUAGE ROLES:
- PRIMARY: Ukrainian for everything.
- ENGLISH: Only in vocabulary tables and one-line grammar notes where absolutely necessary.
- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English.
A2 register. Concrete everyday vocabulary. No literary language, no metaphors. Near-full Ukrainian immersion. Ukrainian sentences max 15 words. Max 2 clauses. All cases allowed. Simple subordinate clauses only. Full aspect pairs. No participles.

GRAMMAR RULES:
- Max 15 words per Ukrainian sentence
- Max 2 clauses per sentence
- All cases allowed
- Simple subordinate clauses allowed (який/що/коли)
- Aspect pairs introduced but not complex
- No participles

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
  1. **Full day in Lviv — morning: arriving at вокзал (m), checking into готель (m, hotel). Day: Площа Ринок (f, main square), кав'ярня (f), книгарня (f, bookshop). Evening: зустріч з друзями (meeting friends), вечеря (f, dinner), обговорення планів на майбутнє.**
     Speakers: Турист, Різні мешканці Львова
     Why: Full A2 capstone: all cases, aspects, tenses in one day trip

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



### Vocabulary

**Required:** прибуття (arrival), вокзал (train station), квиток (ticket), ринок (market), замовити (to order), порадити (to recommend), будівля (building), враження (impression), підсумок (summary), вітаємо (congratulations)
**Recommended:** маршрутка (minibus), прогулянка (walk, stroll), дізнатися (to find out, to learn), готовий (ready)

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
## Ранок: прибуття та орієнтація (Morning: Arrival and Orientation) (~440 words total)
- P1 (~60 words): [Scenario introduction: The learner arrives at the Lviv train station (головний вокзал). Establish the setting using Locative case: "я у Львові," "на вокзалі." Mention the atmosphere of the station and the first task: finding transport.]
- P2 (~110 words): [Dialogue at a ticket kiosk (каса). The tourist buys a ticket for the tram. Focus on Accusative case: "купити квиток," "чекати на трамвай." Use polite forms and the imperative: "Дайте, будь ласка," "Скільки коштує?"]
- P3 (~60 words): [Explanation of city navigation options in Ukraine. Differentiate between "маршрутка," "трамвай," and "таксі." Discuss movement verbs and prepositions of direction: "їхати до центру," "йти пішки."]
- P4 (~130 words): [Dialogue checking into a hotel (готель). Focus on Genitive case for negation and identity: "у мене є бронювання," "немає вільних номерів." Practical interaction: giving a passport ("ось мій паспорт"), asking about breakfast ("о котрій годині сніданок?").]
- P5 (~80 words): [Cultural note on Lviv's unique layout and historical charm. Mention the mix of Austrian and Ukrainian architecture. Introduce the idea of "зустріч" (meeting) and "прогулянка" (walk).]
- <!-- INJECT_ACTIVITY: match-up-situations --> [match-up, Match common travel situations (station, hotel, street) to appropriate Ukrainian phrases, 8 items]

## День: ринок, кав'ярня, прогулянка (Day: Market, Cafe, Walk) (~440 words total)
- P1 (~60 words): [Setting the scene at Ploshcha Rynok (Площа Ринок). Describe the central square using adjectives: "старий," "гарний," "багатолюдний." Transition to the open-air market experience.]
- P2 (~130 words): [Dialogue at the market. Shopping for food while reviewing Numeral agreement and Genitive plural: "два кілограми яблук," "п'ять помідорів." Include comparative adjectives to choose the best product: "ці яблука солодші," "той сир дорожчий."]
- P3 (~60 words): [The ritual of Lviv coffee (львівська кава). Explain preferences using the Instrumental case for accompaniments: "кава з молоком," "чай з лимоном," "кава без цукру." Use the verb "воліти" (to prefer).]
- P4 (~130 words): [Dialogue in a cafe. Ordering a traditional meal (борщ, вареники) and dealing with a service issue. Use Aspect to distinguish between ordering and receiving: "Я замовляв (imp) борщ, а ви принесли (perf) суп." Use the imperative for requests: "порадьте щось смачне."]
- P5 (~60 words): [Sightseeing and inquiry. Asking locals about historical buildings using past tense resultative aspect: "Хто збудував цю церкву?" "Коли відкрили цей театр?" Focus on "дізнатися" (to find out).]
- <!-- INJECT_ACTIVITY: fill-in-dialogues --> [fill-in, Complete typical street and market dialogues with correct case endings and verbs, 8 items]

## Вечір: друзі, розмови, плани (Evening: Friends, Conversations, Plans) (~450 words total)
- P1 (~60 words): [Meeting Ukrainian friends in the evening. Setting a relaxed social tone. Using Vocative case for names: "Друже," "Пане Юрію," "Оксано."]
- P2 (~120 words): [Dialogue narrating the day's events. Heavy focus on Verb Aspect (Perfective vs. Imperfective) to describe completed actions vs. processes: "Сьогодні я бачив (imp) багато пам'ятників, але нарешті купив (perf) сувенір."]
- P3 (~100 words): [Extended conversation: Sharing impressions and opinions. Use "На мою думку" (In my opinion) and "мені здається" (it seems to me). Compare the current city with the learner's hometown using Genitive comparisons: "Львів старіший за моє місто."]
- P4 (~120 words): [Discussing future plans for tomorrow and the B1 journey. Use Future Tense (Compound vs. Simple): "завтра ми будемо гуляти," "я поїду в Карпати." Introduce conditional structures: "якщо буде гарна погода," "якщо я вивчу всі слова."]
- P5 (~50 words): [Conclusion of the day. Farewell formulas: "На добраніч," "До завтра," "Було приємно побачитися."]
- <!-- INJECT_ACTIVITY: quiz-integrated-grammar --> [quiz, Choose the correct grammar form (aspect, case, tense) in a long narrative about a trip to Lviv, 8 items]
- <!-- INJECT_ACTIVITY: error-correction-a2 --> [error-correction, Identify and fix common A2 level mistakes (Russianisms like "приймати участь", gender agreement, aspect), 6 items]

## Підсумок: від A2 до B1 (Summary: From A2 to B1) (~320 words total)
- P1 (~120 words): [Reflection on A2 milestones. Use "Я можу..." statements to list competencies: "Я можу замовити їжу," "Я можу розповісти про минуле," "Я розумію різницю між видами дієслів." Connect these to the CEFR A2 level descriptors.]
- P2 (~120 words): [The bridge to B1. Explain the upcoming shift: more Ukrainian-only instructions, focus on prefixed motion verbs ("приїхати," "вийти"), and the introduction of participles. Encourage the learner that the "metalanguage bridge" is now built.]
- P3 (~80 words): [Final celebratory closing. Completing A2 is a massive achievement for a difficult Slavic language. Final motivating words: "Вітаємо! Ви готові до нових викликів. Побачимося на рівні B1!"]

Grand total: ~1650 words
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
