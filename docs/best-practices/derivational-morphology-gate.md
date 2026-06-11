# Derivational-morphology acceptance layer for the VESUM gate (seminar tracks)

> **Status: IMPLEMENTED** — PR #2956 (`f7b88786da`, codex-impl + Claude adversarial review), 2026-06-10.
> Module: `scripts/lexicon/derivational_morphology.py`. Wired into the folk/seminar VESUM heritage fallback
> in `scripts/build/linear_pipeline.py::_resolve_folk_heritage_attested_missing`. This doc is the SSOT for
> WHY the layer exists, WHAT it accepts/rejects, and the regression contract. Companion:
> [`heritage-attestation-engine.md`](heritage-attestation-engine.md) (the shared classifier this builds on).

## Problem (evidence from 3 live kalendarna builds, 2026-06-10)

`_vesum_gate` flags every word absent from VESUM (~409K lemmas / 6.7M forms). VESUM does **not** enumerate
productive derivations, so rich C1 seminar prose keeps tripping it on **valid** Ukrainian:

- denominal adjective: `гаївковий` ← `гаївка` (dialect, engine-attested)
- deverbal adjective: `знеособлювальний` ← `знеособлювати` (standard, engine-attested)
- secondary imperfective: `виворожувати` ← `виворожити` (standard, engine-attested)

These are false positives — valid Ukrainian, just not enumerated. Each build hit a **different** one, so
per-word allowlist patches never converged (the correction loop traded one valid derivation for another).
`pymorphy3` confidence does **not** discriminate (compound coinage `двохоровий` scores 0.75 via dictionary;
valid `гаївковий` scores 0.17 via guess) — so a confidence threshold is unsafe.

Genuine coinages (`двохоровий`, `обрядознавчий`, `городалька`) MUST stay flagged — they are not productive
derivations off an attested base.

## What it builds on (do not duplicate)

- `scripts/lexicon/heritage_classifier.classify_surface_form(w)` (#2912) → `{classification, is_russianism, …}`.
  Attestation-based across VESUM ∪ Грінченко ∪ ЕСУМ ∪ СУМ-20 ∪ literary quotes. Authentic =
  `{authentic-archaism, dialect, historism, borrowing, standard}`.
- `_vesum_gate` consumes it (#2931) + a morphology fallback (#2950): for a missing word it offers the
  pymorphy3 lemma + a `не`-stripped base to the classifier and accepts iff a candidate is authentic & not
  russianism. **Russianism guard (critical):** never rescue a form the classifier directly flags
  `is_russianism` — else `діюча`→lemma `діяти` (standard) leaks. (Validated: russianism battery, 0 leaks.)

## The layer (#2956)

`derivational_morphology.py` exposes a small, deterministic **suffix-rule table** that, given a still-missing
seminar/folk surface form, emits **full base lemmas only** (never bare stems) for three productive classes:

- **denominal adjectives** → noun base (`гаївковий` → `гаївка`)
- **deverbal adjectives** → verb base (`знеособлювальний` → `знеособлювати`)
- **conservative secondary imperfectives** → perfective base (`виворожувати` → `виворожити`)

`_resolve_folk_heritage_attested_missing` feeds each proposed base to `classify_surface_form` and accepts the
surface form **iff** a base is authentic-and-not-russianism **AND** the surface form is not itself
`is_russianism` (the generalized `діюча` guard). Policy stays in the gate; the module only proposes bases.
An explicit missing-word fallback block keeps standard/dialect homographs from being accepted when VESUM
reported the surface missing.

## Regression contract (acceptance battery — `tests/test_derivational_morphology.py` + `tests/test_vesum_heritage_attestation.py`)

- **VALID — must PASS the gate:** `гаївковий`, `знеособлювальними`, `виворожувати`, `виворожують`, plus existing
  `другоє`, `ягілки`, `гагілку`, `незгладжений`.
- **RUSSIANISM — must STAY FLAGGED:** `діюча`, `протиріччя`, `получаючий`, `поступаючий`, `находячийся`,
  `глазний`, `вкусний`, `слідувати`, `оказувати`, `заказувати`, `настаювати`, `решати`.
- **DIRECT-STANDARD calque participles — unchanged (a separate STYLE concern, not blocked here):** `бажаючий`,
  `оточуючий`, `керуючий`, `завідуючий`, `слідуючий`. (These pass via dictionary attestation; the active-participle
  style preference is out of scope for this gate.)
- **COINAGE — must STAY FLAGGED:** `двохоровий`, `обрядознавчий`, `городалька`.
- Full vesum suite green (65 tests as of 2026-06-11).

The canonical leak test is `діюча`: any base-derivation rule MUST keep `is_russianism` surface forms flagged.

## Stage 2 (not yet implemented — TODO in the rule table)

- **affective folk morphology** (`-оньк-/-еньк-/-ечк-/-иц-/-ятк-`, e.g. `ніженьки`, `горілонька`, `доріженька`) —
  expected to recur heavily in folk modules (diminutives in songs).
- **prefixal iteratives** (`по-…-увати`, e.g. `почитувати`, `походжувати`).

## Why it matters beyond folk

The layer + the heritage engine clear the VESUM false-positive wall for all morphologically-rich seminar
tracks — it is the durable unblock for **lit / hist** and the path to opening **ruth / oes** (philology tracks
with even more archaic/dialectal morphology). Build once, two consumers: the Word Atlas renders heritage badges;
`_vesum_gate` consumes the verdict (allow authentic, block russianisms).
