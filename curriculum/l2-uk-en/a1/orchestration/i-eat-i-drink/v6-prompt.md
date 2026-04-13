

---

## Your Writing Identity

**You are: Lead Ukrainian Instructor.** Your persona is *The Patient Guide*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **37: I Eat, I Drink** (A1, A1.6 [Food and Shopping]).

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
module: a1-037
level: A1
sequence: 37
slug: i-eat-i-drink
version: '1.2'
title: I Eat, I Drink
subtitle: Я їм хліб, п'ю каву — accusative for what you eat and drink
focus: grammar
pedagogy: PPP
phase: A1.6 [Food and Shopping]
word_target: 1200
objectives:
- Conjugate їсти and пити in present tense
- Use accusative case for inanimate direct objects (Я їм хліб, п'ю каву)
- Recognize feminine accusative ending change (-а → -у): кава → каву, вода → воду
- Describe eating and drinking habits using accusative
dialogue_situations:
- setting: 'Lunch break at work — unpacking lunch boxes: Я їм бутерброд (m, sandwich)
    і п''ю чай (m, tea). А ти? Я їм салат (m) і п''ю каву (f, coffee). Also: яблуко
    (n), банан (m), вода (f), сік (m, juice).'
  speakers:
  - Колега 1
  - Колега 2
  motivation: 'Accusative: бутерброд(m), салат(m), каву(f→acc), яблуко(n), чай(m)'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Breakfast conversation: — Що ти їш на сніданок? — Я їм кашу і п''ю
    каву. — А Олена? — Вона їсть хліб з маслом і п''є чай. — А діти? — Вони їдять
    яйця і п''ють молоко. Full conjugation of їсти and пити in natural context.'
  - 'Dialogue 2 — At lunch: — Що ви їсте на обід? — Ми їмо суп і салат. — А що п''єте?
    — Ми п''ємо воду або сік. — Я теж хочу суп. — Добре, замовляй! Review of їсти/пити
    with plural subjects.'
- section: Їсти і пити (To Eat and To Drink)
  words: 300
  points:
  - 'Conjugation of їсти (irregular — NOT Group I or II): я їм, ти їси, він/вона їсть,
    ми їмо, ви їсте, вони їдять. Conjugation of пити (Group I): я п''ю, ти п''єш,
    він/вона п''є, ми п''ємо, ви п''єте, вони п''ють. Both are essential daily verbs
    — high frequency.'
  - 'Ukrainian school approach (Grade 4 — знахідний відмінок): ''Бачу що? кого?''
    — the accusative answers ''what do I see/eat/drink?'' Я їм (що?) хліб. Я п''ю
    (що?) каву. The question що? triggers accusative for inanimate objects.'
- section: Знахідний відмінок — неживе (Accusative Inanimate)
  words: 300
  points:
  - 'Accusative for inanimate nouns — what changes: Masculine inanimate: NO CHANGE
    (= nominative). хліб → хліб (Я їм хліб), суп → суп (Я їм суп), сік → сік (Я п''ю
    сік). Neuter: NO CHANGE (= nominative). молоко → молоко (Я п''ю молоко), яйце
    → яйце (Я їм яйце).'
  - 'Feminine -а → -у (THE key change at A1): кава → каву (Я п''ю каву), вода → воду
    (Я п''ю воду), риба → рибу (Я їм рибу), каша → кашу (Я їм кашу), картопля → картоплю
    (Я їм картоплю). Pattern: feminine nouns ending in -а change to -у, ending in
    -я change to -ю. This is the ONLY accusative change learners need now.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Accusative inanimate summary: Masculine/Neuter: no change (хліб, молоко stay
    the same). Feminine -а → -у, -я → -ю (кава → каву, картопля → картоплю). Test:
    Я їм ___ (риба → рибу). Я п''ю ___ (вода → воду). Self-check: Say 3 things you
    eat and 3 things you drink today. Use the correct accusative form for each.'
vocabulary_hints:
  required:
  - їсти (to eat — irregular)
  - пити (to drink)
  - їм (I eat)
  - п'ю (I drink)
  - каву (coffee — accusative)
  - воду (water — accusative)
  - рибу (fish — accusative)
  recommended:
  - кашу (porridge — accusative)
  - картоплю (potato — accusative)
  - сметану (sour cream — accusative)
  - їсть (he/she eats)
  - п'є (he/she drinks)
  - їдять (they eat)
  - п'ють (they drink)
activity_hints:
- type: fill-in
  focus: Form the accusative case for feminine (-а/-я → -у/-ю) and masculine/neuter
    (no change)
  items: 8
  blanks:
  - Я їм (риба) {рибу}.
  - Вона п'є (вода) {воду}.
  - Він їсть (хліб) {хліб}.
  - Ми п'ємо (молоко) {молоко}.
  - Вони їдять (каша) {кашу}.
  - Ти п'єш (кава) {каву}.
  - Я їм (суп) {суп}.
  - Вона їсть (картопля) {картоплю}.
- type: quiz
  focus: Select the correct accusative form to complete the sentence
  items: 6
  questions:
  - Я п'ю... (каву / кава / кави)
  - Він їсть... (рибу / риба / рибі)
  - Ми п'ємо... (сік / соку / соком)
  - Вона їсть... (м'ясо / м'ясу / м'яса)
  - Вони п'ють... (воду / вода / воді)
  - Ти їш... (кашу / каша / каші)
- type: fill-in
  focus: Conjugate the verbs їсти (irregular) and пити (Group I)
  items: 8
  blanks:
  - Я {їм} суп.
  - Ми {п'ємо} чай.
  - Вона {їсть} хліб.
  - Вони {п'ють} воду.
  - Ти {їси} рибу?
  - Ви {п'єте} каву?
  - Він {п'є} сік.
  - Вони {їдять} кашу.
- type: group-sort
  focus: Sort nouns based on how they change in the accusative case (inanimate)
  items: 8
  groups:
  - name: Змінюється (-у/-ю)
    items:
    - кава
    - вода
    - риба
    - каша
  - name: Не змінюється (як у називному)
    items:
    - хліб
    - сік
    - молоко
    - м'ясо
connects_to:
- a1-038 (At the Cafe)
prerequisites:
- a1-036 (Food and Drink)
grammar:
- 'Accusative inanimate: masculine/neuter = nominative, feminine -а→-у, -я→-ю'
- Conjugation of їсти (irregular) and пити (Group I)
- Question що? as accusative trigger for inanimate
register: розмовний
references:
- title: ULP Season 1, Episode 32
  url: https://www.ukrainianlessons.com/episode32/
  notes: Accusative case introduction — inanimate objects.
- title: 'Grade 4 textbook: Знахідний відмінок (Заболотний)'
  notes: 'Ukrainian school approach: бачу що? кого?'

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
- Confirmed: їсти, пити, їм, п'ю, каву, воду, рибу, кашу, картоплю, сметану, їсть, п'є, їдять, п'ють
- Not found: None

## Grammar Rules
- Apostrophe in verbs (п'ю, п'є, п'ють): Правопис §7 — Апостроф пишемо перед я, ю, є, ї: Після букв на позначення губних приголосних б, п, в, м, ф.

## Calque Warnings
- на сніданок: OK
- на обід: OK
- замовляй: OK

## CEFR Check
- їсти: A1 — OK
- пити: A1 — OK
- кава: A1 — OK
- вода: A1 — OK
- сметана: A1 — OK
- риба: A1 — OK
- каша: A2 — Above target
- картопля: A1 — OK
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
# Knowledge Packet: I Eat, I Drink
**Module:** i-eat-i-drink | **Track:** A1

<wiki_context>
## Compiled Wiki Knowledge

The following articles from the project wiki provide compiled knowledge relevant to this module. Use them as authoritative context — they were compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).

### Вікі: pedagogy/a1/i-eat-i-drink.md

# Педагогіка A1: I Eat I Drink



## Методичний підхід (Methodological Approach)

The core methodological principle for introducing "I eat, I drink" at the A1 level is to move from simple identification to active use through the introduction of the Accusative case. Ukrainian pedagogy emphasizes a structured, cyclical approach where vocabulary is introduced in thematic blocks and immediately put into grammatical practice.

1.  **Thematic Vocabulary Blocks:** Native-speaker textbooks introduce food and drink vocabulary in clear, logical groups. The writer should follow this model. For example, a Grade 5 textbook for Hungarian speakers groups words by question (`Що?`, `Що робити?`) and then by category: `Страви` (Dishes), `Продукти` (Products), `Фрукти` (Fruits), `Овочі` (Vegetables), and `Смак` (Taste) (Source `5-klas-ukrmova-uhor-2022-1_s0022`). This method helps learners build a mental map of the vocabulary domain.

2.  **Verb-Noun Pairing:** The curriculum should immediately link a new noun to its relevant verb. For instance, when teaching `сніданок` (breakfast), also teach the verb `снідати` (to have breakfast). Similarly, pair `обід` with `обідати` and `вечеря` with `вечеряти` (Source `5-klas-ukrmova-uhor-2022-1_s0022`, Source `ext-ulp_youtube-255`). This reinforces the connection and moves the learner from passive vocabulary to active use.

3.  **Grammar in Context (The Accusative Case):** The concept of a direct object (`знахідний відмінок`) is central to this topic. It should not be taught as a dry grammar table. Instead, introduce it through high-frequency sentence patterns like "Я їм...", "Я п'ю...", "Я хочу...". The learner first hears and mimics the pattern, for example, `Я хочу воду` (Source `ext-ulp_youtube-119`). Only after they are comfortable with the pattern should the rule (feminine `-а` → `-у`) be explained. This "pattern before rule" approach is crucial for internalizing the case system naturally. Textbooks for native speakers demonstrate this by showing contrasting sentences like «Несе Галя воду» where `воду` is the object (Source `5-klas-ukrmova-litvinova-2022_s0219`).

4.  **Interactive Practice through Q&A:** Learning is solidified through simple, repetitive questions. For example: `Що ти їси?` (What are you eating?), `Що ти п'єш?` (What are you drinking?), `Яку воду ти вживаєш?` (What water do you consume?) (Source `3-klas-ukrainska-mova-ponomarova-2020-1_s0008`). This encourages active recall and production from the very beginning.

## Послідовність введення (Introduction Sequence)

The introduction must be carefully scaffolded to prevent cognitive overload. Follow this sequence strictly.

1.  **Step 1: Core Verbs & Pronouns:** Introduce the two most critical verbs: `їсти` (to eat) and `пити` (to drink). Teach only the 1st person singular forms: **`Я їм`** (I eat) and **`Я п'ю`** (I drink). (Source `6-klas-ukrmova-betsa-2023_s0206`, Source `ext-ulp_youtube-255`).

2.  **Step 2: Basic Nouns (Nominative Case):** Introduce 5-7 essential, high-frequency food and drink nouns in their dictionary (nominative) form. Focus on items that do not require complex explanations.
    *   `вода` (water), `чай` (tea), `кава` (coffee), `сік` (juice)
    *   `хліб` (bread), `сир` (cheese), `суп` (soup)

3.  **Step 3: The `це` Construction:** Teach the first complete sentence structure using the verb "to be" (which is omitted in the present tense).
    *   `Це вода.` (This is water.)
    *   `Це чай.` (This is tea.)

4.  **Step 4: Introducing the Accusative Case (Direct Object):** This is the most critical step. Use the high-frequency verb `хотіти` (to want) in the `Я хочу` form.
    *   **Feminine nouns:** Explicitly show the change `а` → `у`. This is the first and most important case change for learners to master for this topic.
        *   `вода` → `Я хочу **воду**.`
        *   `кава` → `Я хочу **каву**.`
        (Source `ext-ulp_youtube-119`)
    *   **Masculine/Neuter nouns:** Explain that for inanimate objects, the form *does not change*. This is a point of relief for the learner.
        *   `сік` → `Я хочу **сік**.`
        *   `чай` → `Я хочу **чай**.`
        *   `молоко` → `Я хочу **молоко**.`
        (Source `ext-ulp_youtube-119`)

5.  **Step 5: Active Use with `їм` and `п'ю`:** Now, circle back to the first verbs and apply the new Accusative case knowledge.
    *   `Я п'ю **воду**.` `Я п'ю **каву**.` `Я п'ю **сік**.`
    *   `Я їм **хліб**.` `Я їм **сир**.` `Я їм **суп**.`

6.  **Step 6: Expanding Vocabulary:** Once the grammatical pattern is established, introduce more food and meal-related vocabulary, including meals of the day.
    *   Nouns: `сніданок` (breakfast), `обід` (lunch), `вечеря` (dinner), `риба` (fish), `м'ясо` (meat), `салат` (salad), `борщ` (borscht).
    *   Verbs: `снідати` (to have breakfast), `обідати` (to have lunch), `вечеряти` (to have dinner).
    (Source `5-klas-ukrmova-uhor-2022-1_s0022`)

## Типові помилки L2 (Common L2 Errors)

Address these errors proactively in the lesson design.

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| `Я хочу вода.` | `Я хочу **воду**.` | **Grammar Transfer:** English has no grammatical case for direct objects, so learners default to using the nominative (dictionary) form. The module must provide extensive drills on changing feminine nouns ending in `-а` to `-у` after verbs like `хочу`, `їм`, `п'ю`. (Source `ext-ulp_youtube-119`) |
| `Я їсть хліб.` | `Я **їм** хліб.` | **Verb Conjugation:** Learners often confuse the 1st person (`я їм`) and 3rd person (`він/вона їсть`) forms. These must be taught as distinct pairs. The verb `їсти` is irregular and needs special attention. (Source `6-klas-ukrmova-betsa-2023_s0206`) |
| `Вона п'ю каву.` | `Вона **п'є** каву.` | **Verb Conjugation:** Similar to `їсти`, the verb `пити` (to drink) has a distinct conjugation that must be drilled. `Я п'ю` vs. `Він/Вона п'є`. (Source `ext-ulp_youtube-255`) |
| `Я п'ю борщ.` | `Я **їм** борщ.` | **Semantic Difference:** In English, soup is "eaten". While `пити бульйон` (to drink broth) is possible, thick soups like `борщ` are almost always paired with the verb `їсти`. (Source `ext-ulp_youtube-80`: "...борщ в Україні їдять...") |
| `Я люблю їсти...` (pronounced `істи`) | `Я люблю **їсти**...` (pronounced `йісти`) | **Phonetic Interference:** English speakers struggle with the letter `ї`, often reducing it to `і`. It must be explicitly taught that `ї` is *always* pronounced as two sounds: `[йі]`, as in "Yee-sty". (Source `1-klas-bukvar-bolshakova-2018-1_s0072`) |
| `Мені, будь ласка, піца.` | `Мені, будь ласка, **піцу**.` | **Ordering Phrases:** When ordering, the item is the direct object, even if the verb is implied. This is a very common context for A1 learners. The structure `Мені, будь ласка, [noun in Accusative]` must be drilled. (Source `ext-ulp_youtube-119`, `ext-ulp_youtube-117`) |

## Деколонізаційні застереження (Decolonization Notes)

This section is non-negotiable. The curriculum must teach Ukrainian on its own terms, completely independent of Russian.

-   **No Russian Phonetic Analogues:** Never teach Ukrainian sounds by comparing them to Russian. For example, do not describe Ukrainian `и` as "like Russian ы" or `і` as "like Russian и". Learners must build a new, distinct phonetic system for Ukrainian from zero.
-   **Vocabulary Purity:** Strictly use Ukrainian vocabulary. The word for coffee is **`кава`**. The word `кофе` is a Russianism and must be actively corrected. The word for sugar is **`цукор`**. The word `сахар` is a Russianism. Use the word lists from Ukrainian textbooks as the source of truth (e.g., Source `5-klas-ukrmova-uhor-2022-1_s0022`).
-   **`Горілка` vs. Vodka:** When introducing alcoholic beverages (if at all at A1), present `горілка` as a traditional Ukrainian national drink in its own right, not merely as the "Ukrainian word for vodka." (Source `ext-ulp_youtube-123`).
-   **Cultural Context:** Food idioms and proverbs are deeply tied to culture. While A1 learners won't master them, they should be taught that phrases like `заварити кашу` (to start trouble) or `їсти чужий хліб` (to be dependent on someone) are uniquely Ukrainian cultural expressions and not loan translations. (Source `5-klas-ukrmova-golub-2022_s0059`). The goal is to build respect for Ukrainian as a complete and independent linguistic and cultural system from day one.

## Словниковий мінімум (Vocabulary Boundaries)

This vocabulary is appropriate for an A1 learner. Stick to these words and avoid introducing more complex items.

**Іменники (Nouns)**
*   ★★★ (Essential): `вода`, `хліб`, `чай`, `кава`, `сік`, `молоко`, `суп`, `борщ`
*   ★★ (Useful): `сніданок`, `обід`, `вечеря`, `сир`, `м'ясо`, `риба`, `салат`, `цукор`, `сіль`
*   ★ (Can wait): `каша`, `картопля`, `яблуко`, `бутерброд`, `пиріг`

**Дієслова (Verbs)**
*   ★★★ (Essential): `їсти` (to eat), `пити` (to drink), `хотіти` (to want)
*   ★★ (Useful): `снідати` (to have breakfast), `обідати` (to have lunch), `вечеряти` (to have dinner)
*   ★ (Can wait): `готувати` (to cook), `замовляти` (to order)

**Прикметники (Adjectives)**
*   ★★★ (Essential): `смачний` (tasty)
*   ★★ (Useful): `солодкий` (sweet), `гарячий` (hot), `холодний` (cold)
*   ★ (Can wait): `солоний` (salty), `кислий` (sour)

(Vocabulary sourced and cross-referenced from `5-klas-ukrmova-uhor-2022-1_s0022`, `ext-ulp_youtube-255`, `ext-ulp_youtube-123`)

## Приклади з підручників (Textbook Examples)

The writer should model activities directly on these proven pedagogical patterns from Ukrainian source materials.

1.  **Q&A Practice (Source `3-klas-ukrainska-mova-ponomarova-2020-1_s0008`):**
    *   **Prompt:** Ask and answer simple questions about what you drink.
    *   **Example:**
        *   `— Яку воду ти вживаєш?` (What water do you consume?)
        *   `— Я п'ю мінеральну воду.` (I drink mineral water.)
        *   `— Що ти п'єш на сніданок?` (What do you drink for breakfast?)
        *   `— Я п'ю чай без цукру.` (I drink tea without sugar.) (Source `ext-ulp_youtube-255`)

2.  **Dialogue for Ordering (Source `ext-ulp_youtube-117`):**
    *   **Prompt:** Complete the dialogue to order food at a restaurant. Use the Accusative case.
    *   **Example:**
        *   `— Ви готові зробити замовлення?` (Are you ready to make an order?)
        *   `— Так, мені, будь ласка, **пасту** з овочами і **негазовану воду**.` (Yes, pasta with vegetables and non-carbonated water for me, please.)

3.  **Sentence Transformation (Implicit in Source `5-klas-ukrmova-litvinova-2022_s0219`):**
    *   **Prompt:** Create a sentence using "Я їм" or "Я п'ю". Remember to change the noun if necessary.
    *   **Example:**
        *   Noun: `кава` (f.) → Sentence: `Я п'ю **каву**.`
        *   Noun: `борщ` (m.) → Sentence: `Я їм **борщ**.`
        *   Noun: `риба` (f.) → Sentence: `Я їм **рибу**.`

4.  **Forming Questions (Source `2-klas-ukrmova-bolshakova-2019-2_s0076`):**
    *   **Prompt:** Read the statement and write a question for it.
    *   **Statement:** `Білий ведмідь їсть рибу.` (The polar bear eats fish.)
    *   **Possible Questions:**
        *   `**Хто** їсть рибу?` (Who eats fish?)
        *   `**Що** їсть білий ведмідь?` (What does the polar bear eat?)

## Пов'язані статті (Related Articles)
-   [Pedagogy A1: Verbs of Being and Wanting](./pedagogy/a1/verbs-of-being-wanting)
-   [Grammar: The Accusative Case (Direct Object)](./grammar/cases/accusative) (See also external sources `ext-article-0` through `ext-video-5`)
-   [Phonetics: The Letter Ї](./phonetics/letter-yi)

---

### Вікі: pedagogy/a1/food-and-drink.md

# Педагогіка A1: Food And Drink



## Методичний підхід (Methodological Approach)
The pedagogical approach for teaching "Food and Drink" at the A1 level should be grounded in high-frequency, tangible vocabulary and immediate practical application, mirroring how Ukrainian children learn. The focus is on building a core lexicon and using it in simple, descriptive sentences.

Ukrainian elementary textbooks (Джерело: `2-klas-ukrmova-bolshakova-2019-1_s0090`, `3-klas-ukrainska-mova-kravtsova-2020-1_s0072`) introduce food by connecting nouns to their characteristics. A key activity is linking a food item (`пиріг`) to its ingredients (`з вишнями`) and the resulting adjective (`вишневий пиріг`) (Джерело: `2-klas-ukrmova-bolshakova-2019-2_s0041`). This immediately reinforces noun-adjective agreement, a cornerstone of Slavic grammar.

The learning process should be scaffolded:
1.  **Core Nouns:** Introduce staple products found in any kitchen (`хліб`, `вода`, `молоко`, `сіль`, `цукор`) (Джерело: `ext-ulp_youtube-67`).
2.  **Meal Verbs:** Introduce the meals of the day (`сніданок`, `обід`, `вечеря`) along with their corresponding verbs (`снідати`, `обідати`, `вечеряти`) (Джерело: `ext-ulp_youtube-255`). This creates a natural context for using food vocabulary.
3.  **Descriptive Adjectives:** Immediately introduce `смачний` and its gendered forms (`смачна`, `смачне`). This is a powerful tool for practicing gender agreement in a rewarding context. Learners can express simple opinions (`борщ смачний`) (Джерело: `ext-ulp_youtube-291`).
4.  **Simple Recipes and Menus:** Use simplified recipes or menu-creation tasks to contextualize vocabulary and introduce basic imperative verbs (`візьми`, `додай`) or ordering phrases (`Дайте, будь ласка...`) (Джерело: `2-klas-ukrmova-bolshakova-2019-1_s0088`, `ext-ulp_youtube-292`).

This approach moves from simple identification (Це хліб) to description (Це смачний хліб) to action (Я їм хліб на сніданок) to transaction (Дайте, будь ласка, хліб).

## Послідовність введення (Introduction Sequence)

The vocabulary and grammar should be introduced in a logical, compounding order.

1.  **Step 1: The Essentials (Core Nouns & Verbs).** Start with the absolute highest-frequency words that are culturally universal.
    *   **Nouns:** `хліб`, `вода`, `сіль`, `цукор`, `молоко`, `чай`, `кава`. These are mostly masculine or feminine with clear endings, providing a good entry point for gender.
    *   **Verbs:** Introduce `їсти` (to eat) and `пити` (to drink) and their present-tense conjugations. They are irregular but essential (Джерело: `ext-ulp_youtube-255`).

2.  **Step 2: Meals of the Day.** Provide the daily structure for using food vocabulary.
    *   **Nouns:** `сніданок` (breakfast), `обід` (lunch), `вечеря` (dinner).
    *   **Verbs:** `снідати`, `обідати`, `вечеряти`. Teach the pattern: `Я снідаю о восьмій годині.` (Джерело: `ext-ulp_youtube-255`).

3.  **Step 3: Basic Adjective Agreement.** Introduce the concept of grammatical gender through description.
    *   **Adjective:** `смачний` (m), `смачна` (f), `смачне` (n).
    *   **Practice:** Pair with known nouns: `смачний хліб`, `смачна кава`, `смачне молоко`. This should be drilled extensively. The expression `Смачного!` (Enjoy your meal!) can also be introduced here as a fixed phrase (Джерело: `ext-ulp_youtube-292`).

4.  **Step 4: Common Ukrainian Dishes & Produce.** Expand the lexicon to include culturally relevant items.
    *   **Dishes:** `борщ` (m), `суп` (m), `каша` (f), `салат` (m).
    *   **Produce:** `картопля` (f), `капуста` (f), `м'ясо` (n), `риба` (f), `сир` (m), `яйце` (n). These provide more examples for gender agreement. (Джерело: `5-klas-ukrmova-uhor-2022-1_s0022`).

5.  **Step 5: Ordering Food (Accusative Case).** Introduce a practical, transactional context.
    *   **Phrases:** `Дайте, будь ласка...`, `Я буду...`, `Можна...`.
    *   **Grammar:** Explain that feminine nouns ending in `-а/-я` change to `-у/-ю`. `Дайте, будь ласка, каву` (from `кава`). Masculine inanimate and neuter nouns do not change. `Я буду борщ`. This is a gentle introduction to the case system. (Джерело: `ext-ulp_youtube-292`).

## Типові помилки L2 (Common L2 Errors)
English-speaking learners often encounter predictable hurdles. Proactively addressing them is key.

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| `Я люблю творог.` | `Я люблю сир.` | `Творог` is a Russianism. The Ukrainian word for farmer's cheese/quark is `сир`. This word also means "cheese" in general, and context distinguishes them. For A1, teach `сир` for both. (Джерело: `9-klas-ukrajinska-mova-avramenko-2017_s0014`). |
| `Борщ дуже смачно.` | `Борщ дуже смачний.` | This is a classic confusion between an adverb (`смачно` - tastily/it's tasty) and an adjective (`смачний` - tasty). The adjective must agree in gender with the noun it describes. Teach `Дуже смачно!` as a standalone exclamation and `[noun] + смачний/а/е` as the descriptive structure. (Джерело: `ext-ulp_youtube-291`). |
| `смачний каша` | `смачна каша` | Learners often default to the masculine form of adjectives. Gender agreement must be drilled relentlessly with food items, as they provide a perfect, tangible set of masculine, feminine, and neuter nouns (`борщ`, `каша`, `пюре`). (Джерело: `ext-ulp_youtube-291`). |
| `жарена картопля` | `смажена картопля` | `Жарений` is a common calque from Russian. The correct Ukrainian participle is `смажений`. This should be taught from the beginning to avoid reinforcing the Russianism. (Джерело: `7-klas-ukrmova-zabolotnyi-2024_s0017`). |
| `кава без цукор` | `кава без цукру` | The preposition `без` (without) always requires the Genitive case. While the full case system is A2, `без цукру` and `без молока` are high-frequency chunks worth memorizing at A1. (Джерело: `ext-ulp_youtube-255`). |
| `Я їм сніданок.` | `Я снідаю.` | While not strictly wrong, `Я снідаю` is the more natural and common way to say "I'm having breakfast." Learners often translate directly from English ("I eat breakfast"). Highlighting the dedicated verbs (`снідати`, `обідати`, `вечеряти`) is important. (Джерело: `ext-ulp_youtube-255`). |

## Деколонізаційні застереження (Decolonization Notes)

Teaching Ukrainian food is an opportunity to teach Ukrainian culture on its own terms. It is critical to avoid the colonial trap of explaining Ukrainian phenomena through a Russian lens.

1.  **Borscht is Ukrainian:** This must be stated unequivocally. Explain its ancient origins in Ukraine, tied to the fermentation of beet (`буряковий квас`) long before potatoes or tomatoes were introduced (Джерело: `ext-ulp_youtube-84`). Mention its recognition by UNESCO as part of Ukraine's intangible cultural heritage. Frame it as a dish that unites all Ukrainians, with regional variations, not as a generic "Eastern European soup."
2.  **Avoid Russian Vocabulary:** Do not use or introduce Russianisms. The most common error is `творог` for `сир`. Correct this immediately and explain that `сир` is the authentic Ukrainian word. Likewise, use `смажений` not `жарений`, `тушкований` not `тушений` (Джерело: `9-klas-ukrajinska-mova-avramenko-2017_s0014`, `7-klas-ukrmova-zabolotnyi-2024_s0017`).
3.  **Contextualize Soviet Cuisine:** Dishes like `салат Олів'є` or `Оселедець під шубою` are extremely popular in Ukraine, especially for holidays. However, it's pedagogically important to explain their origin in the Soviet era as part of a policy of culinary unification, which aimed to create a single "Soviet people" and often simplified or replaced regional cuisines (Джерело: `ext-ulp_youtube-81`). This contrasts them with deeper-rooted dishes like borscht or varenyky.
4.  **Teach Phonetics Directly:** Do not explain Ukrainian sounds by comparing them to Russian (e.g., "Ukrainian `и` is like Russian `ы`"). Build the learner's phonetic map from scratch using Ukrainian examples only. For food, this means teaching the pronunciation of `гриби` or `риба` on its own terms.

## Словниковий мінімум (Vocabulary Boundaries)

This vocabulary is suitable for A1 learners.

### Іменники (Nouns)
*   ★★★ `вода`, `хліб`, `сіль`, `цукор`, `чай`, `кава`, `молоко` (staples)
*   ★★★ `сніданок`, `обід`, `вечеря` (meals)
*   ★★☆ `борщ`, `суп`, `каша`, `салат`, `пюре` (simple dishes)
*   ★★☆ `м'ясо`, `риба`, `сир`, `яйце` (pl. `яйця`), `картопля`, `капуста` (core ingredients)
*   ★★☆ `сік`, `узвар`, `компот` (common drinks)
*   ★☆☆ `вареники`, `голубці`, `млинці`, `деруни` (more complex traditional dishes)
*   ★☆☆ `фрукти` (pl.), `овочі` (pl.), `гриби` (pl.) (categories)
*   ★☆☆ `яблуко`, `груша`, `банан`, `лимон` (specific fruits)

### Дієслова (Verbs)
*   ★★★ `їсти`, `пити` (to eat, to drink)
*   ★★★ `снідати`, `обідати`, `вечеряти` (to have breakfast/lunch/dinner)
*   ★★☆ `любити`, `хотіти` (to love, to want)
*   ★★☆ `готувати` (to cook/prepare)
*   ★☆☆ `варити`, `смажити` (to boil, to fry)

### Прикметники / Прислівники (Adjectives / Adverbs)
*   ★★★ `смачний` (-а, -е), `дуже смачно` (tasty, very tasty)
*   ★★☆ `солодкий`, `солоний`, `кислий`, `гіркий` (tastes)
*   ★★☆ `гарячий`, `холодний` (temperature)
*   ★★☆ `червоний`, `зелений`, `жовтий`, `білий` (colors for produce)
*   ★☆☆ `пісний` (lenten/meat-free, culturally important) (Джерело: `ext-ulp_youtube-154`)

## Приклади з підручників (Textbook Examples)

These exercises from Ukrainian textbooks are models for A1 activities.

1.  **Adjective Formation from Nouns (Source: `2-klas-ukrmova-bolshakova-2019-2_s0041`)**
    This exercise directly teaches how to describe a dish based on its main ingredient, reinforcing vocabulary and adjective agreement.
    *   **Завдання:** Запиши слово — назву ознаки.
    *   **Приклад:** `Пиріг з вишнями — вишневий пиріг.`
    *   `Сік із абрикосів — ... сік.`
    *   `Компот із груш — ... компот.`
    *   `Морозиво з полуниці — ... морозиво.`

2.  **Creating a Menu (Source: `2-klas-ukrmova-bolshakova-2019-2_s0041`)**
    A practical, creative task that requires learners to categorize dishes and think about meal structure.
    *   **Завдання:** `Створи меню для обіду та вечері. Запиши страви за послідовністю їх подачі та за абеткою.` (Create a menu for lunch and dinner. Write the dishes in the order they are served and in alphabetical order.)

3.  **Simple Recipe Comprehension (Source: `3-klas-ukrainska-mova-kravtsova-2020-1_s0077`)**
    This uses a recipe to practice numbers and food vocabulary in a command-based context.
    *   **Завдання:** `Прочитай рецепт фруктового салату та приготуй на дозвіллі разом із дорослими.`
    *   **Текст:** `Для його приготування тобі потрібно один стиглий банан, два яблука, три груші, п’ять столових ложок сметани, чотири чайні ложки цукру. Помий та поріж кубиками яблука, банани, груші. Змішай та виклади гіркою на тарілку. Збий сметану з цукром і полий салат.`

4.  **Restaurant Dialogue (Source: `8-klas-ukrmova-zabolotnyi-2025_s0021`)**
    This situational task prepares learners for a real-world interaction, using specific dish names.
    *   **Завдання:** `Уявіть, що ви в закладі громадського харчування. Складіть і запишіть діалог між вами та офіціантом / офіціанткою (4–5 реплік), використавши кілька поданих словосполучень.`
    *   **Опорні слова:** `борщ по-українськи`, `котлета по-київськи`, `кава по-львівськи`, `картопля по-італійськи`.

## Пов'язані статті (Related Articles)
- `pedagogy/a1/noun-genders`
- `pedagogy/a1/adjective-agreement`
- `pedagogy/a1/present-tense-conjugation`
- `pedagogy/a2/genitive-case`
- `culture/ukrainian-national-dishes`
</wiki_context>

## Plan References

- 
- 

</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this **exact** order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Їсти і пити (To Eat and To Drink)` (~300 words)
- `## Знахідний відмінок — неживе (Accusative Inanimate)` (~300 words)
- `## Підсумок — Summary` (~300 words)

**Hard rule (#1189):** Every heading above MUST appear in your output **verbatim** as an `## H2` line. This includes the FINAL summary/transition section (`Підсумок: ...`, `Підсумок та перехід до M...`, etc.) — the writer's most common failure is silently dropping the closing section. Do NOT skip it. Do NOT renumber. Do NOT merge headings. The post-write quick-verify check will fail your build if any heading is missing, even if the prose itself is excellent.

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 20-35% Ukrainian. ⚠️ HARD GATE — the audit REJECTS modules below 20%.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — brief, 2-3 sentences per concept. No long expository paragraphs. Explain once, then show Ukrainian.
- UKRAINIAN NARRATIVE PARAGRAPHS: **REQUIRED — minimum 1 per section.** A 3-6 sentence Ukrainian paragraph demonstrating the concept in use, followed IMMEDIATELY by a `> *English translation*` blockquote. This is the PRIMARY driver of hitting the immersion target. Without these paragraphs you cannot reach 20%.
- PARADIGM TABLES: Conjugation/declension tables with all cells Ukrainian.
- EXAMPLE LISTS: Ukrainian sentences in bulleted lists (each: Ukrainian — English gloss). Minimum 5 per rule.
- DIALOGUES: Mini-dialogues in blockquotes with English gloss per line. At least 1 dialogue per module.
- PATTERN BOXES: Show transformations: `читати → читай → читайте`.
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Every section MUST contain a Ukrainian narrative paragraph (3-6 sentences, translated in blockquote) PLUS supporting tables/lists/dialogues/pattern boxes. Pure-English sections are FORBIDDEN at M35+.
Ukrainian sentences max 12 words. Mix container types.

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

### FORBIDDEN WORDS — never write these (#1189)

The following Russian words have leaked into past builds and broken modules. They are **hard-banned** — the post-write toxic-token scanner will fail your build the moment it sees one. Use the Ukrainian alternative every time, even in dialogues, even in casual prose, even when quoting a learner's mistake (use a `<!-- VERIFY -->` placeholder instead of typing the Russian form):

| Russian (FORBIDDEN) | Ukrainian (USE THIS) |
|---|---|
| хорошо | добре |
| конечно | звичайно / певна річ |
| спасибо | дякую |
| пожалуйста | будь ласка / прошу |
| ничего | нічого |
| сейчас | зараз |
| тоже | теж / також |
| здесь | тут |
| кот | кіт |
| кон | кін |

This list is enforced word-for-word by `scripts/build/quick_verify.py` (SEVERE_RUSSIANISMS). If you produce any of these tokens — even inside a quoted example, even inside a dialogue line spoken by a Russian-speaking character — the build halts immediately. There is no exception.

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
  1. **Lunch break at work — unpacking lunch boxes: Я їм бутерброд (m, sandwich) і п'ю чай (m, tea). А ти? Я їм салат (m) і п'ю каву (f, coffee). Also: яблуко (n), банан (m), вода (f), сік (m, juice).**
     Speakers: Колега 1, Колега 2
     Why: Accusative: бутерброд(m), салат(m), каву(f→acc), яблуко(n), чай(m)

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

GRAMMAR CONSTRAINTS (A1.6 — Food & Shopping, M37-M43):
Instrumental з, accusative objects, genitive quantities.

ALLOWED:
- Instrumental case with 'з' (кава з молоком)
- Accusative inanimate and animate objects
- Genitive for quantities (кілограм цукру)
- All cases from previous phases
- All present tense verbs

BANNED: Past/future tense, dative (until A1.7),
participles, passive voice, complex subordination

### Vocabulary

**Required:** їсти (to eat — irregular), пити (to drink), їм (I eat), п'ю (I drink), каву (coffee — accusative), воду (water — accusative), рибу (fish — accusative)
**Recommended:** кашу (porridge — accusative), картоплю (potato — accusative), сметану (sour cream — accusative), їсть (he/she eats), п'є (he/she drinks), їдять (they eat), п'ють (they drink)

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
## Діалоги (Dialogues) (~330 words total)
- P1 (~50 words): Introduction to the topic of food and drinks, setting the scene for daily meals (`сніданок`, `обід`, `вечеря`) and the verbs used to describe eating and drinking habits.
- P2 (~140 words): Dialogue 1 — Breakfast conversation. Two colleagues discuss their morning meals. Includes the text: "— Що ти їш на сніданок? — Я їм кашу і п'ю каву. — А Олена? — Вона їсть хліб з маслом і п'є чай. — А діти? — Вони їдять яйця і п'ють молоко." Showcases full conjugation of `їсти` and `пити` in a natural context.
- P3 (~140 words): Dialogue 2 — At lunch. A conversation about lunch orders. Includes the text: "— Що ви їсте на обід? — Ми їмо суп і салат. — А що п'єте? — Ми п'ємо воду або сік. — Я теж хочу суп. — Добре, замовляй!" Reviews `їсти` and `пити` with plural subjects and introduces the verb `хотіти` (to want).

## Їсти і пити (To Eat and To Drink) (~330 words total)
- P1 (~110 words): Introduction to the two essential, high-frequency daily verbs `їсти` (to eat) and `пити` (to drink). Note that `їсти` is irregular and does not follow the standard Group I or II patterns, while `пити` is a Group I verb with a shifting stem.
- P2 (~110 words): Present tense conjugation table and explanation for `їсти` (я їм, ти їси, він/вона їсть, ми їмо, ви їсте, вони їдять). Highlight the common L2 error of confusing `я їм` (I eat) with `він їсть` (he eats). Provide examples: `Я їм суп.` and `Вони їдять кашу.`
- P3 (~110 words): Present tense conjugation table and explanation for `пити` (я п'ю, ти п'єш, він/вона п'є, ми п'ємо, ви п'єте, вони п'ють). Emphasize the pronunciation of the apostrophe. Provide examples: `Я п'ю воду.` and `Ми п'ємо чай.`
- <!-- INJECT_ACTIVITY: fill-in-conjugation --> [fill-in, Conjugate the verbs їсти (irregular) and пити (Group I), 8 items]

## Знахідний відмінок — неживе (Accusative Inanimate) (~330 words total)
- P1 (~90 words): Introduce the concept of the direct object (`Знахідний відмінок` - Accusative case). Explain the Ukrainian school approach: the accusative answers the question "Бачу що?" (What do I see/eat/drink?). For inanimate objects like food, the question is `що?`. E.g., `Я їм (що?) хліб.` and `Я п'ю (що?) каву.`
- P2 (~80 words): Explain the rule for Masculine and Neuter inanimate nouns: NO CHANGE. They look exactly like their nominative (dictionary) forms. Provide examples to reassure learners: `хліб` → `хліб` (`Я їм хліб`), `сік` → `сік` (`Я п'ю сік`), `молоко` → `молоко` (`Я п'ю молоко`), `яйце` → `яйце` (`Я їм яйце`).
- P3 (~160 words): Explain the critical rule for Feminine nouns: the ending `-а` changes to `-у`, and `-я` changes to `-ю`. Emphasize that this is the most important accusative change for A1 learners. Provide clear contrasting examples: `кава` → `каву` (`Я п'ю каву`), `вода` → `воду` (`Я п'ю воду`), `риба` → `рибу` (`Я їм рибу`), `каша` → `кашу` (`Я їм кашу`), `картопля` → `картоплю` (`Я їм картоплю`). Point out that this rule applies to any verb taking a direct object (`їм`, `п'ю`, `хочу`).
- <!-- INJECT_ACTIVITY: fill-in-accusative-endings --> [fill-in, Form the accusative case for feminine (-а/-я → -у/-ю) and masculine/neuter (no change), 8 items]
- <!-- INJECT_ACTIVITY: group-sort-accusative --> [group-sort, Sort nouns based on how they change in the accusative case (inanimate), 8 items]
- <!-- INJECT_ACTIVITY: quiz-accusative-selection --> [quiz, Select the correct accusative form to complete the sentence, 6 items]

## Підсумок — Summary (~330 words total)
- P1 (~165 words): A concise recap of the Accusative inanimate rules. Remind learners that Masculine and Neuter nouns do not change form (`хліб`, `молоко` stay the same). Reiterate that Feminine nouns ending in `-а` change to `-у`, and those ending in `-я` change to `-ю` (`кава` → `каву`, `картопля` → `картоплю`). Mention that this applies after verbs like `їсти` and `пити`.
- P2 (~165 words): Provide a short self-check test in a bulleted Q&A format.
  * Test: Я їм ___ (`риба` → `рибу`).
  * Test: Я п'ю ___ (`вода` → `воду`).
  * Self-check: Say 3 things you eat and 3 things you drink today. Use the correct accusative form for each item.

Grand total: ~1320 words
</skeleton>

## Output Format

Write in Markdown. Use:
- `## Section Title` for main sections
- `### Subsection` for subsections within a section
- `**bold**` for Ukrainian words being taught. For **A1 and A2** levels, provide an English translation on first use (e.g. `**стіл** (table)`) because learners lack the vocabulary to infer meaning. For **B1 and above**, do NOT provide inline translations for standard vocabulary — the learner will use the module's словник (vocabulary table). You may provide ONE parenthetical English translation ONLY for highly abstract grammar/linguistic terms on first use (e.g. `**видова пара** (aspectual pair)`).
- Tables for paradigms (conjugation, declension)
- `:::tip` / `:::caution` / `:::note` for callout boxes
- `<!-- INJECT_ACTIVITY: {id} -->` for exercise placement (markers only — do NOT write exercise content)

Do NOT write MDX component syntax, JSON, or DSL exercise blocks (:::quiz, etc.). Plain Markdown with injection markers.

---

## MANDATORY FINAL CHECKLIST (#1189)

Before you finish writing, verify the prose against this checklist. Failing any item will fail the build.

### Section headings (verbatim)

Every heading from "Section Structure" above MUST appear as an `## H2` in your output, in order, **including the closing `Підсумок:` / `Підсумок та перехід до M...` summary**. The single most common writer failure across the B1 build has been silently dropping the final summary section. Re-read your output before stopping. If the last section in the plan is missing, write it now.

### Required vocabulary (every word must appear)

You MUST use **every word** from the list below at least once in the prose, in a natural sentence with bold + English translation. Abstract grammatical metalanguage (видова пара, дієвідміна, особове закінчення, прагматика, діагностика, дієвідмінювання, зворотний, двовидовий, одновидовий, неозначено-кількісний, etc.) is the most frequently dropped category — actively find homes for those words even if it means adding a sentence that defines them.

- [ ] їсти (to eat — irregular)
- [ ] пити (to drink)
- [ ] їм (I eat)
- [ ] п'ю (I drink)
- [ ] каву (coffee — accusative)
- [ ] воду (water — accusative)
- [ ] рибу (fish — accusative)

### Forbidden words (never produce)

Do not write any of these even once. Even in dialogues. Even in quoted examples. Even when illustrating a learner's mistake (use `<!-- VERIFY -->` instead). The post-write toxic-token scanner will fail the build immediately:

❌ хорошо ❌ конечно ❌ спасибо ❌ пожалуйста ❌ ничего ❌ сейчас ❌ тоже ❌ здесь ❌ кот ❌ кон

Use: добре · звичайно · дякую · будь ласка · нічого · зараз · теж · тут · кіт · кін

### Level-specific immersion check

The level-appropriate immersion rule was already injected at the top of
this prompt as `IMMERSION RULE`. Re-read it now BEFORE you stop writing.
If your level's rule contains a CHECKLIST block, walk through every item.
If it doesn't, just verify your output matches the LANGUAGE ROLES and
TARGET stated in that block.

This used to hard-code a B1+ checklist that confused A1/A2 models (where
translation blockquotes are REQUIRED at A1 and ALLOWED at A2-early).
The single source of truth is now
`scripts/pipeline/config_tables.py:IMMERSION_RULES`.

---

Begin writing now. Start with the first section heading.
