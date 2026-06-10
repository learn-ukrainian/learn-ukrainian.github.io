---
title: "Heritage Attestation Engine — shared authentic-Ukrainian classifier (Word Atlas render + VESUM gate)"
status: DRAFT (2026-06-10)
owner: folk driver (gate consumer) + Atlas/lexicon lane (render consumer) — needs orchestrator + user sign-off
relates_to:
  - docs/best-practices/word-atlas-design.md (§5 decolonization layer, §6 heritage_status — the RENDER consumer)
  - docs/best-practices/v7-design-and-corpus.md (V7 + corpus SSOT, #M-11)
  - "#2882 (lexicon enrichment — heritage classification, IN FLIGHT)"
  - "#2899 (folk slovnyk.me attestation allowlist — the folk-side stopgap)"
  - scripts/build/linear_pipeline.py::_vesum_gate (the GATE consumer)
  - scripts/lexicon/enrich_manifest.py (the lexicon enrichment generator)
---

# Heritage Attestation Engine

## TL;DR

VESUM is the modern-standard morphological dictionary — **one** source of authentic-Ukrainian
truth, **not the authority**. Today `vesum_verified` treats *"not in VESUM"* as *"bad form /
russianism,"* which **false-flags authentic archaic / poetic / dialectal Ukrainian** — `другоє`
(«на другоє літо поховаємо»), `ягілки`, `гагілки`, `риндзівки`, `перекличка` — that pervades folk,
lit (poetry/scansion), hist (chronicles), and oes/ruth (philology). The fix is a **shared,
deterministic Heritage Attestation Engine** that answers one question:

> *Is this surface form authentic Ukrainian (archaism / dialect / historism / borrowing / standard),
> or a russianism / surzhyk / calque?*

…by consulting the **full heritage corpus**, not just VESUM. **This engine is the same thing as the
Word Atlas's §5/§6 decolonization layer.** Build it **once**; it has **two consumers**:

| Consumer | Uses it to… | Status |
|---|---|---|
| **Word Atlas** (`scripts/lexicon/`, `/lexicon/{lemma}`) | render per-lemma heritage **badges** (authentic / Russianism / dialect / archaism…) | designed (word-atlas-design.md §5/§6); **classification not yet built** — #2882 Task 6, IN FLIGHT |
| **`vesum_verified` gate** (`linear_pipeline.py::_vesum_gate`) | **allow** a VESUM-missing form when the engine says *authentic*; **keep blocking** russianisms | #2899 ships a folk-only curated stopgap; should converge onto this engine |

## 1. The problem (evidence — folk kalendarna rebuild, 2026-06-10)

`vesum_verified` flagged, across rebuilds of `folk/kalendarna-obriadovist-zvychai`:

| Form | Reality | Source proof |
|---|---|---|
| `другоє` | authentic archaic `-оє` neuter, inside a **verify_quote=1.0** Kupala song «на другоє літо поховаємо» | `literary_texts` ЕУ-1955 `feaa5fa7_c0572` |
| `ягілка`/`гагілка`/`риндзівка`/`ягівка` | authentic regional spring-song genre names | slovnyk.me СУМ-20 / ВТС / Голоскевич / Франко |
| `перекличка` | **common modern word** VESUM simply lacks | slovnyk.me СУМ-20 + ВТС |
| `протиріччя`, `діюча`, `діючі` | genuine russianisms in **teaching prose** | absent everywhere; standard = `суперечність` / `чинна` |

`check_russian_shadow` **false-positives** on `другоє` (`matches_russian=1.0`) because it is a
homograph of Russian `другое` — proof that a russian-pattern heuristic **alone** cannot decide; only
**attestation** can. This is not folk-specific: lit (archaic `-оє`/`-ая`/`-ую` poetic endings),
hist (chronicle forms), oes/ruth (dialectology) hit it constantly.

## 2. Principle

> **Authentic-Ukrainian ⇔ attested in ANY heritage source with `is_russianism=false`.**
> **Russianism ⇔ attested in NONE + russian-pattern + has a Ukrainian standard alternative.**
> VESUM-absence **alone** is not evidence of a russianism.

## 3. The engine (deterministic, local — no live network, CI-reproducible)

A per-form/lemma classifier producing the Atlas §6 `heritage_status`:

```yaml
heritage_status:
  classification: authentic-archaism | dialect | historism | borrowing | standard
                  | russianism | surzhyk | calque | unknown
  attestations:                       # every verdict cites its grounding
    - source: literary_fts            # verify_quote of «на другоє літо поховаємо» @1.0
      ref: feaa5fa7_c0572
    - source: sum20
      url: https://slovnyk.me/dict/newsum/...
  is_russianism: false
  russian_shadow: true                # heuristic-only; NOT authoritative alone
  sovietization_risk: 0
  calque_warning: null
```

Sources (priority order; all local `data/sources.db` / `data/vesum.db`):

1. **VESUM** — modern standard (the current check). Present ⇒ standard, done.
2. **Грінченко 1907** — pre-Soviet attestation (highest heritage weight).
3. **ЕСУМ** — etymology (⚠ OCR-garbled cognates; Atlas lane is migrating etymology to Goroh +
   Wiktionary per the 2026-06-10 atlas session — use whichever the lexicon engine standardises on).
4. **СУМ-20 / slovnyk.me** (cached): СУМ-20, ВТС, Голоскевич 1929, Франко, slang_lviv — modern +
   heritage/regional dictionaries.
5. **`literary_texts` via `verify_quote`** — **surface-form attestation** (see §4): the inflected
   form appears in a real Ukrainian text.
6. **Антоненко-Давидович + UA-GEC** — calque/russianism evidence (demoted-but-recorded warnings).
7. **`check_russian_shadow`** — russian-pattern heuristic; a **negative signal only**, never
   sufficient to allow OR to block on its own (false-positives on archaic homographs).

## 4. Lemma vs surface form — the gate's extra requirement

The Atlas is **lemma-keyed** (`/lexicon/{lemma}` — `другий`, not `другоє`). The `vesum_verified` gate
sees **surface forms**, including **inflected archaic forms** with no lemma page. So the engine MUST
support a **surface-form path**, not only lemma classification:

- **Lemma path** (Atlas + gate): classify the lemma (`ягілка`, `перекличка`).
- **Surface path** (gate only): for an inflected form absent from VESUM (`другоє`), attest via
  (a) a heritage-dictionary surface hit, or (b) **`verify_quote` against `literary_texts`** — the
  form occurs verbatim in an attested Ukrainian text. `другоє` → 1.0 → authentic-archaism.

This is the one capability the lemma-centric Atlas design does **not** yet cover; it must be part of
the shared engine so the gate can use it.

## 5. The gate, precisely

`_vesum_gate`: after the existing VESUM fallbacks, for each still-missing surface form, ask the
engine. **Allow** iff `classification ∈ {authentic-archaism, dialect, historism, borrowing,
standard}` and `is_russianism=false`; otherwise keep it in `missing`. Report `heritage_attested_words`
(auditable). **Independence (teeth):** the russianism/calque/surzhyk gates (`russianisms_strict`,
`calques_clean`, `surzhyk_clean`, `bad_form_heritage`) stay **separate and active** — defense in
depth, so a calque attested *somewhere* is still caught. Scope: **seminar/literary levels** first
(folk, lit, hist, oes, ruth, bio); core a1–c2 unchanged until reviewed.

`данные/protiриччя`-class words: attested in none of 2–6 as authentic ⇒ stay flagged. `другоє` in a
verify_quote'd quote ⇒ allowed. `другоє` in bare prose with **no** attestation ⇒ flagged (writer
should quote it or it's unverified) — context resolves the homograph.

## 6. Convergence + rollout (coordination — READ THIS)

- The heritage **classification** is being built in the **Atlas/lexicon lane** (#2882 Task 6). It
  should be built **once** as a shared module (e.g. `scripts/lexicon/heritage.py`) exposing a pure
  function `classify(form, *, lemma=None) -> heritage_status` over local DBs, importable by both
  `enrich_manifest.py` (render) and `_vesum_gate` (gate).
- **The folk/lit gate work CONSUMES it — do not duplicate.** `#2899`'s
  `data/folk_heritage_attestations.yaml` collapses into a thin **curated override** layer on top of
  the engine (cited edge cases / corrections).
- **Until the engine lands:** `#2899`'s folk allowlist is the stopgap; **folk module re-fires that
  trip this (e.g. kalendarna `другоє`) are ON HOLD** rather than patched per-word.
- **Design-page coverage:** the Atlas POC §5 already specifies dialect/archaism/historism badges
  (`файний` galicianism is the worked example) — the *concept* is covered. **Gap to close:** the POC
  is lemma-based; **surface-form/inflected archaic attestation (§4) is not yet represented** — fold
  it into the engine + (optionally) an Atlas "forms" view.

## 7. Acceptance (when built)

- `другоє` (in a verify_quote'd quote) and `синєє`/`ягілки`/`перекличка` → PASS `vesum_verified`.
- `протиріччя`, `діюча`, a real russianism (`аранжировка`) → STILL FAIL.
- a1–c2 core gate behaviour unchanged (engine scoped to seminar/literary first).
- Every allow decision cites its attestation (no heuristic-only allows).
- Same classifier drives the Atlas badge and the gate verdict (one source of truth).
