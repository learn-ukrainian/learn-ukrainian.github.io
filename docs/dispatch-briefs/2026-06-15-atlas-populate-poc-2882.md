# Dispatch: fully populate Word Atlas per POC — fill remaining gaps (#2882)

Bring the Word Atlas (Лексикон) detail pages up to the POC design
(`docs/poc/poc-word-atlas-design.html`). Read it: `gh issue view 2882`. **The issue is partly STALE — RE-MEASURE
before acting.**

## ⚠️ Re-measure current coverage FIRST (do not trust the issue's old numbers)
- The issue says "Синоніми only 5/52" — **STALE**. Synonyms were re-enriched to 794+ entries (Караванський +
  СУМ синонімів) via #3116/#3098 work merged 2026-06-15. Re-measure live.
- Paths moved: manifest is now **`site/src/data/lexicon-manifest.json`** (not `starlight/...`); astro page is
  **`site/src/pages/lexicon/[lemma].astro`**. The issue's `starlight/` paths are stale.
- Step 1 of your work: run `.venv/bin/python -m scripts.lexicon.verify_manifest` and compute per-POC-section
  coverage on CURRENT main. Report a fresh coverage table. Then fill only the GENUINELY thin sections.

## Likely remaining gaps (confirm against your fresh measurement)
- **Етимологія (ЕСУМ)** — was 19/52 via exact-lemma match; improve with variant/normalised matching (the
  exact-match misses inflected/variant forms). Highest-value gap.
- **Фразеологізми** — data exists (frazeolohichnyi 25K) but substring-match is noisy; tighten matching.
- **Антоніми** — WordNet (ukrajinet) has them; wire if not already surfaced.
- Any other POC section still thin after re-measurement.
All enrichment is DETERMINISTIC local-DB lookup (no LLM). Verify words via sources MCP; never invent data.

## CRITICAL — generated-artifact guard
Code + tests ONLY. **Do NOT regenerate or commit `site/src/data/lexicon-manifest.json`** (regen needs
`data/vesum.db` 967 MB; generated artifact → cross-dispatch conflict). The orchestrator regenerates +
commits the manifest after merge. Your tests must prove the enrichment logic on fixtures, not via a manifest regen.

## Numbered steps
1. `cd /Users/krisztiankoos/projects/learn-ukrainian && git fetch origin` (`--worktree` from origin/main).
2. Re-measure coverage; implement the genuinely-thin sections in `scripts/lexicon/enrich_manifest.py`
   (+ helpers); add unit tests proving each new/improved section on fixtures.
3. `cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python -m pytest -k "lexicon or enrich or etymolog or phrase" -q` → paste summary.
4. `cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/ruff check scripts/ tests/` → paste final line.
5. Confirm no manifest staged: `git status --short` shows NO `site/src/data/lexicon-manifest.json`.
6. Commit `feat(lexicon): populate Atlas POC sections — etymology variant-match + phraseology + antonyms (#2882)`.
7. `git push -u origin <branch>`; `gh pr create` referencing #2882. NO auto-merge.

## Evidence (#M-4 — command + cwd + raw output per claim)
- fresh coverage table (raw); pytest summary; before/after section output for a sample lemma FROM A UNIT TEST
  (not a manifest regen); `git status --short` (no manifest); ruff final line; `git log -1 --oneline`;
  `gh pr view --json url`. Any invented dictionary data = reject.
