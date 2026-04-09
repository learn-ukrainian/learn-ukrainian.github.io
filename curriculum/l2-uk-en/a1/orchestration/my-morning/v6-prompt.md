

---

## Your Writing Identity

**You are: Lead Ukrainian Instructor.** Your persona is *The Patient Guide*.

Write with the authority, depth, and tone that this identity demands. A history professor writes differently from a language tutor. A patient tutor encourages and scaffolds; a senior specialist challenges and deepens. Let your identity shape your word choice, pacing, and cultural sensitivity.

<!-- version: 2.0.0 | updated: 2026-04-07 | wiki replaces RAG -->
# V6 Writing Prompt — Module Content Generation

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **20: My Morning** (A1, A1.3 [Actions]).

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
module: a1-020
level: A1
sequence: 20
slug: my-morning
version: '1.2'
title: My Morning
subtitle: Прокидаюся, вмиваюся — reflexive verbs and routines
focus: grammar
pedagogy: PPP
phase: A1.3 [Actions]
word_target: 1200
objectives:
- Recognize and use reflexive verbs with -ся/-сь
- Describe a morning routine using sequence words
- Conjugate reflexive verbs in present tense (same endings + ся)
- Tell a simple daily story in sequence
dialogue_situations:
- setting: Two roommates comparing their morning routines before leaving for work
  speakers:
  - Ліна
  - Настя
  motivation: 'Reflexive verbs: прокидаюся, вмиваюся, одягаюся in sequence'
content_outline:
- section: Діалоги (Dialogues)
  words: 300
  points:
  - 'Dialogue 1 — Morning routine: — Коли ти прокидаєшся? — Я прокидаюся о сьомій.
    — Що ти робиш потім? — Вмиваюся, одягаюся і снідаю. — А коли ти йдеш на роботу?
    — О восьмій. Reflexive verbs emerge through describing the morning.'
  - 'Dialogue 2 — Weekend morning (contrast): — У суботу я не поспішаю. Прокидаюся
    пізно, лежу, дивлюся телефон. — А я навчаюся вранці. Потім гуляю. Mix of reflexive
    and non-reflexive verbs.'
- section: Дієслова на -ся (Reflexive Verbs)
  words: 300
  points:
  - 'Караман Grade 10 p.176: Дієслова із суфіксом -ся(-сь) означають дію, спрямовану
    на себе. вмивати (to wash someone) → вмиватися (to wash oneself). одягати (to
    dress someone) → одягатися (to dress oneself). The -ся attaches to the end of
    every conjugated form: я вмиваюся, ти вмиваєшся, він/вона вмивається.'
  - 'Кравцова Grade 4 p.113: pronunciation note: -шся sounds like [с'':а] (long soft
    с): вмиваєшся → [вмиваєс'':а]. -ться sounds like [ц'':а] (long soft ц): вмивається
    → [вмиваєц'':а]. The spelling and pronunciation differ — learn both!'
- section: Мій ранок (My Morning)
  words: 300
  points:
  - 'Morning routine vocabulary (reflexive verbs): прокидатися (to wake up), вмиватися
    (to wash face/hands), одягатися (to get dressed), збиратися (to get ready), повертатися
    (to return home). Non-reflexive morning verbs for contrast: снідати (to have breakfast),
    пити каву (to drink coffee). Йти (to go) — irregular: я йду, ти йдеш, він/вона
    йде. Learn these forms — they don''t follow Group I or II patterns.'
  - 'Sequence words for telling a story: спочатку (first), потім (then), після цього
    (after this), нарешті (finally). Мій ранок: Спочатку я прокидаюся. Потім вмиваюся
    і одягаюся. Після цього снідаю. Нарешті йду на роботу.'
- section: Підсумок — Summary
  words: 300
  points:
  - 'Reflexive verbs = regular verb + ся at the end. я -юся, ти -єшся, він/вона -ється
    (Group I pattern + ся). Morning routine: прокидатися → вмиватися → одягатися →
    снідати → йти. Sequence words: спочатку, потім, після цього, нарешті. Self-check:
    Describe your morning in 4-5 sentences using sequence words.'
vocabulary_hints:
  required:
  - прокидатися (to wake up)
  - вмиватися (to wash face/hands)
  - одягатися (to get dressed)
  - снідати (to have breakfast)
  - йти (to go — irregular)
  - спочатку (first, at first)
  - потім (then, next)
  recommended:
  - збиратися (to get ready)
  - повертатися (to return)
  - навчатися (to study/learn)
  - поспішати (to hurry)
  - після цього (after this)
  - нарешті (finally)
  - вранці (in the morning)
  - пізно (late)
activity_hints:
- type: fill-in
  focus: 'Add -ся: я вмиваю__ , ти одягаєш__ , він прокидаєть__'
  items: 10
- type: quiz
  focus: 'Reflexive or not? Choose: Я (вмиваю/вмиваюся) руки.'
  items: 8
- type: fill-in
  focus: 'Put the morning routine in order: спочатку ___, потім ___, нарешті ___'
  items: 6
- type: fill-in
  focus: Describe your morning in 3 sentences
  items: 3
connects_to:
- a1-021 (Checkpoint — Actions)
prerequisites:
- a1-019 (Questions)
grammar:
- 'Reflexive verbs: regular conjugation + -ся/-сь suffix'
- 'Pronunciation: -шся=[с'':а], -ться=[ц'':а] (gemination)'
- 'Sequence words: спочатку, потім, після цього, нарешті'
register: розмовний
references:
- title: Караман Grade 10, p.176
  notes: 'Зворотні дієслова: суфікс -ся(-сь) означає дію, спрямовану на себе.'
- title: Кравцова Grade 4, p.113
  notes: 'Pronunciation: -шся=[с''а], -ться=[ц''а].'
- title: Захарійчук Grade 4, p.162
  notes: 'Дієслова на -ся: вправи з вимовою та правописом.'

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
- Confirmed: прокидатися, вмиватися, одягатися, снідати, йти, спочатку, потім, збиратися, повертатися, навчатися, поспішати, нарешті, вранці, пізно, після, цього.
- Not found: [none] (Note: "після цього" is a multi-word phrase verified as separate components).

## Grammar Rules
- **Euphony (у/в, і/й)**: Правопис §23 — Rules for alternating у/в and і/й to maintain melody (милозвучність). Use "вранці" after a vowel, "уранці" at the start of a sentence or after a consonant. Similarly, "йти" vs "іти".
- **Reflexive Verbs (-ся)**: Grade 10 (Karaman) p. 176 — Suffix -ся(-сь) indicates an action directed at oneself. Used after infinitive -ти or person endings: вмиватися, вмиваюся.
- **Pronunciation of -ся**: Grade 4 (Kravtsova) p. 113 — -шся is pronounced as [с':а] (soft long s), -ться is pronounced as [ц':а] (soft long ts).
- **Conjugation of "йти"**: Grade 1 (Zaharijchuk) p. 87 / Grade 6 (Betsa) p. 219 — Irregular: я йду, ти йдеш, він/вона йде, вони йдуть.

## Calque Warnings
- **після цього**: OK — Standard phrase for "after this".
- **нарешті**: OK — Standard for "finally".
- **потім**: OK — Standard for "then/afterwards".
- **приймати душ**: OK (though not in style guide search, "брати душ" or "митися" are also natural alternatives; "приймати душ" is widely used in modern Ukrainian).

## CEFR Check
- **снідати**: A1 — OK
- **йти**: A1 — OK
- **прокидатися**: A1 — OK
- **вмиватися**: A1 — OK
- **одягатися**: A1 — OK
- **вранці**: A1 — OK
(Note: query_cefr_level tool returned technical errors; levels confirmed via pedagogical common sense and textbook placement).
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
# Knowledge Packet: My Morning
**Module:** my-morning | **Track:** A1

<wiki_context>
## Compiled Wiki Knowledge

The following articles from the project wiki provide compiled knowledge relevant to this module. Use them as authoritative context — they were compiled from primary sources (Костомаров, Чижевський, Попович, textbooks, etc.).

### Вікі: pedagogy/a1/my-morning.md

# Педагогіка A1: My Morning



## Методичний підхід (Methodological Approach)

The topic "My Morning" is a foundational A1 module that introduces daily routine verbs. The core pedagogical challenge is the correct usage and pronunciation of **зворотні дієслова (reflexive verbs)** ending in `-ся`.

The approach should be grounded in simple, sequential actions. The learner first describes what they do, then learns to connect these actions into a narrative.

1.  **Action-First Principle:** Start with physical actions. The curriculum should model simple sentences like "Я п'ю чай" and "Я їм сніданок" before moving to more abstract concepts. This aligns with how native speakers describe their day in simple terms (Source: `ext-ulp_youtube-253`).

2.  **Introducing Reflexive Verbs as "Action on Oneself":** The key concept of `-ся` is that the action is directed back at the subject. Ukrainian grammar textbooks explain that this suffix is a historical remnant of the reflexive pronoun `себе` (Source: `10-klas-ukrmova-karaman-2018_s0315`). Therefore, `умиватися` is conceptually "to wash oneself," and `одягатися` is "to dress oneself." This framing is intuitive for English speakers, who can understand the logic even if their own language doesn't use suffixes this way. A verb with `-ся` is always intransitive (неперехідне) (Source: `6-klas-ukrmova-betsa-2023_s0202`, `10-klas-ukrmova-karaman-2018_s0332`).

3.  **Narrative Scaffolding:** Use sequencing adverbs (`спочатку`, `потім`, `далі`) to build a simple story. This is a natural way to structure a routine, as demonstrated in native speaker monologues (Source: `ext-ulp_youtube-248`). The goal is for the learner to produce a short paragraph like: "Вранці я прокидаюся. Потім я умиваюся. Я снідаю і п'ю каву."

4.  **Pronunciation as a Priority:** The pronunciation of `-шся` `[с':а]` and `-ться` `[ц':а]` is a major hurdle. This must be taught explicitly from the beginning, using targeted drills. Textbooks for native Ukrainian children dedicate specific exercises to this (Source: `4-klas-ukrayinska-mova-kravtsova-2021-1_s0111`).

## Послідовність введення (Introduction Sequence)

1.  **Time of Day:** Begin with the core adverb `вранці` (in the morning). Contrast it with `ввечері` (in the evening) to establish a simple daily timeline (Source: `ext-ulp_youtube-253`).

2.  **Basic Non-Reflexive Verbs:** Introduce high-frequency verbs that don't require `-ся`.
    *   `снідати` (to have breakfast)
    *   `пити` (to drink)
    *   `їсти` (to eat)
    *   `іти` (to go) - e.g., `іти на роботу`
    Example sentence: "Вранці я снідаю" (Source: `ext-ulp_youtube-253`).

3.  **Core Reflexive Verbs (`-ся`):** Introduce the most common morning routine verbs, explaining the `-ся` as an action performed on oneself (Source: `10-klas-ukrmova-karaman-2018_s0315`).
    *   `прокидатися` (to wake up)
    *   `умиватися` (to wash one's face/hands)
    *   `одягатися` (to get dressed)
    *   Also, the set phrase `чистити зуби` (to brush teeth) should be introduced here.

4.  **Sequencing Adverbs:** Provide the learner with tools to build a narrative.
    *   `спочатку` (at first)
    *   `потім` (then)
    *   `завжди` (always)
    *   `зазвичай` (usually)
    *   `іноді` (sometimes)
    Native speaker examples show this is a natural pattern: "Спочатку я випиваю велику склянку води... а потім чашку зеленого чаю" (Source: `ext-ulp_youtube-253`).

5.  **Building a Full Routine:** Combine the elements into a short monologue. The initial goal is for the learner to describe their own morning using 3-5 simple sentences.

## Типові помилки L2 (Common L2 Errors)

This section highlights common mistakes English-speaking learners make with this topic.

| ❌ Помилково | ✅ Правильно | Чому |
| :--- | :--- | :--- |
| Я прокидаю о 7-й. | Я прокидаю**ся** о 7-й. | English uses intransitive verbs ("I wake up") where Ukrainian requires a reflexive verb ("I wake myself up"). Learners often omit the `-ся` particle as it feels redundant from an English perspective (Source: `4-klas-ukrayinska-mova-ponomarova-2021-1_s0098`). |
| "ти умиває**ш-ся**" (pronounced with two distinct sounds) | "ти умиває**[с':а]**" | English speakers try to pronounce `-шся` as `/ʃsja/`. Ukrainian phonetics merge this into a single, soft `[с':]` sound. This is a critical pronunciation rule explicitly taught to native children (Source: `4-klas-ukrayinska-mova-kravtsova-2021-1_s0111`). |
| "він одягає**ть-ся**" (pronounced with two distinct sounds) | "він одягає**[ц':а]**" | Similarly, `-ться` is not `/tsja/`. It merges into a soft `[ц':]` sound. This rule is fundamental to fluent Ukrainian pronunciation (Source: `4-klas-ukrayinska-mova-kravtsova-2021-1_s0111`). |
| Вранці я **сніданок**. | Вранці я **снідаю**. | Noun/verb confusion. In English, "I have breakfast." Learners may incorrectly use the noun `сніданок` as a verb. It must be taught that `снідати` is the action word (Source: `ext-ulp_youtube-253`). |
| Я встаю, а потім я прокидаюся. | Я прокидаюся, а потім я встаю. | Conceptual confusion between `прокидатися` (to wake up, i.e., become conscious) and `вставати` (to get up, i.e., leave the bed). The correct sequence must be explicitly taught. Christina in the ULP podcast says "прокинулася раніше без будильника" (woke up without an alarm) (`ext-ulp_youtube-193`). |
| Я п'ю каву **зрання**. | Я п'ю каву **вранці**. | Use of poetic or archaic forms. `зрання` is a valid word but more poetic or regional. For A1 learners, the standard `вранці` should be taught as the primary word for "in the morning" (Source: `ext-ulp_youtube-14`). |

## Деколонізаційні застереження (Decolonization Notes)

This is a **mandatory** section. The teaching of Ukrainian must be free from Russian-centric frameworks.

1.  **The `-ся` Suffix is Pan-Slavic, Not Russian:** The reflexive suffix `-ся` originates from the Proto-Slavic reflexive pronoun and is present in various forms across Slavic languages. It is **not** a Russian feature that Ukrainian "borrowed." It is a core part of Ukrainian grammar derived from its own historical development (Source: `10-klas-ukrmova-karaman-2018_s0315`). Avoid any comparisons to Russian; teach it as a native Ukrainian feature.

2.  **Pronunciation is Exclusively Ukrainian:** The pronunciation of `-ться` as `[ц':а]` and `-шся` as `[с':а]` is a hallmark of the Ukrainian phonetic system. Do **not** use Russian pronunciation (`[ца]`) as a reference point or an "easier" alternative. Learners must build the correct Ukrainian motor habits from scratch.

3.  **Vocabulary Purity:** Use exclusively Ukrainian vocabulary. For "breakfast," the word is `сніданок` (verb `снідати`). Avoid any calques or loanwords from Russian that may have been prevalent in the Soviet era. The source materials exclusively use standard Ukrainian forms (e.g., `ext-ulp_youtube-253`, `ext-ulp_youtube-248`).

## Словниковий мінімум (Vocabulary Boundaries)

This vocabulary is appropriate for an A1 learner discussing their morning.

**Дієслова (Verbs):**
*   `прокидатися` (to wake up) ★★★
*   `вставати` (to get up) ★★★
*   `умиватися` (to wash one's face/hands) ★★★
*   `чистити зуби` (to brush teeth) ★★★
*   `одягатися` (to get dressed) ★★
*   `снідати` (to have breakfast) ★★★
*   `пити` (to drink) ★★★
*   `їсти` (to eat) ★★★
*   `іти (на роботу / в школу)` (to go to work / to school) ★★

**Іменники (Nouns):**
*   `ранок` (morning) ★★★
*   `сніданок` (breakfast) ★★★
*   `вода` (water) ★★★
*   `чай` (tea) ★★★
*   `кава` (coffee) ★★★
*   `будильник` (alarm clock) ★★
*   `ліжко` (bed) ★★
*   `зуби` (teeth) ★★★

**Прислівники (Adverbs):**
*   `вранці` (in the morning) ★★★
*   `потім` (then) ★★★
*   `спочатку` (at first) ★★
*   `завжди` (always) ★★
*   `зазвичай` (usually) ★★
*   `іноді` (sometimes) ★
*   `рано` (early) ★★
*   `пізно` (late) ★

## Приклади з підручників (Textbook Examples)

These are model exercises the content writer should adapt.

1.  **Pronunciation Drill (adapted from `4-klas-ukrayinska-mova-kravtsova-2021-1_s0111`):**
    *   **Activity:** Listen and repeat. Pay attention to the sound `[с':а]`.
        *   ти прокидає**шся**
        *   ти вмиває**шся**
        *   ти одягає**шся**
    *   **Activity:** Listen and repeat. Pay attention to the sound `[ц':а]`.
        *   він прокидає**ться**
        *   вона вмиває**ться**
        *   вони смію**ться**

2.  **Sentence Transformation (adapted from `4-klas-ukrayinska-mova-kravtsova-2021-1_s0111`):**
    *   **Prompt:** Change the verb to the 2nd person singular ("ти" form).
    *   **Example:** `(Прокидатися) рано - це добре.` → `Ти **прокидаєшся** рано.`

3.  **Simple Q&A (adapted from ULP podcasts `ext-ulp_youtube-253`):**
    *   **Prompt:** Answer the questions about your morning.
        *   О котрій годині ти прокидаєшся?
        *   Що ти п'єш вранці?
        *   Що ти зазвичай їси на сніданок?

4.  **Build a Narrative (adapted from `ext-ulp_youtube-248`):**
    *   **Prompt:** Put the sentences in the correct order to describe a morning routine.
        *   `Потім я п'ю каву.`
        *   `Спочатку я прокидаюся і вмиваюся.`
        *   `Я снідаю о восьмій годині.`
        *   `Я йду на роботу.`

## Пов'язані статті (Related Articles)

*   `pedagogy/a1/present-tense-verbs`
*   `grammar/reflexive-verbs-sya`
*   `vocabulary/a1/daily-routines`
*   `phonetics/pronouncing-consonant-clusters`
*   `pedagogy/a1/telling-time`

---

### Вікі: pedagogy/a1/checkpoint-my-world.md

# Педагогіка A1: Checkpoint My World



## Методичний підхід (Methodological Approach)
The "My World" checkpoint is a crucial consolidation module for A1 learners. The primary pedagogical goal is to shift the learner from passive recognition and simple responses to active, structured production. This module assesses the learner's ability to synthesize vocabulary and grammar from previous lessons to talk about the most important topic: themselves.

The core methodology is **scaffolding from dialogue to monologue**. Ukrainian pedagogy for young learners heavily emphasizes this transition. We start with simple, structured question-and-answer pairs and gradually build towards a short, coherent narrative. As seen in `Source 15` (`6-klas-ukrmova-betsa-2023_s0018`), a key exercise is to "Трансформуйте діалог у монолог" (Transform the dialogue into a monologue). This provides a clear pathway for learners, reducing the cognitive load of spontaneous production.

The structure of the produced text is explicitly taught, following the model used in Ukrainian primary schools: **Зачин (Introduction), Основна частина (Main Part), and Кінцівка (Conclusion)** (Джерело: `2-klas-ukrmova-kravcova-2019-1_s0119`). This simple three-part structure gives learners a reliable template for organizing their thoughts, whether they are writing about their family, their day, or their hobbies. The goal is not literary prowess, but clear, logical communication.

Finally, this module is an opportunity for **active recall and application**. It is not about introducing a large volume of new material. Instead, it's about activating what has already been learned in a meaningful, personalized context. The focus is on communicative competence and building the learner's confidence in using Ukrainian to express personal information (Source 31: `ext-ulp_youtube-60`).

## Послідовність введення (Introduction Sequence)
The "My World" checkpoint should follow a logical progression from simple questions to a structured personal narrative. The sequence of tasks should be designed to build confidence at each stage.

1.  **Step 1: Foundational Q&A (Recycled Vocabulary).**
    Begin by activating core introductory phrases. The task is a simple dialogue where the learner answers basic questions about themselves. This reinforces patterns they should already know.
    *   *Prompt:* — Як тебе звуть? / — Мене звуть... (Джерело: `6-klas-ukrmova-betsa-2023_s0014`)
    *   *Prompt:* — Як твоє прізвище? / — Моє прізвище... (Джерело: `6-klas-ukrmova-betsa-2023_s0014`)
    *   *Prompt:* — Звідки ти? / — Я з [country/city].
    *   *Prompt:* — Де ти живеш? / — Я живу в [city].

2.  **Step 2: Expanding the Circle (Family & Professions).**
    Introduce questions about the people in the learner's "world." This stage focuses on using third-person pronouns (*він, вона*) and possessives (*його, її*), along with the instrumental case for professions.
    *   *Prompt:* — Розкажи... хто це на фото? (Джерело: `6-klas-ukrmova-betsa-2023_s0018`)
    *   *Model:* — Ось це моя мама. Її звуть... Вона працює лікаркою. (Джерело: `6-klas-ukrmova-betsa-2023_s0018`)
    *   This step requires learners to correctly apply noun gender for family members (мама, тато) and agree possessive pronouns accordingly (моя мама, мій тато).

3.  **Step 3: Transitioning from Dialogue to Monologue.**
    This is the most critical step. Guide the learner to connect their previous answers into a simple, continuous text. The prompt is direct: "Transform the dialogue into a monologue" (Джерело: `6-klas-ukrmova-betsa-2023_s0018`).
    *   *Model:* "Мене звати [Ім'я]. Я з [країна]. Я живу в [місто]. Це моя мама. Її звати... Вона працює вчителькою."

4.  **Step 4: Explicitly Structuring the Narrative.**
    Introduce the formal structure for any simple text, as taught in Ukrainian schools. This provides a mental checklist for the learner.
    *   **Зачин (Introduction):** State the topic. ("Я хочу розповісти про свою сім'ю.")
    *   **Основна частина (Main Part):** Provide the details. (Names, professions, etc.)
    *   **Кінцівка (Conclusion):** A simple closing sentence. ("Я люблю свою родину.")
    *   This framework helps organize the information from Step 3 into a more formal composition (Джерело: `2-klas-ukrmova-kravcova-2019-1_s0119`).

5.  **Step 5: Final Production (Written or Spoken).**
    The culminating task is a free, but guided, production. The prompt should be specific but allow for personalization.
    *   *Prompt Example:* "Напишіть розповідь «Моя сім’я»" (Джерело: `6-klas-ukrmova-betsa-2023_s0018`).
    *   *Alternative Prompts:* "Опиши свого друга / свою подругу", "Розкажи про свій дім".

## Типові помилки L2 (Common L2 Errors)
For English-speaking learners, the "My World" topic surfaces several predictable errors related to gender, case, and sentence structure.

| ❌ Помилково (Incorrect) | ✅ Правильно (Correct) | Чому (Why) |
| :--- | :--- | :--- |
| `Моя тато` і `мій мама`. | `Мій тато` і `моя мама`. | Learners incorrectly associate `моя` with "my" for a female (mom) and `мій` for a male (dad). The possessive pronoun must agree with the **grammatical gender of the noun** it modifies (`тато` is masculine, `мама` is feminine), not the gender of the person. (Джерело: `ext-other_blogs-46`) |
| Я працюю `вчитель`. | Я працюю `вчителем`. | When stating a profession with `працювати` (or being something), the noun for the profession must be in the **Instrumental case (Орудний відмінок)**. English uses the nominative ("I work as a teacher"). A Ukrainian school textbook explicitly models this: `Ким працює? (О. в.) ... учителем` (Джерело: `6-klas-ukrmova-betsa-2023_s0016`). |
| Моє ім'я є Анна. | Мене звати Анна. | This is a direct translation of the English structure "My name is...". While `Моє ім'я Анна` is grammatically possible, the most common and natural way to introduce oneself is the structure `Мене звати...` ("They call me..."). This is the first form taught in Ukrainian textbooks (Джерело: `6-klas-ukrmova-betsa-2023_s0014`). |
| `Привіт, Давид!` | `Привіт, Давиде!` | English does not have a vocative case for direct address. In Ukrainian, it is mandatory. Learners often forget to change the ending of a name when addressing someone directly. `Оксанко, ти знаєш...` is a clear example from a textbook (Джерело: `5-klas-ukrmova-uhor-2022-1_s0015`). |
| Це його сестра. Її звати Ірина. Це **його** брат. | Це його сестра. Її звати Ірина. Це **її** брат. | Learners confuse the meaning of possessive pronouns. When talking about Irina's brother, English would use "her brother". The learner mistakenly uses *його* ("his") again, thinking about the brother's gender, not the owner's (Irina's). This requires drilling the concepts of "his" (`його`) vs. "her" (`її`). |
| Моя сестра має 25 років. | Моїй сестрі 25 років. | Age is expressed using the dative case (`кому?`) + number + `років/рік/роки`, not the verb `мати` (to have) as in English and other European languages. This is a fundamental structural difference. <!-- VERIFY --> |

## Деколонізаційні застереження (Decolonization Notes)
Teaching Ukrainian must be done on its own terms, completely independent of Russian. The "My World" topic is an early opportunity to establish correct, decolonized linguistic habits.

1.  **Ukrainian is Not "Russian with different letters":** The writer must NEVER use Russian as a point of comparison (e.g., "This is like the Russian word..."). This creates a false equivalency and hinders the development of authentic Ukrainian phonetics and intuition. The Ukrainian language has its own distinct history, with some words being borrowed by other languages, including Russian and Polish (Джерело: `ext-istoria_movy-10`). The goal is to build a "Ukrainian mental map" from zero.

2.  **Pronunciation without Russian Interference:** Pronunciation of names and words must be based on Ukrainian phonology. For example, the name `Давид` is pronounced with a hard `д` at the end, not devoiced to `[Давіт]` as would happen in Russian. Emphasize listening to native Ukrainian audio, not relying on transliteration or comparison.

3.  **Vocabulary Purity:** Use exclusively Ukrainian vocabulary. Avoid common Russianisms that have crept into Surzhyk (a mixed Russo-Ukrainian vernacular). For instance, use `Гаразд` or `Добре` for "okay," not the Russian `ладно`. Use `дякую` for "thank you," not `спасибі` (which, while Ukrainian, is often overused due to Russian influence and `дякую` is more common in many regions). Source `ext-imtgsh-151` discusses how Russian was used as a tool of occupation, making linguistic purity a crucial act of decolonization.

4.  **Ukrainian Names:** Always use the standard Ukrainian forms of names (e.g., `Ганна`, `Олексій`, `Дмитро`, `Христина`) and not their Russified equivalents (`Анна`, `Алексей`, `Дмитрий`, `Кристина`). This reinforces Ukrainian identity and cultural norms from the very first lesson.

## Словниковий мінімум (Vocabulary Boundaries)
This checkpoint should only test high-frequency, personally relevant vocabulary that has been introduced in A1.

**Іменники (Nouns):**
*   ***Сім'я / Родина*** (family) ★★★
*   ***Мама (or мати), тато (or батько)*** (mom, dad) ★★★
*   ***Брат, сестра*** (brother, sister) ★★★
*   ***Дідусь, бабуся*** (grandfather, grandmother) ★★
*   ***Чоловік, дружина*** (husband, wife) ★★
*   ***Син, дочка (донька)*** (son, daughter) ★★
*   ***Друг, подруга*** (friend m/f) ★★★
*   ***Робота, школа, університет*** (work, school, university) ★★★
*   ***Дім (будинок), квартира*** (house, apartment) ★★
*   ***Місто, країна*** (city, country) ★★★
*   ***Ім'я, прізвище*** (first name, last name) ★★★

**Дієслова (Verbs):**
*   ***бути*** (to be) ★★★
*   ***звати*** (to be called) ★★★
*   ***жити*** (to live) ★★★
*   ***працювати*** (to work) ★★★
*   ***вчитись / навчатись*** (to study) ★★★
*   ***любити*** (to love, to like) ★★★
*   ***мати*** (to have) ★★★

**Займенники (Pronouns):**
*   ***Я, ти, він, вона, воно, ми, ви, вони*** (I, you, he, she, it, we, you, they) ★★★
*   ***Мій/моя/моє, твій/твоя/твоє, його, її, наш/наша/наше, ваш/ваша/ваше, їхній*** (my, your, his, her, our, your, their) ★★★

**Прислівники (Adverbs):**
*   ***тут, там*** (here, there) ★★
*   ***добре*** (well) ★★

## Приклади з підручників (Textbook Examples)
The module should use activity formats that are common in Ukrainian primary and middle school textbooks. These provide authentic, pedagogically sound models.

1.  **Structured Dialogue Completion (Source `6-klas-ukrmova-betsa-2023_s0014`)**
    *   **Task:** Complete and practice a basic introductory dialogue.
    *   **Format:**
        > — Як тебе звуть?
        > — Мене звуть … .
        > — Як твоє прізвище?
        > — Моє прізвище … .

2.  **Photo Description Role-Play (Source `6-klas-ukrmova-betsa-2023_s0018`)**
    *   **Task:** Use a family photo (real or provided) to ask and answer questions about family members.
    *   **Format:**
        > — Розкажи детальніше, хто це на фото.
        > — Ось це моя мама. Її звуть Еріка Іштванівна. Вона працює лікаркою в лікарні. Праворуч від мами моя сестра Іветта. Вона студентка...

3.  **Written Narrative Prompt (Source `6-klas-ukrmova-betsa-2023_s0018`)**
    *   **Task:** Write a short, structured story based on previously practiced dialogues.
    *   **Format:**
        > Напишіть розповідь «Моя сім’я». Використайте матеріали діалогів §4–5.
        > *(This directly links the written task to the preceding spoken practice).*

4.  **Text Scramble / Structure Identification (Source `2-klas-ukrmova-kravcova-2019-1_s0119`)**
    *   **Task:** Give learners the jumbled sentences of a short personal narrative. Their task is to reorder them into a logical Зачин (Introduction), Основна частина (Main Part), and Кінцівка (Conclusion).
    *   **Format:**
        > *[Кінцівка]* Він дуже веселий.
        > *[Основна частина]* Його звати Сергій. Він працює інженером.
        > *[Зачин]* Це мій друг.
        > **Your task:** Put the sentences in the correct order to make a story.

## Пов'язані статті (Related Articles)
*   `pedagogy/a1/personal-pronouns`
*   `pedagogy/a1/possessive-pronouns`
*   `pedagogy/a1/verb-conjugation-present`
*   `pedagogy/a1/instrumental-case`
*   `pedagogy/a1/noun-gender`
*   `pedagogy/a1/vocative-case`
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
- `## Дієслова на -ся (Reflexive Verbs)` (~300 words)
- `## Мій ранок (My Morning)` (~300 words)
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
  1. **Two roommates comparing their morning routines before leaving for work**
     Speakers: Ліна, Настя
     Why: Reflexive verbs: прокидаюся, вмиваюся, одягаюся in sequence

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

**Required:** прокидатися (to wake up), вмиватися (to wash face/hands), одягатися (to get dressed), снідати (to have breakfast), йти (to go — irregular), спочатку (first, at first), потім (then, next)
**Recommended:** збиратися (to get ready), повертатися (to return), навчатися (to study/learn), поспішати (to hurry), після цього (after this), нарешті (finally), вранці (in the morning), пізно (late)

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
## Діалоги — Dialogues (~300 words total)
- P1 (~60 words): Introduction to the setting: Two roommates, Ліна and Настя, are in their kitchen on a Tuesday morning. Lina is already drinking coffee while Nastia is just starting her routine. 
- P2 (~100 words): Dialogue 1: Lina asks Nastia about her timing. Nastia explains her sequence: "Я прокидаюся о сьомій, вмиваюся, одягаюся і снідаю." Lina asks about work, and Nastia replies she leaves at 8:00 ("О восьмій я йду на роботу").
- P3 (~40 words): Linguistic breakdown of Dialogue 1: Highlighting the usage of reflexive verbs (прокидаюся, вмиваюся) to show actions Nastia does to herself, contrasted with "снідаю" (having breakfast).
- P4 (~100 words): Dialogue 2: A contrast with the weekend. Nastia asks Lina if she also hurries on Saturdays. Lina replies: "У суботу я не поспішаю. Прокидаюся пізно, лежу в ліжку, дивлюся телефон." Nastia mentions she usually studies in the morning ("навчаюся вранці").

## Дієслова на -ся — Reflexive Verbs (~300 words total)
- P1 (~70 words): Concept of "-ся": Explaining that these verbs mean the action is directed at the subject (reflexive). Examples from Karaman: "вмивати" (to wash something/someone) vs. "вмиватися" (to wash oneself). Emphasize that "-ся" is like the English "self."
- P2 (~80 words): Conjugation mechanics: How to attach "-ся" to Group I verbs. Presenting the paradigm: я вмиваю-ся, ти вмиваєш-ся, він/вона вмиваєть-ся. Note that the ending remains the same as regular verbs, just with the suffix added.
- P3 (~75 words): Crucial pronunciation rule from Kravtsova: The hidden sounds of Ukrainian. Explain that "-шся" is pronounced as a long soft [с'':а] (вмиваєшся → [вмиваєс'':а]) and "-ться" sounds like a long soft [ц'':а] (вмивається → [вмиваєц'':а]). 
- P4 (~75 words): Usage distinction: When to use reflexive vs. non-reflexive. Contrast "одягати дитину" (dressing a child) with "одягатися" (getting dressed yourself). Mention that verbs with "-ся" are always intransitive.
- <!-- INJECT_ACTIVITY: fill-in-reflexive-endings --> [fill-in, Add -ся: я вмиваю__ , ти одягаєш__ , він прокидаєть__, 10 items]
- <!-- INJECT_ACTIVITY: quiz-reflexive-choice --> [quiz, Reflexive or not? Choose: Я (вмиваю/вмиваюся) руки, 8 items]

## Мій ранок — My Morning (~330 words total)
- P1 (~80 words): The morning routine timeline. Defining "прокидатися" (the moment you open your eyes) vs. "вставати" (the moment you leave the bed). Introducing "чистити зуби" (to brush teeth) as a common non-reflexive routine phrase.
- P2 (~80 words): The irregular verb "йти" (to go). Provide the full present tense forms: я йду, ти йдеш, він/вона йде, ми йдемо, ви йдете, вони йдуть. Explain its use for leaving the house for work or study.
- P3 (~85 words): Narrative sequencing: Using adverbs to tell a story. Introduce "спочатку" (first), "потім" (then), "після цього" (after this), and "нарешті" (finally). Explain how these words turn a list of verbs into a coherent morning description.
- P4 (~85 words): Model narrative: A 5-sentence paragraph combining everything. "Спочатку я прокидаюся. Потім я вмиваюся і чищу зуби. Після цього я снідаю і п'ю каву. Нарешті я одягаюся і йду на роботу."
- <!-- INJECT_ACTIVITY: order-morning-sequence --> [fill-in, Put the morning routine in order: спочатку ___, потім ___, нарешті ___, 6 items]
- <!-- INJECT_ACTIVITY: write-morning-routine --> [fill-in, Describe your morning in 3 sentences, 3 items]

## Підсумок — Summary (~300 words total)
- P1 (~100 words): Recap of the grammar "formula": Verb Ending + -ся. Reiterate that these describe actions on oneself. Quick table for Group I: -юся, -єшся, -ється.
- P2 (~100 words): Phonetic checklist: Remind the learner of the [с'':а] and [ц'':а] sounds for the "ти" and "він/вона" forms to ensure they sound like a native speaker, not like they are reading transliteration.
- P3 (~100 words): Self-check questions for the learner to answer mentally or aloud: 
    * О котрій годині ти прокидаєшся?
    * Що ти робиш спочатку?
    * Ти п'єш каву чи чай вранці?
    * Коли ти йдеш на роботу або навчання?
    * Ти одягаєшся швидко чи повільно?

Grand total: ~1230 words
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
