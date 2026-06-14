# Dispatch: Atlas §6 decolonization moat PR1 — active-participle calque correction layer (#3098)

The §5/§6 calque/Russianism warning layer is thin — most Atlas pages show no stylistic note. This is the
highest-mission-value content grind (strengthens Ukrainian against Russian interference). Read it:
`gh issue view 3098`. **PR1 = active-participle calques ONLY** (the issue's highest-value first slice).
Defer broader collocation calques to PR2.

## Scope (PR1)
Build a calque-correction layer that surfaces a §6 stylistic note when an Atlas lemma (or related form) is an
active-present-participle calque (`-учий/-ючий/-ачий/-ячий`, a Russian pattern Ukrainian traditionally
avoids) with a native replacement:
- `працюючий` → `працівник` / `той, що працює`
- `оточуючий` → `довколишній` / `навколишній`
- `відпочиваючий` → `відпочивальник` / `той, хто відпочиває`
…seed the rule set from the lemmas present in the Atlas manifest; do not hand-wave a giant list.

## Source ONLY from the authoritative corpus we already have — VERIFY, DO NOT INVENT
Every rule must cite its disproving/supporting source. Use sources MCP:
- Антоненко-Давидович: `search_style_guide` (structured 342) **AND** `search_text source=antonenko-davydovych-yak-my-hovorymo` (prose 169) — query BOTH (a rule absent from the structured index may be in the prose).
- `query_pravopys` (Правопис 2019).
- `search_ua_gec_errors` (F/Calque, F/Collocation).
- `search_heritage` BEFORE flagging — never false-flag an authentic Ukrainian word as a calque.
If a candidate can't be grounded in these, DROP it. No invented corrections.

## Wiring
Add the §6 note to the enrichment path (`scripts/lexicon/enrich_manifest.py` §5/§6 section — read it first).
Each emitted note carries the native replacement(s) + a source citation.

## CRITICAL — generated-artifact guard
Code + rules-data + tests ONLY. **Do NOT regenerate or commit `site/src/data/lexicon-manifest.json`**
(regen needs `data/vesum.db` 967 MB; generated artifact → cross-dispatch conflict). Orchestrator regenerates
post-merge.

## Numbered steps
1. `cd /Users/krisztiankoos/projects/learn-ukrainian && git fetch origin` (`--worktree` from origin/main).
2. Read `enrich_manifest.py` §5/§6 path; build the cited participle-calque rule set; wire the §6 note; tests.
3. `cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python -m pytest -k "calque or lexicon or enrich" -q` → paste summary. Test must prove `працюючий` yields a §6 note `→ працівник` with an Antonenko citation.
4. `cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/ruff check scripts/ tests/` → paste final line.
5. Confirm no manifest staged: `git status --short` shows NO `site/src/data/lexicon-manifest.json`.
6. Commit `feat(lexicon): §6 active-participle calque correction layer (PR1 of #3098)`.
7. `git push -u origin <branch>`; `gh pr create` referencing #3098 (note PR1/N). NO auto-merge.

## Evidence (#M-4 — command + cwd + raw output per claim)
- pytest summary; the generated §6 note for `працюючий` FROM A UNIT TEST; the source citation per rule
  (quote the Antonenko/UA-GEC row); `git status --short` (no manifest); ruff final line;
  `git log -1 --oneline`; `gh pr view --json url`. Any uncited correction = fabrication = reject.
