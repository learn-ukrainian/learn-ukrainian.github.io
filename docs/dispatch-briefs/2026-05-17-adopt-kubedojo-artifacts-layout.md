# Dispatch brief — Adopt kubedojo's artifacts page layout (server-rendered sections + table view)

**Agent:** Codex gpt-5.5 xhigh
**Mode:** danger (commits + PR open; NO auto-merge)
**Worktree:** required (per #1952)
**Why Codex:** Architect lane (E:A+ on store-pattern bakeoff 2026-05-17). This is server-rendered HTML + section classifier + Python templating — design judgment + code change, classic Codex shape.

---

## User direction

User 2026-05-17 night: *"i am not happy with how we organize artifact, please check out how kubeodjo does it, much better imo, can we adopt it please: http://127.0.0.1:8768/artifacts"*

## What kubedojo does (verified by orchestrator before writing this brief)

Visit `http://127.0.0.1:8768/artifacts` for the live reference (it's running on the user's machine). Key properties:

1. **Server-rendered HTML (376KB)** — no client JS roundtrip. First-paint = complete.
2. **4-card KPI bar** at top: `Total artifacts (866) | HTML files (40) | Markdown files (826) | Sections (13)`.
3. **13 collapsible `<details>` sections** with `<summary>` titles + count pill. First level closed/open toggle indicated by `>` / `v` glyph.
4. **Auto-classified sections** (the load-bearing UX win). Section names (in their display order):
   - Reports (12)
   - Migrations (3)
   - Handoffs (73)
   - Decisions (10)
   - Sessions (33)
   - Research (691) ← big bucket
   - Audits (4)
   - References (2)
   - Briefs (9)
   - Bug autopsies (1)
   - Dispatch briefs (1)
   - Docs (22)
   - Repository root (5)
5. **Per-section dense table** — columns: Title (linked) / Path (mono) / Type (pill: HTML green, MD blue) / Modified (relative pill "6m ago" / "1d ago") / Size (right-aligned KB).
6. **Single-column layout**, max-width 1200px, dark GitHub-ish theme.

## What we have today (verified by orchestrator)

- `scripts/api/docs_router.py` (434 lines) — discovers artifacts under `EFFECTIVE_ROOTS` (auto-detected `docs/*` + `audit/`), serves JSON via `/api/artifacts/html`. 1007 artifacts at audit time. Endpoint shape (per probe): `{generated_at, total, artifacts: [{path, url, class, date, status, title, kpi_summary, related_issues, related_prs, agents, author, size_bytes, modified_at}]}`.
- `dashboards/artifacts.html` (233 lines) — client-side JS template that fetches the JSON and renders **cards** (158px min-height, grid auto-fill min 290px). 6-field filter bar (search/class/status/author/type/date). 16-tile **"Operational dashboards"** ops-grid at top (Admin / Channels / Comms / Audit Dashboard / Build Events / Cost / Curriculum Dashboard / Delegate / Images / Orient / Progress / Quality / Runtime / Track Health / Wiki — color-coded by domain).

## What this PR ships

A server-rendered redesign of `dashboards/artifacts.html` that adopts kubedojo's section/table approach AND preserves our richer ops-dashboards surface. Hybrid, not pure clone.

### 1. New artifacts page renderer — `scripts/api/artifacts_page.py`

A new module that produces server-side HTML from the existing `collect_artifacts()` data. NO new data discovery — reuses `docs_router.collect_artifacts()`.

```python
"""Server-rendered HTML artifacts page (replaces dashboards/artifacts.html JS rendering)."""
from __future__ import annotations
import datetime as dt
from typing import Iterable

from scripts.api.docs_router import collect_artifacts

# Section classification table (path-prefix → section name, ordered by display priority).
SECTION_CLASSIFIERS: tuple[tuple[str, str], ...] = (
    # most specific first — first match wins
    ("docs/handoffs/", "Handoffs"),
    ("docs/session-state/", "Sessions"),
    ("docs/decisions/", "Decisions"),
    ("docs/dispatch-briefs/", "Dispatch briefs"),
    ("docs/bug-autopsies/", "Bug autopsies"),
    ("docs/reports/", "Reports"),
    ("docs/architecture/", "Architecture"),
    ("docs/best-practices/", "Best practices"),
    ("docs/references/", "References"),
    ("docs/proposals/", "Proposals"),
    ("docs/poc/", "POC"),
    ("docs/agents/", "Agents"),
    ("audit/", "Audits"),
    ("docs/", "Docs"),  # catch-all for any other docs/* path
    ("", "Repository root"),  # final catch-all
)

# Section display order (counts shown next to title; empty sections hidden).
SECTION_ORDER: tuple[str, ...] = (
    "Handoffs", "Sessions", "Decisions", "Dispatch briefs", "Bug autopsies",
    "Reports", "Audits", "Architecture", "Best practices", "Agents",
    "References", "Proposals", "POC", "Docs", "Repository root",
)


def classify(path: str) -> str:
    for prefix, name in SECTION_CLASSIFIERS:
        if path.startswith(prefix):
            return name
    return "Repository root"


def relative_time(modified_at_iso: str) -> str:
    """Return '6m ago' / '1d ago' style label from ISO timestamp."""
    # ... implementation: parse, diff against now (UTC), return human-friendly label
    # Buckets: <1m → "just now"; <60m → "Nm ago"; <24h → "Nh ago"; <7d → "Nd ago";
    # else absolute date "YYYY-MM-DD"


def render_artifacts_page(artifacts: list[dict], ops_dashboards: list[dict]) -> str:
    """Return full HTML page as string. Uses inline CSS (no external dep)."""
    # 1. Compute KPI bar: total, html_count, md_count, section_count
    # 2. Group artifacts by section, preserve SECTION_ORDER for display
    # 3. Within each section: sort by (modified_at DESC, path ASC)
    # 4. Emit:
    #    - <head> with inline CSS (steal palette from kubedojo: dark, github-ish — see brief)
    #    - top-bar with our existing nav (Home / Orient / Channels / Comms / Artifacts / Runtime)
    #    - hero with title + subtitle + total count
    #    - ops-dashboards section (KEEP from current — 16 tiles, color-coded, COLLAPSED by default via <details>)
    #    - KPI bar (4 cards)
    #    - <section id="sections"> with one <details><summary><h2>+count pill</h2></summary><table>...</table></details> per non-empty section
    #    - <details> "Advanced filters" at bottom (collapsed) — keeps current 6-field filter bar but JS-based and operates on the rendered DOM
    return html_string
```

Color/style: borrow kubedojo's CSS variables (dark theme with green/blue accents) and adapt to our existing `monitor.css` palette. Where they conflict, ours wins (consistency with Orient / Comms / Runtime pages already styled with `monitor.css`).

### 2. Wire the page into the existing route

`scripts/api/main.py` (or wherever `dashboards/artifacts.html` is served from) currently serves a static template. Add a route handler that:
- Calls `collect_artifacts()` to get the data
- Calls `render_artifacts_page()` to produce the HTML string
- Returns `HTMLResponse(html_string)` from FastAPI

**Path:** `/artifacts/` (replace current). Also keep `/artifacts/v1` or similar for back-compat for one release if it's easy; otherwise just replace.

**The `dashboards/artifacts.html` file becomes either:**
- (a) Deleted, replaced by the Python-rendered template, OR
- (b) Stub HTML that just contains a `<meta http-equiv="refresh">` to the new route, OR
- (c) Kept as a server-rendered fallback that the route reads + post-processes (NOT recommended — duplicates state)

**Pick (a)** unless there's a discovery test that requires the file to exist. If you pick (b) or (c), explain why in PR body.

### 3. Ops-dashboards strip — preserve

The 16-tile ops grid currently rendered in `dashboards/artifacts.html` is genuinely useful and richer than kubedojo's top-nav-only approach. Preserve it in the new rendered page, but:
- Wrap in `<details>` so it can be collapsed
- Default state: OPEN (it's the secondary navigation people scan first when they land on /artifacts/)
- Keep the 5-color category coding (runtime / agent / audit / pipeline / curriculum)

The list of 16 tiles + their categories + descriptions lives currently in the HTML. Lift them into a Python list-of-dicts constant in `artifacts_page.py` so they're maintainable from one place. Schema:

```python
OPS_DASHBOARDS: tuple[dict[str, str], ...] = (
    {"category": "runtime", "title": "Admin", "url": "/admin.html",
     "blurb": "Backups, health checks, disk usage, broker vacuum, log cleanup."},
    {"category": "agent", "title": "Agent Channels", "url": "/channels.html",
     "blurb": "Topic-scoped multi-agent discussion threads."},
    # ... 14 more
)
```

### 4. Filters — keep, but secondary

Current page has a 6-field filter bar (search / class / status / author / type / date) ABOVE the artifacts list. In the new page, move this to a `<details>` block AT THE BOTTOM titled "Advanced filters". Default state: COLLAPSED.

The filter logic is currently client-side JS reading the rendered DOM. Keep that pattern — operate on the sections' table rows (`tr` elements). When a filter matches, the matching `<details>` should auto-open and non-matching rows hide.

If the JS is too tangled to keep working on the new structure, ALL-RIGHT-TO-DEFER filter behavior to a follow-up PR — note in PR body and file follow-up issue. The section grouping is the primary UX win; filters are now secondary.

### 5. Tests

| Test | What |
|---|---|
| `tests/api/test_artifacts_page.py::test_classify_handoff` | `classify("docs/handoffs/foo.md") == "Handoffs"` |
| `..::test_classify_session_state` | `classify("docs/session-state/2026-05-17-foo.md") == "Sessions"` |
| `..::test_classify_dispatch_brief` | `classify("docs/dispatch-briefs/2026-05-17-foo.md") == "Dispatch briefs"` |
| `..::test_classify_audit_root` | `classify("audit/2026-05-17-foo/REPORT.md") == "Audits"` |
| `..::test_classify_unknown_falls_back_to_docs` | `classify("docs/internal-notes/foo.md") == "Docs"` |
| `..::test_classify_root_file` | `classify("README.md") == "Repository root"` |
| `..::test_relative_time_minutes` | `relative_time(now-6min) == "6m ago"` |
| `..::test_relative_time_hours` | `relative_time(now-2h) == "2h ago"` |
| `..::test_relative_time_days` | `relative_time(now-3d) == "3d ago"` |
| `..::test_relative_time_old_falls_back_to_date` | `relative_time(now-30d) == "2026-04-17"` (or similar absolute) |
| `..::test_render_includes_all_sections_with_artifacts` | render → assert each non-empty section header appears in HTML |
| `..::test_render_kpi_bar_counts` | render with synthetic 5 HTML + 10 MD → assert KPI bar shows `Total artifacts 15 \| HTML 5 \| Markdown 10 \| Sections N` |
| `..::test_render_section_order` | render → assert sections appear in `SECTION_ORDER` order, even when alphabetical would differ |
| `..::test_render_skips_empty_sections` | render with no Decisions → assert "Decisions" section NOT in HTML |
| `..::test_render_table_columns` | render → assert each table has Title/Path/Type/Modified/Size columns |
| `..::test_render_html_well_formed` | render → assert `<html>`, `<head>`, `<body>`, `</html>` present and matched count |
| `..::test_ops_dashboards_strip_present` | render with `OPS_DASHBOARDS=[...]` → assert all titles + URLs in HTML |
| `..::test_route_returns_html` | FastAPI test client GET `/artifacts/` → assert 200 + `text/html` content type + contains "Artifacts" in title |
| `..::test_route_classification_stable_against_known_corpus` | smoke against real `collect_artifacts()` output → assert no section count drops to 0 unexpectedly (regression guard) |

---

## Verifiable claims this PR must produce (per #M-4)

| Claim | Tool + raw output to quote in PR body |
|---|---|
| New module landed | `git diff --stat origin/main` showing `scripts/api/artifacts_page.py` row + `dashboards/artifacts.html` deletion (or stub) row + `tests/api/test_artifacts_page.py` row |
| All new tests pass | `.venv/bin/pytest tests/api/test_artifacts_page.py -v` final summary line raw |
| Existing API tests still pass | `.venv/bin/pytest tests/api/ -q` final summary line raw (NO `-x` per #1942) |
| Full pytest still green | `.venv/bin/pytest tests/ -q --ignore=tests/build/` final summary line raw |
| Ruff clean | `.venv/bin/ruff check scripts/api/artifacts_page.py tests/api/test_artifacts_page.py` raw output (must be `All checks passed!`) |
| Live smoke against running API | restart API + `curl -s http://localhost:8765/artifacts/ \| python3 -c "import sys,re; html=sys.stdin.read(); sections=re.findall(r'<h2[^>]*>([^<]+)</h2>', html); print(f'sections in rendered page: {len(sections)}'); print(sections[:15])"` raw output (expect 8-15 section headers per the SECTION_ORDER + non-empty filter) |
| Commit landed + PR opened | `git log -1 --oneline` raw + `gh pr view --json url` raw URL |

**No claim allowed without its raw output line.** Per #M-4.

---

## Worktree setup

`delegate.py dispatch --worktree` handles creation. Branch name: `feat/artifacts-page-server-rendered`.

---

## Verification (must run all BEFORE pushing)

```bash
# venv symlinked from main; run from worktree root
.venv/bin/pytest tests/api/test_artifacts_page.py -v
.venv/bin/pytest tests/api/ -q
.venv/bin/pytest tests/ -q --ignore=tests/build/
.venv/bin/ruff check scripts/api/artifacts_page.py tests/api/test_artifacts_page.py scripts/api/main.py
.venv/bin/python -m pre_commit run --files \
    scripts/api/artifacts_page.py \
    tests/api/test_artifacts_page.py \
    scripts/api/main.py \
    dashboards/artifacts.html
git diff --stat origin/main
```

Per #M-7: pre-commit ≠ pytest. Both required.

If you can't restart the API from inside the worktree (deployment-ish action), skip the live smoke and note in PR body — orchestrator will restart + verify.

---

## Commit + PR

Title: `feat(api): server-rendered artifacts page with classified sections + table view`

Commit message:

```
feat(api): server-rendered artifacts page with classified sections (kubedojo-inspired)

User direction 2026-05-17: kubedojo's /artifacts page (4-card KPI bar + 13
collapsible <details> sections + dense table view + relative-time pills)
is genuinely more usable for a 1000+-document corpus than our card grid.
Adopt the structure; preserve our richer ops-dashboards strip.

What this PR ships:
* scripts/api/artifacts_page.py — section classifier (path prefix → section
  name table), relative_time() helper, render_artifacts_page() that emits
  the full HTML server-side.
* dashboards/artifacts.html — deleted (replaced by Python-rendered route).
* scripts/api/main.py — /artifacts/ route now returns the server-rendered
  HTML instead of static file.
* 18+ tests covering classifier, relative-time, render, ops-dashboards
  strip, section ordering, empty-section skip, and route smoke.

Preserved from old page:
* 16-tile ops-dashboards strip (Admin / Channels / Comms / Audit Dashboard
  / Build Events / Cost / Curriculum Dashboard / Delegate / Images / Orient
  / Progress / Quality / Runtime / Track Health / Wiki) — wrapped in
  <details>, open by default, lifted from HTML into Python list-of-dicts.
* 6-field filter bar (search/class/status/author/type/date) — moved to
  collapsed "Advanced filters" <details> at bottom, JS operates on
  rendered DOM.
* /api/artifacts/html JSON endpoint UNCHANGED (back-compat).

Sections (auto-classified by path prefix; empty sections hidden):
Handoffs, Sessions, Decisions, Dispatch briefs, Bug autopsies, Reports,
Audits, Architecture, Best practices, Agents, References, Proposals, POC,
Docs, Repository root.

Verification:
* tests/api/test_artifacts_page.py: <quote pytest final line>
* tests/api/ full: <quote pytest final line>
* tests/ full (excl tests/build/): <quote pytest final line>
* ruff: <quote raw>
* live smoke section count: <quote stdout>
```

PR body:

```markdown
## Summary

Adopts kubedojo's artifacts page layout (verified by orchestrator at http://127.0.0.1:8768/artifacts before brief written): server-rendered, 4-card KPI bar, 13 collapsible <details> sections grouped by document class, dense table view (Title / Path / Type / Modified / Size), relative-time pills. Replaces our client-side card grid which doesn't scale past ~300 documents (current corpus: 1007).

Preserves the 16-tile **Operational dashboards** strip at top — it's richer than kubedojo's top-nav-only approach — but moves it inside a `<details>` so it can be collapsed. Filters become "Advanced filters" at bottom (collapsed by default).

## Verifiable claims (per #M-4)

* `git diff --stat`: <quote raw>
* `pytest test_artifacts_page.py`: <quote final line>
* `pytest tests/api/`: <quote final line>
* `pytest tests/ (excl build)`: <quote final line>
* `ruff`: <quote raw>
* live smoke section count: <quote stdout>

## Test plan

- [x] Classifier returns correct section for each path-prefix
- [x] Catch-all paths go to "Docs" or "Repository root"
- [x] Relative-time formatter handles min/hour/day/old buckets
- [x] Render emits each non-empty section in display order
- [x] Render KPI bar counts match input
- [x] Empty sections are hidden
- [x] Ops-dashboards strip preserved
- [x] /artifacts/ route returns HTML
- [x] /api/artifacts/html JSON endpoint unchanged (no test breakage)
```

NO `--auto-merge`. Leave the PR open; orchestrator reviews + merges after CI green.

---

## Out of scope (do NOT do)

* Changing `/api/artifacts/html` JSON endpoint shape (back-compat).
* Adding new artifact fields (size_bytes already there; status / class / author / kpi_summary all in current JSON).
* Re-classifying or moving any actual artifact file on disk — classifier reads path patterns, doesn't reorganize the tree.
* Adding new ops-dashboard tiles (preserve existing 16; new tiles are a follow-up PR).
* Server-side filter implementation (JS operates on rendered DOM — kubedojo doesn't have filters at all; deferring is acceptable).
* Light theme support (kubedojo is dark-only; our monitor.css is also dark — defer light-mode toggle).
* Search infrastructure change (existing JS searches `title + path + kpi_summary` substring; preserve that behavior).
* Changes to `scripts/api/docs_router.py` `collect_artifacts()` — reuse as-is.

---

## Anti-fabrication preamble

If the existing route for `/artifacts/` is wired differently than expected — e.g., served by Starlette `StaticFiles` mount rather than a FastAPI route handler — STOP and quote the actual mount setup before patching. Don't paper over.

If `dashboards/artifacts.html` has features the orchestrator's inspection missed (e.g., a websocket subscription for live updates, an embedded service-worker, an admin-mode toggle), preserve them in the new page or explicitly call out in the PR body that you dropped them with rationale.

If kubedojo's section list (Reports / Migrations / Handoffs / Decisions / Sessions / Research / Audits / References / Briefs / Bug autopsies / Dispatch briefs / Docs / Repository root) maps to path prefixes that DON'T exist in our tree — that's expected (their tree is different). Use OUR tree's prefixes as the source of truth for SECTION_CLASSIFIERS. The orchestrator's proposed list above is a strawman; refine based on what's actually in `collect_artifacts()` output.

If the live smoke reveals 0 artifacts in a section that should be populated — that's a classifier bug. Fix and re-run before declaring done.

If a test feels redundant or impossible to write deterministically, name the specific test and the specific blocker; do not silently drop tests from the list.
