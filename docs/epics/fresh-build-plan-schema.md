# Fresh lesson-based build — plan and evidence-pack schema (design)

> Sub-epic #8397, child 3. Status: **design draft r9** (r1 reviewed by AGY `gemini-3.8-flash-high`, task
> `design-review-8397-schema-r1`: REVISE, 7 findings, all folded in) by the curriculum-upgrade driver, for
> cross-family design review and operator correction. Implements requirements R-01…R-09, R-22,
> R-24…R-28, R-30, R-32, R-33, R-34, R-35 of [`fresh-build-requirements.md`](fresh-build-requirements.md).
> **Revisions 3–7 (2026-09-21):** §2a added — the semantics the plan validator needs, found while briefing
> #8412 (a pre-dispatch critic showed that rules 1–7 could not be implemented without guessing). The
> first code against this design is the arc data file (#8411, merged). Revision 4 folds in two independent
> reviews of revision 3 (`design-review-8412-r3`, Gemini lane, 10 findings; `critic-8412-design-r3`, Kimi seat, 5);
> revision 5 folds in the six findings of the confirming review (`design-review-8412-r4`). On its finding about
> `recycled` versus planned learner state, the accepted §4 and §5 are kept: planned state remains the writer's
> allowlist, and `recycled` is defined as the subset a lesson commits to re-expose.
> **Revision 8 (2026-09-21) — forms are not restricted, lemmas are (operator decision).** Asked which forms a
> lesson writer may use (#8431, question 1), the operator answered: *"allow yes, if something is have not
> tought yet the student has to memorize it. it is normal. later he will learn about it."* A writer may use
> **any form of an allowed lemma**; a form whose category the learner has not been taught is met as something
> to memorise and is not explained. Changed: §2 (the meaning of a lesson's `forms` list), §3 (the word store
> holds full paradigms), §4 (planned state; the new paragraph on forms), §6 (the inventory gate). R-16 is read
> accordingly: its limit is on vocabulary and on what a lesson *explains*, not on the forms of known words.
> **Revision 9 (2026-09-22) — the fields the two contracts need; the contracts themselves.** The lesson writer
> contract ([`fresh-build-writer-contract.md`](fresh-build-writer-contract.md), #8431 r3) and the review contracts
> ([`fresh-build-review-contracts.md`](fresh-build-review-contracts.md), #8430 r4) are §5 and the *review* row of §6,
> kept as their own files; each was critiqued by two independent seats (AGY, Codex) and **accepted by the operator on
> 2026-09-22**. §2 gains `dialogue.step`, `dialogue.speakers[].evidence`, `dialogue.places`,
> `steps[].needs`, `steps[].paradigm` and `activities[].error_refs` (writer contract §1b; learner state #8414: names are
> admitted by id, never by string). §3 fixes what a built lesson records (`evidence.lesson_entry_sha256`, #8413 Brief C).
> The build order and the packages are in [`fresh-build-build-program.md`](fresh-build-build-program.md).

## 1. Three artifacts, one owner each

| Artifact | Path | Owns | Does not own |
| --- | --- | --- | --- |
| **Level arc** | `curriculum/l2-uk-en/lesson-plans/<level>/_arc.yaml` | module order, one-sentence job per module, the progression table (letters/sounds, grammar, vocabulary themes), learner-position checkpoints | lesson detail |
| **Module plan** (schema v2) | `curriculum/l2-uk-en/lesson-plans/<level>/<slug>.yaml` | `lessons[]`: each lesson's job, inventory, steps, activities, videos, rationale, targets | source text, word facts |
| **Evidence pack** | `curriculum/l2-uk-en/evidence/<level>/<slug>.yaml` + `.lock` (sha256), plus the shared level word store `evidence/<level>/_words.yaml` | the frozen source material and verified word records that lessons cite by id | sequence, pedagogy decisions |

**Why `lesson-plans/` and not `plans/`.** `curriculum/l2-uk-en/plans/<level>/` already holds the
old-format plans — for A1, 55 files whose names equal all 55 slugs of the new arc — and §7.4 keeps
them on disk unconverted. Seven existing tools also read every `*.yaml` in that directory as an
old-format plan (`scripts/build/vocab_gen.py`, `scripts/build/plan_tracking.py`,
`scripts/generate_mdx/generate_objectives.py`, `scripts/generate_mdx/generate_plan_markdown.py`,
`scripts/rewrite_activity_hints.py`, `scripts/tools/fix_plans_phase1.py`,
`scripts/tools/enrich_summary_points.py`). The new artifacts therefore live under their own root,
named for what it holds rather than for a schema version. Rules that follow: the new validator
and every new reader are scoped to `lesson-plans/` and refuse files outside it; any lookup of "the
plan for slug X" takes the root explicitly and never searches both; the evidence-to-plan join by
slug names `lesson-plans/` explicitly. (Found 2026-09-21 while implementing #8411; decided on the
sanctioned design consult recorded on #8397.)

Two more files live beside the plans and are owned by the validator's tooling, not by an author's
prose: the level grammar registry `lesson-plans/<level>/_grammar.yaml` and the generated scope
sidecars `lesson-plans/<level>/_scope/<slug>.yaml` (both defined in §2a). Every name in that
directory that begins with an underscore is not a plan.

Sequence exists in exactly one place (the plan). Facts exist in exactly one place (the pack). That
is the structural answer to the Module 1 failure, where plan, derived lesson map and content each
carried their own version of "what this module teaches".

## 2. Module plan v2

Top-level fields kept from v1: `module`, `level`, `sequence`, `slug`, `version`, `title`,
`subtitle`, `focus`, `objectives`, `connects_to`, `prerequisites`, `register`, `changelog`.

Removed from the plan (they move): `minutes` (computed, §2a); `content_outline` and the module-level `word_target`
(→ per lesson); `references` and `vocabulary_hints` (→ evidence pack); `pedagogy: PPP` as a
module-wide label (→ lesson `shape`).

```yaml
plan_schema: 2
arc_ref: { level: a1, position: 1 }        # must match _arc.yaml
evidence_ref: { path: evidence/a1/<slug>.yaml, sha256: <lock> }

lessons:
  - n: 1
    slug: sounds-and-letters                # stable; becomes /a1/<module>/<n>/
    title: "…"                              # Ukrainian; must describe what the lesson does (R-07)
    kind: teach                             # teach | practice | recap | checkpoint (§2a)
    # closes_with_recap: true              # only on a last `teach` lesson that closes the module (rule 1b)
    job: "One sentence: what the learner can do after this lesson that they could not before."
    rationale: "Why here, why in this order; what English speakers get wrong."   # replaces wiki prose
    word_target: <n>                        # minimum, per lesson (R-04). NOT v1's 1,200, which was a
                                            # whole module; lesson-grain values are calibrated from
                                            # the first built pilot, per level, then fixed in config
    inventory:
      phonetics: { letters: [А, О, У], sounds: [] }   # optional block; A1 letter modules only
      grammar:                              # named points; ids are stable within the level (§2a)
        - { id: G-a1-001, point: "One sentence naming the point.", evidence: [T-003] }
      vocabulary:
        core:                               # actively taught; enters learner state as "known"
          - lemma: мама
            evidence: W-012
            forms: ["noun:anim:f:v_naz", "noun:anim:f:v_zna"]   # forms this lesson teaches and drills (r8; R-22)
        incidental:                         # allowed in dialogues/situations, glossed inline,
          - { lemma: кава, evidence: W-040 }  # NOT counted as known; no `forms` — nothing is taught or drilled (r8)
        recycled: [W-003, W-007]            # word-store ids introduced in an earlier lesson or plan (§2a)
    steps:                                  # textbook shape: theory step → practice, repeated (R-27)
      - id: s1
        kind: teach                         # teach | practice | recap (§2a)
        teach: "Point taught, in one sentence."
        introduces: { letters: [А], grammar: [G-a1-001], vocabulary: [W-012] }   # §2a
        uses: { grammar: [], vocabulary: [] }                                     # §2a
        evidence: [T-003, T-007]            # pack ids; every id must be used and cited (R-28)
        practice: [a1, a2]                  # activity ids below
        needs: [example, paradigm]          # r9: the record kinds this step's blocks need (example | quote | error | video | culture | paradigm);
                                            # the engine's preflight checks each exists before the writer is called (writer contract §4)
        paradigm: { id: P-01, word: W-012, forms: ["noun:anim:f:v_naz", "noun:anim:f:v_rod"] }   # r9, optional: a table of forms the
                                            # engine generates from the word record in this order; the writer places it (writer contract §1)
      - id: s2
        …
    consolidation: [a5, a6, a7]             # the larger practice block closing the lesson
    activities:
      - id: a1
        type: quiz
        placement: inline                   # inline | workbook
        focus: "What it checks."
        model: X-004                        # optional: textbook exercise it is modelled on
        error_refs: [E-001, E-002]          # r9, required when type is error-correction: the E- records its items may draw on (writer contract §1c)
    videos:
      - evidence: V-002                     # never a bare URL; the pack verifies it (R-18)
        use: "Where in the lesson and why."
    dialogue:
      step: s3                              # r9: the step that hosts the dialogue block (writer contract §1b)
      situation: "…"
      setting: "…"                          # place and objects, as v1 required
      speakers: [ { name: Оксана, role: waiter, gender: f, evidence: W-301 }, { name: Тарас, role: customer, gender: m, evidence: W-302 } ]
                                            # r9: a name is a word record with its case forms; the inventory gate admits it by id (#8414)
      places: [ { name: Київ, evidence: W-310 } ]   # r9, optional: place names used in the dialogue, by record
      register: informal                    # informal | formal
      target_grammar: "…"                   # what the dialogue exists to show
      evidence: [T-010]                     # r9: includes the EX- records of attested exchanges for this situation (writer contract §5)
    practice:                               # R-33: the deck is generated from this + the word store
      vocabulary: core                      # every core lemma of this lesson, in the forms it teaches;
                                            # the deck generator adds this lesson's `recycled` ids itself
      stress: [W-012, W-019]                # word records whose stress placement is drilled
      patterns: [a2, a5]                    # activity ids whose pattern is recycled into the deck
    reading_passages: []                    # optional; B2+ and seminar tracks later
```

Rules the validator enforces (all deterministic):

1. `lessons` is non-empty; `n` is 1..N contiguous. The module closes with a recap (R-03) in exactly
   one of two shapes: (a) the last lesson has `kind: recap`; or (b) the last lesson is `teach` and
   carries `closes_with_recap: true` with a final `recap` step that introduces nothing — allowed
   only when the module has at most two teach lessons, and flagged for the plan review to confirm.
   Checkpoint modules are exempt from the closing-recap shapes: all their lessons are
   `checkpoint`, with no new inventory.
2. The recap lesson has empty `inventory.vocabulary.core`, empty `phonetics` and `grammar`, and no `teach` steps (§2a).
3. Every `evidence` id exists in the locked pack; the pack hash matches `evidence_ref.sha256`.
   Word ids (`W-…`) resolve in the shared level word store `evidence/<level>/_words.yaml`, which
   has its own `.lock` (§7.2); every other id resolves in the module pack.
4. Every `inventory.vocabulary.recycled` id and every id a step `uses` was introduced earlier: in an
   earlier lesson of this plan or in the plan of an earlier arc position (grammar and vocabulary
   used inside the lesson that introduces them must be introduced in an earlier step). The arc is
   not an input to this check (§2a).
5. Union of lesson `core` inventories equals what the arc says this module introduces — nothing
   more, nothing less (limited today to what the arc carries as data — §2a). A generated,
   structured `scope` (letter count and list, grammar points, core-lemma count) is **derived from
   the lessons by the validator, never typed**, and kept as a sidecar file (§2a); the landing page
   renders its numbers from it. The deterministic title check is
   limited to enumerated letter lists found in `title`/`subtitle`, which must equal the `scope`
   letter list (a subtitle enumerating seven letters over lessons that teach 33 fails here);
   digit quantities are not parsed and are reported as not checked (§2a).
   Broader "does the title describe the job" is judged in the cross-family plan review.
6. Every `teach` step has at least one practice activity; activity types are in the level's
   allowlist; inline/workbook counts meet the per-lesson minimums (uncalibrated today — §2a).
7. No Ukrainian word form, stress or morphology appears in a plan except as a reference to a pack
   word record; every `forms` tag cited in a lesson must exist in that word record.

### 2a. Semantics the validator needs (revision 3, 2026-09-21)

Rules 1–7 above use words that were not yet mechanical. They are defined here; where a number or
a data source does not exist yet, the validator **reports the rule as not checked** — it never
passes silently and never invents a value.

- **Files in `lesson-plans/<level>/`.** A module plan is `<slug>.yaml`. Every other file or folder
  there begins with an underscore and is never a plan: `_arc.yaml`, `_grammar.yaml`, and the folder
  `_scope/`. Every reader of plans must skip names that begin with `_`.
- **Lesson kinds and step kinds.** Step kinds are `teach | practice | recap`. `teach` steps exist
  only in `teach` lessons. A `practice`, `recap` or `checkpoint` lesson introduces nothing: its
  `inventory` has empty `phonetics`, `grammar` and `vocabulary.core`, and none of its steps carries
  `introduces`. A `recap` step is the closing step of rule 1(b) or a step of a `recap` lesson; a
  `practice` step rehearses what is already introduced. A `checkpoint` lesson has `practice`
  steps only, or none. Rule 1's closing shapes are unchanged.
- **"Introduces" is declared, not inferred.** A `teach` step
  carries `introduces: { letters, grammar, vocabulary }` (ids, any list may be empty) and may carry
  `uses: { grammar, vocabulary }`. A lesson's `inventory` must equal the union of its steps'
  `introduces`: `phonetics.letters` ↔ letters, `grammar[].id` ↔ grammar, `vocabulary.core[].evidence`
  ↔ vocabulary. An item introduced in two steps, or present in the inventory and in no step, fails.
  A `practice` or `recap` step has no `introduces`, or an empty one. "A recap lesson introduces nothing" (rule 2)
  and "a final `recap` step that introduces nothing" (rule 1b) mean exactly this.
- **Grammar points** are records `{ id, point, evidence }`. The id is `G-<level>-<nnn>`; `point` is
  one English sentence; `evidence` lists pack ids. Level-wide uniqueness needs a registry, because
  plans are drafted out of order: `lesson-plans/<level>/_grammar.yaml` is an append-only list of
  `{ id, point, introduced_at: { position, lesson } }` (plus `superseded_by: <id>` on a record that
  a later one replaces). A plan may introduce only an id that the
  registry assigns to that position and lesson with the same `point`; an id is never removed or
  renumbered. `plan-validate` checks the plan against the registry and the registry for duplicate
  ids. Append-only is mechanical, not a review courtesy. `plan-validate --strict` compares
  the registry with the same file at `git merge-base HEAD origin/main`: every record present there
  must still be present, in the same order, with `id`, `point` and `introduced_at` unchanged; new
  records come only after them. The single permitted change to an existing record is adding
  `superseded_by: <id>`, where that id exists in the registry and is not itself superseded; a
  plan may not introduce or use a superseded id. Correcting a merged point's wording is therefore
  a deliberate act: a new id, and the old record kept and marked. Edge cases: if the file does not
  exist at the merge base (first registry, or a new level) every record is new and the check
  passes; on `main` itself the merge base is `HEAD` and the check passes; if no merge base can be
  computed (a shallow clone), `--strict` **fails** and says to fetch full history — the CI job
  that runs it checks out with full history.
  "Used but not introduced" (rule 4) means: every id in a step's `uses.grammar` or
  `uses.vocabulary` must have been introduced in an earlier step of the same lesson, an earlier
  lesson of the same plan, or a plan at an earlier arc position.
- **`recycled` and `uses`.** `vocabulary.recycled` is a list of word-store ids (not lemmas). Each
  must have been introduced in an earlier lesson or an earlier plan — never in the same lesson.
  Every id in a step's `uses.vocabulary` that this lesson does not itself introduce must be listed
  in `recycled`, and every `recycled` id must be used by at least one step.
- **Missing earlier plans fail closed.** If rule 4 needs the plan of an earlier position and that
  file does not exist under `lesson-plans/<level>/`, validation fails with the missing positions
  listed. `--allow-missing-prior` turns that failure into a printed, machine-readable waiver
  (`waived: prior_plans_missing`) for pilots written out of order; a waived run is never reported
  as a clean pass. Enforcement point: the build preflight and CI call `plan-validate --strict`,
  which rejects every waiver flag, so a plan that needs a waiver cannot be built or merged as
  buildable.
- **The arc side of rule 5 is limited by the arc's data.** The arc file carries structured
  `letters` for the literacy positions and prose for everything else. Rule 5 therefore checks
  `arc_ref`, the slug, and letter equality (and that non-literacy plans introduce no letters), and
  reports `not_checked: arc_has_no_structured_grammar_or_vocabulary` until the arc gains such
  fields. Lesson counts are not compared with the arc's estimate; the module plan decides.
- **`scope` is a generated sidecar, never part of the hand-written plan:**
  `lesson-plans/<level>/_scope/<slug>.yaml`, written by `plan-validate --write-scope` and checked
  byte-for-byte by `plan-validate` (the same generate-and-check pattern as `_arc.yaml`). It holds
  the letter count and list, the grammar-point count and ids, and the core-lemma count, and —
  once it can be computed — each lesson's `minutes`. A `scope` key inside the plan file fails. The
  landing page and the arc review read the sidecar.
- **Title check.** This check reads the **module's** `title` and `subtitle` only; a lesson's title
  may name just that lesson's letters and is not compared with the module-wide `scope`. In the
  module `title` and `subtitle`, a run of two or more enumerated single letters must
  equal the `scope` letter list, or validation fails — that is the unambiguous case (the Module 1
  subtitle that enumerated seven letters over lessons teaching 33). Numbers are not parsed: a
  natural title may count something that is not inventory (days of the week), and a number that
  happens to equal a `scope` count proves nothing about the noun it modifies. The validator
  therefore always reports `not_checked: title_quantities_not_parsed`, quoting any ASCII digits it
  found in the title and subtitle, and the cross-family plan review checks stated quantities,
  digits or words, against the `scope` sidecar. There is no separate "attention" status: the
  validator's outcomes are failure, `not_checked` and `waived`, nothing else.
- **`minutes` is not a plan field.** Decision 7.3 stands: it is computed. Until the constants it
  needs exist (reading speed, per-type activity time), it is not computed either, and the
  validator reports `not_checked: minutes_constants_undefined`. A `minutes` key in a plan fails.
- **`word_target`** is a required positive integer per lesson. Its calibrated per-level minimum
  does not exist until the first pilot is built; until then the validator checks presence and type
  and reports `not_checked: word_target_not_calibrated`.
- **Activity count minimums** at lesson grain are uncalibrated (§4): reported as
  `not_checked: lesson_activity_minimums_not_calibrated`. The type allowlist is the set of
  definitions in `schemas/activities-<level>.schema.json`, read at run time.
- **Rule 7, precisely.** An inventory entry (`vocabulary.core` and `vocabulary.incidental`) names a
  word as `{ lemma, evidence, forms }` where `evidence` resolves to a word-store record, `lemma`
  equals that record's lemma, and every tag in `forms` exists in that record. Since revision 8 `forms`
  is **required on `core`** (the forms the lesson teaches and drills) and **absent on `incidental`**
  (an incidental word is neither taught nor drilled, and any of its forms may be used — §4); the
  validator fails a `forms` list on an incidental entry, so that nobody reads it as a restriction. Everywhere else —
  `recycled`, a step's `introduces` and `uses`, `practice.stress` — a word is a bare `W-…` id. Cyrillic text is otherwise allowed only in the prose fields a reviewer
  reads (module `title`, `subtitle`, `focus` and `objectives`; lesson `title`, `job`, `rationale`,
  `teach`, activity `focus`, video `use`, the `dialogue` text fields and speaker names) and as single letters in `phonetics.letters` and `introduces.letters`. `connects_to` and
  `prerequisites` hold slugs and are ASCII.
  A combining acute or grave accent (U+0301, U+0300) anywhere in a plan fails: stress lives in the
  word store. Word forms quoted inside prose fields are not machine-checked; they are in scope for
  the cross-family plan review, which checks them against the sources (R-35).
- **A v1 plan** is any file without `plan_schema: 2`, or with a `content_outline` key. It is
  rejected with a message saying v1 plans are not read or converted (§7.4).
- **Failure, not-checked and waiver codes are a registry**, one constant per code in the validator
  package, listed in its `--help`; tests assert the exact set of codes a fixture produces.

## 3. Evidence pack

```yaml
evidence_schema: 1
module: a1/<slug>
built_with: { mcp_commit: <sha>, sources_db: <sha256>, vesum: <sha256>, ulif_forms: <sha256|pending> }

texts:        # T-…  verbatim quotes
  - id: T-003
    source: { kind: textbook, file: …, grade: 1, author: …, page: 24, chunk_id: … }
    quote: "…"                              # verbatim; verified by verify_quote / chunk hash
    supports: "What teaching point this quote grounds."
exercises:    # X-…  model exercises from textbooks (theory→practice density reference)
  - id: X-004
    source: { … }
    pattern: "What the exercise makes the learner do."
    items_sample: [ "…" ]
examples:     # EX-… corpus sentences usable as models
  - id: EX-001
    sentence_ref: { words: [W-…] }          # surface text lives here once, verified at build
    text: "…"
    translation_en: "…"
    source: { kind: textbook, chunk_id: … }
errors:       # E-…  learner-error evidence (UA-GEC, style guide)
  - id: E-001
    pattern: "What goes wrong, in one sentence."
    incorrect: "…"
    correct: "…"
    source: { kind: ua-gec|style-guide, ref: … }
videos:       # V-…
  - id: V-002
    url: …
    channel: …                              # corpus channels first (R-18 / Q6)
    checked: { http_status: 200, date: 2026-… }
    transcript_ref: …                       # corpus subtitle record when we have it
standard:     # S-…  State Standard 2024 lines this module serves
```

The shared level word store `evidence/<level>/_words.yaml` (decision 7.2) holds the word records;
a module pack contains **no** `words:` list and refers to words by id only. One record:

```yaml
words:        # W-…  one record per lemma **sense** (homonym-safe); ids are level-wide
  - id: W-012
    lemma: мама
    entry: { source: ulif|vesum|atlas, key: [мама, 1] }   # (spelling, homonym_index) per #8400
    pos: noun
    cefr: { level: A1, source: puls }
    forms:                                  # the full paradigm of the lemma (r8); a form may be `pending`
      - { form: мама, tags: "noun:anim:f:v_naz", stressed: "ма́ма", stress_source: ulif|trie|pending }
    gloss_en: "mom"
    shadow: { russian_shadow: false }
```

Rules:

- Built by a tool run (MCP batch calls), never typed from memory. The builder records the exact
  source hashes in `built_with`.
- Frozen by `.lock` — two separate locks (§2 rule 3). An edit to a **module pack** changes its hash
  and invalidates the plan's `evidence_ref` until the plan is re-reviewed. An edit to the **level word
  store** changes `_words.yaml.lock`; it lists the plans that cite the changed records (§7.2) and
  those are re-verified. `built_with` is recorded in both files; `ulif_forms` is meaningful for the
  word store, which since revision 8 holds full paradigms and is therefore the larger of the two.
- **What a built lesson records (r9, #8413 Brief C).** A per-lesson lock `evidence/<level>/_state/<slug>/lessons.lock.yaml`
  hashes the records each lesson cites; the built lesson's frontmatter carries `evidence: { lesson_entry_sha256 }` only,
  and the gates compare that entry — so a pack fix invalidates only the lessons that cite the changed records. The plan's
  `evidence_ref` keeps the module-pack hash the plan review bound to; plan review runs on a **provisional** lock that is
  promoted into `evidence_ref` on APPROVE (review contracts, Contract 1).
- `stress_source: pending` is legal while the ULIF base is not ready (R-23); a build refuses a
  lesson whose cited forms are still `pending` — and, since r8, a lesson whose **built text uses** a
  form that is still `pending`. Planning is not blocked; building is.
- The pack contains **no sequencing and no pedagogy prose**.

## 4. Learner state at lesson grain (R-14, R-30)

Two layers, because a plan cannot know everything a built lesson will contain:

- **Planned state** (available at plan time, used by plan-validate and as the writer's allowlist):
  a project-wide base layer of closed-class function words and proper-noun handling (as
  `scripts/audit/checks/learner_state.py` already does) + all `core` items of earlier modules and
  of lessons `1..n−1`, held as word-store record ids (one per lemma **sense**), not as bare
  lemmas. `incidental` items never enter it. Planned state is the writer's allowlist, as before.
  A lesson's `vocabulary.recycled` list (§2a) is a **subset** of it with a different job: the words
  this lesson *commits* to bringing back — the plan's steps may rely on them, the practice deck
  includes them, and the inventory gate checks they really appear. A writer may still use any
  other word in planned state without the plan listing it.
- **Observed state** (after a lesson is built): a post-build index of what the lesson actually
  exposed — forms and exposure counts. It feeds recycling decisions and later lessons' exposure
  counts. A built lesson that uses a word-store record outside planned state
  plus its own `core` and `incidental` fails the inventory gate; it does not silently extend the
  state.

**Forms (revision 8).** The allowlist restricts **lemmas**, not forms. A sentence needs the case its
verb or preposition governs and the agreement its noun imposes, whether or not the plan listed that
form for that word; a writer held to listed forms cannot write natural Ukrainian. So:

- A built lesson may use **any form** of a word-store record that is in planned state or in its own
  `core` or `incidental`. The inventory gate fails a lemma outside that set, never a form of a lemma
  inside it.
- A form whose grammatical category the learner has not yet been taught is **used, not explained**:
  no rule, no table and no terminology for a category the arc places later. The learner memorises it,
  as with anything the arc marks a chunk, and meets the system when the arc reaches it.
- **The risk this opens, named:** nothing mechanical now stops a writer from filling an A1 dialogue
  with case forms the learner has never seen. The **only** check is the lesson review's learner-fit
  dimension (review contract, #8430, Contract 2 point 3: constructions, sentence length and clause
  depth fit the position). The observed state (below) records every form a built lesson exposed, so
  the share of not-yet-taught forms per lesson can be **reported** by script; turning that report
  into a gate with a threshold is a decision for after the pilot has shown real numbers.
- A lesson's `forms` lists (§2) keep a narrower job: the forms this lesson **teaches and drills**.
  The practice deck (R-33) and the inventory gate's "every core item appears" check use them.
- The price is in the word store (§3): it holds the **full paradigm** of every lemma it admits, each
  form with its stressed spelling (R-22), because any form may now be printed and none may be printed
  with a guessed stress. A form may be `pending` in the store; a lesson that uses it does not build
  (R-23). This widens the dependence on the ULIF base from the cited forms to all forms of all
  admitted lemmas.

**Immersion.** Thresholds are carried over unchanged (R-30). What changes is grain and key:

- A1 stays ULP-derived from cumulative vocabulary, now evaluated at the lesson's learner position.
- A2 keeps its module-indexed ramp (`compute_immersion_band` returns the module band for A2 today);
  the arc maps each new module to the band of the old module range it replaces, so a split module
  inherits, not shifts, its band. That mapping table is part of the arc deliverable.
- Structural minimums (`min_uk_dialogue_lines`, `min_uk_example_sentences`, `min_vocab_entries`,
  …) are **module-level today**. They need lesson-level equivalents, defined by dividing through a
  calibrated built module rather than by guess, in a new
  `compute_lesson_immersion_band(track, arc_position, lesson_n, cumulative_vocab)`. Until that is
  calibrated, the module-level minimums are checked on the module as a whole.

## 5. What the lesson writer receives (R-26)

**r9:** what the writer *returns*, the style card, the resolver, the gap procedure and the verification pass are the writer contract, [`fresh-build-writer-contract.md`](fresh-build-writer-contract.md) (#8431 r3). The four inputs below are unchanged.

Exactly four things: the lesson's plan entry; the evidence records that entry cites; the learner
state for that position (planned state as §4 defines it, held as word-store ids) with the
immersion rule for it; the fixed style card (ULP practices, voice,
four tabs). Not the other lessons' plans, not the whole pack, not any earlier edition.

The recap writer additionally receives the **built** lessons `1..N−1` of the same module — this is
the only place built content is an input, and only within the module being built.

## 6. Gates implied (all deterministic unless stated)

| Gate | Checks |
| --- | --- |
| plan-validate | §2 rules 1–7 with the semantics of §2a; not-checked items are reported, never passed silently. The build preflight and CI run it with `--strict`, which refuses any waiver |
| pack-verify | every quote matches its chunk; every word record re-verifies against current sources; every video URL answers |
| coverage | every evidence id cited by the lesson plan appears in the lesson and in Ресурси |
| inventory | lesson introduces exactly its `inventory.vocabulary.core` plus its new `phonetics` and `grammar` items; uses no word-store record (lemma sense) outside planned learner state + this lesson's `core` and `incidental` — any form of an allowed record is allowed (r8, §4); every form the built text uses has a non-`pending` stressed form; a token that VESUM analyses as a form of several records is **admissible** when at least one of them is allowed, and is then resolved to one record as the writer contract specifies (#8431 §3: what VESUM tags prove first, then one constrained question) — it passes only if the resolved record is allowed, and an unresolved token fails, because the gate never guesses; every `recycled` id actually appears (§4) |
| standard-coverage | R-32: every State Standard requirement the arc assigns to this module is cited by at least one lesson (`standard:` ids in the pack); an item taught earlier than the Standard places it must carry a ULP evidence id. Teaching early is never a failure by itself. Reads the corrected mapping file (#8404) |
| stress | every stressed form in the lesson matches the pack's form record for that grammatical context |
| practice | the generated deck contains every `practice` item of the lesson plan and nothing outside the lesson's inventory + learner state |
| atlas-link | every core lemma resolves to an Atlas entry; a miss triggers Atlas enrichment and is reported, never linked blind (R-34) |
| immersion | existing structural gates, keyed by learner position |
| review | cross-family content review (LLM) — the only non-deterministic gate; specified in full by the review contracts, [`fresh-build-review-contracts.md`](fresh-build-review-contracts.md) (#8430 r4): one task per lesson, receipts for every language claim, an active validator, a seeded-defect measurement of every reviewer seat, the settle step, the fix loop with its budgets |

## 7. Design decisions (operator accepted the driver's recommendations, 2026-09-21)

1. **Steps are fixed structure.** Which steps exist, their order, their evidence and their practice
   activities are binding and machine-checked; the wording inside a step is the writer's. An awkward
   step order is fixed in the plan, not improvised around.
2. **Shared word store per level.** `curriculum/l2-uk-en/evidence/<level>/_words.yaml` (+ `.lock`)
   holds one record per lemma sense for the whole level, with where it is first introduced. Module
   packs keep texts, exercises, examples, errors, videos and standard lines, and reference words by
   id. A correction (for example a ULIF stress fix) is made once. The store is versioned; a change
   lists the modules whose plans cite the changed records so they can be re-verified.
3. **`minutes` is kept and computed**, not typed: reading time from the word target, a per-type time
   per activity, and the video durations from the pack. The arc review uses it to spot overloaded
   lessons; no gate fails on it.
4. **Start clean.** No v1 plan is converted. v1 plans stay on disk as the record of `/a1-v1/` and
   are never read by the new engine. The arc author may look up which textbook pages they cited and
   re-verifies each citation through the MCP before using it (R-11).

Resolved earlier in r2: form-grain vocabulary (kept for stress and for what a lesson teaches; as a limit on what a writer may use it was lifted in revision 8, §4), core vs incidental, planned vs observed learner
state, lesson-grain immersion, quantity-only deterministic title check, dialogue fields,
`examples`/`errors` shapes, optional `phonetics` and `reading_passages`.

Added after #8403: a text quote is anchored by **verbatim text + content hash + (source file,
page)**. `chunk_id` is a convenience locator only — textbook chunk ids shifted on a re-chunk and
left 93 wiki registries dangling, so an id alone is not a stable reference.
