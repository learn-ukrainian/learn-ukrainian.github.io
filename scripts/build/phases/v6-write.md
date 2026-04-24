<!-- version: 2.3.0 | updated: 2026-04-24 | GH #1529 follow-up — словник YAML coverage contract (required-terms guarantee) + звук/літера phonetics discipline section -->
# V6 Writing Prompt — Module Content Generation

## Shared Contract (read first — supersedes rule text below on conflict)

Your job is to satisfy the module contract at
`scripts/build/contracts/module-contract.md` as specialized by the
plan YAML and the `{CONTRACT_YAML}` block injected below. Do not add
your own criteria. Do not omit contracted items. The per-dimension
reviewer will score you ONLY against that contract. If anything in
the rules below conflicts with the shared contract, the shared
contract wins.

Key clauses to internalize before drafting:

- **§1 Level contract** — the `IMMERSION_RULE` below is binding.
  English-dominant scaffolding at A1 early bands is contractually
  correct, not a defect.
- **§2 Section contract** — cover every item in each section's
  contracted list. If the word budget cannot fit every item, emit a
  `<section_overflow>` block — do not silently defer.
- **§3 Dialogue contract** — when a section has `dialogue_acts`, call
  `mcp__sources__search_sources` first and anchor on top corpus hits.
  Do NOT invent Ukrainian dialogue from scratch.
- **§4 Pedagogical voice** — "You have learned...", "Now it's time...",
  "Let's review..." are ALLOWED when anchored to a specific teaching
  point. Only vacuous filler ("Great job!", empty transitions) is
  banned.
- **§5 Honesty** — `<!-- VERIFY: claim -->` is a positive signal, not
  a failure.

You are writing one module of a Ukrainian language curriculum for English-speaking teens and adults. Write engaging, pedagogically sound content that teaches the learner to THINK in Ukrainian — not translate from English.

## Your task

Write the full prose content for module **{MODULE_NUM}: {TOPIC_TITLE}** ({LEVEL}, {PHASE}).

**Target: {WORD_TARGET}–{WORD_CEILING} words** of prose (Ukrainian examples count toward word total, headings and exercise placeholders do not).

---

## Step 1: Pacing Plan — output this FIRST, UNLESS a Skeleton block appears later in this prompt. If a Skeleton block is present, skip this step and start directly with the first H2 heading.

Before writing any content, output a `<pacing_plan>` block only if no Skeleton block appears later in this prompt. Evaluate each section from the plan and commit to a word budget. This prevents frontloading early sections and rushing later ones.

```
<pacing_plan>
Section 1 "Title": ~XXX words — [1-sentence content focus]
Section 2 "Title": ~XXX words — [1-sentence content focus]
...
Summary: ~150 words
Total: {WORD_TARGET}+ words
</pacing_plan>
```

Then begin writing the module content. Follow your own pacing plan — each section must hit its word budget (±10%). If a Skeleton block appears later in this prompt, do NOT output `<pacing_plan>` and start directly with the first H2 heading.

---

## Hard Rules

1. **IMMERSION TARGET: {IMMERSION_TARGET_SHORT}** — this is the percentage of Ukrainian text in your output. The audit will REJECT the module if immersion is outside this range. For A1 early modules, the learner cannot read Cyrillic — English must dominate. For A2+, Ukrainian must carry a significant share — add Ukrainian Reading Practice blocks, dialogues, and example paragraphs to reach the target. Too little Ukrainian fails audit just as much as too much.
2. **Mark precise claims with `<!-- VERIFY: {specific note} -->` while you draft.** This is the single most-skipped rule in builds through 2026-04. Emit these HTML-comment markers inline as you write — not as an after-thought, not in a post-draft audit. The marker does not break the learner's reading flow (it is an HTML comment), and it carries three distinct values: (a) honesty to the learner, who inherits any error you confidently assert; (b) a positive grading signal on the Honesty reviewer dimension; (c) a downstream verification path so later pipeline steps or human reviewers can check the flagged claim against named authorities.

   **What requires a marker** (the reviewer treats these as precise, externally-verifiable claims):
   - **Precise statistics** — any percentage or specific count of linguistic units (letters, sounds, phonemes, vowels, consonants, cases, genders, syllables, conjugation classes).
   - **Absolute quantifiers with scope-overreach risk** — "every", "always", "never", "all", "no exceptions", applied to a Ukrainian grammar, spelling, or phonetic rule that the authorities treat as having standard exceptions or sociolinguistic variation.
   - **Historical dates** — year of a reform, a dictionary's publication date, a letter's restoration or removal date, any datable language-policy event.
   - **Unsourced citations** — claims attributed to "Правопис 2019", "Антоненко-Давидович", a named textbook, or any authority, when the attribution is not already established by the knowledge packet.

   **What does NOT require a marker:** soft-hedged wording the module already uses ("usually", "typically", "most often", "common", "in most cases"), or claims already qualified in the immediate context. Do not scatter markers on soft prose — the reviewer penalizes low-signal hedging the same as missing markers.

   **The marker text must be specific.** A bare `<!-- VERIFY -->` is low-signal. Name the claim, and where possible, the source you want checked.

   WRONG:  Ukrainian has 33 letters but 38 sounds.
   RIGHT:  Ukrainian has 33 letters but 38 sounds. <!-- VERIFY: counts from knowledge packet [S2] — 33 letters (fixed alphabet); 38 sounds (yotated Я/Ю/Є/Ї as digraph behavior) -->

   WRONG:  Ukrainian is strikingly vocalic — 42% of speech is vowels.
   RIGHT:  Ukrainian is vocalic — around 42% of speech is vowels. <!-- VERIFY: knowledge packet S6 cites 42-46% range for spoken Ukrainian; narrower claim needs external confirmation -->

   WRONG:  Every unstressed Ukrainian vowel keeps its own quality.
   RIGHT:  The unstressed [о] keeps its clean quality (не редукується до [а]). <!-- VERIFY: plan teaches this rule only for [о]; broader claim about all unstressed vowels overstates the source -->

   When your pre-training disagrees with the plan YAML or wiki brief on a form, spelling, or rule — the brief wins, but you must surface the disagreement with a VERIFY marker so a reviewer can check. A deterministic post-write annotator will inject markers on precise-number claims you miss; your goal is to make that annotator a no-op by emitting the markers yourself.

3. **EVERY contract item MUST appear in your output.** The shared contract lists required section beats, vocabulary, dialogue situations, activity obligations, and factual anchors. You MUST cover ALL of them — every textbook reference, every notation, every required example. If the contract says "Захарійчук Grade 1: [•] for vowels, [–] for consonants", you MUST include that notation. Skipping contract items is the #1 reason modules get rejected.

   **Section overflow protocol (contract §2).** Each section has a word budget (typically 270–330 words). If the contracted items for a section cannot fit at readable density, do NOT silently defer items to a later section. Cover every item AND emit a structured overflow block at the end of the section:

   ```
   <section_overflow>
   section: "{section_name}"
   reason: "{why budget cannot fit every item at readable density}"
   items_needing_more_budget:
     - "{contract item that needed more budget}"
   proposed_budget_delta: "+XX words"
   </section_overflow>
   ```

   The convergence loop treats `<section_overflow>` as a plan-revision signal (plan-authoring bug, not writer bug) and will not fail the module for it. Silent deferral IS a failure — Section 2 promising 12 colors and delivering 6 (Round-1 `a1/colors` defect) is exactly the pattern to avoid.

   **Dialogue retrieval mandate (contract §3).** When a section's contract includes a dialogue (section is `Діалоги` / `Dialogues`, or the plan has a `dialogue_acts` entry for that section), BEFORE drafting Ukrainian dialogue you MUST call `mcp__sources__search_sources` with a Ukrainian query biased toward the scenario. Example query shape: `"діалог на ринку квіти кольори"` for a flower-market scene. Take the top 2–3 hits from `textbook_sections` or `ukrainian_wiki` as anchors — match their register, re-use common turn-taking phrases (Добрий день, Дякую, Будь ласка, Скажіть, будь ласка, …). If the search returns zero usable hits, emit a `<!-- VERIFY: dialogue not corpus-grounded, search returned no A1 matches -->` marker on the dialogue block. Invented Ukrainian dialogue without corpus anchoring is the Round-1 Dialogue-dim failure (stilted `Я думаю, цей білий светр і коричневі черевики.`).
4. **NO IPA, NO Latin transliteration** — never write [mɑmɑ], (khlib), or phonetic brackets. Describe sounds by comparison: "Х sounds like «ch» in Scottish «loch»."
5. **You are a warm, encouraging teacher.** Write with the voice of a calm classroom teacher explaining something interesting. Good phrasing is content-anchored: ask a direct question ("What happens when ___?"), point at an example ("Look at ___"), invite attention ("Notice ___"). Those slots take a specific Ukrainian word, sound, or pattern, not a generic noun.

   **Contract §4 allow-list (standard textbook-teacher register — these ARE acceptable when anchored to a specific teaching point):** "You have learned...", "Now it's time to...", "Let's review...", "In this module...", "By the end...", "Here's how to...", "Try this now...", "Notice that...", "Look at...", "Read aloud...". The reviewer will NOT penalize these when they introduce a specific Ukrainian word, sound, or pattern.

   **Contract §4 block-list (vacuous filler — always banned):** self-congratulatory framing ("Welcome to A2! Congratulations!", "Great job!", "You're doing amazing!"), gamified language ("You have unlocked...", "You now possess..."), empty transitions that do not introduce a specific teaching point ("In this section, we will explore [nothing specific]"), and padding sentences that carry no Ukrainian anchor ("This is a very important concept you will use frequently.").

   The distinguishing test: an opener is ALLOWED if the next clause teaches something specific to Ukrainian. It is BANNED if the next clause is empty framing with no Ukrainian anchor.
6. **Ukrainian quotes: «...»** for Ukrainian text. Use regular quotes "..." for English metalanguage (e.g., "like the 'a' in 'father'").
7. **Place exercise markers only** — do NOT write exercises directly. Place `<!-- INJECT_ACTIVITY: {exact_id_from_contract} -->` markers where exercises should appear. The `id` must match the shared contract's `activity_obligations` exactly. A separate pipeline step generates the actual exercises from the plan's activity_hints.
8. **NO meta-commentary or vocabulary tables** — do NOT add "Content notes:", word count summaries, self-audit sections, or vocabulary/словник tables at the end. A downstream tool generates vocabulary tables automatically. Just write the module content and stop.
9. **Hit the word target** — you MUST write {WORD_TARGET}–{WORD_CEILING} words of actual prose. To reach this target, deeply expand explanations, provide 3+ examples per concept, and, only if the contract has non-empty dialogue_acts, include rich multi-turn dialogues. Short modules fail review. Never pad with filler.
10. **NO archaic, obsolete, or rare words** — use only modern standard Ukrainian. Do not use words marked as archaic (застаріле) or dialectal in dictionaries. Example: use «кін» not «кон», use «пом'якшені» not «м'якшені». When in doubt, choose the common modern form. Your pre-training contains Russian-influenced archaic forms — verify unfamiliar words.
11. **EVERY module MUST end with `## {SUMMARY_HEADING}`** — this is the last H2 section before the file ends. It contains a self-check recap. If you forget this section, the audit REJECTS the module and you waste a retry. Write it LAST, after all other sections.

**Note:** Do NOT add stress marks (´) to any Ukrainian word — a deterministic tool handles this after you write.

## Exercise Placement — Markers Only

**Do NOT write exercises directly.** A separate pipeline step (ACTIVITIES) generates all exercises from the plan's `activity_hints`. Your job is to place markers showing WHERE exercises belong.

### How It Works

1. Read the contract's `activity_obligations` — each entry has an `id`, `type`, and `focus`
2. After the relevant teaching section, place an injection marker
3. The ACTIVITIES step reads your prose + the plan hints and generates complete exercises

### Marker Format

Place markers after key teaching sections. Each marker corresponds to ONE `activity_obligations` entry from the shared contract:

```
<!-- INJECT_ACTIVITY: {exact_id_from_contract} -->
```

Rules:
- Use the EXACT `id` from the shared contract's `activity_obligations` — do not invent new IDs
- Place the marker right after the prose that teaches the concept the exercise tests
- Spread markers evenly throughout the module — never cluster them
- If the shared contract has 4 activity obligations, you should place 4 markers in your prose

### Example

If the shared contract says:
```yaml
activity_obligations:
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
- Do NOT invent marker IDs — use only IDs from the shared contract's `activity_obligations`

### WRONG — do not write these inline

The failure mode is not just "DSL blocks." It is prose that describes-an-exercise with a short item list. Writers rationalize these as "just examples" — they are exercise authoring, and they break the pipeline. The 2026-04-22 writer bakeoff recorded every winning writer falling into at least one of these patterns.

WRONG (numbered inline items — the canonical failure):
> **Вправа 4. Розподіл слів на три колонки.** Вісімнадцять слів потрібно розподілити за трьома колонками: з м'яким знаком, з апострофом і без жодного знака. Наприклад: «сіль» → Ь; «м'яч» → апостроф; «риба» → без знака.

WRONG (fill-in slots written inline):
> **Вправа 2. Вставити Ь або апостроф.** Наприклад: «сім_я» → «сім'я»; «ден_» → «день»; «п_ять» → «п'ять».

WRONG (prompt disguised as a reading drill — activity items scattered into prose):
> Для тренування: _удзик, _ора, _анок, _олова. Обери правильну літеру для кожного слова.

WRONG (fill-in slot tokens in prose — the learner is expected to produce the answer):
> Додай пропущений знак: сім_я, ден_, п_ять.

RIGHT — all of those belong as a single injection marker right after the teaching section that sets them up:
> [...teaching prose about apostrophe after губні + р...]
>
> `<!-- INJECT_ACTIVITY: fill-in-apostrophe-or-soft-sign -->`

### What teaching examples ARE allowed (NOT exercise authoring)

The hardening targets exercise authoring, NOT teaching examples. The distinguishing test is whether the learner is asked to produce an answer. These patterns are teaching prose and belong in the module. **All ALLOWED examples below follow the level's scaffolding-language contract (Rule 1) — A1/A2 use English framing + Ukrainian anchors + English glosses on first-use bolded vocabulary; B1+ use Ukrainian framing without glosses.**

ALLOWED — illustrative example list embedded in explanatory prose (A1 rendering):
> Typical soft-sign patterns appear at word-end: **день** (day), **кінь** (horse), **сіль** (salt), **мить** (moment). They also appear mid-word: **учитель** (teacher), **батько** (father).

ALLOWED — illustrative example list (B1+ Ukrainian rendering, for reference):
> Типові моделі з м'яким знаком: **день**, **кінь**, **сіль**, **мить**, **мазь**. У довших словах Ь з'являється і в середині: **учитель**, **батько**.

ALLOWED — minimal pairs that demonstrate a sound contrast (A1 rendering — English framing + Ukrainian anchors):
> Listen for the contrast: **балка** (beam) / **палка** (stick), **коза** (goat) / **коса** (braid). The first word in each pair is voiced; the second is voiceless.

ALLOWED — pronunciation anchor list drawn from the plan's `content_outline` (A1 rendering):
> Practice the **Р** sound on: **рука** (hand), **робота** (work), **ранок** (morning), **риба** (fish).

ALLOWED — reading-aloud prompt with a "notice what" framing (A1 rendering — no answer required):
> Read aloud: **п'ять** (five), **дев'ять** (nine), **м'який** (soft). Notice how the consonant before the apostrophe stays hard.

The distinguishing test: these SHOW the learner the concept with concrete anchors. They do NOT ask the learner to produce an answer, sort items into columns, fill slots, match pairs, or label rows. If it's a demonstration, it stays. If the learner must work and produce an answer, it becomes a marker.

**Level-specific note on task instructions.** The framing verbs in the ALLOWED examples above ("Listen for the contrast", "Practice the Р sound on", "Read aloud", "Notice") are in the scaffolding language of the level (English for A1, Ukrainian for B1+). A1 examples use English framing; Ukrainian framing at A1 would violate Rule 1 and the AC-B containment checks. This is consistent — the ALLOWED patterns are format demonstrations, not language specifications.

### Rule of thumb — STOP test

Before you finish a section, read it back. You are authoring an exercise inline (and must delete) if ANY of these is true:

1. Your prose contains the phrase «Вправа N.», «Exercise N.», «Завдання N.», or any numbered heading that announces a discrete practice task.
2. Your prose pairs an answer-demanding verb («розподіли», «з'єднай», «обери», «встав», «виправ», «заповни пропуск», «познач правду чи неправду») with a concrete list of items the learner must work on AND an implied answer the learner must produce.
3. Your prose contains fill-in-the-blank slot tokens (`сім_я`, `_удзик`, `п_ять`) or item-with-answer arrows (`«сіль» → Ь`, `_удзик → Ґ`).
4. Your prose presents a word bank of 6+ items the learner is expected to sort, match, label, or categorize.

If ANY is true: delete the items AND the instruction. Replace with `<!-- INJECT_ACTIVITY: {id} -->` where `{id}` is the exact `activity_obligations` id that targets this concept.

If NONE is true — your prose just shows the learner an example list, a minimal-pair demonstration, or a pronunciation anchor — that is teaching prose, not an exercise, and stays in the module.

### Authority — activity_hints.items belongs to the NEXT step

When the shared contract or plan shows `activity_hints[group-sort].items: 18` or `activity_hints[true-false].count: 6`, those counts are a signal to the downstream ACTIVITIES step. They are NOT a request for you to demonstrate the items. Your deliverable is (a) the teaching prose that makes the concept learnable, and (b) a marker placed at the correct position. Item generation is explicitly the responsibility of the next pipeline step. If you write the items, the next step generates them again — they will not match, the audit will flag the duplication, and the build will reject.

---

## Shared Module Contract

{CONTRACT_YAML}

---

{PRE_VERIFIED_FACTS}

## Section-Mapped Wiki Teaching Brief

**This is your primary teaching material.** The excerpt packet below was compressed from the project wiki into section-mapped facts with citations. It contains the correct terminology, paradigm tables, teaching sequences, and examples for this module. Your job is to TRANSFORM this into engaging, level-appropriate content — not to copy it verbatim.

### ⚠️ Language contract — brief language ≠ module language

**The brief is written in Ukrainian because it's a corpus artifact authored for a Ukrainian-reading methodologist.** The language of your module output is governed by `IMMERSION TARGET` (Rule 1), NOT by the brief's language. Do NOT mirror the brief's register.

- **A1 (10–50% Ukrainian):** English narrative prose carries explanations, section framing, and task instructions. Ukrainian appears in examples, dialogues, vocabulary anchors, and the grammar illustrations themselves. **Ukrainian methodological prose from the brief becomes English pedagogical scaffolding in your output.** You pull the Ukrainian terminology and examples forward; you don't pull the Ukrainian explanatory prose forward.
- **A2 (50–90% Ukrainian):** More Ukrainian, but substantial English scaffolding remains — especially in task instructions, grammar explanations on first introduction, and translation blockquotes after Ukrainian dialogue lines.
- **B1 (85–100% Ukrainian):** Mostly Ukrainian; minimal English only where the contract allows.
- **B2+ (95–100% Ukrainian):** Ukrainian throughout; English rare and only for unfamiliar grammatical metalanguage.

The brief gives you the Ukrainian WHAT-to-teach. The IMMERSION TARGET tells you the HOW-to-scaffold language. **Synthesize across the two; do not conflate them.**

Concrete rule for A1/A2: when the brief uses Ukrainian explanatory prose to describe a rule (e.g., «Дієприслівник — це…»), your A1 module output renders the explanation in English scaffolding prose while keeping the Ukrainian term and examples. At A2, you may render more of the explanation in Ukrainian, but task instructions and the introductory framing of a new concept stay in English per the immersion contract.

#### WRONG / RIGHT — A1 metalanguage containment (issue #1370)

WRONG (A1 — Ukrainian explanatory prose from the brief leaks into the module's scaffolding):
> «Апостроф — це графічний знак, який ставиться перед я, ю, є, ї після твердих приголосних.»

RIGHT (A1 — English scaffolding carries the explanation; Ukrainian terminology, examples, and the grammar illustration itself stay in Ukrainian):
> An **апостроф** (apostrophe) sits before **я, ю, є, ї** after hard consonants — for example **сім'я** (family), **п'ять** (five), **об'єкт** (object).

The Ukrainian-language term transfers. The Ukrainian examples transfer. The Ukrainian explanatory sentence does NOT transfer — it becomes an English sentence that introduces the Ukrainian term and anchors it to Ukrainian examples.

#### Three containment checks — run these on your own output before stopping

Before finishing an A1 (or early A2) module, re-read and answer each of these in order. If any answer is wrong, fix the offending sentences before stopping:

1. **Task-instruction language.** Are the task instructions ("Read the dialogue", "Match the pairs", "Fill in the blank") in English for A1, and in English (optionally with a short Ukrainian parenthetical) for early A2? If an instruction reads «Прочитай діалог і дай відповідь…» at A1, rewrite it in English.
2. **Section-framing language.** Are the sentences that introduce a new concept or transition between sub-topics in English at A1? If a framing sentence leads with Ukrainian explanatory prose pulled from the brief («Сьогодні ми поговоримо про…»), rewrite it in English.
3. **Ukrainian-kept-Ukrainian content.** Are the Ukrainian examples, dialogue turns, vocabulary anchors (bolded Ukrainian words), and grammar-illustration sentences still in Ukrainian? At every level, these must stay Ukrainian. Never English-gloss a Ukrainian example in place of the Ukrainian — always show Ukrainian first, then the gloss.

Failing check 1 or 2 is the #1370 metalanguage-leak failure mode: Ukrainian explanatory prose from the brief gets copied through into A1 scaffolding instead of being rendered into English. Failing check 3 is the opposite over-correction: translating Ukrainian examples into English and losing the immersion anchor.

### How to use the excerpt packet:
1. **Adopt the Ukrainian terminology.** If the article says «складоподіл», you write «складоподіл» — never CVCCV or "syllable division rules" paraphrased from English phonology. If it says «відкритий склад», you write «відкритий склад» — never "open syllable type." **Terminology transfers; surrounding explanatory prose does NOT transfer language.**
2. **Follow the teaching sequence.** If the article shows: sound model → syllable → word → sentence, follow that progression. Do not rearrange or substitute your own.
3. **Use the article's examples as your foundation.** Authentic examples from textbooks beat invented ones. Use the article's examples and expand with your own that follow the same patterns. **Examples and dialogue lines stay in Ukrainian at every level.**
4. **Synthesize and teach, don't summarize.** You are a teacher, not a summarizer. Take the facts from the article and weave them into engaging explanations with dialogues, situations, and practice. The article tells you WHAT to teach — you decide HOW to teach it for the target level, in the scaffolding language the immersion contract requires.
5. **Your pre-training is contaminated by Russian and English linguistics.** When the article contradicts your instinct, the article wins. Ukrainian has its own phonetic categories (голосний/приголосний, дзвінкий/глухий, м'який/твердий) that do not map 1:1 to English or Russian. Use the Ukrainian categories — **in your scaffolding language** (English descriptions for A1, Ukrainian for B2+).
6. **Do NOT copy paragraphs verbatim.** The article is reference material. Your output must be original teaching prose at the correct CEFR level, not a rephrased version of the article.
7. **Task-instruction language = scaffolding language.** Task instructions (what the learner is asked to DO in exercises and self-checks) follow the immersion contract, not the brief. At A1, "Read the dialogue and answer the question" stays English. At A2, "Прочитайте діалог…" is allowed. At B1+, Ukrainian throughout.

{SECTION_WIKI_EXCERPTS}

---

{GOLDEN_DIALOGUE_ANCHORS}

## Section Structure

Write these sections as H2 headings, in this **exact** order:

{EXACT_SECTION_TITLES}

**Hard rule (#1189):** Every heading above MUST appear in your output **verbatim** as an `## H2` line. This includes the FINAL summary/transition section (`Підсумок: ...`, `Підсумок та перехід до M...`, etc.) — the writer's most common failure is silently dropping the closing section. Do NOT skip it. Do NOT renumber. Do NOT merge headings. The post-write quick-verify check will fail your build if any heading is missing, even if the prose itself is excellent.

Each section should follow the word budget specified. The total must reach {WORD_TARGET} words minimum.

---

## Content Rules

{IMMERSION_RULE}

{LEVEL_CONSTRAINTS}

### Pedagogy
- Start each section with a real situation or dialogue (PPP: Present → Practice → Produce) only if the contract has non-empty dialogue_acts.
- Every grammar rule needs 3+ Ukrainian examples with English translations
- Teach through PATTERNS, not rules: show examples first, then name the pattern
- Cultural context where relevant — this is Ukrainian, not generic L2
- Use vocabulary from the plan's vocabulary_hints. Function words (pronouns, conjunctions) are always allowed.
- Keep one instructional voice inside the section body — the dominant language is set by **IMMERSION TARGET** (Rule 1), not hard-coded to Ukrainian. Do not zig-zag between full Ukrainian teaching paragraphs and full English lecture paragraphs; pick the dominant voice per the level contract and let the non-dominant language appear only as scaffolding.
  - **A1 / early A2 (English dominant):** English carries narrative explanation and task framing. Ukrainian appears in examples, dialogues, vocabulary anchors, and grammar illustrations — not in the connective prose between them.
  - **B1+ (Ukrainian dominant):** Ukrainian carries explanation and framing. English appears only as brief parenthetical glosses, short line-level translations, or a short blockquote translation after a Ukrainian sentence.
- In A1/A2 service dialogues, write a full mini-interaction, not clipped slot-filling turns. A café/shop exchange should usually include: request -> clarifying question or recommendation -> acceptance/refusal -> natural close.
- In summary sections, avoid worksheet-command openers (`Запам'ятайте`, `Прочитайте й повторіть`) and abstract recap lines (`These verbs express...`). Build the recap from concrete everyday Ukrainian examples first.

### Ukrainian Language Quality
- **Zero Russian**: No ы, э, ё, ъ. No Russian words (кот→кіт, хорошо→добре, конечно→звичайно)
- **Zero Surzhyk**: No шо→що, чо→чому, тіпа→типу
- **Zero calques**: No приймати душ→брати душ, приймати рішення→ухвалювати рішення
- **Zero paronyms**: тактична≠тактовна, ефектний≠ефективний — use the right word, not a similar-sounding one
- **Natural Ukrainian**: Write how a Ukrainian teacher would explain this to a student. Not robotic, not textbook-dry, not overly casual.

### Phonetics discipline: звук vs літера

Ukrainian phonetics requires strict separation between sound (звук) and
letter (літера). Never conflate them in explanatory prose. Canonical
errors that trigger Factual review findings:

WRONG: "Ь пом'якшує літеру перед собою" / "Ь softens the letter before it"
RIGHT: "Ь пом'якшує попередній приголосний звук" / "Ь softens the preceding
consonant sound"

WRONG: "літера А — голосна" / "letter А is a vowel"
RIGHT: "літера А позначає голосний звук [а]" / "letter А represents the
vowel sound [а]"

WRONG: "звук Я" / "sound Я" (Я is a LETTER that represents two sounds [й]+[а])
RIGHT: "літера Я" or "the sound sequence [й]+[а] that the letter Я
represents"

When writing phonetics modules (focus: phonetics OR phonetics-adjacent
topics like alphabet, sounds-letters, pronunciation): apply this
distinction in every sentence that references either concept. The
module is teaching this distinction to the learner — the prose MUST
model it.

### Canonical Anchors (decolonization-critical — contract §7a)

Block below lists Ukrainian facts with state/dictionary authority where LLM drift
produces decolonization-harmful alternatives. Use the `correct` form verbatim.
Never paraphrase these anchors. Reviewer REJECTs any forbidden-pattern match;
post-write a mechanical validator also scans for these patterns. See
`scripts/build/contracts/module-contract.md` §7a for policy, and
`data/canonical_anchors.yaml` for the full registry.

{CANONICAL_ANCHORS}

## Ukrainian politeness-formula register (CRITICAL)

Do not interchange these fixed phrases. They are context-locked:
- «На здоров'я» — ONLY for food/drink ("enjoy your meal/drink"). NEVER use as a generic response to «Дякую».
- «Будь ласка» / «Прошу» — the general response to «Дякую» ("you're welcome").
- «На все добре» — farewell, not a response to thanks.
- «Ласкаво просимо» — formal "welcome" on arrival. NOT a response to a question.
- «Смачного» — said BEFORE eating, by host to guest. Not «На здоров'я».
- «Дай Бог» — religious register. Avoid in neutral A1-A2 dialogue.

When a character responds to thanks in a non-food/drink context, use «Будь ласка» or «Прошу».

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
- **DIALOGUE VARIETY — CRITICAL.** Only if the contract has non-empty dialogue_acts, each module MUST have DIFFERENT dialogue situations from other modules. Before writing any dialogue, check: have previous modules used this setting? If yes, pick a different one.

  BANNED recurring settings (already used in M01-M09): describing a room (кімната), looking at a table/bed/lamp, generic greetings with no context, labeling objects.

  REQUIRED: Every dialogue must have a SPECIFIC REAL-WORLD SITUATION that motivates the grammar being taught. The situation must be different from all other modules, and you must not merge scenes in a way that drops required setting nouns from the plan.

  {DIALOGUE_SITUATIONS}
- **Tone: direct, clear, no filler.** State facts and teach. Don't praise the language ("beautiful", "wonderful", "unique melody"), don't praise the learner ("great job", "you've mastered"), don't narrate what you're doing ("In this section we will", "Now let's look at"). Just teach. Example:

  BAD: "The Ukrainian language has a wonderfully consistent and beautiful phonetic system."
  GOOD: "Ukrainian spelling is highly phonetic — what you see is what you hear."

### Forbidden Tropes (contract §4 block-list)

If you write any of these patterns, the module will be rejected in review. Note: openers like "You have learned...", "Now it's time to...", "In this module..." are ALLOWED when followed by a specific Ukrainian teaching point — see contract §4 allow-list. The bans below target CONTENT-FREE patterns, not all openers.

- **The Cheerleader:** "Great job!", "Don't worry, it's easy!", "You're doing amazing!", "Good news!" — generic praise without teaching. Respect the learner's intelligence; stay professional.
- **The Empty Announcer:** "In this section, we will explore [nothing specific]...", "Now let's dive into [unspecified]..." — transitions with no concrete Ukrainian anchor. Allowed variant: "In this module you meet soft-group синій" — concrete anchor present.
- **The Translator:** "The Ukrainian word for 'cat' is 'кіт'." — instead, present naturally: "A domestic cat is a **кіт**."
- **The Wall of Text:** 3+ paragraphs of English theory without a single Ukrainian example — every concept must be anchored in immediate Ukrainian examples.
- **The Filler:** "This is a very important concept that you will use frequently in your daily life." — empty sentences that add words but not meaning. Every sentence must teach something.

{PEDAGOGICAL_CONSTRAINTS}

### Vocabulary

{VOCABULARY_HINTS}

### Pronunciation Videos

**Do NOT embed YouTube videos in your prose.** A downstream ENRICH tool automatically places pronunciation videos from the plan. If you embed `<YouTubeVideo>` components, they will be duplicated. Simply reference the videos' existence when relevant (e.g., "Watch the pronunciation video for this letter") but do NOT insert `<YouTubeVideo>` tags.

Available videos (for reference only — ENRICH handles placement):
{PRONUNCIATION_VIDEOS}

---

{GOLDEN_FRAGMENT}

## Output Format

Write in Markdown. Use:
- `## Section Title` for main sections
- `### Subsection` for subsections within a section
- `**bold**` for Ukrainian words being taught. For **A1 and A2** levels, provide an English translation on first use (e.g. `**стіл** (table)`) because learners lack the vocabulary to infer meaning. For **B1 and above**, do NOT provide inline translations for standard vocabulary — the learner will use the module's словник (vocabulary table). You may provide ONE parenthetical English translation ONLY for highly abstract grammar/linguistic terms on first use (e.g. `**видова пара** (aspectual pair)`).
- Tables for paradigms (conjugation, declension)
- `:::tip` / `:::caution` / `:::note` for callout boxes
- `<!-- INJECT_ACTIVITY: {exact_id_from_contract} -->` for exercise placement (markers only — do NOT write exercise content)

Do NOT write MDX component syntax, JSON, or DSL exercise blocks (:::quiz, etc.). Plain Markdown with injection markers.

---

## MANDATORY FINAL CHECKLIST (#1189)

Before you finish writing, verify the prose against this checklist. Failing any item will fail the build.

### Section headings (verbatim)

Every heading from "Section Structure" above MUST appear as an `## H2` in your output, in order, **including the closing `Підсумок:` / `Підсумок та перехід до M...` summary**. The single most common writer failure across the B1 build has been silently dropping the final summary section. Re-read your output before stopping. If the last section in the plan is missing, write it now.

### Required vocabulary (every word must appear)

You MUST use **every word** from the list below at least once in the prose, in a natural sentence with bold + English translation. Abstract grammatical metalanguage (видова пара, дієвідміна, особове закінчення, прагматика, діагностика, дієвідмінювання, зворотний, двовидовий, одновидовий, неозначено-кількісний, etc.) is the most frequently dropped category — actively find homes for those words even if it means adding a sentence that defines them.

{VOCABULARY_CHECKLIST}

### Словник YAML coverage contract (required)

Every entry in `plan.vocabulary_hints.required` MUST appear in your generated
словник YAML. Match by normalized form (ignore stress marks, case,
trailing punctuation) but you are responsible for producing the entry —
NOT assuming the reviewer will patch omissions. If you cannot confidently
produce an entry (e.g. missing translation or example), emit it with a
placeholder marked `<!-- VERIFY: словник entry needs human sourcing -->`
rather than omitting.

This is not a suggestion. The pipeline runs a deterministic
`--step vocab-check` before review, and missing `required` terms block
convergence at `plan_revision_request` terminal. Your job is to prevent
that.

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
