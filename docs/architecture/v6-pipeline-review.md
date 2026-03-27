# V6 Pipeline Architecture Review

> Full code review of v6_build.py (3,660 lines) + dispatch.py (236 lines) + enrich.py (730 lines) + 6 prompt templates (840 lines total)
>
> Issue: #1073 | Date: 2026-03-27

---

## 1. Architecture Diagram

```
CLI: v6_build.py a1 2 --writer gemini --reviewer claude-tools

main()
  |
  v
[RESOLVE SLUG] ── curriculum.yaml → slug = "reading-ukrainian"
  |
  v
[PREFLIGHT] ── RAG server health check (if --writer ends with -tools)
  |
  v
[CLEAN] ── _clean_build_artifacts() (only --step all)
  |
  +──────────────────────────────────────────────────────────────+
  |  PIPELINE PHASES (sequential)                                |
  |                                                              |
  |  1. CHECK ─── step_check()                                   |
  |     └─ check_plan() + auto_fix_plan() + fix_russianisms()    |
  |                                                              |
  |  2. RESEARCH ─── step_research()                             |
  |     └─ build_packet() → {slug}-knowledge-packet.md           |
  |     └─ assess_research_compat() → research-quality.json      |
  |                                                              |
  |  3. SKELETON ─── step_skeleton()                             |
  |     └─ Dispatch: Sonnet/Gemini → <skeleton> → skeleton.md    |
  |                                                              |
  |  4. WRITE ─── step_write_with_retry()                        |
  |     ├─ Attempt 1: step_write() with writer                   |
  |     │    ├─ Chunking gate: wt≥2000 + ≥2 sections             |
  |     │    │    └─ step_write_chunked() (section-by-section)    |
  |     │    └─ Single-call mode                                 |
  |     ├─ quick_verify() → pass/retry                           |
  |     ├─ Attempt 2: same writer + correction directive         |
  |     └─ Attempt 3: opposite writer (circuit breaker)          |
  |                                                              |
  |  5a. EXERCISES (legacy) ─── step_exercises()                 |
  |     └─ Skipped in --step all (ACTIVITIES replaces it)        |
  |                                                              |
  |  5b. ACTIVITIES ─── step_activities()                        |
  |     └─ Dispatch: Gemini-tools/Claude-tools → YAML            |
  |     └─ JSON Schema validation + retry loop                   |
  |     └─ _inject_abetka_activities() (A1 deterministic inject) |
  |                                                              |
  |  5c. VERIFY EXERCISES ─── step_verify_exercises()            |
  |     └─ Grounding check (informational, non-blocking)         |
  |                                                              |
  |  6. POST-PROCESS ─── _post_process_content()                 |
  |     └─ Strip: dup summary, content notes, stress marks,      |
  |        tab markers, stray quotes                             |
  |                                                              |
  |  5d. VOCAB ─── step_vocab()                                  |
  |     └─ Dispatch: Flash-Lite/Sonnet → vocabulary YAML         |
  |     └─ Dedupe against previous modules                       |
  |                                                              |
  |  7a. ENRICH ─── step_enrich()                                |
  |     └─ enrich.py: tabs, slovnyk, videos, resources, dialogue |
  |                                                              |
  |  7b. VERIFY ─── step_verify()                                |
  |     └─ VESUM check, Russicism scan, IPA scan                 |
  |     └─ VERIFY flag resolution                                |
  |                                                              |
  |  8. REVIEW ─── step_review()                                 |
  |     ├─ Cross-agent: Claude wrote → Gemini reviews (or vice)  |
  |     ├─ VESUM report injected, VERIFY flags injected          |
  |     ├─ Parse scores (9 dimensions, weighted)                 |
  |     ├─ Two gates: score ≥ 8.0 AND verdict == PASS            |
  |     └─ Fix loop (if REVISE):                                 |
  |          ├─ Score ≥ 9.0: rewrite + accept (no re-review)     |
  |          └─ Score < 9.0: rewrite → re-enrich → re-review     |
  |               └─ Max 2 rounds, stop if score doesn't improve |
  |                                                              |
  |  8b. ANNOTATE ─── step_annotate()                            |
  |     └─ Stress marks via stress_annotator.py                  |
  |                                                              |
  |  9. PUBLISH ─── step_publish()                               |
  |     └─ Load activities YAML, strip legacy DSL                |
  |     └─ Inject inline activities at markers                   |
  |     └─ Build 4-tab MDX (Урок/Словник/Зошит/Ресурси)         |
  |     └─ Write frontmatter + imports + MDX to starlight/       |
  |                                                              |
  +──────────────────────────────────────────────────────────────+
```

---

## 2. Dispatch Table — Every LLM Call

| Phase | Default Agent | Default Model | Timeout | MCP Tools | Notes |
|-------|--------------|---------------|---------|-----------|-------|
| skeleton | writer base (strip -tools) | `claude-sonnet-4-6` (Claude) / Gemini PRO | 300s | No | Structure planning, cheap model OK |
| write (single) | writer flag | Inherited from dispatch | 600s (900s w/tools) | If -tools | Full content generation |
| write (chunked) | writer base | Inherited from dispatch | 300s/section | No | **BUG: no tools in chunks** |
| activities | gemini-tools / claude-tools | Gemini PRO / `claude-sonnet-4-6` | 300s | Yes | JSON Schema validated |
| vocab | writer base | `FLASH_LITE_MODEL` (Gemini) / `claude-sonnet-4-6` | 180s | No | Dictionary-like structured output |
| review | cross-agent | Gemini PRO / `claude-opus-4-6` | 600s | Yes | Adversarial, opposite of writer |
| section-rewrite | writer family-tools | Inherited from dispatch | 300s | Yes (Claude) / Yes (Gemini) | Fix weak sections |

### Model resolution flow:

```
dispatch_agent(model=None)
  → is_gemini? → from batch_gemini_config import PRO_MODEL → "gemini-3.1-pro-preview"
  → is_claude? → from batch_gemini_config import CLAUDE_MODEL_CORE_CONTENT → claude-opus-4-6
  → BUT many callers pass model= explicitly, bypassing this default
```

---

## 3. File I/O Map — Every File Read/Written During a Build

### Read:
| File | Phase | Purpose |
|------|-------|---------|
| `curriculum.yaml` | main, check, publish | Module ordering, slug resolution |
| `plans/{level}/{slug}.yaml` | check, skeleton, write, activities, vocab, review, enrich | Source of truth |
| `{level}/research/{slug}-knowledge-packet.md` | skeleton, write | RAG excerpts |
| `{level}/{slug}.md` | exercises, annotate, enrich, verify, review, publish | Content |
| `{level}/activities/{slug}.yaml` | publish | Activity data |
| `{level}/vocabulary/{slug}.yaml` | enrich | Словник data |
| `{level}/orchestration/{slug}/skeleton.md` | write (single-step mode) | Existing skeleton |
| `{level}/orchestration/{slug}/verify-flags.yaml` | review | Writer uncertainty flags |
| `docs/rules/global-friction.yaml` | write retry | Cross-build learnings |
| `{level}/orchestration/*/friction.yaml` | write retry | Module friction files |
| `docs/rules/pedagogy-patterns.yaml` | activities | Exercise patterns |
| `docs/resources/external_resources.yaml` | enrich | External links |
| `docs/resources/miyklas-url-index.yaml` | enrich | МійКлас URLs |
| `docs/resources/ulp-articles-index.yaml` | enrich | ULP article URLs |
| `schemas/activity-v2.schema.json` | activities | Validation schema |
| `data/vesum.db` | enrich, verify, review | VESUM SQLite |

### Written:
| File | Phase | Purpose |
|------|-------|---------|
| `{level}/research/{slug}-knowledge-packet.md` | research | RAG packet |
| `{level}/orchestration/{slug}/research-quality.json` | research | Quality score |
| `{level}/orchestration/{slug}/skeleton.md` | skeleton | Structure plan |
| `{level}/orchestration/{slug}/v6-skeleton-prompt.md` | skeleton | Saved prompt |
| `{level}/orchestration/{slug}/v6-prompt.md` | write | Saved prompt |
| `{level}/orchestration/{slug}/pacing-plan.txt` | write | Pacing plan extract |
| `{level}/{slug}.md` | write | **Content (main output)** |
| `{level}/activities/{slug}.yaml` | activities | Activity data |
| `{level}/orchestration/{slug}/v6-activities-prompt.md` | activities | Saved prompt |
| `{level}/vocabulary/{slug}.yaml` | vocab | Vocabulary YAML |
| `{level}/review/{slug}-review-r{N}.md` | review | Versioned review |
| `{level}/review/{slug}-review.md` | review | Latest review |
| `{level}/orchestration/{slug}/review-structured-r{N}.yaml` | review | Parsed scores |
| `{level}/orchestration/{slug}/v6-review-prompt.md` | review | Saved prompt |
| `{level}/orchestration/{slug}/verify-flags.yaml` | verify | VERIFY flags |
| `{level}/orchestration/{slug}/exercise-verification.json` | verify-exercises | Grounding |
| `{level}/orchestration/{slug}/quick-verify.json` | write | Quick verify results |
| `{level}/orchestration/{slug}/state.json` | all phases | Pipeline state |
| `{level}/orchestration/{slug}/dispatch/*-meta.json` | all dispatches | Dispatch logs |
| `{level}/orchestration/{slug}/dispatch/*.stderr.log` | all dispatches | Stderr capture |
| `{level}/build-stats.jsonl` | write | Retry statistics |
| `{level}/build-errors/{slug}-errors.md` | write (exhausted) | Error report |
| `{level}/orchestration/{slug}/friction.yaml` | write (exhausted) | Auto-friction |
| `{level}/orchestration/{slug}/correction-attempt-{N}.md` | write retry | Directive |
| `starlight/src/content/docs/{level}/{slug}.mdx` | publish | **MDX output** |
| `{level}/orchestration/{slug}/index.md` | final | Orchestration index |

---

## 4. Bug List

### CRITICAL (will cause incorrect behavior)

**BUG-01: Chunked write mode never enables MCP tools**
- Location: `step_write_chunked()` line 756
- The chunked writer dispatches with `agent=base_writer` (e.g., "gemini") but never passes `mcp_tools=True` or `allowed_tools`. Even if the user specified `--writer claude-tools`, the tools suffix is stripped at line 722 (`base_writer = "gemini" if "gemini" in writer else "claude"`).
- Impact: Modules built with chunking (word_target ≥ 2000) never get MCP tool verification during writing.
- Fix: Pass the original `writer` to dispatch, not `base_writer`, when tools are requested.

**BUG-02: Chunked write injects correction directive only on chunk 0**
- Location: `step_write_chunked()` line 748
- If a correction directive exists (from retry loop), it's only prepended to the first chunk's prompt. Chunks 2-N don't see the corrections.
- Impact: Errors in later sections aren't corrected on retry.
- Note: The retry flow calls `step_write()` which gates into `step_write_chunked()`, so this is the actual retry path for large modules.

**BUG-03: `_build_review_correction()` is dead code**
- Location: Lines 2911-2997
- This function is defined but NEVER called anywhere. It was replaced by `_rewrite_weak_sections()` but wasn't removed.
- Impact: No functional impact, but 86 lines of dead code.

**BUG-04: `_parse_review_fixes()` is dead code**
- Location: Lines 3000-3038
- This function parses `<fixes>` blocks from reviews but is NEVER called. The pipeline switched from find/replace to section rewriting.
- Impact: No functional impact, but 38 lines of dead code.

**BUG-05: `step_exercises()` is dead code in the main pipeline**
- Location: Lines 1371-1408, called at 3505-3508
- Only runs in `--step exercises` single-step mode. In `--step all`, it's explicitly skipped (line 3509-3512) but still saves state for "exercises" phase. The `step_activities()` function replaced it entirely.
- Impact: Confusing. The "exercises" state is saved twice — once from the skip message, once from activities.

**BUG-06: Step numbering is inconsistent and confusing**
- The docstring (line 2-16) says: CHECK=2, RESEARCH=3, SKELETON=4, WRITE=5, EXERCISES=5b, VERIFY_EXERCISES=5d, ANNOTATE=6, ENRICH=7b, VERIFY=7, REVIEW=8, PUBLISH=9
- But in main() the actual order is: CHECK → RESEARCH → SKELETON → WRITE → EXERCISES(skip) → ACTIVITIES → VERIFY_EXERCISES → POST_PROCESS → VOCAB → ENRICH → VERIFY → REVIEW → ANNOTATE → PUBLISH
- POST_PROCESS happens at "step 6" but is not in the docstring steps
- VOCAB happens between POST_PROCESS and ENRICH but is listed as "5c"
- ACTIVITIES is "5e" but runs after "5b" (EXERCISES)
- Impact: Impossible to understand the pipeline from the docstring. The actual execution order is the source of truth.

**BUG-07: `_post_process_content()` strips ALL TAB markers unconditionally**
- Location: Lines 1454-1458
- If writer output contains `<!-- TAB:` anywhere, everything from that point is removed. But `_post_process_content` runs in `--step all` mode BEFORE enrich, so this shouldn't cause data loss... unless someone runs `--step annotate` on already-enriched content.
- The step_annotate docstring (line 1478-1482) explicitly warns about this: "Does NOT call _post_process_content".
- Impact: Fragile. The ordering dependency is correct but undocumented in code flow comments.

**BUG-08: Section rewrite accepts results even when rewrite is rejected**
- Location: Lines 3589-3595
- When score ≥ 9.0 and rewrite fails validation (too short, dropped sections), the code falls through to `passed = True` with message "rewrite rejected but score sufficient".
- This means a 9.0-scoring module with identified errors passes without any fix attempt.
- Impact: Known errors ship to learners. The logic should at minimum log the specific errors that went unfixed.

**BUG-09: Seminar write template has unreplaced placeholders**
- Location: `v6-write-seminar.md` lines 127-129
- Contains `{SKELETON_SECTION}` and `{CORRECTION_SECTION}` placeholders, but `step_write()` never replaces these — it only replaces `{PLAN_CONTENT}`, `{KNOWLEDGE_PACKET}`, and `{GOLDEN_FRAGMENT}`.
- For core modules, the skeleton is injected by code in `step_write()` (lines 928-952). For seminar modules, the template expects it in a different placeholder.
- Impact: Seminar modules get literal `{SKELETON_SECTION}` text in their prompts.
- Fix: Either add replacement logic in step_write for seminar templates, or standardize both templates.

### MAJOR (quality/maintenance issues)

**BUG-10: Model resolution is scattered across 6+ locations**
- Skeleton: hardcoded `claude-sonnet-4-6` (line 483)
- Write: dispatcher defaults from `batch_gemini_config` (dispatch.py line 174-178)
- Activities Claude: hardcoded `claude-sonnet-4-6` (line 2068)
- Vocab Gemini: `FLASH_LITE_MODEL` from config (line 1549)
- Vocab Claude: hardcoded `claude-sonnet-4-6` (line 1552)
- Review Claude: hardcoded `claude-opus-4-6` (line 2669)
- Review Gemini: dispatcher default (PRO_MODEL)
- Impact: Changing a model requires editing 6+ places. This is exactly what #1072 (ModelFamily refactor) addresses.

**BUG-11: `_build_review_correction()` has stale block-parsing logic**
- Already dead code (BUG-03), but the block parser at lines 2940-2958 uses `[DIMENSION` to detect block starts, but the review template uses `[DIMENSION] [SEVERITY: ...]` format. The detection regex would never match.
- Impact: No functional impact (dead code), but worth noting for future reference.

**BUG-12: Friction file scanning is O(N*M) across ALL modules in ALL levels**
- Location: `_query_friction_for_errors()` lines 1158-1240
- Iterates every orchestration directory in the current level AND all other levels.
- With 1,735 modules, this could scan hundreds of directories on every write retry.
- Impact: Slow retries. Should be cached or indexed.

**BUG-13: VESUM lookup in enrich.py opens/closes SQLite connection per word**
- Location: `enrich.py` `_vesum_lookup()` lines 50-81
- Called once per vocabulary item. Each call opens a new SQLite connection.
- Impact: Slow enrichment for modules with many vocab items. Should use a connection pool or pass the connection.

**BUG-14: `_build_resources_tab()` in v6_build.py duplicates logic from enrich.py**
- Location: Lines 3156-3206 (v6_build.py) vs lines 282-378 (enrich.py)
- Both build a resources section from plan references + external_resources.yaml.
- The enrich.py version is more complete (includes ULP, МійКлас auto-matching).
- Impact: If resources are updated in enrich logic, the publish step may overwrite with a simpler version. In practice, `step_publish` prefers the existing enriched resources (line 3318-3319).

**BUG-15: Chunk prompt says "Write exercises directly in DSL format"**
- Location: `_build_chunk_prompt()` line 663
- The chunk prompt says: "Write exercises directly in DSL format (:::quiz, :::fill-in, etc.) if the skeleton places them in this section."
- But the main write prompt says: "Do NOT write exercises directly. Place `<!-- INJECT_ACTIVITY: {id} -->` markers."
- Impact: Chunked writes get contradictory instructions about exercises. The ACTIVITIES step generates exercises separately, so DSL blocks from the writer would be stripped anyway, but it wastes writer tokens.

### MINOR (cleanup/style)

**BUG-16: Multiple `import re` statements scattered throughout**
- Lines 40, 494, 1004, 1249, 1391, 1419, 2534, 2697, 2791, 2921, 3013, 3068 — 12 instances of `import re` inside functions.
- `re` is already imported at the module level (line 40).
- Impact: No functional impact, but cluttered code.

**BUG-17: `_log()` is defined twice**
- Lines 24 (dispatch.py) and 246 (v6_build.py) — both are identical `print(msg, flush=True)`.
- Impact: No functional impact, but should be shared.

**BUG-18: Comment references non-existent code**
- Line 2907-2908: Comment says functions were "REMOVED" but the comment itself is orphaned (indented under `_rewrite_weak_sections` which already returned).
- Impact: Confusing. This is the remnant of the dead code removal.

**BUG-19: `step_check` numbering mismatch**
- The function docstring says "Step 2" but it's actually the first pipeline step (CHECK).
- Impact: Confusing when reading code.

---

## 5. Prompt Template Analysis

### Placeholders by template

| Template | Placeholders |
|----------|-------------|
| v6-skeleton.md | TOPIC_TITLE, MODULE_NUM, LEVEL, PHASE, WORD_TARGET, WORD_OVERSHOOT, PLAN_CONTENT, KNOWLEDGE_PACKET, SUMMARY_HEADING |
| v6-write.md | TOPIC_TITLE, MODULE_NUM, LEVEL, PHASE, WORD_TARGET, WORD_CEILING, PLAN_CONTENT, KNOWLEDGE_PACKET, EXACT_SECTION_TITLES, IMMERSION_RULE, PEDAGOGICAL_CONSTRAINTS, LEVEL_CONSTRAINTS, VOCABULARY_HINTS, PRONUNCIATION_VIDEOS, GOLDEN_FRAGMENT, SUMMARY_HEADING |
| v6-write-seminar.md | TOPIC_TITLE, MODULE_NUM, LEVEL, PHASE, WORD_TARGET, WORD_CEILING, PLAN_CONTENT, KNOWLEDGE_PACKET, GOLDEN_FRAGMENT, **SKELETON_SECTION**, **CORRECTION_SECTION** |
| v6-activities.md | MODULE_NUM, TOPIC_TITLE, LEVEL, MODULE_SLUG, INJECTION_MARKERS, PLAN_ACTIVITY_HINTS, PLAN_VOCABULARY, MODULE_CONTENT, TOOL_INSTRUCTIONS, LEVEL_CONTEXT, PEDAGOGY_PATTERNS |
| v6-vocab.md | PLAN_VOCABULARY, MODULE_CONTENT |
| v6-review.md | MODULE_NUM, TOPIC_TITLE, LEVEL, PHASE, WRITER_MODEL, WORD_TARGET, PLAN_CONTENT, GENERATED_CONTENT |

### Contradictions between prompts

1. **Write vs Chunk: exercise format** (BUG-15 above)
   - Write: "Do NOT write exercises directly. Place `<!-- INJECT_ACTIVITY: {id} -->` markers."
   - Chunk: "Write exercises directly in DSL format (:::quiz, :::fill-in, etc.)"

2. **Write vs Seminar: skeleton injection**
   - Core write prompt: skeleton injected by Python code before `## Output Format`
   - Seminar write prompt: expects `{SKELETON_SECTION}` placeholder (never replaced — BUG-09)

3. **Write prompt: "NO IPA" rule (rule 2) vs knowledge packet**
   - Rule says no IPA or Latin transliteration. Knowledge packet may contain IPA from textbooks.
   - Not a bug — the writer should describe sounds by comparison, not copy IPA from the packet.

4. **Review prompt: "Do NOT check for stress marks" vs actual content**
   - Review says stress marks should be absent (correct — added after review).
   - But if `--step review` is run after `--step annotate`, content WILL have stress marks.
   - The reviewer correctly ignores them, but could falsely flag words with combining acute.

### Stale instructions

1. **v6-write.md line 164-167**: Dialogue format example uses `> **Оленка:**` blockquote style, but the `_format_dialogues()` in enrich.py converts these to `<div class="dialogue">`. Not stale per se, but the writer doesn't need to know about the final format.

2. **v6-review.md line 67**: "List every exercise block (:::quiz, :::fill-in...)" — but V6 activities are YAML-based, not DSL blocks. The review prompt hasn't been updated to describe YAML activities.

3. **v6-write-seminar.md line 35**: "Write exercises directly" — but the activities step should handle this. Seminar prompts lag behind core prompts.

---

## 6. State Machine: state.json

### Fields
```json
{
  "mode": "v6",
  "track": "a1",
  "slug": "reading-ukrainian",
  "phases": {
    "check": { "status": "complete", "ts": "..." },
    "research": { "status": "complete", "ts": "..." },
    "skeleton": { "status": "complete", "ts": "..." },
    "write": { "status": "complete", "ts": "..." },
    "exercises": { "status": "complete", "ts": "..." },
    "activities": { "status": "complete", "ts": "..." },
    "verify-exercises": { "status": "complete", "ts": "..." },
    "annotate": { "status": "complete", "ts": "..." },
    "vocab": { "status": "complete", "ts": "..." },
    "enrich": { "status": "complete", "ts": "..." },
    "verify": { "status": "complete", "ts": "..." },
    "review": { "status": "complete", "ts": "..." },
    "stress": { "status": "complete", "ts": "..." },
    "publish": { "status": "complete", "ts": "..." }
  }
}
```

### Issues
- Status is always "complete" — no "failed" or "in_progress" states recorded
- `_save_v6_state` is called AFTER success, so failure leaves the previous state
- "annotate" and "stress" are separate state entries for the same conceptual step
- "exercises" state is saved even when skipped (line 3513)

---

## 7. Silent Failure Points

| Location | What can fail | What happens |
|----------|--------------|--------------|
| `step_research` research_quality import | `assess_research_compat` missing | Warning logged, continues |
| `step_verify` VESUM check | `_run_vesum_verify` import fails | Warning, continues |
| `step_verify` IPA scan | `_run_ipa_scan` import fails | Warning, continues |
| `step_vocab` YAML parse | Writer returns non-YAML | Returns None, logged |
| `step_enrich` enrichment | Exception in enrich_file | Returns empty list, logged |
| `step_annotate` stress marks | Import or runtime error | Warning, continues |
| `_resolve_verify_flags` | VESUM DB missing | Returns unresolved flags |
| `_query_friction_for_errors` | YAML parse errors in friction files | Silent continue per file |
| `_save_structured_findings` | Regex doesn't match review format | Empty YAML saved |
| `enrich.py` `_vesum_lookup` | SQLite error | Returns ("", ""), silent |
| `_build_vesum_report` | SQLite error | Returns "" |

### Content corruption risk

| Scenario | Risk | Mitigation |
|----------|------|------------|
| `_rewrite_weak_sections` produces truncated output | **MEDIUM** — checked at line 2893-2896 (reject if <70% of original) |
| Enrichment shrinks content | **LOW** — checked at line 704 (reject if <50% of original) |
| `_post_process_content` strips valid tab markers | **LOW** — only runs in full pipeline before enrich adds tabs |
| Review fix loop worsens score | **LOW** — stopped if score doesn't improve (line 3627-3632) |
| Section rewrite drops sections | **LOW** — checked at line 2888-2889 |

---

## 8. Refactor Recommendations

### P0: Fix before next build

1. **Fix BUG-09**: Add `{SKELETON_SECTION}` and `{CORRECTION_SECTION}` replacement in `step_write()` for seminar templates, or standardize templates.

2. **Fix BUG-01**: Pass original `writer` (with -tools suffix) through chunked write path.

3. **Fix BUG-15**: Align chunk prompt with main prompt — use `<!-- INJECT_ACTIVITY -->` markers, not DSL format.

4. **Fix BUG-08**: When score ≥ 9.0 and rewrite fails, log the specific unfixed errors. Don't silently accept.

### P1: ModelFamily refactor (#1072)

5. **Replace scattered model constants** (BUG-10) with a `ModelFamily` dataclass:
```python
@dataclass
class ModelFamily:
    name: str           # "claude" or "gemini"
    thinking: str       # opus / pro
    fast: str           # sonnet / flash
    tools_prefix: str   # "mcp__rag__" / "rag_"

CLAUDE = ModelFamily("claude", "claude-opus-4-6", "claude-sonnet-4-6", "mcp__rag__")
GEMINI = ModelFamily("gemini", "gemini-3.1-pro-preview", "gemini-3-flash-preview", "rag_")
```
Then each phase picks `family.thinking` or `family.fast` based on phase type:
- Skeleton, Activities, Vocab → `fast`
- Write, Review → `thinking`
- Section rewrite → `thinking` (same family as writer)

### P2: Clean up dead code

6. **Remove dead functions**: `_build_review_correction()`, `_parse_review_fixes()`, the orphan comment at 2907-2908.

7. **Remove `step_exercises()`**: It's fully replaced by `step_activities()`. Keep it only if someone needs `--step exercises` for backward compat, but mark it clearly as legacy.

8. **Clean up module-level re-imports**: Remove all 12 `import re` inside functions since `re` is already imported at module level.

### P3: Structural improvements

9. **Fix step numbering**: Renumber all steps to match actual execution order. Update docstring.

10. **Extract prompt building into separate module**: `_build_chunk_prompt`, `_build_tool_instructions`, `_build_activity_level_context`, `_build_pedagogy_patterns` could all live in a `prompt_builder.py` module (~500 lines extracted).

11. **Cache friction file scanning**: Build an in-memory index of active frictions at startup instead of O(N*M) directory scanning on every retry.

12. **Connection pooling for VESUM**: Pass a single SQLite connection through enrich functions instead of opening per-word.

13. **Standardize seminar vs core templates**: The seminar template is significantly less developed than core. Either bring it to parity (injection markers, MCP tool instructions, exercise format) or document the differences.

---

## 9. Function Reference (42 functions)

### Pipeline steps (public):
| Function | Lines | Purpose |
|----------|-------|---------|
| `step_check` | 284-358 | Plan validation + auto-fix |
| `step_research` | 361-409 | RAG knowledge packet |
| `step_skeleton` | 412-511 | Paragraph-level structure |
| `step_write` | 797-1034 | Single-call content generation |
| `step_write_chunked` | 677-794 | Section-by-section generation |
| `step_write_with_retry` | 1037-1155 | Write + quick_verify + retry loop |
| `step_exercises` | 1371-1408 | **LEGACY** — fill exercise placeholders |
| `step_activities` | 1935-2154 | Structured activity YAML generation |
| `step_vocab` | 1504-1604 | Writer-generated vocabulary |
| `step_enrich` | 2278-2301 | Deterministic enrichment |
| `step_verify` | 2304-2421 | VESUM + Russicism + IPA checks |
| `step_verify_exercises` | 1703-1751 | Exercise grounding check |
| `step_annotate` | 1477-1501 | Stress mark annotation |
| `step_review` | 2502-2777 | Cross-agent adversarial review |
| `step_publish` | 3209-3385 | MDX generation with 4 tabs |
| `main` | 3388-3660 | CLI + orchestration |

### Support functions (private):
| Function | Lines | Purpose |
|----------|-------|---------|
| `_build_tool_instructions` | 58-148 | MCP tool prompt section |
| `_extract_body` | 158-180 | Split prose from enrichment tabs |
| `_clean_build_artifacts` | 183-243 | Remove previous build files |
| `_log` | 246-247 | Print with flush |
| `_save_v6_state` | 250-281 | Write state.json |
| `_parse_skeleton_sections` | 514-551 | Parse skeleton H2 sections |
| `_extract_word_budget` | 554-557 | Parse word budget from heading |
| `_build_section_summary` | 560-575 | Rolling summary for chunks |
| `_build_chunk_prompt` | 578-674 | Build prompt for one section |
| `_query_friction_for_errors` | 1158-1240 | Search friction files for patterns |
| `_save_structured_findings` | 1243-1286 | Parse review scores → YAML |
| `_generate_friction` | 1289-1328 | Auto-generate friction on failure |
| `_log_stats` | 1331-1347 | Append retry stats to JSONL |
| `_save_quick_verify` | 1350-1368 | Persist quick verify results |
| `_post_process_content` | 1411-1474 | Strip LLM artifacts |
| `_extract_verify_flags` | 1607-1625 | Parse `<!-- VERIFY -->` markers |
| `_resolve_verify_flags` | 1628-1685 | VESUM lookup for flags |
| `_save_verify_flags` | 1688-1700 | Write flags YAML |
| `_check_activity_semantics` | 1754-1771 | Check inline activity ids |
| `_build_activity_level_context` | 1774-1853 | Level-aware activity context |
| `_build_pedagogy_patterns` | 1856-1932 | Match pedagogy patterns |
| `_inject_abetka_activities` | 2157-2275 | Deterministic alphabet activities |
| `_build_vesum_report` | 2424-2499 | Pre-verify words for reviewer |
| `_rewrite_weak_sections` | 2780-2904 | Section-level content rewrite |
| `_build_review_correction` | 2911-2997 | **DEAD CODE** — correction directive |
| `_parse_review_fixes` | 3000-3038 | **DEAD CODE** — parse `<fixes>` block |
| `_strip_dsl_blocks` | 3041-3057 | Remove legacy DSL exercises |
| `_convert_tab_markers` | 3060-3093 | Tab markers → MDX components |
| `_load_activities` | 3096-3108 | Load activities YAML |
| `_inject_inline_activities` | 3111-3132 | Replace markers with JSX |
| `_build_workbook_tab` | 3135-3153 | Render workbook activities |
| `_build_resources_tab` | 3156-3206 | Build resources from plan |

---

## 10. Supporting File Analysis (AC20-AC23)

### activity_renderer.py (AC21)
- **Input**: Parsed activity YAML dicts (from `activities/{slug}.yaml`)
- **Processing**: Maps YAML structure to React component props via `_RENDERERS` registry
- **Output**: JSX strings for MDX insertion; HTML comments for unknown types
- **37 component types**: 14 core (Quiz, FillIn, MatchUp, GroupSort, TrueFalse, ErrorCorrection, Anagram, Translate, Unjumble, Observe, Classify, LetterGrid, WatchAndRepeat, etc.) + 13 seminar (CriticalAnalysis, EssayResponse, SourceEvaluation, EtymologyTrace, etc.)
- **`get_required_imports()`**: Returns deduplicated, sorted import statements for only the components actually used

### audit/core.py (AC23)
- **Gates**: Structure (outline compliance, tone), core (word count, engagement, required activity types), pedagogy (blocking violations), immersion score
- **Pass/fail**: Fails on critical template violations, missing required activity types, critical pedagogy violations (blocking=True), self-review detection
- **V6 interaction**: Skips template compliance when plan data exists (plan-based metadata). Loads sidecar metadata from `meta.yaml` or plan YAML. Merges plan fields (title, content_outline, word_target, objectives, grammar) into metadata if missing.
- **Flow**: Load → Resolve metadata → Template check → Structure/outline → Word count → YAML activity validation → Core gates → Pedagogical checks → Immersion → Report

### stress_annotator.py (AC22)
- **Input**: Content .md file path
- **Processing**: Extracts Ukrainian words from body text (skips headings, code blocks, HTML tags), looks up stress position in `ukrainian-word-stress` library (2.7M forms), adds combining acute (U+0301) after stressed vowel
- **Body-only check**: Only annotates prose between first H2 and TAB:Словник marker (5% threshold — skips if <5% of words get stress marks, indicating the file isn't Ukrainian prose)
- **Output**: Modified file with stress marks in-place, returns count of annotated words

---

## 11. Summary

The V6 pipeline is functional but shows clear signs of incremental patching. The core flow (check → research → skeleton → write → activities → enrich → review → publish) works correctly for single-call builds. The main issues are:

1. **Seminar template broken** (BUG-09) — unreplaced placeholders
2. **Chunked writes lack tools** (BUG-01) — no MCP verification for large modules
3. **~125 lines of dead code** (BUGs 03, 04, 05) — confusion risk
4. **Model resolution scattered** (BUG-10) — change requires editing 6+ places
5. **Prompt contradictions** (BUG-15) — chunk prompt says write DSL, main says markers only

The review confirms #1072 (ModelFamily refactor) is the right next step. After that, fix the seminar template and chunk prompt contradictions.
