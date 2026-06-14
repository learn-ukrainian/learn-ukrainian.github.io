# Dispatch: route CORE factual_accuracy + register off Gemini-family → deepseek (#3087)

## Why (bakeoff evidence — all 5 reviewers working, same B1 article, 3 repeats)
Reliability (score σ across repeats) on `factual_accuracy` / `register`:
- **deepseek: σ 0.47 / 0.0, 0 errors** ← most reliable, chosen
- claude: σ 0.0 / 0.82 but 1 error + burns interactive quota at CORE volume
- agy (status quo): σ 0.94 / 0.0 — the documented factual noise (REJECT flip)
- cursor: σ 0.94 — no better than agy; grok-build: σ 2.83 (scored 10,10,4) — worst

CORE `DEFAULT_PRIMARY` currently routes `factual_accuracy`→agy and `register`→agy
(Gemini-family → noisy AND same-family self-review since the wiki writer is also agy).
SEMINAR already overrides these to claude via `seminar_reviewer_overrides`. Add the CORE analog.

## Change (mirror the existing seminar pattern exactly)
1. **`scripts/wiki/review.py`** — add `core_reviewer_overrides(domain: str) -> dict[str, str]`
   directly beside `seminar_reviewer_overrides`. For CORE levels (a1–c2; i.e.
   `_infer_level_from_domain(domain)` is a core level, NOT "seminar"), return
   `{"factual_accuracy": "deepseek", "register": "deepseek"}`. For seminar domains return `{}`
   (so seminar's claude override stands). Add a module constant
   `_CORE_OFF_GEMINI_DIMS = ("factual_accuracy", "register")` + a `_CORE_REVIEWER = "deepseek"`
   so the routing is explicit and testable. Docstring: cite the #3087 bakeoff (deepseek σ 0.47/0.0,
   0 err) and that this removes agy same-family self-review.
2. **`scripts/wiki/compile.py:634`** — currently `review_overrides = seminar_reviewer_overrides(domain)`.
   Combine both (they are mutually exclusive by level, but be explicit):
   `review_overrides = {**core_reviewer_overrides(domain), **seminar_reviewer_overrides(domain)}`.
   Leave the `agent_overrides=review_overrides` call (line ~641) unchanged.
3. Do NOT touch `DEFAULT_PRIMARY` (keep agy as the global default / standalone-CLI default);
   this routes only the compile production path, matching how seminar does it (no blast radius).

## Tests (`tests/` — mirror any existing seminar_reviewer_overrides test)
- `core_reviewer_overrides("grammar/b1/aspect")` → `{"factual_accuracy":"deepseek","register":"deepseek"}`.
- `core_reviewer_overrides("folk/genres")` (seminar) → `{}`.
- `seminar_reviewer_overrides` unchanged for seminar; the combined dict in compile resolves
  CORE→deepseek and SEMINAR→claude correctly (a small unit asserting both branches).
- source_grounding + ukrainian_perspective are NOT changed for CORE.

## Numbered steps
1. `cd /Users/krisztiankoos/projects/learn-ukrainian && git fetch origin`. You are in a worktree from `origin/main`.
2. Implement 1–3.
3. `.venv/bin/python -m pytest tests/ -k "review or reviewer or compile" -q` → paste summary.
4. `.venv/bin/ruff check scripts/ tests/` → paste `All checks passed!`.
5. Commit: `feat(wiki): route CORE factual_accuracy+register off Gemini → deepseek (#3087)`.
6. `git push -u origin <branch>`; `gh pr create` referencing #3087. NO auto-merge.

## Evidence (#M-4): command + cwd + raw output for tests/lint/push/PR. Unproven claims = fabrication.
