# Triage report — 5 py/path-injection alerts (#1860)

## Alert #170 — scripts/api/docs_router.py:246

**Verdict:** FALSE POSITIVE
**Data-flow trace:**
- Step 1: `path` string enters `serve_artifact` via FastAPI route parameter
- Step 2: `path` is checked against allowed roots, returning `remainder` (user input) via `_get_root_info(path)` at line 233
- Step 3: `full_path` is created via `safe_join(root_path, remainder)` at line 241
- Step 4: `full_path` is verified via `_assert_under_root(full_path, root_path)` at line 244
- Sink: `full_path.exists()` is called at line 246

**Validation evidence (verbatim quotes with file:line):**
```python
# scripts/api/docs_router.py:241
        full_path = safe_join(root_path, remainder) if remainder else root_path.resolve()
# scripts/path_safety.py:48
        common = os.path.commonpath([abs_base, target])
# scripts/path_safety.py:52
    if common != abs_base:
        raise ValueError("Path escapes the configured root")
# scripts/api/docs_router.py:244
    _assert_under_root(full_path, root_path)
```

**If FP — dismissal comment for UI (<=200 chars):**
> FP: Code performs explicit path-traversal validation (`os.path.commonpath` check in `safe_join`). CodeQL doesn't recognize this validation pattern.

---

## Alert #172 — scripts/api/docs_router.py:262

**Verdict:** FALSE POSITIVE
**Data-flow trace:**
- Step 1: `path` string enters `serve_artifact` via FastAPI route parameter
- Step 2: `path` is checked against allowed roots, returning `remainder` (user input) via `_get_root_info(path)` at line 233
- Step 3: `full_path` is created via `safe_join(root_path, remainder)` at line 241
- Step 4: `full_path` is verified via `_assert_under_root(full_path, root_path)` at line 244
- Sink: `full_path` is passed to `FileResponse` at line 262

**Validation evidence (verbatim quotes with file:line):**
```python
# scripts/api/docs_router.py:241
        full_path = safe_join(root_path, remainder) if remainder else root_path.resolve()
# scripts/path_safety.py:48
        common = os.path.commonpath([abs_base, target])
# scripts/path_safety.py:52
    if common != abs_base:
        raise ValueError("Path escapes the configured root")
# scripts/api/docs_router.py:244
    _assert_under_root(full_path, root_path)
```

**If FP — dismissal comment for UI (<=200 chars):**
> FP: Code performs explicit path-traversal validation (`os.path.commonpath` check in `safe_join`). CodeQL doesn't recognize this validation pattern.

---

## Alert #176 — scripts/api/docs_router.py:110

**Verdict:** FALSE POSITIVE
**Data-flow trace:**
- Step 1: `path` string enters `serve_artifact` via FastAPI route parameter
- Step 2: `path` is checked against allowed roots, returning `remainder` (user input) via `_get_root_info(path)` at line 233
- Step 3: `full_path` is created via `safe_join(root_path, remainder)` at line 241
- Step 4: `full_path` is passed into `_assert_under_root(full_path, root_path)` at line 244
- Sink: `full_path.resolve()` is called inside `_assert_under_root` at line 110

**Validation evidence (verbatim quotes with file:line):**
```python
# scripts/api/docs_router.py:241
        full_path = safe_join(root_path, remainder) if remainder else root_path.resolve()
# scripts/path_safety.py:48
        common = os.path.commonpath([abs_base, target])
# scripts/path_safety.py:52
    if common != abs_base:
        raise ValueError("Path escapes the configured root")
```

**If FP — dismissal comment for UI (<=200 chars):**
> FP: The `full_path` is explicitly validated via `os.path.commonpath` in `safe_join` before being passed to `_assert_under_root` which calls `resolve()`. CodeQL misses the upstream validation.

---

## Alert #177 — scripts/api/docs_router.py:249

**Verdict:** FALSE POSITIVE
**Data-flow trace:**
- Step 1: `path` string enters `serve_artifact` via FastAPI route parameter
- Step 2: `path` is checked against allowed roots, returning `remainder` (user input) via `_get_root_info(path)` at line 233
- Step 3: `full_path` is created via `safe_join(root_path, remainder)` at line 241
- Step 4: `full_path` is verified via `_assert_under_root(full_path, root_path)` at line 244
- Sink: `full_path.is_dir()` is called at line 249

**Validation evidence (verbatim quotes with file:line):**
```python
# scripts/api/docs_router.py:241
        full_path = safe_join(root_path, remainder) if remainder else root_path.resolve()
# scripts/path_safety.py:48
        common = os.path.commonpath([abs_base, target])
# scripts/path_safety.py:52
    if common != abs_base:
        raise ValueError("Path escapes the configured root")
# scripts/api/docs_router.py:244
    _assert_under_root(full_path, root_path)
```

**If FP — dismissal comment for UI (<=200 chars):**
> FP: Code performs explicit path-traversal validation (`os.path.commonpath` check in `safe_join`). CodeQL doesn't recognize this validation pattern.

---

## Alert #173 — scripts/path_safety.py:23

**Verdict:** FALSE POSITIVE
**Data-flow trace:**
- Step 1: The `base` parameter is passed into the `safe_join` function
- Sink: `base.resolve()` is called when `parts` is empty at line 23
- Note: The `base` parameter is NOT user input. It is passed as a trusted root (e.g., from hardcoded `ALLOWED_ROOTS`). CodeQL incorrectly assumes generic function parameters are tainted.

**Validation evidence (verbatim quotes with file:line):**
```python
# scripts/api/docs_router.py:241
        full_path = safe_join(root_path, remainder) if remainder else root_path.resolve()
# scripts/path_safety.py:23
        return base.resolve()  # codeql[py/path-injection] - base is the trusted root passed by caller
```

**If FP — dismissal comment for UI (<=200 chars):**
> FP: The `base` parameter is a trusted, server-defined root path, not user input. CodeQL incorrectly taints the arguments of this public helper function.

---

## Summary

- Real bugs: 0
- False positives: 5 (alerts: #170, #172, #176, #177, #173)
- If any real bugs: N/A
- Confidence level on each verdict: H
