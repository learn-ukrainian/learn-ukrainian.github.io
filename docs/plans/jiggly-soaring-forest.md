# l2-uk-direct Build Pipeline

## Context

The 47 A1 module YAML plans are complete in `curriculum/l2-uk-direct/a1/`. These YAMLs already contain vocabulary, activities, grammar tables, and teaching notes. Unlike l2-uk-en (where the pipeline creates content from scratch), the l2-uk-direct pipeline **enriches** existing plans, **validates** correctness, optionally **reviews** cross-agent, and **generates MDX**.

The l2-uk-en pipeline (`build_module.py`) is 5000+ lines with 7 phases, v3/v4 state machines, orchestration directories, and complex retry logic. That complexity is not needed here. We build a separate, simpler script.

## Pipeline Phases

```
enrich → validate → [review] → mdx
```

| Phase | Actor | Purpose |
|-------|-------|---------|
| `enrich` | Gemini | Fill gaps: expand thin activities, add teaching notes, suggest pronunciation video URLs |
| `validate` | Deterministic | Schema check, activity count, Latin detection, decodability |
| `review` | Claude (optional) | Cross-agent adversarial review |
| `mdx` | Deterministic | Generate MDX via existing `generate_mdx_direct.py` |

## Files to Create

### 1. `scripts/build_module_direct.py` (~350 lines)

Main pipeline script. Key components:
- `DirectModuleContext` dataclass (slug, level, yaml_path, status_path, module_data, etc.)
- `load_status()` / `save_status()` — read/write `.status.json`
- `is_phase_complete()` / `mark_phase_complete()` — phase state helpers
- `phase_enrich(ctx)` — build prompt from template, dispatch to Gemini, parse YAML output, sanity-check critical fields preserved, write back
- `phase_validate(ctx)` — call `validate_direct.validate_file()`, report errors/warnings
- `phase_review(ctx)` — build review prompt, dispatch to Claude via `ai_agent_bridge.py`, parse verdict
- `phase_mdx(ctx)` — subprocess call to `generate_mdx_direct.py`
- `get_available_letters(level, slug)` — compute cumulative letter set for decodability
- `run_pipeline(ctx)` — main loop over phases
- CLI: `build_module_direct.py {level} {slug} [--review] [--force-phase X] [--validate-only] [--mdx-only] [--all]`

Reuses from `pipeline_lib.py`: `dispatch_gemini()`, `log()`, `_now_iso()`, `PRO_MODEL`

### 2. `claude_extensions/phases/gemini/direct-enrich.md`

Gemini prompt template for enrich phase. Structure:
- Role definition (enriching, not creating)
- Current YAML content injected inline
- Module context (slug, type, position, available letters)
- Enrichment rules: expand activities to minimums, add teaching notes, ensure all vocab items have sentences
- Output format: complete YAML, no markdown fences
- Hard constraint: preserve module/track/level/type/title fields exactly

### 3. `claude_extensions/phases/claude/direct-review.md`

Claude review prompt template. 5-dimension checklist:
1. Ukrainian language correctness (grammar, no Russianisms)
2. Pedagogical soundness (A1-appropriate, no scope creep)
3. Activity correctness (answers match, distractors plausible)
4. L1-agnosticism (zero English in content)
5. Decodability (script_foundation modules only)

Output: JSON with verdict (PASS/FAIL), issues list, summary.

## Files to Modify

### `scripts/status_direct.py`
- Add `enriched`, `validated`, `reviewed` to `STATUS_EMOJI` and `STATUS_ORDER`

### `scripts/validate_direct.py`
- Add `"reading"` and `"writing"` to `VALID_MODULE_TYPES` (modules 44-45 use these types)
- Verify `validate_file()` return works cleanly for pipeline import (already returns `ValidationResult`)

## State Machine

Status in `.status.json`:
```
draft → enriched → validated → reviewed → ready
```

Phase tracking added to `.status.json`:
```json
{
  "module": "tse",
  "track": "l2-uk-direct",
  "level": "a1",
  "status": "validated",
  "phases": {
    "enrich": {"status": "complete", "ts": "2026-03-05T14:20:00Z"},
    "validate": {"status": "complete", "ts": "2026-03-05T14:25:00Z", "errors": 0, "warnings": 2}
  }
}
```

Phase completion is idempotent. Re-running skips completed phases unless `--force-phase`.

## Enrich Phase Details

**Gemini dispatch:** Uses `dispatch_gemini()` from `pipeline_lib.py` with `PRO_MODEL`, timeout 600s, stdout_only=True.

**Safety checks after Gemini returns:**
1. Output parses as valid YAML
2. Critical fields (module, track, level, type, title) unchanged
3. Activity count did not decrease
4. Vocabulary item count did not decrease

If any check fails, reject the enrichment and mark phase failed.

## Decodability

For `script_foundation` modules, compute cumulative letter set from manifest sequence:

```python
def get_available_letters(level, target_slug):
    manifest = load_manifest()
    letters = set()
    for slug in manifest[level]:
        data = load_yaml(slug)
        if data.get("type") == "script_foundation":
            for letter in data.get("letters", []):
                letters.add(letter["upper"])
                letters.add(letter["lower"])
        if slug == target_slug:
            break
    return letters
```

Used in: enrich prompt (constraint for Gemini) + validate phase (check compliance).

## Review Phase Details

Cross-agent: Gemini enriched, Claude reviews. Dispatch via `ai_agent_bridge.py ask-gemini` with `--model claude-opus-4-6` (or direct subprocess to `claude` CLI following `build_module.py` pattern).

Max 1 fix attempt in v1. If review fails, log issues and mark failed.

## v1 Scope Boundaries (NOT building)

- No parallel batch execution
- No VESUM word verification (add later as `--vesum` flag)
- No image sourcing (separate pipeline)
- No completion reports
- Max 1 review fix attempt
- No audit/config.py integration (direct track has no word targets)

## Implementation Order

1. Create GH issue
2. Create `build_module_direct.py` with validate-only mode first
3. Create `direct-enrich.md` prompt template
4. Add enrich phase to script
5. Create `direct-review.md` prompt template
6. Add review + mdx phases
7. Update `status_direct.py` and `validate_direct.py`
8. Test: `build_module_direct.py a1 tse --validate-only`
9. Test: `build_module_direct.py a1 tse` (full pipeline)
10. Gemini adversarial review of the script
11. `/simplify`

## Verification

```bash
# Validate-only (no LLM, deterministic)
.venv/bin/python scripts/build_module_direct.py a1 tse --validate-only

# Full pipeline on one module
.venv/bin/python scripts/build_module_direct.py a1 tse

# With review
.venv/bin/python scripts/build_module_direct.py a1 tse --review

# Status dashboard shows new statuses
.venv/bin/python scripts/status_direct.py --level a1
```
