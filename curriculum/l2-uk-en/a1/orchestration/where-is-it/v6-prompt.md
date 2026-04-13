

---

## Your Writing Identity

**You are: Lead Ukrainian Instructor.** Your persona is *The Patient Guide*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **29: Where Is It?** (A1, A1.5 [Places]).

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

1. **IMMERSION TARGET: 15-30% Ukrainian** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if immersion is outside this range. For A1 early modules, the learner cannot read Cyrillic — English must dominate. For A2+, Ukrainian must carry a significant share — add Ukrainian Reading Practice blocks, dialogues, and example paragraphs to reach the target. Too little Ukrainian fails audit just as much as too much.
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
module: a1-029
level: A1
sequence: 29
slug: where-is-it
version: '1.1'
title: Where Is It?
subtitle: В школі, на роботі — the locative case
focus: grammar
pedagogy: PPP
phase: A1.5 [Places]
word_target: 1200
objectives:
- Use в/у and на + locative to answer Де? (Where?)
- Form basic locative endings for familiar nouns
- Distinguish в (inside) from на (on/at) with place vocabulary
- Use the Grade 4 helper word method: М. (на, у) — "на/у кому? на/у чому?"
dialogue_situations:
- setting: 'First week in a new city — asking a neighbor where to find: аптека (f,
    pharmacy), банк (m, bank), пошта (f, post office), кафе (n, café), лікарня (f,
    hospital), парк (m, park). В аптеці, на пошті, у банку.'
  speakers:
  - Новий мешканець (newcomer)
  - Сусід (neighbor)
  motivation: В/на + locative with аптека(f), банк(m), пошта(f), кафе(n)
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Where is everyone? (ULP Ep17 pattern): — Де Олена? — Вона в школі.
    — А Тарас? — Він на роботі. — А діти? — Вони в парку. — А кішка? — Вона на дивані!
    Locative case emerges naturally from answering ''Де?'''
  - 'Dialogue 2 — Describing locations: — Де ти живеш? — Я живу в Києві, на вулиці
    Хрещатик. — А де ти працюєш? — В офісі, на другому поверсі. City + street + building
    locations.'
- section: Місцевий відмінок (The Locative Case)
  words: 300
  points:
  - 'Grade 4 case system: helper word method (Захарійчук Gr4 p.74): М. = місцевий
    відмінок: на/у кому? на/у чому? The locative ALWAYS needs a preposition — в/у
    or на. В/у = inside: в школі, у банку, в магазині, у лікарні. На = on/at: на роботі,
    на вулиці, на площі, на уроці.'
  - 'Basic locative endings (most common patterns): Masculine: -і or -у — в парку,
    у банку, в офісі, на уроці. Feminine: -і — в школі, на роботі, у лікарні, на вулиці.
    Neuter: -і — в місті, на морі. Note: endings depend on the noun''s declension
    — learn the common places as fixed phrases for now.'
- section: В чи на? (В or На?)
  words: 300
  points:
  - 'General guide: В/у = enclosed spaces: в школі, в магазині, у банку, в лікарні,
    в кафе. На = open spaces, surfaces, events: на вулиці, на площі, на роботі, на
    концерті. Some are conventional: на пошті (not в пошті), на вокзалі (not в вокзалі).
    Learn each place with its preposition — like English ''at school'' vs ''in the
    office''.'
  - 'Country/city rule: В/у + country/city: в Україні, у Києві, у Львові, в Одесі.
    На + some special cases: на Хрещатику (on Khreshchatyk street). Remember: NEVER
    ''на Україні'' — it''s ЗАВЖДИ ''в Україні''. This is not just grammar — it''s
    a matter of respect and sovereignty.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Locative case = where something IS (static location). Де? → в/у + locative (inside)
    or на + locative (on/at). Helper word: М. (на, у) — на/у кому? на/у чому? Common
    places: в школі, на роботі, у банку, в парку, на вулиці. Self-check: Where are
    you right now? Where do you work? Where do you live?'
vocabulary_hints:
  required:
  - школа → в школі (school)
  - робота → на роботі (work)
  - банк → у банку (bank)
  - магазин → у/в магазині (shop)
  - вулиця → на вулиці (street)
  - місто → у/в місті (city)
  recommended:
  - парк → у/в парку (park)
  - лікарня → у/в лікарні (hospital)
  - кафе → у/в кафе (café — indeclinable)
  - площа → на площі (square)
  - вокзал → на вокзалі (train station)
  - пошта → на пошті (post office)
activity_hints:
- type: quiz
  focus: В or на? Choose the correct preposition for each place.
  items: 10
- type: fill-in
  focus: 'Answer Де?: Олена ___ (школа). Тарас ___ (робота).'
  items: 8
- type: match-up
  focus: 'Match nominative to locative: школа ↔ в школі'
  items: 8
- type: quiz
  focus: Where is it? Choose the correct locative form.
  items: 6
connects_to:
- a1-030 (My City)
prerequisites:
- a1-028 (Euphony)
grammar:
- 'Locative case: в/у + М.в. (inside), на + М.в. (on/at)'
- 'Helper word method: М. (на, у) — на/у кому? на/у чому?'
- 'Basic locative endings: -і (most common), -у (masculine some)'
- В Україні (never на Україні)
register: розмовний
references:
- title: Захарійчук Grade 4, p.74
  notes: 'Case system table: М.в. = на/у кому? на/у чому?'
- title: ULP Season 1, Episode 17
  url: https://www.ukrainianlessons.com/episode17/
  notes: Locative case for places — where things are.

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
- Confirmed: школа, робота, банк, магазин, вулиця, місто, парк, лікарня, кафе, площа, вокзал, пошта, школі, роботі, банку, магазині, вулиці, місті, парку, лікарні, площі, вокзалі, пошті
- Not found: 

## Grammar Rules
- Чергування У/В: Правопис §23 — Щоб уникнути збігу букв на позначення приголосних звуків... вживають прийменник "у". Щоб уникнути збігу букв, що передають голосні... вживають прийменник "в".

## Calque Warnings
- по вулиці: Calque — на вулиці (Антоненко-Давидович: неправильно "живу по вулиці", треба "живу на вулиці")
- на вулиці: OK — на вулиці
- на Україні: Calque — в Україні (згідно з інструкціями плану, питання суверенітету)
- на роботі: OK — на роботі
- в місті: OK — в місті

## CEFR Check
- школа: A1 — OK
- робота: A1 — OK
- банк: A1 — OK
- магазин: A1 — OK
- вулиця: A1 — OK
- місто: A1 — OK
- парк: A1 — OK
- лікарня: A1 — OK
- кафе: A1 — OK
- площа: A1 — OK
- вокзал: A1 — OK
- пошта: A1 — OK
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
# Knowledge Packet: Where Is It?
**Module:** where-is-it | **Track:** A1

<wiki_context>
## Compiled Wiki Knowledge

The following articles from the project wiki provide compiled knowledge relevant to this module. Use them as authoritative context — they were compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).

### Вікі: pedagogy/a1/where-is-it.md

# Педагогіка A1: Where Is It



## Методичний підхід (Methodological Approach)

Teaching A1 learners to express location centers on the **Місцевий відмінок (Locative case)**. The pedagogical approach, drawn from Ukrainian primary school textbooks and L2 materials, prioritizes communicative function over abstract grammatical rules.

The core concept is that the Locative case answers the question **Де?** (Where?) and *always* requires a preposition, most commonly `в` (`у`) or `на` (Source 21, 14). The initial teaching strategy is pattern-based, not rule-based. Learners are exposed to high-frequency chunks and frame sentences.

1.  **Start with Function:** Introduce the question `Де ти?` (Where are you?) and provide simple, uninflected answers like `Я вдома` (I'm at home) (Source 1). This establishes the communicative goal immediately.
2.  **Introduce `в / у` for Enclosed Spaces:** Begin with easily recognizable places. Exercises often involve matching a person/profession to their workplace, like `Лікар працює в лікарні` (The doctor works in the hospital) (Source 40). This builds a strong association between the preposition `в` and being "inside" a location.
3.  **Introduce `на` for Open Spaces & Concepts:** Contrast `в` with `на`. `На` is used for open areas (`на вулиці`, `на площі`), surfaces, events (`на концерті`), and some institutional concepts (`на пошті`, `на роботі`) (Source 8, 7). This distinction is a key learning point that differs significantly from English.
4.  **Pattern Recognition of Endings:** Instead of presenting declension tables upfront, introduce case endings through examples. Start with the most common ending (`-і` for feminine nouns like `Україна` -> `в Україні`), then introduce masculine/neuter (`Київ` -> `у Києві`), and finally the masculine exceptions (`парк` -> `у парку`) (Sources 7, 34, 1). Consonant mutation (`рука` -> `в руці`) is taught as a sound change rule connected to the `-і` ending (Source 43).
5.  **Capitalization as a Writing Skill:** Ukrainian textbooks for early grades explicitly teach that names of countries, cities, villages, and streets are written with a capital letter (Джерело: `2-klas-ukrmova-vashulenko-2019-1_s0058`, `2-klas-ukrmova-bolshakova-2019-2_s0036`). This is presented as a fundamental writing convention.

The overall method is to move from whole communicative phrases to recognizing patterns, and only then to explicit (but simplified) grammatical explanation.

## Послідовність введення (Introduction Sequence)

To avoid cognitive overload, concepts should be introduced in a logical, scaffolded sequence.

1.  **Step 1: The Question `Де?` and Preposition `в/у`**
    *   Begin with the question `Де?` (Where?).
    *   Introduce the preposition `в` (or its euphonic variant `у`) with simple, high-frequency, enclosed nouns that are often cognates for English speakers. At this stage, use masculine nouns that take the `-у` ending to avoid teaching case endings immediately.
    *   **Examples:** `Я в парку.` (I am in the park.), `Ми в банку.` (We are at the bank.) (Source 1, 12). The key takeaway is `в + місце` (in + place).

2.  **Step 2: The Preposition `на` for Open Spaces and Concepts**
    *   Introduce `на` to contrast with `в/у`. Teach it with open spaces and common institutional concepts.
    *   **Examples:** `Я на вулиці.` (I am on the street.), `Він на роботі.` (He is at work.), `Вони на ринку.` (They are at the market.) (Source 8).

3.  **Step 3: The Locative `-і` Ending (Feminine Nouns)**
    *   Introduce the most common Locative ending: `-і`.
    *   Start with feminine nouns ending in `-а`. `школа → в школі`, `кав'ярня → в кав'ярні`.
    *   Immediately teach the associated consonant mutation `г, к, х → з, ц, с` before the `-і` ending. This is a phonological rule, not an exception.
    *   **Examples:** `рука → в руці`, `нога → на нозі`, `книга → в книзі`, `муха → на мусі` (Source 43). `площа -> на площі` (Source 9).

4.  **Step 4: The Locative `-і` Ending (Masculine & Neuter Nouns)**
    *   Introduce the `-і` ending for most masculine and neuter nouns.
    *   **Examples:** `Київ → в Києві` (Source 7), `Львів → у Львові` (Source 1), `місто → у місті` (Source 7), `море → на морі` (Source 1).

5.  **Step 5: Masculine `-у/-ю` Ending Revisited**
    *   Solidify the list of common masculine exceptions that take the `-у`/`-ю` ending. Present these as a group to be memorized for A1.
    *   **Examples:** `парк → в парку`, `банк → в банку`, `будинок → у будинку`, `аеропорт -> в аеропорту`, `ліс -> у лісі` (Source 1, 12, 32).

6.  **Step 6: Plural Locative (`-ах/-ях`)**
    *   Introduce the plural ending for all genders.
    *   **Examples:** `Карпати → в Карпатах` (Source 1), `Чернівці → у Чернівцях` (Source 1), `гори → в горах` (Source 1).

## Типові помилки L2 (Common L2 Errors)

English-speaking learners often make predictable errors when learning to express location. The curriculum should proactively address these.

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| `Я в місто Київ.` | `Я в місті Києві.` | English doesn't decline nouns for location, so learners often forget to apply the Locative case to both the general noun (`місто`) and the proper noun (`Київ`). The correct Ukrainian structure requires both to be in the Locative case (Джерело: `11-klas-ukrajinska-mova-avramenko-2019_s0082`). |
| `Я працюю в роботі.` | `Я працюю на роботі.` | This is a direct translation of the English preposition "in". Ukrainian uses `на роботі` for the abstract concept of being "at work". This is a fixed expression that must be memorized (Джерело: `ext-ulp_youtube-284`). |
| `Я в книгі.` | `Я в книзі.` | Learners often master the `-і` ending but forget the mandatory consonant mutation for feminine nouns ending in `-г`, `-к`, `-х`. The change `г → з` is a fundamental phonetic rule of the language (Джерело: `4-klas-ukrayinska-mova-ponomarova-2021-1_s0046`). |
| `Ми в паркі.` | `Ми в парку.` | This is an overgeneralization of the `-і` ending. Learners apply the most common Locative ending to masculine nouns that are exceptions. A curated list of common nouns taking `-у` should be drilled early (Джерело: `ext-ulp_youtube-237`). |
| `Я живу вулиця Шевченка.` | `Я живу на вулиці Шевченка.` | English can omit the preposition in some contexts ("I live Шевченка Street"). Ukrainian's Locative case requires a preposition (`на` for streets) to signify location. Omitting it changes the meaning or makes the sentence ungrammatical (Source 21, 6). |
| `Театр є в площа.` | `Театр є на площі.` | Learners mix up `в` and `на`. The rule is generally `в` for enclosed spaces and `на` for open spaces/surfaces. A square (`площа`) is an open space, so it takes `на` and the Locative ending `-і` (Source 9, 33). |

## Деколонізаційні застереження (Decolonization Notes)

Teaching Ukrainian requires a conscious effort to avoid Russification and present the language on its own terms.

*   **Orthography and Pronunciation:** The primary example is the capital's name. It must be taught as **`Київ` (Kyiv)**, not the Russian-derived `Киев` (Kiev). This is not just a spelling preference but a matter of national identity and linguistic accuracy (Source 7). All place names should use the official Ukrainian romanization standard.
*   **Avoid Russian Analogies:** Never teach Ukrainian concepts as "like the Russian X". For example, the distinction between `в` and `на` has its own logic and history in Ukrainian and does not perfectly map to Russian usage. Learners must build a Ukrainian mental model from scratch, not by adapting a Russian one.
*   **Historical Context of Place Names:** When discussing locations, use Ukrainian-centric historical narratives. For example, the history of industrialization in Donbas should include figures like the Ukrainian entrepreneur Oleksiy Alchevsky, challenging the Russian myth that the region's industry was a purely Russian creation (Джерело: `ext-komik_istoryk-72`).
*   **Vocabulary:** Be mindful of semantic false friends with Russian. While many words are shared Slavic roots, their usage or frequency can differ. The curriculum must be based on contemporary Ukrainian sources, like the provided podcasts and textbooks, not on bilingual dictionaries that may contain outdated or Russian-influenced vocabulary. The goal is to teach living, natural Ukrainian.

## Словниковий мінімум (Vocabulary Boundaries)

This vocabulary is essential for forming basic sentences about location at the A1 level.

#### Іменники (Nouns)
*   **★★★ (Essential):** `місто` (city), `село` (village), `вулиця` (street), `площа` (square), `парк` (park), `дім / будинок` (house/building), `квартира` (apartment), `кімната` (room), `школа` (school), `робота` (work), `магазин` (store), `кафе` (cafe), `ресторан` (restaurant), `банк` (bank), `пошта` (post office), `ринок` (market), `Україна` (Ukraine), `Київ` (Kyiv). (Sources 6, 7, 8, 13, 40, 44)
*   **★★ (Useful):** `музей` (museum), `театр` (theater), `річка` (river), `море` (sea), `гори` (mountains), `ліс` (forest), `офіс` (office), `центр` (center). (Sources 1, 13, 27)
*   **★ (Can wait):** `університет` (university), `бібліотека` (library), `лікарня` (hospital), `вокзал` (train station), `аеропорт` (airport). (Source 40, 41, 42)

#### Дієслова (Verbs)
*   `бути` (to be), `жити` (to live), `працювати` (to work), `гуляти` (to walk/stroll), `сидіти` (to sit), `їсти` (to eat), `бувати` (to be/visit). (Source 7, 5)

#### Прислівники (Adverbs)
*   `тут` (here), `там` (there), `вдома` (at home), `далеко` (far), `близько` (near).

## Приклади з підручників (Textbook Examples)

The writer should model activities on these proven formats from Ukrainian textbooks.

1.  **Fill-in-the-Blank Address (Source 30)**
    *   **Concept:** Practice writing a personal address, reinforcing the structure and capitalization of place names.
    *   **Prompt:** `Напиши свою адресу за планом.`
        1.  `Як називається країна, у якій ти живеш?`
        2.  `Як називається місто, у якому ти живеш?`
        3.  `Як називається вулиця, на якій ти живеш?`
        4.  `Номер будинку, номер квартири.`

2.  **Sentence Completion with Places (Source 6)**
    *   **Concept:** Practice using place names in the correct form within a sentence structure.
    *   **Prompt:** `Додайте потрібні назви і запишіть.`
        *   `Наше місто (село) називається _____.`
        *   `Центральна вулиця в місті (селі) — _____.`
        *   `Наша школа розташована на вулиці _____.`
        *   `Поблизу міста (села) протікає річка _____.`

3.  **Tourist & Local Dialogue (Source 20)**
    *   **Concept:** A communicative role-playing exercise to practice asking for and giving locations. This is highly effective.
    *   **Setup:** Provide a simple map of a fictional town with key locations labeled (парк, банк, музей, театр, кав'ярня).
    *   **Prompt:** `Один з вас турист, а інший — мешканець міста. Турист не знає, що де розташовано. Поясніть йому.`
    *   **Example Dialogue:**
        *   Турист: `— Вибачте, де розташований театр?`
        *   Мешканець: `— Театр розташований на вулиці Мукачівській. Йдіть прямо і поверніть ліворуч. Там побачите театр.`

4.  **Matching People to Workplaces (Source 40)**
    *   **Concept:** Reinforce vocabulary for places and professions, and the `в/у + Locative` structure.
    *   **Setup:** Create two columns: one with professions (`лікар`, `вчитель`, `продавець`) and one with workplaces (`лікарня`, `школа`, `магазин`).
    *   **Prompt:** `З'єднайте пари і складіть речення за зразком.`
    *   **Example:** `Зразок: Лікар працює в лікарні.`

## Пов'язані статті (Related Articles)

*   `pedagogy/a1/what-is-this`
*   `grammar/cases/locative`
*   `grammar/prepositions-of-place`
*   `vocabulary/a1/places-in-a-city`

---

### Вікі: pedagogy/a1/what-is-it-like.md

# Педагогіка A1: What Is It Like



## Методичний підхід (Methodological Approach)

The core of teaching descriptive language at the A1 level is to establish the **прикме́тник (adjective)** as a word that answers the questions **яки́й? яка́? яке́? які́?** (what kind of?) and describes an **озна́ку предме́та (an attribute of an object)** (Source `3-klas-ukrainska-mova-vashulenko-2020-1_s0120`, Source `2-klas-ukrmova-kravcova-2019-1_s0075`). The native Ukrainian pedagogy, evident in early grade textbooks, avoids dense grammatical tables. Instead, it builds an intuitive understanding of agreement through question-and-answer pairings.

The primary method is to always present adjectives in tight connection with the noun they modify. Exercises in Grade 2 and 3 textbooks consistently model this relationship (Джерело: `2-klas-ukrmova-kravcova-2019-1_s0081`, `3-klas-ukrainska-mova-vashulenko-2020-1_s0123`). For example, a teacher would ask, "Огірок (який?)" and expect the answer "зелений" (Source `2-klas-ukrmova-kravcova-2019-1_s0075`). This constant questioning reinforces the concept of gender and number agreement organically before the formal case system is introduced.

The initial focus is on **які́сні прикме́тники (qualitative adjectives)**—those describing a quality that can exist in degrees (e.g., big, small, good, bad)—as they are the most frequent and intuitive for beginners (Джерело: `6-klas-ukrmova-zabolotnyi-2020_s0135`). The concept of comparative (`вищий ступінь`) and superlative (`найвищий ступінь`) is introduced with only the most common, irregular forms (`кращий`, `більший`) at first, mirroring how they appear in natural A1-level conversation (Джерело: `ext-ulp_youtube-199`).

## Послідовність введення (Introduction Sequence)

The introduction of descriptive language must be systematic and build from the concrete to the abstract.

1.  **Step 1: Core Concept & Basic Vocabulary.** Introduce the `прикметник` as a "describing word." Start with a small set of high-frequency, concrete adjectives related to size, quality, and color.
    *   **Size:** `вели́кий` (big), `мали́й` (small) (Source `ext-ulp_youtube-251`)
    *   **Quality:** `га́рний` (good/nice), `пога́ний` (bad), `нови́й` (new), `стари́й` (old) (Source `5-klas-ukrmova-uhor-2022-1_s0034`)
    *   **Color:** `бі́лий` (white), `чо́рний` (black), `черво́ний` (red), `си́ній` (blue) (Джерело: `4-klas-ukrmova-zaharijchuk_s0107`)

2.  **Step 2: Nominative Case Agreement (Gender & Number).** This is the most critical A1 skill. Teach the pattern of endings `-ий, -а, -е, -і` through examples, not rules.
    *   `гарний стіл` (masculine)
    *   `гарна ручка` (feminine)
    *   `гарне вікно` (neuter)
    *   `гарні книги` (plural)
    *   This pattern is consistently drilled in early-grade textbooks (Джерело: `5-klas-ukrmova-uhor-2022-1_s0034`).

3.  **Step 3: Expanding Vocabulary & Simple Phrases.** Introduce adjectives for weather, feelings, and taste. Practice them in simple phrases like `Мені подо́бається...` or `Це...`.
    *   **Weather/Temp:** `холо́дний` (cold), `те́плий` (warm)
    *   **Feelings:** `весе́лий` (happy), `сумни́й` (sad)
    *   **Taste:** `смачни́й` (tasty), `соло́дкий` (sweet) (Source `6-klas-ukrmova-avramenko-2023_s0154`)

4.  **Step 4: Introduction to Simple Comparatives.** Introduce only the most essential, suppletive (irregular) forms that are unavoidable in A1 conversation.
    *   `гарний → кра́щий` (good → better)
    *   `поганий → гі́рший` (bad → worse)
    *   `великий → бі́льший` (big → bigger)
    *   `малий → ме́нший` (small → smaller)
    *   This is explicitly supported by multiple grammar guides (Джерело: `6-klas-ukrmova-litvinova-2023_s0206`, `6-klas-ukrmova-golub-2023_s0134`). The form `більш/менш + adjective` should be delayed until A2, as it is a more formal, "bookish" construction (Джерело: `11-klas-ukrajinska-mova-glazova-2019_s0022`).

## Типові помилки L2 (Common L2 Errors)

English-speaking learners often struggle with agreement and transfer habits from English.

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| `це *гарний* книга` | `це *гарна* книга` | **Gender Agreement Failure.** English adjectives are invariable. Learners must be drilled to match the adjective's ending to the noun's gender. The question `книга (яка?)` helps correct this (Джерело: `5-klas-ukrmova-uhor-2022-1_s0034`). |
| `мій *новий* друзі` | `мої *нові* друзі` | **Number Agreement Failure.** The learner forgets to make the adjective plural to match the plural noun. The question `друзі (які?)` reinforces the correct form (Джерело: `3-klas-ukrainska-mova-vashulenko-2020-1_s0120`). |
| `*самий кращий* день` | `*найкращий* день` | **Russian Calque.** This is a direct translation of the Russian superlative construction (`самый лучший`). Ukrainian uses the prefix `най-`. This error is a critical one to correct, as it is a hallmark of Surzhyk. Textbooks for natives explicitly forbid using `самий` (Джерело: `6-klas-ukrmova-betsa-2023_s0121`, `6-klas-ukrmova-golub-2023_s0134`). |
| `Вона співає *гарний*.` | `Вона співає *гарно*.` | **Adjective/Adverb Confusion.** In English, the distinction between "good" (adjective) and "well" (adverb) can be fluid. Ukrainian maintains a strict distinction between `гарний` (describes a noun) and `гарно` (describes a verb). This must be taught explicitly (Джерело: `4-klas-ukrayinska-mova-ponomarova-2021-1_s0118`). |
| `Він *великий* за мене.` | `Він *більший* за мене.` | **Using Base Adjective for Comparison.** English uses "bigger than," not "big than." The learner attempts a literal translation without using the comparative form (`вищий ступінь`). It's crucial to teach that comparisons require a special form (`більший`, `кращий`, etc.) (Джерело: `11-klas-ukrajinska-mova-glazova-2019_s0023`). |

## Деколонізаційні застереження (Decolonization Notes)

Teaching Ukrainian on its own terms from day one is non-negotiable.

1.  **NO Russian Analogies:** Never teach Ukrainian phonetics or letters by comparing them to Russian (e.g., "Ukrainian `и` is like Russian `ы`"). Teach the sounds of Ukrainian independently, using native audio and phonetic descriptions relevant to an English speaker's palate. The learner must build a new, separate phonetic system for Ukrainian.

2.  **Color Terminology:** Be precise with color names that are false friends with Russian.
    *   `си́ній` in Ukrainian is a deep, dark blue. The lighter, sky-blue color is `блаки́тний` or `голуби́й`. Historical linguistic sources show that `синій` historically meant "dark" or even "black," which explains its modern usage for dark shades (Джерело: `ext-istoria_movy-78`). Confusing it with Russian `синий` (which covers a broader blue spectrum) leads to unnatural phrasing.
    *   `черво́ний` is the standard word for "red." The word `кра́сний` is archaic/poetic for "beautiful" and should not be taught as "red," which is its primary meaning in Russian.

3.  **Source of Vocabulary:** When discussing shared Slavic words (e.g., `стодола`, `груба`), present them as part of a shared heritage or as Ukrainian words that influenced neighboring languages like Romanian, rather than defaulting to a narrative of Russian influence (Джерело: `ext-istoria_movy-10`). This correctly positions Ukrainian as a historically significant and independent language.

## Словниковий мінімум (Vocabulary Boundaries)

This vocabulary is foundational for A1 learners to describe their immediate world.

**Прикметники (Adjectives):**
*   ★★★ (Essential): `га́рний` (good, nice), `пога́ний` (bad), `вели́кий` (big), `мали́й`/`мале́нький` (small), `нови́й` (new), `стари́й` (old), `добрий` (kind), `ціка́вий` (interesting), `холо́дний` (cold), `те́плий` (warm). Colors: `бі́лий`, `чо́рний`, `черво́ний`, `си́ній`, `зеле́ний`, `жо́втий`.
*   ★★ (Useful): `смачни́й` (tasty), `швидки́й` (fast), `пові́льний` (slow), `важки́й` (heavy, difficult), `легки́й` (light, easy), `деше́вий` (cheap), `дороги́й` (expensive), `весе́лий` (cheerful), `сумни́й` (sad).
*   ★ (Can wait): `чи́стий` (clean), `брудни́й` (dirty), `висо́кий` (tall/high), `низьки́й` (short/low), `широ́кий` (wide), `вузьки́й` (narrow).

**Іменники (Nouns to pair with):**
*   ★★★: `день`, `дім`, `стіл`, `друг`; `кни́га`, `робо́та`, `вода́`, `їжа`; `вікно́`, `сло́во`, `мі́сто`; `лю́ди`, `ді́ти`, `о́чі`.

**Дієслова (Verbs to use in sentences):**
*   ★★★: `бу́ти` (to be), `ма́ти` (to have), `хоті́ти` (to want), `люби́ти` (to love), `ба́чити` (to see), `зна́ти` (to know), `подо́батися` (to like).

## Приклади з підручників (Textbook Examples)

These exercises from Ukrainian textbooks are the gold standard for A1 activities. They are simple, repetitive, and build intuition for agreement.

1.  **Question-based Completion (Source: `2-klas-ukrmova-kravcova-2019-1_s0075`)**
    *   **Format:** The student is given a noun and a question word to prompt the correct adjective form.
    *   **Example:**
        *   `Огірок (який?) ______________`
        *   `Диня (яка?) ______________`
        *   `Сонце (яке?) ______________`
        *   `Кабачки (які?) ______________`
    *   **Pedagogical Value:** Directly links the noun's gender/number to the adjective's ending through the question word.

2.  **Identifying Nouns by Attribute (Source: `2-klas-ukrmova-kravcova-2019-1_s0075`)**
    *   **Format:** The student fills in the blank with a noun that matches the given adjective.
    *   **Example:**
        *   `Колючий ...` (їжак)
        *   `Великий ...` (ведмідь)
        *   `Хитра ...` (лисиця)
        *   `Пухнасте ...` (курчатко)
    *   **Pedagogical Value:** Reinforces adjective-noun collocations and vocabulary.

3.  **Pattern Drill for Agreement (Source: `5-klas-ukrmova-uhor-2022-1_s0034`)**
    *   **Format:** The student applies a single adjective to a list of nouns with different genders and numbers.
    *   **Example:** `(гарний) шарф — дівчина — озеро — квіти.`
    *   **Expected Output:** `гарний шарф, гарна дівчина, гарне озеро, гарні квіти.`
    *   **Pedagogical Value:** Isolates and drills the core A1 skill of changing adjective endings to match the noun.

4.  **Fill-in-the-blank from a Word Bank (Source: `4-klas-ukrmova-zaharijchuk_s0089`)**
    *   **Format:** Students complete a short poem or text by choosing appropriate adjectives from a provided list (`Довідка`).
    *   **Example:**
        ```
        І цей ... та ... запах
        Прийшов до мене уві сні.
        А ранком кіт приніс на лапах
        ... ... перший сніг!
        Довідка: п’янку, тонкий, ніжний, пухнастий, білий.
        ```
    *   **Pedagogical Value:** Combines reading comprehension with adjective agreement in a meaningful context.

## Пов'язані статті (Related Articles)
- `pedagogy/a1/noun-gender`
- `pedagogy/a1/nominative-case`
- `pedagogy/a1/asking-questions`
- `grammar/adjectives/comparative-superlative`
- `decolonization/surzhyk-and-russianisms`
</wiki_context>

## Plan References

- 
- 

</knowledge_packet>

---

## Section Structure

Write these sections as H2 headings, in this **exact** order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Місцевий відмінок (The Locative Case)` (~300 words)
- `## В чи на? (В or На?)` (~300 words)
- `## Підсумок — Summary` (~300 words)

**Hard rule (#1189):** Every heading above MUST appear in your output **verbatim** as an `## H2` line. This includes the FINAL summary/transition section (`Підсумок: ...`, `Підсумок та перехід до M...`, etc.) — the writer's most common failure is silently dropping the closing section. Do NOT skip it. Do NOT renumber. Do NOT merge headings. The post-write quick-verify check will fail your build if any heading is missing, even if the prose itself is excellent.

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 15-30% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — explain the grammar concept once, clearly.
- EXAMPLES: Ukrainian sentences in bulleted lists (each line: Ukrainian — English gloss). Max 2-4 per rule.
- TABLES: Paradigm tables, case endings, vocabulary groups — all cells Ukrainian.
- PATTERN BOXES: Show transformations: `книга → книгу` (nominative → accusative).
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences go in tables, bulleted lists, or pattern boxes.
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
  1. **First week in a new city — asking a neighbor where to find: аптека (f, pharmacy), банк (m, bank), пошта (f, post office), кафе (n, café), лікарня (f, hospital), парк (m, park). В аптеці, на пошті, у банку.**
     Speakers: Новий мешканець (newcomer), Сусід (neighbor)
     Why: В/на + locative with аптека(f), банк(m), пошта(f), кафе(n)

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

**Required:** школа → в школі (school), робота → на роботі (work), банк → у банку (bank), магазин → у/в магазині (shop), вулиця → на вулиці (street), місто → у/в місті (city)
**Recommended:** парк → у/в парку (park), лікарня → у/в лікарні (hospital), кафе → у/в кафе (café — indeclinable), площа → на площі (square), вокзал → на вокзалі (train station), пошта → на пошті (post office)

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
- P1 (~50 words): Introduce the module's scenario: a newcomer is settling into a city and asking their neighbor where essential places are. Establish the core question "Де?" (Where?).
- P2 (~120 words): Dialogue 1 — Where is everyone? (ULP Ep17 pattern). A rapid-fire exchange about locations: — Де Олена? — Вона в школі. — А Тарас? — Він на роботі. — А діти? — Вони в парку. — А кішка? — Вона на дивані!
- P3 (~60 words): Break down Dialogue 1. Point out that answering "Де?" naturally leads to the locative case, using phrases like "в школі" and "на роботі", which combine a preposition (в/на) with a changed noun ending.
- P4 (~100 words): Dialogue 2 — Describing locations. A conversation about living and working: — Де ти живеш? — Я живу в Києві, на вулиці Хрещатик. — А де ти працюєш? — В офісі, на другому поверсі. Emphasize city, street, and building locations.

## Місцевий відмінок (The Locative Case) (~350 words total)
- P1 (~90 words): Introduce the Grade 4 helper word method (Захарійчук Gr4 p.74): М. = місцевий відмінок: на/у кому? на/у чому? Explain that the locative case is used for static location (where something IS) and ALWAYS needs a preposition, most commonly в/у or на.
- P2 (~100 words): Explain the most common locative ending: -і. Show how it applies to feminine nouns (школа → в школі, лікарня → у лікарні, вулиця → на вулиці) and neuter nouns (місто → у місті, море → на морі).
- P3 (~90 words): Explain masculine locative endings. While some take -і (офіс → в офісі, урок → на уроці), many common places take -у. Provide essential examples to memorize: парк → у парку, банк → у банку.
- P4 (~70 words): Emphasize learning these places as fixed phrases. Instead of overthinking the declension rules right now, learners should memorize the chunks (e.g., "в школі", "на роботі", "у банку") just like English "at school" vs "in the office".
- <!-- INJECT_ACTIVITY: match-up-nominative-locative --> [match-up, Match nominative to locative: школа ↔ в школі, 8 items]
- <!-- INJECT_ACTIVITY: fill-in-answer-where --> [fill-in, Answer Де?: Олена ___ (школа). Тарас ___ (робота)., 8 items]

## В чи на? (В or На?) (~340 words total)
- P1 (~90 words): Explain the general rule for "В/у". It is used for enclosed spaces or being "inside" a structure. Provide clear examples: в школі, в магазині, у банку, в лікарні, в кафе (note that кафе is indeclinable).
- P2 (~100 words): Explain the general rule for "На". It is used for open spaces, surfaces, or events. Provide examples: на вулиці, на площі, на роботі, на концерті. Highlight conventional exceptions that must be memorized: на пошті (not в пошті), на вокзалі (not в вокзалі).
- P3 (~90 words): Explain the Country/City rule. Countries and cities ALWAYS take "В/у": в Україні, у Києві, у Львові, в Одесі. Contrast this with streets and squares, which take "На": на Хрещатику, на площі.
- P4 (~60 words): Address the critical decolonization note: NEVER say "на Україні". Explain that it is ЗАВЖДИ "в Україні", and this distinction is not just a grammatical rule, but a matter of respect and national sovereignty.
- <!-- INJECT_ACTIVITY: quiz-v-or-na --> [quiz, В or на? Choose the correct preposition for each place., 10 items]
- <!-- INJECT_ACTIVITY: quiz-where-is-it --> [quiz, Where is it? Choose the correct locative form., 6 items]

## Підсумок — Summary (~300 words total)
- P1 (~100 words): Recap that the Locative case is used for static location (where something IS). Answering "Де?" requires "в/у + locative" (inside) or "на + locative" (on/at). Reiterate the helper word: М. (на, у) — на/у кому? на/у чому?
- P2 (~100 words): Summarize the core vocabulary chunks to memorize: в школі, на роботі, у банку, в парку, на вулиці. Remind the learner about the importance of "в Україні".
- P3 (~100 words): Self-check questions. Provide a bulleted Q&A list for the learner to practice answering:
  - Де ви зараз? (Where are you right now?)
  - Де ви працюєте? (Where do you work?)
  - Де ви живете? (Where do you live?)

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

- [ ] школа → в школі (school)
- [ ] робота → на роботі (work)
- [ ] банк → у банку (bank)
- [ ] магазин → у/в магазині (shop)
- [ ] вулиця → на вулиці (street)
- [ ] місто → у/в місті (city)

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
