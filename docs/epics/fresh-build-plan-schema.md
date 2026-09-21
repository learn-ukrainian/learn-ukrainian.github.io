# Fresh lesson-based build — plan and evidence-pack schema (design)

> Sub-epic #8397, child 3. Status: **design draft** by the curriculum-upgrade driver, for
> cross-family design review and operator correction. Implements requirements R-01…R-09, R-22,
> R-24…R-28, R-30 of [`fresh-build-requirements.md`](fresh-build-requirements.md). No code yet.

## 1. Three artifacts, one owner each

| Artifact | Path | Owns | Does not own |
| --- | --- | --- | --- |
| **Level arc** | `curriculum/l2-uk-en/plans/<level>/_arc.yaml` | module order, one-sentence job per module, the progression table (letters/sounds, grammar, vocabulary themes), learner-position checkpoints | lesson detail |
| **Module plan** (schema v2) | `curriculum/l2-uk-en/plans/<level>/<slug>.yaml` | `lessons[]`: each lesson's job, inventory, steps, activities, videos, rationale, targets | source text, word facts |
| **Evidence pack** | `curriculum/l2-uk-en/evidence/<level>/<slug>.yaml` + `.lock` (sha256) | the frozen source material and verified word records that lessons cite by id | sequence, pedagogy decisions |

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
      letters: [А, О, У]                    # letter modules only
      sounds: []
      grammar: []                           # named points, each traceable to an evidence id
      vocabulary:
        new: [ { lemma: мама, evidence: W-012 } ]
        recycled: [ … ]                     # must already be in learner state
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
    dialogue: { situation: "…", evidence: [T-010] }
```

Rules the validator enforces (all deterministic):

1. `lessons` is non-empty; `n` is 1..N contiguous; exactly one lesson has `kind: recap` and it is
   the last (checkpoint modules: all lessons `checkpoint`, no new inventory).
2. The recap lesson has empty `inventory.*.new` and no `teach` steps that introduce material.
3. Every `evidence` id exists in the locked pack; the pack hash matches `evidence_ref.sha256`.
4. Every `inventory.vocabulary.recycled` lemma and every grammar point used but not introduced is
   present in the learner state computed from the arc and earlier lessons.
5. Union of lesson inventories equals what the arc says this module introduces — nothing more,
   nothing less. **Title/subtitle claims are checked against this union** (a subtitle naming seven
   letters with lessons teaching 33 fails here).
6. Every `teach` step has at least one practice activity; activity types are in the level's
   allowlist; inline/workbook counts meet the per-lesson minimums.
7. No Ukrainian word form, stress or morphology appears in a plan except as a reference to a pack
   word record.

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
errors:       # E-…  learner-error evidence (UA-GEC, style guide)
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

`learner_state(level, module, lesson)` = everything introduced by all earlier modules plus lessons
`1..n−1` of this module: lemmas (with counts of exposures), grammar points, letters. It is computed
from the arc and the plans, not from built content, so it is available at plan time.

Immersion band lookup changes key from *module number* to *learner position*
(cumulative lessons + cumulative vocabulary). The thresholds themselves are carried over unchanged
from `IMMERSION_POLICIES`; the mapping table from today's module ranges to learner positions is
part of the arc deliverable and is reviewed with it.

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

## 7. Open design questions for the reviewer

1. Should `steps` be mandatory structure or guidance? Proposed: mandatory ids and evidence, free
   prose inside them.
2. One pack per module, or a shared level pack with per-module views, given heavy word reuse?
   Proposed: per-module pack for texts/exercises/videos, a shared **level word store** for `words`,
   referenced by id, to avoid 55 copies of `мама`.
3. Is `minutes` worth keeping if no gate reads it? Proposed: keep; the arc review uses it to spot
   overloaded lessons.
4. Migration: nothing is migrated. v1 plans stay in place for `/a1-v1/` provenance and are never
   read by the new engine (R-11).
