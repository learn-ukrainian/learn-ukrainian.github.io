

---

## Your Writing Identity

**You are: Lead Ukrainian Instructor.** Your persona is *The Patient Guide*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **11: How Many?** (A1, A1.2 [My World]).

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

1. **IMMERSION TARGET: 10-20% Ukrainian** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if immersion is outside this range. For A1 early modules, the learner cannot read Cyrillic — English must dominate. For A2+, Ukrainian must carry a significant share — add Ukrainian Reading Practice blocks, dialogues, and example paragraphs to reach the target. Too little Ukrainian fails audit just as much as too much.
2. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
3. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
4. **You are a warm, encouraging teacher.** Natural teacher phrasing ("Let us look at...", "Have you noticed...") is fine. What to AVOID: self-congratulatory openers ("Welcome to A2! Congratulations!"), gamified language ("You have unlocked...", "You now possess..."), and empty filler sentences that add words but zero information. Every sentence should teach something specific to Ukrainian.
5. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
6. **Place exercise markers only** — do NOT write exercises directly. Place `<!-- INJECT_ACTIVITY: {id} -->` markers where exercises should appear. A separate pipeline step generates the actual exercises from the plan's activity_hints.
7. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
8. **Hit the word target** — you MUST write 1200–1800 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
9. **NO archaic, obsolete, or rare words** — use only modern standard Ukrainian. Do not use words marked as archaic (застаріле) or dialectal in dictionaries. Example: use «кін» not «кон», use «пом'якшені» not «м'якшені». When in doubt, choose the common modern form. Your pre-training contains Russian-influenced archaic forms — verify unfamiliar words.
10. **EVERY module MUST end with `## Підсумок — Summary`** — this is the last H2 section before the file ends. It contains a self-check recap. If you forget this section, the audit REJECTS the module and you waste a retry. Write it LAST, after all other sections.

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
module: a1-011
level: A1
sequence: 11
slug: how-many
version: '1.2'
title: How Many?
subtitle: Один, два, три — numbers through prices, ages, and phones
focus: vocabulary
pedagogy: PPP
phase: A1.2 [My World]
word_target: 1200
objectives:
- Count from 1 to 100 in Ukrainian
- Say prices using гривня and round numbers up to 1000
- Give age using Мені ... років (as memorized chunk — NO case grammar)
- Read and say Ukrainian phone numbers
dialogue_situations:
- setting: 'At a bakery — ordering bread, pastries, and cakes for a family gathering.
    Count: один хліб (m, bread), одна булочка (f, bun), одне тістечко (n, pastry). Prices in гривні.
    Ask: Скільки коштує торт? А три булочки?'
  speakers:
  - Покупець
  - Пекар (baker)
  motivation: Скільки коштує? with торт(m), булочка(f), тістечко(n), хліб(m)
- setting: Counting items in a school backpack before class — ручка (f, pen), олівець
    (m, pencil), зошит (m, notebook), підручник (m, textbook).
  speakers:
  - Учень (student)
  - Мама
  motivation: 'Numbers with school supplies: один олівець, дві ручки, п''ять зошитів'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — At a market stall: — Скільки коштує сумка? — Двісті гривень.
    — А маленька? — Сто п''ятдесят. — Добре, дякую!
    Numbers emerge through real shopping context. Uses only vocabulary from M08-M10
    (gender, adjectives, colors). Demonstratives (ця/та) come in M12.'
  - 'Dialogue 2 — Meeting someone new (extending M05): — Скільки тобі років? — Мені
    двадцять п''ять. А тобі? — Мені тридцять два. А твоя сестра? — Їй вісімнадцять.
    Age formula as chunk: Мені/тобі/їй + number + років/роки/рік.'
- section: Числа 1-20 (Numbers 1-20)
  words: 300
  points:
  - '1-10: один, два, три, чотири, п''ять, шість, сім, вісім, дев''ять, десять. Pronunciation
    focus: п''ять (apostrophe!), сім (not ''сем''), дев''ять (apostrophe!). Practice:
    counting objects from M08 — один стіл, два стільці, три книги. Note: the noun
    changes after numbers, but we learn the PATTERNS as chunks, not the grammar rule.'
  - '11-20: одинадцять, дванадцять, тринадцять, чотирнадцять, п''ятнадцять, шістнадцять,
    сімнадцять, вісімнадцять, дев''ятнадцять, двадцять. Pattern: base + -надцять (like
    English ''-teen''). Watch the stress: одинáдцять, дванáдцять — stress always falls
    on the syllable ''на'' in -надцять.'
- section: Десятки і сотні (Tens and Hundreds)
  words: 300
  points:
  - 'Tens: двадцять, тридцять, сорок (!), п''ятдесят, шістдесят, сімдесят, вісімдесят,
    дев''яносто (!), сто. Two irregulars: сорок (40 — not ''чотиридесят'') and дев''яносто
    (90 — not ''дев''ятдесят''). Combined: двадцять один, тридцять п''ять, сорок сім
    — just add the unit.'
  - 'Hundreds for prices: сто (100), двісті (200), триста (300), чотириста (400),
    п''ятсот (500), тисяча (1000). Гривня: одна гривня, дві гривні, п''ять гривень.
    These noun changes are memorized patterns — grammar comes in A2. ULP Ep9: Anna
    teaches numbers through real prices.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Three practical uses of numbers: 1. Prices: Скільки коштує? — Двісті гривень.
    Сто п''ятдесят гривень. 2. Age: Скільки тобі років? — Мені двадцять три (роки).
    3. Phone: Мій номер — нуль дев''яносто сім, три два один, сорок п''ять, шістдесят
    сім. Self-check: Say your age in Ukrainian. Say a price (250 hryvnias). Read a
    phone number.'
vocabulary_hints:
  required:
  - один, два, три, чотири, п'ять (1-5)
  - шість, сім, вісім, дев'ять, десять (6-10)
  - двадцять, тридцять, сорок (20, 30, 40)
  - сто, тисяча (100, 1000)
  - скільки (how many/how much)
  - коштує (costs — from коштувати)
  - гривня (hryvnia — Ukrainian currency)
  - рік, роки, років (year/years — age chunks)
  recommended:
  - п'ятдесят, шістдесят, сімдесят (50, 60, 70)
  - вісімдесят, дев'яносто (80, 90)
  - двісті, триста, п'ятсот (200, 300, 500)
  - копійка (kopek)
  - номер (number — phone/room)
  - нуль (zero)
activity_hints:
- type: fill-in
  focus: 'Write the number in words: 15 → п''ятнадцять, 47 → сорок сім'
  items: 10
- type: quiz
  focus: Скільки коштує? Match price tags to spoken prices.
  items: 8
- type: quiz
  focus: Скільки років? Match ages to descriptions.
  items: 6
- type: fill-in
  focus: Complete the phone number dictation
  items: 4
connects_to:
- a1-012 (This and That)
prerequisites:
- a1-009 (What Is It Like?)
grammar:
- Cardinal numbers 1-1000 (vocabulary, not morphology)
- Скільки коштує? question pattern
- 'Age chunk: Мені + number + років/роки/рік (memorized, not analyzed)'
- 'Irregular tens: сорок (40), дев''яносто (90)'
register: розмовний
references:
- title: ULP Season 1, Episode 5
  url: https://www.ukrainianlessons.com/episode5/
  notes: Numbers 1-10 pronunciation.
- title: ULP Season 1, Episode 9
  url: https://www.ukrainianlessons.com/episode9/
  notes: Numbers 11-100 and prices.
- title: Авраменко Grade 6, p.152
  notes: Числівники кількісні vs порядкові — basic classification.

</plan_content>

---



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
# Knowledge Packet: How Many?
**Module:** how-many | **Track:** A1

<wiki_context>
## Compiled Wiki Knowledge

The following articles from the project wiki provide compiled knowledge relevant to this module. Use them as authoritative context — they were compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).

### Вікі: pedagogy/a1/how-many.md

# Педагогіка A1: How Many



## Методичний підхід (Methodological Approach)

Навчання кількісних числівників на рівні A1 має бути зосереджено на негайному практичному застосуванні. Українські підручники для початкових класів демонструють підхід, що базується на поступовому ускладненні: від простого рахунку до вирішення елементарних математичних прикладів і практичних завдань, як-от відповіді на питання "Скільки тобі років?".

Основний принцип — зв'язок числівника з конкретним іменником. На відміну від англійської, де числівник є статичним, в українській мові він "живе" і впливає на форму іменника, з яким він пов'язаний. Тому вправи повинні з першого дня вводити числівники у словосполученнях, а не ізольовано (Джерело: `6-klas-ukrmova-litvinova-2023_s0248`).

Педагогічний підхід для L2-учнів має імітувати цей природний процес:
1.  **Візуальна асоціація:** Починати з рахунку предметів на малюнках (Джерело: `ext-article-4`).
2.  **Аудіо-повторення:** Багаторазове прослуховування та повторення числівників для закріплення вимови та наголосу (Джерело: `ext-article-5`, `3-klas-ukrainska-mova-vashulenko-2020-1_s0138`).
3.  **Контекстуалізація:** Введення числівників через діалоги та практичні ситуації: вік, час, номер телефону, ціна (Джерело: `ext-other_blogs-10`, `5-klas-ukrmova-uhor-2022-1_s0037`).
4.  **Ігрові елементи:** Використання простих математичних прикладів (`два плюс два дорівнює чотири`) як вправи на повторення (Джерело: `2-klas-ukrmova-kravcova-2019-1_s0092`, `5-klas-ukrmova-uhor-2022-1_s0037`).
5.  **Чітке правило:** Явно і багаторазово пояснювати правило "1, 2-4, 5+" для узгодження іменників, оскільки це є найбільшою трудністю для англомовних учнів (Джерело: `ext-article-1`).

Кінцева мета на рівні A1 — не знання всіх відмінкових форм, а впевнене використання числівників у називному відмінку для базового рахунку та в сталих виразах (вік, час).

## Послідовність введення (Introduction Sequence)

Порядок введення числівників має бути логічним і відповідати зростанню складності як самих чисел, так і граматичних правил, що їх супроводжують.

1.  **Step 1: Numbers 0-10.** Це основа. Вводяться числівники `нуль`, `один`, `два`, `три`, `чотири`, `п'ять`, `шість`, `сім`, `вісім`, `дев'ять`, `десять`. На цьому етапі основна увага приділяється правильній вимові та наголосу (Джерело: `5-klas-ukrmova-uhor-2022-1_s0036`).

2.  **Step 2: Gender Agreement for 1 and 2.** Відразу після введення базових числівників необхідно пояснити родові форми:
    *   `один` (чоловічий рід, напр., *один стіл*)
    *   `одна` (жіночий рід, напр., *одна книга*)
    *   `одне` (середній рід, напр., *одне вікно*)
    *   `два` (чоловічий/середній рід, напр., *два столи, два вікна*)
    *   `дві` (жіночий рід, напр., *дві книги*)
    Це фундаментальне правило, яке відрізняє українську від англійської, і його потрібно закріпити до переходу до складніших тем (Джерело: `10-klas-ukrmova-karaman-2018_s0299`, `6-klas-ukrmova-zabolotnyi-2020_s0164`).

3.  **Step 3: The "1, 2-4, 5+" Noun Agreement Rule.** Це найважливіше граматичне правило при вивченні числівників для L2-учнів.
    *   **1 + Іменник у Н.в. однини:** `один рік` (Джерело: `5-klas-ukrmova-uhor-2022-1_s0037`).
    *   **2, 3, 4 + Іменник у Н.в. множини:** `два роки`, `три студенти`, `чотири гривні` (Джерело: `5-klas-ukrmova-uhor-2022-1_s0037`, `6-klas-ukrmova-litvinova-2023_s0248`). Важливо наголосити, що для англомовних учнів це виглядає як "чотири студенти" (Nom.Pl), хоча історично це форма двоїни.
    *   **5+ (до 20) + Іменник у Р.в. множини:** `п'ять років`, `десять студентів`, `двадцять гривень` (Джерело: `6-klas-ukrmova-litvinova-2023_s0248`). Це вимагає знання закінчень родового відмінка множини.

4.  **Step 4: Numbers 11-20 and Tens.** Після засвоєння базових правил вводяться числівники на `-надцять` та круглі десятки (`двадцять`, `тридцять`...).
    *   `одинадцять` - `дев'ятнадцять` (Джерело: `3-klas-ukrainska-mova-vashulenko-2020-1_s0138`).
    *   `двадцять`, `тридцять`, `сорок`, `п'ятдесят` і т.д. (Джерело: `5-klas-ukrmova-uhor-2022-1_s0036`). Пояснити, що ці числівники також керують іменником у родовому відмінку множини.

5.  **Step 5: Practical Application - "How much/many?" and Age.** Вводиться питальне слово `Скільки?` та структура для відповіді про вік.
    *   `Скільки тобі років?`
    *   `Мені ... років/рік/роки.`
    Це знайомить учнів із давальним відмінком займенників (`мені`, `тобі`) у фіксованому, високочастотному контексті (Джерело: `ext-other_blogs-10`).

## Типові помилки L2 (Common L2 Errors)

Англомовні учні часто роблять передбачувані помилки, що виникають через інтерференцію з рідною мовою.

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| `два книга` | `дві книги` | Учні ігнорують рід іменника та не використовують жіночу форму `дві`. Також забувають про форму множини іменника. (Джерело: `6-klas-ukrmova-zabolotnyi-2020_s0164`) |
| `п'ять студент` | `п'ять студентів` | Найпоширеніша помилка. Після числівників 5 і більше іменник повинен стояти в родовому відмінку множини, а не в однині чи називному множини. (Джерело: `ext-article-1`, `6-klas-ukrmova-litvinova-2023_s0248`) |
| `п'ят**ь**надцять` | `п'ятнадцять` | Перенесення м'якого знака з `п'ять` у середину складного числівника. Правило: `ь` не пишеться в середині числівників `-надцять` та `-десят`. (Джерело: `6-klas-ukrmova-golub-2023_s0160`, `6-klas-ukrmova-zabolotnyi-2020_s0170`) |
| `одинадц**я**ть` (наголос на я) | `один**а́**дцять` | Неправильний наголос. У числівниках на `-а́дцять` наголос падає на склад `-на́-`. (Джерело: `6-klas-ukrmova-betsa-2023_s0005`, `3-klas-ukrainska-mova-vashulenko-2020-1_s0138`) |
| `Я маю двадцять років.` | `Мені двадцять років.` | Прямий переклад англійської конструкції "I have X years". В українській мові для позначення віку використовується давальний відмінок (`Мені`, `Тобі`, `Йому`). (Джерело: `ext-other_blogs-10`) |
| `чотир**ь**ма` | `чотирма` | Хибне додавання `ь` в орудний відмінок числівника `чотири` за аналогією до `трьох`, `п'ятьох`. Форма `чотирма` є винятком і пишеться без `ь`. (Джерело: `6-klas-ukrmova-avramenko-2023_s0176`) |

## Деколонізаційні застереження (Decolonization Notes)

**Це обов'язковий розділ.** Навчання української мови має відбуватися на її власних умовах, без опори на російську як "посередника" чи "базову" мову.

1.  **Жодних порівнянь з російською.** Заборонено пояснювати українські числівники через їхню схожість або відмінність від російських. Наприклад, ніколи не казати: "Українське *дев'яносто* — це як російське *девяносто*, але пишеться інакше". Учень має будувати нову лінгвістичну систему з нуля.

2.  **Фонетика з чистого аркуша.** Вимова українських числівників має базуватися на фонетичних правилах української мови. Не можна використовувати російські звуки як аналоги (напр., пояснювати український звук [и] через російський [ы]).

3.  **Історична самодостатність.** Підкреслюйте, що українські числівники, як і вся лексика, є частиною самостійної східнослов'янської мовної традиції. Такі слова, як `сорок` чи `дев'яносто`, мають власну історію в давньоруській мові і не є запозиченнями (Джерело: `ext-other_blogs-67`). Це не "спільні" з російською слова, а слова спільного спадку, який кожна мова розвинула по-своєму.

4.  **Уникати "суржикізмів" у прикладах.** Приклади речень та діалогів повинні бути природними для сучасної української мови. Не можна використовувати кальки з російської, навіть якщо вони поширені в побутовому мовленні. Наприклад, конструкції типу `Я рахую, що...` (калька з "Я считаю, что...") слід замінювати на `Я вважаю, що...` або `На мою думку...`.

Навчання числівників — це чудова нагода показати системну відмінність та самобутність української мови на базовому рівні.

## Словниковий мінімум (Vocabulary Boundaries)

На рівні А1 лексика для рахунку має бути простою, високочастотною та конкретною.

| Частина мови | Слово | Рівень | Приклад |
| :--- | :--- | :--- | :--- |
| **Іменники** | | | |
| | рік, роки, років | ★★★ | один рік, п'ять років |
| | гривня, гривні, гривень | ★★★ | дві гривні, десять гривень |
| | стіл, столи, столів | ★★★ | один стіл, три столи |
| | книга, книги, книг | ★★★ | одна книга, сім книг |
| | вікно, вікна, вікон | ★★★ | одне вікно, чотири вікна |
| | студент(ка) | ★★ | два студенти |
| | день, дні, днів | ★★ | три дні |
| | брат, сестра | ★★ | два брати, одна сестра |
| | кілометр | ★ | сорок кілометрів |
| | будинок | ★ | десять будинків |
| **Дієслова** | | | |
| | бути (є) | ★★★ | У мене є одна сестра. |
| | мати | ★★★ | Я маю двадцять гривень. |
| | коштувати | ★★ | Скільки це коштує? |
| | дорівнювати | ★ | два плюс два дорівнює чотири |
| **Прислівники/Питальні слова** | | | |
| | скільки | ★★★ | Скільки тобі років? |
| | плюс, мінус | ★ | п'ять плюс п'ять |

## Приклади з підручників (Textbook Examples)

Ці приклади демонструють формати вправ, які є ефективними та відповідають українській педагогічній традиції.

**1. Вправа: Математичні приклади (для відпрацювання вимови та форм)**
Прочитайте приклади. Запишіть (на вибір) два речення. Підкресліть числівники.
*   `Чотири плюс вісім дорівнює дванадцять.`
*   `Сто мінус сімдесят дорівнює тридцять.`
*   `П’ятдесят три плюс сімнадцять дорівнює сімдесят.`
(Джерело: `2-klas-ukrmova-kravcova-2019-1_s0092`)

**2. Вправа: Відповіді на питання (контекстуалізація)**
Запиши повні відповіді на запитання.
*   `Скільки дівчаток у вашому класі?`
*   `Скільки хлопчиків?`
*   `Скільки загалом дітей у вашому класі?`
(Джерело: `3-klas-ukrainska-mova-vashulenko-2020-1_s0138`)

**3. Вправа: Узгодження з іменником (ключове правило 1, 2-4, 5+)**
Прочитайте вголос словосполучення, правильно узгоджуючи числівник з іменником.
*   `будинок № 25 (двадцять п'ять)`
*   `будинок № 1 (один)`
*   `будинок № 4 (чотири)`
*   `квартира № 14 (чотирнадцять)`
*   `квартира № 2 (дві)`
(Адаптовано з Джерела: `5-klas-ukrmova-uhor-2022-1_s0037`)

**4. Вправа: Заміна цифр словами (письмове закріплення)**
Спишіть речення, замінюючи цифри словами. Зверніть увагу на правильність уживання іменників.
*   `Текст був на 294 сторінках.`
*   `Зустріч із 45 студентами відбулась у вівторок.`
*   `У школі навчається понад 1000 учнів і учениць.`
(Джерело: `6-klas-ukrmova-zabolotnyi-2020_s0177`)

## Пов'язані статті (Related Articles)

*   `pedagogy/a1/what-is-this`
*   `grammar/a1/noun-genders`
*   `grammar/a1/nominative-case`
*   `grammar/a2/genitive-case`
*   `pedagogy/a1/telling-time`

---

### Вікі: pedagogy/a1/many-things.md

# Педагогіка A1: Many Things



## Методичний підхід (Methodological Approach)
The concept of "many things" (множина, plural) is foundational and should be introduced early in A1, but methodically. The Ukrainian native pedagogy for early grades focuses on concrete, visual association and pattern recognition rather than abstract rule memorization.

The core principle is that the plural is a change in the **ending** of a word to signify more than one item. The approach should be:

1.  **Concrete to Abstract:** Start with physical objects in the classroom or in pictures. "Це стіл. А це столи." (This is a table. And these are tables). The visual contrast makes the concept intuitive.
2.  **Agreement over Declension:** Initially, focus on the agreement between nouns and adjectives in the nominative case. The key takeaway for learners is that adjectives must also change to reflect the plural noun they describe (`3-klas-ukrainska-mova-vashulenko-2020-1_s0128`). Ukrainian primary school textbooks emphasize this with tables showing gendered singular adjectives all converging on a single plural form (`4-klas-ukrayinska-mova-zaharijchuk-2021-1_s0064`).
3.  **Pattern Recognition:** Group nouns by their plural endings. Introduce the most common patterns first (masculine/feminine hard stems ending in **-и**) before moving to soft stems (**-і**) and neuter nouns (**-а, -я**) (`ext-ulp_youtube-261`).
4.  **Plurality in Context:** Introduce plural forms within simple sentence structures like "У мене є..." (I have...) or "Тут є..." (Here are...). For example, "У кімнаті є два стільці, книги і лампи" (`ext-ulp_youtube-258`). This immediately makes the grammar useful.
5.  **Verb Agreement:** Once the noun/adjective plural is established, introduce verb agreement. It's crucial to teach that a plural subject requires a plural verb form. A common construction in textbooks is combining two singular nouns to form a plural subject: "Кіт і собака **пустують** у дворі" (A cat and a dog **are playing** in the yard) (`8-klas-ukrmova-avramenko-2025_s0172`). The verb must be in the plural form.

Avoid overwhelming the learner with all case endings for plurals at once. A1 should master the nominative (who/what?) and basic counting rules, with other cases introduced gradually.

## Послідовність введення (Introduction Sequence)
This sequence builds from the simplest, most frequent patterns to more complex ones, mirroring the logic of Ukrainian primary education materials.

-   **Step 1: The Concept of Plural (Nominative Case)**
    -   Introduce "one" vs. "many" with high-frequency masculine and feminine nouns that follow the simplest rule: adding **-и**.
    -   **Examples:** `стіл` → `столи`, `кіт` → `коти`, `шафа` → `шафи`, `лампа` → `лампи` (`ext-ulp_youtube-261`).

-   **Step 2: The Soft Stem Plural (Nominative Case)**
    -   Introduce nouns ending in a soft consonant (e.g., -ць, -нь) or -я, which typically take an **-і** ending.
    -   **Why this order?** This is the next most common pattern.
    -   **Examples:** `стілець` → `стільці`, `учитель` → `учителі`, `полиця` → `полиці` (`ext-ulp_youtube-261`).

-   **Step 3: The Neuter Plural (Nominative Case)**
    -   Introduce neuter nouns, which are distinct in taking **-а** (for hard stems) or **-я** (for soft stems) in the plural.
    -   **Why this order?** Neuter nouns are a large and consistent group, but their plural ending is very different from masculine/feminine, so it needs its own focus.
    -   **Examples:** `вікно` → `вікна`, `ліжко` → `ліжка`, `море` → `моря` (`ext-ulp_youtube-261`, `5-klas-ukrmova-uhor-2022-1_s0030`).

-   **Step 4: Adjective Agreement in the Plural**
    -   Introduce the "magic" of the plural adjective ending **-і**. Show how it replaces all three gendered singular endings (`-ий`, `-а`, `-е`). This simplifies things for the learner.
    -   Use tables to demonstrate: `новий стіл`, `нова книга`, `нове вікно` → `нові столи, книги, вікна` (`4-klas-ukrmova-zaharijchuk_s0082`).

-   **Step 5: Basic Counting with Plurals**
    -   This is a critical, non-negotiable step for A1. Introduce the "1, 2-3-4, 5+" rule.
        -   **1:** Agrees in gender (`один стіл`, `одна книга`, `одне вікно`).
        -   **2, 3, 4:** Take the noun in **Nominative Plural** (`два столи`, `три книги`, `чотири вікна`).
        -   **5+:** Take the noun in **Genitive Plural** (`п'ять столів`, `шість книг`, `десять вікон`).
    -   At the A1 stage, it's sufficient to provide the genitive plural forms for memorization alongside the numbers, as the rules for forming it are complex. This rule is explicitly detailed in Ukrainian school grammar (`6-klas-ukrmova-litvinova-2023_s0248`).

-   **Step 6: Essential Irregular Plurals**
    -   Introduce a small, curated list of high-frequency irregular plurals that don't follow the main patterns.
    -   **Examples:** `людина` → `люди`, `дитина` → `діти`, `друг` → `друзі`, `око` → `очі` (`ext-ulp_youtube-258`).

## Типові помилки L2 (Common L2 Errors)
For English-speaking learners, plurals present several predictable challenges. Addressing them proactively is key.

| ❌ Помилково (Incorrect) | ✅ Правильно (Correct) | Чому (Why) |
| :--- | :--- | :--- |
| `Я бачу два *стіл*.` | `Я бачу два **столи**.` | English uses the singular form after a number ("one table", "two table**s**"), but Ukrainian uses the **nominative plural** for numbers 2, 3, and 4. The noun must change. (Джерело: `6-klas-ukrmova-litvinova-2023_s0248`) |
| `У мене є п'ять *столи*.` | `У мене є п'ять **столів**.` | This is the second half of the counting rule. Numbers 5 and up require the **genitive plural**, not the nominative plural. This is a fundamental concept with no direct English equivalent and must be drilled. (Джерело: `6-klas-ukrmova-litvinova-2023_s0248`) |
| `Кіт і собака *сидить* тут.` | `Кіт і собака **сидять** тут.` | In English, two singular subjects joined by "and" take a plural verb. The same is true in Ukrainian. Learners often forget to change the verb, leaving it in the 3rd person singular. A plural subject demands a plural verb. (Джерело: `8-klas-ukrmova-avramenko-2025_s0172`) |
| `Це *новий* книги.` | `Це **нові** книги.` | Adjectives **must** agree in number with the noun they describe. The singular adjective `новий` cannot describe the plural noun `книги`. The adjective must take the universal plural ending `-і`. (Джерело: `4-klas-ukrmova-zaharijchuk_s0082`) |
| `Тут *кни́жка* і *ру́чка*.` | `Тут **книжки́** і **ру́чки**.` | Learners often ignore or misapply stress shifts in the plural. The stress in `кни́жка` (singular) moves to the end in the plural `книжки́`. This is a common feature and cannot be ignored for correct pronunciation. (Джерело: `ext-ulp_youtube-29`) |
| `Це мої *друг*.` | `Це мої **друзі**.` | Learners may try to apply a regular plural ending (`-и`) to an irregular noun. High-frequency irregulars like `друг` → `друзі` must be memorized as vocabulary items. (Джерело: `ext-ulp_youtube-258`) |

## Деколонізаційні застереження (Decolonization Notes)
**MANDATORY:** Teaching Ukrainian plurals requires a strict decolonization framework to avoid common pedagogical pitfalls that center or rely on Russian.

1.  **Teach Ukrainian on Its Own Terms:** Never introduce Ukrainian plurals by comparing them to Russian (e.g., "Ukrainian `-и` is like Russian `-ы`"). This frames Ukrainian as a derivative and builds an incorrect mental model. The learner must build a new, separate Ukrainian system from zero.
2.  **Stress is Not Russian:** Emphasize that plural stress patterns in Ukrainian are independent and often differ from Russian cognates. A learner's knowledge of Russian stress can be a hindrance, not a help. For example, `по́казник` in Ukrainian has stress on the second syllable, unlike the Russian equivalent (`ext-ulp_youtube-29`). The writer must provide audio and clear markings for all new vocabulary.
3.  **Correct Etymology:** Acknowledge shared Slavic roots neutrally. When a word exists in both Ukrainian and Russian, present it as part of a common linguistic heritage, not as a "Russian word used in Ukrainian" (`ext-ulp_youtube-139`). The default assumption must be that the word is native to Ukrainian unless proven otherwise.
4.  **Avoid Surzhyk and Russianisms:** The writer must be vigilant in using vocabulary. For example, use `фарту́х` (correct Ukrainian) not `фа́ртук` (Russian stress/form) (`ext-ulp_youtube-29`). The vocabulary provided in the A1 modules must be vetted to be purely Ukrainian.
5.  **Pluralia Tantum as a Feature:** When introducing nouns that only exist in the plural (pluralia tantum), like `двері` (doors), `окуляри` (glasses), or city names like `Суми` (`ext-komik_istoryk-67`), present this as a normal and interesting feature of Ukrainian, not as an oddity.

## Словниковий мінімум (Vocabulary Boundaries)
This vocabulary is appropriate for introducing and practicing plurals at the A1 level.

**Іменники (Nouns):**
-   ★★★ `стіл` (table), `стілець` (chair), `книга` (book), `кімната` (room), `вікно` (window), `двері` (door), `ліжко` (bed), `будинок` (house), `друг` (friend), `день` (day), `рік` (year), `людина` (person).
-   ★★☆ `шафа` (wardrobe), `полиця` (shelf), `лампа` (lamp), `картина` (picture), `фотографія` (photo), `син` (son), `брат` (brother), `сусід` (neighbor), `олівець` (pencil), `зошит` (notebook), `урок` (lesson).
-   ★☆☆ `вазон` (flowerpot), `квітка` (flower), `дерево` (tree), `кіт` (cat), `собака` (dog), `риба` (fish).

**Прикметники (Adjectives):**
-   ★★★ `новий` (new), `старий` (old), `великий` (big), `маленький` (small), `гарний` (good, beautiful), `добрий` (good, kind).
-   ★★☆ `цікавий` (interesting), `український` (Ukrainian), `високий` (tall/high), `зелений` (green), `синій` (blue), `білий` (white), `чорний` (black).
-   ★☆☆ `зручний` (comfortable), `світлий` (light/bright), `теплий` (warm).

**Дієслова (Verbs):**
-   ★★★ `бути` (to be, especially `є`), `мати` (to have), `жити` (to live).
-   ★★☆ `стояти` (to stand), `лежати` (to lie), `бачити` (to see), `робити` (to do).

## Приклади з підручників (Textbook Examples)
These exercise formats are adapted from Ukrainian primary school textbooks and are ideal for A1 learners.

1.  **Вправа: Утвори множину (Exercise: Form the Plural)**
    -   **Мета:** Practice basic singular-to-plural conversion for nouns and adjectives.
    -   **Формат:** Fill-in-the-blanks.
    -   **Завдання:** "Допишіть закінчення, щоб утворити множину." (Add the endings to form the plural.)
        -   `Акваріумн.. рибка` → `Акваріумн.. рибки`
        -   `Маленьк.. окунь` → `Маленьк.. окуні`
        -   `Хиж.. щука` → `Хиж.. щуки`
        -   `Вусат.. сом` → `Вусат.. соми`
    -   *(Джерело: Адаптовано з `3-klas-ukrainska-mova-kravtsova-2020-1_s0069`)*

2.  **Вправа: Один → Багато (Exercise: One → Many)**
    -   **Мета:** Reinforce adjective-noun agreement across genders.
    -   **Формат:** Table completion.
    -   **Завдання:** "Заповніть таблицю за зразком." (Fill the table according to the model.)
| Однина (Singular) | Множина (Plural) |
| :--- | :--- |
| `солодкий торт` (ч.р.) | `солодк.. торти` |
| `солодка слива` (ж.р.) | `солодк.. сливи` |
| `солодке яблуко` (с.р.) | `солодк.. яблука` |
    -   *(Джерело: Адаптовано з `4-klas-ukrayinska-mova-zaharijchuk-2021-1_s0064`)*

3.  **Вправа: Порахуй предмети (Exercise: Count the Items)**
    -   **Мета:** Practice the crucial 2-3-4 vs. 5+ counting rule.
    -   **Формат:** Combine numbers with nouns.
    -   **Завдання:** "Напишіть правильну форму іменника." (Write the correct form of the noun.)
        -   `два (зошит)` → __________ (`два зошити`)
        -   `три (клієнт)` → __________ (`три клієнти`)
        -   `чотири (смартфон)` → __________ (`чотири смартфони`)
        -   `п'ять (урок)` → __________ (`п'ять уроків`)
        -   `десять (учень)` → __________ (`десять учнів`)
    -   *(Джерело: Адаптовано з `6-klas-ukrmova-litvinova-2023_s0248`)*

4.  **Вправа: Що є в кімнаті? (Exercise: What is in the room?)**
    -   **Мета:** Use plurals in a descriptive context.
    -   **Формат:** Picture description or text completion.
    -   **Завдання:** "Подивіться на малюнок і опишіть кімнату, використовуючи слова в множині." (Look at the picture and describe the room, using words in the plural.)
    -   **Приклад тексту:** "У кімнаті є два (ліжко), один (стіл) і чотири (стілець). На стіні висять (картина) і (фотографія). На полицях стоять (книга)." (In the room there are two beds, one table, and four chairs. On the wall hang pictures and photographs. On the shelves stand books.)
    -   *(Джерело: Адаптовано з `ext-ulp_youtube-258` та `7-klas-istoria-ukr-pometun-2024_s0072`)*

## Пов'язані статті (Related Articles)
-   [[pedagogy/a1/noun-genders|Педагогіка A1: Noun Genders]]
-   [[pedagogy/a1/adjective-agreement|Педагогіка A1: Adjective Agreement]]
-   [[pedagogy/a1/numbers-and-counting|Педагогіка A1: Numbers and Counting (1-100)]]
-   [[pedagogy/a1/nominative-case|Педагогіка A1: The Nominative Case]]
-   [[pedagogy/a2/genitive-case|Педагогіка A2: The Genitive Case]]
</wiki_context>

## Plan References

- 
- 
- 

</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Числа 1-20 (Numbers 1-20)` (~300 words)
- `## Десятки і сотні (Tens and Hundreds)` (~300 words)
- `## Підсумок — Summary` (~300 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 10-20% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose. Introduce Ukrainian grammar terms bolded with translation on first use.
- UKRAINIAN CONTENT: Words and short phrases bolded inline: "The word **книга** (book) is feminine."
- TABLES: Vocabulary tables, word families, simple paradigm tables.
- STRUCTURAL RULE: Every paragraph is English. Ukrainian words/phrases appear inline bolded. Full Ukrainian sentences (3+ words with a verb) go in tables or bulleted example lists with English gloss.
Ukrainian sentences max 10 words.

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
  1. **At a bakery — ordering bread, pastries, and cakes for a family gathering. Count: один хліб (m, bread), одна булочка (f, bun), одне тістечко (n, pastry). Prices in гривні. Ask: Скільки коштує торт? А три булочки?**
     Speakers: Покупець, Пекар (baker)
     Why: Скільки коштує? with торт(m), булочка(f), тістечко(n), хліб(m)
  2. **Counting items in a school backpack before class — ручка (f, pen), олівець (m, pencil), зошит (m, notebook), підручник (m, textbook).**
     Speakers: Учень (student), Мама
     Why: Numbers with school supplies: один олівець, дві ручки, п'ять зошитів

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

GRAMMAR CONSTRAINTS (A1.2 — My World, M08-M14):
Noun gender, adjective agreement, plurals, numbers, demonstratives.

ALLOWED:
- Це + noun, У мене є/немає
- Adjective-noun agreement (nominative only)
- Numbers 1-1000
- Demonstratives цей/ця/це/ці
- Question words: Який? Яка? Яке? Скільки?
- Fixed verbal phrases from A1.1 (Мене звати, працювати)

BANNED: Verb conjugation (taught in A1.3), past/future tense, cases beyond nominative,
participles, passive voice, subordinate clauses

### Vocabulary

**Required:** один, два, три, чотири, п'ять (1-5), шість, сім, вісім, дев'ять, десять (6-10), двадцять, тридцять, сорок (20, 30, 40), сто, тисяча (100, 1000), скільки (how many/how much), коштує (costs — from коштувати), гривня (hryvnia — Ukrainian currency), рік, роки, років (year/years — age chunks)
**Recommended:** п'ятдесят, шістдесят, сімдесят (50, 60, 70), вісімдесят, дев'яносто (80, 90), двісті, триста, п'ятсот (200, 300, 500), копійка (kopek), номер (number — phone/room), нуль (zero)

### Pronunciation Videos

**Do NOT embed YouTube videos in your prose.** A downstream ENRICH tool automatically places pronunciation videos from the plan. If you embed `<YouTubeVideo>` components, they will be duplicated. Simply reference the videos' existence when relevant (e.g., "Watch the pronunciation video for this letter") but do NOT insert `<YouTubeVideo>` tags.

Available videos (for reference only — ENRICH handles placement):


---

### Style Reference (match this tone and structure)

Look at the text on this page. What you are seeing are letters. Now, say a word out loud. What you just produced is a sound. This distinction is the absolute foundation of the Ukrainian language. There is a golden rule taught to every Ukrainian student in the first grade: **Ми чуємо і вимовляємо звуки, а бачимо і пишемо літери**. We hear and pronounce sounds, but we see and write letters.

These friendly letters are **А**, **О**, **К**, **М**, and **Т**. Because they are so familiar, you can start reading real Ukrainian words immediately. Look at the word **мама**. It means mother, and you already know how to read it. Now look at **тато**. It means father.

*Note: English prose dominates. Ukrainian words appear bolded inline. Short Ukrainian sentences illustrate one concept at a time. No conjugated verbs. Tables and bulleted lists for vocabulary.*



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
## Діалоги — Dialogues (~330 words total)
- P1 (~110 words): Introduction to the utility of numbers in Ukrainian daily life. We count things everywhere: at a bakery (один хліб, одна булочка, одне тістечко), in a backpack (один олівець, дві ручки), or at a market. Numbers allow us to navigate prices and personal details like age.
- P2 (~110 words): Dialogue 1 — At a market stall. A customer asks about prices for bags of different sizes using "Скільки коштує?". Key vocabulary: сумка (bag), маленька (small), ціна (price). Numbers used: сто п'ятдесят (150), двісті (200).
- P3 (~110 words): Dialogue 2 — Meeting someone and sharing age. This extends the greetings from M05. Introducing the age question "Скільки тобі років?" and the response chunk "Мені...". Numbers used: вісімнадцять (18), двадцять п'ять (25), тридцять два (32).

## Числа 1-20 — Numbers 1-20 (~330 words total)
- P1 (~80 words): The foundation: numbers 1-10. Focus on the phonetics of the apostrophe in п'ять and дев'ять, and the distinct [i] sound in сім and вісім (avoiding the Russian 'e' sound).
- P2 (~100 words): Gender agreement for "one" and "two" (Wiki Step 2). Explain that 'one' must match the noun's gender: один стіл (m), одна книга (f), одне вікно (n). Similarly, 'two' has a feminine form: два столи but дві книги.
- P3 (~90 words): Numbers 11-20 and the "-надцять" pattern. Explain the historical "one on ten" logic. Emphasize the stress shift: the stress always falls on the "на" syllable (одина́дцять, дванадця́ть).
- P4 (~60 words): Counting classroom objects to practice noun endings as chunks. We don't learn the Genitive case yet, just the patterns: один зошит, два зошити, п'ять зошитів.
- <!-- INJECT_ACTIVITY: fill-in-numbers-words --> [fill-in, Write the number in words: 15 → п'ятнадцять, 12 → дванадцять, 10 items]

## Десятки і сотні — Tens and Hundreds (~330 words total)
- P1 (~110 words): The tens (20-90). Introduce the regular patterns (п'ятдесят, шістдесят) and the critical irregulars: сорок (40) and дев'яносто (90). Explain how to combine them: сорок сім (47), дев'яносто дев'ять (99).
- P2 (~100 words): The hundreds (100-1000) for high-value items and prices. List the forms: сто, двісті, триста, чотириста, п'ятсот, тисяча. Note the spelling of двісті (not "двасто").
- P3 (~120 words): Money and currency. Introduce "гривня" (hryvnia). Provide the memorized patterns for the 1, 2-4, 5+ rule: одна гривня, дві/три/чотири гривні, п'ять/десять/сто гривень. Teach the question "Скільки це коштує?".
- <!-- INJECT_ACTIVITY: quiz-prices --> [quiz, Match price tags (e.g., 250₴, 400₴) to their Ukrainian written forms, 8 items]

## Підсумок — Summary (~330 words total)
- P1 (~90 words): Recapping Age. Explain that "Мені... років" is a fixed chunk. Provide the three variants for endings based on the last digit: 1 (рік), 2-4 (роки), 5-0 (років). Examples: двадцять один рік, тридцять три роки, сорок років.
- P2 (~80 words): Phone numbers. Explain the use of "нуль" (zero) and how numbers are typically read in blocks of two or three digits. Example: 067 (нуль шістдесят сім) or 0-9-7 (нуль, дев'ять, сім).
- P3 (~80 words): Summary of "Скільки" functions. It covers both "how many" (quantity) and "how much" (price). Comparison of "Скільки книг?" vs "Скільки коштує книга?".
- P4 (~80 words): Self-check list:
  - Can you say your age? (Мені ... років)
  - Can you ask for a price? (Скільки коштує ...?)
  - Can you count to ten without looking?
  - Can you say your phone number in Ukrainian?
- <!-- INJECT_ACTIVITY: quiz-age-matching --> [quiz, Match ages in digits to the correct sentence (рік/роки/років), 6 items]
- <!-- INJECT_ACTIVITY: fill-in-phone-numbers --> [fill-in, Complete the phone number sequences based on audio/text prompts, 4 items]

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
