# Dispatch brief — fix Atlas §4 heritage classifier (STRICT Grinchenko/ESUM) + §1 non-lemma entries

**Agent:** Codex (gpt-5.5, xhigh) · worktree · commit + push + PR (NOT draft) · no auto-merge.
**Base:** `codex/atlas-finalize-all` (origin). This branch already contains the GOOD work from the prior
dispatch — §1 vocab rebuild (138→2167 lemmas), §2 Грінченко-attestation removal, §3 soviet-caveat
re-scoping — all of which are §8-gate-clean. You are fixing two remaining gate failures only.

## Why this dispatch exists
The prior dispatch (`atlas-finalize-all`) implemented §1–§4 but **died stuck in an enrichment wait-loop and
never committed** (it backgrounded the manifest build in an interactive shell and polled it with empty stdin
forever — DO NOT repeat this; see "Regenerate, DO NOT HANG" below). Running its own conformance test reveals
**128 §8 violations** it never saw:
- **13× `lemma_in_vesum`** — non-lemma entries leaked into the manifest.
- **115× `heritage_evidence_required`** — the §4 heritage classifier **over-fires** (≥84% false positives:
  `бути`→archaism, `автобус`→dialect, `журналіст`→historism, `книга`→historism, `білий`→archaism, …),
  and its attestation sources (СУМ-20 / СУМ-11 / wiktionary) are all rejected by the §8 gate.

## Fix 1 — §1 non-lemma manifest entries (`scripts/lexicon/build_data_manifest.py`)
The 13 failing entries: `Богдане, Давай!, Маріє, Олено, Смачного!, Соломіє, Тарасе, Ходімо!, бірка, в/у,
прийом, у/в, і/й`. Root cause: A2 `word` fields carry inflected/phrase/notation surface forms, not lemmas.
- **Vocative proper names** (`Богдане, Маріє, Олено, Соломіє, Тарасе`): map to nominative lemma
  (`Богдан, Марія, Олена, Соломія, Тарас`) if that nominative is a taught lemma; else drop. Investigate the
  source `vocabulary.yaml`.
- **Interjection / multi-token phrases** (`Давай!, Смачного!, Ходімо!`): not lemmas → drop from the
  Atlas manifest (Atlas is lemma-keyed). They stay in course vocab, just don't get an Atlas page.
- **Orthographic variant-pair notations** (`в/у, у/в, і/й`): not lemmas → drop the slash-notation entries.
  (If clean single-token `в`, `у`, `і`, `й` are wanted as Atlas pages, that's a separate add — not required here.)
- **`бірка`, `прийом`**: these are REAL words — find the ROOT CAUSE of the lemma_in_vesum miss (stress mark
  e.g. `прийо́м`? VESUM variant lookup? `_strip_stress`/`_lookup_variants` in the gate). Do NOT delete a
  legitimate taught lemma — fix the normalization so it resolves in VESUM.

**Goal:** 0 `lemma_in_vesum` violations, without dropping any legitimate taught lemma.

## Fix 2 — §4 heritage classifier: STRICT Grinchenko-1907/ESUM only (`scripts/lexicon/heritage_classifier.py`)
**DECISION (user, 2026-06-12 — strict, correctness over coverage):** a heritage classification
(`authentic-archaism` / `historism` / `dialect` / `borrowing`) may fire **ONLY when Grinchenko-1907 OR ESUM
attests the headword**, and that Grinchenko/ESUM attestation MUST be attached to
`heritage_status.attestations` so the §8 gate's `_has_pre_soviet_attestation` passes.
- **The §8 gate `scripts/audit/validate_atlas_conformance.py` is the SSOT and MUST NOT be modified.**
- **Remove** the loose mapping that fires on СУМ-20 / СУМ-11 / wiktionary / any `search_heritage` hit. Those
  sources do NOT justify a heritage badge.
- `classify_lemma` MUST return `standard` (no badge) for `бути, автобус, журналіст, книга, білий, гарний,
  адреса, банкір, …` — every word lacking a Grinchenko/ESUM attestation.
- For words Grinchenko-1907 or ESUM DOES attest as archaic/dialectal/historical: fire the classification AND
  attach the Grinchenko/ESUM attestation. **Accept** that `гетьман/кобіта/вельми` may now read as `standard`
  if Grinchenko/ESUM don't cover them — this is the accepted tradeoff.
- Keep `is_russianism` word-level РУСИЗМ badges unchanged (e.g. `міроприємство`) — separate path.
- Design §5 discipline: no badges from heuristics; only from Grinchenko/ESUM tool results.

## Regenerate, DO NOT HANG
1. Regenerate the manifest by running the builder/enricher **as FOREGROUND blocking commands with an explicit
   `timeout`** — e.g. `timeout 3600 .venv/bin/python scripts/lexicon/build_data_manifest.py` then
   `timeout 3600 .venv/bin/python scripts/lexicon/enrich_manifest.py` (use the real entrypoints).
   **DO NOT** launch the build in a backgrounded/interactive shell and poll it with empty stdin — that is the
   exact hang that killed the prior run. Run foreground; if a command exceeds its timeout, STOP and report.
   The slovnyk cache at `data/lexicon/slovnyk_cache/` (~2,143 files) is populated → enrichment is fast.
2. `cd starlight && npm run build` (skip `npm ci` if `node_modules/` is present) — verify it builds.
3. **Gates GREEN (real vesum is present locally at `data/vesum.db`):**
   - `.venv/bin/python -m pytest tests/test_atlas_conformance.py tests/test_heritage_classifier.py tests/test_lexicon_build_manifest.py tests/test_lexicon_enrich_manifest.py -q` → ALL pass, **0** conformance violations.
   - `.venv/bin/ruff check scripts/ tests/` → clean.

## §M-4 quality sample (REQUIRED in your final report — quote raw evidence, no "I verified X")
Dump classified/rendered evidence for: `прапор` (word CLEAN, soviet caveat only on СУМ-11 card), `банк` (same),
`міроприємство` (word-level РУСИЗМ), `вода`/`голосний` (synonyms omitted-not-wrong), `батько` (synonyms
тато/отець), `вікно` (no Грінченко / no Russian), `бути`/`автобус`/`книга` (now `standard`, no heritage badge),
**plus every word that RETAINED a heritage badge** (list each + its Grinchenko/ESUM attestation). Confirm 0
Russian strings in built dist for sampled pages. Report per-category counts (archaism/historism/dialect/
borrowing) — expect SMALL numbers.

## Finalize (numbered)
1. Work inside the dispatch worktree (branched from `origin/codex/atlas-finalize-all`).
2. Implement Fix 1 + Fix 2.
3. Regenerate manifest (FOREGROUND + timeout).
4. `npm run build`.
5. pytest (4 files) + ruff → green; quote raw output.
6. §M-4 quality sample in the report.
7. Commit (conventional; `X-Agent: codex` trailer). Squashing the WIP preservation commit is fine.
8. `git push -u origin <branch>`.
9. `gh pr create` — **NON-draft**, base `main`, no auto-merge.
10. **Out of scope / DO NOT TOUCH:** `validate_atlas_conformance.py` §8 gate, `.python-version`, `.yamllint`,
    `.markdownlint.json`, any `curriculum/l2-uk-en/*/*` course content, status/audit/review artifacts.

#M-4 preamble: every verifiable claim (tests pass, ruff clean, violation counts, build success, PR URL) must
quote the raw command + output line. A claim without a quoted tool line is treated as unverified.
