# Fresh lesson-based build — plan and evidence-pack schema (design)

> Sub-epic #8397, child 3. Status: **design draft r2** (r1 reviewed by AGY `gemini-3.8-flash-high`, task
> `design-review-8397-schema-r1`: REVISE, 7 findings, all folded in) by the curriculum-upgrade driver, for
> cross-family design review and operator correction. Implements requirements R-01…R-09, R-22,
> R-24…R-28, R-30 of [`fresh-build-requirements.md`](fresh-build-requirements.md). No code yet.

## 1. Three artifacts, one owner each

| Artifact | Path | Owns | Does not own |
| --- | --- | --- | --- |
| **Level arc** | `curriculum/l2-uk-en/plans/<level>/_arc.yaml` | module order, one-sentence job per module, the progression table (letters/sounds, grammar, vocabulary themes), learner-position checkpoints | lesson detail |
| **Module plan** (schema v2) | `curriculum/l2-uk-en/plans/<level>/<slug>.yaml` | `lessons[]`: each lesson's job, inventory, steps, activities, videos, rationale, targets | source text, word facts |
| **Evidence pack** | `curriculum/l2-uk-en/evidence/<level>/<slug>.yaml` + `.lock` (sha256), plus the shared level word store `evidence/<level>/_words.yaml` | the frozen source material and verified word records that lessons cite by id | sequence, pedagogy decisions |

Sequence exists in exactly one place (the plan). Facts exist in exactly one place (the pack). That
is the structural answer to the Module 1 failure, where plan, derived lesson map and content each
carried their own version of "what this module teaches".

## 2. Module plan v2

Top-level fields kept from v1: `module`, `level`, `sequence`, `slug`, `version`, `title`,
`subtitle`, `focus`, `objectives`, `connects_to`, `prerequisites`, `register`, `changelog`.

Removed from the plan (they move): `content_outline` and the module-level `word_target`
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
    kind: teach                             # teach | practice | recap | checkpoint
    job: "One sentence: what the learner can do after this lesson that they could not before."
    rationale: "Why here, why in this order; what English speakers get wrong."   # replaces wiki prose
    minutes: 60                             # plan estimate, not a gate
    word_target: 1200                       # minimum, per lesson (R-04)
    inventory:
      phonetics: { letters: [А, О, У], sounds: [] }   # optional block; A1 letter modules only
      grammar: []                           # named points, each traceable to an evidence id
      vocabulary:
        core:                               # actively taught; enters learner state as "known"
          - lemma: мама
            evidence: W-012
            forms: ["noun:anim:f:v_naz", "noun:anim:f:v_zna"]   # authorised forms this lesson (R-22)
        incidental:                         # allowed in dialogues/situations, glossed inline,
          - { lemma: кава, evidence: W-040, forms: ["noun:inanim:f:v_zna"] }  # NOT counted as known
        recycled: [ … ]                     # must already be core in learner state
    steps:                                  # textbook shape: theory step → practice, repeated (R-27)
      - id: s1
        teach: "Point taught, in one sentence."
        evidence: [T-003, T-007]            # pack ids; every id must be used and cited (R-28)
        practice: [a1, a2]                  # activity ids below
      - id: s2
        …
    consolidation: [a5, a6, a7]             # the larger practice block closing the lesson
    activities:
      - id: a1
        type: quiz
        placement: inline                   # inline | workbook
        focus: "What it checks."
        model: X-004                        # optional: textbook exercise it is modelled on
    videos:
      - evidence: V-002                     # never a bare URL; the pack verifies it (R-18)
        use: "Where in the lesson and why."
    dialogue:
      situation: "…"
      setting: "…"                          # place and objects, as v1 required
      speakers: [ { name: Оксана, role: waiter, gender: f }, { name: Тарас, role: customer, gender: m } ]
      register: informal                    # informal | formal
      target_grammar: "…"                   # what the dialogue exists to show
      evidence: [T-010]
    reading_passages: []                    # optional; B2+ and seminar tracks later
```

Rules the validator enforces (all deterministic):

1. `lessons` is non-empty; `n` is 1..N contiguous; exactly one lesson has `kind: recap` and it is
   the last (checkpoint modules: all lessons `checkpoint`, no new inventory).
2. The recap lesson has empty `inventory.vocabulary.core`, empty `phonetics` and `grammar`, and no `teach` steps that introduce material.
3. Every `evidence` id exists in the locked pack; the pack hash matches `evidence_ref.sha256`.
4. Every `inventory.vocabulary.recycled` lemma and every grammar point used but not introduced is
   present in the learner state computed from the arc and earlier lessons.
5. Union of lesson `core` inventories equals what the arc says this module introduces — nothing
   more, nothing less. The plan carries a generated, structured `scope` block (letter count and
   list, grammar points, core-lemma count) **derived from the lessons by the validator, never
   typed**; the landing page renders its numbers from `scope`. Deterministic title check is
   limited to explicit quantities and enumerated letter lists found in `title`/`subtitle`, which
   must equal `scope` (a subtitle naming seven letters over lessons teaching 33 fails here).
   Broader "does the title describe the job" is judged in the cross-family plan review.
6. Every `teach` step has at least one practice activity; activity types are in the level's
   allowlist; inline/workbook counts meet the per-lesson minimums.
7. No Ukrainian word form, stress or morphology appears in a plan except as a reference to a pack
   word record; every `forms` tag cited in a lesson must exist in that word record.

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
words:        # W-…  one record per lemma **sense** (homonym-safe)
  - id: W-012
    lemma: мама
    entry: { source: ulif|vesum|atlas, key: [мама, 1] }   # (spelling, homonym_index) per #8400
    pos: noun
    cefr: { level: A1, source: puls }
    forms:                                  # only the forms this module uses
      - { form: мама, tags: "noun:anim:f:v_naz", stressed: "ма́ма", stress_source: ulif|trie|pending }
    gloss_en: "mom"
    shadow: { russian_shadow: false }
videos:       # V-…
  - id: V-002
    url: …
    channel: …                              # corpus channels first (R-18 / Q6)
    checked: { http_status: 200, date: 2026-… }
    transcript_ref: …                       # corpus subtitle record when we have it
standard:     # S-…  State Standard 2024 lines this module serves
```

Rules:

- Built by a tool run (MCP batch calls), never typed from memory. The builder records the exact
  source hashes in `built_with`.
- Frozen by `.lock`. Any edit changes the hash and invalidates the plan's `evidence_ref` until the
  plan is re-reviewed.
- `stress_source: pending` is legal while the ULIF base is not ready (R-23); a build refuses a
  lesson whose cited forms are still `pending`. Planning is not blocked; building is.
- The pack contains **no sequencing and no pedagogy prose**.

## 4. Learner state at lesson grain (R-14, R-30)

Two layers, because a plan cannot know everything a built lesson will contain:

- **Planned state** (available at plan time, used by plan-validate and as the writer's allowlist):
  a project-wide base layer of closed-class function words and proper-noun handling (as
  `scripts/audit/checks/learner_state.py` already does) + all `core` items of earlier modules and
  of lessons `1..n−1`. `incidental` items never enter it.
- **Observed state** (after a lesson is built): a post-build index of what the lesson actually
  exposed — forms and exposure counts. It feeds recycling decisions and later lessons' exposure
  counts. A built lesson that uses a lemma outside planned state + its own inventory fails the
  inventory gate; it does not silently extend the state.

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

Exactly four things: the lesson's plan entry; the evidence records that entry cites; the learner
state for that position with the immersion rule for it; the fixed style card (ULP practices, voice,
four tabs). Not the other lessons' plans, not the whole pack, not any earlier edition.

The recap writer additionally receives the **built** lessons `1..N−1` of the same module — this is
the only place built content is an input, and only within the module being built.

## 6. Gates implied (all deterministic unless stated)

| Gate | Checks |
| --- | --- |
| plan-validate | §2 rules 1–7 |
| pack-verify | every quote matches its chunk; every word record re-verifies against current sources; every video URL answers |
| coverage | every evidence id cited by the lesson plan appears in the lesson and in Ресурси |
| inventory | lesson introduces exactly its `inventory.new`; nothing outside learner state + new |
| stress | every stressed form in the lesson matches the pack's form record for that grammatical context |
| immersion | existing structural gates, keyed by learner position |
| review | cross-family content review (LLM) — the only non-deterministic gate |

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

Resolved earlier in r2: form-grain vocabulary, core vs incidental, planned vs observed learner
state, lesson-grain immersion, quantity-only deterministic title check, dialogue fields,
`examples`/`errors` shapes, optional `phonetics` and `reading_passages`.

Added after #8403: a text quote is anchored by **verbatim text + content hash + (source file,
page)**. `chunk_id` is a convenience locator only — textbook chunk ids shifted on a re-chunk and
left 93 wiki registries dangling, so an id alone is not a stable reference.
