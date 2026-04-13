

---

## Your Writing Identity

**You are: Lead Ukrainian Instructor.** Your persona is *The Conversation Partner*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **33: Скільки?** (A2, A2.5 [Case Synthesis and Plurals]).

**Target: 2000–3000 words** of prose (Ukrainian examples count toward word total, headings and exercise placeholders do not).

---

## Step 1: Pacing Plan (output this FIRST)

Before writing any content, output a `<pacing_plan>` block. Evaluate each section from the plan and commit to a word budget. This prevents frontloading early sections and rushing later ones.

```
<pacing_plan>
Section 1 "Title": ~XXX words — [1-sentence content focus]
Section 2 "Title": ~XXX words — [1-sentence content focus]
...
Summary: ~150 words
Total: 2000+ words
</pacing_plan>
```

Then begin writing the module content. Follow your own pacing plan — each section must hit its word budget (±10%).

---

## 9 Hard Rules

1. **IMMERSION TARGET: 55-75% Ukrainian — Ukrainian dominates. English for abstract grammar only.** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if immersion is outside this range. For A1 early modules, the learner cannot read Cyrillic — English must dominate. For A2+, Ukrainian must carry a significant share — add Ukrainian Reading Practice blocks, dialogues, and example paragraphs to reach the target. Too little Ukrainian fails audit just as much as too much.
2. **EVERY plan point MUST appear in your output.** The plan's `content_outline` lists specific points for each section. You MUST cover ALL of them — every textbook reference, every notation, every example. If the plan says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping plan points is the #1 reason modules get rejected. Before submitting, mentally check each plan point against your output.
3. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
4. **You are a warm, encouraging teacher.** Natural teacher phrasing ("Let us look at...", "Have you noticed...") is fine. What to AVOID: self-congratulatory openers ("Welcome to A2! Congratulations!"), gamified language ("You have unlocked...", "You now possess..."), and empty filler sentences that add words but zero information. Every sentence should teach something specific to Ukrainian.
5. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
6. **Place exercise markers only** — do NOT write exercises directly. Place `<!-- INJECT_ACTIVITY: {id} -->` markers where exercises should appear. A separate pipeline step generates the actual exercises from the plan's activity_hints.
7. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
8. **Hit the word target** — you MUST write 2000–3000 words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
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
module: a2-033
level: A2
sequence: 33
slug: plural-genitive
version: '1.0'
title: Скільки?
subtitle: Родовий відмінок множини — найскладніший відмінок
focus: grammar
pedagogy: PPP
phase: A2.5 [Case Synthesis and Plurals]
word_target: 2000
objectives:
  - Learner can form the Genitive plural for I відміна nouns, applying the zero 
    ending correctly and inserting fleeting vowels where needed (сестер, 
    книжок).
  - Learner can form the Genitive plural for II відміна nouns using the correct 
    ending (-ів/-їв for most masculine, zero ending for most neuter, -ей for 
    soft-stem masculine).
  - Learner can use quantity expressions (скільки, багато, мало, кілька, 
    декілька, numerals 5+) with the Genitive plural correctly.
  - Learner can produce short utterances about quantities in everyday contexts 
    (shopping, describing a room, talking about family).
dialogue_situations:
  - setting: 'School cafeteria inventory — counting remaining items: Скільки тарілок
      (f, plates)? Двадцять. Виделок (f, forks)? П''ятнадцять. Ложок (f, spoons)?
      Десять. Склянок (f, glasses)? Немає склянок!'
    speakers:
      - Завідувач їдальні (cafeteria manager)
      - Помічник
    motivation: 'Genitive plural: тарілка→тарілок, виделка→виделок, склянка→склянок'
content_outline:
  - section: 'Чому родовий множини такий складний? (Why Is the Genitive Plural So
      Hard?)'
    words: 400
    points:
      - 'Overview: Gen.Pl. has THREE possible endings — zero (нульове закінчення),
        -ів/-їв, -ей — plus fleeting vowels. No single rule covers all nouns.'
      - 'Why it matters: Gen.Pl. appears after numbers 5+, after багато/мало/кілька/скільки,
        and in many prepositional phrases. It is the most common plural case.'
      - 'Strategy: learn by відміна and gender, with the most frequent words first.'
  - section: 'I відміна: нульове закінчення (First Declension: Zero Ending)'
    words: 500
    points:
      - 'Most I відміна nouns (feminine -а/-я) take zero ending: книга → книг, зірка
        → зірок, вишня → вишень.'
      - 'Fleeting vowels appear when consonant clusters form: сестра → сестер, земля
        → земель, пісня → пісень, казка → казок.'
      - 'Exceptions with -ів or -ей: суддя → суддів, сім''я → сімей, стаття → статей.'
      - 'Drill: form Gen.Pl. for common I відміна nouns with and without fleeting
        vowels.'
  - section: 'II відміна: -ів, нульове, -ей (Second Declension: Three Patterns)'
    words: 600
    points:
      - 'Masculine hard stems: -ів (столів, братів, учнів, днів).'
      - 'Masculine soft stems: -ів or -ей (учителів, but гостей, коней).'
      - 'Neuter -о: zero ending, often with fleeting vowels (вікон, слів, but міст
        — no fleeting vowel).'
      - 'Neuter -е/-я: -ів/-їв (морів, подвір''їв) or zero (сердець, яєць).'
      - 'The -ин/-їн suffix disappears: громадянин → громадян, киянин → киян.'
  - section: 'Скільки чого? Кількість у житті (How Much of What? Quantity in Daily
      Life)'
    words: 500
    points:
      - 'Pattern: скільки/багато/мало/кілька/декілька + Gen.Pl. — Скільки студентів?
        Багато книжок. Мало грошей. Кілька друзів.'
      - 'Numbers 5+ take Gen.Pl.: п''ять яблук, десять студентів, двадцять гривень.'
      - 'Contrast with 2-4 (Nom.Pl.): два студенти vs. п''ять студентів; три книжки
        vs. сім книжок.'
      - 'Dialogues: at a store asking for quantities, describing what is in a room,
        talking about family members.'
vocabulary_hints:
  required:
    - родовий відмінок (genitive case)
    - нульове закінчення (zero ending)
    - кількість (quantity, amount)
    - багато (a lot, many)
    - мало (few, little)
    - кілька (a few, several)
    - декілька (a few, several)
    - скільки (how many, how much)
    - гроші (money)
    - гривня (hryvnia)
  recommended:
    - вставний голосний (fleeting vowel)
    - виняток (exception)
    - десяток (a dozen, ten-unit)
activity_hints:
  - type: fill-in
    focus: Form the Genitive plural from given nouns (mixed відміни), inserting 
      fleeting vowels where needed
    items: 8
  - type: quiz
    focus: Choose the correct Gen.Pl. form in quantity expressions (багато ___, 
      п'ять ___)
    items: 8
  - type: match-up
    focus: Match singular nouns with their correct Genitive plural forms
    items: 8
  - type: true-false
    focus: Judge whether a given Gen.Pl. form is correct or incorrect (common 
      errors like книгів instead of книг)
    items: 8
references:
  - title: Літвінова Grade 6, с. 160
    notes: Gen.Pl. endings for II відміна with full table and exercises
  - title: Заболотний Grade 6, §62
    notes: Gen.Pl. of I відміна — zero ending, fleeting vowels, exceptions
  - title: "ULP: Genitive Plural"
    url: "https://www.ukrainianlessons.com/genitive-case/"
    notes: Practical examples of Gen.Pl. in everyday speech

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
- Confirmed: родовий, відмінок, нульове, закінчення, кількість, багато, мало, кілька, декілька, скільки, гроші, гривня, вставний, голосний, виняток, десяток.
- Not found: None.

## Grammar Rules
- **Genitive Plural Endings**: Правопис § 95-97 (I відміна), § 101-103 (II відміна) — I declension nouns (-а/-я) typically have a zero ending (нульове закінчення): *книг, зірок, вишень*. II declension masculine nouns take *-ів/-їв* (*столів, батьків*) or *-ей* (*коней, гостей*). Neuter nouns in *-о* take a zero ending (*вікон, слів*).
- **Fleeting Vowels (Вставні голосні)**: Правопис § 95, 103 — In nouns with zero endings, vowels **о, е** (or **и** in some cases) may appear to break up consonant clusters: *сестра → сестер, казка → казок, вікно → вікон*.
- **Quantity and Numerals**: Правопис § 106, 122 — Quantity words (*багато, мало, кілька, декілька, скільки*) and numerals from **5 upwards** govern the Genitive Plural: *багато людей, п’ять гривень, скільки книжок*.

## Calque Warnings
- **приймати участь**: Calque — Correct form: **брати участь**.
- **пару слів**: Often a calque from Russian "пару слов" — Better form: **кілька слів**.
- **багато грошей**: OK — Standard usage found in textbooks (e.g., Grade 6, Golub).
- **декілька людей**: OK — Standard usage for indefinite small quantities.

## CEFR Check
- **багато, мало, скільки, гроші, гривня**: A1 — OK for A2 module.
- **кілька, декілька, десяток**: A2 — OK.
- **кількість, виняток**: A2/B1 — Acceptable for grammar explanations and synthesis at A2.5 level.
- **родовий відмінок, нульове закінчення, вставний голосний**: Metalanguage — Appropriate for linguistic instruction at A2.
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
# Knowledge Packet: Скільки?
**Module:** plural-genitive | **Track:** A2

<wiki_context>
## Compiled Wiki Knowledge

The following articles from the project wiki provide compiled knowledge relevant to this module. Use them as authoritative context — they were compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).

### Вікі: grammar/a2/plural-genitive.md

# Граматика A2: Скільки?



## Як це пояснюють у школі (How Schools Teach This)

The grammar of counting in Ukrainian is foundational and introduced early. The core principle, taught from elementary grades, is that the form of the noun depends on the number that precedes it. This concept is often called "узгодження числівників з іменниками" (agreement of numerals with nouns).

The approach can be broken down into three main rules:

1.  **The "1" Rule:** The numeral `один` (one) behaves like an adjective. It agrees in gender, case, and number with the noun it modifies.
    *   `один стіл` (masculine)
    *   `одна книга` (feminine)
    *   `одне вікно` (neuter)

2.  **The "2, 3, 4" Rule:** The numerals `два`/`дві` (two), `три` (three), and `чотири` (four) require the noun to be in the **називний відмінок множини (Nominative Plural)**. Textbooks for grades 4-6 introduce this with simple examples like `два пальці` or `чотири літаки` (Source 26).
    *   `два стільці` (two chairs)
    *   `три сестри` (three sisters)
    *   `чотири вікна` (four windows)
    *   A significant exception, noted in advanced grammar (Source 26), is the word `друг`, which takes the **родовий відмінок однини (Genitive Singular)**: `два друга`, `три друга`, `чотири друга`.

3.  **The "5+" Rule:** All numerals from `п'ять` (five) onwards, as well as indefinite numerals like `багато` (many), `кілька` (a few), and the question word `скільки` (how many), require the noun to be in the **родовий відмінок множини (Genitive Plural)**. This is the most complex part because forming the Genitive Plural is not always straightforward. School grammar (e.g., Source 24, 32) dedicates significant attention to the various endings (`-ів`, `-ей`, or нульове закінчення/zero ending) and the sound changes that occur. For example, `п'ять грамів` or `кілька сотень` (Source 10).

4.  **Predicate Agreement:** At a more advanced stage (Grade 8), students learn that when a numeral + noun phrase is the subject, the verb (predicate) can be either singular or plural. The singular form emphasizes the quantity as a single unit, while the plural form emphasizes the individual actors performing the action (Source 22).
    *   `П'ятеро дітей **нудьгувало**.` (Five children **was** bored - focus on the group's state).
    *   `П'ятеро дітей **нудьгували**.` (Five children **were** bored - focus on the individuals).

This progressive approach—from simple agreement with `один` to the complex Genitive Plural with `5+`—is standard across the Ukrainian curriculum.

## Повна парадигма (Full Paradigm)

The central challenge in answering "Скільки?" is correctly forming the **родовий відмінок множини (Genitive Plural)** for nouns, as this case is required after most numbers (5+) and quantity words. The ending depends on the noun's declension, gender, and stem.

### І Відміна (1st Declension)
*(Mainly feminine, some masculine/common gender nouns ending in -а, -я)*

| Group | Stem Ends In | Gen. Pl. Ending | Rule/Example | Source |
| :--- | :--- | :--- | :--- | :--- |
| Тверда (Hard) | Hard Consonant | **-ø** (zero) | `машина` → `машин` <br> `дорога` → `доріг` (with `o`→`i` alternation) | (Source 24, 29) |
| М'яка (Soft) | Soft Consonant | **-ь** or **-ø** | `вишня` → `вишень` (with inserted `е`) <br> `земля` → `земель` | (Source 24, 29) |
| Мішана (Mixed) | Шиплячий (Shibilant) | **-ø** | `круча` → `круч` <br> `тиша` → `тиш` | (Source 29) |
| Special Cases | `-я` after vowel, etc. | **-ей** | `стаття` → `статей` <br> `сім'я` → `сімей` | (Source 29) |
| Special Cases | Masculine | **-ів** | `сусіда` → `сусідів` <br> `тесля` → `теслів` | (Source 29) |

### ІІ Відміна (2nd Declension)
*(Masculine nouns with zero/-о ending; neuter nouns with -о, -е, -я endings)*

| Gender | Stem Type | Gen. Pl. Ending | Rule/Example | Source |
| :--- | :--- | :--- | :--- | :--- |
| Чоловічий (Masc.) | Most | **-ів / -їв** | `батько` → `батьків` <br> `трамвай` → `трамваїв` | (Source 18, 32) |
| Середній (Neuter) | `-o` | **-ø** (zero) | `місто` → `міст` <br> `село` → `сіл` (with `е`→`і`) | (Source 18, 32) |
| Середній (Neuter) | `-е` | **-ів / -їв** or **-ø** | `море` → `морів` <br> `поле` → `піль` (from *полів*) | (Source 32) |
| Both | Irregular | **-ей** | `гість` → `гостей` <br> `кінь` → `коней` | (Source 32) |
| Both | Paired body parts | **-ей** or **-ø** | `око` → **`очей`** / **`віч`** <br> `плече` → **`плечей`** / **`пліч`** | (Source 32) |
| Special Case | Masc. `*-in` suffix loss | **-ø** | `киянин` → `киян` <br> `селянин` → `селян` | (Source 32) |

### ІІІ Відміна (3rd Declension)
*(Feminine nouns with zero ending, and `мати`)*

| Stem Ends In | Gen. Pl. Ending | Rule/Example | Source |
| :--- | :--- | :--- | :--- |
| Any consonant | **-ей** | `ніч` → `ночей` (with `і`→`о`) <br> `подорож` → `подорожей` <br> `радість` → `радостей` | (Source 24) |

### IV Відміна (4th Declension)
*(Neuter nouns in -а, -я with suffixes -ат-, -ят-, -ен- in declension)*

| Stem Suffix | Gen. Pl. Ending | Rule/Example | Source |
| :--- | :--- | :--- | :--- |
| `-ат-` / `-ят-` | **-ø** (zero) | `лоша` → `лошат` <br> `кошеня` → `кошенят` | (Source 28) |
| `-ен-` | **-ø** (zero) | `ім'я` → `імен` | (Source 28) |

### Іменники, що мають лише форму множини (*Pluralia Tantum*)

| Ending Group | Gen. Pl. Ending | Example | Source |
| :--- | :--- | :--- | :--- |
| Group 1 | **-ів / -їв** | `окуляри` → `окулярів` <br> `хитрощі` → `хитрощів` | (Source 30) |
| Group 2 | **-ей** | `гроші` → `грошей` <br> `двері` → `дверей` | (Source 30) |
| Group 3 | **-ø** (zero) | `ворота` → `воріт` <br> `Карпати` → `Карпат` | (Source 30) |

## Частотність і пріоритети (Frequency & Priorities)

For A2/B1 learners, mastering the grammar of "скільки" should be prioritized as follows:

1.  **Core Rule Distinction (Highest Priority):** The learner MUST internalize the fundamental split:
    *   **2, 3, 4 + Nominative Plural**
    *   **5+ & `кілька`/`багато` + Genitive Plural**
    This is the most frequent and basic requirement for producing correct quantitative phrases.

2.  **Genitive Plural of Common Nouns (High Priority):** Learners should focus on the most common Genitive Plural patterns first.
    *   **ІІ Declension Masculine `-ів`:** `студентів, доларів, метрів, кілограмів`. This is a very productive and frequent ending.
    *   **І Declension Feminine Zero Ending:** `хвилин, гривень, книжок, машин`. This includes mastering the inserted vowels (`-ок`, `-ень`).

3.  **Key Irregular Forms (Medium Priority):** Certain high-frequency nouns have irregular or unique Genitive Plural forms that must be memorized.
    *   `люди` → `людей`
    *   `роки` → `років`
    *   `очі` → `очей`
    *   `гроші` → `грошей`
    *   The `друг` exception with 2, 3, 4 (`два друга`).

4.  **Predicate Agreement Nuance (B1 Level):** Understanding the choice between a singular and plural verb (`п'ять студентів прийшло` vs. `прийшли`) is a B1-level goal. A2 learners should first master forming the subject phrase correctly; either predicate form will be understood.

## Типові помилки L2 (Common L2 Errors)

English speakers often struggle with the case changes required by Ukrainian numerals, leading to predictable errors.

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| `Я купив *п'ять книги*.` | `Я купив **п'ять книжок**.` | The learner incorrectly uses the Nominative Plural (`книги`) after `п'ять`, instead of the required Genitive Plural (`книжок`). This is a direct transfer of the English pattern "five books," which does not change the noun's form. |
| `У мене є *два брата*.` | `У мене є **два брати**.` | The learner incorrectly applies the Genitive Singular (`брата`), often due to influence from Russian grammar where this is the standard. In Ukrainian, `два` governs the Nominative Plural for most nouns. |
| `Тут сидять *три жінки*.` | `Тут сидять **три жінки**.` | While the form is correct (`жінки` is Nominative Plural), the learner might be tempted to use the Russian-influenced Genitive Singular. The error is the *reasoning*, not always the form. A clearer error: `*три студентка*` instead of `**три студентки**`. |
| `Я чекав *двадцять хвилина*.` | `Я чекав **двадцять хвилин**.` | A common mistake is to use the singular form of the noun after a number greater than one, or to fail to produce the correct Genitive Plural form. The correct form is `хвилин` (Gen. Pl. of `хвилина`). |
| `Нам потрібно *троє дівчат*.` | `Нам потрібно **три дівчини**.` | Collective numerals (`двоє, троє, четверо...`) cannot be used with feminine nouns (Source 26). Learners must use the standard cardinal numeral (`три`) instead. |
| `Я знаю *два слова* українською.` | `Я знаю **два слова** українською.` | This is often correct by chance. The error is when the learner applies this same logic everywhere, failing to distinguish Nom. Pl. `слова` from the Gen. Pl. `слів` required after five: `❌ п'ять слова` -> `✅ п'ять слів`. |

## Деколонізаційні застереження (Decolonization Notes)

It is critical to teach Ukrainian grammar on its own terms, not as a variant of Russian. The grammar of numerals is a key area where this distinction matters.

1.  **The 2, 3, 4 Rule is a Ukrainian Standard, Not an Exception:** The primary rule in modern Ukrainian is that `два, три, чотири` govern the **Nominative Plural** (`два столи`, `три хлопці`). This contrasts with modern Russian, which uses the Genitive Singular (`два стола`, `три парня`). While both languages evolved from a common Old East Slavic root where numerals behaved differently (Source 8), their modern paths have diverged. Presenting the Ukrainian rule as "different from Russian" frames Russian as the default. Instead, present the Ukrainian Nominative Plural rule as the primary standard.

2.  **The `друг` Exception is Not "the Russian Rule":** The special case of `два друга` (Genitive Singular) in Ukrainian (Source 26) coincidentally matches the form in Russian. It should be taught as a specific, high-frequency exception within the Ukrainian system, not as an example of "following the Russian rule." It's a relic of an older grammatical system that has survived in this specific context.

3.  **Historical Roots Are Shared, Not Borrowed:** The historical reason that numerals from 5 onwards govern the Genitive Plural is that words like `пѧть` (five) and `десѧть` (ten) were grammatically **feminine nouns** in Old East Slavic (Source 8). A phrase like `пѧть братъ` was grammatically equivalent to "a quintet of brothers." This historical reality is common to East Slavic languages and explains the "why" behind the rule. It is a shared heritage, not a Russian import.

4.  **Avoid Using Russian as a Crutch:** Do not explain Ukrainian numeral agreement by saying "it's like in Russian, except...". Teach the Ukrainian system (`1`=adj; `2,3,4`=Nom.Pl; `5+`=Gen.Pl.) as a complete and independent set of rules.

## Природні приклади (Natural Examples)

These examples are sourced from Ukrainian textbooks and media, demonstrating natural usage.

**Rule: 1 (`один, одна, одне`)**
*   `За одну гривню можна було купити вола.` (Source 25) - For one hryvnia, you could buy an ox.
*   `...поїхати на один навчальний рік у Сполучені Штати.` (Source 1) - ...to go for one academic year to the United States.

**Rule: 2, 3, 4 + Nominative Plural**
*   `В Україні це переважно чотири роки навчання.` (Source 1) - In Ukraine, it's mostly four years of study.
*   `Під одним ковпаком сімсот козаків.` (Source 19) - This is a riddle, but `три` and `чотири` follow the same pattern: `Три козаки`, `Чотири козаки`.
*   `Мій університет... пропонує здобувати minor...` <!-- VERIFY --> This example doesn't fit. A better one: `У мого друга є три сини.` (My friend has three sons.)

**Rule: 5+ & `кілька`/`багато` + Genitive Plural**
*   `Треба приготувати 12 страв на святу вечерю.` (Source 4) - It is necessary to prepare 12 dishes for the Holy Supper.
*   `У попередньому епізоді я давала п'ять порад для покращення української мови.` (Source 3) - In the previous episode, I gave five tips for improving the Ukrainian language.
*   `Блокнот коштує сорок гривень.` (Source 24) - The notebook costs forty hryvnias.
*   `Скільки відсотків голосних в українських словах?` (Source 5) - What percentage of vowels are in Ukrainian words?
*   `...за лаштунками — мільйони непереможних.` (Source 10) - ...behind the scenes are millions of invincible people.

**Predicate Agreement**
*   `П’ятеро дітей нудьгували.` (Source 22) - Five children were bored. (Focus on the actors)
*   `Минуло десять літ.` (Source 22) - Ten years have passed. (Singular verb for a time period)
*   `Багато малечі поспішає на відкриття...` (based on Source 22) - Many little ones are hurrying to the opening... (Singular verb with `багато`)

## Рекомендації для вправ (Activity Concepts)

A phased approach works best for mastering numeral agreement.

*   **Phase 1: Controlled Recognition & Production**
    *   **Drill Type:** Simple Gap-Fill.
    *   **Format:** Provide the number and the noun in its base form. The student must supply the correct noun form.
    *   **Example:**
        *   `Я бачу (2, стіл) → __________.` (Answer: `два столи`)
        *   `Вона має (5, подруга) → __________.` (Answer: `п'ять подруг`)
        *   `Скільки (люди) → __________ тут?` (Answer: `людей`)

*   **Phase 2: Genitive Plural Formation**
    *   **Drill Type:** Transformation Table.
    *   **Format:** Focus exclusively on forming the Genitive Plural from the Nominative Singular. Group by declension/ending type.
    *   **Example:**
| Н. в. однини | Р. в. множини |
| :--- | :--- |
| `хвилина` | `хвилин` |
| `книжка` | `книжок` |
| `студент` | `студентів` |
| `море` | `морів` |
| `ніч` | `ночей` |

*   **Phase 3: Full Sentence Construction**
    *   **Drill Type:** Sentence Scramble or Full Translation.
    *   **Format:** Give prompts and have students construct full, grammatically correct sentences, including the correct verb agreement.
    *   **Example:**
        *   `(П'ять студентів / прийти / на лекцію).` → `П'ять студентів прийшло на лекцію.` OR `П'ять студентів прийшли на лекцію.`
        *   Translate: "I waited for three hours." → `Я чекав три години.`

## Зв'язки з іншими темами (Connections)

Understanding numeral agreement is a crucial hub connecting several grammatical areas.

*   **Prerequisites:**
    *   **Noun Declensions & Gender:** It's impossible to form the Genitive Plural without knowing the noun's declension and gender (Sources 21, 33, 41).
    *   **Cases (Відмінки):** The student must understand the concept of the Nominative and Genitive cases (Source 14, 40).
    *   **Nominative Plural:** To apply the "2, 3, 4" rule, the student must first know how to form the Nominative Plural.

*   **Enables:**
    *   **Telling Age:** `Мені двадцять п'ять **років**.`
    *   **Shopping:** `Дайте, будь ласка, два **кілограми** яблук і десять **яєць**.`
    *   **Telling Time:** `Зараз п'ять **хвилин** на третю.`
    *   **General Quantification:** Describing the world accurately (`У кімнаті було троє **людей**`, `У мене багато **питань**`).

## Пов'язані статті (Related Articles)
*   `grammar/a1/nominative-plural`
*   `grammar/a2/genitive-case`
*   `grammar/a1/noun-declensions`
*   `grammar/b1/collective-numerals`

---

### Вікі: grammar/a2/genitive-plural.md

# Граматика A2: Багато книг, мало студентів



## Як це пояснюють у школі (How Schools Teach This)

В українській шкільній програмі тема узгодження числівників з іменниками вводиться поступово. Базові концепції роду та числа закладаються в початкових класах (Source 27, 33, 37). У 3-4 класах учні вчаться змінювати іменники за числами та відмінками, а прикметники узгоджувати з ними (Source 6, 7, 36).

Ключове правило, що стосується родового відмінка множини, вивчається в 6 класі разом із відмінюванням кількісних числівників. У підручниках чітко розмежовується вживання іменників з числівниками `один`, `два, три, чотири` та `п'ять` і більше.

1.  **Числівник `один (одна, одне)`**: Узгоджується з іменником у роді, числі та відмінку, як прикметник. Наприклад, `один стіл`, `одна книга`, `одне вікно` (Source 16, 20).
2.  **Числівники `два (дві), три, чотири`**: Вимагають після себе іменника у формі **називного відмінка множини**: `два студенти`, `три кімнати`, `чотири яблука` (Source 16, 20).
3.  **Числівники від `п'яти` до `двадцяти`, а також `тридцять` тощо**: Вимагають після себе іменника у формі **родового відмінка множини**. Наприклад, `п'ять студентів`, `шість кімнат`, `десять яблук`. Це центральне правило для даної теми.
4.  **Складені числівники (21, 22, 105 тощо)**: Форма іменника залежить від **останнього** слова в числівнику. Наприклад:
    *   `двадцять **один** студент` (як з `один`)
    *   `тридцять **два** студенти` (як з `два`)
    *   `сто **п'ять** студентів` (як з `п'ять`)

Ця логіка є послідовною і подається як фундаментальне правило синтаксичної сполучуваності (Source 16). Крім числівників, родовий відмінок множини використовується зі словами, що позначають невизначену кількість: `багато`, `мало`, `кілька`, `декілька`, `багато`, а також у конструкціях із запереченням (`немає`).

## Повна парадигма (Full Paradigm)

Родовий відмінок множини (Genitive Plural) — один із найскладніших для іноземців через варіативність закінчень, що залежать від відміни, роду та кінцевого приголосного основи.

### І відміна (жін., чол., спільний рід на `-а, -я`)

| Група | Основа на... | Закінчення | Приклад (Н.в. одн.) | Родовий відмінок множини | Примітки |
| :---- | :--- | :--- | :--- | :--- | :--- |
| Тверда | Твердий приголосний | **Нульове** | `книга`, `сестра`, `фабрика` | `книг`, `сестер`, `фабрик` | Часто з'являється вставний голосний **-о-**, **-е-**: `сестра -> сестер`, `думка -> думок`. |
| М'яка | М'який приголосний | **-ь**, **-ей** | `земля`, `пісня`, `стаття`, `сім'я` | `земель`, `пісень`, `статей`, `сімей` | Вставний **-е-** у закритому складі: `вишня -> вишень`. Слова на `-я` після голосного мають **-й-**: `мрія -> мрій`. |
| Мішана | Шиплячий (`ж, ч, ш`) | **Нульове** | `вежа`, `круча`, `тиша` | `веж`, `круч`, `тиш` | Аналогічно до твердої групи. Може бути вставний голосний: `круча -> круч`. |
| **Винятки** | - | **-ей, -ів** | `миша`, `свиня`, `суддя`, `староста` | `мишей`, `свиней`, `суддів`, `старостів` | Деякі іменники чол. роду на `-а/-я` мають закінчення `-ів`: `суддя -> суддів`, `тесля -> теслів`. (Source 14) |

### ІІ відміна (чол. рід з нульовим закінченням або на `-о`; сер. рід на `-о, -е, -я`)

| Рід | Основа на... | Закінчення | Приклад (Н.в. одн.) | Родовий відмінок множини | Примітки |
| :---- | :--- | :--- | :--- | :--- | :--- |
| Чол. | Будь-який | **-ів (-їв)** | `стіл`, `завод`, `студент`, `герой`, `трамвай` | `столів`, `заводів`, `студентів`, `героїв`, `трамваїв` | Це найпродуктивніше закінчення для чоловічого роду. |
| Чол. | (винятки) | **-ей** | `гість`, `кінь` | `гостей`, `коней` | Невелика група слів. |
| Сер. | `-о` | **Нульове** | `місто`, `село`, `вікно` | `міст`, `сіл`, `вікон` | Вставний голосний **-о-** є типовим: `вікно -> вікон`. |
| Сер. | `-е` | **-ів (-їв)** | `море`, `поле` | `морів`, `полів` | |
| Сер. | `-я` | **-ь**, **-ів** | `життя`, `завдання`, `обличчя`, `почуття` | `життів`, `завдань`, `облич`, `почуттів` | Подвоєння приголосних зникає: `знання -> знань`. |
| **Винятки** | сер. рід | **-ей** | `око`, `плече` | `очей`, `плечей` | Ці слова мають особливі форми. (Source 39) |

### ІІІ та IV відміни

| Відміна | Рід | Закінчення | Приклад (Н.в. одн.) | Родовий відмінок множини | Примітки |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **III** | Жіночий (нульове) | **-ей** | `ніч`, `річ`, `тінь`, `любов`, `мати` | `ночей`, `речей`, `тіней`, `любовей` (арх.), `матерів` | Подовження основи на `-ер` у слова `мати` -> `матер-`. |
| **IV** | Середній (`-а/-я` + суфікси `-ат-/-ят-`) | **Нульове** | `теля`, `лоша`, `ім'я`, `плем'я` | `телят`, `лошат`, `імен`, `племен` | Суфікс `-ат-/-ят-` або `-ен-` зберігається. |

## Частотність і пріоритети

Для рівня А2-В1 пріоритетом є засвоєння правила сполучуваності з числівниками та словами кількості.

1.  **Найвищий пріоритет**: Правило **`5+ + Gen. Pl.`**. Це одна з найчастотніших конструкцій у мові. Сюди ж належать слова `багато`, `мало`, `кілька`, `декілька`, `скільки`.
    *   *Приклад: "На них приїхали понад **100 жінок**..."* (Source 4)
    *   *Приклад: "...не менше ніж **50% усіх** виданих упродовж року **книг**"* (Source 5)

2.  **Середній пріоритет**: Найпродуктивніші закінчення родового відмінка множини:
    *   **`-ів`** для чоловічого роду (`студентів`, `років`, `днів`).
    *   **Нульове закінчення** для жіночого роду І відміни (`книг`, `сестер`, `країн`) та середнього роду на `-о` (`міст`, `слів`).
    *   **`-ей`** для жіночого роду III відміни (`ночей`, `речей`).

3.  **Нижчий пріоритет**: Рідкісні винятки та паралельні форми (`чоловік/чоловіків`, `очей/віч`). Вони важливі для просунутих рівнів, але на А2-В1 можна зосередитись на базових моделях.

Конструкція заперечення `немає + Gen. Pl.` також є високочастотною і має вивчатися паралельно. Наприклад: `У мене немає братів`.

## Типові помилки L2 (Common L2 Errors)

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| *Я маю п'ять **книги**.* | Я маю п'ять **книг**. | Прямий переклад з англійської ("I have five books"), де іменник стоїть у множині. В українській мові числівники 5+ керують родовим відмінком множини. |
| *У класі десять **студентов**.* | У класі десять **студентів**. | Неправильний вибір закінчення. Для більшості іменників чоловічого роду в родовому відмінку множини характерне закінчення **-ів**. Закінчення *-ов* нетипове для української мови в цій функції. |
| *У моєї бабусі п'ять **дочок**.* | У моєї бабусі п'ять **дочок**. (або `п'ятеро дочок`). | Це складний випадок. Слово `дочка` має форму `дочок`, а не `дочок`. Але частіше вживається збірний числівник `п'ятеро` з назвами істот. З іншого боку, з'являється вставний голосний: `донька` -> `доньок`. Отже, `п'ять доньок` є правильною і поширеною формою. |
| *Тут багато **люди**.* | Тут багато **людей**. | Слова `люди`, `діти`, `гуси`, `кури` є формами множини, що відмінюються за особливим зразком. Їхня форма родового відмінка — `людей`, `дітей`, `гусей`, `курей`. |
| *Двісті **гривнів**.* | Двісті **гривень**. | Іменник `гривня` належить до м'якої групи І відміни. Правильна форма родового відмінка множини — `гривень` (з нульовим закінченням та вставним **-е-**), а не `-ів`. |
| *Двадцять два **років**.* | Двадцять два **роки**. | Форма іменника визначається останнім словом числівника. Тут це «два», що вимагає називного відмінка множини (`роки`), а не родового (`років`). |

## Деколонізаційні застереження

Українська граматика числівників має глибоке історичне коріння і не є "варіантом" російської. Важливо наголошувати на її самостійному розвитку.

1.  **Історичний контекст**: У давньоруській мові (спільному предку української та російської) числівники від 5 до 10 були **іменниками жіночого роду** (Source 1, 24). Вони відмінювалися як слово `ніч` і буквально означали "п'ятірка", "шістка". Саме тому вони вимагали після себе іменника в родовому відмінку множини, так само як сучасні слова `група студентів` або `десяток яєць`. Це пояснює, чому `п'ять` керує відмінком, на відміну від `два`, `три`, `чотири`, які історично були прикметниками і узгоджувалися з іменником (Source 24). Цей історичний факт пояснює логіку правила, а не зводить його до механічного запам'ятовування.

2.  **Форма `чотири`**: У давньоруській мові існувала форма чоловічого роду `четыре` (Source 24). Сучасна російська мова зберегла її (`четыре`), тоді як українська мова узагальнила форму жіночого/середнього роду `чотири` (Source 24). Представляти українську форму як відхилення від російської є некоректним; обидві мови розвинули різні риси спільного предка.

3.  **Закінчення `-ів` vs. `-ов`**: Продуктивне українське закінчення родового відмінка множини для чоловічого роду **`-ів`** (`столів`, `студентів`) є однією з яскравих відмінностей від російського **`-ов`** (`столов`, `студентов`). Помилкове вживання `-ов` в українському мовленні є ознакою русифікації.

4.  **Паралельні форми та варіативність**: В українській мові існують паралельні форми, як-от `полів` і `піль`, `голів` і `голов` (Source 14). Це свідчить про багатство та внутрішню динаміку мови. Не варто подавати одну з форм як "правильну", а іншу як "неправильну", якщо обидві є літературними.

5.  **Наголос**: Наголоси в числівниках та іменниках після них можуть відрізнятися. Наприклад, укр. `чотир**ьо**х` vs. рос. `четыр**ё**х`. Важливо звертати увагу на правильну українську вимову.

## Природні приклади

#### Кількість з конкретними числами (5+)
1.  "...в Україні готують **12 страв** на різдвяну вечерю." (Source 11)
2.  "...опублікували свої твори **17 авторок** з Галичини і наддніпрянської України." (Source 4)
3.  "У цьому законі чітко прописано ті сфери у яких саме українська мова має домінувати..." (Source 5) (Приклад без числівника, але ілюструє контекст)
4.  "...було опубліковано близько **50 мільйонів наукових статей**" (Source 25)

#### Невизначена кількість (`багато`, `кілька` тощо)
5.  "Крізь густу (…) ліщину синів Дніпро. **Довгим (…) поглядом** Софія охопила широку (…) річку, піщані (…) острови..." (Source 13)
6.  "на Закарпатті роблять **так багато вина**" (Source 8)
7.  "Отже абітурієнт - це людина яка хоче збирається вступати в університет це людина яка подає заявку на вступ вона називається абітурієнт А виш - це вища школа або вищий навчальний заклад ми говоримо виш ВНЗ або просто університет чи інститут Так от повернімось до теми тесту система ЗНО в Україні створена не дуже давно але вона чудово працює це тому Мабуть що так можна найкраще запобігти корупції вступ за результатами тестів максимально об'єктивний натомість у США наскільки мені відомо для вступу треба подавати цілий пакет документів не тільки тести а і есе рекомендації оцінки з школи Також в Америці дивляться на те наскільки активною була учениця чи учень в школі дивляться на спортивні досягнення якщо деться про університети для яких спорт це важливо в Україні ж основне фактично все залежить від балів ЗНО **балів те**" (Source 2)
8.  "Опублікували свої твори **17 авторок** з Галичини і наддніпрянської України" (Source 4)
9.  "...переважно це **Кілька десятків тисяч гривень** на рік." (Source 2)

#### Конструкції з `з`/`із` + Родовий відмінок
10. "узвар - це напій **із сухофруктів**." (Source 11)
11. "я саме повернувся **з Ужгорода**." (Source 8)

#### Історичні та розмовні приклади
12. "...суть ту **десяти людї**" (давньоруська, означає "близько десяти людей") (Source 1)
13. "І реча друго година сваримо, іноді сваримося та увекося ладімо, та завжди миримося." (Source 1)

## Рекомендації для вправ

-   **Phase 1 (Розпізнавання та вибір)**: Вправи на вибір правильної форми.
    *   *Формат*: `П'ять (студент / студенти / студентів)`.
    *   *Мета*: Засвоїти базове правило `5 + Gen. Pl.` vs. `2/3/4 + Nom. Pl.`.
    *   *Приклад*: `Три (гривня / гривні / гривень) лежать на столі.`

-   **Phase 2 (Трансформація)**: Вправи на утворення правильної форми з називного відмінка однини.
    *   *Формат*: `багато + (друг) -> багато друзів`.
    *   *Мета*: Практика утворення закінчень `-ів`, `-ей` та нульового закінчення, включно зі вставними голосними.
    *   *Приклад*: `десять + (сестра) -> ...`; `сім + (день) -> ...`; `багато + (місто) -> ...`.

-   **Phase 3 (Контрольована продукція)**: Вправи на заповнення пропусків у реченнях.
    *   *Формат*: `У моєму місті є __________ (7, театр).` -> `У моєму місті є сім театрів.`
    *   *Мета*: Інтеграція правила в синтаксичний контекст.

-   **Phase 4 (Вільна продукція)**: Відповіді на запитання, що вимагають використання числівників.
    *   *Формат*: `Скільки днів у тижні?`, `Скільки у вас братів і сестер?`, `Скільки років вашому місту?`
    *   *Мета*: Автоматизація навички в спонтанному мовленні.

## Зв'язки з іншими темами

-   **Попередні теми (Prerequisites)**:
    *   **Відміни іменників (`noun-declensions`)**: Розуміння відміни та групи іменника є необхідним для правильного утворення форми родового відмінка множини.
    *   **Називний відмінок множини (`nominative-plural`)**: Необхідний для правильного вживання з числівниками 2, 3, 4.
    *   **Роди іменників (`noun-genders`)**: Важливий для узгодження з числівником `один/одна/одне` та `два/дві`.

-   **Наступні теми (Enables)**:
    *   **Дати та час (`dates-and-time`)**: Конструкції на кшталт `п'ять хвилин`, `десять років`.
    *   **Розповіді про статистику та кількість (`talking-about-quantity`)**: Використання слів `відсоток`, `більшість`, `частина` з родовим відмінком множини (`80 відсотків людей`).
    *   **Покупки та ціни (`shopping-and-prices`)**: `Це коштує сто гривень`.

## Пов'язані статті

-   [[grammar/a1/nominative-plural|Називний відмінок множини]]
-   [[grammar/a2/noun-declensions|Відміни іменників]]
-   [[grammar/a2/numerals-1-100|Числівники: основи]]
-   [[grammar/b1/cases-overview|Огляд відмінків]]
</wiki_context>

## Plan References

- 
- 
- 

</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Чому родовий множини такий складний? (Why Is the Genitive Plural So Hard?)` (~400 words)
- `## I відміна: нульове закінчення (First Declension: Zero Ending)` (~500 words)
- `## II відміна: -ів, нульове, -ей (Second Declension: Three Patterns)` (~600 words)
- `## Скільки чого? Кількість у житті (How Much of What? Quantity in Daily Life)` (~500 words)
- `## Підсумок` (~150 words)

Each section should follow the word budget specified. The total must reach 2000 words minimum.

---

## Content Rules

TARGET: 55-75% Ukrainian.
LANGUAGE ROLES:
- PRIMARY: Ukrainian for all content — dialogues, examples, section intros, cultural context.
- ENGLISH: Only for abstract grammar concepts that need explicit explanation.
- STRUCTURAL RULE: Each sentence is 100% Ukrainian OR 100% English. Dialogues, examples, section intros all stay Ukrainian-only.
A2 register. Concrete everyday vocabulary. No literary language, no metaphors. Ukrainian sentences max 15 words. Max 2 clauses. All cases allowed. Simple subordinate clauses only. Aspect pairs introduced. No participles.

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
  1. **School cafeteria inventory — counting remaining items: Скільки тарілок (f, plates)? Двадцять. Виделок (f, forks)? П'ятнадцять. Ложок (f, spoons)? Десять. Склянок (f, glasses)? Немає склянок!**
     Speakers: Завідувач їдальні (cafeteria manager), Помічник
     Why: Genitive plural: тарілка→тарілок, виделка→виделок, склянка→склянок

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

**Required:** родовий відмінок (genitive case), нульове закінчення (zero ending), кількість (quantity, amount), багато (a lot, many), мало (few, little), кілька (a few, several), декілька (a few, several), скільки (how many, how much), гроші (money), гривня (hryvnia)
**Recommended:** вставний голосний (fleeting vowel), виняток (exception), десяток (a dozen, ten-unit)

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
## Чому родовий множини такий складний? (~420 words total)
- P1 (~120 words): [Introduction to the Genitive Plural as the "heavyweight" of Ukrainian cases. Explain that while other cases have relatively predictable endings, Genitive Plural involves a choice between three major patterns (zero, -ів/-їв, -ей) and internal sound changes (o→i, e→i, and fleeting vowels). Use the core question "Скільки?" (How many?) to illustrate why this case is ubiquitous in daily life.]
- P2 (~100 words): [Detailing the functional importance of this case. Explain that it is required after numerals 5-20, all round numbers (30, 40, 50...), and indefinite quantity words like багато (many), мало (few), кілька (several). Contrast the simplicity of the English "five books" with the Ukrainian "п'ять книг," highlighting the noun's morphological shift.]
- P3 (~100 words): [Discussing the "Consonant Cluster" problem. Explain that because many feminine and neuter nouns take a zero ending, they often end in a cluster of consonants (e.g., сестра → сестр*). Introduce the concept of "вставні голосні" (inserted vowels -o- and -e-) as the language's way of making these words easier to pronounce (сестер, книжок).]
- P4 (~100 words): [Strategy for mastery: Explain that the module will break the case down by declension (відміна) rather than trying to memorize a single rule. Emphasize that most masculine nouns follow one path, while most feminine/neuter nouns follow another, allowing the learner to categorize new vocabulary quickly.]

## I відміна: нульове закінчення (~550 words total)
- P1 (~140 words): [Explain the "Zero Ending" (нульове закінчення) for feminine nouns ending in -а/-я. Demonstrate the "dropping" of the vowel with hard-stem examples: книга → книг, машина → машин, газета → газет. Introduce the o→i alternation in closed syllables: дорога → доріг, корова → корів.]
- P2 (~160 words): [In-depth focus on fleeting vowels (-o-, -e-). Explain the rule: if dropping the ending results in two consonants, we insert -о- (usually after hard consonants or before -к) or -е- (after soft consonants or shibilants). Provide clear pairs: книжка → книжок, картка → карток, казка → казок vs. земля → земель, вишня → вишень, пісня → пісень.]
- P3 (~120 words): [Soft stem nouns and nouns ending in -я after a vowel. Explain the -й ending for words like мрія → мрій, надія → надій. Mention the soft sign for stems ending in a soft consonant like кухоль → кухлів (wait, I відміна focus) ... like їдальня → їдалень, спальня → спалень.]
- P4 (~130 words): [Exceptions and special patterns. Explain that some feminine nouns take -ей (стаття → статей, сім'я → сімей, миша → мишей) and masculine nouns of the I declension take -ів (суддя → суддів, тесля → теслів). Emphasize that these are "high-frequency survivors" of older patterns.]
- <!-- INJECT_ACTIVITY: fill-in-genitive-i --> [Fill-in-the-blank, forming Genitive Plural for mixed I declension nouns including fleeting vowel cases (сестра, книжка, вишня, машина, стаття), 8 items]

## II відміна: -ів, нульове, -ей (~680 words total)
- P1 (~150 words): [Masculine Hard Stems: The dominant -ів ending. Explain that the vast majority of masculine nouns (II declension, zero ending in singular) take -ів. Provide frequency-rich examples: студентів, доларів, метрів, днів, комп'ютерів, столів. Note that this is the "safest bet" for a learner guessing a masculine plural.]
- P2 (~130 words): [Soft and Mixed Stems: Explain the -ів/-їв ending for soft stems (музеїв, героїв, учнів). Contrast this with the -ей ending for a specific group of soft-stem nouns: гостей, коней, грошей (pluralia tantum but follows this logic), солов'їв.]
- P3 (~150 words): [Neuter nouns in -o: The return of the Zero Ending. Explain that neuter nouns ending in -o behave like feminine nouns, dropping the -o and often gaining a fleeting vowel. Examples: місто → міст, слово → слів (o→i), вікно → вікон, яблуко → яблук (no fleeting vowel needed here), село → сіл.]
- P4 (~150 words): [Neuter nouns in -е and -я (soft/mixed stems). Explain that nouns in -е often take -ів (морів, полів - or the rare "піль"). For nouns in -я (task/assignment group), explain the zero ending with the loss of consonant doubling: завдання → завдань, знання → знань, обличчя → облич.]
- P5 (~100 words): [The -ин suffix loss. Explain the specific group of nouns denoting nationality or status: киянин → киян, громадянин → громадян, селянин → селян. This is a common point of confusion for learners who expect "киянинів."]
- <!-- INJECT_ACTIVITY: match-up-singular-plural --> [Match-up, connect singular Nominative nouns to their correct Genitive Plural form (брат, вікно, стаття, гість, знання), 8 items]

## Скільки чого? Кількість у житті (~550 words total)
- P1 (~120 words): [The "5+ Rule" and Indefinite Numerals. Synthesize the grammar by explaining the governing role of numbers. List quantity words: багато, мало, кілька, декілька, скільки. Provide examples: багато друзів, мало часу (singular), кілька хвилин, скільки гривень?]
- P2 (~100 words): [The Decolonization Contrast: 2, 3, 4 vs. 5+. Explicitly contrast the Ukrainian Nominative Plural for 2-4 (три студенти, чотири книги) with the Genitive Plural for 5+ (п'ять студентів, шість книг). Note that this is a major distinction from Russian grammar and a key marker of natural Ukrainian speech.]
- P3 (~110 words): [Dialogue: School Cafeteria Inventory. Two speakers counting supplies. Focus on feminine nouns with fleeting vowels and masculine nouns with -ів. "Скільки у нас тарілок? Двадцять тарілок. А виделок? Тільки десять виделок. Нам треба більше склянок!"]
- P4 (~110 words): [Dialogue: Shopping for a party. Focus on currency (гривень) and weights (кілограмів). "Дайте мені п'ять кілограмів яблук. Це коштує двісті гривень. У мене є тільки кілька сотень."]
- P5 (~110 words): [Dialogue: Describing a city tour. Focus on neuter nouns and pluralia tantum. "У цьому місті багато вікон, але мало дверей відкриті. Скільки тут людей? Кілька тисяч."]
- <!-- INJECT_ACTIVITY: quiz-quantity-agreement --> [Quiz, choose the correct noun form after specific numbers and quantity words (2, 5, багато, скільки), 8 items]
- <!-- INJECT_ACTIVITY: true-false-genitive-errors --> [True-False, identify if the provided Genitive Plural form is correct (e.g., *студентов is false, *книгів is false), 8 items]

## Підсумок (~150 words)
- P1 (~150 words): [Recap the three pillars of Genitive Plural:
    - **-ів/-їв**: Most masculine (студентів) and some neuter (морів).
    - **Zero ending (ø)**: Most feminine (книг) and neuter in -о (вікон). Remember the fleeting -о-/-е-!
    - **-ей**: Feminine III declension (ночей), some soft masculine (гостей), and specific exceptions (статей).
    
    Self-check:
    - What ending do neuter nouns in -о usually take? (Zero ending)
    - What happens to the word 'сестра' in Genitive Plural? (It becomes 'сестер' due to a fleeting vowel)
    - Which case do we use after 'багато'? (Genitive Plural)]

Grand total: ~2350 words
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
