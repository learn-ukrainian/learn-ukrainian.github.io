# Codex dispatch brief — #1822 test coverage for /artifacts/ docs router

**Why this matters now:** `scripts/api/docs_router.py` shipped in commit `c17450a6c1` with **zero tests**. The orchestrator manually smoke-tested four scenarios before commit (root, file serve, traversal block) but a PR can break any of those without a test catching it. This is a routine post-merge hardening pass. No bug is masked — we're adding the regression net that should have shipped with the original PR.

## Worktree (already prepared by dispatcher)

You start in `.worktrees/dispatch/codex/1822-artifacts-router-tests/` on branch `codex/1822-artifacts-router-tests`. Do NOT `cd` out, do NOT create a new branch in the main checkout.

## Goal

Create `tests/test_docs_router.py` with comprehensive coverage of `scripts/api/docs_router.py`:

- All 8 `ALLOWED_ROOTS` happy paths
- Directory listing + root index
- Path-traversal defense (raw + URL-encoded variants)
- Symlink-escape defense
- Extension allowlist
- Unapproved-root defense
- Missing-file 404
- Hidden-file (dotfile) defense

Plus two bonus checks: performance smoke + concurrent-access sanity.

## Files to read (in order)

1. **`scripts/api/docs_router.py`** — the target. ~265 lines. Read end-to-end to understand:
   - `ALLOWED_ROOTS` (line 28) — the 8 roots we serve
   - `_ALLOWED_EXT` (line 39) — extension allowlist
   - Path-resolution logic (lines ~97-160)
   - Route handlers (around line 209+)

2. **`scripts/api/main.py`** — to see how the router mounts and to construct the test app fixture (`TestClient(app)`).

3. **`tests/test_playground_api_stability.py`** — pattern reference. Uses `TestClient` + assertions on response status, content-type, perf bounds. Mirror its style.

4. **`tests/test_artifacts_site_api.py`** — the unrelated namespace mentioned in the issue body. Read briefly to confirm it doesn't already cover this and to avoid name collisions.

## Approach to negative-path tests

The issue body warns: *"either monkeypatch `docs_router.ALLOWED_ROOTS` to a tmp tree, or assert behaviors against the real repo (acceptable for happy paths, NOT for negative paths since the result depends on filesystem state)."*

The right approach:

- **Happy paths:** assert against the real repo. The 8 roots all exist (`docs/session-state/`, `audit/`, etc.) — find any single existing `.html` under each. The test is robust because its assertions key off `Content-Type`, `Cache-Control`, and `200`, not file content.

- **Negative paths:** monkeypatch `docs_router.ALLOWED_ROOTS` to a `tmp_path`-based tree. Construct controlled fixtures:
  ```
  tmp/
    safe-root/
      file.html       (allowed)
      script.py       (extension blocked)
      .hidden         (dotfile blocked)
    outside-root/
      secret.txt      (no allowed root reaches here)
    safe-root/escape  (symlink → outside-root/secret.txt)
  ```
  Monkeypatch `ALLOWED_ROOTS = {"safe": tmp_path / "safe-root"}` for the test, then exercise traversal/symlink/extension paths.

Use `pytest.mark.parametrize` for the 8-root happy-path test and the 3 traversal-encoding variants.

## Acceptance criteria (from issue body)

- [ ] **Happy path file serve** — parametrized over all 8 `ALLOWED_ROOTS`. GET an existing HTML under each → 200, `Content-Type` matches, `Cache-Control: max-age=300`.
- [ ] **Happy path directory listing** — GET a directory path → 200 JSON with `root`, `items[].{name,size,mtime}`.
- [ ] **Happy path root index** — GET `/artifacts/` → 200 with all 8 roots listed.
- [ ] **Path traversal blocked** — three parametrized variants: raw `../../../etc/passwd`, URL-encoded `..%2f`, dotted `%2e%2e/`. Each → 404 (NOT 500).
- [ ] **Symlink escape blocked** — create a symlink under an allowed root pointing outside; GET → 403/404, content NOT served.
- [ ] **Forbidden extension** — `.py`, `.sh`, `.env` → 403/404.
- [ ] **Path under unapproved root** — `/artifacts/scripts/api/main.py` → 403/404.
- [ ] **Missing file** — non-existent path inside allowed root → 404.
- [ ] **Hidden file (dotfile)** — `/artifacts/audit/.git/HEAD` or similar → 403/404.

## Bonus (do these — they're cheap)

- [ ] **Performance smoke** — assert a 100KB HTML serves in <50ms (mirror the `/api/orient` 0.8s pattern from `test_playground_api_stability.py`). Tolerance: 200ms in CI to avoid flakes.
- [ ] **Concurrent access** — 10 parallel GETs (use `concurrent.futures.ThreadPoolExecutor` with the same TestClient or 10 clients) return correct content + 200.

## Numbered execution steps

1. **Verify worktree** — `git rev-parse --abbrev-ref HEAD` must print `codex/1822-artifacts-router-tests`. If not, STOP.

2. **Read context** — `scripts/api/docs_router.py` end-to-end, `scripts/api/main.py` (mount point), `tests/test_playground_api_stability.py` (style reference). Note the actual ALLOWED_ROOTS keys + paths.

3. **Find one existing HTML per allowed root** for the happy-path parametrize fixture. Run:
   ```
   .venv/bin/python -c "
   from scripts.api.docs_router import ALLOWED_ROOTS
   from pathlib import Path
   for k, v in ALLOWED_ROOTS.items():
       html = next(Path(v).rglob('*.html'), None)
       print(k, '->', html)
   "
   ```
   If a root has no .html (some are PDF/image roots), pick an existing file with an allowed extension.

4. **Implement `tests/test_docs_router.py`** per the AC list. Use:
   - `pytest.fixture` for a fresh `TestClient`
   - `monkeypatch` for negative-path tests with controlled `ALLOWED_ROOTS`
   - `pytest.mark.parametrize` for the 8-root and 3-traversal-encoding variants
   - `tmp_path` for symlink + filesystem fixtures
   - `concurrent.futures.ThreadPoolExecutor` for the concurrent test

5. **Run tests:**
   ```
   .venv/bin/pytest tests/test_docs_router.py -v
   ```
   ALL must pass. Investigate any failure carefully — it could be a real router bug. If you find one, file a separate issue and continue with the test pass; do NOT try to fix `docs_router.py` in this PR.

6. **Run sibling tests for regression** — `tests/test_artifacts_site_api.py` + `tests/test_playground_api_stability.py` + any other API-related tests:
   ```
   .venv/bin/pytest tests/test_artifacts_site_api.py tests/test_playground_api_stability.py tests/test_api_*.py -v
   ```
   None must regress.

7. **Lint** — `.venv/bin/ruff check tests/test_docs_router.py`.

8. **Commit** — single conventional commit:
   ```
   test(api): coverage for /artifacts/ docs router (#1822)

   Adds tests/test_docs_router.py with 9 ACs from the issue:
   - Happy path file serve (parametrized over all 8 ALLOWED_ROOTS)
   - Directory listing + root index
   - Path-traversal defense (raw, URL-encoded, %2e%2e variants)
   - Symlink escape defense
   - Extension allowlist
   - Unapproved-root + missing-file + dotfile defenses
   - Performance smoke (<50ms for 100KB HTML)
   - Concurrent access (10 parallel GETs)

   Closes #1822
   Refs #1814 (umbrella), c17450a6c1 (the original commit that landed
   the router without tests)
   ```

9. **Push** — `git push -u origin codex/1822-artifacts-router-tests`.

10. **Create PR** — `gh pr create --title "test(api): coverage for /artifacts/ docs router (#1822)" --body "..."`. Reference this brief. Do NOT enable auto-merge.

## What NOT to do

- Do NOT modify `scripts/api/docs_router.py`. This is a tests-only PR.
- Do NOT skip a negative test "because the real repo doesn't have a malicious symlink" — use `tmp_path` + monkeypatch.
- Do NOT enable auto-merge.
- Do NOT lower the perf budget below 200ms — flakes will haunt CI.

## Output expected

A single PR on branch `codex/1822-artifacts-router-tests` with `tests/test_docs_router.py` (only file added). PR body should list the 9 AC tests + 2 bonus tests with brief descriptions.
