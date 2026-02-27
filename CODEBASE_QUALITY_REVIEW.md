# Codebase Quality Review

> Generated: 2026-02-18 | Scope: `scripts/`, `tests/`, config files
> Linked: GH #540

---

## Summary

The codebase is structurally sound but has accumulated significant technical debt from rapid development sprints. Most issues fall into three categories: **stale scripts** (migration one-offs that ran once and were never deleted), **duplicated utility logic** (load_curriculum defined 9 times), and **test suite drift** (dashboard tests referencing removed files).

No critical bugs found in active pipeline code. Issues below are ranked by impact.

---

## 1. Deprecated Scripts (Safe to Remove)

### 1a. Explicitly Deprecated (delete immediately)

| Script | Reason | Replacement |
|--------|---------|-------------|
| `scripts/signal_claude.py` | Marked `DEPRECATED` in file header | `scripts/ai_agent_bridge.py` |
| `scripts/generate_resource_sections.py` | Marked `DEPRECATED — DO NOT USE IN BUILD PIPELINE` | Resources injected at MDX generation time |

Both files have warnings in their headers but still clutter the `scripts/` root. Neither is referenced in `package.json`, docs, or any other script.

### 1b. Debug Scripts (delete)

Dead code analyzer flagged these as zero-reference debug utilities:

- `scripts/debug_immersion.py` (40 days stale)
- `scripts/debug_hash.py` (13 days)
- `scripts/debug_pymorphy.py` (13 days)
- `scripts/debug_stanza.py` (13 days)

### 1c. Ad-hoc Test Scripts (delete or move to `tests/`)

These live in `scripts/` but behave like tests — no production use:

- `scripts/test_regex.py`
- `scripts/test_regex_cloze.py`
- `scripts/test_richness_patch.py`
- `scripts/test_frontend_integrity.py`

If valuable, move to `tests/`. If one-off experiments, delete.

---

## 2. One-Off Migration Scripts (47 files)

The `scripts/fix_*.py` pattern contains 47 scripts created to patch data during development sprints. Most ran once and are now dead weight.

**Examples:**
- `fix_activity_ids.py`, `fix_activity_ids_a1_a2_c1.py` — IDs already assigned
- `fix_cloze_blank_lines.py`, `fix_cloze_structure.py` — Cloze format stabilized
- `fix_b2hist_plans.py`, `fix_b2_yaml.py` — HIST plans finalized
- `fix_anagrams.py`, `fix_ascii_quotes.py`, `fix_md_quotes.py` — formatting passes done

**Recommendation:** Audit each, archive ones with no future use into `scripts/archive/` or delete. The `analyze_dead_code.py` script categorizes most as "medium risk" — verify via its report before mass-deleting.

**Similarly stale:**
- `scripts/update_a2_immersion.py` — one-time migration for A2 bands, now superseded by `get_a2_immersion_range()` in `audit/config.py`
- `scripts/add_content_outline.py`, `add_practice_section.py`, `add_summary_to_meta.py` — one-time additions, likely done

---

## 3. Duplicated Logic

### 3a. `load_curriculum()` defined 9 times

Every script that needs the curriculum manifest defines its own loader:

```
scripts/extract_plans.py         → load_curriculum_yaml()
scripts/sync_plan_sequence.py    → load_curriculum()
scripts/validate_module_numbering.py → load_curriculum()
scripts/sync_module_ids.py       → load_curriculum()
scripts/validate_curriculum_plans.py → load_curriculum()
scripts/verify_track.py          → load_curriculum()
scripts/generate_level_status.py → load_curriculum_yaml()
scripts/fix_bio_ids.py        → load_curriculum_order()
scripts/update_a2_immersion.py   → load_curriculum_modules()
```

`slug_utils.py` already has a docstring saying "All scripts should import from here instead of using inline re.sub or stem[3:]." The same principle should apply to curriculum loading. A shared `scripts/curriculum_utils.py` would eliminate 9 duplicates.

### 3b. `curriculum.yaml` opened inline in 35+ scripts

Beyond the named functions above, 35 scripts open `curriculum.yaml` with raw `open()` + `yaml.safe_load()` without any error handling or path resolution utility.

**Recommendation:** Create `scripts/curriculum_utils.py` with:
```python
def load_curriculum() -> dict: ...
def get_track_modules(track: str) -> list[str]: ...
def get_module_slug(track: str, num: int) -> str: ...
```

This is a medium-priority refactor (scripts still work, just harder to maintain).

---

## 4. TODO / FIXME Comments

| File | Line | Item |
|------|------|------|
| `scripts/audit/checks/vocabulary.py` | 515 | `# TODO: Re-enable blocking after vocab enrichment is complete` |
| `scripts/audit/report.py` | 209 | `"audit_duration_ms": 0, # TODO: Track duration` |
| `scripts/audit/checks/activities.py` | 914, 928 | Two deprecated resource check functions |
| `scripts/auto_vocab_extract.py` | 153 | `# TODO: Could be enhanced to only load modules 01-current` |
| `scripts/validate_external_resources.py` | 345 | `# TODO: Implement --check-urls if flag is set` |
| `scripts/vocab-manager.py` | 267 | `# TODO: Validate modules against vocab.csv` |
| `scripts/migrate_to_v2.py` | 9 | `Part 2: Generate Status Cache (TODO)` |

**Priority:** The vocabulary gate TODO (line 515) is the most important — it currently skips blocking which means vocab errors silently pass.

---

## 5. Test Suite Issues

### 5a. Hard Error: Missing Dashboard File

```
tests/test_api_router_split.py::TestDashboardApiPaths::test_no_stale_blue_paths
```
**Error:** `AssertionError: Dashboard not found: playgrounds/v2-blue/batch-monitor.html`

The file `playgrounds/v2-blue/batch-monitor.html` was deleted from the repo but the test was not updated. Also affects `tests/test_blue_dashboard_ui.py` (references same path via live server).

**Fix options:**
1. If the v2-blue dashboard is gone permanently: delete `tests/test_api_router_split.py::TestDashboardApiPaths` and `tests/test_blue_dashboard_ui.py`
2. If the dashboard will be rebuilt: add `pytest.skip` with a TODO until the file exists

### 5b. Expected Failures (not code bugs)

These failures are expected given the in-progress curriculum build, not code quality issues:

- `tests/test_docusaurus_links.py` — 26 failures: MDX not yet generated for all modules (c1, istorio, lit, etc. still building)
- `tests/test_gold_dashboard_ui.py` — 4 errors: require live API server at localhost:8765

Total baseline: **648 passing, 27 failing, 36 errors** (36 errors are API/server-dependent, expected when server not running).

---

## 6. Undocumented New Scripts

`scripts/scan_activity_errors.py` was recently added (git untracked) but is not documented in `docs/SCRIPTS.md`. It's a useful batch scanner for structural activity errors — should be documented.

---

## 7. Error Handling Patterns

`scripts/audit/core.py` has 13 `except Exception` / bare `except:` clauses. One pattern that recurs:

```python
try:
    ...
except Exception:
    pass  # Non-critical — don't break audit if X fails
```

This pattern is correct for non-critical gates (IPA lint, naturalness) but makes debugging harder. **Recommendation:** Log to stderr with `logging.debug()` even in non-critical catches so failures are visible when debugging.

---

## Recommendations (Prioritized)

| Priority | Action | Effort |
|----------|--------|--------|
| 🔴 High | Delete 2 explicitly deprecated scripts (`signal_claude.py`, `generate_resource_sections.py`) | 5 min |
| 🔴 High | Fix or skip `test_api_router_split.py` dashboard test (blocks `-x` test runs) | 15 min |
| 🟡 Medium | Delete/archive 9 dead debug/test scripts from `scripts/` | 10 min |
| 🟡 Medium | Enable vocabulary blocking gate (remove TODO on line 515) | 30 min |
| 🟡 Medium | Document `scan_activity_errors.py` in `docs/SCRIPTS.md` | 10 min |
| 🟢 Low | Create `scripts/curriculum_utils.py` shared loader | 2 hrs |
| 🟢 Low | Archive `fix_*` one-off migration scripts | 1 hr |
| 🟢 Low | Add `logging.debug()` to silent `except: pass` blocks | 1 hr |

---

## Out of Scope

Per #540 constraints, curriculum content files (`.md`, activities YAML, vocabulary YAML) and audit logic/scoring thresholds were not reviewed.
