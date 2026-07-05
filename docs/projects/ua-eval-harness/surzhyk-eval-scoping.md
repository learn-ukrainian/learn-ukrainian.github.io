# Surzhyk spoken-register eval — scoping (#4287)

- status: **FLEET-REVIEWED scoping** (agy research 2026-07-05 · codex + cursor design reviews 2026-07-05,
  findings folded). Gates fixture-building; fixtures are a later PR with their own review.
- parent: #2156 (explicitly out of its scope; this is the follow-on shape)

## 1. What this eval measures (the "define the task" decision)

**Chosen task: detection + variety classification.** Given a Ukrainian text span with carrier context, the
system under eval must (a) detect Russian-contact features and (b) classify the variety correctly.

**v1 scored labels (5, collapsed per codex IAA review):**

`surzhyk | dialect_or_regional_heritage | non_contact_ukrainian | code_switching | insufficient_evidence`

- `non_contact_ukrainian` merges standard + colloquial-standard for scoring; `register` survives as item
  metadata, not a scored class.
- `learner_error` is DEFERRED from v1 (no learner metadata in available sources → inter-annotator agreement
  vs `surzhyk` would collapse). Documented as a v2 candidate gated on a source with learner identity.
- `standard_with_calque` is NOT a #4287 class — written-standard calques are #2156's axis; UA-GEC-derived
  items feed #2156 gold only (double-scoring guard in §4).
- `code_switching` is a small boundary-trap set, not a balanced class.
- `insufficient_evidence` is a first-class gold label AND a legitimate system answer (the abstention path —
  a reviewer that says "cannot determine" must be scorable, not penalized as wrong-by-default).

**Explicitly NOT chosen (issue non-goals honored):** learner-facing correction (the pedagogy/register stance
is an unmade curriculum decision); sociolinguistic description; corpus-scale scoring (also empirically
impossible — see §4: no public labeled spoken-surzhyk corpus exists).

**Why classification is the load-bearing axis:** the dangerous failure is the FALSE POSITIVE — flagging
authentic dialect (Hutsul, Polissian, Galician regionalisms) or colloquial standard as "surzhyk". That does
active decolonization damage. Prior art: the heritage-defense layer (`search_heritage`; кобета/кобіта).
This eval generalizes it: **score the boundary, not just the hit rate.**

## 2. Boundary taxonomy (reference definitions + annotation tests)

Reference definitions for all six linguistic phenomena (surzhyk / dialect / colloquial standard /
code-switching / learner error / standard-with-calque) with distinguishing features:

| variety | systematicity | level of mixing | example signal |
|---|---|---|---|
| Surzhyk | unsystematic per-speaker | INTRA-word/phrase blend (RU stem + UA inflection; RU function words in UA syntax) | «шо ти дєлаєш», «канєшна» |
| Dialect / regional heritage | systematic, territorial, historically continuous | own phonology/lexicon/morphology | Hutsul «файний», Galician «кобіта» |
| Colloquial standard | systematic register of standard UA | register markers, not contact forms | «та ну», elisions |
| Code-switching | discourse-level, pragmatic | INTER-sentential alternation between intact codes | full-RU quote in UA narration |
| Learner error (v2) | unsystematic, developmental | any level, inconsistent | variable case errors |
| Standard + calque (→ #2156) | standard-register carrier | lexical/phraseological calque | «приймати участь» in a news article |

**Required annotation fields per item (codex: t1–t4 alone are insufficient for real GRAC extracts):**

- `t1_mixing_level`: intra_word | intra_phrase | inter_clause
- `t2_territorial_attestation`: heritage-layer result (Грінченко/ЕСУМ/regional; tool-verified at build)
- `t3_carrier_register`: spoken_interview | spoken_public | written_informal | …
- `t4_speaker_consistency`: consistent | variable | unknown
- `contact_feature_type`: lexeme | function_word | morphosyntax | phonetic_spelling | phraseological_calque | clause_switch
- speaker/context metadata: region, genre/setting, quote-or-reported-speech flag, speaker id IF the source
  provides it (PII policy below)
- `transcription_normalization`: verbatim | normalized (+ policy version)
- `annotation_confidence`: high | medium | low

**IAA pilot gate (codex — MANDATORY before the fixture build):** pilot 20–30 items with two annotators +
adjudication. If agreement on the 5-class scheme is unacceptable, collapse labels further BEFORE building
the full set. No 100-item build on an unvalidated label scheme.

**PII policy:** spoken-interview items must carry no personal identifiers; speaker id is an opaque
source-local code or absent.

## 3. Schema + storage (cursor — the two-layer pattern, no shared-schema fork)

- Findings stay in the canonical `ua_contact_quality_evidence.v1` envelope — `validate_finding` is a
  closed validator; NO new top-level fields. Gold labels live in a **fixture wrapper schema**
  `surzhyk_variety_fixture.v1` + `finding.metadata.eval_gold` (variety_gold, distinguishing tests,
  heritage_attestation, eval_axis) — mirroring the `ua_gec_gold_fixture.v1` two-layer pattern.
- New profile `variety_eval` added to `PROFILES` (small schema PR) before any `build_evidence_record` use.
- Storage: `data/surzhyk-variety-gold/` (NOT `tests/fixtures/curriculum_qg/` — that lane is curriculum
  calibration). New thin `VarietyGoldFixtureAdapter` in `qg_adapters.py`; ingest script mirrors
  `ingest_ua_gec_gold.py` and FAILS if a dialect/heritage negative lacks tool attestation.
- **Double-scoring guard:** `metadata.eval_gold.eval_axis: variety_classification` + ingest lint asserting
  no shared id/excerpt-hash with the #2156 gold sets.
- Scoring: a NEW `variety_gold_metrics.v1` block with a **cost matrix** (false-surzhyk-on-dialect penalized
  hardest, matching the #2156 bakeoff's asymmetric-scoring logic) — not bolted onto contact_calque F1.

## 4. Data sources (agy web-grounded research 2026-07-05; licenses re-verified at build time)

| source | content | labels | access | fixture use |
|---|---|---|---|---|
| **GRAC spoken subcorpus** | transcribed interviews/speeches, region-sortable | spoken, regional, dialect | research use — **NO verified redistribution right** (codex checked; treat like a closed corpus for git purposes) | PRIMARY — but **pointer-only in git**: `grac:doc_id/subcorpus/region` + span offsets + ≤160-char excerpt (schema cap) + license line; NO verbatim concordance dumps; local fetch via `query_grac` at build |
| UA-GEC v2.0 | written GEC corpus, Fluency/Calque tags | written | CC BY 4.0 (repo-verified 2026-05-19; re-verify — one research reply said BY-SA) | feeds **#2156 only** (the standard_with_calque exclusion) |
| Del Gaudio corpus | Kyiv spoken surzhyk recordings | spoken | **closed** (author permission) | ❌ |
| Oldenburg corpus (OCUS) | spoken family interviews | spoken | **closed** (PII) | ❌ |
| HF / UberText social crawls | mixed sociolects | **unlabeled** (no surzhyk-tagged HF dataset exists) | varies | raw material for manual curation only, never gold as-is |

**Consequence:** no public labeled spoken-surzhyk gold exists → the v1 set is hand-curated (50–100 items
AFTER the IAA pilot), GRAC-pointer-based, heritage-attested, license-clean by construction.

## 5. Reviewer guidance (ships with the fixture set)

Non-standard ≠ defect. (1) A form is condemnable as surzhyk ONLY with a failed heritage-attestation check
AND a positive contact-feature test; (2) dialect/colloquial labels are variety classifications, NEVER
"errors"; (3) uncertain → `insufficient_evidence`, never default-to-surzhyk (and the gold set scores that
answer fairly).

## 6. Build order

Scoping (this doc) → schema PR (`variety_eval` profile + wrapper schema + adapter skeleton) → **IAA pilot
(20–30 items, 2 annotators, adjudication)** → label-scheme freeze → fixture build (50–100) → scorer wiring.
Each step its own reviewed PR. Machinery prerequisites (#4306/#4307/#4308) are already merged.
