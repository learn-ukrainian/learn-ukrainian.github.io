# Tech Debt Registry

> Tracked via GitHub Issues with the `tech-debt` label.
> Query: `gh issue list --label tech-debt --state open`

## Active Items

### TD-1: Combined fix phase fallback active for meta-only gate failures

**Issue:** `phase-fix.md` (combined fix) is still used as fallback when only metadata/audit meta gates fail. Three templates doing similar work increases maintenance burden.

**Impact:** Low — meta-only gate failures are rare, but the combined template still works.

**Resolution:** Monitor whether the combined fix is still needed after split phases are validated in production. If not triggered for 50+ modules, remove it and always use split phases.

**Filed:** 2026-02-10

### TD-4: Hardcoded activity examples in runner

**Issue:** `_get_seminar_activity_examples()` and `_get_core_activity_examples()` return hardcoded YAML strings. If the activity schema evolves (new fields, renamed types), these examples become stale.

**Impact:** Low — examples are correct today and changes to the schema are infrequent.

**Resolution:** Generate examples from the schema file or a shared examples directory rather than hardcoding. Not urgent.

**Filed:** 2026-02-10

## Resolved Items

### TD-2: Schema filter uses heuristic header matching

**Status:** Resolved — verification tests added (`tests/test_batch_fix_mode.py::TestSchemaFilterVerification`)

**Issue:** `_filter_schema_for_track()` in `batch_gemini_runner.py` parses ACTIVITY-YAML-REFERENCE.md headers with heuristic matching (`header_text.startswith(atype)`). If header format changes, the filter breaks silently.

**Resolution:** Added CI tests that verify: (1) all LEVEL_CONFIG priority_types exist in the filter's ALL_TYPES set, (2) seminar priority types have parseable H3 headers in the schema file, (3) filter produces non-empty output for each seminar track.

**Filed:** 2026-02-10 | **Resolved:** 2026-02-10

### TD-3: No integration tests for batch runner fix loop

**Status:** Resolved — integration tests added (`tests/test_batch_fix_loop_integration.py`)

**Issue:** The fix loop (`process_module_fix`) had unit tests for routing logic but no integration test exercising the full audit → diagnose → fix → re-audit flow.

**Resolution:** Created mock-based integration tests covering: happy path (audit fail → fix → pass), stall detection (same gates fail 3x → break), activities-only routing, and iteration exhaustion.

**Filed:** 2026-02-10 | **Resolved:** 2026-02-10

### TD-5: oes/ruth missing from TRACK_CONFIGS

**Status:** Resolved — invalid (already implemented)

**Issue:** Claimed `oes` and `ruth` had no entry in `TRACK_CONFIGS`. Investigation found both tracks are already present in `batch_gemini_config.py` (lines 184-213) with `type: "seminar"`.

**Resolution:** No code change needed. Verified by existing test `test_oes_and_ruth_have_seminar_type` in `tests/test_batch_fix_mode.py`.

**Filed:** 2026-02-10 | **Resolved:** 2026-02-10

### TD-6: Research path unconditional in fix-content template

**Status:** Resolved — fallback message added

**Issue:** `_generate_prompt()` in `batch_gemini_runner.py` referenced research content for all tracks. Core tracks don't generate research files, resulting in empty context being passed to Gemini.

**Resolution:** Added fallback `if not research_content: research_content = "(no research file available)"` after the `_read_file_safe()` call, matching the pattern in `batch_review.py`.

**Filed:** 2026-02-10 | **Resolved:** 2026-02-10
