# Dispatch brief — wire kaikki IPA + etymology into the Word Atlas

**Agent:** Codex (gpt-5.5, xhigh) · worktree · commit + push + PR (NOT draft) · no auto-merge.
**Base:** `main`.
**Context:** The kaikki fillability assessment (PR #3038, merged) showed the kaikki Ukrainian extract (English
Wiktionary via `wiktextract`, **CC BY-SA 3.0**) is an **88% net-add for IPA** (a field the Atlas lacks
ENTIRELY) and **39% net-add for etymology**. Wire both in. Extract is on disk at
`~/.cache/learn-ukrainian-kaikki/kaikki-uk.jsonl` (252 MB, JSONL). DO NOT re-download.

## Architecture — preprocess ONCE, fast per-build enrich (this avoids the build-hang)
1. **NEW `scripts/lexicon/build_kaikki_lookup.py`:** parse the 252 MB kaikki JSONL ONE TIME → emit a compact
   `data/lexicon/kaikki_uk_lookup.json` keyed by **stress-stripped lowercased lemma** → `{ipa: [...],
   etymology_text: str, pos: [...]}`. Aggregate multi-line entries by `word`. **Reuse the proven parsing +
   stress-normalization logic from the merged `scripts/lexicon/assess_kaikki_fillability.py`** (same field
   names: `word`, `senses[].glosses`, `etymology_text`, `sounds[].ipa`). If the lookup file is < ~8 MB commit
   it; if larger, gitignore it and document the rebuild command. Run this FOREGROUND with `timeout 1800`.
2. **`scripts/lexicon/enrich_manifest.py`:**
   - **IPA (NEW field):** add `pronunciation: {ipa, source: "kaikki/Wiktionary (CC BY-SA 3.0)"}` to each entry,
     matched via stress-stripped lemma against the lookup. There is NO existing pronunciation field — purely additive.
   - **Etymology (FILL GAPS ONLY — do NOT overwrite):** the existing chain is Goroh → ЕСУМ → uk.wiktionary
     (see `_goroh_etymology` / `_esum_etymology` + the module docstring). Add kaikki as the **FINAL fallback**,
     used ONLY when Goroh/ESUM/uk.wiktionary produced nothing. Tag `source: "kaikki/Wiktionary (CC BY-SA 3.0)"`.
3. **`starlight/src/pages/lexicon/[lemma].astro`:** render IPA (pronunciation) near the headword; render kaikki
   etymology where used. Add a **CC BY-SA 3.0 attribution** line on pages that use kaikki data ("Pronunciation /
   etymology from English Wiktionary, CC BY-SA 3.0") + a site-level NOTICE/attribution entry (find where other
   source attributions live).
4. **Conformance gate `scripts/audit/validate_atlas_conformance.py` (§8):** IF an entry has `pronunciation.ipa`
   it must be a non-empty well-formed IPA string; IF kaikki-sourced data is present, the attribution/source tag
   must be present. Add the gate + a test. **Do NOT change existing §8 gates** (heritage/lemma_in_vesum/etc.).

## Regenerate — DO NOT HANG (the prior atlas dispatch stalled polling a backgrounded build)
1. `timeout 1800 .venv/bin/python scripts/lexicon/build_kaikki_lookup.py` (FOREGROUND; one-time 252 MB parse, ~1-2 min).
2. Regenerate the manifest FOREGROUND with timeout (now fast — reads the compact lookup, not 252 MB).
   **DO NOT** launch a build in a backgrounded interactive shell and poll it with empty stdin.
3. `cd starlight && npm run build` (skip `npm ci` if `node_modules/` present).
4. Gates GREEN (real vesum present at `data/vesum.db`):
   `.venv/bin/python -m pytest tests/test_atlas_conformance.py tests/test_heritage_classifier.py tests/test_lexicon_build_manifest.py tests/test_lexicon_enrich_manifest.py tests/test_build_kaikki_lookup.py -q`
   + `.venv/bin/ruff check scripts/ tests/`.

## §M-4 quality sample (REQUIRED in report — quote raw evidence)
- IPA + etymology now present for: `автобус` (expect `[ɐu̯ˈtɔbʊs]`), `книга`, `місто`, `адреса`, `вікно`.
- Show ≥1 word where kaikki etymology FILLED a gap (Goroh/ESUM/uk.wiktionary had none).
- Prove existing Goroh/ESUM etymology was **NOT overwritten** (pick a word that already had Goroh etym; show it unchanged).
- Counts: N lemmas gained IPA, N gained etymology. Confirm CC BY-SA attribution renders. Confirm 0 Russian text introduced.

## Finalize (numbered)
1. Worktree off origin/main. 2. Implement 1–4. 3. Preprocess lookup (foreground+timeout). 4. Regen manifest (foreground).
5. `npm run build`. 6. pytest + ruff green; quote raw. 7. §M-4 sample. 8. Commit (conventional; `X-Agent: codex`).
9. `git push -u origin <branch>`. 10. `gh pr create` NON-draft, base main, no auto-merge.
Out of scope: course content; don't break existing etymology/heritage/§3 soviet-caveat/lemma_in_vesum.

#M-4 preamble: every count / "tests pass" / "build ok" / PR URL must quote the raw command output.
