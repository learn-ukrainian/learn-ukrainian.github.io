# RAG-Grounded Gemini Review Phase

## Context

1600 modules to build, no Claude budget for review. Gemini-cli is free (OAuth). The current review phase (`phase_review_v4`) uses Claude exclusively — we need a Gemini-based alternative.

Gemini reviewing Gemini's work raises self-review concerns. The mitigation: **RAG ground truth transforms the review from "does this look right?" to "does this match authoritative textbook sources?"** — factual comparison, not a vibes check.

### Alignment with #720 (Research Quality)

#720 established the **sharded review architecture**: two parallel single-purpose agents instead of one overloaded context window. This plan implements the same pattern for module review (content + activities), not just research.

#720's key decisions that apply here:
- **Sharded agents** (Gemini point #3): Agent 1 = Fact Checker, Agent 2 = Language Pedant
- **Citation enforcement** (Gemini point #1): only RAG chunk IDs and verified source references count, free-text citations = zero weight
- **Decoupled metrics** (Gemini point #2): factual accuracy and linguistic quality are separate scores
- **VESUM validates relationships, not just existence** (Gemini point #4): check grammatical assertions, not just word forms

### Trusted Source Tiers (shared with #720)

| Tier | Sources | Available now | Role in review |
|------|---------|--------------|----------------|
| **1** | RAG textbooks (18K chunks), RAG literary (37K chunks), VESUM (415K lemmas) | Yes | Ground truth. Discrepancy = auto-flag. |
| **2** | GRAC corpus, ULIF declension tables, pravopys.net, goroh.pp.ua, r2u.org.ua, sum20ua.com | Not yet (#720) | Future: paradigm validation, frequency checks, anti-Russianisms |
| **3** | Ukrainian Wikipedia, osvita.ua, zno.osvita.ua | Not yet (#720) | Verifiable external references |

Currently the review uses **Tier 1 only**. As #720 expands the source pool, the review benefits automatically — more reference material = fewer UNVERIFIED claims.

**Issue:** #703, related: #720, #722, #723

### Relationship to #720, #722, #723

**#720** (research quality evaluation) and **this plan** (module review) use the same architectural pattern at **different pipeline phases**:
- #720 evaluates *research files* (research → discover boundary)
- This plan evaluates *built modules* (validate → mdx boundary)

Both share: sharded agents (Fact Checker + Language Pedant), RAG grounding, citation enforcement, decoupled metrics. The architecture was designed once (#720) and applied twice.

**#722** (ESU crawl → RAG) and **#723** (live query tools: GRAC, ULIF, goroh, pravopys, r2u) expand the Tier 2/3 source pool. **Neither is a dependency for this plan** — we work with Tier 1 (RAG textbooks + literary + VESUM) today. As #722/#723 deliver new sources, they automatically flow into both the research evaluator and the module reviewer through the same injection mechanism.

## Architecture

Sharded Gemini review (per #720 pattern): two parallel single-purpose agents, each a separate `dispatch_gemini_raw()` call.

```
validate phase (existing)
    ↓ screen-result.json (metrics, VESUM, audit gates)
Agent 1: Fact Checker (Gemini + Tier 1 RAG ground truth)
    ↓ compare content against textbook chunks, flag discrepancies
Agent 2: Language Pedant (Gemini + checklists + VESUM)
    ↓ Russianisms, calques, naturalness, dimension scores
Merge → decoupled verdicts (factual accuracy + linguistic quality)
    ↓ FAIL on either?
Fix Loop (Gemini, FIND/REPLACE, max 2 iterations)
    ↓ re-audit after each fix
Final status
```

**Key difference from Claude review:** Gemini has no tool access (no Read/Edit/Grep). Everything inline via stdin, output via stdout with delimiters. Fixes via FIND/REPLACE pairs applied programmatically (existing `_apply_find_replace_fixes()` infrastructure).

**Decoupled metrics** (per #720 point #2):
- **Factual Accuracy** — from Agent 1: discrepancies, unverified claims, alignment score
- **Linguistic Quality** — from Agent 2: Russianisms, naturalness, pedagogy, dimension scores
- **Multimedia Readiness** — from discover phase, completely separate (never drags down review score)

## Pipeline Wiring

- `--review` = Gemini review (free, new default)
- `--review-claude` = Claude review (paid, same as current behavior)
- No flag = no review (rapid iteration, unchanged)

Routing in a `phase_review_v4_dispatch()` wrapper that checks `ctx.review_agent`.

## Step 1: Prompt Templates (3 new files)

### `phase-gemini-review-pass1.md` — Agent 1: Fact Checker (Tier-Aware)

Gemini gets inline:
- Module content (full `.md`)
- **Tier 1 references**, labeled by source:
  - RAG textbook chunks (from `discovery.yaml`, labeled "Textbook, Grade X, Author")
  - RAG literary sources (seminar tracks, labeled "Primary Source: Work Title, Year")
  - RAG image descriptions (labeled "Textbook Image, Grade X")
  - VESUM verification results (labeled "VESUM Dictionary")
- Plan content (objectives, outline)
- Research notes (if available — may already contain Tier 2/3 citations from research phase)

Task: For each grammar explanation / factual claim, compare against tiered reference sources:
- **CONFIRMED [Tier N]** — matches a reference source (cite both, note tier)
- **DISCREPANCY [Tier N]** — contradicts a reference source (cite both, suggest fix). Tier 1 discrepancy = HIGH severity. Tier 2/3 = MEDIUM.
- **UNVERIFIED** — no reference coverage (flag explicitly, do NOT evaluate from own knowledge)

Citation enforcement (per #720 point #1): every discrepancy MUST cite exact quote from content AND exact quote from reference source with **chunk ID or source identifier**. Free-text citations with no chunk ID = zero weight, programmatically discarded.

Output delimiters: `===FACTUAL_REVIEW_START===` / `===FACTUAL_REVIEW_END===` + `===SECTION_FIX_START===` / `===SECTION_FIX_END===`

Edge case: 0 RAG chunks → skip Pass 1, mark as PASS with note "(No RAG sources available)".

**Future expansion:** As Tier 2 sources (sum.in.ua, r2u.org.ua, etc.) are added to the pipeline via #720, they get injected here alongside Tier 1 RAG data. The prompt structure already supports multiple labeled source tiers.

### `phase-gemini-review-pass2.md` — Agent 2: Language Pedant

Gemini gets inline:
- Module content + activities YAML + vocabulary YAML
- Russianisms checklist (`{RUSSIANISM_TABLE}`)
- VESUM failures (`{RAG_WORD_VERIFICATION}`)
- Deterministic screening results (`{DETERMINISTIC_ISSUES}`, `{FILLER_PHRASES}`)
- Pre-computed metrics (word count, immersion %, richness, activity count)
- Scoring rubric (`{SCORING_SECTION}`, `{SCORING_OUTPUT_TABLE}`)
- Track calibration + tier guidance

Task: Standard review — language quality, naturalness, pedagogical flow, known error patterns. Same scoring dimensions as existing D.1.

Output: Uses **same** `===REVIEW_START===` / `===REVIEW_END===` + `===SECTION_FIX_START===` / `===SECTION_FIX_END===` delimiters as existing D.1. This means `_parse_d1_review()` works unmodified.

### `phase-gemini-review-fix.md` — FIND/REPLACE Fix

Adapted from `phase-D2-repair.md`. Key differences:
- No Edit/Grep tool instructions (Gemini has no tools)
- All file contents injected inline (`{CONTENT_FILE_CONTENT}`, `{ACTIVITIES_FILE_CONTENT}`, `{VOCAB_FILE_CONTENT}`)
- Outputs FIND/REPLACE pairs only (applied via existing `_apply_find_replace_fixes()`)
- Maximum 15 FIND/REPLACE pairs per iteration

Output: `===SECTION_FIX_START===` / `===SECTION_FIX_END===`

## Step 2: Helper Functions in `build_module.py`

### `_load_rag_for_review(ctx)` → dict
Load RAG data from `discovery.yaml`. If empty, re-run `search_rag()` as fallback.
Returns `{"text_chunks": [...], "images": [...], "literary": [...]}`.

### `_build_pass1_prompt(ctx, screen, rag_data)` → str
Reads template, injects content file + RAG data + plan + metrics. Returns complete prompt string.

### `_build_pass2_prompt(ctx, screen)` → str
Reads template, injects content + activities + vocab + checklists + metrics + scoring rubric. Returns complete prompt string. Reuses existing helpers: `_get_russicism_table()`, `_format_vesum_verification()`, `_get_track_calibration()`, `_get_scoring_section()`.

### `_parse_factual_review(raw_output)` → D1Result
Extracts `===FACTUAL_REVIEW_START===` / `===FACTUAL_REVIEW_END===` using existing `_extract_delimiter()` / `_extract_delimiter_tolerant()`. Parses discrepancy count, factual alignment score, UNVERIFIED count.

### `_merge_gemini_review_passes(pass1, pass2)` → D1Result
- Both ok: merge raw reviews, combine scores (factual from P1, all others from P2), FAIL if either FAIL
- One failed dispatch: use the other alone (graceful degradation)
- Both failed: `D1Result(ok=False)`

### `_gemini_fix_iteration(ctx, fix_plan, audit_out, fix_iter)` → bool
Builds fix prompt, dispatches to Gemini, applies FIND/REPLACE via existing `_apply_fixes_with_rollback()`.

## Step 3: Main Function `phase_review_gemini_v4()`

```
1. Load cached screen from validate phase
2. Load RAG discovery data
3. Dispatch Pass 1 (factual, 600s timeout)
4. Dispatch Pass 2 (style, 600s timeout)
5. Merge results
6. Quality gate check (existing _quick_review_quality_gate)
7. Save review to review/{slug}-review.md
8. Apply inline FIND/REPLACE fixes from both passes
9. Run deterministic fixes
10. Post-review audit
11. If PASS → done
12. If FAIL → fix loop (max 2 iterations):
    a. Build fix prompt with fix plan + audit failures + inline file contents
    b. Dispatch to Gemini (600s)
    c. Apply FIND/REPLACE fixes with rollback guard
    d. Re-run deterministic fixes + audit
    e. If PASS → done, else continue
13. If exhausted → mark needs-manual-review
```

## Step 4: Pipeline Wiring

### CLI flags (argparse, ~line 4889)
- `--review` → `ctx.review_agent = "gemini"` (new default)
- `--review-claude` → `ctx.review_agent = "claude"`

### `phase_review_v4_dispatch(ctx, state)` → bool
Routes to `phase_review_gemini_v4()` or `phase_review_v4()` based on `ctx.review_agent`.

### `PHASE_FUNCTIONS_V4["review"]` = `phase_review_v4_dispatch`

### SELF_REVIEW_DETECTED gate
Add `review_grounding: "rag-textbook"` to review metadata when Gemini reviews. Audit gate accepts RAG-grounded reviews from same model family.

## Step 5: Tests

### Unit tests in `tests/test_gemini_review.py` (new file)

| Test | What it verifies |
|------|-----------------|
| `test_parse_factual_review_clean` | 0 discrepancies → PASS |
| `test_parse_factual_review_discrepancies` | Extracts discrepancy count and details |
| `test_parse_factual_review_truncated` | Tolerant parser recovers partial output |
| `test_merge_both_pass` | Both PASS → merged PASS |
| `test_merge_one_fail` | Either FAIL → merged FAIL |
| `test_merge_pass1_dispatch_failed` | Degrades to Pass 2 only |
| `test_merge_both_dispatch_failed` | Returns ok=False |
| `test_gemini_fix_find_replace` | Existing _apply_find_replace_fixes works with Gemini output |
| `test_load_rag_for_review` | Loads from discovery.yaml |
| `test_load_rag_fallback` | Falls back to search_rag() |
| `test_cli_review_routes_gemini` | --review → Gemini |
| `test_cli_review_claude_routes_claude` | --review-claude → Claude |
| `test_pass1_skip_no_rag` | No RAG chunks → skip Pass 1, PASS |
| `test_prompt_size_caps` | Content truncated if too large |

### Integration test (manual, needs Gemini access)
```bash
.venv/bin/python scripts/build_module.py a1 10 --review --restart-from review
```

## Verification

1. Run unit tests: `.venv/bin/python -m pytest tests/test_gemini_review.py -v`
2. Run all pipeline tests: `.venv/bin/python -m pytest tests/test_pipeline_v4.py tests/test_pipeline_v4_e2e.py tests/test_video_discovery.py tests/test_gemini_review.py -v`
3. Deploy templates: `npm run claude:deploy`
4. Manual test on a1-10: `.venv/bin/python scripts/build_module.py a1 10 --review --restart-from review`
5. Verify review output in `curriculum/l2-uk-en/a1/review/my-world-objects-review.md`
6. Verify status updated to "reviewed" in `status/my-world-objects.json`

## Existing Infrastructure Reused

| Function | Location | Reused for |
|----------|----------|-----------|
| `dispatch_gemini_raw()` | pipeline_lib.py:719 | All 3 Gemini dispatches |
| `_parse_d1_review()` | build_module.py:2600 | Parsing Pass 2 (same delimiters) |
| `_extract_delimiter()` / `_tolerant()` | build_module.py:816 | Parsing Pass 1 |
| `_apply_find_replace_fixes()` | build_module.py:575 | Fix loop |
| `_apply_fixes_with_rollback()` | build_module.py:1349 | Fix loop safety |
| `_quick_review_quality_gate()` | build_module.py:2444 | Merged review validation |
| `_extract_fix_plan()` | build_module.py:2710 | Fix loop prompt |
| `_extract_audit_failures()` | build_module.py:1156 | Fix loop prompt |
| `_inject_file_contents()` | build_module.py:1260 | Fix prompt assembly |
| `format_rag_discovery()` | video_discovery.py:361 | Pass 1 RAG formatting |
| `read_discovery_yaml()` | video_discovery.py:767 | RAG data loading |
| `_deterministic_screen()` | build_module.py:2906 | Pre-computed metrics |
| `_run_deterministic_fixes()` | build_module.py:1402 | Post-fix cleanup |
| `write_review_with_hash()` | build_module.py | Review persistence |

## Files to Create/Modify

| File | Action |
|------|--------|
| `claude_extensions/phases/gemini/phase-gemini-review-pass1.md` | CREATE |
| `claude_extensions/phases/gemini/phase-gemini-review-pass2.md` | CREATE |
| `claude_extensions/phases/gemini/phase-gemini-review-fix.md` | CREATE |
| `scripts/build_module.py` | MODIFY — add ~200 lines: helper functions + main function + dispatch routing + CLI flags |
| `tests/test_gemini_review.py` | CREATE — ~14 unit tests |
