<!-- version: 1.4.1 | updated: 2026-04-25 | example de-poisoning — concrete Ukrainian words in format examples replaced with abstract placeholders to stop the model from copying them into output (#1550 U8) -->
# V6 Activity Generation — Structured YAML for Inline + Workbook Exercises

You are generating structured exercise YAML for a Ukrainian language module. The exercises will be injected into the lesson tab (inline) and workbook tab (workbook) of the module.

## Your Task

Generate an `activities/{MODULE_SLUG}.yaml` file for module **{MODULE_NUM}: {TOPIC_TITLE}** ({LEVEL}).

**CRITICAL: Output ONLY raw YAML.** Your very first character must be `version:`. No markdown, no commentary, no explanation, no file paths, no "Here is the YAML", no code fences. Just the YAML document starting with `version: "1.0"`. ANY text before `version:` will cause a parse failure.

---

## ⚠️ HARD COUNT TARGETS — READ TWICE

These are the binding numerical contracts for THIS module. The audit will FAIL if you fall short.

| Bucket | Min | Max | Notes |
|---|---|---|---|
| Total activities | {TOTAL_TARGET} | {TOTAL_TARGET}+ | inline + workbook combined |
| Inline (lesson tab) | {INLINE_MIN} | {INLINE_MAX} | exactly one per `<!-- INJECT_ACTIVITY -->` marker, see below |
| Workbook (Зошит tab) | {WORKBOOK_MIN} | {WORKBOOK_MAX} | extended practice |
| Items per activity | {ITEMS_MIN} | — | each activity must have at least {ITEMS_MIN} items (unless its type cap is lower — see Activity Type Reference below) |

**Inline activity count: exactly {INLINE_MIN}.** The writer placed {INLINE_MIN} injection marker(s), and each marker needs exactly one inline activity with the matching `id`.

**You MUST ship exactly {INLINE_MIN} inline activities AND at least {WORKBOOK_MIN} workbook activities.** Going under either is a hard failure — the audit gate enforces it and the build will reject your output.

**Type diversity is required.** The module (inline + workbook combined) MUST use at least **{MIN_TYPES_UNIQUE}** distinct activity types — do NOT ship a wall of the same type. As a quality target, quiz + true-false combined should be NO MORE than ~25% of the workbook (i.e. lean on the priority types below, not on easy multiple-choice). Use the `WORKBOOK_PRIORITY_TYPES` list below; those carry the most weight at this level.

<letter-module-exception>
Plan `letter_module` active: {LETTER_MODULE_ACTIVE}.

If the plan declares `letter_module: true`, the activity-count and type-diversity caps for the level are SOFT — the module may exceed them. Letter modules legitimately need ~33 letter-recognition items plus standard activity types. Do NOT cap below the level of letter coverage required by the plan.

Audit gates must treat `letter_module: true` modules as exempt from activity-count MAX warnings. Unit 4 (audit config sweep) wires this. The activity_count MIN still applies — letter modules cannot have FEWER activities than the level minimum.

Word-count target is UNCHANGED for letter modules. Prose length expectations are level-standard.
</letter-module-exception>

---

## Allowed types for THIS level

- **Inline (lesson) types:** {INLINE_ALLOWED_TYPES}
- **Inline priority (preferred):** {INLINE_PRIORITY_TYPES}
- **Workbook types:** {WORKBOOK_ALLOWED_TYPES}
- **Workbook priority (preferred):** {WORKBOOK_PRIORITY_TYPES}
- **FORBIDDEN at this level:** {FORBIDDEN_ACTIVITY_TYPES}

Pick from the allowed list. Lean heavily on the priority lists. Do not use any forbidden type — the build will reject it.

---

## Inline vs Workbook Split

Activities have two placement categories:

1. **inline** — short, focused exercises placed directly in the lesson (Урок tab) at specific injection points. The writer has placed `<!-- INJECT_ACTIVITY: {id} -->` markers in the prose. Each inline activity MUST have an `id` that matches one of these markers.

2. **workbook** — extended practice exercises in the workbook (Зошит tab). These do NOT need ids.

**Rule of thumb:** inline = exactly {INLINE_MIN} quick checks after key teaching points. Workbook = {WORKBOOK_MIN}–{WORKBOOK_MAX} deeper practice exercises covering the full topic. **Every inline marker in the prose MUST have a matching inline activity** — that is what determines `INLINE_MIN`, so do NOT skip markers.

---

## Injection Markers in the Prose

The writer placed these markers in the module content. Your inline activities must match them:

{INJECTION_MARKERS}

Each inline activity's `id` must match one of these markers exactly (lowercase, hyphenated).

---

## Plan Activity Hints

The plan specifies these exercises to create:

{PLAN_ACTIVITY_HINTS}

You MUST create activities that cover all these hints. Distribute them between inline and workbook as appropriate: focused checks go inline, extended practice goes to workbook.

---

## Plan Vocabulary

These words are the module's vocabulary foundation. ALL exercise items must use words from this list or from the prose:

{PLAN_VOCABULARY}

**Grounding rule:** Every Ukrainian word in your exercises must appear either in the prose content or in this vocabulary list. Do NOT invent new words the learner hasn't seen.

<retry-feedback>
{UNGROUNDED_FEEDBACK}
</retry-feedback>

<required-vocab-coverage>
Every entry in the plan's `vocabulary_hints.required` list MUST appear in at least one activity. Coverage is mandatory at 100%.

At generation time, verify: for each required-vocab item, find at least one activity whose `prompt`, `correct_answer`, or `options` contains the lemma (case-insensitive, after normalization).

If a required-vocab item is not testable within the level's allowed activity types, escalate via `plan_revision_request` rather than silently dropping it.
</required-vocab-coverage>

<strict-grounding>
<no-example-words>
The format examples in THIS prompt use placeholder tokens like `<UKR_1>`
because the activity validator REJECTS any Ukrainian word in your output
that does not appear in the prose or in `PLAN_VOCABULARY`. NEVER copy a
Ukrainian word from this prompt's format examples into your activity
items. The placeholders mark the SHAPE of the data; the words you put
there must come from the module's prose or the plan's vocabulary list,
not from this prompt.

If a placeholder cannot be filled with a prose-grounded or
plan-vocabulary-grounded word for a given activity type at this level,
DROP the activity and pick a different type from the allowed list. Do
not fall back to "common A1 words" the model knows — those are exactly
the words the validator will reject.
</no-example-words>

Every activity MUST be answerable from the prose alone. Before emitting an activity, verify:
1. The activity's correct answer is a lemma, phrase, or fact that appears in the prose (or in standard linguistic knowledge for grammar-mechanics drills).
2. Any keyword referenced (e.g., names, dates, terms) appears in the prose verbatim or as a clearly inflected form.

If grounding fails, drop the activity rather than emit a context-gap.
</strict-grounding>

---

## Module Content (the prose the learner reads before exercises)

<module_content>
{MODULE_CONTENT}
</module_content>

---

## YAML Schema Format

Your output MUST follow this exact structure:

```yaml
version: "1.0"
module: {MODULE_SLUG}
level: {LEVEL}

# NOTE — these are SHAPE examples. The real targets are at the top of this prompt
# ({TOTAL_TARGET} total / exactly {INLINE_MIN} inline / {WORKBOOK_MIN}–{WORKBOOK_MAX} workbook,
# {ITEMS_MIN}+ items per activity). The shapes below are TRUNCATED for readability;
# YOUR output MUST hit those minimums.

inline:
  - id: marker-id-here        # MUST match an <!-- INJECT_ACTIVITY: ... --> marker
    type: quiz                 # activity type
    instruction: "<UKR_1> <UKR_2> <UKR_3>"
    items:                     # ← real output: ≥ {ITEMS_MIN} items
      - question: "_____ <UKR_1>"
        options: ["<UKR_2>", "<UKR_3>", "<UKR_4>", "<UKR_5>"]
        correct: 0             # 0-based index
      - question: "<UKR_1> ____ <UKR_2>."
        options: ["<UKR_3>", "<UKR_4>", "<UKR_5>", "<UKR_6>"]
        correct: 1
      # ... add at least {ITEMS_MIN} items total — never stop at 1-2

  - id: another-marker-id
    type: fill-in
    instruction: "<UKR_1> <UKR_2> <UKR_3>"
    items:                     # ← real output: ≥ {ITEMS_MIN} items
      - sentence: "<UKR_1> ____ <UKR_2>."
        answer: "<UKR_3>"
        options: ["<UKR_4>", "<UKR_3>", "<UKR_5>"]
      - sentence: "<UKR_1> ____ <UKR_2>."
        answer: "<UKR_3>"
        options: ["<UKR_4>", "<UKR_5>", "<UKR_3>"]
      # ... ≥ {ITEMS_MIN} items total

workbook:
  - id: match-up-vocab
    type: match-up
    instruction: "<UKR_1> <UKR_2>"
    pairs:                     # ← real output: ≥ {ITEMS_MIN} pairs
      - left: "<UKR_1>"
        right: "<UKR_2>"
      - left: "<UKR_3>"
        right: "<UKR_4>"
      - left: "<UKR_5>"
        right: "<UKR_6>"
      # ... ≥ {ITEMS_MIN} pairs total

  - id: group-sort-gender
    type: group-sort
    instruction: "<UKR_1> <UKR_2> <UKR_3> <UKR_4>"
    groups:
      - label: "Чоловічий рід"
        items: ["<UKR_1>", "<UKR_2>", "<UKR_3>"]   # ≥ 3 items per group
      - label: "Жіночий рід"
        items: ["<UKR_4>", "<UKR_5>", "<UKR_6>"]
      - label: "Середній рід"
        items: ["<UKR_7>", "<UKR_8>", "<UKR_9>"]

  - id: true-false-grammar
    type: true-false
    instruction: "<UKR_1> <UKR_2>?"
    items:                     # ← real output: ≥ {ITEMS_MIN} items
      - statement: "«<UKR_1>» — це чоловічий рід."
        correct: false
        explanation: "<UKR_1> закінчується на <suffix>, отже жіночий рід."
      # ... ≥ {ITEMS_MIN} items total

  - type: observe
    examples:
      - "example sentence 1"
      - "example sentence 2"
    prompt: "What pattern do you notice?"

  - type: anagram
    instruction: "<UKR_1> <UKR_2> <UKR_3> <UKR_4>"
    items:
      - letters: ["<LETTER_1>", "<LETTER_2>", "<LETTER_3>", "<LETTER_4>", "<LETTER_5>"]
        answer: "<UKR_1>"
    # NOTE — do NOT add a `hint:` field to items. The audit rule
    # HINT_IN_ACTIVITY rejects item-level hints because they break
    # activity rendering. Keep items minimal: letters + answer only.

  - type: order
    instruction: "<UKR_1> <UKR_2> <UKR_3> <UKR_4> <UKR_5>"
    items:                         # Lines displayed SHUFFLED to the learner
      - "— <UKR_1> <UKR_2>, <UKR_3> <UKR_4>."
      - "— <UKR_1>! <UKR_2> <UKR_3>!"
      - "— <UKR_1> <UKR_2>?"
    correct_order: [0, 1, 2]       # TOP-LEVEL field, zero-based indices into items[]

  - type: unjumble
    instruction: "<UKR_1> <UKR_2> <UKR_3> <UKR_4> <UKR_5>"
    items:
      - words: ["<UKR_1>!", "<UKR_2>"]            # Jumbled words
        correct_order: ["<UKR_2>", "<UKR_1>!"]    # Words as STRINGS in correct order (NOT integers!)
      - words: ["<UKR_1>", "<UKR_2>", "<UKR_3>."]
        correct_order: ["<UKR_2>", "<UKR_1>", "<UKR_3>."]
    # NOTE — do NOT add a `hint:` field to items. The audit rule
    # HINT_IN_ACTIVITY rejects item-level hints because they break
    # activity rendering. Keep unjumble items minimal: words + correct_order.

```

---

## Activity Type Reference

**CRITICAL RULE: EVERY single activity object MUST include an `id` field (a unique string like "quiz-grammar", "match-up-vocab"). Do NOT generate an activity without an `id`.**

### Core types (use for A1-C2):
- **quiz**: Multiple choice. Required: id, instruction, items[{question, options[], correct}]
- **fill-in**: Blanks in sentences. Required: id, instruction, items[{sentence, answer}]. Optional: options[]. **CRITICAL: use `____` (four underscores) for the blank, NOT `{word}` curly-brace syntax. Example: `sentence: "<UKR_1> ____ <UKR_2>."` with `answer: "<UKR_3>"`. The validator REJECTS `{word}` format.**
- **match-up**: Pair matching. Required: id, instruction, pairs[{left, right}]. Min 3 pairs.
- **group-sort**: Categorization. Required: id, instruction, groups[{label, items[]}]. Min 2 groups.
- **true-false**: Statement evaluation. Required: id, instruction, items[{statement, correct}]
- **error-correction**: Find wrong word. Required: id, instruction, items[{sentence, error, correction}]. Optional: error_type (MUST be one of: `"word"`, `"phrase"`, `"register"`, `"construction"` — NOT "grammar"), options[], explanation
- **anagram**: Letter rearrangement. Required: id, instruction, items[{letters[], answer}]
- **translate**: Type translation. Required: id, instruction, items[{source}]. Use options[] for multiple choice.
- **unjumble**: Word reordering. Required: id, instruction, items[{words[], correct_order[]}]. ⚠️ correct_order is an array of **STRINGS** (the words in correct order), NOT integers!
- **order**: Sentence/line ordering. Required: id, instruction, items[] (array of strings), correct_order[] (TOP-LEVEL array of **integers** — zero-based indices into items). ⚠️ correct_order is a TOP-LEVEL field next to items, NOT inside each item.
- **observe**: Pattern discovery. Required: id, examples[], prompt
- **classify**: Multi-category sort. Required: id, instruction, categories[{label, items[]}]

### Ukrainian pedagogy types (A1 phonetics/syllables):
- **divide-words**: Interactive syllable division. Required: id, instruction, items[{word, answer}]. Example: word: "<UKR_1>", answer: "<syl-1>-<syl-2>-<syl-3>". Do NOT add `hint:` to items — the HINT_IN_ACTIVITY audit rule rejects item-level hints.
- **count-syllables**: Count syllables in a word. Required: id, items[{word, correct}]. Optional: instruction, maxCount, translation. Example: word: "<UKR_1>", correct: 3
- **pick-syllables**: Select syllables matching criteria. Required: id, syllables[], correctIndices[], category. Example: syllables: ["<SYL_1>", "<SYL_2>", "<SYL_3>"], correctIndices: [1], category: "закриті"
- **odd-one-out**: Find the word that doesn't belong. Required: id, items[{words[], correct, explanation}]. `correct` is 0-based index. Example: words: ["<UKR_1>", "<UKR_2>", "<UKR_3>"], correct: 2, explanation: "<UKR_3> — 3 syllables, rest have 1"
- **image-to-letter**: See image/emoji, identify letter. Required: id, instruction, items[{image, letter}]. Optional: options[]
- **letter-grid**: Letter reference grid. Required: id, letters[{upper, lower}]. Optional: name, emoji, key_word, sound_type
- **watch-and-repeat**: Watch video, repeat pronunciation. Required: id, items[{video}]. Optional: letter, word, note
- **phrase-table**: Grouped phrases for communication patterns. Required: id, groups[{label, phrases[]}]

{SEMINAR_TYPE_REFERENCE}

---

## Learner Level Context

{LEVEL_CONTEXT}

## Topic-Specific Exercise Patterns (from Ukrainian pedagogy)

These patterns come from МійКлас and Ukrainian textbook analysis. They show what KINDS of exercises work best for this module's topic. Use them as templates — adapt the specific content to this module's vocabulary and concepts.

{PEDAGOGY_PATTERNS}

**You MUST use these patterns.** The pedagogy patterns encode how Ukrainian teachers actually test each concept. For each matched pattern:
1. Generate **at least one activity of each recommended type** from the pattern. If the pattern lists divide-words, count-syllables, and odd-one-out — your output MUST include all three.
2. Follow the anti-patterns — if a type is listed under "DO NOT generate", do NOT use it for this topic.
3. Use the Ukrainian instruction (назва / instruction_uk) when the level allows Ukrainian instructions.

---

## Quality Rules

**ACTIVITY COUNT MINIMUMS (non-negotiable, audit-enforced):**
- **Total: {TOTAL_TARGET} activities.** Inline: exactly {INLINE_MIN}. Workbook: {WORKBOOK_MIN}–{WORKBOOK_MAX}. The audit gate FAILS the module if you ship fewer.
- **Type diversity: module MUST cover at least {MIN_TYPES_UNIQUE} distinct activity types.** A wall of quizzes is rejected. Quiz + true-false combined ≤ 25% of workbook.
- **Match the inline markers exactly.** Every `<!-- INJECT_ACTIVITY: id -->` marker in the prose needs a matching inline activity with that exact id. Skipping markers means the lesson tab is broken.

**ITEM COUNT MINIMUMS (non-negotiable, per-activity):**
- **Default minimum: {ITEMS_MIN} items per activity.** Quiz, fill-in, match-up, true-false, anagram, error-correction, translate, cloze, mark-the-words, divide-words, count-syllables, odd-one-out, group-sort categories: all ≥ {ITEMS_MIN}.
- **Lower minimums for specific types only:** order = 3+ items (dialogue lines), observe = 2+ examples, pick-syllables = 4+ syllables, watch-and-repeat = 3+ items, essay-response/critical-analysis = 1 prompt.
- If you can't think of enough items, add more examples from the module's vocabulary and content. NEVER ship a 1-item or 2-item activity unless its type cap explicitly allows it.
- **Exactly 4 options per quiz question at A2+** — enough to prevent guessing, not so many to overwhelm. A1 allows 3-4.
- **BINARY CONCEPTS (e.g., НВ/ДВ, masculine/feminine, true/false):** Do NOT use `quiz` with only 2 options — use `true-false` (for statement evaluation) or `group-sort` (for categorization) instead. Quiz type requires 4 options at A2+.

**Instructions match learner level:**
1. **A1.1 (M01-M07):** Instructions in ENGLISH. The learner is a complete beginner who cannot read Ukrainian yet. They are learning the alphabet and first words. Use activity types: image-to-letter, letter-grid, match-up (letter↔sound), quiz (in English about Ukrainian sounds/letters). Anna Ohoiko's pronunciation videos should be referenced where relevant.
2. **A1.2-A1.3 (M08-M21):** Instructions in simple English with Ukrainian key terms in bold. Learner knows basic words but not grammar terminology.
3. **A1.4+ (M22-M55):** Instructions can be in simple Ukrainian with English translation in parentheses.
4. **A2+:** Instructions in Ukrainian.
5. **B1+:** Full Ukrainian, no English.

**Other rules:**
6. **No duplicate options** — each option in a quiz item must be unique
7. **Answer must be in options** — for quiz items, `correct` must be a valid index. For fill-in with options, `answer` must appear in `options`.
8. **Plausible distractors** — wrong options should be real Ukrainian words that test the specific skill. Not random words.
9. **Min 6 pairs for match-up** — to prevent trivial elimination
10. **Explanations for true-false and error-correction** — help the learner understand WHY
11. **Test LANGUAGE, not trivia** — exercises must test Ukrainian language skills. Not "In what year..." factual recall.

---

## Verification Tools (MCP)

Use these tools to verify your exercise content:

{TOOL_INSTRUCTIONS}

**Verification checklist:**
1. Run `verify_words` on all Ukrainian words in your exercises — every word must exist in VESUM
2. Run `query_cefr_level` on any word you're unsure about — it must be {LEVEL}-appropriate
3. For fill-in answers and distractors, verify the exact form (case, number, gender) with `verify_lemma`

---

## ⚠️ MANDATORY FINAL CHECKLIST — verify before emitting YAML

Walk through this checklist explicitly before you start emitting. If ANY box is unchecked, fix it FIRST.

- [ ] My output has **exactly {INLINE_MIN}** inline activities (one per `<!-- INJECT_ACTIVITY -->` marker).
- [ ] My output has **at least {WORKBOOK_MIN}** workbook activities.
- [ ] **Total ≥ {TOTAL_TARGET}.**
- [ ] **Every** activity has **at least {ITEMS_MIN}** items, pairs, or statements (except types with explicitly lower caps: order=3, observe=2, pick-syllables=4, watch-and-repeat=3, essay-response=1).
- [ ] The module (inline + workbook combined) uses **at least {MIN_TYPES_UNIQUE} distinct activity types**. I am NOT shipping a wall of quizzes.
- [ ] Quiz + true-false combined are roughly ≤25% of the workbook (quality target — lean on `WORKBOOK_PRIORITY_TYPES` instead).
- [ ] I prioritized types from `WORKBOOK_PRIORITY_TYPES` (heavy practice formats), not just easy-to-write quizzes.
- [ ] I used ZERO types from `FORBIDDEN_ACTIVITY_TYPES`.
- [ ] All fill-in items use `____` blanks, NOT `{word}` curly-brace syntax.
- [ ] My inline count is exactly {INLINE_MIN}, with one inline activity per prose marker.
- [ ] Every Ukrainian word in my items appears in the prose or in `PLAN_VOCABULARY`.
- [ ] At B1+, all instructions are in Ukrainian (no English fallback).

If you cannot tick all of these, REGENERATE the activities BEFORE outputting. Shipping under-spec means the build rejects you and the heal loop has to redo your work — wasting compute.

---

## Output

Output the complete YAML document. Start with `version: "1.0"` — no markdown fence, no preamble.
