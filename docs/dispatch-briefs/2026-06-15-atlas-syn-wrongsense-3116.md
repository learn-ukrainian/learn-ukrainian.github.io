# Dispatch: Atlas §7 — exclude wrong-sense synonyms + preserve register qualifiers (#3116)

After the 2026-06-14 re-enrich (synonyms 21→794 from Караванський + СУМ синонімів), a few entries carry a
wrong-sense synonym that sits ADJACENT to a correct one in the source synset. Read it: `gh issue view 3116`.

## The bug (authoritative-source over-reach, NOT WordNet junk)
- `шлях` (road/way) → list wrongly includes `кам'яниця` (= stone building / stone-bramble berry, NO road
  sense — verify: `search_grinchenko_1907`/`search_esum`). It sits next to the CORRECT `кам'янка` (dialectal
  stone road) in the synset.
- `річка` (river) → wrongly includes `звір` (beast; dialectal ravine).
Low rate (~2/14 sampled) but pedagogically harmful — a learner must never be told `кам'яниця` means "road".

## Fix (sense-guard + keep legit dialectal terms with their tag)
1. In the synonym builder (`scripts/lexicon/` — find with `git grep -l "synonym" scripts/lexicon`), add a
   sense-matching guard so synset members whose sense doesn't match the lemma are dropped. Use sources MCP to
   verify sense (`search_heritage`, `search_esum`, `search_grinchenko_1907`) — do NOT guess.
2. **Preserve register/sense qualifiers** (діал./розм./заст.) on the kept chips so legitimate dialectal
   synonyms (гостинець, путівець, вуйко, світлина) are KEPT, tagged — NOT pruned. Do NOT over-prune.
3. A small curated wrong-sense exclusion list is acceptable IF each entry cites its disproving source; a
   general sense-guard is preferred. Document the approach.

## CRITICAL — generated-artifact guard
Code + tests + exclusion-data ONLY. **Do NOT regenerate or commit `site/src/data/lexicon-manifest.json`**
(full regen needs `data/vesum.db` 967 MB; the manifest is a generated artifact — committing it causes
cross-dispatch conflicts). The orchestrator regenerates + commits the manifest after merge.

## Numbered steps
1. `cd /Users/krisztiankoos/projects/learn-ukrainian && git fetch origin` (`--worktree` from origin/main).
2. Implement the sense-guard + qualifier preservation + tests.
3. `cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python -m pytest -k "synonym or lexicon or enrich" -q` → paste summary. Test must prove `шлях` drops `кам'яниця` and KEEPS `кам'янка`/`гостинець` (with tag).
4. `cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/ruff check scripts/ tests/` → paste final line.
5. Confirm no manifest staged: `git status --short` shows NO `site/src/data/lexicon-manifest.json`.
6. Commit `fix(lexicon): §7 drop wrong-sense synonyms + preserve register qualifiers (#3116)`.
7. `git push -u origin <branch>`; `gh pr create` referencing #3116. NO auto-merge.

## Evidence (#M-4 — command + cwd + raw output per claim)
- pytest summary; the before/after synonym list for `шлях`+`річка` FROM A UNIT TEST (not a manifest regen);
  the disproving source snippet for `кам'яниця`; `git status --short` (no manifest); ruff final line;
  `git log -1 --oneline`; `gh pr view --json url`.
