# Atlas §8 `lemma_in_vesum` gate — VESUM-lookup false positives

**Date:** 2026-06-15 · **Issue:** #3197 follow-up · **PR:** #3210 ·
**Category:** `atlas-conformance-vesum-false-positives`

## What broke
A full `make atlas` regen (run to ship the #3197 antonym-noise cleanup live and
refresh a badly-stale committed manifest — the regen diff was +120K lines) made
`verify_manifest` report **4 §8 conformance violations** under `lemma_in_vesum` and
abort the commit (`VERDICT: do NOT commit`). The 4 lemmas: `Афіни`, `Чернівці`,
`УЗД`, `хвастливий`.

## Root cause
**All 4 were gate false-positives — zero content bugs.**
The `lemma_in_vesum` gate (`scripts/audit/validate_atlas_conformance.py`) proves a
single-word Atlas head is a real Ukrainian word by exact-matching it against VESUM's
`forms` table. Three independent defects made it reject valid words:

1. **Casefold vs canonical-case storage (the big one).** `_lookup_variants`
   casefolded every query (`Афіни`→`афіни`, `УЗД`→`узд`) before an exact-match
   `SELECT ... WHERE lemma=? / word_form=?`. But VESUM stores **proper nouns and
   abbreviations capitalized**. Deterministic proof: `lemma=Афіни` → match,
   `lemma=афіни` → no match. SQLite's `NOCASE` collation folds only ASCII, not
   Cyrillic, so it can't paper over this. Net: the gate false-flagged *every*
   capitalized VESUM entry. (`verify_words` MCP found all three; the gate didn't.)
2. **Suffix-blind proper-noun exemption.** `_is_proper_noun_entry` matched pos
   exactly against `{"proper noun","proper name"}`, but real manifest tags carry a
   morphology suffix (`proper noun:pl` for `Афіни`/`Чернівці`) → exemption never
   fired.
3. **No allowance for VESUM gaps.** `хвастливий` is authentic Ukrainian — Грінченко
   1907 «Хвастливий = хвастовитий» (Фр. Пр. 92), ЕСУМ псл. *хвастати, СУМ-20 «те
   саме, що хвалькуватий» — but absent from VESUM's tables. The gate treated VESUM
   membership as *sufficient* proof of validity; it is only *necessary*. Absence ≠
   Russianism (the кобета / блискучий heritage-defense lesson).

Latent because the offending lemmas were **new vocab** not present in the previously
committed (stale) manifest, so the gate only saw them on the orchestrator's first
real regen — same shape as #3124 (`fixture-only-feature-latent-gate-break`), one
layer down: #3124 wired the conformance suite into `verify_manifest`; this is the
conformance logic itself being wrong on real data.

## Prevention
- `_lookup_variants` now probes **both** the casefolded and case-preserved form.
- `_is_proper_noun_entry` matches the **base** pos (strips the `:suffix`).
- `_VESUM_GAP_HERITAGE_LEMMAS`: a tiny, **per-entry-cited** allowlist for VESUM-gap
  words attested in Грінченко/ЕСУМ/СУМ-20 (`хвастливий`).
- 3 regression tests in `test_atlas_conformance.py`; the real regenerated manifest
  goes 4 → 0 violations under the fixed gate.
- **Class-level fix DONE (#3211 / PR #3218):** the heritage allowlist was a stopgap;
  the robust fix shipped — a `sources.db` heritage fallback (`HeritageLemmaLookup`:
  Грінченко headword / ЕСУМ lemma) is consulted on every VESUM miss before flagging,
  so the gate **self-heals** on any heritage-attested VESUM gap. Proven: with the
  allowlist emptied the real manifest still passes 0 violations (`хвастливий` resolved
  by Грінченко alone). `_VESUM_GAP_HERITAGE_LEMMAS` retained ONLY as the offline
  fallback (no sources.db, e.g. CI — which already skips the gate without VESUM).

## Lesson
A deterministic "is this a real word?" gate that consults ONE dictionary inherits
that dictionary's coverage and storage conventions. Case-normalize to match the
store (don't assume ASCII-fold semantics on Cyrillic), strip morphology tags before
set-membership checks, and treat single-dictionary absence as *suspicion*, not
*proof of invalidity* — cross-check the heritage sources before flagging an
unfamiliar Ukrainian word.
