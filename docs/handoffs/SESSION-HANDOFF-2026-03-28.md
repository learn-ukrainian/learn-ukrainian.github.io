# Session Handoff — 2026-03-28

## Critical: Last build FAILED — root causes identified

### What happened
A1 M01 build scored R1:8.3 → R2:9.1 → R3:8.9 → then section rewrite produced garbage (dropped all H2 headings) → R4:1.8. Content is now just video embeds — all prose lost.

### Root causes (must fix before next build)

1. **Pre-verify TIMED OUT twice** (300s each, ok=False) — no pre-verify results file exists. The writer had NO verified facts, NO textbook excerpts. Build ran blind.

2. **Write also timed out once** (900s, ok=False) — Gemini rate limits. The retry produced content but quality was lower without pre-verify grounding.

3. **Section rewrite produced zero H2 headings** — the validation caught it (`0 → 5, rejecting`) but the code path accepted it anyway (`accepting as final`). The bug: when rewrite is rejected, the code should keep the PREVIOUS content, not the broken rewrite.

4. **4 review rounds** — too many. R2 was 9.1 (good enough to accept). The loop continued and degraded.

5. **Content is now just video embeds** — the enrichment tail (Словник/Ресурси tabs) survived but the prose body was destroyed by the bad rewrite.

### Fixes needed

```
FIX 1: Pre-verify timeout — increase from 300s to 600s, or retry on timeout
FIX 2: Section rewrite rejection — when rejected, KEEP previous content (don't overwrite)
FIX 3: Accept R2 at 9.0+ — don't continue to R3/R4 when score is already passing
FIX 4: Investigate why Gemini timed out — rate limits? prompt too long?
```

## Session accomplishments (before the failed build)

### Gemini adversarial reviews — 9 reviews, ~20 bugs fixed

| # | Area | Key bugs found |
|---|------|---------------|
| 1 | _apply_review_fixes | 6 bugs: stress matching, TAB duplication, dangling chars |
| 2 | step_pre_verify | 3 bugs: YAML null safety, brittle injection |
| 3 | ModelFamily | 2 bugs: silent fallback, dual source of truth |
| 4 | RAG + persona | 4 missing track personas |
| 5 | _rewrite_weak_sections | word threshold 70%→90%, section count exact |
| 6 | step_activities + quiz parser | bool/int confusion in isinstance |
| 7 | dispatch.py | timeout partial output lost |
| 8 | enrich.py | (no response — rate limited) |
| 9 | step_publish + post_process | video stripping too aggressive for seminar |

### RAG improvements
- **ColBERT reranking** — token-level MaxSim for knowledge packet (BGE-M3, no new model)
- **Cross-encoder reranker** — bge-reranker-v2-m3 for MCP tool calls (lazy-loaded)
- **Knowledge packet optimized** — 40K→7.5K chars, fits 8K prompt, real author names
- **RAG pre-load** — embedding model loads at startup (fixed meta tensor crash)

### Pipeline fixes
- Pre-verify phase implemented (#1070)
- Gemini tool prefix fixed (rag_ → mcp_rag_)
- <fixes> find/replace restored (was dead code)
- Body extraction for fix matching (enrichment stripping)
- Stress-mark-aware matching
- Forbidden A1 activity types stripped deterministically
- V2 quiz parser (correct: integer index)
- Persona system for all tracks
- Video duplicate prevention
- Activity YAML saved after stripping deterministic types

### PR handling
- **#1069** merged + 3 follow-up fixes (МійКлас grammar index)
- **#1034, #1035, #1036** — rebase requested from dependabot
- **#1037, #1038, #1039** — major version bumps on hold (need testing)

### Design
- POC dialogue HTML structure (dialogue-line + speaker classes)
- Typography classes (.ukr, .trans)
- Most POC design already ported in lesson.css

### Issues
- Created: #1096 (СУМ-20 + slavkaa dictionary), #1098 (reranker — now closed), #1099 (ColBERT — closed)
- Closed: #1097, #1099 (both reranker issues)

## Open issues from epic #1093

| Phase | Status |
|-------|--------|
| 0: Skills | ✅ Done |
| 1: Pipeline fixes | ✅ Done (but build exposed new bugs) |
| 2: Quality infra | ✅ Done |
| 3: Code review | ✅ Done (9 Gemini reviews) |
| 4: Ship A1 | ❌ Build failed — fix root causes first |

## Next session priorities

1. **Fix the 4 root causes** from the failed build (pre-verify timeout, rewrite rejection, accept at 9.0+, rate limits)
2. **Clean A1 and rebuild** — fresh build with fixes
3. **Continue Gemini code reviews** — enrich.py review never came back
4. **Continue design work** — #1067 POC mostly done, need to verify rendering

## Services
```bash
./services.sh status  # RAG on 8766, API on 8765, Starlight on 4321
```

## Build command
```bash
.venv/bin/python scripts/build/v6_build.py a1 1 --writer gemini-tools
```
