

---

## Your Writing Identity

**You are: Lead Ukrainian Instructor.** Your persona is *The Patient Guide*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **15: What I Like** (A1, A1.3 [Actions]).

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

1. **IMMERSION TARGET: 15-25% Ukrainian** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if immersion is outside this range. For A1 early modules, the learner cannot read Cyrillic — English must dominate. For A2+, Ukrainian must carry a significant share — add Ukrainian Reading Practice blocks, dialogues, and example paragraphs to reach the target. Too little Ukrainian fails audit just as much as too much.
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
module: a1-015
level: A1
sequence: 15
slug: what-i-like
version: '1.1'
title: What I Like
subtitle: Я люблю читати — your first verbs
focus: grammar
pedagogy: PPP
phase: A1.3 [Actions]
word_target: 1200
objectives:
- Use люблю + infinitive to express what you like doing
- Use мені подобається + noun to express what you like (as memorized chunk)
- Recognize Ukrainian infinitive form (-ти ending)
- Talk about hobbies and interests using simple verb phrases
dialogue_situations:
- setting: First day at a language exchange — sharing hobbies over tea
  speakers:
  - Анна (learner)
  - Віктор (tandem partner)
  motivation: 'Люблю + infinitive: Люблю читати, Люблю малювати'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Meeting someone''s interests (ULP Ep14 pattern): — Що ти любиш робити?
    — Я люблю читати і слухати музику. — А я люблю готувати. — Правда? Що ти готуєш?
    Infinitives introduced naturally through ''люблю + verb''.'
  - 'Dialogue 2 — Describing preferences: — Тобі подобається ця книга? — Так, мені
    подобається. — А цей фільм? — Ні, мені не подобається. Мені подобається музика.
    ''Подобається'' as a fixed chunk — dative grammar NOT analyzed.'
- section: Я люблю... (I Like...)
  words: 300
  points:
  - 'Люблю + infinitive (what you enjoy doing): Я люблю читати (I like to read). Я
    люблю гуляти (I like to walk). Я люблю готувати (I like to cook). Я люблю слухати
    музику (I like to listen to music). Pattern: subject + люблю + infinitive (-ти
    ending). Infinitive = dictionary form of the verb, always ends in -ти.'
  - 'Common infinitives for hobbies (new vocabulary): читати (to read), гуляти (to
    walk), готувати (to cook), слухати (to listen), дивитися (to watch), грати (to
    play), малювати (to draw), подорожувати (to travel), співати (to sing). Pronunciation:
    the stress in infinitives varies — learn each one.'
- section: Мені подобається... (I Like...)
  words: 300
  points:
  - 'Two ways to say ''I like'' — different grammar, same meaning at A1: Я люблю +
    infinitive = I love/like doing something. Мені подобається + noun = I like something
    (a thing). Мені подобається музика. Мені подобається ця книга. Мені подобається
    Київ. Note: ''мені подобається'' is a chunk — we don''t analyze WHY мені (dative).
    Just use it.'
  - 'Negative: Я не люблю / Мені не подобається: Я не люблю готувати. Мені не подобається
    цей фільм. Question: Ти любиш читати? Тобі подобається? Note: люблю changes by
    person (я люблю, ти любиш) — full conjugation in M17 (Group II).'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Two structures for ''like'': 1. Я люблю + infinitive (-ти) — for activities 2.
    Мені подобається + noun — for things Negative: не before the verb (не люблю, не
    подобається). Self-check: Name 3 things you like doing (Я люблю...). Name 2 things
    you like (Мені подобається...). Name 1 thing you don''t like (Я не люблю... /
    Мені не подобається...).'
vocabulary_hints:
  required:
  - любити (to love/like — verb)
  - подобатися (to be pleasing — used as 'to like')
  - читати (to read)
  - гуляти (to walk)
  - готувати (to cook)
  - слухати (to listen)
  - дивитися (to watch)
  - грати (to play)
  recommended:
  - малювати (to draw)
  - подорожувати (to travel)
  - співати (to sing)
  - музика (music, f)
  - фільм (film, m)
  - книга (book — review from M08)
activity_hints:
- type: fill-in
  focus: 'Complete: Я люблю ___. (choose infinitive for the picture)'
  items: 8
- type: quiz
  focus: Люблю or подобається? Choose the right structure.
  items: 8
- type: match-up
  focus: 'Match infinitives to their meanings: читати ↔ to read'
  items: 8
- type: fill-in
  focus: 'Make it negative: Я люблю → Я не люблю'
  items: 6
connects_to:
- a1-016 (Verbs Group I)
prerequisites:
- a1-014 (Checkpoint — My World)
grammar:
- 'Infinitive form: all verbs end in -ти'
- Люблю + infinitive for activities
- Мені подобається + noun (chunk — no dative analysis)
- Negation with не before the verb
register: розмовний
references:
- title: ULP Season 1, Episode 14
  url: https://www.ukrainianlessons.com/episode14/
  notes: Hobbies and interests — люблю + infinitive pattern.
- title: Літвінова Grade 7, p.26-27
  notes: 'Infinitive definition: форма, що закінчується суфіксом -ти.'

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
- Confirmed: любити, подобатися, читати, гуляти, готувати, слухати, дивитися, грати, малювати, подорожувати, співати, музика, фільм, книга.
- Not found: None.

## Grammar Rules
- Infinitive endings: Правопис §106 — The standard ending for the infinitive is **-ти** (e.g., читати, любити). In certain contexts (poetry, colloquial speech), **-ть** can occur, but **-ти** is the primary literary form.
- Negation with verbs: Правопис §107 — The particle **не** is written separately from verbs (e.g., не люблю, не подобається), except in cases where the verb does not exist without it (e.g., ненавидіти, нетямитися).

## Calque Warnings
- подобатися: OK — Used correctly for "to like" in the sense of "to be pleasing to" (Мені подобається...).
- любити: OK — Used correctly for "to like/love" (Я люблю читати...).
- грати: OK — Note: Use "грати в" + Accusative for sports/games (грати в футбол) and "грати на" + Locative for musical instruments (грати на гітарі). In the plan, it is used as a general activity.

## CEFR Check
- любити: A1 — OK (High frequency, found in Grade 1-2 textbooks).
- читати: A1 — OK (Fundamental skill, Grade 1-2).
- гуляти: A1 — OK (Basic activity, Grade 2).
- готувати: A1 — OK (Daily routine, Grade 2).
- подорожувати: A1 — OK (Found in Grade 2 textbooks: "Ви продовжуєте подорожувати світом української мови").
- фільм: A1 — OK (Modern basic vocabulary).
- музика: A1 — OK (Internationalism, basic vocabulary).
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
# Knowledge Packet: What I Like
**Module:** what-i-like | **Track:** A1

<wiki_context>
## Compiled Wiki Knowledge

The following articles from the project wiki provide compiled knowledge relevant to this module. Use them as authoritative context — they were compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).

### Вікі: pedagogy/a1/what-i-like.md

# Педагогіка A1: What I Like



## Методичний підхід (Methodological Approach)

The core pedagogical goal at A1 is to empower learners to express personal preferences simply and confidently. Ukrainian textbooks for native children achieve this through a communicative and iterative approach, which should be adapted for L2 learners.

The primary structure is introducing a verb of preference followed by either a noun or another verb in the infinitive. The most fundamental verb, **`любити`** (to love/like), is introduced very early. First-grade materials (Джерело: `1-klas-bukvar-bolshakova-2018-2_s0066`) present it in simple, contrasting pairs: "**Я люблю** малювати. **Я не люблю** грати в хокей." This immediately establishes the verb and its negation as tools for expressing personal choice.

The second key structure, **`Мені подобається`** (I like, lit. "To me it is pleasing"), is introduced as a parallel concept. While grammatically more complex (requiring the Dative case), it is frequently used for general likes and is presented as a chunk (Джерело: `ext-ulp_youtube-290`). Textbooks for slightly older children (2nd-3rd grade) begin to use it in questions like "Що тобі подобається найбільше у школі?" (What do you like most at school?) (Джерело: `2-klas-ukrmova-vashulenko-2019-2_s0011`).

The learning process is built around thematic vocabulary clusters related to personal life:
1.  **Food and Drink:** "Я люблю пироги з вишнями" (I love pies with cherries) (Джерело: `1-klas-bukvar-bolshakova-2018-2_s0066`).
2.  **Activities and Hobbies:** "Люблю читати книжку я" (I love to read a book) (Джерело: `6-klas-ukrmova-betsa-2023_s0198`), "Кататися на роликах, ... читати книжки, слухати музику" (Rollerblading, reading books, listening to music) (Джерело: `6-klas-ukrmova-betsa-2023_s0026`).
3.  **School and Learning:** "Мені подобається дізнаватися про вулкани" (I like to learn about volcanoes) (Джерело: `2-klas-ukrmova-vashulenko-2019-2_s0011`).

Exercises are practical and action-oriented, moving from simple sentence construction to dialogues and short narratives about oneself (Джерело: `8-klas-ukrmova-zabolotnyi-2025_s0062`, `6-klas-ukrmova-betsa-2023_s0026`). The focus is always on what the learner can *do* with the language.

## Послідовність введення (Introduction Sequence)

The introduction must be carefully staged to avoid cognitive overload, moving from grammatically simple structures to more complex ones.

-   **Step 1: The Verb `любити` + Noun (Accusative Case)**
    Introduce `Я люблю` (I love/like) with simple, concrete nouns. This is the most direct parallel to the English "I like X." At this stage, use only feminine nouns that have a clear Accusative `-у` ending or masculine inanimate nouns that don't change.
    -   `Я люблю **музику**.` (I like music.) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0077`)
    -   `Я люблю **свою рідну землю**.` (I love my native land.) (Джерело: `3-klas-ukrainska-mova-vashulenko-2020-1_s0014`)
    -   Explain this as a strong, general liking, akin to "love" or a deeply held preference.

-   **Step 2: `любити` + Verb (Infinitive)**
    Immediately expand on Step 1 by showing that `любити` can be followed by an action. This is the gateway to talking about hobbies. The infinitive form, always ending in `-ти`, is presented as a fixed unit.
    -   `Я люблю **малювати**.` (I love to draw.) (Джерело: `1-klas-bukvar-bolshakova-2018-2_s0066`)
    -   `Катерина любить **читати**.` (Kateryna loves to read.) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0048`)
    -   Reinforce with the negative: `Я не люблю **грати** в хокей.` (I don't like to play hockey.) (Джерело: `1-klas-bukvar-bolshakova-2018-2_s0066`).

-   **Step 3: The `подобатися` Construction (Dative + Nominative)**
    Introduce `Мені подобається` as a common alternative for "I like." It's crucial to present `Мені подобається` as a memorized chunk (Джерело: `ext-ulp_youtube-290`). Explain its logic: "To me, X is pleasing."
    -   Start with a noun: `Мені подобається **кімната** моєї старшої сестри.` (I like my older sister's room.) (Джерело: `6-klas-ukrmova-betsa-2023_s0126`). The liked object (`кімната`) is in the Nominative case (the subject of the sentence).
    -   Then add an infinitive: `Мені подобається **дізнаватися** про вулкани...` (I like to learn about volcanoes...) (Джерело: `2-klas-ukrmova-vashulenko-2019-2_s0011`).

-   **Step 4: Distinguishing `любити` and `подобатися`**
    Once both forms are familiar, clarify the nuance. `любити` is for passions, deep affection, and established favorites. `подобатися` is for general liking, first impressions, and objective appeal. A podcast for learners explicitly makes this distinction, noting `любити` is a "very strong phrase" whereas `подобатися` is the more general "like" (Джерело: `ext-ulp_youtube-290`). For A1, the rule of thumb is: use `любити` for hobbies you are passionate about, and `подобатися` for things you generally enjoy.

-   **Step 5: Expanding Hobby Vocabulary with Prepositions**
    Introduce specific constructions for activities that require prepositions. These must be taught as fixed phrases.
    -   `**грати у** + [sport]`: `грати у футбол` (to play football) (Джерело: `6-klas-ukrmova-betsa-2023_s0026`).
    -   `**грати на** + [instrument]`: `грати на гітарі` (to play the guitar) (Джерело: `6-klas-ukrmova-betsa-2023_s0026`).
    -   `**кататися на** + [vehicle/equipment]`: `кататися на велосипеді` (to ride a bicycle) (Джерело: `ext-ulp_youtube-107`), `кататися на роликах` (to rollerblade) (Джерело: `6-klas-ukrmova-betsa-2023_s0026`).

## Типові помилки L2 (Common L2 Errors)

English speakers often map their native grammar onto Ukrainian, leading to predictable errors.

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| `Я подобаюся футбол.` | `Мені подобається футбол.` | This is a direct translation of "I like football." The learner assumes `подобатися` is a regular transitive verb like English "to like" and conjugates it for "I" (`я`). The correct structure requires the Dative pronoun `мені` ("to me") and the verb agrees with the thing being liked, `футбол` (Джерело: `ext-other_blogs-10`). |
| `Я люблю грати футбол.` | `Я люблю грати у футбол.` | The preposition `у`/`в` is required when playing a sport (`грати у`). English structure ("play football") lacks a preposition, so learners often omit it. This rule is explicitly demonstrated in textbook examples (Джерело: `6-klas-ukrmova-betsa-2023_s0020`). |
| `Я люблю грати на футбол.` | `Я люблю грати у футбол.` | Learners overgeneralize the `грати на` rule for musical instruments (`грати на гітарі`) and apply it incorrectly to sports. The distinction between `у` (sports) and `на` (instruments) must be explicitly taught (Джерело: `6-klas-ukrmova-betsa-2023_s0020`). |
| `Мені подобаюся фільми.` | `Мені подобаються фільми.` | The learner correctly uses the Dative `Мені` but fails to make the verb agree with the plural subject `фільми`. The verb must be in the 3rd person plural (`подобаються`), not singular. English "I like" doesn't change based on the object, causing this interference. |
| `Я люблю читати книга.` | `Я люблю книгу.` / `Я люблю читати книги.` | The verb `любити` takes a direct object in the Accusative case. Learners often forget to decline the noun, leaving it in the Nominative (`книга`). This must be drilled with examples like `любити (що?) країну` (Джерело: `3-klas-ukrainska-mova-ponomarova-2020-1_s0044`). |
| `Я хочу бути актриса.` | `Я хочу бути актрисою!` | This is a more advanced error, but relevant. The instrumental case is used for professions after "to be". A learner might use the nominative case. The example `Я хочу бути актрисою!` appears in source material (Джерело: `5-klas-ukrlit-avramenko-2022_s0303`). |

## Деколонізаційні застереження (Decolonization Notes)

**This is a mandatory section for all pedagogical briefs.** The goal is to build a learner's understanding of Ukrainian *from a Ukrainian foundation*, not as a derivative of another language, particularly Russian.

1.  **Teach Ukrainian on its Own Terms:** Never introduce Ukrainian grammar or vocabulary by comparing it to Russian. Avoid phrases like, "Ukrainian `любити` is like Russian `любить`," or "Ukrainian `и` is like Russian `ы`." This frames Ukrainian as a variant rather than a distinct language and builds an incorrect mental model.

2.  **Use Authentic Ukrainian Sources:** All examples, vocabulary, and pedagogical models should come from modern Ukrainian textbooks (e.g., Большакова, Вашуленко, Угор) and media created for Ukrainians or Ukrainian learners (e.g., Ukrainian Lessons Podcast). This ensures cultural and linguistic authenticity. The source material for this brief is exclusively Ukrainian (Джерела: 1-50).

3.  **Correctly Frame Shared Vocabulary:** When encountering cognates (words that are similar in Ukrainian and Russian, like `читати`/`читать`), present them as part of a shared Common Slavic heritage. Do not describe them as "Russian words used in Ukrainian" or "borrowings from Russian." A podcast source notes that about a third of Slavic vocabulary is shared, but this does not imply a parent-child language relationship (Джерело: `ext-ulp_youtube-139`).

4.  **Emphasize Different Usage Patterns:** Even when words are cognates, their usage frequency and grammatical behavior can differ significantly. For example, the `Мені подобається` construction is central to expressing "like" in Ukrainian. While a similar structure exists in Russian (`Мне нравится`), its idiomatic use, frequency, and social context are not identical. Teach the Ukrainian pattern `Мені подобається` based on its own merits and prevalence in Ukrainian speech (Джерело: `ext-ulp_youtube-290`).

## Словниковий мінімум (Vocabulary Boundaries)

This vocabulary is appropriate for the A1 level and is drawn from the provided source materials (Grades 1-6 and beginner podcasts).

### Дієслова (Verbs)

-   `любити` ★★★ (to love, like) (Джерело: `1-klas-bukvar-bolshakova-2018-2_s0066`)
-   `подобатися` ★★★ (to like, be pleasing to) (Джерело: `6-klas-ukrmova-betsa-2023_s0126`)
-   `читати` ★★★ (to read) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0048`)
-   `дивитися` ★★★ (to watch) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0077`)
-   `слухати` ★★★ (to listen to) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0077`)
-   `грати` ★★ (to play) (Джерело: `6-klas-ukrmova-betsa-2023_s0020`)
-   `малювати` ★★ (to draw) (Джерело: `1-klas-bukvar-bolshakova-2018-2_s0066`)
-   `кататися` ★★ (to ride, go for a ride) (Джерело: `6-klas-ukrmova-betsa-2023_s0026`)
-   `співати` ★★ (to sing) (Джерело: `5-klas-ukrmova-golub-2022_s0027`)
-   `подорожувати` ★ (to travel) (Джерело: `5-klas-ukrmova-golub-2022_s0028`)
-   `плавати` ★ (to swim) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0049`)
-   `їсти` ★ (to eat) (Джерело: `ext-ulp_youtube-290`)
-   `пити` ★ (to drink) (Джерело: `ext-ulp_youtube-290`)

### Іменники (Nouns)

-   `книга` / `книжки` ★★★ (book/books) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0048`)
-   `музика` ★★★ (music) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0077`)
-   `фільм` ★★★ (film, movie) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0077`)
-   `футбол` ★★ (football) (Джерело: `5-klas-ukrmova-uhor-2022-1_s0048`)
-   `велосипед` ★★ (bicycle) (Джерело: `6-klas-ukrmova-betsa-2023_s0026`)
-   `літо` ★★ (summer) (Джерело: `ext-ulp_youtube-290`)
-   `осінь` ★★ (autumn) (Джерело: `ext-ulp_youtube-290`)
-   `чай` ★★ (tea) (Джерело: `ext-ulp_youtube-290`)
-   `гітара` ★ (guitar) (Джерело: `6-klas-ukrmova-betsa-2023_s0020`)
-   `ролики` ★ (rollerblades) (Джерело: `6-klas-ukrmova-betsa-2023_s0026`)
-   `шахи` ★ (chess) (Джерело: `1-klas-bukvar-bolshakova-2018-2_s0066`)

## Приклади з підручників (Textbook Examples)

These exercises are models for the types of activities the content writer should create.

1.  **Simple Sentence Completion (Verb + Infinitive)**
    This exercise from a Grade 8 textbook (adaptable for A1) reinforces the core structure of liking an action.
    *   **Prompt format:** "Підготуйте коротку розповідь про себе ... використовуючи складені дієслівні присудки." (Prepare a short story about yourself... using compound verbal predicates.)
    *   **Example List:**
        -   `люблю читати (спостерігати)`
        -   `хочу поїхати в Карпати`
        -   `умію готувати`
        -   `мрію побудувати дім`
        -   `почав грати у футбол`
    *   **Source:** `8-klas-ukrmova-zabolotnyi-2025_s0062`

2.  **Collocation Building (Verb + Noun)**
    This exercise forces learners to connect the correct verb with a list of nouns, building natural-sounding phrases.
    *   **Prompt format:** "Складіть словосполучення. Озвучте складені словосполучення." (Create word combinations. Voice the created combinations.)
    *   **Example:**
        -   **ДИВИТИСЯ:** `серіал, фільм, мультфільм, балет, телепередачу...`
        -   **СЛУХАТИ:** `концерт, музику, класичну музику, оперу, сучасну музику...`
        -   **ЧИТАТИ:** `підручник, словник, детектив, журнал, електронний лист...`
    *   **Source:** `5-klas-ukrmova-uhor-2022-1_s0077`

3.  **Structured Sentence Building**
    This activity guides the learner from simple concepts to a full sentence, practicing word order and verb conjugation.
    *   **Prompt format:** "Складіть речення за зразком." (Create sentences according to the model.)
    *   **Example:**
        -   **Input:** `Томаш — кататися на ковзанах — льодовий майданчик.`
        -   **Output:** `Томаш катається на ковзанах на льодовому майданчику.`
        -   *Further expansion:* `Узимку Томаш катається на ковзанах на міському льодовому майданчику.`
    *   **Source:** `6-klas-ukrmova-betsa-2023_s0020`

4.  **Communicative Question & Answer**
    This exercise places the target language in a realistic, personal context, encouraging learners to talk about themselves.
    *   **Prompt format:** "Дайте усну відповідь на запитання." (Give an oral answer to the questions.)
    *   **Example Questions:**
        -   `Як тебе звати?`
        -   `Які шкільні уроки тобі подобаються?`
        -   `Чим ти любиш займатися у вільний час?`
    *   **Source:** `6-klas-ukrmova-betsa-2023_s0026`

## Пов'язані статті (Related Articles)

-   `pedagogy/a1/dative-case`
-   `pedagogy/a1/accusative-case`
-   `pedagogy/a1/verb-conjugation-present-tense`
-   `pedagogy/a1/infinitive-verbs`
-   `vocabulary/a1/hobbies-and-leisure`
-   `vocabulary/a1/food-and-drink`

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

Write these sections as H2 headings, in this exact order:

- `## Діалоги (Dialogues)` (~300 words)
- `## Я люблю... (I Like...)` (~300 words)
- `## Мені подобається... (I Like...)` (~300 words)
- `## Підсумок — Summary` (~300 words)

Each section should follow the word budget specified. The total must reach 1200 words minimum.

---

## Content Rules

TARGET: 15-25% Ukrainian.
LANGUAGE ROLES:
- THEORY & EXPLANATION: English prose — explain the grammar concept once, clearly.
- EXAMPLES: Ukrainian sentences in bulleted lists (each line: Ukrainian — English gloss). Max 2-4 per rule.
- TABLES: Paradigm tables, gender sorting, vocabulary groups — all cells Ukrainian.
- PATTERN BOXES: Show transformations and rules: `книга → книги` (singular → plural).
- INLINE: Ukrainian words/phrases bolded in English prose.
- STRUCTURAL RULE: Paragraphs are English with inline bold Ukrainian. Full Ukrainian sentences go in tables, bulleted lists, or pattern boxes — never in flowing prose.
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

PLAN-AWARE EXEMPTIONS: The following bans are RELAXED for this module because the plan explicitly teaches these constructs: Dative case (plan teaches it). Exception: If a grammar construct appears in this module's plan grammar list or objectives, it is ALLOWED for this module.

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
  1. **First day at a language exchange — sharing hobbies over tea**
     Speakers: Анна (learner), Віктор (tandem partner)
     Why: Люблю + infinitive: Люблю читати, Люблю малювати

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

GRAMMAR CONSTRAINTS (A1.3 — Actions & Desires, M15-M21):
Present tense verbs, modals, questions, reflexives.

ALLOWED:
- Present tense conjugation (both groups: -ати and -ити)
- Modal verbs: хотіти, могти, мусити + infinitive
- Question words: Хто? Що? Де? Куди? Коли? Чому?
- Negation: не/ні
- Reflexive verbs (-ся/-сь)
- 'Мені подобається' as lexical chunk (NO dative grammar)

BANNED: Past/future tense, cases beyond nominative,
participles, passive voice, complex subordinate clauses

### Vocabulary

**Required:** любити (to love/like — verb), подобатися (to be pleasing — used as 'to like'), читати (to read), гуляти (to walk), готувати (to cook), слухати (to listen), дивитися (to watch), грати (to play)
**Recommended:** малювати (to draw), подорожувати (to travel), співати (to sing), музика (music, f), фільм (film, m), книга (book — review from M08)

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
## Діалоги — Dialogues (~330 words)
- P1 (~120 words): [Dialogue 1: Meeting at a tandem exchange. Anna and Viktor discuss hobbies. Viktor asks: "Що ти любиш робити?" Anna responds with a list: "Я люблю читати і слухати музику." Viktor shares his passion for cooking: "Я люблю готувати." They use 'Правда?' to show interest and introduce the verb 'готуєш' naturally.]
- P2 (~120 words): [Dialogue 2: Preferences regarding objects. Viktor shows Anna a book and a film. He asks: "Тобі подобається ця книга?" Anna confirms: "Так, мені подобається." When asked about a film, she expresses a negative preference: "Ні, мені не подобається цей фільм. Мені подобається музика." This dialogue establishes 'подобається' as a chunk for things.]
- P3 (~90 words): [Analysis of the dialogues: Point out that when we talk about *doing* things (actions like reading or cooking), we used 'люблю'. When we talked about *things* (the book, the film, music), we used 'подобається'. Note the transition from verbs to nouns.]

## Я люблю... — I Like Doing... (~330 words)
- P1 (~80 words): [Explaining the structure "Я люблю + infinitive". Explain that this is the most direct way to talk about hobbies. Provide the formula: Subject (Я) + verb (люблю) + Action (Infinitive). Use 3 core examples: Я люблю читати, Я люблю малювати, Я люблю співати.]
- P2 (~80 words): [Defining the Ukrainian infinitive. Explain that the "dictionary form" of a verb always ends in the suffix -ти. Give examples of how to spot it in a dictionary: читати (to read), гуляти (to walk), слухати (to listen). Explain that the ending -ти never changes in this 'like' structure.]
- P3 (~100 words): [Hobby Vocabulary Expansion. Introduce high-frequency verbs for free time: дивитися (to watch), грати (to play), подорожувати (to travel), готувати (to cook). Briefly introduce the prepositions for sports and instruments: 'грати у футбол' (sports) vs 'грати на гітарі' (instruments) as fixed phrases to memorize.]
- <!-- INJECT_ACTIVITY: match-up-infinitives --> [match-up, Match infinitives to their English meanings: читати ↔ to read, 8 items]
- <!-- INJECT_ACTIVITY: fill-in-hobbies --> [fill-in, Complete the sentence based on a picture: Я люблю ___. (e.g., гуляти, малювати), 8 items]
- P4 (~70 words): [Negation with 'люблю'. Explain that to say "I don't like", we simply place 'не' before the verb. Provide contrasting examples: "Я люблю гуляти" vs "Я не люблю гуляти". Explain that 'не' is always a separate word.]

## Мені подобається... — It Pleases Me... (~340 words)
- P1 (~100 words): [Introduction to the 'Мені подобається' construction. Explain that this is a "fixed chunk" used to express that you like a thing (a noun). Emphasize that learners should not analyze the grammar of 'мені' (dative) yet—just memorize the phrase. Examples: Мені подобається книга, Мені подобається музика, Мені подобається Київ.]
- P2 (~100 words): [Distinguishing 'любити' vs 'подобатися'. Use the pedagogical distinction: 'любити' is for active hobbies, passions, and things you "love" (Я люблю читати). 'Подобатися' is for general liking, things, and first impressions (Мені подобається цей фільм). Mention that 'любити' is a stronger emotion.]
- P3 (~100 words): [Asking questions and Negation. Show how to ask "Do you like?" using both structures: "Ти любиш читати?" and "Тобі подобається цей фільм?". Explain the negative: "Мені не подобається". Note that the word order 'Тобі подобається' or 'Подобається тобі' can vary, but the chunk remains.]
- <!-- INJECT_ACTIVITY: quiz-like-choice --> [quiz, Choose the correct structure based on context (noun vs infinitive): Люблю or подобається?, 8 items]
- <!-- INJECT_ACTIVITY: fill-in-negatives --> [fill-in, Change the positive sentence to negative: Я люблю → Я не люблю, 6 items]
- P4 (~40 words): [Common error warning. Explicitly warn against literal translation of "I like". Correct the mistake "Я подобаюся футбол" to "Мені подобається футбол", explaining that in Ukrainian, the football is doing the "pleasing".]

## Підсумок — Summary (~300 words)
- P1 (~150 words): [Recap of the two ways to say "I like". First, for activities: "Я люблю + -ти verb" (Я люблю співати). Second, for things: "Мені подобається + noun" (Мені подобається музика). Reminder that 'не' always comes before the verb to make it negative (Я не люблю, Мені не подобається).]
- P2 (~150 words): [Self-check checklist for the learner:
  - Can you name three hobbies? (Я люблю читати, малювати, гуляти).
  - Can you name two things you like? (Мені подобається музика, книга).
  - Do you know the ending of a Ukrainian infinitive? (-ти).
  - Can you tell a friend you don't like something? (Мені не подобається...).
  - Do you know which preposition to use with 'гітара' (на) and 'футбол' (у)?]

Grand total: ~1300 words
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
