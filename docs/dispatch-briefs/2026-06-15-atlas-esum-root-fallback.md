# Dispatch — Atlas etymology fill: ЕСУМ root-fallback (#2882)

Close the ~740-word core-vocab **etymology** gap. Strategy: `docs/atlas-data-coverage-strategy.md`
("etymology" row). Root cause: `_etymology(conn, lemma)` in `scripts/lexicon/enrich_manifest.py`
queries `esum_etymology` by exact `lemma`, but ЕСУМ is **root-based** (36K entries) — a
*derived* word (e.g. `хвастливий`) misses, while its root (`хвастати`) is present. Fill by
falling back to the etymological ROOT when the exact lemma misses.

## #M-4 — verify against the REAL db before coding
Inspect `esum_etymology` (cols `lemma, etymology_text, cognates, vol, page`) in the real
`data/sources.db`. Confirm with raw queries: `хвастливий` misses, `хвастати` hits (the
canonical example). Paste raw output.

## Implementation (numbered)
1. Confirm worktree (`git status`).
2. In `_etymology`, when the exact-lemma ЕСУМ lookup yields nothing, attempt a **root-fallback**:
   derive candidate roots from the lemma by stripping common Ukrainian derivational suffixes
   (adjectival `-ливий/-ний/-ський/-овий`, deverbal/nominal `-ння/-ість/-ач/-ник`, diminutive
   `-ок/-ик/-ка`, etc. — keep the list SMALL and conservative) and the existing
   `_etymology_lookup_variants`, then look up each candidate in `esum_etymology`. Reuse any
   stemming/root helpers already in `enrich_manifest.py` / `derivational_morphology.py` —
   check before writing new logic.
3. On a root hit, return the etymology with a source label that is HONEST about the indirection,
   e.g. `"ЕСУМ (etymology of root «<root>»)"` — never imply the derived form has its own ЕСУМ entry.
   Cap to ONE best root (most specific / longest match) to avoid wrong-root noise.
4. **Conservatism > coverage:** if no confident root match, return None (leave the gap) rather
   than attach a doubtful etymology. A wrong etymology is worse than a missing one (#1 quality).
5. Tests in `tests/test_lexicon_enrich_manifest.py` (mirror existing `_conn()` fixtures with an
   in-memory `esum_etymology` table): derived word → root etymology with the honest label;
   unrelated word → None; exact-lemma hit still returns the direct entry (no regression).
6. `.venv/bin/python -m pytest tests/test_lexicon_enrich_manifest.py -q` green. `ruff check` clean.
7. **Code-only — do NOT run `make atlas`, do NOT commit `lexicon-manifest.json`/fingerprint.**
8. Commit `feat(lexicon): ЕСУМ root-fallback for derived-word etymology (#2882)` +
   `X-Agent: grok-build/atlas-esum-root`. `git push -u origin <branch>` + `gh pr create`. NO merge.

## Acceptance
A derived word absent from ЕСУМ but whose root is present now gets a root-labelled etymology;
unrelated words stay None (no fabricated etymology). Exact-lemma path unchanged. Tests green.
