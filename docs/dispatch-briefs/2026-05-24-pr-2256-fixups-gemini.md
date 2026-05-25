# PR #2256 fix-up commits — addressing codex REQUEST_CHANGES findings

**Date**: 2026-05-24
**Agent**: gemini (gemini-3-flash-preview is fine; gemini-3.1-pro-preview if available)
**Mode**: danger
**Effort**: medium
**Wall budget**: 45 min

## Why this dispatch exists

PR #2256 `fix(monitor): polish artifacts UI and migrate comms off deprecated endpoints` (branch `cursor/monitor-api-ui-polish-2026-05-24`, 11 files, 287/110 LOC) was reviewed by codex and received `REQUEST_CHANGES`. Codex flagged 3 Significant findings; no Critical. CI is otherwise green (only the persistent `review/review` F7 GEMINI_API_KEY advisory is failing — that is not your concern).

Your job: push fix-up commits to the SAME branch so the PR converges. The orchestrator will then re-verify and merge.

Codex's full audit is at `audit/pr-2256-codex-review-2026-05-24.md` — read it before editing.

## The 3 findings to fix

### Fix A — restore accurate `page_count` without opening every PDF per list call

**File**: `scripts/api/images_router.py`

**What the PR did wrong**: Replaced the eager `_read_pdf_page_count` loop with `page_count = max(pages_with_images.keys(), default=0) if pages_with_images else 0`. This means `page_count` reports the highest page that has indexed images, not the actual PDF page count. Result: `dashboards/image-explorer.html:673` (which uses `page_count` as the hard navigation limit) blocks users from browsing valid pages that lack indexed images. Real UX regression.

**The right design**: Pre-populate `page_count` in `_pdf_catalog` entries at index build time (during `ensure_loaded()` / `_build_index`), using the existing `_read_pdf_page_count` function which is ALREADY cached at mtime+size keyed `_pdf_page_count_cache` (line 197). Then the list endpoint reads `info["page_count"]` directly — zero threads, zero opens per request.

**Concrete changes**:

1. In the index build path (around line 104-118 where `pdf_catalog[pdf_file.stem] = {...}` is constructed), add `page_count` to the catalog entry by calling `_read_pdf_page_count(str(pdf_file))`. This pays the cost ONCE at build time, populates the cache, and stores the value in the catalog.
   - Note: `_read_pdf_page_count` is defined at line 207 and takes a `pdf_path: str`.
   - The function returns `0` on read failure (line 226), which is acceptable as a fallback.

2. In `list_textbooks` (around line 289), replace the codex-quoted line:
   ```python
   page_count = max(pages_with_images.keys(), default=0) if pages_with_images else 0
   ```
   with:
   ```python
   page_count = info.get("page_count", 0)
   ```
   Remove the comment about "image explorer only needs a rough page span" — it is now false.

3. Verify no other call site in `images_router.py` relies on `page_count` being the indexed-image max. The other endpoints (`/page/{pdf_stem}/{page_num}` at line 321, `_extract` at line 335) already use `len(doc)` for live page bounds, so they are unaffected.

### Fix E — finish the `playgrounds/` → `dashboards/` directory rename

**File**: `scripts/generate_mdx/generate_playground_data.py`

**What the PR did wrong**: `scripts/build/build_playgrounds.py:8` was migrated to read `DASHBOARDS_DIR / "data" / "status.json"`, but `scripts/generate_mdx/generate_playground_data.py:180` still writes `Path(__file__).parent.parent / "playgrounds" / "data" / "status.json"`. So `npm run dashboards:data` writes to one path and `npm run dashboards:build` reads from a different path → stale data downstream.

**The right fix**: Change `generate_playground_data.py:180` to write to `dashboards/data/status.json`. Mechanical 1-line edit. Update any nearby comment that still says "playground" to "dashboard" if it would mislead future readers.

**Also**: grep the repo for ANY remaining `playgrounds/` path references in code/configs/workflows and fix them in the same commit (do not leave orphans for a follow-up PR). Specifically check:
- `grep -rn "playgrounds/" scripts/ tests/ .github/ package.json`
- If any active references remain that should be `dashboards/`, fix them. If `playgrounds/` is intentionally kept somewhere (e.g. an archived path), leave it but document why in the commit message.

### Fix G — update consumer-map matrix rows

**File**: `docs/api-endpoint-consumer-map-2026-05-06.md`

**What the PR did wrong**: Updated the scope sentence at the top to say `dashboards/*.html`, but left all the matrix rows (lines 39, 57, 180 per codex) still referencing `playgrounds/*.html`. The row at line 57 even still claims `/api/comms/live-activity` is consumed by `playgrounds/comms.html`, which directly contradicts the implementation at `dashboards/comms.html:491` which now fetches `/api/build/events/active`.

**The right fix**:

1. Replace every `playgrounds/` reference in the matrix table rows with `dashboards/`. Sed-style: `sed -i 's|playgrounds/|dashboards/|g' docs/api-endpoint-consumer-map-2026-05-06.md`. Verify by diffing.
2. Update the `comms.html` consumer row (around line 180 per codex): drop `/api/comms/live-activity` from the consumed-endpoints list; add `/api/build/events/active; /api/build/events/recent`.
3. Update the `/api/comms/live-activity` row (around line 57): change its `KEEP/DEPRECATE` status to `REMOVED` if the endpoint no longer exists (verify by grepping `scripts/api/comms_router.py` for the route; if the route was deleted in this PR or a previous one, mark `REMOVED`; if it still exists but no longer has consumers, mark `DEPRECATE` and note "no consumers post-#2256"). Update the consumer column accordingly.

## REQUIRED steps (numbered — follow in order)

1. From the project root: `git fetch origin && git worktree add -b gemini/pr-2256-fixups-2026-05-24 .worktrees/dispatch/gemini/pr-2256-fixups-2026-05-24 origin/cursor/monitor-api-ui-polish-2026-05-24`
   - This branches off the PR's HEAD and gives you a clean worktree.
2. `cd .worktrees/dispatch/gemini/pr-2256-fixups-2026-05-24`
3. `ln -s ../../../../.venv .venv` (venv symlinked) # venv symlinked
4. Read the codex audit: `cat ../../../../audit/pr-2256-codex-review-2026-05-24.md` — note every quoted line:number reference.
5. Apply Fix A: edit `scripts/api/images_router.py` per the design above. Verify your change with `git diff scripts/api/images_router.py`.
6. Apply Fix E: edit `scripts/generate_mdx/generate_playground_data.py:180`. Grep for residual `playgrounds/` references and fix any active ones.
7. Apply Fix G: edit `docs/api-endpoint-consumer-map-2026-05-06.md` matrix rows.
8. Run focused tests:
   - `.venv/bin/pytest tests/test_dashboards.py tests/test_playground_api_stability.py -v` — must pass.
   - `.venv/bin/pytest tests/api/ -x` (if directory exists) — must pass.
   - If a test asserts the OLD `page_count = max(pages_with_images.keys())` behavior, update the test to assert the correct new behavior (cached real page_count from PDF). Do not weaken the assertion.
9. Lint: `.venv/bin/ruff check scripts/api/images_router.py scripts/generate_mdx/generate_playground_data.py` — clean. Then `.venv/bin/ruff format` the changed Python files.
10. Self-diff before committing:
    ```
    git diff --stat
    git diff scripts/api/images_router.py
    git diff scripts/generate_mdx/generate_playground_data.py
    git diff docs/api-endpoint-consumer-map-2026-05-06.md
    ```
    Confirm:
    - Fix A: index build path adds `page_count`; list endpoint reads `info.get("page_count", 0)`.
    - Fix E: no `playgrounds/` remains anywhere it should now be `dashboards/`.
    - Fix G: matrix rows no longer reference `playgrounds/` or claim `live-activity` is consumed.
11. **Three separate commits** (one per fix, for clean atomic history):
    ```
    git add scripts/api/images_router.py
    git commit -m "fix(images_router): cache PDF page_count in pdf_catalog at index build (PR #2256 codex finding A)

    Codex review of PR #2256 flagged that page_count = max(pages_with_images.keys())
    is the highest page WITH indexed images, not the actual PDF page count, which
    breaks image-explorer.html navigation (uses page_count as hard nav limit).

    Restores accurate page_count by pre-populating it in pdf_catalog entries at
    ensure_loaded() time, using the existing _pdf_page_count_cache. The list
    endpoint now reads info[\"page_count\"] directly — zero threads, zero opens
    per list call, preserving the 504-stability win from the original PR."
    ```
    ```
    git add scripts/generate_mdx/generate_playground_data.py [any other migrated files]
    git commit -m "fix(dashboards): finish playgrounds/ → dashboards/ rename in data generator (PR #2256 codex finding E)

    generate_playground_data.py still wrote playgrounds/data/status.json while
    build_playgrounds.py reads dashboards/data/status.json post-PR — npm run
    dashboards builds from stale data. Fix completes the rename."
    ```
    ```
    git add docs/api-endpoint-consumer-map-2026-05-06.md
    git commit -m "docs(consumer-map): update matrix rows for playgrounds/ → dashboards/ rename (PR #2256 codex finding G)

    Scope sentence was updated but matrix rows still said playgrounds/comms.html
    consumes /api/comms/live-activity, contradicting dashboards/comms.html:491
    which now fetches /api/build/events/active."
    ```
12. `git push -u origin gemini/pr-2256-fixups-2026-05-24`
13. **CHANGE THE PR BASE BRANCH** — the PR is on `cursor/monitor-api-ui-polish-2026-05-24`. To get your fixes INTO that PR, you have two options:
    - **Option A (preferred)**: Push your commits ONTO the PR branch directly. After step 12, run:
      ```
      git push origin gemini/pr-2256-fixups-2026-05-24:cursor/monitor-api-ui-polish-2026-05-24
      ```
      If GitHub rejects the push (force-protection on the PR branch), fall back to Option B.
    - **Option B**: Open a follow-up PR targeting `cursor/monitor-api-ui-polish-2026-05-24` (NOT main). Body: `Fix-up commits for PR #2256 per codex review.` Title: `fixups for #2256: page_count cache + playgrounds rename + consumer map`.
14. Report which option you used in the PR comment thread of #2256:
    ```
    gh pr comment 2256 --body "Pushed 3 fix-up commits addressing codex findings A/E/G. (Option A or B notice.) Branch HEAD: $(git rev-parse HEAD)"
    ```
15. **NO auto-merge.** Orchestrator handles the re-review and final merge.

## Self-verification before committing

For each commit, verify the bullet under Fix A/E/G above is FULLY addressed. If you find yourself thinking "this is close enough" — go back and finish.

For Fix A specifically: write a one-line sanity assertion in a Python REPL or in a test to confirm `info["page_count"]` returns the same value as `_read_pdf_page_count(info["path"])` for at least one PDF in `data/textbooks/`. Paste that output in your PR comment.

## Verifiable claims you must back with raw tool output

| Claim | Required evidence in your PR comment / final report |
|---|---|
| "Fix A: page_count now sourced from cached catalog" | `git diff scripts/api/images_router.py` showing both edits + a REPL one-liner confirming round-trip |
| "Fix E: no remaining playgrounds/ in active code paths" | `git grep -n "playgrounds/" scripts/ tests/ .github/ package.json` after edits — should show only intentional/archived references |
| "Fix G: consumer-map rows updated" | `git diff docs/api-endpoint-consumer-map-2026-05-06.md` |
| "Tests pass" | `.venv/bin/pytest tests/test_dashboards.py tests/test_playground_api_stability.py -v` final summary raw |
| "Lint clean" | `.venv/bin/ruff check` raw |
| "Commits pushed onto PR branch" | `git log -3 --oneline cursor/monitor-api-ui-polish-2026-05-24` after push (or new PR URL if Option B used) |

## Anti-fabrication preamble (#M-4)

Every verifiable claim must be tool-backed. If you find yourself writing "this should be fine" or "I believe X" — stop, run the tool, paste raw output. No paraphrase.

## Time budget

45 min wall. The actual editing is ~15 min; tests + push + verify is the other ~30 min. If you exceed budget, report partial state (which fixes landed, which are still pending) and exit. Do not push half-finished commits.
