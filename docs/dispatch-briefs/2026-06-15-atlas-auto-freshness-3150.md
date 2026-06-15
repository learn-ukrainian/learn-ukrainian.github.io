# Dispatch: Atlas auto-freshness — `make atlas` target + DB-free CI staleness gate (#3150)

The Word Atlas manifest (`site/src/data/lexicon-manifest.json`) is a deterministic two-step generated
artifact (`build_data_manifest.py` → `enrich_manifest.py`) but BOTH steps are MANUAL, so the live manifest
silently drifts behind lexicon-code changes (`scripts/lexicon/*.py`) and new module vocab. Read it:
`gh issue view 3150`. This session alone the orchestrator hand-ran enrich+verify+commit 3× — automate it.

## Constraint (why CI can't just regenerate)
`enrich_manifest` needs `data/vesum.db` (967 MB) + `data/sources.db` + slovnyk cache — **none on CI** (same
wall as #2928). So NO CI-side regeneration. The CI gate must be **DB-free**: detect staleness by fingerprint,
not by regenerating.

## Scope
1. **`make atlas` local target** (add to `Makefile`): runs `build_data_manifest` → `enrich_manifest` →
   `verify_manifest` in sequence, fail-fast. One command to regenerate + validate locally (needs the DBs).
2. **DB-free staleness fingerprint.** Compute a deterministic fingerprint of the manifest's *code+vocab*
   inputs that CI HAS (NOT the DBs): a hash over (a) `scripts/lexicon/*.py` source, (b) the sorted set of
   lemmas drawn from every module `vocabulary.yaml`. Write it to a committed sidecar
   (`site/src/data/lexicon-manifest.fingerprint.json`) as part of `make atlas` (and `enrich_manifest`).
3. **CI freshness gate** (a new check + a small script `scripts/lexicon/check_manifest_freshness.py`):
   recompute the fingerprint from the current code+vocab (no DB needed) and compare to the committed sidecar.
   **FAIL** if they differ → "manifest stale vs lexicon code / vocab; run `make atlas` locally and commit."
   - HONEST SCOPE: this catches code-drift + vocab-drift. It does NOT catch dictionary re-ingests (those need
     the DBs CI lacks — acknowledge in the gate message + a `# TODO(#3150)` that dict-version drift is
     out of scope until #2928's CI-DB story changes). Do NOT pretend to cover dict re-ingests.
4. Wire the gate into the existing CI (the `Content CI` or `CI` workflow — mirror an existing lightweight
   gate's placement). Make it a BLOCKING check only once it's proven green on a fresh manifest.

## Constraints / guards
- The fingerprint MUST be deterministic: sort lemmas, sort file list, hash file *contents* (not mtimes).
- `make atlas` writes BOTH the manifest AND the fingerprint sidecar so they never diverge.
- Do NOT commit `data/*.db`. The sidecar fingerprint is small JSON — commit it.
- Add a unit test: fingerprint is stable across runs; changes when a `scripts/lexicon/*.py` byte changes or a
  vocab lemma is added; the freshness check passes on a matching pair and fails on a mismatched one (use temp
  fixtures, not the real 967 MB DB).

## Numbered steps
1. `cd /Users/krisztiankoos/projects/learn-ukrainian && git fetch origin` (`--worktree` from origin/main).
2. Implement the Makefile target + fingerprint writer (in `enrich_manifest` or a shared helper) + the
   DB-free check script + the CI wiring + tests.
3. `cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python -m pytest -k "freshness or fingerprint or manifest" -q` → paste summary.
4. `cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/ruff check scripts/ tests/` → paste final line.
5. Confirm no `.db` and no regenerated `lexicon-manifest.json` staged (you can't regen — no DBs): `git status --short`.
6. Commit `feat(lexicon): make atlas target + DB-free manifest staleness gate (#3150)`.
7. `git push -u origin <branch>`; `gh pr create` referencing #3150. NO auto-merge.

## Evidence (#M-4 — command + cwd + raw output per claim)
- pytest summary; the fingerprint output for a sample input + proof it changes on a code/vocab edit FROM A
  UNIT TEST; the freshness-check pass AND fail demonstrations; ruff final line; `git status --short`
  (no .db / no manifest); `git log -1 --oneline`; `gh pr view --json url`.
