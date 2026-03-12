# Plan: Merge Discover into Research + Pipeline Fixes

## Context

The pipeline v5 has separate `research` and `discover` phases, but they serve overlapping goals — both gather information before content writing. The user wants to merge discover into research so all pre-content intelligence gathering happens in one phase. Additionally, Claude research dispatch is missing MCP RAG tools, phase delimiter mapping is wrong for research, the beginner activity types aren't being required for early A1 modules, and obsolete MDX files need cleanup.

## Changes

### 1. Merge discover into research (`scripts/build/pipeline_v5.py`)

**Goal**: Run discovery (video/blog/RAG search) inside `phase_research()` after LLM dispatch completes, then remove standalone `phase_discover()`.

**a) Add `_run_discovery_within_research()` helper** (after `_append_discovery_to_research`, ~line 1020):
```python
def _run_discovery_within_research(ctx: ModuleContext, state: dict) -> None:
    """Run discovery search within the research phase (non-blocking)."""
    # Import video_discovery, call run_discovery + search_blogs + search_rag
    # Write discovery.yaml, update external_resources.yaml
    # Append results to research file
    # Same logic as phase_discover() but without state management
```
- Extract the core logic from `phase_discover()` (lines 1947-2014) into this helper
- Call it at the end of `phase_research()`, after `_save_research_output()` but before `_apply_meta_outline()`
- Non-blocking: wrap in try/except, log warnings on failure
- Skip if `ctx.skip_discover` or `ctx.dry_run`

**b) Update `phase_research()`** (line ~1853):
- After `_save_research_output()`, call `_run_discovery_within_research(ctx, state)`
- Mark discover as complete within research: `mark_complete(state, "discover", ctx, note="merged-into-research")`

**c) Make `phase_discover()` a no-op passthrough**:
- Keep the function but make it immediately return True with a log message: "discover: SKIP (merged into research phase)"
- This avoids breaking `--restart-from discover` or any external references

**d) Update `PHASE_FUNCTIONS` dict** — no change needed (discover stays as passthrough)

### 2. Fix Claude research tool allowlist (`scripts/build/pipeline_v5.py:1722`)

**Current**: `allow_tools=["WebSearch", "WebFetch", "Read"]`

**Change to**:
```python
allow_tools=[
    "WebSearch", "WebFetch", "Read",
    "mcp__rag__search_text", "mcp__rag__verify_word",
    "mcp__rag__verify_lemma", "mcp__rag__search_images",
    "mcp__rag__search_literary", "mcp__rag__query_wikipedia",
]
```

### 3. Fix `_PHASE_DELIMITERS` for research (`scripts/build/pipeline_v5.py:324`)

**Current**: `"A": ("===META_OUTLINE_START===", "===META_OUTLINE_END===")`

**Change to**: `"A": ("===RESEARCH_START===", "===RESEARCH_END===")`

The beginner-research template produces `===RESEARCH_START===` / `===RESEARCH_END===` delimiters, not META_OUTLINE.

### 4. Make `_apply_meta_outline()` non-fatal (`scripts/build/pipeline_v5.py:1768`)

**Current**: Returns `False` (fails pipeline) when no META_OUTLINE found.

**Change**: When meta_text is None/empty, log an INFO message and return `True`. The plan is now the source of truth for content_outline — meta_outline generation is a legacy feature that beginner modules don't use.

Lines 1768-1769:
```python
if not meta_text:
    log("  research: No META_OUTLINE — plan content_outline is source of truth")
    return True
```

### 5. Fix beginner activity REQUIRED_TYPES (`scripts/pipeline_lib.py:2470-2477`)

**Problem**: A1 `REQUIRED_TYPES` is empty. The fallback at line 2474 picks first 3 from `PRIORITY_TYPES` which are `fill-in, match-up, anagram` — missing the bukvar types (`watch-and-repeat`, `classify`, `image-to-letter`).

**Fix**: For A1 modules 1-4 (alphabet/pre-literacy modules), override REQUIRED_TYPES to include the bukvar activity types. Add logic after line 2477:

```python
# Early A1 alphabet modules require bukvar activity types
if ctx.track == "a1" and ctx.module_num <= 4:
    bukvar_types = ["watch-and-repeat", "classify", "image-to-letter"]
    existing = [t.strip() for t in placeholders.get("REQUIRED_TYPES", "").split(",") if t.strip()]
    for bt in bukvar_types:
        if bt not in existing:
            existing.append(bt)
    placeholders["REQUIRED_TYPES"] = ", ".join(existing)
```

### 6. Delete obsolete MDX files

Remove 4 files (old cyrillic-code naming, replaced by new M1-M4 slugs):
- `starlight/src/content/docs/a1/the-cyrillic-code-i.mdx`
- `starlight/src/content/docs/a1/the-cyrillic-code-ii.mdx`
- `starlight/src/content/docs/a1/the-cyrillic-code-iii.mdx`
- `starlight/src/content/docs/a1/the-cyrillic-code-iv.mdx`

## Critical Files

| File | Change |
|------|--------|
| `scripts/build/pipeline_v5.py` | Changes 1-4 (merge discover, fix tools, fix delimiters, non-fatal meta outline) |
| `scripts/pipeline_lib.py` | Change 5 (bukvar REQUIRED_TYPES for A1 M1-4) |
| `starlight/src/content/docs/a1/the-cyrillic-code-*.mdx` | Change 6 (delete) |

## Verification

1. **Unit tests**: `pytest tests/test_lint_prompts.py` — all pass
2. **Dry-run M1**: `.venv/bin/python scripts/build_module_v5.py a1 1 --dry-run --use-claude A` — research phase runs, discover is merged
3. **Dry-run M3**: `.venv/bin/python scripts/build_module_v5.py a1 3 --dry-run --use-claude A` — same
4. **Check placeholder generation**: Verify REQUIRED_TYPES includes bukvar types for M1-M4
5. **Full test suite**: `pytest` — no regressions
