# Dispatch: fix wiki_coverage err-obligation seam so m20 (a1/my-morning) ships

**Agent:** codex · **Mode:** danger (worktree) · **No auto-merge.**

## Why (root cause — VERIFIED in code, do not re-litigate)
m20 dies at `wiki_coverage_gate` 66.7% (12/18) on err-1..err-6 (`l2_error`,
`implementation_map_missing`). The seam:

- `scripts/audit/wiki_coverage_gate.py::check_wiki_coverage` (~line 366-393):
  `claim = map_entries.get(obligation_id)` where `map_entries =
  parse_implementation_map(implementation_map)` and `implementation_map` is the
  **writer's emitted `<implementation_map>` block** (passed as
  `implementation_map=writer_output` from the gate runner). Line 373-374:
  `if not claim: FAIL "implementation_map_missing"`.
- `check_wiki_coverage_paths` (~line 455-458) auto-loads
  `module_dir/implementation_map.json` (the **pre-seeded sidecar** from
  `seed_implementation_map`) into `seeded_map`, but it is consumed ONLY by
  `_enrich_obligation_from_seeded_map` (line 368-371) to fill `subtype`
  metadata — it **never supplies a missing `claim`**.
- The writer under-emits err-correction rows; the correction loop is
  contractually forbidden from adding top-level activities/multiline YAML
  (`scripts/build/phases/linear-correction-wiki-coverage.md:25`). So err-1..err-6
  hard-fail no matter how many correction rounds run.

3-agent alignment (codex+gemini+cursor) + claude verification: fix at the
GENERATOR/GATE layer (first-pass completeness), keep correction YAML valid only
as a safety net. Anchor-first scope — full typed-field refactor + prompt
slim/exemplar are explicitly OUT (fast-follow).

## #M-4 — verifiable claims & the deterministic tool for each
| Claim you will make | Tool that proves it (quote raw output) |
|---|---|
| "err-1..err-6 now resolve (PASS or genuine substance-FAIL, not implementation_map_missing)" | new unit test asserting on a gate report built from the forensic m20 artifacts; `pytest` final summary line raw |
| "no cosmetic pass" | test that a seeded-but-absent-substance obligation still FAILs (substance check runs) |
| "correction YAML now valid" | unit test feeding the two bad strings; `yaml.safe_load` succeeds |
| "tests pass" | `.venv/bin/python -m pytest <files> -q` final `N passed` line raw |
| "lint clean" | `.venv/bin/ruff check scripts tests` final line raw |
| "commit landed / PR opened" | `git log -1 --oneline` + `gh pr view --json url` raw |

## Reproduction inputs (forensic, retained per #M-10)
`.worktrees/builds/a1-my-morning-20260528-232046/` (and siblings 221218/221953/
222759/230427) hold the failing `module.md`, `activities.yaml`,
`implementation_map.json`, wiki manifest, and the gate report (`python_qg.json`
/ wiki_coverage report). Use these as test fixtures — copy minimal slices into
`tests/`, do NOT depend on the worktree at test time.

## What to change
1. **Gate seam (`scripts/audit/wiki_coverage_gate.py::check_wiki_coverage`):**
   when `claim is None`, fall back to the seeded entry
   (`seeded_index.get(obligation_id)`) as the authoritative claim — read its
   `artifact` + `location` — THEN continue to the normal resolution
   (`_activity_text` / `_location_text`) and substance check
   (`_check_obligation_text`). Net effect: a pre-seeded obligation whose location
   resolves AND whose artifact contains matching substance PASSES even if the
   writer didn't echo the row; if the location is absent or substance missing it
   still FAILs (`claimed_location_missing` / substance reason) — never a cosmetic
   pass. Keep behaviour identical when there is no seeded entry.
2. **Stub seeding (`scripts/build/phases/implementation_map.py::seed_implementation_map`):**
   confirm `l2_error` / `contrast_pair` obligations are seeded with
   `artifact: activities.yaml` + a resolvable `location`. Pre-seed the matching
   bounded error-correction **activity stubs** into `activities.yaml` (skeleton
   only: `obligation_id`, `type: error-correction`, manifest `incorrect`/
   `correct`/`why`, **EMPTY** `sentence`/`items` placeholders, `location_hint`).
   NEVER put full Ukrainian sentences/distractors in a stub — that produces
   copy-paste "visible compliance token" pathology. Writer fills the Ukrainian.
3. **Correction-loop YAML validity (`scripts/build/linear_pipeline.py`,
   search `wiki_coverage_correction_yaml_invalid` + the activities.yaml
   fix-application path):** fix (a) newline-concat producing
   `...вмиваюся.    implementation_map:` (`mapping values are not allowed here`)
   — injected YAML must start its own line / document; (b) IPA apostrophe
   doubling `[прокидайес'':а]` — correct single-quote escaping on YAML emission
   (sibling of PR #2184). Safety-net only.
4. **Goodhart sentinel:** N distinct `err-N` obligations cannot all be satisfied
   by a single activity entry / one location — require distinct
   activity-or-location (or distinct contrast pairs) per obligation.

## DO NOT
- Re-fire the full v7 build (the fix must land on main first; the orchestrator
  re-fires after merge). Prove correctness with unit tests on forensic fixtures.
- Touch prompt size / exemplar slot / typed-field refactor / CEFR prune — OUT of
  scope (fast-follow).
- Weaken any gate to make m20 pass. The substance check must remain real.

## Numbered execution steps
1. `git worktree` is created for you by `--worktree` (branch
   `codex/m20-wiki-coverage-err-seam-2026-05-29` off `origin/main`).
2. Implement changes 1–4 above. Add/extend unit tests in
   `tests/audit/test_wiki_coverage_gate.py` (gate seam + no-cosmetic-pass +
   sentinel) and a correction-YAML test (use the two bad strings verbatim).
3. `.venv/bin/python -m pytest tests/audit/test_wiki_coverage_gate.py <other touched test files> -q` → green.
4. `.venv/bin/ruff check scripts tests` → clean.
5. Commit (conventional): `fix(wiki_coverage): seeded implementation_map is authoritative claim fallback for err-obligations + valid correction YAML + Goodhart sentinel`. Trailer `X-Agent: codex/m20-wiki-coverage-err-seam-2026-05-29`.
6. `git push -u origin codex/m20-wiki-coverage-err-seam-2026-05-29`.
7. `gh pr create` — body: root cause (the seam above), the 4 changes, test evidence (raw pytest line), and "anchor-first; prompt-slim/exemplar/typed-refactor are fast-follow." Reference issue #2389 (Step 7 m20 rebuild) + #2380.
8. Do NOT merge. Leave for orchestrator review.
