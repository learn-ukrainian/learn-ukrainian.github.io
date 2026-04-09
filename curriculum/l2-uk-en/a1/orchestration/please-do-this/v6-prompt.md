

---

## Your Writing Identity

**You are: Lead Ukrainian Instructor.** Your persona is *The Patient Guide*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **43: Please Do This** (A1, A1.7 [Communication]).

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
module: a1-043
level: A1
sequence: 43
slug: please-do-this
version: '1.1'
title: Please Do This
subtitle: Читай! Скажіть! Дайте! — asking people to do things
focus: grammar
pedagogy: PPP
phase: A1.7 [Communication]
word_target: 1200
objectives:
- Form imperative mood for 2nd person singular (ти) and plural/formal (ви)
- Give instructions and make requests using будь ласка
- Recognize common classroom and daily-life imperatives
- Distinguish ти-imperatives from ви-imperatives
dialogue_situations:
- setting: 'Volleyball practice — coach gives warm-up instructions: Принеси м''яч (m,
    ball)! Розстав конуси (pl, cones)! Натягни сітку (f, net)! Поклади рушники (pl,
    towels) на лавку (f, bench)! Відкрий двері (pl)!'
  speakers:
  - Тренер (coach)
  - Гравці (players)
  motivation: Imperative with м'яч(m), конуси(pl), сітка(f), рушники(pl), лавка(f)
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — In the classroom: — Відкрийте підручники, будь ласка. Читайте текст.
    — Вибачте, яку сторінку? — Сторінку двадцять три. — Тепер пишіть. Напишіть три
    речення. — Можна запитати? — Так, запитуйте! Classroom imperatives: відкрийте,
    читайте, пишіть, напишіть.'
  - 'Dialogue 2 — Between friends: — Слухай, ходімо в кафе! — Добре, йди, я зараз.
    — Подивись, яка гарна погода! — Так! Сідай тут. — Дай мені меню, будь ласка. —
    Ось, дивись. — Скажи, що ти хочеш? — Я хочу каву. Informal imperatives: слухай,
    подивись, сідай, дай, скажи.'
- section: Наказовий спосіб (The Imperative Mood)
  words: 300
  points:
  - 'Ukrainian Grade 5 term: наказовий спосіб (imperative mood). Used for commands,
    requests, instructions, invitations. Two forms at A1: ти (informal, one person)
    and ви (formal or plural). Будь ласка makes any command polite: Дай! (Give!) →
    Дай, будь ласка. (Please give.) Дайте! (Give! — formal) → Дайте, будь ласка.'
  - 'Not rude — just direct: Ukrainian imperatives are normal in daily speech. Читай!
    is not rude — it''s how teachers, parents, friends talk. Adding будь ласка = polite.
    Adding tone + name = friendly: Олено, прочитай, будь ласка. (Olena, please read.)'
- section: Як утворити? (How to Form It)
  words: 300
  points:
  - 'Ти-form (informal, singular): Group I (-ати): читати → читай, слухати → слухай,
    писати → пиши. Group II (-ити): говорити → говори, дивитися → дивись, ходити →
    ходи. Irregular (common): дати → дай, сказати → скажи, їсти → їж, іти → іди. Pattern:
    stem + ending. Most are short — one or two syllables.'
  - 'Ви-form (formal or plural): Add -те to the ти-form: читай → читайте, слухай →
    слухайте, пиши → пишіть, говори → говоріть, дивись → дивіться, ходи → ходіть,
    дай → дайте, скажи → скажіть, іди → ідіть. Note: some get -іть (not -ить) — stress
    shifts: пиши → пишіть, сиди → сидіть, дивись → дивіться.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Essential imperatives for daily life: | Infinitive | Ти | Ви | Meaning | | читати
    | читай | читайте | read | | писати | пиши | пишіть | write | | слухати | слухай
    | слухайте | listen | | дивитися | дивись | дивіться | look | | говорити | говори
    | говоріть | speak | | іти | іди | ідіть | go | | дати | дай | дайте | give |
    | сказати | скажи | скажіть | say/tell | | сісти | сядь | сядьте | sit down |
    | відкрити | відкрий | відкрийте | open | Self-check: How do you say ''Please
    read'' to your teacher? To your friend?'
vocabulary_hints:
  required:
  - читати (to read)
  - писати (to write)
  - слухати (to listen)
  - дивитися (to look/watch)
  - говорити (to speak)
  - дати (to give)
  - сказати (to say/tell)
  - іти (to go)
  recommended:
  - відкрити (to open)
  - сісти (to sit down)
  - показати (to show)
  - запитати (to ask)
  - підручник (textbook, m)
  - сторінка (page, f)
  - речення (sentence, n)
activity_hints:
- type: fill-in
  focus: 'Form imperative: читати → читай / читайте, писати → пиши / пишіть'
  items: 10
- type: quiz
  focus: 'Choose correct: ___, будь ласка! (дай / даєш / дати)'
  items: 8
- type: group-sort
  focus: 'Sort: ти-forms vs ви-forms (читай vs читайте, дай vs дайте)'
  items: 10
- type: fill-in
  focus: 'Complete: Олено, ___ книжку! Пане Іване, ___ книжку! (дай/дайте)'
  items: 6
connects_to:
- a1-044 (Linking Ideas)
prerequisites:
- a1-042 (Hey, Friend!)
grammar:
- 'Imperative mood (наказовий спосіб): 2nd person ти and ви forms only'
- 'Ти-form: читай, пиши, дай, скажи, іди'
- 'Ви-form: add -те (читайте) or -іть (пишіть, скажіть)'
- Будь ласка for politeness
register: розмовний
references:
- title: State Standard 2024, §4.2.4.2
  notes: Imperative mood — 2nd person only at A1.
- title: 'Grade 5 textbook: Наказовий спосіб (Заболотний)'
  notes: Formation of imperative from verb stem. Ти and ви forms.

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
- Confirmed: читати, писати, слухати, дивитися, говорити, дати, сказати, іти, відкрити, сісти, показати, запитати, підручник, сторінка, речення.
- Not found: None. All planned words exist and are grammatically sound for A1.

## Grammar Rules
- The Imperative Mood (Наказовий спосіб): Правопис § 116 — Provides rules for forming imperatives with endings -и, -∅ (2nd sing); -імо, -ім, -мо (1st plur); -іть, -те (2nd plur).
- Stem-based formation: Group I (-ати) mostly uses -й/-йте (читай, слухай, відкривай); Group II and consonant stems use -и/-іть (пиши, пишіть, кажи, скажіть).

## Calque Warnings
- "Давай" + infinitive: Potential calque from Russian — "давай читати" is incorrect. Correct Ukrainian uses the synthetic imperative: "читаймо" or "давай" + perfective future (but better avoid at A1). Use synthetic forms like "ходімо" (let's go) or "пишімо".
- "Відкрийте підручники": OK — although "розгорніть" is more specific for books, "відкрийте" is standard and more accessible for A1 learners.

## CEFR Check
- читати: A1 — OK
- писати: A1 — OK
- слухати: A1 — OK
- дивитися: A1 — OK
- говорити: A1 — OK
- іти: A1 — OK
- підручник: A1 — OK
- сторінка: A1 — OK
- речення: A1 — OK
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
# Knowledge Packet: Please Do This
**Module:** please-do-this | **Track:** A1

<wiki_context>
## Compiled Wiki Knowledge

The following articles from the project wiki provide compiled knowledge relevant to this module. Use them as authoritative context — they were compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).

### Вікі: pedagogy/a1/please-do-this.md

# Педагогіка A1: Please Do This



## Методичний підхід (Methodological Approach)

This guide outlines the core pedagogical principles for creating A1 level content. The primary goal is not just to teach rules, but to foster a positive, effective, and decolonized learning experience from the very first lesson.

1.  **Emotion-Driven Learning (Емоційне навчання):** We remember things that evoke strong emotions (Source: `ext-ulp_youtube-90`). A1 content should not be a dry list of vocabulary. It must be embedded in relatable, personal stories. For example, instead of just a list of foods, present them in a story about a family dinner, connecting a word like «смачно» to the warmth of family, just as a diaspora learner might remember a word from their grandfather (Source: `ext-ulp_youtube-90`).

2.  **Active Retrieval Practice (Практика відтворення):** Passive re-reading is inefficient. The most effective learning happens when the brain struggles to recall information (`відтворення`). This is when the "muscles" of memory are built (Source: `ext-ulp_youtube-90`). A1 modules MUST be built around frequent, low-stakes retrieval exercises. This means less passive reading and more "test-like" activities that force the learner to produce language.

3.  **Testing as a Learning Tool (Тест як метод навчання):** For A1, "tests" are not for grades; they are the primary method of learning. Instead of teaching a concept and then testing it, we should often test *before* teaching. For instance, before a lesson on verb forms, give the learner a sentence with a blank and ask them to guess the verb. This creates a "need to know," making the subsequent explanation more effective (Source: `ext-ulp_youtube-90`). This "test-first" approach helps learners immediately see what they need to focus on.

4.  **Goal-Oriented Content (Цілеспрямований контент):** Every A1 learner has a goal, whether it's understanding relatives, reading the news, or traveling (Source: `ext-ulp_youtube-166`). The content must serve these goals. For A1, this means focusing on practical, high-frequency situations: introductions, ordering food, asking for directions, talking about family and hobbies. The curriculum must deliver immediate, real-world communicative competence.

5.  **Structured Comfort Zone Expansion (Вихід із зони комфорту):** While A1 is about building foundations, learners must be gently pushed to interact with simple, authentic materials. This could be a short children's poem (Source: `ext-ulp_youtube-164`), a simple dialogue from a podcast, or a single page from a graded reader (Source: `ext-ulp_youtube-69`). The key is to make this process structured and supported, for example, by providing a transcript and vocabulary for a one-minute authentic audio clip (Source: `ext-ulp_youtube-166`).

## Послідовність введення (Introduction Sequence)

The order of introduction is critical for building a solid foundation.

1.  **Step 1: Foundational Concepts & Core Vocabulary.** Begin with the absolute basics. Introduce the concept that a text is a series of sentences linked by meaning (Source: `3-klas-ukrainska-mova-vashulenko-2020-1_s0002`). Teach high-frequency social formulas ("Привіт," "Дякую," "Будь ласка") and the most common nouns and verbs related to personal identity (`я`, `ти`, `студент`, `читати`).

2.  **Step 2: Basic Sentence Structure & Present Tense.** Introduce the simple sentence structure (Subject-Verb-Object). Teach the present tense of high-frequency verbs from the 1st and 2nd conjugations. Crucially, teach the omission of "to be" in the present tense ("Я студент," not "Я є студент"). Model this with sentence-building exercises (Source: `6-klas-ukrmova-betsa-2023_s0020`).

3.  **Step 3: Introduction to Cases (Nominative & Accusative).** Do not overwhelm with all seven cases. Start with the Nominative (subject) and Accusative (direct object). This unlocks the ability to form basic transitive sentences ("Я читаю книжку").

4.  **Step 4: The Imperative Mood for Polite Requests.** Introduce the imperative mood not as a command, but as the primary way to make polite requests when combined with "будь ласка." This is a fundamental communicative function (Source: `7-klas-ukrmova-litvinova-2024_s0066`, `5-klas-ukrmova-uhor-2022-1_s0187`).

5.  **Step 5: Past Tense & Basic Prepositional Phrases.** Introduce the past tense, which is relatively simple in Ukrainian (forms based on gender and number). Simultaneously, teach basic prepositional phrases to talk about location (`в/у`, `на`). This allows for simple storytelling ("Я був у Києві").

The general sequence of grammatical topics should follow the logic seen in native textbooks: Verb Forms (Infinitive, Person) → Tense/Mood → Cases (Source: `7-klas-ukrmova-litvinova-2024_s0008`).

## Типові помилки L2 (Common L2 Errors)

This section guides the writer on what to anticipate and proactively address.

| ❌ Помилково (Incorrect) | ✅ Правильно (Correct) | Чому (Why) |
| :--- | :--- | :--- |
| *Я є студент. | Я студент. | The verb `бути` (to be) is omitted in the present tense in standard Ukrainian. This is a direct structural transfer from English and must be explicitly corrected from Day 1. |
| *Дайте мені каву. (Abrupt) | Дайте, будь ласка, каву. | English speakers often look for modal verbs ("Could I have...") for politeness. In Ukrainian, the imperative form + `будь ласка` is the standard, natural way to make a polite request. The bare imperative can sound like a rude command (Sources: `7-klas-ukrmova-litvinova-2024_s0066`, `5-klas-ukrmova-uhor-2022-1_s0187`). |
| Прівєт! Как діла? | Привіт! Як справи? | This is Surzhyk, a mix of Ukrainian and Russian. It is not "slang" or a "dialect"; it is a remnant of linguistic Russification. The curriculum must teach pure, standard Ukrainian from the start (Source: `ext-ulp_youtube-168`). |
| Я маю книжку. | У мене є книжка. | While `мати` can mean "to have," the `У + [genitive] + є` construction is far more common and natural for expressing possession of objects in everyday speech. Teaching this structure first prevents an unnatural, English-like sentence pattern. |
| *Він хоче іти в **парікмахерську**. | Він хоче йти в **перукарню**. | This is a lexical error, borrowing a common Russian word instead of using the correct Ukrainian equivalent. A1 vocabulary must be carefully vetted to exclude such Russianisms (Source: `ext-ulp_youtube-168`). |
| Я читаю книжку **зараз**. | Я читаю книжку. | English speakers overuse "now" to specify the present continuous. In Ukrainian, the imperfective verb `читаю` already implies an ongoing action in the present. Adding `зараз` is often redundant and unnatural unless for specific emphasis. |

## Деколонізаційні застереження (Decolonization Notes)

**This is a non-negotiable component of the curriculum.** The teaching of Ukrainian must be free from the influence of Russian linguistic colonialism. Russia actively uses its language and its version of "history" as a weapon to erase Ukrainian identity (Source: `ext-realna_istoria-101`).

1.  **No Russian Comparisons:** Never teach Ukrainian letters, sounds, or grammar by comparing them to Russian (e.g., "Ukrainian 'и' is like Russian 'ы'"). This centers Russian as the default and frames Ukrainian as a deviation. Ukrainian phonetics and grammar must be taught on their own terms.

2.  **Zero Tolerance for Surzhyk:** Surzhyk is not a "quirky dialect." It is a direct result of centuries of forced Russification and the suppression of the Ukrainian language (Source: `ext-ulp_youtube-168`). Its use in educational materials, even as an example of "what not to do," can normalize it. The curriculum must present only standard, clean Ukrainian. Examples like `Привет` or `садік` must be identified as foreignisms to be avoided.

3.  **Correctly Frame Shared Vocabulary:** Ukrainian and Russian share some vocabulary due to a common Slavic root. It is critical to frame this correctly. These are not "Russian words in Ukrainian." They are cognates from a common ancestor. When a word exists in both languages, the Ukrainian form is presented as native, not as a borrowing (Source: `ext-ulp_youtube-139`).

4.  **Ukrainian is the Only Medium of Instruction (for the language itself):** While explanations can be in English, all target language examples, dialogues, and texts must be 100% Ukrainian. The goal is to build a "Ukrainian brain" from scratch, not to map Ukrainian onto an English or Russian framework.

## Словниковий мінімум (Vocabulary Boundaries)

This vocabulary is suitable for A1 learners (teens and adults). It is simple but not childish.

**Іменники (Nouns):**
*   ★★★: `книжка`, `школа`, `студент`, `вчитель`, `мова`, `Україна`, `Київ`, `день`, `друг`, `сім'я`, `мама`, `тато`, `час`, `робота`, `вода`, `кава`
*   ★★: `музей`, `вулиця`, `місто`, `село`, `сніданок`, `обід`, `вечеря`, `питання`, `слово`
*   ★: `подорож`, `хобі`, `канікули` (Source: `6-klas-ukrmova-betsa-2023_s0083`)

**Дієслова (Verbs):**
*   ★★★: `бути`, `мати`, `хотіти`, `могти`, `знати`, `розуміти`, `говорити`, `читати`, `писати`, `жити`, `працювати`, `йти`, `їхати`
*   ★★: `любити`, `дивитися`, `слухати`, `робити`, `давати`, `питати`, `їсти`, `пити`
*   ★: `грати (в/на)` (Source: `6-klas-ukrmova-betsa-2023_s0020`), `починати`, `допомагати`

**Прикметники / Прислівники (Adjectives / Adverbs):**
*   ★★★: `добрий`, `новий`, `старий`, `великий`, `малий`, `український`, `тут`, `там`, `добре`, `погано`
*   ★★: `цікавий`, `гарний`, `смачний`, `сьогодні`, `завтра`, `вчора`, `швидко`, `повільно`
*   ★: `важливий`, `легкий`, `важкий`

## Приклади з підручників (Textbook Examples)

The writer should model activities on these proven formats from Ukrainian schoolbooks.

1.  **Structured Sentence Building (Побудова речень):**
    *   **Task:** Create full sentences from prompts. This drills vocabulary and basic grammar in a controlled way.
    *   **Example:** (From `6-klas-ukrmova-betsa-2023_s0020`)
        > Складіть речення за зразком.
        > **Зразок:** Томаш — кататися на ковзанах — льодовий майданчик. -> *Томаш катається на ковзанах на льодовому майданчику.*
        > 1. Андрій — кататися на скейтборді — парк
        > 2. Марті — подобатися — народні танці
        > 3. Батьки — ходити в похід — гори

2.  **Polite Request Dialogues (Діалоги з проханням):**
    *   **Task:** Create and role-play short dialogues for common situations, focusing on polite forms.
    *   **Example:** (Adapted from `5-klas-ukrmova-uhor-2022-1_s0187`)
        > Складіть діалог, уявіть ситуацію: ви прийшли у магазин. Вам потрібно купити ручку і зошит. Використайте в ньому слова «Спасибі!» і «Будь ласка».

3.  **Imperative Verb Formation (Утворення наказового способу):**
    *   **Task:** Fill in the blanks by correctly forming the imperative mood of the verb.
    *   **Example:** (From `7-klas-ukrmova-litvinova-2024_s0066`)
        > Утворіть від дієслів у дужках форми наказового способу.
        > 1. Так (сказати), ви хочете стати справжніми богатирями?
        > 2. (Слухати), добрий чоловіче, коли вже довелося нам іти разом, (зробити) так.
        > 3. Тепер (іти) додому, бо пізно.

4.  **Intensive Listening & Repetition (Інтенсивне слухання і повторення):**
    *   **Task:** A powerful exercise to train listening comprehension and pronunciation simultaneously.
    *   **Example:** (Based on the method described in `ext-ulp_youtube-166`)
        > 1. Знайдіть українське відео з субтитрами.
        > 2. Прослухайте одне речення без субтитрів. Зупиніть відео.
        > 3. Спробуйте самі сказати вголос, що ви почули. Повторіть кілька разів.
        > 4. Включіть субтитри і перевірте, чи правильно ви почули і сказали. Запишіть нові слова.

## Пов'язані статті (Related Articles)
- `pedagogy/a1/introduction-to-cases`
- `pedagogy/a1/present-tense-conjugation`
- `pedagogy/a1/imperative-mood-politeness`
- `pedagogy/decolonization/surzhyk-and-russianisms`
- `curriculum/a1/vocabulary-by-theme`

---

### Вікі: pedagogy/a1/this-and-that.md

# Педагогіка A1: This And That



## Методичний підхід (Methodological Approach)

The core pedagogical principle for teaching demonstratives (`цей`, `той`) in Ukrainian is to tightly integrate them with the concept of noun gender. Ukrainian elementary school textbooks do not teach these words in isolation; they are presented as a fundamental tool for identifying and reinforcing a noun's gender from the very beginning (Джерело: `3-klas-ukrainska-mova-kravtsova-2020-1_s0062`).

The primary method is **substitution and association**. Learners are taught to associate a noun with a chain of gender-agreeing words. For a masculine noun like `стіл` (table), the chain is `стіл` → `він` (he) → `мій` (my) → `цей` (this) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0030`, `3-klas-ukrainska-mova-ponomarova-2020-1_s0085`). This creates a powerful mental link between the noun and its grammatical gender, making adjective agreement (e.g., `цей червоний стіл`) intuitive later on.

The unchangeable pronoun `це` ("this/that is") is introduced first as a simple identifier. It is the most frequent and simplest form, used in basic sentence patterns like "**Це** + [іменник]" (e.g., "**Це** стіл," "**Це** книга."). This allows learners to start building sentences before tackling gender agreement (Джерело: `ext-video-4`, `5-klas-ukrmova-uhor-2022-1_s0081`).

Only after `цей/ця/це` are mastered as pointers for "close" objects is the "far" equivalent `той/та/те` introduced, often through direct contrastive exercises (`цю книгу чи ту книгу?` — "this book or that book?") (Джерело: `6-klas-ukrmova-litvinova-2023_s0280`).

Finally, demonstratives are presented as a key tool for creating cohesive text by avoiding noun repetition. Textbooks show how words like `цей`, `ця`, `він`, `вона` connect sentences and make writing flow more naturally (Джерело: `4-klas-ukrmova-zaharijchuk_s0014`, `4-klas-ukrayinska-mova-zaharijchuk-2021-1_s0148`). At the A1 level, the focus is purely on the nominative (subject) case. Full declension is a B1 topic (<!-- VERIFY -->).

## Послідовність введення (Introduction Sequence)

The introduction must be methodical and layered, building from the simplest concept to the more complex.

- **Step 1: The Universal Identifier `Це`**
  - **What:** Introduce the word `це` as the universal, gender-neutral way to say "This is..." or "That is...". It answers the question `Що це?` (What is this?).
  - **Why:** This is the highest frequency demonstrative and requires zero knowledge of gender. It allows learners to immediately start identifying objects. For example: `Що це? - Це стіл.` `Що це? - Це книга.` (Джерело: `ext-video-4`). It functions like "It is" in English.

- **Step 2: The Gender Pointers `Цей`, `Ця`, `Це`**
  - **What:** Introduce the three gendered forms of "this": `цей` (masculine), `ця` (feminine), and `це` (neuter). Explicitly link them to the gender pronouns `він`, `вона`, `воно` and possessives `мій`, `моя`, `моє`.
  - **Why:** This directly reinforces noun gender. The teaching pattern is: see a noun (`стіл`), recall its gender pronoun (`він`), and then select the corresponding demonstrative (`цей стіл`) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0030`, `3-klas-ukrainska-mova-vashulenko-2020-1_s0128`). This builds the grammatical reflex for agreement.

- **Step 3: The Plural Pointer `Ці`**
  - **What:** Introduce the plural form `ці` ("these") for all genders.
  - **Why:** After mastering the three singular forms, the single plural form is a simple next step. It shows how gender distinctions disappear in the plural for demonstratives. Example: `ці столи`, `ці книги`, `ці вікна`. (Джерело: `4-klas-ukrmova-zaharijchuk_s0014`).

- **Step 4: Distinguishing "This" vs. "That" (`Той`, `Та`, `Те`, `Ті`)**
  - **What:** Introduce the "far" pointers `той` (m), `та` (f), `те` (n), and `ті` (pl) to contrast with the "near" pointers (`цей`, `ця`, `це`, `ці`).
  - **Why:** This concept of proximity is familiar to English speakers ("this/that"). It should be taught with contrastive examples, physically pointing to near and far objects. For example: `Цей стілець тут, а той стілець там.` (This chair is here, and that chair is there). `Мені, будь ласка, це/те тістечко` (Source 3) is a perfect textbook example of this choice.

- **Step 5: Demonstratives for Text Cohesion**
  - **What:** Show how `цей`, `він`, `вона` etc., are used to refer back to a previously mentioned noun to avoid clumsy repetition.
  - **Why:** This moves learners from single sentences to basic text construction. It's a key feature of natural Ukrainian writing style. (Джерело: `4-klas-ukrayinska-mova-zaharijchuk-2021-1_s0148`, `4-klas-ukrmova-zaharijchuk_s0014`). For example: "Славко купив букет квітів... **Він** також узяв книжку." (Slavko bought a bouquet... **He** also took a book).

## Типові помилки L2 (Common L2 Errors)

English-speaking learners often make predictable errors when learning Ukrainian demonstratives due to interference from English grammar.

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| `Що цей?` | `Що це?` | Learners mistakenly use the gendered `цей` for the general question "What is this?". The correct form for identification is always the neutral, unchangeable `це`. (Джерело: `ext-video-4`) |
| `Ця стіл великий.` | `Цей стіл великий.` | This is a direct gender agreement error. The learner has not yet internalized that `стіл` is masculine and requires the masculine demonstrative `цей`. This is the most common error and is why linking demonstratives to gender is so critical. (Джерело: `3-klas-ukrainska-mova-ponomarova-2020-1_s0085`) |
| `Це стіл є новий.` | `Цей стіл новий.` or `Це новий стіл.` | Learners overuse the verb `є` (is/are), translating directly from English. In simple descriptive sentences in Ukrainian, the verb "to be" is usually omitted in the present tense. The first correct option uses the demonstrative as a pointer, while the second uses `це` as an identifier. |
| `Це столи.` | `Ці столи.` | The learner incorrectly uses the singular identifier `це` when pointing to multiple items. The correct plural demonstrative is `ці` for "these". (Джерело: `ext-ulp_youtube-261`) |
| `Мені подобається цей дівчина.` | `Мені подобається ця дівчина.` | Another gender agreement error, but with a feminine noun. The learner applies the default/masculine form `цей` to the feminine noun `дівчина`. (Джерело: `5-klas-ukrmova-uhor-2022-1_s0030`) |
| `Я живу в цей будинок.` | `Я живу в цьому будинку.` | This is a case error. While full declension is not an A1 topic, learners will encounter prepositions. They often incorrectly use the nominative form (`цей`) after a preposition instead of the required locative (`цьому`). This should be taught as a fixed chunk (`в цьому будинку`) at A1, with the grammatical explanation delayed. (<!-- VERIFY -->) |

## Деколонізаційні застереження (Decolonization Notes)

Teaching Ukrainian requires a conscious effort to de-link it from Russian and establish its own phonetic and grammatical foundation in the learner's mind.

1.  **Independent Phonetics:** The sound `[ц]` must be taught as a native Ukrainian phoneme. Do not describe it as "like the Russian ц". Use examples from within Ukrainian, like `цукор` (sugar), `палець` (finger), `кінець` (end). The learner's reference point must be Ukrainian itself.

2.  **No Russian Cognates as a Crutch:** Avoid teaching `цей` by comparing it to Russian `этот` or `той` to `тот`. While they are cognates from a common Slavic root, using Russian as the bridge reinforces a colonial linguistic dependency. Teach `цей` and `той` through their function and context within Ukrainian only.

3.  **Emphasize Native Etymology:** Briefly explain that `цей` comes from an older Ukrainian form `отъ + сей` ("lo, this"), which evolved into `отсей` and then was re-analyzed as `о-цей`, eventually yielding the standalone `цей` (Джерело: `ext-istoria_movy-103`). This demonstrates a clear, internal path of development for the word within the Ukrainian language itself, countering any false narrative of it being a Russian import or derivative.

4.  **Ukrainian Sentence Structure:** Stress that the omission of "to be" (`є`) in sentences like `Цей стіл червоний` is a standard feature of Ukrainian grammar. It is not an "informal" version of a structure that "should" have a verb like in Russian (`Этот стол есть красный`). This validates Ukrainian grammar on its own terms.

5.  **Stylistic Norms:** The use of demonstratives and personal pronouns (`цей`, `він`, `вона`) to avoid repeating nouns is a characteristic of good Ukrainian style, as taught in Ukrainian schools (Джерело: `4-klas-ukrmova-zaharijchuk_s0014`, `2-klas-ukrmova-bolshakova-2019-2_s0044`). It should be presented as a native stylistic device, not a calque from another language.

## Словниковий мінімум (Vocabulary Boundaries)

This vocabulary is appropriate for A1 learners when practicing demonstratives. It focuses on concrete, point-able objects found in a classroom or home.

**Іменники (Nouns):**
- ★★★ `стіл` (table) (Джерело: `ext-ulp_youtube-261`)
- ★★★ `стілець` (chair) (Джерело: `ext-ulp_youtube-261`)
- ★★★ `книга` (book)
- ★★★ `ручка` (pen) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0030`)
- ★★★ `вікно` (window) (Джерело: `ext-ulp_youtube-261`)
- ★★☆ `будинок` (house, building) (Джерело: `3-klas-ukrainska-mova-vashulenko-2020-1_s0128`)
- ★★☆ `кімната` (room) (Джерело: `ext-ulp_youtube-261`)
- ★★☆ `двері` (door - *plural only*) (Джерело: `ext-ulp_youtube-261`)
- ★★☆ `олівець` (pencil) (Джерело: `3-klas-ukrainska-mova-savchenko-2020-2_s0009`)
- ★★☆ `шафа` (wardrobe, cabinet) (Джерело: `ext-ulp_youtube-261`)
- ★☆☆ `ліжко` (bed) (Джерело: `ext-ulp_youtube-261`)
- ★☆☆ `поле` (field) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0030`)

**Прикметники (Adjectives):**
- ★★★ `новий` (new) (Джерело: `4-klas-ukrayinska-mova-zaharijchuk-2021-1_s0065`)
- ★★★ `старий` (old) (Джерело: `6-klas-ukrmova-betsa-2023_s0113`)
- ★★★ `великий` (big)
- ★★★ `малий` (small)
- ★★☆ `червоний` (red) (Джерело: `10-klas-ukrajinska-mova-avramenko-2018_s0186`)
- ★★☆ `синій` (blue) (Джерело: `3-klas-ukrainska-mova-vashulenko-2020-1_s0128`)
- ★★☆ `жовтий` (yellow) (Джерело: `6-klas-ukrmova-betsa-2023_s0113`)
- ★★☆ `зелений` (green) (Джерело: `6-klas-ukrmova-betsa-2023_s0113`)
- ★★☆ `гарний` (good, beautiful) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0081`)

**Дієслова (Verbs):**
- ★★★ `бути` (to be)
- ★★★ `мати` (to have)
- ★★★ `бачити` (to see)
- ★★☆ `жити` (to live) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0081`)
- ★★☆ `хотіти` (to want)

## Приклади з підручників (Textbook Examples)

These exercises, adapted from Ukrainian school materials, provide a gold standard for practice activities.

1.  **Gender Sorting with Demonstratives (Джерело: `3-klas-ukrainska-mova-kravtsova-2020-1_s0062`)**
    - **Format:** Sorting task. Provide a list of nouns and three columns.
    - **Prompt:** "Розподіли іменники за родами. Запиши назви в потрібний рядок." (Distribute the nouns by gender. Write the names in the correct row.)
    - **Task:**
        - **Він, мій, цей:** `стіл`, `олівець`, `будинок`
        - **Вона, моя, ця:** `книга`, `ручка`, `шафа`
        - **Воно, моє, це:** `вікно`, `ліжко`, `поле`

2.  **Forced Choice: This vs. That (Джерело: `6-klas-ukrmova-litvinova-2023_s0280`)**
    - **Format:** Multiple choice within a sentence.
    - **Prompt:** "Прочитайте речення, обираючи правильний займенник." (Read the sentences, choosing the correct pronoun.)
    - **Task:**
        - 1. Привал буде за (цією / тією) горою. (The stop will be behind *this* / *that* mountain.)
        - 2. Мені, будь ласка, (це / те) тістечко. (For me, please, *this* / *that* pastry.)
        - 3. Візьміть (цю / ту) книгу, не пошкодуєте. (Take *this* / *that* book, you won't regret it.)

3.  **Adjective and Demonstrative Agreement (Джерело: `6-klas-ukrmova-betsa-2023_s0113`, `3-klas-ukrainska-mova-vashulenko-2020-1_s0128`)**
    - **Format:** Fill-in-the-blanks for endings.
    - **Prompt:** "Оберіть правильний варіант закінчення." (Choose the correct ending.)
    - **Task:**
        - Який? (m): `Нов__ стіл`, `цікав__ фільм`, `цей хорош__ друг` → (`-ий`, `-ий`, `-ій`)
        - Яка? (f): `Ця нов__ сукня`, `цікав__ казка` → (`-а`, `-а`)
        - Яке? (n): `Це нов__ крісло`, `цікав__ оповідання` → (`-е`, `-е`)

4.  **Text Cohesion via Pronoun Substitution (Джерело: `4-klas-ukrmova-zaharijchuk_s0014`)**
    - **Format:** Text rewriting.
    - **Prompt:** "Спишіть текст, уникаючи повторів виділених слів. Підкресліть слова, які зв’язують речення в тексті." (Rewrite the text, avoiding repetition of the highlighted words. Underline the words that connect the sentences in the text.)
    - **Original Text:** "Марусі... подарували маленький рожевий ноутбук. **Ноутбук** став для Марусі найкращим другом. **Ноутбук** зберігав маленькі таємниці дівчинки..."
    - **Expected Output:** "Марусі... подарували маленький рожевий ноутбук. **Він** став для Марусі найкращим другом. **Цей комп'ютер** зберігав маленькі таємниці дівчинки..."

## Пов'язані статті (Related Articles)

- `pedagogy/a1/noun-gender`
- `pedagogy/a1/adjective-agreement`
- `pedagogy/a1/personal-pronouns`
- `pedagogy/a2/introduction-to-cases`
- `grammar/nouns/pluralization`
</wiki_context>

## Plan References

- 
- 

</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Наказовий спосіб (The Imperative Mood)` (~300 words)
- `## Як утворити? (How to Form It)` (~300 words)
- `## Підсумок — Summary` (~300 words)

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

PLAN-AWARE EXEMPTIONS: The following bans are RELAXED for this module because the plan explicitly teaches these constructs: Perfective aspect (plan teaches perfective verbs). Exception: If a grammar construct appears in this module's plan grammar list or objectives, it is ALLOWED for this module.

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
  1. **Volleyball practice — coach gives warm-up instructions: Принеси м'яч (m, ball)! Розстав конуси (pl, cones)! Натягни сітку (f, net)! Поклади рушники (pl, towels) на лавку (f, bench)! Відкрий двері (pl)!**
     Speakers: Тренер (coach), Гравці (players)
     Why: Imperative with м'яч(m), конуси(pl), сітка(f), рушники(pl), лавка(f)

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

GRAMMAR CONSTRAINTS (A1.7 — People & Communication, M44-M50):
Vocative, imperative, dative, conjunctions, subordinate clauses.

ALLOWED:
- Vocative case (Олено! Тарасе!)
- Imperative mood (Читай! Скажіть! Дайте!)
- Dative case basics (мені, тобі, йому)
- Conjunctions (і, а, але, бо, тому що)
- Simple subordinate clauses (що, де, коли, якщо)
- All cases and tenses from previous phases

BANNED: Past/future tense, participles, passive voice

### Vocabulary

**Required:** читати (to read), писати (to write), слухати (to listen), дивитися (to look/watch), говорити (to speak), дати (to give), сказати (to say/tell), іти (to go)
**Recommended:** відкрити (to open), сісти (to sit down), показати (to show), запитати (to ask), підручник (textbook, m), сторінка (page, f), речення (sentence, n)

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
## Діалоги (~330 words)
- P1 (~30 words): Introduction to the social contexts where instructions and requests are vital, setting the scene for two different registers of speech.
- P2 (~100 words): Dialogue 1 — In the classroom. A teacher gives instructions to students: «Відкрийте підручники, будь ласка. Читайте текст. Пишіть три речення. Запитуйте, якщо є питання.» Focus on the plural/formal forms.
- P3 (~50 words): Analysis of the classroom dialogue, highlighting the relationship between the teacher and students and the use of plural verbs for a group.
- P4 (~100 words): Dialogue 2 — Between friends. Two friends discuss going to a café: «Слухай, ходімо! Подивись, яка погода. Дай мені меню. Скажи, що ти хочеш.» Focus on informal singular forms.
- P5 (~50 words): Analysis of the informal dialogue, noting how the tone differs from the classroom setting despite the grammatical goal remaining the same.

## Наказовий спосіб (~330 words)
- P1 (~90 words): Defining the "Наказовий спосіб" (Imperative Mood) using Ukrainian Grade 5 terminology. Explain its primary functions: commands, requests, invitations, and warnings.
- P2 (~80 words): Register awareness: Choosing between "ти" (informal singular) and "ви" (formal or plural). Explain that this choice mirrors the pronouns the learner already knows from earlier modules.
- P3 (~90 words): Politeness and "Будь ласка." Explain the cultural nuance that while the imperative is direct, adding "будь ласка" (please) transforms a command into a standard polite request. Contrast "Дай!" with "Дай, будь ласка."
- P4 (~70 words): Using names and titles to soften requests. Examples of addressing peers (Олено, читай) versus formal address (Пане Іване, читайте) using the vocative hint.
- <!-- INJECT_ACTIVITY: group-sort-imperative-register --> [group-sort, Sort: ти-forms vs ви-forms (читай vs читайте, дай vs дайте, скажи vs скажіть), 10 items]

## Як утворити? (~330 words)
- P1 (~80 words): Formation of the "ти" form for Group I verbs ending in -ати. Explain the stem extraction and adding -й: читати → читай, слухати → слухай, співати → співай.
- P2 (~80 words): Formation of the "ти" form for Group II verbs ending in -ити. Explain the drop of the ending and the result: говорити → говори, ходити → ходи, сидіти → сиди. Mention the role of stress.
- P3 (~80 words): Common irregular and short imperatives that every A1 learner needs. Examples: дати → дай, сказати → скажи, їсти → їж, іти → іди, відкрити → відкрий.
- P4 (~90 words): Formation of the "ви" form for all verbs. The universal rule: take the "ти" form and add -те. Examples: читай + те = читайте, говори + те = говоріть (note the vowel shift for stress), дай + те = дайте.
- <!-- INJECT_ACTIVITY: fill-in-imperative-formation --> [fill-in, Form imperative: читати → читай / читайте, писати → пиши / пишіть, 10 items]
- <!-- INJECT_ACTIVITY: quiz-polite-choice --> [quiz, Choose correct: ___, будь ласка! (дай / даєш / дати) for context, 8 items]

## Підсумок — Summary (~330 words)
- P1 (~150 words): Comprehensive table of essential imperatives for daily life. List verbs: читати, писати, слухати, дивитися, говорити, іти, дати, сказати, сісти, відкрити. Provide the "ти" form, "ви" form, and English meaning for each.
- P2 (~180 words): Self-check and practical application. 
    - Q: How do you ask a friend to "look"? (A: Дивись!) 
    - Q: How do you ask a group of people to "listen"? (A: Слухайте!)
    - Q: What word makes any command polite? (A: Будь ласка.)
    - Q: How do you say "Please say" to a boss? (A: Скажіть, будь ласка.)
- <!-- INJECT_ACTIVITY: fill-in-contextual-names --> [fill-in, Complete: Олено, ___ книжку! Пане Іване, ___ книжку! (дай/дайте), 6 items]

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
