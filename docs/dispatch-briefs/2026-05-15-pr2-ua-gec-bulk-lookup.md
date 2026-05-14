# Codex Dispatch — PR-2: bulk UA-GEC calque lookup table

**Dispatched:** 2026-05-15 by orchestrator (Claude)
**Agent:** Codex (gpt-5.5, high effort)
**Worktree:** `.worktrees/dispatch/codex/pr2-ua-gec-bulk-lookup-2026-05-15/`
**Branch:** `codex/pr2-ua-gec-bulk-lookup-2026-05-15`
**Estimated:** ~3 hours runtime, ~250 LOC code + tests + 1 CSV data file
**Depends on:** PR #1997 (the precursor PR-1, currently open) — base your branch on `origin/main` post-merge if it lands first; otherwise base on the PR-1 branch `feat/russicism-ua-gec-patterns`

---

## Goal (one sentence)

Add a CSV-backed bulk lookup table of ~256 UA-GEC F/Calque pairs (frequency ≥ 2× in source corpus) to dramatically increase the deterministic Russianism detector's recall, ship as a separate `severity: info` tier so context-dependent matches surface as suggestions without escalating the existing `warning` gates.

## Context — empirical motivation

PR-1 just landed (or is about to). Even with the expanded 39-pattern detector, recall against UA-GEC's gold set is **1.6%** (27 of 1,640 unique F/Calque entries caught). UA-GEC has 1,613 unique misses, of which the high-frequency tier (≥2×) is ~256 single-word + ~51 multi-word patterns. Importing them as a lookup table (not regex per pattern) materially raises recall toward usable levels for our LLM eval work.

Source data:
- `/tmp/ua-gec-pairs.jsonl` — 17,605 extracted edit pairs (already produced — see `/tmp/ua_gec_extract.py` for the extraction script)
- The mining report at `/tmp/ua-gec-mining-report.md` documents the analysis
- UA-GEC clone lives at `data/ua-gec/` (CC-BY-4.0, untracked, do not commit)

## Acceptance criteria (measurable)

1. **Data file:** `data/russianism-patterns-ua-gec.csv` shipped in the PR with columns:
   - `bad` (lowercased, stripped)
   - `good` (lowercased, stripped)
   - `error_type` (always `F/Calque` for this PR)
   - `frequency` (count in UA-GEC source)
   - `source` (always `UA-GEC v2`)
   - `license` (always `CC-BY-4.0`)
   - `attribution` (always `Syvokon et al., UNLP 2023`)
   - First two lines of file are CSV-comment headers explaining license + source
   - Filter: F/Calque entries where `frequency ≥ 2` (gives ~256 rows). Skip entries where `bad` or `good` is empty. Skip entries where `bad` is a substring of an existing `_RUSSICISMS` or `_RUSSICISMS_FROM_UA_GEC` regex pattern (avoid duplicates).
2. **New function:** `check_ua_gec_calques(content: str, file_path: str = '') -> list[dict]` in `scripts/audit/checks/russicism_detection.py`:
   - Loads CSV at module import (cache as module-level dict)
   - Tokenizes input (use simple word-boundary regex; same case-folding as existing `check_russicisms`)
   - For single-word `bad`: O(1) lookup per token
   - For multi-word `bad` (contains a space): use `pyahocorasick` if installed, else regex fallback. Add `pyahocorasick` to requirements only if it's not already there.
   - Skip matches inside guillemets / blockquotes (reuse existing `_is_in_quote_context`)
   - Skip OES/RUTH track exemptions (reuse `_EXEMPT_TRACKS`)
   - Each violation: `{'type': 'UA_GEC_CALQUE_DETECTED', 'severity': 'info', 'issue': ..., 'fix': ..., 'matched': ..., 'attribution': 'UA-GEC v2 (CC-BY-4.0)'}`
   - **Severity is `info`, not `warning`** — these are softer suggestions; don't fire build-breaking gates.
3. **Integration:** Call `check_ua_gec_calques` from wherever `check_russicisms` is called (probably `scripts/audit/checks/__init__.py` or `scripts/audit/audit_module.py` — find the call sites).
4. **Tests:** Add `TestUaGecBulkLookup` class to `tests/test_russicism_detection.py`:
   - 8 positive cases drawn from the new CSV (e.g. `коментарій → коментар`, `підписники → читачі`, `пост → публікація`, `лайки → вподобання`, `тренду → тенденцій`)
   - 4 negative cases: dual-use words that must NOT trigger (e.g. `пара взуття`, `справа важлива`, `будь-який наступний крок`, `даний метод` if math context — pick negatives carefully to match real CSV content)
   - 1 test confirming severity='info' for all matches
   - 1 test confirming guillemets / blockquotes skipped
5. **Recall measurement script:** add `scripts/audit/measure_russicism_recall.py` — runs current detector + bulk lookup against UA-GEC source and prints recall %. This is the regression detector; future PRs reference its output. Inline help, no flags needed.
6. **Verifiable claims preamble (per #M-4):** Brief explicitly enumerates these required tool-backed evidence lines in your turn body:
   - `pytest` final summary line raw
   - `ruff check` final line raw
   - Recall before / recall after (run measure script, paste raw)
   - `git log -1 --oneline` raw
   - `gh pr view N --json url` raw URL
   These appear verbatim in your turn output, not paraphrased.

## Hard guardrails

- **DO NOT modify existing patterns** in `_RUSSICISMS` or `_RUSSICISMS_FROM_UA_GEC` — those are PR-1's surface, surgically tested, do not touch.
- **DO NOT use `git commit --no-verify`.** Pre-commit hooks must pass cleanly.
- **DO NOT use `gh pr merge --admin`.** PR is for human review.
- **DO NOT touch starlight/** — there's a known build-hook issue stripping POS columns from MDX. Revert any unrelated worktree changes with `git checkout -- <path>` before commit.
- **DO NOT add `data/ua-gec/` to .gitignore** — user explicitly said "gitignore can stay" 2026-05-14.
- **CSV format strict:** ASCII commas, double-quote any cell with comma/newline/quote. No BOM. UTF-8.

## Step-by-step

1. `git worktree add -b codex/pr2-ua-gec-bulk-lookup-2026-05-15 .worktrees/dispatch/codex/pr2-ua-gec-bulk-lookup-2026-05-15 origin/main` — IF PR-1 not yet merged, base on `feat/russicism-ua-gec-patterns` branch instead.
2. `cd .worktrees/dispatch/codex/pr2-ua-gec-bulk-lookup-2026-05-15 && ln -s ../../../../.venv .venv` (worktree env)
3. Read `/tmp/ua-gec-pairs.jsonl` (17,605 pairs already extracted — DO NOT re-clone or re-extract).
4. Filter to F/Calque ≥2× frequency, dedupe, dedupe-vs-existing-patterns, write `data/russianism-patterns-ua-gec.csv` (in the worktree's `data/` dir — this CSV WILL be committed; only `data/ua-gec/` clone stays untracked).
5. Add `check_ua_gec_calques` to `scripts/audit/checks/russicism_detection.py`. Hook into `check_russicisms` call sites (find via `grep -rn check_russicisms scripts/`).
6. Write `scripts/audit/measure_russicism_recall.py`. Run it; record before/after numbers.
7. Add tests under `TestUaGecBulkLookup`. Run `.venv/bin/python -m pytest tests/test_russicism_detection.py -v`.
8. `.venv/bin/ruff check scripts/audit/ tests/test_russicism_detection.py` — fix any lint.
9. Commit with conventional message:
   ```
   feat(audit): bulk UA-GEC F/Calque lookup table (~256 patterns, severity:info)
   ```
   Body: cite recall before/after, attribution, depends-on PR-1 if applicable.
10. `git push -u origin codex/pr2-ua-gec-bulk-lookup-2026-05-15`
11. `gh pr create` with body covering: motivation (1.6% → ?% recall), what's added (CSV row count, function, tests), license attribution, depends-on PR-1, NO auto-merge.

## What success looks like

You return with:
- PR URL (raw `gh pr view --json url` output)
- Recall before number (raw script output)
- Recall after number (raw script output)
- Pytest pass count (raw final-summary line)
- Ruff result (raw final line: "All checks passed!")
- Commit SHA (raw `git log -1 --oneline`)

If recall doesn't materially increase (target: ≥10% post-PR-2, stretch: ≥15%), STOP and explain why before marking done. The whole point of this PR is recall improvement; if it doesn't show, something is wrong with the lookup integration.
