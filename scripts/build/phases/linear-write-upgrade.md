# V7 UPGRADE writer — preserve and expand an existing module

Mode: upgrade. Base level: {BASE_LEVEL}. Module: {SLUG}.
Your current published unit: {LESSON_SCOPE}.

Upgrade the supplied built module into the deterministic lesson map below.
Do not write a plan, retrieve a wiki packet, or author a replacement from scratch.
The original plan and artifacts are input evidence, never files you may change.
Return artifacts for the current lesson only using the existing V7 output contract.

## Lesson contract

Each lesson is a 60-minute block: warm-up and retrieval, presentation, dialogue and
breakdown, guided practice, independent practice, recap and next step.

**Classify the archive. Do not preserve every paragraph.** Keep what already teaches
(letter videos, good examples, working activities). Drop junk (hyphenation, named-narrator
openers, unread Ukrainian walls, AI padding). Rewrite explanations that a learner at
this module cannot use. Keep original activity IDs when you keep the activity.
The introduction belongs to lesson 1. Expand with useful transitions and breakdown
tables; never pad. Each lesson must meet its word_target (minimum 550); the whole
module must reach at least 2000 prose tokens. The final lesson closes the module
with `### Підсумок модуля — Module summary` and 4–7 bilingual can-do bullets
(module 9 *shape* only). Do **not** title it `Завершення модуля`.

Copy **how** Anna Ohoiko teaches, not who she is: Ukrainian as sound, English that
explains, Ukrainian again. NO named narrator and NO self-introduction. No "Hi, I'm X."
Named people occur only inside dialogues. Do not paste her scripts. Do not invent
Teacher Oksana or any other host. A quotation must be marked, attributed, and listed
in resources.yaml.

**They cannot read a letter they have not been taught.** For A1 alphabet modules
(sounds-letters-and-hello, reading-ukrainian, special-signs, and any module that
introduces graphemes), teaching metalanguage is English. Ukrainian on the page is
the letters and words this lesson (and earlier ones) already gave, plus audio/video.
Do not write unread Ukrainian paragraphs. A1.1 modules 1–4: English next to prompts,
options, and explanations (operating rules). From who-am-i onward, UA first with
English support. A2+: do not raise English.

Keep every original `watch-and-repeat` / letter-video activity (YouTube) that the
archive maps into this lesson. Dropping a letter video is a defect.

Follow docs/best-practices/ulp-presentation-pattern.md (method, not persona) and
docs/epics/a1-upgrade-landing-contract.md. Dialogues as `>` blockquotes, never code
fences; English breakdown after.

## Prove what you write — named `sources` MCP tools (HARD, runtime-gated)

**Why: this is the reason the page is better Ukrainian, not a ritual.** A fluent model
still mixes Russian calques, wrong gender, wrong government, and invented rules and
example sentences. Our corpus (textbooks, VESUM, Правопис) is the record. This run is
also a **test of the sources tools**, and this corpus is the dataset for a Ukrainian
LLM — guessed forms and guessed rules become the next model's errors.

Call these MCP tools **by these exact names** (your harness may expose them as
`call_mcp_tool` with ServerName `sources`, or as `mcp_sources_<tool>`; same tools):

- `mcp__sources__search_text` — **probe every theory claim and every landing claim in
  the textbook corpus BEFORE you emit the sentence.** Query the rule the way a textbook
  states it, read the hits, and write what the corpus supports. If the corpus does not
  support the claim, write `<!-- VERIFY: … -->` and do **not** invent.
- `mcp__sources__verify_words` — every lemma you teach: all vocabulary entries plus
  every new example word you add (batch them in one call).
- Optional, same server: `mcp__sources__query_pravopys` for an orthography rule,
  `mcp__sources__verify_lemma` / `mcp__sources__check_modern_form` for a single doubtful form.

Required probes, checked against your recorded tool trace:

1. **Theory probe (every lesson).** At least one `mcp__sources__search_text` (or other
   `sources` corpus search) that probes a **theory claim in this lesson's presentation**
   — the rule you explain, not a random word.
2. **Landing probe (lesson 1 only).** When you return `landing-overview.md`, at least one
   corpus search that probes the landing itself: each bilingual "By the end, you can"
   bullet and each bold Ukrainian target must be corpus-true and actually taught in this
   module. The landing is an executive orientation portal
   (docs/epics/a1-upgrade-landing-contract.md) — not a theory dump, not a table, not YAML
   objectives — but its claims are still claims, and you probe the landing like theory.
3. **Vocabulary proof (every lesson).** At least one `mcp__sources__verify_words` covering
   this lesson's vocabulary and new example words.

**What does NOT count as proof.** Only `sources` MCP calls are recorded in the tool
trace. Shell commands, Python scripts, `curl`/HTTP requests and direct SQLite reads of
any dictionary database are invisible to the trace and are never a substitute — do not
run them. A lesson whose trace holds zero `sources` MCP calls **fails the build**
(`MCP_TOOLS_NEVER_INVOKED`) and the write is discarded. If the MCP tools are not
visible in your session, stop and report that in one line instead of working around it.

Stress marks come from the pipeline annotator after review. Do not invent stressed
spellings, and do not look stress up by any other route.

A1 landing overview (lesson 1 only): if the original module opening (text before the first `##`) has no "By the end, you can" after tables/tips/code fences are ignored, also return:

```markdown file=landing-overview.md
```

Shape = module 9, not a clone: (1) 1–2 short English-carrier paragraphs with bold Ukrainian targets, (2) "By the end, you can:" 4–7 communicative bullets, (3) one "keep the scope small" sentence. Vary the hook. No `:::tip`, no markdown tables, no `Привіт!` narrator. If the cleaned original already has "By the end, you can", do **not** write this file.

A2+ upgrade: full Ukrainian immersion. Do not write English-carrier landings or landing-overview.md.

## Activities and vocabulary

Keep every original activity's type, items, answer flags and groups structurally intact
**except** activities you classified as drop (hyphenation / divide-words on alphabet
modules; narrator junk). **Keep** every `watch-and-repeat` with a video URL.
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
`дере-в'яний`, `бур'-ян`, `паль-ці` or any other hyphenated break. The lesson map, plan
and original artifacts below have been filtered of `перенос` items on purpose; an
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
