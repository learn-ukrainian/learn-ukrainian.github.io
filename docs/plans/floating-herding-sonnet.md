# Plan: Fix #665 + Remove Pipeline Blockers for Batch Processing

## Context

The pipeline hardening epic (#667) completed steps 1-3 (unit tests #668, B2 tests #669, v1/v2/v3 consolidation #671). Remaining: #670 (diagnose failing modules) and #672 (batch runs). Issue #665 (D.1 YAML parse failure) is a known bug blocking reliable Phase D execution.

**Goal**: Fix D.1 parsing, remove remaining blockers, enable batch processing of A1→A2→B1→B2.

**Current state**: 144 pipeline tests pass. Dispatcher stalled for 11 days (last run 2026-02-16). Modules at A2/B1/B2 have content but fail audit before Phase D.

---

## Step 1: Fix #665 — D.1 Review Parsing

### Root Cause

`_parse_d1_yaml()` (build_module_v3.py:2146-2236) first searches for YAML code fences (`` ```yaml ... ``` ``), but the D.1 template (`phase-D1-output-format.md`) asks for **Markdown structured output** — not YAML. The YAML path is vestigial from an older design. Every real D.1 review hits the "YAML parse failed" warning and falls to the prose regex fallback.

### Secondary Bug

`_extract_delimiter_tolerant()` (build_module_v3.py:619-668) validates extracted content with `yaml.safe_load()` and checks for `items` key — designed for vocab/activity YAML only. When D.1 review is truncated (missing `===REVIEW_END===`), tolerant extraction fails because Markdown isn't valid YAML. Result: truncated reviews are silently lost (`ok=False`).

### Fix

**`_parse_d1_yaml` → rename to `_parse_d1_review`**:
- Remove the YAML code fence search entirely (lines 2166-2187)
- Make Markdown regex parsing the primary and only path
- Also extract per-dimension scores from `## Scores` table (currently only gets `**Overall Score:**`)
- Update D1Result docstring
- Update all callers and test references

**`_extract_delimiter_tolerant` — add content-type awareness**:
- Add `content_type` param: `"yaml"` (default, current behavior) or `"markdown"`
- For `"markdown"`: skip YAML validation, just return cleaned content if non-empty
- `_parse_d1_review` calls tolerant with `content_type="markdown"`

### Files

| File | Change |
|------|--------|
| `scripts/build_module_v3.py` | Rename `_parse_d1_yaml` → `_parse_d1_review`, remove YAML path, add score table extraction, update `_extract_delimiter_tolerant` |
| `tests/test_pipeline_v3.py` | Update `TestParseD1Yaml` class name + imports, add test for truncated Markdown recovery, add test for score table extraction |

---

## Step 2: Rescan Dispatcher + Unblock Batch

The dispatcher state is 11 days stale. Before batch processing:

1. Run dispatcher scan to refresh module counts/pass rates
2. Verify A1 status (explore agent found 44/44 pass; dispatcher thinks 68%)
3. If A1 is at 100%, A2 auto-unblocks (needs 80%)

```bash
# Rescan all tracks
.venv/bin/python scripts/batch_dispatcher.py scan

# Check updated state
cat batch_state/dispatcher_state.json | .venv/bin/python -m json.tool
```

No code changes needed — just run the scan command after Step 1.

---

## Verification

```bash
# 1. Run pipeline tests (must stay at 144+ passing)
.venv/bin/python -m pytest tests/test_pipeline_v3.py tests/test_build_module_v3_comprehensive.py -v

# 2. Test D.1 parsing with real review fixture
.venv/bin/python -m pytest tests/test_pipeline_v3.py::TestParseD1Review -v

# 3. Verify dispatcher scan works
.venv/bin/python scripts/batch_dispatcher.py scan
```

---

## Scope Boundary

This plan covers **code fixes only** (#665 + tolerant extraction). Batch processing (#672) and failing module diagnosis (#670) are separate follow-up work after these fixes land.
