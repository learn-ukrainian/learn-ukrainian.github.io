# V7 UPGRADE writer — preserve and expand an existing module

Mode: upgrade. Base level: {BASE_LEVEL}. Module: {SLUG}.
Your current published unit: {LESSON_SCOPE}.

Upgrade the supplied built module into the deterministic lesson map below.
Do not write a plan, retrieve a wiki packet, or author a replacement from scratch.
The original plan and artifacts are input evidence, never files you may change.
Return artifacts for the current lesson only using the existing V7 output contract.

## Lesson contract

Each lesson is a 60-minute block: warm-up and retrieval, Ukrainian-first presentation,
dialogue and breakdown, guided practice, independent practice, recap and next step.
Preserve every original paragraph in its mapped section and lesson verbatim, exactly
once across the split (only whitespace and deterministic stress annotation may differ).
The introduction belongs to lesson 1. Keep original section headings and activity IDs.
Expand with useful transitions, explanations and breakdown tables; never pad or repeat
paragraphs to meet the floor. Each lesson must meet its word_target (minimum 550);
the whole module must reach at least 2000 prose tokens. The final lesson closes the module. On that lesson, end with a bilingual heading
`### Підсумок модуля — Module summary` and 4–7 bilingual bullets of what the
learner can now do (module 9 shape). Do **not** title it `Завершення модуля` /
`Module completion`, and do **not** put that close in a support table.

Follow docs/best-practices/ulp-presentation-pattern.md and the v4 lesson contract.
Use a direct, friendly teaching voice with NO named narrator and NO self-introduction.
Named people occur only inside dialogues. Do not adopt any reference author's persona
or lesson structure. A quotation must be visibly marked, attributed, and have a matching
entry in resources.yaml (Ресурси). Preserve source provenance.
Ukrainian comes first, with English scaffolding appropriate to the supplied learner state
and to **this module's original A1 mix** (do not clone module 9's adjectives lesson;
clone only its close/summary *shape*). Added Ukrainian passages of three or more
sentences require side-by-side English support. Write dialogues as > blockquotes,
never as code fences; put the English breakdown after.

**Why you must call `sources` / VESUM — not as a ritual, as the reason this page is better Ukrainian.**
A fluent model still mixes Russian calques, wrong gender, wrong government, and invented
example sentences. VESUM is the dictionary of record for lemma, gender, aspect, and
rections. Looking it up is what makes the line teachable. This run is also a **test of
the sources tools**: we will check your tool trace. If you never call them, we cannot
tell they work, and this corpus is the dataset for a Ukrainian LLM — guessed forms
become the next model's errors. If a lookup misses, mark `<!-- VERIFY: … -->` and do
not invent. Stress marks still come from the pipeline annotator after review; do not
invent stressed spellings.

A1 landing overview (lesson 1 only): if the original module opening (text before the first `##`) has no "By the end, you can" after tables/tips/code fences are ignored, also return:

```markdown file=landing-overview.md
```

Shape = module 9, not a clone: (1) 1–2 short English-carrier paragraphs with bold Ukrainian targets, (2) "By the end, you can:" 4–7 communicative bullets, (3) one "keep the scope small" sentence. Vary the hook. No `:::tip`, no markdown tables, no `Привіт!` narrator. If the cleaned original already has "By the end, you can", do **not** write this file.

A2+ upgrade: full Ukrainian immersion. Do not write English-carrier landings or landing-overview.md.

## Activities and vocabulary

Keep every original activity's type, items, answer flags and groups structurally intact.
Use provenance to find its assigned lesson. Inline IDs stay unchanged; id-less workbook
originals use act-w1, act-w2, etc. Add distinct activities with globally unique IDs.
A lesson with no activities is a defect (boring theory). After a 2–5 lesson split the
originals will not fill every lesson — **generate new unique activities** until this
lesson has 4–6 inline and 6–9 workbook (≥10 total). Closing/summary lessons still need
practice, not recap-only. >=6 items each unless the deterministic map declares an
original-item exemption. Do not create exemptions.
Use <!-- INJECT_ACTIVITY: id --> for each inline activity, once, in its relevant section.
Use only the base A1 placement/type matrix below. Preserve every option of odd-one-out.

### Find-and-Fix (`error-correction`) — HARD (upgrade gate)

Step 1 is “spot the bad token”. Step 2 must be a **real spelling choice**, not a
tautology. The component removes the spotted error from the step-2 chips, so an
`options:` list that contains the `error` token both fails the lesson gates and
shrinks the visible choice set.

For **every** `error-correction` item that has a non-empty `error:`:

1. `sentence:` is a **natural Ukrainian carrier** (dialogue/scene) with **no**
   English gloss. At **A1**, put the short English scaffold in `explanation:`
   (not after `—` on the sentence, and not in parentheses on the sentence).
   For items preserved from the original module, do **not** rewrite `sentence:`
   (structural preservation); still put EN in `explanation:` if it is missing.
   Forbidden: English meta stems (“Find the word…”, “Identify which…”,
   “In Ukrainian, the word for…”).
2. Canonical fields only: `sentence`, `error`, `correction`, `options`,
   optional `explanation` (same contract as fresh write).
3. `options:` has **≥3 distinct** forms, **includes `correction`**, and must **NOT
   contain the `error` token** (any option equal to `error` fails). The three chips
   are the correction plus ≥2 distractors, none of them the error. Distractors are
   **other spellings of the same word** (`день` → `дєнь` / `дінь`), never an unrelated
   vocabulary word (`кінь`, `сіль`, `свято`).
4. **Render-faithful chips:** after MDX derivation, at least one option string
   must equal the rendered `correctForm` **exactly** (React uses
   `selectedFix === correctForm`). Do not put English glosses on chips
   (`день (day)` vs bare `день`); keep glosses in `explanation` only.
5. Distractors come **only** from the inventory below (wiki L2 / bad-form pairs /
   cumulative learner-state contrasts). Never invent Russianisms or fabricate
   wrong forms. If inventory is thin, reuse attested pairs from the original
   module’s other EC items / quiz contrasts — still never put the error token in `options`.
6. You **may grow** original `options` lists (preservation is ⊆). You **must**
   grow empty or binary tautological originals to satisfy (3)–(5).

Empty `options` (UI reveal-only) is a hard fail.

### Fill-in (`fill-in`) — HARD (upgrade gate, #8214)

Every fill-in **item** must include a non-empty `explanation:` that teaches why
the answer is correct (apostrophe rule, soft sign, letter, etc.). Micro-blanks
like `бур___ян` / answer `'` without feedback are a hard fail — same contract as
quiz/translate explanations. Structural blank + `answer∈options` checks still
apply.

**Empty choice (blank slot).** When "no character" is the right answer, the option
and the `answer` are the **empty string `""`**, nothing else. The chip renders as a
blank clickable slot; grading compares the selected value to `answer`; empty means
no character inserted. Never write `без знака`, `без зна́ка — no sign`, `Немає знака`
or any gloss in `options` or `answer` — the gate rejects them. Sample:

```json
{"sentence": "ден___ь", "options": ["", "ь", "'"], "answer": "", "explanation": "..."}
```

### Alphabet modules: no line breaks (`sounds-letters-and-hello`, `reading-ukrainian`, `special-signs`)

These three modules teach syllables, not line breaks. Do **not** teach `перенос`, do
not emit `divide-words` activities, and do not use the models `Мар'-яна`,
`дере-в'яний`, `бур'-ян`, `паль-ці` or any other hyphenated break. The plan and
original artifacts below have been filtered of `перенос` items on purpose; an
original divide-words activity that is missing from them is intentionally dropped.
The gate fails such a build.

### Learner-facing phrases banned at every level

Never write (case-insensitive): "mastery of all 33 letters", "comprehensive command of
the complete 33-letter", "use only prepared models", "before you leave the lesson
tab", "Stay inside Ukrainian for this lesson".

### Activity chrome language

Learner-facing `instruction:` / bilingual titles may keep `UA — EN` shape; the
site chrome locale toggle picks the facing language at runtime. Do not bake
English-only instructions for Ukrainian chrome. Content stems stay as above.

Allocate each original vocabulary entry once, at its first teaching use. Keep the union
equal to the original vocabulary, with >=12 complete entries per lesson. Learner knowledge
is cumulative: prior-module vocabulary plus entries introduced in previous lessons.
Every entry needs lemma, translation, pos, usage. Every lesson needs nonempty resources
with title plus url, chunk_id or source. The landing page aggregates these artifacts.

{ACTIVITY_CONFIG}

## Distractor inventory (read-only — use for EC / MCQ wrong forms)

{DISTRACTOR_INVENTORY}

## Learner state before this lesson

{LEARNER_STATE}

## Deterministic lessons.yaml (read-only)

{LESSON_MAP}

## Original plan (read-only)

{ORIGINAL_PLAN}

## Existing module artifacts (read-only)

{ORIGINAL_ARTIFACTS}

## Response format

Return exactly four named fenced blocks, with no other commentary:
```markdown file=module.md
(the current lesson's complete preserved-and-expanded prose)
```
```json file=activities.yaml
{"inline": [], "workbook": []}
```
```json file=vocabulary.yaml
[]
```
```json file=resources.yaml
[]
```
The arrays above describe the syntax; empty artifacts fail the gates. Structured artifacts
must be strict JSON inside the fences; V7 writes them as YAML. Do not return lessons.yaml.
